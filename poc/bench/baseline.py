"""Baseline: DIRECT LLM extraction of every document (no binding), same held-out docs, same scoring.

Arms reported:
  direct_llm               : LLM output taken as-is (LLM may itself REJECT)
  direct_llm_+_validators  : LLM output, then Spoolgeist's independent validators (V1-V8)
usage: python -m bench.baseline --per-layout-clean 5 --workers 6
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

from spoolgeist import llm, validators
from spoolgeist.dictionary import DICT, unit_factor
from spoolgeist.grid import normalize
from spoolgeist.rulegen import TARGET_FIELDS, dictionary_text
from bench.score import classify

ROOT = Path(__file__).resolve().parents[1]

PROMPT = """Extract structured data from this printed laboratory report (normalised text of a print job).
{fields}
Canonical test dictionary (use these codes; the unit must be copied exactly as printed and must be one of the accepted
spellings, otherwise reject):
{dictionary}

Rules: copy values exactly as printed. Do not guess, infer or fill in anything that is not printed. If the document is
malformed, truncated, ambiguous, internally inconsistent, missing a required field or unit, contains an unknown test,
an impossible value or date, or you are not certain, return status "REJECT" with reasons. Otherwise return "ACCEPT".

Return ONLY a JSON object:
{{"status": "ACCEPT"|"REJECT", "reasons": [..], "patient_id": str|null, "patient_name": str|null,
  "patient_age": int|null, "patient_sex": "male"|"female"|null, "collected": "YYYY-MM-DD"|null,
  "reported": "YYYY-MM-DD"|null,
  "results": [{{"label": str, "code": str, "value": str, "unit": str, "ref_low": str|null, "ref_high": str|null,
               "flag": "H"|"L"|"A"|""}}]}}

<report>
{doc}
</report>"""


def sample_docs(per_clean: int, seed: int = 7):
    rng = random.Random(seed)
    out = []
    for lay in "ABCDEF":
        docs = [json.loads(p.read_text()) for p in sorted((ROOT / "data/corpus/test" / lay).glob("*.json"))]
        clean = [d for d in docs if d["perturbation"] == "clean"]
        out += rng.sample(clean, per_clean)
        by_p = {}
        for d in docs:
            if d["perturbation"] != "clean":
                by_p.setdefault(d["perturbation"], d)   # first instance of each perturbation type
        out += list(by_p.values())
    return out


def run_one(d):
    text = normalize(d["text"].encode()).text
    p = PROMPT.format(fields=TARGET_FIELDS, dictionary=dictionary_text(), doc=text)
    t0 = time.time()
    try:
        resp = llm.call(p, [text], purpose=f"baseline:{d['doc_id']}", model="sonnet",
                        system="You are a careful clinical data abstractor. Output only JSON.")
        out = llm.extract_json(resp["text"])
    except Exception as e:
        return {"doc_id": d["doc_id"], "error": str(e)[:300]}
    secs = time.time() - t0
    status = "ACCEPT" if out.get("status") == "ACCEPT" else "REJECT"
    rec = {k: out.get(k) for k in ("patient_id", "patient_name", "patient_age", "patient_sex", "collected", "reported")}
    rec["results"] = [r for r in (out.get("results") or []) if isinstance(r, dict)]
    cls = classify(status, rec, d)
    # arm 2: same LLM record + Spoolgeist's independent validators
    issues = []
    try:
        for r in rec["results"]:
            r["value"] = str(r.get("value"))
            for k in ("ref_low", "ref_high"):
                if r.get(k) in ("", None):
                    r.pop(k, None)
            Decimal(r["value"])
        issues = validators.validate(rec)
    except Exception as e:
        issues = [f"unparseable: {e}"]
    status2 = "ACCEPT" if status == "ACCEPT" and not issues else "REJECT"
    cls2 = classify(status2, rec, d)
    return {"doc_id": d["doc_id"], "layout": d["layout"], "perturbation": d["perturbation"], "expected": d["expected"],
            "status": status, "class": cls, "reasons": out.get("reasons"), "class_with_validators": cls2,
            "validator_issues": issues, "seconds": round(secs, 1), "cost_usd": resp.get("cost_usd"), "record": rec}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-layout-clean", type=int, default=5)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    docs = sample_docs(a.per_layout_clean)
    print("baseline docs:", len(docs), flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(run_one, docs))
    with (ROOT / "runtime/baseline_rows.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    ok = [r for r in rows if "error" not in r]
    summ = {"documents": len(docs), "llm_errors": len(rows) - len(ok)}
    for arm, key in (("direct_llm", "class"), ("direct_llm_plus_validators", "class_with_validators")):
        c = Counter(r[key] for r in ok)
        acc = c["correct_accept"] + c["silent_error"] + c["unsafe_accept"]
        summ[arm] = {"outcomes": dict(c), "silent_errors": c["silent_error"] + c["unsafe_accept"],
                     "silent_error_rate_of_accepted": f"{c['silent_error'] + c['unsafe_accept']}/{acc}",
                     "false_rejects": f"{c['false_reject']}/{sum(1 for r in ok if r['expected'] == 'accept')}",
                     "clean_refusals": f"{sum(1 for r in ok if r['perturbation'] == 'clean' and r[key] == 'false_reject')}/{sum(1 for r in ok if r['perturbation'] == 'clean')}"}
    summ["median_seconds_per_doc"] = sorted(r["seconds"] for r in ok)[len(ok) // 2] if ok else None
    summ["total_cost_usd"] = round(sum(r.get("cost_usd") or 0 for r in ok), 3)
    summ["llm_calls"] = len(rows)
    (ROOT / "runtime/baseline_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))
