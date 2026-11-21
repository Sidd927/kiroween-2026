"""Stage 3: compile the six LLM-written v1 bindings (unchanged LLM output) into v6 candidates from the bench2
operator-verified samples (data/corpus2 gen + dev), run gate v2 (re-run at approval), record agent approvals.
No LLM call. usage: .venv/bin/python -m phase2.stage3.build_bindings_v6 [--approve-as-agent]"""
import argparse, glob, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from spoolgeist_h.approval import approve_binding, gate_binding, ref_for
from spoolgeist_h.compile import compile_binding
from spoolgeist_h.registry import DEFAULT_DIR, Registry, canonical_sha

VERSION = 7   # v6 candidates were superseded before approval (note-continuation bug, EXPERIMENT_LOG 57)
AGENT = "AGENT claude-opus-5-5 (Phase 2 experiment; NOT a human review)"


def paths(split, lay):
    return sorted(glob.glob(str(ROOT / f"data/corpus2/{split}/{lay}/*.json")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve-as-agent", action="store_true")
    ap.add_argument("--only", nargs="*", default=list("ABCDEF"))
    ap.add_argument("--version", type=int, default=VERSION)
    ap.add_argument("--use-repaired", action="store_true",
                    help="LLM source = bindings_h/candidates/<id>.llm-repair-longname.json instead of bindings/<id>.v1.json")
    ap.add_argument("--source", default=None, help="explicit LLM source file (single layout)")
    a = ap.parse_args()
    reg = Registry()
    summary = {}
    for lay in a.only:
        bid = f"lab-{lay.lower()}"
        if a.source:
            v1 = json.loads(Path(a.source).read_text())
        elif a.use_repaired:
            v1 = json.loads((DEFAULT_DIR / "candidates" / f"{bid}.llm-repair-longname.json").read_text())
        else:
            v1 = json.loads((ROOT / "bindings" / f"{bid}.v1.json").read_text())
            v1.pop("_meta")
        reg_paths = paths("gen", lay) + paths("dev", lay)
        docs = [json.load(open(p)) for p in reg_paths]
        appr = [(p, d) for p, d in zip(reg_paths, docs) if d["expected"] == "accept"]
        cand, crep = compile_binding(v1, [d for _, d in appr], a.version, [ref_for(p) for p, _ in appr], [ref_for(p) for p in reg_paths])
        f = DEFAULT_DIR / f"{bid}.v{a.version}.json"
        if f.exists() and canonical_sha(json.loads(f.read_text())) != canonical_sha(cand):
            raise SystemExit(f"{f.name} exists with different content; bump VERSION")
        f.write_text(json.dumps(cand, indent=1, ensure_ascii=False))
        g, _ = gate_binding(cand)
        if a.approve_as_agent and g["passed"] and not any(e["action"] == "approve" and e["binding_sha256"] == canonical_sha(cand) for e in reg.entries()):
            approve_binding(f, AGENT, "agent", g["warnings_requiring_ack"], date_confirmed=False,
                            note="experiment approval on bench2 samples; NOT a human review")
        (DEFAULT_DIR / "gate_reports" / f"{bid}.v{a.version}.gate.json").write_text(json.dumps(g, indent=1, default=str, ensure_ascii=False))
        C = g["conditions"]
        summary[bid] = {"passed": g["passed"], "failed": {k: {kk: vv for kk, vv in v.items() if kk in ("counts", "failures", "accepted_mutations", "errors", "collisions", "accepted", "of")} for k, v in C.items() if not v["passed"]},
                        "warnings": g["warnings_requiring_ack"], "compiled": crep["compiled_summary"] | {"date_formats": None}}
    print(json.dumps(summary, indent=1, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
