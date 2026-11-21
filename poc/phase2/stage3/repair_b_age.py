"""Stage 3: LLM repair round 2 for layout B: after truth-based promotion made age required, long names glued to
"Age :" are rejected (the age regex needs a word boundary). Synthetic only; output is a candidate.
usage: .venv/bin/python -m phase2.stage3.repair_b_age"""
import glob, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from spoolgeist_h import llm, rulegen
from spoolgeist_h.compile import sample_norm
from spoolgeist_h.interpreter import process, static_check
base = json.loads((ROOT / "bindings_h/candidates/lab-b.llm-repair-longname.json").read_text())
gen = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / "data/corpus2/gen/B/*.json")))]
dev = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / "data/corpus2/dev/B/*.json")))]
b9 = json.loads((ROOT / "bindings_h/lab-b.v9.json").read_text())
fails = [d for d in dev if d["cls"] == "long_name_overflow" and process([b9], sample_norm(d).text, "full", [], sample_norm(d).bold).status == "REJECT"]
failures = [{"doc_id": d["doc_id"], "expected": "accept", "status": "REJECT",
             "problem": "valid document was rejected: missing_field patient_age. The long patient name runs directly into "
                        "the 'Age' label without a space, so a word boundary before 'Age' fails. Age (and sex) must still be extracted.",
             "text": sample_norm(d).text} for d in fails[:2]]
resp = llm.call(rulegen.repair_prompt(base, failures, [sample_norm(d).text for d in gen], "lab-b"),
                [sample_norm(d).text for d in gen] + [f["text"] for f in failures], purpose="stage3:repair_b_age", model="sonnet")
cand = llm.extract_json(resp["text"])
(ROOT / "bindings_h/candidates/lab-b.llm-repair-age.json").write_text(json.dumps(cand, indent=1))
print({"static_errors": static_check(cand), "failures_given": len(failures), "cost_usd": resp["cost_usd"],
       "changed": {k: (base["fields"].get(k, {}).get("regex"), cand["fields"][k]["regex"]) for k in cand["fields"] if cand["fields"][k] != base["fields"].get(k)},
       "results_changed": cand["results"] != base["results"]})
