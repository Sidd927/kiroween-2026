"""Build v4 FHIR bundles (generic + ABDM-profiled) for every ACCEPTED document of the sealed bench2 test split,
plus checks the validator cannot do: unit/code mapping, date precision, note preservation, identifiers.
Bundles go to runtime_h/fhir_v4/ (git-ignored); validate with phase2/stage3/validate_fhir_v4.sh.
usage: .venv/bin/python -m phase2.stage3.post_freeze.fhir_v4"""
import base64, glob, json, sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from spoolgeist_h import llm
from spoolgeist_h.dictionary import DICT
from spoolgeist_h.fhir_builder import build_bundle
from spoolgeist_h.grid import normalize
from spoolgeist_h.pipeline import Pipeline

llm.FORBID["enabled"] = True
P = Pipeline(allow_agent_approval=True)
out = {v: ROOT / "runtime_h" / "fhir_v4" / v for v in ("generic", "abdm")}
for p in out.values():
    p.mkdir(parents=True, exist_ok=True)
    for f in p.glob("*.json"):
        f.unlink()
checks, n = Counter(), 0
for p in sorted(glob.glob(str(ROOT / "data/corpus2/test/*/*.json"))):
    d = json.load(open(p))
    if d["group"] != "valid":
        continue
    norm = normalize(base64.b64decode(d["raw_b64"]), d["queue_codepage"])
    oc = P.process_normalized(norm)
    if oc.status != "ACCEPT":
        continue
    n += 1
    for v in out:
        (out[v] / f"{d['doc_id']}.json").write_text(build_bundle(oc.record, norm.text, norm.sha256, abdm=(v == "abdm")))
    b = json.loads((out["abdm"] / f"{d['doc_id']}.json").read_text())
    res = {e["resource"]["resourceType"]: e["resource"] for e in b["entry"] if e["resource"]["resourceType"] != "Observation"}
    obs = [e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "Observation"]
    t = d["truth"]
    checks["patient_id_ok"] += res["Patient"]["identifier"][0]["value"] == t["patient_id"]
    checks["name_ok"] += res["Patient"]["name"][0]["text"].casefold() == t["patient_name"].casefold()
    checks["gender_ok"] += res["Patient"].get("gender") == t["patient_sex"]
    eff = res["DiagnosticReport"]["effectiveDateTime"]
    checks["date_ok"] += eff[:10] == t["collected"]
    checks["precision_ok"] += ("T" in eff) == bool(t.get("collected_time")) and (not t.get("collected_time") or eff[11:16] == t["collected_time"])
    tr = {x["code"]: x for x in t["results"]}
    ok_val = ok_units = ok_interp = True
    for o in obs:
        code = next(k for k, v in DICT["tests"].items() if v["loinc"] == o["code"]["coding"][0]["code"])
        x = tr[code]
        f = Decimal(str(DICT["tests"][code]["units"][x["unit"]]))
        ok_val &= Decimal(str(o["valueQuantity"]["value"])) == Decimal(x["value"]) * f
        ok_units &= o["valueQuantity"]["code"] == DICT["tests"][code]["ucum"] and o["valueQuantity"]["system"] == "http://unitsofmeasure.org"
        ok_interp &= bool(o.get("interpretation")) == bool(x["flag"])
    checks["observation_count_ok"] += len(obs) == len(t["results"])
    checks["values_converted_ok"] += ok_val
    checks["ucum_ok"] += ok_units
    checks["interpretation_presence_ok"] += ok_interp
    concl = res["DiagnosticReport"]["conclusion"].casefold()
    checks["notes_preserved_ok"] += all(" ".join(nt.split()).casefold() in concl for nt in t.get("notes") or [])
print(json.dumps({"bundles": n, **{k: f"{v}/{n}" for k, v in checks.items()}}, indent=1))
(ROOT / "phase2/stage3/results/fhir_v4_semantic_checks.json").write_text(json.dumps({"bundles": n, **checks}, indent=1))
