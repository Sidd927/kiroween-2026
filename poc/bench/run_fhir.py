"""Build FHIR bundles (generic + ABDM-profiled) for every ACCEPTED held-out document and write them
to runtime/fhir/{generic,abdm}/. Validation is done separately with the official HL7 validator."""
import json, sys
from pathlib import Path
from spoolgeist import interpreter, llm
from spoolgeist.grid import normalize
from spoolgeist.fhir_builder import build_bundle
from bench.run_benchmark import load_bindings

ROOT = Path(__file__).resolve().parents[1]
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
llm.FORBID["enabled"] = True
B = load_bindings()
out = {v: ROOT / "runtime" / "fhir" / v for v in ("generic", "abdm")}
for p in out.values():
    p.mkdir(parents=True, exist_ok=True)
    for f in p.glob("*.json"):
        f.unlink()
n = 0
for p in sorted((ROOT / "data/corpus/test").glob("*/*.json")):
    d = json.loads(p.read_text())
    norm = normalize(d["text"].encode())
    oc = interpreter.process(B, norm.text)
    if oc.status != "ACCEPT":
        continue
    for v in ("generic", "abdm"):
        (out[v] / f"{d['doc_id']}.json").write_text(build_bundle(oc.record, norm.text, norm.sha256, abdm=(v == "abdm")))
    n += 1
    if n >= limit:
        break
print("bundles written:", n)
