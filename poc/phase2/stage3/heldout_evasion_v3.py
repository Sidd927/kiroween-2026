"""HELD-OUT evasion set v3 (qualitative + note channels). Written and hash-registered in EXPERIMENT_LOG.md BEFORE the
v4 note handling, text skeletons and qualitative vocabulary were implemented; not run until v4 is frozen.
The phrasings below deliberately avoid the generator's HIDDEN_QUAL list (bench2/generator.py).

Placements (bench2 dev-style clean reports, layouts A, B, C, which print a referrer line):
  P1 appended to the patient-ID line (field line)
  P2 appended to the end of the referrer line
  P3 as a note in that layout's approved note style, after the table
  P4 as a new line after the end that matches a binding skip regex (A "Ref. By :", B "Referred by :", C "Consultant :")
  P5 REPLACING the referrer name (i.e. inside the variable slot of a trusted line)
Expected outcome for every case: REJECT (a printed result must not be dropped silently).
"""
import base64
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

QUAL = ["Typhidot IgM: Pos", "Sickling test: positive", "Pregnancy test - Detected", "Crossmatch compatible",
        "Smear shows ring forms of P vivax", "Coombs direct: neg", "Stool occult blood present", "VDRL non reactive",
        "Blood culture: no growth", "Gram stain GPC in clusters", "Rh factor D positive", "Widal agglutination seen"]
NUMERIC = ["Widal O 1:160", "ESR 1st hr 34", "Hb A2 3.1%", "Retic 2.5"]
PREFIX = {"A": "Ref. By      : ", "B": "Referred by : ", "C": "Consultant : "}


def cases():
    from bench2 import generator as B
    from bench import generator as G
    out = []
    for lay in "ABC":
        for cat, phrases in (("qualitative", QUAL), ("numeric", NUMERIC)):
            for k, ph in enumerate(phrases):
                r = B.make_report(lay, random.Random(960_000 + k))
                base = G.RENDER[lay](r, G.Opts())
                L = base.split("\n")
                pid = next(j for j, l in enumerate(L) if r.patient_id in l)
                ref = next(j for j, l in enumerate(L) if r.doctor.upper() in l.upper())
                end = B._end_line(L, lay)
                variants = {}
                m = list(L); m[pid] += "   " + ph; variants["P1_field_line"] = m
                m = list(L); m[ref] += "   " + ph; variants["P2_referrer_line_end"] = m
                m = list(L); m.insert(end + 1, B.note_line(lay, ph)); variants["P3_approved_note"] = m
                m = list(L); m.insert(end + 1, PREFIX[lay] + ph); variants["P4_new_trusted_line"] = m
                m = list(L); m[ref] = m[ref].replace(r.doctor.upper(), ph.upper()).replace(r.doctor, ph); variants["P5_inside_referrer_slot"] = m
                for place, lines in variants.items():
                    out.append((lay, cat, place, ph, B.encode("\n".join(lines), lay), B.QUEUE_CODEPAGE[lay]))
    return out


def run(process):
    by, leaks = defaultdict(Counter), []
    for lay, cat, place, ph, raw, cp in cases():
        st = process(raw, cp)
        by[cat][st] += 1
        by[f"{cat}:{place}"][st] += 1
        if st == "ACCEPT":
            leaks.append({"layout": lay, "category": cat, "placement": place, "phrase": ph})
    return {k: dict(v) for k, v in sorted(by.items())}, leaks


if __name__ == "__main__":
    from bench2.evaluate import adapter
    sysname = sys.argv[1] if len(sys.argv) > 1 else "v4"
    tag = sys.argv[2] if len(sys.argv) > 2 else "run"
    fn, label = adapter(sysname if sysname != "v4" else "current")
    s, leaks = run(lambda raw, cp: fn(raw, cp)[0])
    out = {"system": label, "n_cases": len(cases()), "summary": s, "leaks": leaks}
    (ROOT / "phase2/stage3/results" / f"heldout_evasion_v3_{tag}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in s.items() if ":" not in k}, indent=1), "\nleaks:", len(leaks))
