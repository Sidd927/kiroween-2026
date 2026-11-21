"""Activation gate v2 (F-08). Every condition is an executable check; the report lists each one.

A candidate binding can only become active through registry.approve(), which requires a PASSED gate report for
the exact binding SHA-256, acknowledgement of every warning, and date-format confirmation where the samples do
not disambiguate DD/MM vs MM/DD. Producing valid JSON is never enough.

Inputs are operator-verified documents (with expected outcome and ground truth): the generation samples, the dev
regression set (clean + valid variations + one document per applicable defect class). The held-out test split and
the Phase-2 adversarial suite are never used here.

Conditions
  G1 static      schema, regex compile, required groups, codes exist (v2 static_check) + compiled section present
  G2 compiled    compiler produced a page-1 header with an identity line; >= MIN_CLEAN approved clean samples
  G3 regression  on dev docs (generation samples EXCLUDED): 0 silent errors, 0 unsafe accepts, evaluated together
                 with every already-active binding
  G4 clean       dev clean acceptance >= ceil(90%) (generation samples excluded from the denominator)
  G5 variations  every valid-variation class in dev is reported; a rejected class becomes a warning that the
                 approver must acknowledge ("unsupported variation")
  G6 self-adv    generic structural mutations of the approved clean samples must ALL be rejected
                 (v3.1: includes a result appended to every line the binding trusts: skip/anchor/field lines)
  G7 collision   candidate must not recognise any active binding's approved samples, and no active binding may
                 recognise the candidate's samples
  G8 dates       day/month-order formats must be disambiguated by the samples, else approval needs confirmation
  G9 coverage    >= MIN_INVALID defect documents; multi-page coverage warning if no approved multi-page sample
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List

from .grid import normalize
from .interpreter import _c, nonblank, page_starts, process, static_check
from .registry import canonical_sha

MIN_CLEAN, MIN_INVALID = 8, 5
VALID_VARIATIONS = ("col_shift", "drop_optional", "page_break", "crlf_trailing", "long_name")


def _classify(status, rec, doc):
    from bench.score import classify
    return classify(status, rec, doc)


def _region(b, lines):
    s = next((i for i, l in enumerate(lines) if _c(b["results"]["start"]).search(l)), None)
    e = next((i for i in range(s + 1, len(lines)) if _c(b["results"]["end"]).search(lines[i])), None) if s is not None else None
    return s, e


def mutations(b: dict, text: str, other_text: str) -> Dict[str, str]:
    """Generic structural defects. Uses only the candidate binding and the sample itself."""
    n = normalize(text.encode())
    L = list(n.lines)
    s, e = _region(b, L)
    out = {}
    C = b["compiled"]
    nb = nonblank(L)
    ident_line = nb[C["identity_index"]]
    m = list(L); m[ident_line] = "ACME DIAGNOSTICS - NEW REPORT FORMAT"; out["identity_line_replaced"] = "\n".join(m)
    if len(C["header"]) > 2:
        m = list(L); del m[nb[1]]; out["header_line_dropped"] = "\n".join(m)
    if s is not None and e is not None:
        m = list(L); m.insert(e + 1, "UNEXPECTED LINE 4471 12.5"); out["unknown_line_after_end"] = "\n".join(m)
        # v3.2: digit-free unexplained text too (the numeric rule would otherwise mask a permissive skip regex)
        m = list(L); m.insert(e + 1, "UNEXPECTED REMARK TEXT"); out["unknown_text_line_after_end"] = "\n".join(m)
        m = list(L); m.insert(s + 1, "UNEXPECTED REMARK TEXT"); out["unknown_text_line_in_table"] = "\n".join(m)
        m = list(L); m.insert(s, "UNEXPECTED LINE 4471 12.5"); out["unknown_line_before_start"] = "\n".join(m)
        m = list(L); m.insert(s + 1, "UNEXPECTED LINE 4471 12.5"); out["unknown_line_in_table"] = "\n".join(m)
        # the column header is the start line if it has text; otherwise (start = a separator) the nearest text line above
        ch = s if sum(c.isalpha() for c in L[s]) >= 3 else next((i for i in range(s - 1, -1, -1) if sum(c.isalpha() for c in L[i]) >= 3), s)
        m = list(L); m[ch] = m[ch][: max(1, len(m[ch].rstrip()) // 2)]; out["column_header_truncated"] = "\n".join(m)
        from .dictionary import DICT
        units = sorted({u for t in DICT["tests"].values() for u in t["units"]}, key=len, reverse=True)
        for i in range(s + 1, e):
            hit = next((u for u in units if f" {u}" in L[i] and len(u) >= 2), None)
            if hit:
                m = list(L); m[i] = L[i].replace(f" {hit}", " " * (len(hit) + 1), 1); out["unit_deleted"] = "\n".join(m)
                break
    # v3.1 (RV-1): a result smuggled onto lines the binding trusts must still be rejected
    SMUG = "   SODIUM 138 mmol/L"
    if s is not None and e is not None:
        trusted = [p for p in b["results"]["skip_lines"] + b["layout"]["anchors"] if not _c(p).search("")]
        for k, pat in enumerate(trusted):
            src = next((ln for ln in L if ln.strip() and _c(pat).search(ln)), None)
            if src is None:
                continue
            m = list(L); m.insert(e + 1, src + SMUG); out[f"result_on_trusted_line_after_end:{k}"] = "\n".join(m)
            m = list(L); m.insert(s + 1, src + SMUG); out[f"result_on_trusted_line_in_table:{k}"] = "\n".join(m)
            # v3.2: vocabulary-free smuggle (no unit, no known analyte) must also be rejected
            m = list(L); m.insert(e + 1, src + "   QX 42"); out[f"bare_number_on_trusted_line_after_end:{k}"] = "\n".join(m)
            m = list(L); m.insert(s + 1, src + "   QX 42"); out[f"bare_number_on_trusted_line_in_table:{k}"] = "\n".join(m)
        pid = next((i for i, ln in enumerate(L) if _c(b["fields"]["patient_id"]["regex"]).search(ln)), None)
        if pid is not None:
            m = list(L); m[pid] = L[pid] + SMUG; out["result_on_field_line"] = "\n".join(m)
            m = list(L); m[pid] = L[pid] + "   QX 42"; out["bare_number_on_field_line"] = "\n".join(m)
    out["two_reports_one_job"] = text + "\n" + other_text
    st = page_starts(b, L, n.ff_page_starts)
    if len(st) >= 2:
        p1, p2 = L[st[0]:st[1]], L[st[1]:(st[2] if len(st) > 2 else len(L))]
        rest = L[st[2]:] if len(st) > 2 else []
        out["pages_swapped"] = "\n".join(p2 + p1 + rest)
    return out


def run_gate(candidate: dict, gen_docs: List[dict], dev_docs: List[dict], active: List[dict],
             active_samples: Dict[str, List[dict]], compile_report: dict) -> dict:
    rep = {"binding_id": candidate["binding_id"], "version": candidate.get("version"),
           "binding_sha256": canonical_sha(candidate), "conditions": {}, "warnings_requiring_ack": [],
           "date_format_confirmation_required": False}
    C = rep["conditions"]
    llm_part = {k: v for k, v in candidate.items() if k not in ("compiled", "version")}
    errs = static_check(llm_part)
    C["G1_static"] = {"passed": not errs and "compiled" in candidate, "errors": errs}
    n_clean = compile_report.get("n_clean", 0)
    C["G2_compiled"] = {"passed": not compile_report.get("errors") and n_clean >= MIN_CLEAN,
                        "errors": compile_report.get("errors"), "approved_clean_samples": n_clean}
    if not C["G2_compiled"]["passed"] or candidate["compiled"].get("identity_index") is None:
        for k in ("G3_regression", "G4_clean_acceptance", "G5_variations", "G6_self_adversarial", "G7_collision",
                  "G8_dates", "G9_coverage"):
            C[k] = {"passed": False, "note": "not evaluated: compilation failed (fail closed)"}
        rep["passed"] = False
        return rep
    others = [b for b in active if b["binding_id"] != candidate["binding_id"]]
    bset = [candidate] + others
    gen_ids = {d["doc_id"] for d in gen_docs}
    dev = [d for d in dev_docs if d["doc_id"] not in gen_ids]
    counts, fails, var = Counter(), [], {}
    for d in dev:
        n = normalize(d["text"].encode())
        oc = process(bset, n.text, "full", n.ff_page_starts)
        cls = _classify(oc.status, oc.record, d)
        counts[cls] += 1
        if cls in ("silent_error", "unsafe_accept"):
            fails.append({"doc_id": d["doc_id"], "cls": cls, "reasons": oc.reasons})
        if d["perturbation"] in VALID_VARIATIONS:
            var.setdefault(d["perturbation"], Counter())[oc.status] += 1
    C["G3_regression"] = {"passed": counts["silent_error"] == 0 and counts["unsafe_accept"] == 0,
                          "counts": dict(counts), "failures": fails, "n_docs": len(dev)}
    clean = [d for d in dev if d["perturbation"] == "clean"]
    ok = 0
    for d in clean:
        n = normalize(d["text"].encode())
        oc = process(bset, n.text, "full", n.ff_page_starts)
        ok += _classify(oc.status, oc.record, d) == "correct_accept"
    need = math.ceil(0.9 * len(clean))
    C["G4_clean_acceptance"] = {"passed": len(clean) > 0 and ok >= need, "accepted": ok, "of": len(clean), "required": need}
    unsupported = [k for k, v in var.items() if v.get("REJECT")]
    rep["warnings_requiring_ack"] += [f"unsupported_variation:{k}" for k in sorted(unsupported)]
    C["G5_variations"] = {"passed": True, "per_class": {k: dict(v) for k, v in var.items()},
                          "unsupported": unsupported, "note": "rejections are safe but must be acknowledged"}
    approved_clean = [d for d in gen_docs + clean]
    mres, mfail = Counter(), []
    for i, d in enumerate(approved_clean[:4]):
        other = approved_clean[(i + 1) % len(approved_clean)]["text"]
        for name, t in mutations(candidate, d["text"], other).items():
            n = normalize(t.encode())
            oc = process(bset, n.text, "full", n.ff_page_starts)
            mres[f"{name}:{oc.status}"] += 1
            if oc.status == "ACCEPT":
                mfail.append({"doc": d["doc_id"], "mutation": name})
    C["G6_self_adversarial"] = {"passed": not mfail, "results": dict(mres), "accepted_mutations": mfail}
    coll = []
    for bid, docs in active_samples.items():
        if bid == candidate["binding_id"]:
            continue
        for d in docs:
            n = normalize(d["text"].encode())
            if process([candidate], n.text, "full", n.ff_page_starts).binding_id == candidate["binding_id"]:
                coll.append(f"candidate recognises {bid} sample {d['doc_id']}")
    for d in gen_docs + clean:
        n = normalize(d["text"].encode())
        for ob in others:
            if process([ob], n.text, "full", n.ff_page_starts).binding_id == ob["binding_id"]:
                coll.append(f"active {ob['binding_id']} recognises candidate sample {d['doc_id']}")
    C["G7_collision"] = {"passed": not coll, "collisions": coll[:10]}
    dates = candidate["compiled"].get("date_formats", {})
    amb = [k for k, v in dates.items() if v["day_month_order_ambiguous_format"] and not v["samples_disambiguate"]]
    rep["date_format_confirmation_required"] = bool(amb)
    C["G8_dates"] = {"passed": True, "ambiguous_fields": amb, "formats": dates,
                     "note": "approval requires --confirm-date-format when ambiguous_fields is non-empty"}
    n_invalid = sum(1 for d in dev if d["expected"] == "reject")
    for sk in compile_report.get("generic_numeric_skeletons", []):
        rep["warnings_requiring_ack"].append(f"generic_numeric_skeleton:{sk}")
    if candidate["compiled"].get("continuation_len") is None:
        rep["warnings_requiring_ack"].append("multipage_documents_rejected")
    C["G9_coverage"] = {"passed": n_invalid >= MIN_INVALID, "invalid_docs": n_invalid,
                        "defect_classes": sorted({d["perturbation"] for d in dev if d["expected"] == "reject"})}
    rep["passed"] = all(v["passed"] for v in C.values())
    return rep
