"""Build v3 FHIR bundles for every ACCEPTED held-out test document into runtime_h/fhir/{generic,abdm}/ (git-ignored).
Validation: phase2/stage2/validate_v3.sh (official HL7 validator, same versions and IG as the PoC)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from spoolgeist_h import llm
from spoolgeist_h.fhir_builder import build_bundle
from spoolgeist_h.grid import normalize
from spoolgeist_h.pipeline import Pipeline

llm.FORBID["enabled"] = True
P = Pipeline(allow_agent_approval=True)
out = {v: ROOT / "runtime_h" / "fhir" / v for v in ("generic", "abdm")}
for p in out.values():
    p.mkdir(parents=True, exist_ok=True)
    for f in p.glob("*.json"):
        f.unlink()
n = 0
for p in sorted((ROOT / "data/corpus/test").glob("*/*.json")):
    d = json.loads(p.read_text())
    norm = normalize(d["text"].encode())
    oc = P.process_normalized(norm)
    if oc.status != "ACCEPT":
        continue
    for v in out:
        (out[v] / f"{d['doc_id']}.json").write_text(build_bundle(oc.record, norm.text, norm.sha256, abdm=(v == "abdm")))
    n += 1
print("bundles written:", n)
