"""Deterministic benchmark. LLM calls are FORBIDDEN during this run (any attempt raises).

usage:
  python -m bench.run_benchmark --freeze          # write the freeze manifest (hashes of all system code)
  python -m bench.run_benchmark --split test      # evaluate; refuses to run if code changed after freeze
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

from spoolgeist import interpreter, llm, validators
from spoolgeist.grid import normalize
from bench.score import classify, field_checks

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "corpus"
RUNTIME = ROOT / "runtime"
FROZEN = ["spoolgeist/grid.py", "spoolgeist/interpreter.py", "spoolgeist/validators.py", "spoolgeist/dictionary.py",
          "spoolgeist/lab_dictionary.json", "spoolgeist/binding_schema.json", "spoolgeist/rulegen.py",
          "spoolgeist/llm.py", "bench/score.py", "bench/generator.py", "bench/run_benchmark.py"]
DEV, UNSEEN = ["A", "B", "C"], ["D", "E", "F"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze():
    m = {f: sha(ROOT / f) for f in FROZEN}
    m["_frozen_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (RUNTIME / "freeze_manifest.json").write_text(json.dumps(m, indent=1))
    print("frozen", len(FROZEN), "files")


def check_freeze():
    p = RUNTIME / "freeze_manifest.json"
    if not p.exists():
        raise SystemExit("no freeze manifest: run --freeze first")
    m = json.loads(p.read_text())
    changed = [f for f in FROZEN if m.get(f) != sha(ROOT / f)]
    if changed:
        raise SystemExit(f"code changed after freeze: {changed}")
    return m


def load_bindings():
    out = []
    for p in sorted((ROOT / "bindings").glob("*.v1.json")):
        b = json.loads(p.read_text())
        meta = b.pop("_meta", {})
        if meta.get("status") == "active":
            assert hashlib.sha256(json.dumps(b, sort_keys=True).encode()).hexdigest() == meta["sha256"], p
            out.append(b)
    return out


def upper95(k: int, n: int) -> float:
    """One-sided 95% upper confidence bound for a proportion (Clopper-Pearson; k=0 -> 1-0.05**(1/n))."""
    if n == 0:
        return float("nan")
    if k == 0:
        return 1 - 0.05 ** (1 / n)
    # simple Wilson upper bound for k>0
    z, p = 1.645, k / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def run(split: str, tag: str):
    manifest = check_freeze()
    bindings = load_bindings()
    llm.FORBID["enabled"] = True
    rows = []
    for lay_dir in sorted((CORPUS / split).iterdir()):
        for p in sorted(lay_dir.glob("*.json")):
            d = json.loads(p.read_text())
            raw = d["text"].encode()
            t0 = time.perf_counter()
            norm = normalize(raw)
            oc = interpreter.process(bindings, norm.text)
            ms = (time.perf_counter() - t0) * 1000
            cls = classify(oc.status, oc.record, d)
            # ablation: same extraction, independent validators switched off
            orig = validators.validate
            validators.validate = lambda rec, today=None: []
            try:
                oc_nv = interpreter.process(bindings, norm.text)
            finally:
                validators.validate = orig
            cls_nv = classify(oc_nv.status, oc_nv.record, d)
            recog = oc.binding_id
            row = {"doc_id": d["doc_id"], "layout": d["layout"], "perturbation": d["perturbation"],
                   "expected": d["expected"], "status": oc.status, "class": cls, "reasons": oc.reasons,
                   "recognised": recog, "expected_layout": d["expected_layout"], "ms": round(ms, 3),
                   "class_without_validators": cls_nv}
            if oc.status == "ACCEPT" and d["truth"]:
                row["fields"] = field_checks(oc.record, d["truth"])
                row["record"] = oc.record
            rows.append(row)
    llm.FORBID["enabled"] = False
    RUNTIME.mkdir(exist_ok=True)
    with (RUNTIME / f"bench_{tag}_rows.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    summary = summarise(rows, bindings)
    summary["freeze_manifest_time"] = manifest["_frozen_at"]
    summary["active_bindings"] = [b["binding_id"] for b in bindings]
    summary["llm_calls_during_run"] = 0
    (RUNTIME / f"bench_{tag}_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


def summarise(rows, bindings):
    active_layouts = {b["binding_id"].split("-")[1].upper() for b in bindings}

    def block(rs):
        c = Counter(r["class"] for r in rs)
        c_nv = Counter(r["class_without_validators"] for r in rs)
        accepted = [r for r in rs if r["status"] == "ACCEPT"]
        exp_acc = [r for r in rs if r["expected"] == "accept"]
        clean_valid = [r for r in rs if r["perturbation"] == "clean"]
        exp_rej = [r for r in rs if r["expected"] == "reject"]
        fields = [v for r in accepted if "fields" in r for v in r["fields"].values()]
        crit = [v for r in accepted if "fields" in r for k, v in r["fields"].items() if k.startswith("crit:")]
        rec_rows = [r for r in rs if r["perturbation"] in ("clean", "col_shift", "drop_optional", "page_break",
                                                            "crlf_trailing", "long_name", "header_changed") or r["layout"] == "G"]
        rec_ok = sum(1 for r in rec_rows if (r["recognised"] or None) == (r["expected_layout"] and f"lab-{r['expected_layout'].lower()}"))
        silent = c["silent_error"] + c["unsafe_accept"]
        silent_nv = c_nv["silent_error"] + c_nv["unsafe_accept"]
        ms = [r["ms"] for r in rs]
        return {
            "documents": len(rs),
            "outcomes": dict(c),
            "layout_recognition_accuracy": f"{rec_ok}/{len(rec_rows)}",
            "field_extraction_accuracy_on_accepted": f"{sum(fields)}/{len(fields)}",
            "critical_field_accuracy_on_accepted": f"{sum(crit)}/{len(crit)}",
            "silent_errors": silent,
            "silent_error_rate_of_accepted": f"{silent}/{len(accepted)}",
            "silent_error_95pct_upper_bound_of_accepted": round(upper95(silent, len(accepted)), 4) if accepted else None,
            "unsafe_accepts_of_invalid_docs": f"{c['unsafe_accept']}/{len(exp_rej)}",
            "false_rejection_rate_valid_docs": f"{c['false_reject']}/{len(exp_acc)}",
            "refusal_rate_clean_supported_docs": f"{sum(1 for r in clean_valid if r['status'] == 'REJECT')}/{len(clean_valid)}",
            "refusal_rate_all_docs": f"{sum(1 for r in rs if r['status'] == 'REJECT')}/{len(rs)}",
            "accepted_without_ai": f"{len(accepted)}/{len(rs)}",
            "latency_ms_median": round(statistics.median(ms), 2) if ms else None,
            "latency_ms_p95": round(sorted(ms)[int(0.95 * (len(ms) - 1))], 2) if ms else None,
            "ABLATION_silent_errors_without_validators": silent_nv,
            "ABLATION_outcomes_without_validators": dict(c_nv),
        }

    out = {"ALL": block(rows)}
    out["dev_layouts_ABC"] = block([r for r in rows if r["layout"] in DEV])
    out["unseen_layouts_DEF"] = block([r for r in rows if r["layout"] in UNSEEN])
    out["unregistered_G"] = block([r for r in rows if r["layout"] == "G"])
    for lay in DEV + UNSEEN:
        out[f"layout_{lay}{'' if lay in active_layouts else ' (NO ACTIVE BINDING)'}"] = block([r for r in rows if r["layout"] == lay])
    per_pert = defaultdict(Counter)
    for r in rows:
        per_pert[r["perturbation"]][r["class"]] += 1
    out["by_perturbation"] = {k: dict(v) for k, v in sorted(per_pert.items())}
    reasons = Counter(r["reasons"][0].split(":")[0] for r in rows if r["status"] == "REJECT" and r["reasons"])
    out["reject_reason_codes"] = dict(reasons.most_common())
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--split", default="test")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    if a.freeze:
        freeze()
    else:
        run(a.split, a.tag or a.split)
