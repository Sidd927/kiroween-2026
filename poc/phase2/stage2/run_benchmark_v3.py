"""Run the ORIGINAL held-out benchmark (data/corpus/test, 326 docs) against v3, reusing the frozen v2.1 scoring and
summary code unchanged, so v2.1 and v3 numbers are directly comparable. Refuses to run if v3 changed after its
freeze manifest (phase2/stage2/freeze_manifest_v3.json). LLM calls are forbidden.

usage: .venv/bin/python -m phase2.stage2.run_benchmark_v3 [--freeze] [--split test] [--tag TAG]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bench.run_benchmark import summarise           # noqa: E402  (frozen v2.1 summary code)
from bench.score import classify, field_checks      # noqa: E402
from spoolgeist_h import llm, validators            # noqa: E402
from spoolgeist_h.pipeline import Pipeline          # noqa: E402

OUT = ROOT / "phase2" / "stage2" / "results"
MANIFEST = ROOT / "phase2" / "stage2" / "freeze_manifest_v3.json"
FROZEN_GLOBS = ["spoolgeist_h/*.py", "spoolgeist_h/*.json", "bindings_h/*.json", "bindings_h/approvals.jsonl",
                "bindings_h/gate_reports/*.json", "bench/score.py", "bench/generator.py", "bench/run_benchmark.py",
                "phase2/suites/adversarial.py", "tests_h/*.py", "tests/test_property_abstain_or_correct.py",
                "phase2/stage2/run_benchmark_v3.py", "phase2/stage2/build_bindings.py", "phase2/stage2/redteam_v3.py",
                "phase2/stage2/redteam_v31.py", "phase2/stage2/redteam_v31_evasion.py", "phase2/stage2/heldout_evasion_v2.py"]


def files():
    return sorted({str(p.relative_to(ROOT)) for g in FROZEN_GLOBS for p in ROOT.glob(g)})


def freeze():
    m = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files()}
    m["_frozen_at"] = time.strftime("%Y-%m-%d %H:%M:%S %z")
    MANIFEST.write_text(json.dumps(m, indent=1))
    print("frozen", len(m) - 1, "files")


def check():
    m = json.loads(MANIFEST.read_text())
    cur = files()
    changed = [f for f in cur if m.get(f) != hashlib.sha256((ROOT / f).read_bytes()).hexdigest()]
    gone = [f for f in m if not f.startswith("_") and f not in cur]
    if changed or gone:
        raise SystemExit(f"v3 changed after freeze: changed={changed} removed={gone}")
    return m


def run(split, tag):
    m = check()
    P = Pipeline(allow_agent_approval=True)
    llm.FORBID["enabled"] = True
    rows = []
    for lay_dir in sorted((ROOT / "data" / "corpus" / split).iterdir()):
        for p in sorted(lay_dir.glob("*.json")):
            d = json.loads(p.read_text())
            t0 = time.perf_counter()
            oc = P.process_bytes(d["text"].encode())
            ms = (time.perf_counter() - t0) * 1000
            orig = validators.validate
            validators.validate = lambda rec, today=None: []
            try:
                oc_nv = P.process_bytes(d["text"].encode())
            finally:
                validators.validate = orig
            row = {"doc_id": d["doc_id"], "layout": d["layout"], "perturbation": d["perturbation"],
                   "expected": d["expected"], "status": oc.status, "class": classify(oc.status, oc.record, d),
                   "reasons": oc.reasons, "recognised": oc.binding_id, "expected_layout": d["expected_layout"],
                   "ms": round(ms, 3), "class_without_validators": classify(oc_nv.status, oc_nv.record, d)}
            if oc.status == "ACCEPT" and d["truth"]:
                row["fields"] = field_checks(oc.record, d["truth"])
            rows.append(row)
    llm.FORBID["enabled"] = False
    s = summarise(rows, P.bindings)
    s["freeze_manifest_v3"] = m["_frozen_at"]
    s["active_bindings"] = {b["binding_id"]: b["version"] for b in P.bindings}
    s["approval_note"] = "bindings approved by an AI agent for this experiment (approver_kind=agent), not by a human"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"bench_v3_{tag}_rows.jsonl").write_text("\n".join(json.dumps(r, default=str) for r in rows) + "\n")
    (OUT / f"bench_v3_{tag}_summary.json").write_text(json.dumps(s, indent=1))
    print(json.dumps(s["ALL"], indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--split", default="test")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    freeze() if a.freeze else run(a.split, a.tag or a.split)
