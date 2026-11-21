"""bench2 evaluator: three-tier scoring (spec 02 sections 1 and 5). Sees only system outputs via an adapter.

usage (from poc/):
  .venv/bin/python -m bench2.evaluate --split dev --system v3.2 [--tag TAG]
  systems: v2.1 | v3.2 (= current spoolgeist_h, any version) | snapshot:<dir> (a spoolgeist_h snapshot)
"""
from __future__ import annotations

import argparse
import base64
import glob
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "phase2" / "stage3" / "results"


# ----------------------------------------------------------------------------- scoring
def _ws(s):
    return " ".join(str(s or "").split()).casefold()


def _dec(v):
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError):
        return None


def tiers(rec: dict, t: dict) -> dict:
    out = {}
    out["t1:patient_id"] = rec.get("patient_id") == t["patient_id"]
    out["t1:patient_name"] = _ws(rec.get("patient_name")) == _ws(t["patient_name"])
    out["t1:collected_date"] = rec.get("collected") == t["collected"]
    if t.get("collected_time"):
        out["t1:collected_time"] = (rec.get("collected_dt") or "")[11:16] == t["collected_time"]
    got = {x["code"]: x for x in rec.get("results") or []}
    exp = {x["code"]: x for x in t["results"]}
    out["t2:result_set"] = set(got) == set(exp)
    out["t2:values_units"] = all(c in got and _dec(got[c]["value"]) == _dec(x["value"]) and got[c]["unit"] == x["unit"]
                                 for c, x in exp.items())
    out["t3:sex"] = rec.get("patient_sex") == t["patient_sex"]
    out["t3:age"] = rec.get("patient_age") == t["patient_age"]
    out["t3:reported"] = (rec.get("reported") == t["reported"]) if t.get("reported") else True
    out["t3:precision"] = ("collected_dt" in rec and bool(rec.get("collected_dt"))) == bool(t.get("collected_time"))
    fl_ok, rr_ok = True, True
    for c, x in exp.items():
        g = got.get(c)
        if not g:
            continue
        gf, ef = (g.get("flag") or ""), (x.get("flag") or "")
        if t["flag_semantics"] == "direction":
            fl_ok &= gf == ef
        else:
            fl_ok &= bool(gf) == bool(ef)
        if "ref_low" in g:
            rr_ok &= _dec(g["ref_low"]) == _dec(x["ref_low"]) and _dec(g["ref_high"]) == _dec(x["ref_high"])
        else:
            rr_ok = False
    out["t3:flags"] = fl_ok
    out["t3:ref_ranges"] = rr_ok
    rn = [_ws(n) for n in rec.get("notes") or []]
    out["t3:notes_preserved"] = all(any(_ws(n) in r_ or r_ in _ws(n) for r_ in rn) for n in t.get("notes") or [])
    return out


def classify(doc: dict, status: str, rec) -> dict:
    g = doc["group"]
    if g == "valid":
        if status != "ACCEPT":
            return {"outcome": "false_reject"}
        tt = tiers(rec, doc["truth"])
        crit = all(v for k, v in tt.items() if k[:2] in ("t1", "t2"))
        ctx = all(v for k, v in tt.items() if k.startswith("t3"))
        return {"outcome": "correct_accept" if crit else "silent_error", "context_ok": ctx,
                "failed_fields": [k for k, v in tt.items() if not v]}
    if g == "policy":
        if status != "ACCEPT":
            return {"outcome": "policy_refusal"}
        tt = tiers(rec, doc["truth"])
        crit = all(v for k, v in tt.items() if k[:2] in ("t1", "t2"))
        return {"outcome": "policy_accept_correct" if crit else "policy_accept_WRONG",
                "failed_fields": [k for k, v in tt.items() if not v]}
    return {"outcome": "correct_reject" if status != "ACCEPT" else "unsafe_accept"}


# ----------------------------------------------------------------------------- systems
def adapter(name: str):
    if name == "v2.1":
        from bench.run_benchmark import load_bindings
        from spoolgeist import interpreter, llm
        from spoolgeist.grid import normalize
        llm.FORBID["enabled"] = True
        B = load_bindings()

        def run(raw, cp):
            oc = interpreter.process(B, normalize(raw).text)
            return oc.status, oc.binding_id, oc.record, oc.reasons
        return run, "v2.1 (bindings v1)"
    if name.startswith("snapshot:"):
        sys.path.insert(0, name.split(":", 1)[1])
    from spoolgeist_h import llm
    from spoolgeist_h.pipeline import Pipeline
    import inspect
    llm.FORBID["enabled"] = True
    P = Pipeline(allow_agent_approval=True)
    takes_cp = "codepage" in inspect.signature(P.process_bytes).parameters

    def run(raw, cp):
        oc = P.process_bytes(raw, codepage=cp) if takes_cp else P.process_bytes(raw)
        return oc.status, oc.binding_id, oc.record, oc.reasons
    import spoolgeist_h
    return run, f"{spoolgeist_h.__file__} bindings {[b['binding_id'] + ' v' + str(b['version']) for b in P.bindings]}"


# ----------------------------------------------------------------------------- run + summarise
def load_split(split):
    return [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / f"data/corpus2/{split}/*/*.json")))]


def upper95(k, n):
    if n == 0:
        return None
    if k == 0:
        return round(1 - 0.05 ** (1 / n), 4)
    z, p = 1.96, k / n
    return round((p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n), 4)


def evaluate(split, system):
    run, label = adapter(system)
    rows = []
    for d in load_split(split):
        raw = base64.b64decode(d["raw_b64"])
        t0 = time.perf_counter()
        status, bid, rec, reasons = run(raw, d["queue_codepage"])
        ms = (time.perf_counter() - t0) * 1000
        c = classify(d, status, rec)
        exp_b = None if d["group"] == "foreign" else f"lab-{d['layout'].lower()}"
        rows.append({"doc_id": d["doc_id"], "layout": d["layout"], "cls": d["cls"], "group": d["group"],
                     "status": status, "binding": bid, "recognised_ok": (bid == exp_b) if status == "ACCEPT" or d["group"] == "foreign" else None,
                     "reason": (reasons or [""])[0][:140], "ms": round(ms, 3), **c})
    return rows, label


def summarise(rows):
    S = {}
    by_cls = defaultdict(Counter)
    for r in rows:
        by_cls[f"{r['group']}:{r['cls']}"][r["outcome"]] += 1
        by_cls[f"{r['group']}:{r['cls']}"]["n"] += 1
        if r["outcome"] == "correct_accept" and not r.get("context_ok", True):
            by_cls[f"{r['group']}:{r['cls']}"]["context_error"] += 1
    S["per_class"] = {k: dict(v) for k, v in sorted(by_cls.items())}
    for g in ("valid", "policy", "defect", "foreign"):
        rs = [r for r in rows if r["group"] == g]
        S[f"group_{g}"] = dict(Counter(r["outcome"] for r in rs), n=len(rs))
    for part, lays in (("ABC", "ABC"), ("DEF", "DEF")):
        rs = [r for r in rows if r["layout"] in lays and r["group"] != "foreign"]
        S[f"layouts_{part}"] = dict(Counter(f"{r['group']}:{r['outcome']}" for r in rs))
    val = [r for r in rows if r["group"] == "valid"]
    acc = [r for r in val if r["status"] == "ACCEPT"]
    bad = [r for r in rows if r["group"] in ("defect", "foreign")]
    unsafe = sum(1 for r in bad if r["outcome"] == "unsafe_accept")
    silent = sum(1 for r in val if r["outcome"] == "silent_error")
    fields = Counter(f for r in acc for f in r.get("failed_fields", []))
    S["headline"] = {
        "valid_correct_accept": f"{sum(1 for r in val if r['outcome'] == 'correct_accept')}/{len(val)}",
        "valid_false_reject": f"{sum(1 for r in val if r['outcome'] == 'false_reject')}/{len(val)}",
        "silent_errors_of_accepted_valid": f"{silent}/{len(acc)}", "silent_upper95": upper95(silent, len(acc)),
        "context_errors_of_correct_accepts": f"{sum(1 for r in val if r['outcome'] == 'correct_accept' and not r.get('context_ok'))}/{sum(1 for r in val if r['outcome'] == 'correct_accept')}",
        "unsafe_accepts_defect_and_foreign": f"{unsafe}/{len(bad)}", "unsafe_upper95": upper95(unsafe, len(bad)),
        "policy_refusals": f"{sum(1 for r in rows if r['outcome'] == 'policy_refusal')}/{sum(1 for r in rows if r['group'] == 'policy')}",
        "policy_accept_WRONG": sum(1 for r in rows if r["outcome"] == "policy_accept_WRONG"),
        "failed_fields_on_accepted_valid": dict(fields),
        "recognition_ok_on_accepted": f"{sum(1 for r in acc if r['recognised_ok'])}/{len(acc)}",
        "latency_ms_median": round(statistics.median(r["ms"] for r in rows), 3),
        "latency_ms_p95": round(sorted(r["ms"] for r in rows)[int(0.95 * (len(rows) - 1))], 3),
        "llm_calls": 0,
    }
    S["unsupported_valid_classes(>50% FR)"] = [k for k, v in S["per_class"].items()
                                               if k.startswith("valid:") and v.get("false_reject", 0) > 0.5 * v["n"]]
    return S


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--system", default="v3.2")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    rows, label = evaluate(a.split, a.system)
    s = summarise(rows)
    s["system"], s["split"] = label, a.split
    tag = a.tag or f"{a.split}_{a.system.replace(':', '_').replace('/', '_')}"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"eval_{tag}_rows.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    (OUT / f"eval_{tag}_summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
    print(json.dumps(s["headline"], indent=1, ensure_ascii=False))
    print("unsupported:", s["unsupported_valid_classes(>50% FR)"])
