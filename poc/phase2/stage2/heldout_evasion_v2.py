"""HELD-OUT evasion set v2 for RV-1. Written and hash-registered in EXPERIMENT_LOG.md BEFORE v3.2 was implemented,
and not run until v3.2 was frozen. It is different from the v1 evasion set (redteam_v31_evasion.py), which informed v3.2.

Each phrasing is a printed result (numeric or qualitative) placed where v3.0/v3.1 trusted text:
  P1 appended to the patient-ID line (a field line)
  P2 a new line after the report end that matches one of the binding's skip/anchor regexes
  P3 the same inside the results-table region
Layouts A, B, C (prefix-only skip regexes) and E (unanchored anchor). Expected outcome for every case: REJECT.
Categories are reported separately: numeric-with-digits, spelled-out numbers, qualitative (no number).
"""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PHRASES = {
    "digits": ["Na138", "138mEq/L", "Hb-9.8", "K:4.1", "Cr 1.2", "HbA1c=6.1", "urea 32", "TLC 11,200",
               "PLT 1.5L", "Hb 9.8 (L)", "INR 2.9", "FBS 182 PPBS 240", "Na/K 138/4.1", "Ca++ 8.1",
               "Hb ９.８", "Na ١٣٨", "repeat after 2 days, Hb was 7.9", "value 4.1"],
    "spelled": ["Hb nine point eight", "sodium one hundred thirty eight", "potassium four point one",
                "Hb: twelve", "creatinine two point four", "platelets one lakh fifty thousand"],
    "qualitative": ["HIV reactive", "HBsAg: POSITIVE", "Urine sugar ++", "Dengue NS1 positive",
                    "Malaria parasite seen", "Blood group B negative"],
}
TRUSTED = {"A": ("Ref. By      : ", "END OF REPORT", "Patient Name : "),
           "B": ("Referred by : ", "End of Report", "Name    : "),
           "C": ("Consultant : ", "-- END --", "Consultant : "),
           "E": ("", "Report generated", None)}
E_SUFFIX = "   Sex/Age:"


def cases():
    from bench import generator as G
    out = []
    for lay, (prefix, end_kw, in_table_prefix) in TRUSTED.items():
        for cat, phrases in PHRASES.items():
            for k, ph in enumerate(phrases):
                r = G.make_report(lay, random.Random(940_000 + k))
                L = G.RENDER[lay](r, G.Opts()).split("\n")
                # P1: patient-ID line
                m = list(L)
                i = next(j for j, l in enumerate(m) if r.patient_id in l)
                m[i] = m[i] + "   " + ph
                out.append((lay, cat, "P1_field_line", ph, "\n".join(m)))
                # P2: trusted line after the end
                m = list(L)
                i = next(j for j, l in enumerate(m) if end_kw in l)
                m.insert(i + 1, (prefix + ph) if lay != "E" else (ph + E_SUFFIX))
                out.append((lay, cat, "P2_trusted_line_after_end", ph, "\n".join(m)))
                # P3: trusted line inside the table
                if in_table_prefix:
                    m = list(L)
                    lab = r.results[0].label
                    i = next(j for j, l in enumerate(m) if lab in l) + (2 if lay == "C" else 0)
                    m.insert(i + 1, in_table_prefix + ph)
                    out.append((lay, cat, "P3_trusted_line_in_table", ph, "\n".join(m)))
    return out


def run(process):
    by = defaultdict(Counter)
    leaks = []
    for lay, cat, place, ph, text in cases():
        st = process(text)
        by[cat][st] += 1
        by[f"{cat}:{place}"][st] += 1
        if st == "ACCEPT":
            leaks.append({"layout": lay, "category": cat, "placement": place, "phrase": ph})
    return {k: dict(v) for k, v in sorted(by.items())}, leaks


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "v3"
    if which == "v2.1":
        from bench.run_benchmark import load_bindings
        from spoolgeist import interpreter
        from spoolgeist.grid import normalize
        B = load_bindings()
        proc = lambda t: interpreter.process(B, normalize(t.encode()).text).status
    else:
        from spoolgeist_h.pipeline import Pipeline
        P = Pipeline(allow_agent_approval=True)
        proc = lambda t: P.process_bytes(t.encode()).status
        which = f"v3 (active: {', '.join(b['binding_id'] + ' v' + str(b['version']) for b in P.bindings)})"
    summary, leaks = run(proc)
    out = {"system": which, "n_cases": len(cases()), "summary": summary, "leaks": leaks}
    tag = sys.argv[2] if len(sys.argv) > 2 else "run"
    (ROOT / "phase2/stage2/results" / f"heldout_evasion_v2_{tag}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: out[k] for k in ("system", "n_cases", "summary")}, indent=1, ensure_ascii=False))
    print("leaks:", len(leaks))
