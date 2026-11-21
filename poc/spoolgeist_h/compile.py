"""Deterministic binding compiler (v3). NO LLM.

Takes an LLM-written Binding (v2 schema) plus operator-verified approved samples and derives, without any
model call, the structural facts the v3 interpreter enforces:

  header            ordered line patterns that must open page 1 (exact static text where the line never varies,
                    otherwise one of the binding's own anchor / skip regexes that matches that line in EVERY sample)
  identity_index    position of the lab-identity line inside the header (used to find continuation pages
                    when there is no form feed)
  continuation_len  how many header lines every continuation page repeats (None = no approved multi-page sample:
                    multi-page documents will be rejected)
  template_lines    static lines present in every approved clean sample (footers, section titles, notes)
  promoted_required optional fields present in 100% of approved samples become required (F-06)
  date_formats      per date field: format, the sample strings, and whether the samples disambiguate DD/MM vs MM/DD

The compiler only uses documents an operator verified (gen + dev with expected=accept). It never sees the
held-out test split or the adversarial suite.
"""
from __future__ import annotations

import copy
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import regex

from .grid import normalize
from . import interpreter as I
from .interpreter import Reject, _c, _field, nonblank, line_matches, ws, page_starts

MAX_HEADER = 12


# ----------------------------------------------------------------------------- operator-verified sample records
def sample_bytes(d: dict) -> bytes:
    """A sample is {doc_id, text | raw_b64, queue_codepage?, expected, truth, perturbation | cls}."""
    if "raw_b64" in d:
        import base64
        return base64.b64decode(d["raw_b64"])
    return d["text"].encode()


def sample_cp(d: dict):
    cp = d.get("queue_codepage")
    return None if cp in (None, "ascii") else cp


def sample_class(d: dict) -> str:
    return d.get("perturbation") or d.get("cls") or "clean"


def sample_norm(d: dict):
    return normalize(sample_bytes(d), sample_cp(d))


def _page1_header_lines(b: dict, lines: List[str]) -> List[int]:
    start_re = _c(b["results"]["start"])
    s = next((i for i, ln in enumerate(lines) if start_re.search(ln)), len(lines))
    return nonblank(lines, 0, s)[:MAX_HEADER]


def _alpha(s: str) -> int:
    return sum(ch.isalpha() for ch in s)


def derive_header(b: dict, docs: List[List[str]]) -> Tuple[List[dict], Optional[int]]:
    heads = [[ln[i] for i in _page1_header_lines(b, ln)] for ln in docs]
    regexes = [("anchor", p) for p in b["layout"]["anchors"]] + [("skip", p) for p in b["results"]["skip_lines"]]
    regexes = [(k, p) for k, p in regexes if not _c(p).search("")]
    pats = []
    for k in range(min(len(h) for h in heads)):
        col = [h[k] for h in heads]
        if len({ws(x) for x in col}) == 1:
            pats.append({"exact": ws(col[0])})
            continue
        hit = next(((kind, p) for kind, p in regexes if all(_c(p).search(x) for x in col)), None)
        if hit is None:
            break
        pats.append({"regex": hit[1], "source": hit[0]})
    ident = next((i for i, p in enumerate(pats)
                  if ("exact" in p and _alpha(p["exact"]) >= 6) or p.get("source") == "anchor"), None)
    return pats, ident


def compile_binding(b: dict, approved: List[dict], version: int, sample_refs: Optional[List[dict]] = None,
                    regression_refs: Optional[List[dict]] = None) -> Tuple[dict, dict]:
    """approved: list of corpus docs (dicts with text, perturbation, doc_id, truth). Returns (binding, report).
    v3.1: the original LLM binding and the exact sample / regression-set references (path + SHA-256) are stored in
    the compiled block, so approval can re-derive the binding and re-run the gate instead of trusting a report."""
    b = copy.deepcopy(b)
    b.pop("compiled", None)
    b.pop("version", None)
    llm_original = copy.deepcopy(b)
    out = copy.deepcopy(b)
    out["version"] = version
    norms = [sample_norm(d) for d in approved]
    lines = [n.lines for n in norms]
    clean_idx = [i for i, d in enumerate(approved) if sample_class(d) == "clean"]
    report = {"binding_id": b["binding_id"], "version": version, "samples": [d["doc_id"] for d in approved],
              "n_samples": len(approved), "n_clean": len(clean_idx), "warnings": [], "errors": []}

    header, ident = derive_header(b, lines)
    if ident is None or len(header) < 2:
        report["errors"].append(f"no usable page-1 header template (patterns={len(header)}, identity={ident})")
    tmpl = set.intersection(*[{ws(x) for x in lines[i] if x.strip()} for i in clean_idx]) if clean_idx else set()
    out["compiled"] = {"compiler": "spoolgeist_h.compile/5", "header": header, "identity_index": ident,
                       "template_lines": sorted(tmpl), "continuation_len": None,
                       "llm_binding": llm_original, "sample_refs": sample_refs or [],
                       "regression_refs": regression_refs or []}
    # continuation pages
    cont = []
    if ident is not None:
        for n in norms:
            st = page_starts(out, n.lines, n.ff_page_starts)
            for s in st[1:]:
                nb = nonblank(n.lines, s)
                m = 0
                while m < len(header) and m < len(nb) and line_matches(header[m], n.lines[nb[m]]):
                    m += 1
                cont.append(m)
    report["n_continuation_pages"] = len(cont)
    if cont:
        m = min(cont)
        if m >= (ident or 0) + 1:
            out["compiled"]["continuation_len"] = m
        else:
            report["warnings"].append(f"continuation pages repeat only {m} header lines (< identity line): multi-page documents will be rejected")
    else:
        report["warnings"].append("no approved multi-page sample: multi-page documents will be rejected")
    # optional-field promotion (F-06)
    promoted = []
    for name, spec in b["fields"].items():
        if spec.get("required"):
            continue
        present = 0
        for n in norms:
            try:
                present += _field(b, name, n.text) is not None
            except Reject:
                pass
        # v4: the operator-verified truth also decides: if every approved sample's truth carries this field, the
        # layout always prints it, so a sample where the regex missed it must not lower the bar (EXPERIMENT_LOG 60)
        truth_has = all((d.get("truth") or {}).get(name) not in (None, "") for d in approved) and \
            all(name in (d.get("truth") or {}) for d in approved)
        if norms and (present == len(norms) or truth_has):
            out["fields"][name]["required"] = True
            promoted.append(name)
    out["compiled"]["promoted_required"] = promoted
    # date formats (F-08 g / Phase D)
    dates = {}
    for name, spec in b["fields"].items():
        if spec["type"] != "date":
            continue
        fmt = spec["format"]
        swapped = fmt.replace("%d", "\0").replace("%m", "%d").replace("\0", "%m") if ("%d" in fmt and "%m" in fmt) else None
        strings = []
        for n in norms:
            for m in _c(spec["regex"]).finditer(n.text):
                strings.append(ws(m.group("v")))
        disamb = None
        if swapped:
            def ok(s, f):
                try:
                    datetime.strptime(s, f)
                    return True
                except ValueError:
                    return False
            disamb = any(ok(s, fmt) and not ok(s, swapped) for s in strings)
        dates[name] = {"format": fmt, "day_month_order_ambiguous_format": bool(swapped),
                       "samples_disambiguate": disamb, "n_strings": len(strings)}
    out["compiled"]["date_formats"] = dates
    # v4: note markers + continuation indent, learned from the operator-verified truth notes of approved samples
    import regex as _rx
    markers, indents = set(), []
    for d, n in zip(approved, norms):
        for note in (d.get("truth") or {}).get("notes") or []:
            ln = next((x for x in n.lines if ws(x) == ws(note)), None)
            if ln is None:
                continue
            m = _rx.match(r"^(\|\s*)?[A-Za-z][A-Za-z ]{0,20}?\s?(?::|\s-)\s", ws(ln))
            if m:
                markers.add(m.group(0).strip())
            elif ln.startswith("  "):
                indents.append(len(ln) - len(ln.lstrip(" ")))
    out["compiled"]["note_markers"] = sorted(markers)
    out["compiled"]["note_continuation_indent"] = min(indents) if indents else None
    # v4: approved static lines inside the table (e.g. section subheadings): lines without any digit that an
    # approved sample carries inside the table region and no row consumes
    tstatic = set()
    out["compiled"]["table_static_lines"] = []
    for n in norms:
        for _ in range(4):
            try:
                I.execute(out, n.text, [], [], [], n.bold)
                break
            except Reject as r:
                if r.code != "unparsed_content":
                    break
                frag = r.detail.strip("'\"")
                ln = next((x for x in n.lines if frag[:40] and frag[:40] in x), None)
                if ln is None or any(ch.isdigit() for ch in ln):
                    break
                tstatic.add(ws(ln))
                out["compiled"]["table_static_lines"] = sorted(tstatic)
    # v3.2: approved numeric skeletons (lines outside parsed rows that legitimately carry numbers)
    skel, generic = set(), set()
    for n in norms:
        try:
            region = []
            I.execute(out, n.text, [], region, [], n.bold)
        except Reject as r:
            # an approved sample this binding cannot extract (e.g. an unsupported long name) contributes no
            # skeletons; it is reported by gate G5 as an unsupported variation, not a compile error
            report.setdefault("numeric_skeleton_skipped_samples", []).append(f"{r.code}")
            continue
        ls = I.line_starts_of(n.lines)
        note_lines = set(I.NOTE_LINES)
        for i in I.checked_lines(n.lines, region, list(I.SKIPPED)):
            if i in note_lines or I.is_note_start(n.lines[i], out["compiled"]):
                continue          # notes are never a source of approved numbers (policy: numbers in notes -> refuse)
            sk = I.numeric_skeleton(I.masked_line(n.lines, i, ls, list(I.VSPANS)))
            if sk is not None:
                from .sentinel import UNIT_RE
                if UNIT_RE.search(n.lines[i]) or any(l in n.lines[i] for l in b["results"]["labels"] if len(l) >= 3):
                    report.setdefault("refused_numeric_skeletons", []).append(sk)
                    continue          # a line with a unit or a test name is never approved as "allowed numeric text"
                skel.add(sk)
                if sum(ch.isalpha() for ch in sk.replace("<V>", "")) < 3:
                    generic.add(sk)
    out["compiled"]["numeric_skeletons"] = sorted(skel)
    # v4: text skeletons of trusted lines + abnormal marker (bold), learned from extractable approved samples
    learned, bold_agree, bold_rows = {}, True, 0
    for d, n in zip(approved, norms):
        try:
            spans, region = [], []
            rec = I.execute(out, n.text, spans, region, [], n.bold)
            I.classify_lines(out, n.lines, region, list(I.SKIPPED), spans, list(I.VSPANS), learn=learned)
        except Reject:
            continue
        tr = {x["code"]: x for x in ((d.get("truth") or {}).get("results") or [])}
        for x in rec["results"]:
            if x["code"] in tr and "flag" in tr[x["code"]]:
                bold_rows += x.get("emphasis", False)
                if bool(x.get("emphasis")) != bool(tr[x["code"]]["flag"]):
                    bold_agree = False
    out["compiled"]["text_skeletons"] = I.derive_skeletons(learned)
    has_flag_group = "flag" in _c(b["results"]["row"]).groupindex
    out["compiled"]["abnormal_marker"] = "bold" if (not has_flag_group and bold_agree and bold_rows > 0) else None
    if generic:
        report["warnings"].append(f"generic numeric skeletons (fewer than 3 letters): {sorted(generic)}")
        report["generic_numeric_skeletons"] = sorted(generic)
    report["compiled_summary"] = {"header_patterns": len(header), "identity_index": ident,
                                  "continuation_len": out["compiled"]["continuation_len"],
                                  "template_lines": len(tmpl), "promoted_required": promoted, "date_formats": dates,
                                  "numeric_skeletons": out["compiled"]["numeric_skeletons"],
                                  "note_markers": out["compiled"]["note_markers"],
                                  "table_static_lines": out["compiled"]["table_static_lines"],
                                  "text_skeleton_keys": len(out["compiled"]["text_skeletons"]),
                                  "abnormal_marker": out["compiled"]["abnormal_marker"]}
    return out, report
