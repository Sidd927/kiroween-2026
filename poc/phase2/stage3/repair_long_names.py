"""Stage 3: one LLM repair round per layout whose v1 binding rejects long patient names (B, D, E, F).
Synthetic documents only (pre-send guard). The repaired LLM output is only a CANDIDATE: it is compiled, gated
(re-run at approval) and approved like any other binding. Logged to runtime_h/llm_calls.jsonl.
usage: .venv/bin/python -m phase2.stage3.repair_long_names B D E F"""
import glob, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from spoolgeist_h import llm, rulegen
from spoolgeist_h.compile import sample_norm
from spoolgeist_h.interpreter import process, static_check

OUT = ROOT / "bindings_h" / "candidates"
OUT.mkdir(parents=True, exist_ok=True)
summary = {}
for lay in sys.argv[1:]:
    hint = f"lab-{lay.lower()}"
    base = json.loads((ROOT / "bindings" / f"{hint}.v1.json").read_text())
    base.pop("_meta")
    gen = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / f"data/corpus2/gen/{lay}/*.json")))]
    dev = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / f"data/corpus2/dev/{lay}/*.json")))]
    samples = [sample_norm(d).text for d in gen]
    fails = [d for d in dev if d["cls"] == "long_name_overflow" and process([base], sample_norm(d).text, "anywhere").status == "REJECT"]
    failures = [{"doc_id": d["doc_id"], "expected": "accept", "status": "REJECT",
                 "problem": "valid document was rejected: the patient name is longer than its printed column and runs "
                            "directly into the next label (no space). The name must still be extracted exactly.",
                 "text": sample_norm(d).text} for d in fails[:2]]
    prompt = rulegen.repair_prompt(base, failures, samples, hint)
    resp = llm.call(prompt, samples + [f["text"] for f in failures], purpose=f"stage3:repair_long_names:{lay}", model="sonnet")
    cand = llm.extract_json(resp["text"])
    errs = static_check(cand)
    ok_long = sum(process([cand], sample_norm(d).text, "anywhere").status == "ACCEPT" for d in dev if d["cls"] == "long_name_overflow")
    n_long = sum(1 for d in dev if d["cls"] == "long_name_overflow")
    clean_before = sum(process([base], sample_norm(d).text, "anywhere").status == "ACCEPT" for d in dev if d["expected"] == "accept")
    clean_after = sum(process([cand], sample_norm(d).text, "anywhere").status == "ACCEPT" for d in dev if d["expected"] == "accept")
    p = OUT / f"{hint}.llm-repair-longname.json"
    p.write_text(json.dumps(cand, indent=1))
    summary[lay] = {"static_errors": errs, "long_name_accepted": f"{ok_long}/{n_long}", "valid_accepted_before": clean_before,
                    "valid_accepted_after": clean_after, "seconds": round(resp["seconds"], 1), "cost_usd": resp["cost_usd"],
                    "changed_fields": sorted(k for k in cand["fields"] if cand["fields"][k] != base["fields"].get(k)),
                    "results_changed": cand["results"] != base["results"], "layout_changed": cand["layout"] != base["layout"]}
print(json.dumps(summary, indent=1))
print("total LLM cost USD:", round(llm.CALLS["cost_usd"], 4), "calls:", llm.CALLS["count"])
