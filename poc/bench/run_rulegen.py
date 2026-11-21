"""Run AI rule generation + activation gate for the given layouts.
usage: python -m bench.run_rulegen A B C   (collision check against gen docs of --against layouts)"""
import argparse, json, sys, time
from pathlib import Path
from spoolgeist import rulegen, llm

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "corpus"

def load(split, lay):
    return [json.loads(p.read_text()) for p in sorted((C / split / lay).glob("*.json"))]

ap = argparse.ArgumentParser()
ap.add_argument("layouts", nargs="+")
ap.add_argument("--against", nargs="*", default=["A", "B", "C"])
ap.add_argument("--model", default="sonnet")
a = ap.parse_args()
for lay in a.layouts:
    t0 = time.time()
    others = [d for o in a.against if o != lay for d in load("gen", o)]
    res = rulegen.generate_and_activate(lay, load("gen", lay), load("dev", lay), others, model=a.model)
    res["wall_seconds"] = round(time.time() - t0, 1)
    res["llm_cost_usd"] = round(llm.CALLS["cost_usd"], 4)
    out = ROOT / "runtime" / f"rulegen_{lay}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(lay, "activated" if res["activated"] else "NOT activated", "rounds:", res["rounds_used"],
          "calls:", res["llm_calls"], f"{res['wall_seconds']}s", f"${res['llm_cost_usd']}")
    for h in res["history"]:
        print("  round", h["round"], {k: v for k, v in h.items() if k in ("passed", "counts", "static_errors", "error")})
        for f in h.get("failures", [])[:6]:
            print("     -", f["doc_id"], f["cls"], f["problem"][:220])
