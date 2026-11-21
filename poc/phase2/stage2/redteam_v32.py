"""Red-team re-run against v3.2: same probes as redteam_v31.py (R1–R7), pointed at the v5 bindings.
Writes results/redteam_v32_frozen.json itself and exits non-zero on any error (no copying of output files)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from phase2.stage2 import redteam_v3 as RT, redteam_v31 as R31

R31.BH = ROOT / "bindings_h"
src = {}
for name in ("r5_forgery_paths", "r6_revoke_fallback"):
    fn = getattr(R31, name)
    code = fn.__code__.co_consts
src_text = (ROOT / "phase2/stage2/redteam_v31.py").read_text().replace("lab-a.v4.json", "lab-a.v5.json") \
    .replace('compile_binding(llm, docs, 6,', 'compile_binding(llm, docs, 7,').replace('"lab-a.v6.json"', '"lab-a.v7.json"') \
    .replace('docs, 5, b["compiled"]', 'docs, 6, b["compiled"]').replace('"lab-a.v5.json")\n        approve_binding(d / "lab-a.v5.json"', '"lab-a.v6.json")\n        approve_binding(d / "lab-a.v6.json"') \
    .replace('revoke("lab-a", 5,', 'revoke("lab-a", 6,').replace("active_after_revoking_v5", "active_after_revoking_v6")
ns = {"__name__": "redteam_v32_impl", "__file__": str(ROOT / "phase2/stage2/redteam_v31.py")}
exec(compile(src_text.split('if __name__ == "__main__":')[0], "redteam_v32_impl", "exec"), ns)
out = {"system": "v3.2 (active bindings: " + ", ".join(f"{b['binding_id']} v{b['version']}" for b in RT.P3.bindings) + ")",
       "text_probes": RT.run_text_probes(), "R5_forgery": ns["r5_forgery_paths"](),
       "R6_revoke_fallback": ns["r6_revoke_fallback"](), "R7_processing_exception": ns["r7_processing_exception"]()}
assert all(f"v5" in s for s in [out["system"]]), out["system"]
(ROOT / "phase2/stage2/results/redteam_v32_frozen.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps({k: (v if k != "text_probes" else {n: x["v3"] for n, x in v.items()}) for k, v in out.items()}, indent=1, default=str))
