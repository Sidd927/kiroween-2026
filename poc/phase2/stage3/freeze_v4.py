"""Freeze manifest for v4 (Stage 3). Covers system code, bindings, registry, gate reports, LLM candidates, the bench2
generator and evaluator, tests, Stage-3 runners, the design spec and the gen/dev corpus.
usage: .venv/bin/python -m phase2.stage3.freeze_v4 --freeze | --check"""
import argparse, hashlib, json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "phase2/stage3/freeze_manifest_v4.json"
GLOBS = ["spoolgeist_h/*.py", "spoolgeist_h/*.json", "bindings_h/*.json", "bindings_h/approvals.jsonl",
         "bindings_h/gate_reports/*.json", "bindings_h/candidates/*.json", "bench2/*.py", "tests_h/*.py",
         "tests/test_property_abstain_or_correct.py", "bench/generator.py", "bench/score.py",
         "phase2/stage3/*.py", "phase2/02_BENCHMARK_DESIGN.md", "data/corpus2/gen/*/*.json", "data/corpus2/dev/*/*.json"]


def files():
    return sorted({str(p.relative_to(ROOT)) for g in GLOBS for p in ROOT.glob(g)})


def sha(f):
    return hashlib.sha256((ROOT / f).read_bytes()).hexdigest()


def check():
    m = json.loads(MANIFEST.read_text())
    cur = files()
    changed = [f for f in cur if m["files"].get(f) != sha(f)]
    gone = [f for f in m["files"] if f not in cur]
    if changed or gone:
        raise SystemExit(f"v4 changed after freeze: changed={changed[:10]} removed={gone[:10]}")
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--freeze", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.freeze:
        fs = files()
        m = {"frozen_at": time.strftime("%Y-%m-%d %H:%M:%S %z"), "n_files": len(fs), "files": {f: sha(f) for f in fs}}
        m["manifest_sha256"] = hashlib.sha256(json.dumps(m["files"], sort_keys=True).encode()).hexdigest()
        MANIFEST.write_text(json.dumps(m, indent=1))
        print("frozen", len(fs), "files; manifest", m["manifest_sha256"][:16])
    else:
        m = check()
        print("v4 freeze valid:", m["n_files"], "files, frozen", m["frozen_at"])
