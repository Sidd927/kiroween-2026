"""Held-out evasion probes for the v3.1 result sentinel, written AFTER the v3.1 freeze. Measures what the
vocabulary-based sentinel still misses. Layout A, result text placed on a trusted 'Ref. By' line after the report end."""
import json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bench import generator as G
from spoolgeist_h.pipeline import Pipeline
P = Pipeline(allow_agent_approval=True)
PHRASES = ["NA+ 138 mEq", "Serum Na 138", "S.Sodium138mmol/L", "Hb nine point eight", "repeat HGB 9.8",
           "K 4.1 mmol per litre", "ESR 22 mm in 1st hr", "138 mmol / L", "Sodium: 138", "sodium=138 (135-145)",
           "TSH 2.5 uIU/ml", "Hb 9,8 g/dl", "HbA1c 6.1%", "Na 138 K 4.1 Cl 101", "glucose (PP) 182"]
out = {}
for ph in PHRASES:
    acc = 0
    for s in range(5):
        r = G.make_report("A", random.Random(930_000 + s)); t = G.RENDER["A"](r, G.Opts()).split("\n")
        i = next(k for k, l in enumerate(t) if "END OF REPORT" in l)
        t.insert(i + 1, "Ref. By      : " + ph)
        acc += P.process_bytes("\n".join(t).encode()).status == "ACCEPT"
    out[ph] = f"{acc}/5 accepted (result dropped)" if acc else "0/5 (rejected)"
(ROOT / "phase2/stage2/results/redteam_v31_evasion.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
