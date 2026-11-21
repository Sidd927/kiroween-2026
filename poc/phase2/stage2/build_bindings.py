"""Stage 2: compile the six LLM-written v1 bindings into v3 candidates, run gate v2, and record approvals.

No LLM call. The v1 bindings in bindings/ are read, never modified.

Approval: the registry needs an approver. No human has reviewed these bindings, so for the experiment this script
records approver_kind="agent" with an explicit note. The v3 pipeline refuses agent approvals unless
allow_agent_approval=True is passed, so these approvals cannot silently become production approvals.

usage (from poc/): .venv/bin/python -m phase2.stage2.build_bindings [--approve-as-agent]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from spoolgeist_h.approval import approve_binding, gate_binding, ref_for   # noqa: E402
from spoolgeist_h.compile import compile_binding     # noqa: E402
from spoolgeist_h.registry import DEFAULT_DIR, Registry, canonical_sha, load_approved  # noqa: E402

VERSION = 5   # v3.2 system: + numeric_skeletons (v4 = v3.1 provenance; v3 = v3.0)
GATE_DIR = DEFAULT_DIR / "gate_reports"
AGENT = "AGENT claude-opus-5-5 (Phase 2 experiment; NOT a human review)"


def corpus(split, lay):
    return [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / f"data/corpus/{split}/{lay}/*.json")))]


def paths(split, lay):
    return sorted(glob.glob(str(ROOT / f"data/corpus/{split}/{lay}/*.json")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve-as-agent", action="store_true")
    a = ap.parse_args()
    GATE_DIR.mkdir(parents=True, exist_ok=True)
    reg = Registry()
    samples = {}
    for lay in "ABCDEF":
        gen, dev = corpus("gen", lay), corpus("dev", lay)
        samples[f"lab-{lay.lower()}"] = [d for d in gen + dev if d["expected"] == "accept" and d["perturbation"] == "clean"]
    summary = {}
    for lay in "ABCDEF":
        bid = f"lab-{lay.lower()}"
        v1 = json.loads((ROOT / "bindings" / f"{bid}.v1.json").read_text())
        v1.pop("_meta")
        reg_paths = paths("gen", lay) + paths("dev", lay)
        reg_docs = [json.load(open(p)) for p in reg_paths]
        appr = [(p, d) for p, d in zip(reg_paths, reg_docs) if d["expected"] == "accept"]
        cand, crep = compile_binding(v1, [d for _, d in appr], VERSION, [ref_for(p) for p, _ in appr],
                                     [ref_for(p) for p in reg_paths])
        f = DEFAULT_DIR / f"{bid}.v{VERSION}.json"
        if f.exists() and canonical_sha(json.loads(f.read_text())) != canonical_sha(cand):
            raise SystemExit(f"{f.name} exists with different content; bump VERSION instead of overwriting")
        f.write_text(json.dumps(cand, indent=1, ensure_ascii=False))
        if a.approve_as_agent:
            already = any(e["action"] == "approve" and e["binding_sha256"] == canonical_sha(cand) for e in reg.entries())
            if not already:
                g, _ = gate_binding(cand)
                approve_binding(f, AGENT, "agent", g["warnings_requiring_ack"], date_confirmed=False,
                                note="experiment approval; gate re-run at approval; warnings acknowledged by the agent, not by a human")
        g, _ = gate_binding(cand)
        gf = GATE_DIR / f"{bid}.v{VERSION}.gate.json"
        gf.write_text(json.dumps(g, indent=1, default=str))
        summary[bid] = {"passed": g["passed"], "failed": [k for k, v in g["conditions"].items() if not v["passed"]],
                        "warnings": g["warnings_requiring_ack"], "date_confirm": g["date_format_confirmation_required"],
                        "G6_accepted": g["conditions"]["G6_self_adversarial"].get("accepted_mutations"),
                        "G6_n": sum(g["conditions"]["G6_self_adversarial"].get("results", {}).values())}
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
