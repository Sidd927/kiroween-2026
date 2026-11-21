"""v3 (Phase 2 hardened): deterministic execution of a compiled Binding. NO LLM is ever called from this module.

Fail-closed: every unexpected condition produces a REJECT with an explicit reason.

Changes vs v2.1 (spoolgeist/interpreter.py), each traceable to an audit finding:
  * recognition modes (F-01): "anywhere" (= v2.1), "pos" (page-1 header template), "pos+pages" (+ every page
    must start with the approved continuation header), "full" (+ every non-blank line of the document must be
    accounted for: table coverage, header template, static template lines, binding skip/anchor lines, field lines)
  * date precision is recorded; no time is invented for date-only layouts (F-03)
  * v3.1: in "full" mode a binding-independent result sentinel rejects result-like text that no parsed row
    consumed (review finding RV-1: results hidden on field / skip / anchor lines)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional

import jsonschema
import regex  # supports timeouts -> protects against catastrophic backtracking in LLM-written regexes

from .dictionary import DICT, unit_factor
from . import sentinel, validators

MODES = ("anywhere", "pos", "pos+pages", "full")

SCHEMA = json.loads((Path(__file__).with_name("binding_schema.json")).read_text())
TIMEOUT = 0.5  # seconds per regex operation
DECIMAL_RE = regex.compile(r"^[0-9]{1,7}(?:\.[0-9]{1,4})?$")


class Reject(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


@dataclass
class Outcome:
    status: str                       # ACCEPT | REJECT
    binding_id: Optional[str]
    record: Optional[dict] = None
    reasons: List[str] = field(default_factory=list)
    llm_calls: int = 0                # always 0 here, recorded for the metric


def _c(p: str, flags=regex.MULTILINE):
    return regex.compile(p, flags)


# ----------------------------------------------------------------------------- static checks
def static_check(b: dict) -> List[str]:
    """Checks a candidate binding before it is ever run. Returns a list of problems."""
    errs = []
    try:
        jsonschema.validate(b, SCHEMA)
    except jsonschema.ValidationError as e:
        return [f"schema: {e.message} at {list(e.absolute_path)}"]
    pats = list(b["layout"]["anchors"]) + [b["results"]["start"], b["results"]["end"], b["results"]["row"]]
    pats += b["results"]["skip_lines"]
    for name, f in b["fields"].items():
        pats.append(f["regex"])
        try:
            if "v" not in _c(f["regex"]).groupindex:
                errs.append(f"field {name}: regex lacks named group 'v'")
        except regex.error as e:
            errs.append(f"field {name}: bad regex {e}")
        if f["type"] == "date" and not f.get("format"):
            errs.append(f"field {name}: date without format")
        if f["type"] == "enum" and not f.get("enum_map"):
            errs.append(f"field {name}: enum without enum_map")
    for p in pats:
        try:
            _c(p)
        except regex.error as e:
            errs.append(f"bad regex {p!r}: {e}")
    try:
        gi = _c(b["results"]["row"]).groupindex
        for g in ("label", "value", "unit"):
            if g not in gi:
                errs.append(f"row regex lacks required group '{g}' (units must come from the document)")
    except regex.error:
        pass
    for lbl, code in b["results"]["labels"].items():
        if code not in DICT["tests"]:
            errs.append(f"label {lbl!r} maps to unknown code {code!r}")
    for p in b["layout"]["anchors"]:
        try:
            if _c(p).search(""):
                errs.append(f"anchor {p!r} matches the empty string")
        except regex.error:
            pass
    for p in b["results"]["skip_lines"]:
        try:
            if _c(p).fullmatch("HAEMOGLOBIN 13.5 g/dL 13.0-17.0") or _c(p).search("Z9Z9 13.5 g/dL"):
                errs.append(f"skip regex {p!r} is too permissive (matches a result-like line)")
        except regex.error:
            pass
    return errs


# ----------------------------------------------------------------------------- recognition
def matches_layout(b: dict, text: str) -> bool:
    try:
        return all(_c(a).search(text, timeout=TIMEOUT) for a in b["layout"]["anchors"])
    except TimeoutError:
        return False


def recognise(bindings: List[dict], text: str) -> List[dict]:
    return [b for b in bindings if matches_layout(b, text)]


# ----------------------------------------------------------------------------- extraction
def _norm_ws(s: str) -> str:
    return regex.sub(r"\s+", " ", s).strip()


def _field(b: dict, name: str, text: str, spans: Optional[list] = None):
    spec = b["fields"].get(name)
    if spec is None:
        return None
    vals = []
    for m in _c(spec["regex"]).finditer(text, timeout=TIMEOUT):
        if spans is not None:
            spans.append((m.start(), m.end()))
        v = m.group("v")
        if v is not None and _norm_ws(v):
            vals.append(_norm_ws(v))
    distinct = sorted(set(vals))
    if not distinct:
        if spec["required"]:
            raise Reject("missing_field", name)
        return None
    if len(distinct) > 1:
        raise Reject("conflicting_field", f"{name}: {distinct}")
    v = distinct[0]
    if spec.get("pattern") and not regex.fullmatch(spec["pattern"], v, timeout=TIMEOUT):
        raise Reject("pattern_mismatch", f"{name}={v!r}")
    t = spec["type"]
    try:
        if t == "integer":
            if not regex.fullmatch(r"[0-9]{1,4}", v):
                raise ValueError(v)
            return int(v)
        if t == "date":
            return datetime.strptime(v, spec["format"])
        if t == "enum":
            if v not in spec["enum_map"]:
                raise ValueError(v)
            return spec["enum_map"][v]
    except ValueError:
        raise Reject("invalid_type", f"{name}={v!r} as {t} {spec.get('format', '')}")
    return v


def _table(b: dict, text: str, region: Optional[list] = None, consumed: Optional[list] = None) -> List[dict]:
    R = b["results"]
    lines = text.split("\n")
    start_re, end_re = _c(R["start"]), _c(R["end"])
    s = next((i for i, ln in enumerate(lines) if start_re.search(ln, timeout=TIMEOUT)), None)
    if s is None:
        raise Reject("table_start_missing")
    e = next((i for i in range(s + 1, len(lines)) if end_re.search(lines[i], timeout=TIMEOUT)), None)
    if e is None:
        raise Reject("table_end_missing", "document truncated or layout changed")
    if region is not None:
        region += [s, e]
    skip = [_c(p) for p in R["skip_lines"]]
    row_re = _c(R["row"])
    # v2 (post-freeze fix, found by the property-based test): result-like rows OUTSIDE the parsed
    # table region mean the table boundaries were mis-detected (e.g. a damaged column header on page 1
    # made the table start on page 2). Reject instead of silently dropping those rows.
    outside = "\n".join(lines[:s + 1]) + "\n" + "\n".join(lines[e:])
    for m in row_re.finditer(outside, timeout=TIMEOUT):
        if _norm_ws(m.groupdict().get("label") or "") in R["labels"]:
            raise Reject("rows_outside_table", _norm_ws(m.group(0))[:60])
    for ln in lines[:s] + lines[e + 1:]:
        if any(lb == _norm_ws(ln)[:len(lb)] and len(lb) >= 3 and regex.search(r"\d", ln) for lb in R["labels"]):
            raise Reject("rows_outside_table", _norm_ws(ln)[:60])
    kept = []
    for ln in lines[s + 1:e]:
        if any(p.search(ln, timeout=TIMEOUT) for p in skip):
            if row_re.search(ln, timeout=TIMEOUT) and _norm_ws(ln) and any(lb in _norm_ws(ln) for lb in R["labels"]):
                raise Reject("skip_hides_row", ln.strip()[:60])
            continue
        kept.append(ln)
    block = "\n".join(kept)
    rows, pos = [], 0
    for m in row_re.finditer(block, timeout=TIMEOUT):
        gap = block[pos:m.start()]
        if gap.strip():
            raise Reject("unparsed_content", repr(gap.strip()[:60]))
        if m.end() == m.start():
            continue
        rows.append(m)
        if consumed is not None:
            consumed.append(m.group(0))
        pos = m.end()
    if block[pos:].strip():
        raise Reject("unparsed_content", repr(block[pos:].strip()[:60]))
    if not (R["min_rows"] <= len(rows) <= R["max_rows"]):
        raise Reject("row_count", f"{len(rows)} not in [{R['min_rows']},{R['max_rows']}]")
    out = []
    for m in rows:
        gd = m.groupdict()
        label = _norm_ws(gd.get("label") or "")
        if label not in R["labels"]:
            raise Reject("unknown_label", repr(label))
        code = R["labels"][label]
        value = (gd.get("value") or "").strip()
        if not DECIMAL_RE.match(value):
            raise Reject("invalid_value", f"{label}={value!r}")
        unit = (gd.get("unit") or "").strip()
        if not unit:
            raise Reject("missing_unit", label)
        f = unit_factor(code, unit)
        if f is None:
            raise Reject("unit_not_accepted", f"{label}: {unit!r} for {code}")
        flag_raw = (gd.get("flag") or "").strip()
        flag = ""
        if flag_raw:
            if flag_raw not in R["flags"]:
                raise Reject("unknown_flag", f"{label}: {flag_raw!r}")
            flag = R["flags"][flag_raw]
        ref = {}
        for k in ("ref_low", "ref_high"):
            rv = (gd.get(k) or "").strip()
            if rv:
                if not DECIMAL_RE.match(rv):
                    raise Reject("invalid_ref", f"{label} {k}={rv!r}")
                ref[k] = rv
        out.append({"label": label, "code": code, "value": value, "unit": unit,
                    "value_canonical": str(Decimal(value) * f), "unit_canonical": DICT["tests"][code]["ucum"],
                    "flag": flag, **ref})
    return out


def _has_time(fmt: str) -> bool:
    return any(d in fmt for d in ("%H", "%I", "%M"))


def execute(b: dict, normalized_text: str, spans: Optional[list] = None, region: Optional[list] = None,
            consumed: Optional[list] = None) -> dict:
    rec = {"binding_id": b["binding_id"], "binding_version": b.get("version")}
    for name in ("patient_id", "patient_name", "patient_age", "patient_sex", "collected", "reported"):
        v = _field(b, name, normalized_text, spans)
        rec[name] = v
    rec["results"] = _table(b, normalized_text, region, consumed)
    for k in ("collected", "reported"):
        if isinstance(rec[k], datetime):
            fmt = b["fields"][k]["format"]
            rec[k + "_precision"] = "datetime" if _has_time(fmt) else "date"
            if _has_time(fmt):                       # F-03: only emit a time if the document printed one
                rec[k + "_dt"] = rec[k].isoformat()
            rec[k] = rec[k].strftime("%Y-%m-%d")
    return rec


# ----------------------------------------------------------------------------- v3 structure checks
def ws(s: str) -> str:
    return " ".join(s.split())


def line_matches(pat: dict, line: str) -> bool:
    if "exact" in pat:
        return ws(line) == pat["exact"]
    try:
        return bool(_c(pat["regex"]).search(line, timeout=TIMEOUT))
    except TimeoutError:
        return False


def nonblank(lines: List[str], start: int = 0, stop: Optional[int] = None):
    stop = len(lines) if stop is None else stop
    return [i for i in range(start, stop) if lines[i].strip()]


def header_matches_at(b: dict, lines: List[str], start: int, n: int) -> bool:
    hdr = b["compiled"]["header"][:n]
    idx = nonblank(lines, start)[:len(hdr)]
    return len(idx) == len(hdr) and all(line_matches(p, lines[i]) for p, i in zip(hdr, idx))


def page1_ok(b: dict, lines: List[str]) -> bool:
    if "compiled" not in b:
        return False
    nb = nonblank(lines)
    return bool(nb) and header_matches_at(b, lines, nb[0], len(b["compiled"]["header"]))


def page_starts(b: dict, lines: List[str], ff_starts: List[int]) -> List[int]:
    """Page boundaries = form feeds + every recurrence of the identity line (continuous paper has no form feeds)."""
    C = b["compiled"]
    k = C["identity_index"]
    ident = C["header"][k]
    nb = nonblank(lines)
    first_ident = nb[k] if len(nb) > k else None
    starts = {nb[0]} if nb else set()
    starts |= {i for i in ff_starts if lines[i:] and nonblank(lines, i)}
    for pos, i in enumerate(nb):
        if i != first_ident and line_matches(ident, lines[i]):
            back = nb[max(0, pos - k)]
            starts.add(back)
    return sorted(starts)


def check_pages(b: dict, lines: List[str], ff_starts: List[int]) -> None:
    C = b["compiled"]
    st = page_starts(b, lines, ff_starts)
    for pno, s in enumerate(st[1:], start=2):
        nxt = st[pno] if pno < len(st) else len(lines)
        # a "page" that starts at a form feed but continues right after the previous page's text is still a page
        s_nb = nonblank(lines, s, nxt)
        if not s_nb:
            continue
        if C.get("continuation_len") is None:
            raise Reject("multipage_not_approved", f"page {pno}")
        if not header_matches_at(b, lines, s_nb[0], C["continuation_len"]):
            raise Reject("page_header_mismatch", f"page {pno} line {s_nb[0] + 1}")


def account_lines(b: dict, lines: List[str], region: List[int], spans: list, text: str) -> None:
    """Every non-blank line outside the table region must be explained. Unexplained content -> REJECT."""
    s, e = region
    starts, off = [], 0
    for ln in lines:
        starts.append(off)
        off += len(ln) + 1
    import bisect
    covered = set()
    for a, z in spans:
        la, lz = bisect.bisect_right(starts, a) - 1, bisect.bisect_right(starts, max(a, z - 1)) - 1
        covered.update(range(la, lz + 1))
    C = b["compiled"]
    tmpl = set(C["template_lines"])
    pats = [_c(p) for p in b["results"]["skip_lines"] + b["layout"]["anchors"] if not _c(p).search("")]
    for i in nonblank(lines):
        if s <= i <= e or i in covered:
            continue
        if ws(lines[i]) in tmpl:
            continue
        if any(line_matches(p, lines[i]) for p in C["header"]):
            continue
        if any(p.search(lines[i], timeout=TIMEOUT) for p in pats):
            continue
        raise Reject("unaccounted_line", f"line {i + 1}: {lines[i].strip()[:50]!r}")


def recognise_v3(bindings: List[dict], lines: List[str], text: str, mode: str) -> List[dict]:
    c = [b for b in bindings if matches_layout(b, text)]
    if mode != "anywhere":
        c = [b for b in c if page1_ok(b, lines)]
    return c


def process(bindings: List[dict], normalized_text: str, mode: str = "full",
            ff_starts: Optional[List[int]] = None) -> Outcome:
    """Full deterministic path: recognise -> structure checks -> extract -> independent validation."""
    if mode not in MODES:
        raise ValueError(f"unknown recognition mode {mode!r}")
    lines = normalized_text.split("\n")
    cands = recognise_v3(bindings, lines, normalized_text, mode)
    if not cands:
        return Outcome("REJECT", None, reasons=["unknown_layout"])
    if len(cands) > 1:
        return Outcome("REJECT", None, reasons=[f"ambiguous_layout: {[c['binding_id'] for c in cands]}"])
    b = cands[0]
    spans, region, consumed = [], [], []
    try:
        if mode in ("pos+pages", "full"):
            check_pages(b, lines, ff_starts or [])
        rec = execute(b, normalized_text, spans, region, consumed)
        if mode == "full":
            account_lines(b, lines, region, spans, normalized_text)
            # v3.1 (RV-1): binding-independent result sentinel over everything not consumed by a parsed row
            hits = sentinel.scan(normalized_text, consumed, b["results"]["labels"].keys())
            if hits:
                raise Reject("result_like_text_unparsed", hits[0])
    except Reject as r:
        return Outcome("REJECT", b["binding_id"], reasons=[f"{r.code}: {r.detail}"])
    except TimeoutError:
        return Outcome("REJECT", b["binding_id"], reasons=["regex_timeout"])
    issues = validators.validate(rec)
    if issues:
        return Outcome("REJECT", b["binding_id"], record=rec, reasons=issues)
    return Outcome("ACCEPT", b["binding_id"], record=rec)
