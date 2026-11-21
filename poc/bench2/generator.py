"""bench2: physiologically consistent, more realistic synthetic lab reports + ground truth (Phase 2, Stage 3).

Implements catalogue v2 of phase2/02_BENCHMARK_DESIGN.md. Reuses the frozen v1 layout renderers (bench/generator.py)
so layouts A-F print exactly as the bindings were written for; adds:
  * consistent values (report 03): Hct = RBC x MCV / 10, MCH = Hb x 10 / RBC, MCHC = Hb x 100 / Hct
    (StatPearls NBK604207); NEUT% + LYMPH% <= 100; DBIL <= TBIL; ALB < TP; sex-specific printed ranges for Hb/Hct/RBC;
    flags computed against the PRINTED range
  * realistic VALID variations, POLICY classes and new DEFECT classes (spec section 4)
  * bytes in a declared queue code page (layout C prints cp1252; accented names)
Ground truth comes from the structured Report, never from rendered text. EVERYTHING IS SYNTHETIC.

The system under test (spoolgeist_h) must never import this package (tests_h/test_independence.py).
"""
from __future__ import annotations

import base64
import copy
import json
import math
import random
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bench import generator as G

SYNTH = G.SYNTH
LAYOUTS = list("ABCDEF")
QUEUE_CODEPAGE = {"A": "ascii", "B": "ascii", "C": "cp1252", "D": "ascii", "E": "ascii", "F": "ascii"}
ACCENTED = [("Renée", "D'Souza"), ("José", "Fernandes"), ("Zoë", "Mascarenhas"), ("Inés", "Pereira"), ("Chloé", "Rodrigues")]
REFERRERS = ["S. Joshi", "A. Rao", "M. Kulkarni", "Anjali R. Deshpande", "Prakash Shinde", "SELF", "V. K. Gupta", "R. Shah"]
NOTE_TEXT = ["Sample slightly haemolysed.", "Clinical correlation advised.", "Verified twice.", "Fasting status not stated.",
             "Lipaemic sample.", "Result checked on repeat run."]
INTERP = ["Interpretation: values should be correlated with the clinical picture",
          "  and previous reports. Kindly consult your physician."]
NOTE_NUMERIC = ["Repeat after 2 days.", "Sample received at 10:45.", "Retest advised in 3 months."]
NOTE_STYLE = {"A": ("Note: {t}", None), "B": ("Remark - {t}", None), "C": ("  Comment: {t}", None),
              "D": ("| Note: {t:<57}|", None), "E": ("NB: {t}", None), "F": ("COMMENT: {T}", None)}
UNAPPROVED_NOTE = "*** {t} ***"
SUBHEAD = {"A": ("NEUT%", "DIFFERENTIAL COUNT"), "B": ("NEUT%", "Differential Leucocyte Count"),
           "C": ("TP", "  PROTEINS"), "D": ("HGB", "| HAEMATOLOGY" + " " * 52 + "|"), "F": ("GLU", "CHEMISTRY")}
HIDDEN_NUMERIC = ["Serum Na 138", "K 4.1", "Hb 9.8 g/dL", "TSH 2.5"]
HIDDEN_QUAL = ["HIV REACTIVE", "HBsAg POSITIVE", "Malaria parasite seen", "Urine sugar ++"]
# sex-specific printed ranges (adult; laboratory-specific in reality, see report 03)
RANGES = {"HGB": {"M": (13.0, 17.0), "F": (12.0, 15.5)}, "HCT": {"M": (40.0, 50.0), "F": (36.0, 46.0)},
          "RBC": {"M": (4.50, 5.90), "F": (4.00, 5.20)}}


@dataclass
class Doc:
    doc_id: str
    layout: str
    cls: str
    group: str            # valid | policy | defect | foreign
    expected: str         # accept | reject
    raw: bytes
    queue_codepage: str
    truth: Optional[dict]          # full truth (valid; also policy, for "accepted with wrong data" checks)
    note: str = ""

    def to_json(self) -> dict:
        return {"doc_id": self.doc_id, "layout": self.layout, "cls": self.cls, "group": self.group,
                "expected": self.expected, "raw_b64": base64.b64encode(self.raw).decode(),
                "queue_codepage": self.queue_codepage, "truth": self.truth, "note": self.note}


# ----------------------------------------------------------------------------- consistent values
def _clip(x, lo, hi):
    return max(lo, min(hi, x))


def _round(x: float, d: int) -> str:
    return f"{x:.{d}f}"


def cbc_values(sex: str, rng: random.Random) -> Dict[str, float]:
    """Hb, RBC, MCV drawn; Hct, MCH, MCHC derived by the definitional identities."""
    anaemia = rng.random() < 0.2
    micro = anaemia and rng.random() < 0.6
    hb = rng.gauss(14.8 if sex == "M" else 13.1, 1.0) - (rng.uniform(2.0, 4.5) if anaemia else 0)
    rbc = rng.gauss(5.1 if sex == "M" else 4.5, 0.35) - (rng.uniform(0.2, 0.6) if anaemia and not micro else 0)
    mcv = rng.gauss(74 if micro else 90, 4.5)
    hb, rbc, mcv = _clip(hb, 6.0, 19.5), _clip(rbc, 2.6, 6.6), _clip(mcv, 62, 108)
    hct = rbc * mcv / 10
    # amendment 1 (spec 02 section 9): keep MCHC physiologically realistic (26-37 g/dL) by adjusting Hb
    hb = _clip(hb, 0.26 * hct, 0.37 * hct)
    return {"HGB": hb, "RBC": rbc, "MCV": mcv, "HCT": hct, "MCH": hb * 10 / rbc, "MCHC": hb * 100 / hct,
            "WBC": rng.choice([rng.gauss(7.5, 1.8), rng.uniform(11.5, 19.0)]) if rng.random() < 0.15 else rng.gauss(7.5, 1.8),
            "PLT": rng.uniform(80, 140) if rng.random() < 0.1 else rng.gauss(260, 60)}


def chem_values(rng: random.Random) -> Dict[str, float]:
    tbil = rng.uniform(1.4, 4.5) if rng.random() < 0.15 else rng.uniform(0.25, 1.1)
    dbil = tbil * rng.uniform(0.0, 0.35 if tbil < 1.2 else 0.6)
    tp = rng.gauss(7.1, 0.5)
    alb = tp * rng.uniform(0.5, 0.68)
    neut = rng.uniform(42, 75)
    lymph = rng.uniform(18, min(45, 98 - neut))
    return {"TBIL": tbil, "DBIL": dbil, "TP": tp, "ALB": alb, "NEUT%": neut, "LYMPH%": lymph,
            "ALT": rng.uniform(60, 180) if rng.random() < 0.12 else rng.uniform(8, 38),
            "AST": rng.uniform(55, 160) if rng.random() < 0.12 else rng.uniform(10, 36),
            "ALP": rng.uniform(140, 320) if rng.random() < 0.1 else rng.uniform(45, 120),
            "GLU": rng.uniform(110, 260) if rng.random() < 0.2 else rng.uniform(72, 98),
            "CREA": rng.uniform(1.4, 3.5) if rng.random() < 0.1 else rng.uniform(0.6, 1.1),
            "UREA": rng.uniform(46, 110) if rng.random() < 0.1 else rng.uniform(16, 40)}


def make_report(layout: str, rng: random.Random, force_day_gt12=False, accented=False) -> G.Report:
    r = G.make_report(layout, rng, force_day_gt12=force_day_gt12)       # identity, dates, panel membership
    if accented:
        r.first, r.last = rng.choice(ACCENTED)
    sex = r.sex
    v = {**cbc_values(sex, rng), **chem_values(rng)}
    for x in r.results:
        d = len(x.value.split(".")[1]) if "." in x.value else 0
        lo, hi = float(x.low), float(x.high)
        if x.code in RANGES:
            lo, hi = RANGES[x.code][sex]
            x.low, x.high = _round(lo, d), _round(hi, d)
        val = v[x.code]
        # unit scaling to the layout's printed unit (canonical draws: WBC/PLT in 10^3/uL)
        if x.code == "WBC" and x.unit in ("/cumm", "cells/cumm"):
            val *= 1000
        if x.code == "PLT" and x.unit in ("lakh/cumm", "lakhs/cumm"):
            val /= 100
        x.value = _round(val, d)
        x.flag = "H" if float(x.value) > float(x.high) else ("L" if float(x.value) < float(x.low) else "")
    r.doctor = rng.choice(REFERRERS)
    return r


def truth(r: G.Report, notes: List[str]) -> dict:
    lay = r.layout
    t = G.truth(r)
    t["collected_time"] = r.collected.strftime("%H:%M") if lay in "ABCF" else None
    t["reported"] = r.reported.strftime("%Y-%m-%d") if lay in "ABC" else None
    t["results"] = [{"code": x.code, "value": x.value, "unit": x.unit, "label": x.label, "flag": x.flag,
                     "ref_low": x.low, "ref_high": x.high} for x in r.results]
    t["notes"] = [" ".join(n.split()) for n in notes]
    t["flag_semantics"] = "direction" if lay in "ADF" else "presence"
    return t


# ----------------------------------------------------------------------------- text helpers
def _lines(t):
    return t.split("\n")


def _row_end(L, r, i_res):
    lab = r.results[i_res].label
    i = next(k for k, l in enumerate(L) if (lab + " ") in l or l.strip().startswith(lab) or l.endswith(lab))
    return i + 2 if r.layout == "C" else i


def _end_line(L, lay):
    kw = {"A": "END OF REPORT", "B": "End of Report", "C": "-- END --", "D": "End of Report",
          "E": "Report generated", "F": "END OF REPORT"}[lay]
    return next(k for k, l in enumerate(L) if kw in l)


def note_line(lay, t):
    fmt, _ = NOTE_STYLE[lay]
    return fmt.format(t=t, T=t.upper())


def encode(text: str, lay: str, codepage: Optional[str] = None) -> bytes:
    cp = codepage or QUEUE_CODEPAGE[lay]
    return text.encode("utf-8" if cp == "ascii" else cp)


# ----------------------------------------------------------------------------- builders
def build(lay: str, seed: int, cls: str) -> Optional[Doc]:
    rng = random.Random(seed)
    accented = cls in ("accented_name", "wrong_code_page")
    if accented and lay != "C":
        return None
    r = make_report(lay, rng, force_day_gt12=(seed % 7 == 0), accented=accented)
    o = G.Opts()
    notes: List[str] = []
    group, expected, cp = "valid", "accept", None
    post = []          # text operations applied after rendering

    def need(cond):
        if not cond:
            raise _NA()

    try:
        # ---------------- VALID
        if cls == "clean":
            pass
        elif cls in ("col_shift", "crlf_trailing"):
            post.append("text:" + {"col_shift": "col_shift", "crlf_trailing": "crlf"}[cls])
        elif cls == "drop_optional":
            res = G.p_drop_optional(r, o, rng)
            need(res)
        elif cls == "page_break":
            need(G.p_page_break(r, o, rng))
        elif cls == "long_name_overflow":
            r.first, r.last = rng.choice(G.LONG_NAMES)
        elif cls == "referrer_variation":
            r.doctor = rng.choice(["Anjali R. Deshpande", "SELF", "V. K. Gupta", "Mohammed Irfan Shaikh"])
        elif cls == "approved_note":
            notes.append(note_line(lay, rng.choice(NOTE_TEXT)))
            post.append(("note", notes[-1], rng.choice(["in_table", "after_table"])))
        elif cls == "interpretive_note":
            need(lay != "D")
            notes += INTERP
            post.append(("interp", INTERP))
        elif cls == "section_subheading":
            need(lay in SUBHEAD and any(x.code == SUBHEAD[lay][0] for x in r.results))
            post.append(("subhead", SUBHEAD[lay]))
        elif cls == "footer_version_drift":
            need(lay == "E")
            post.append(("replace", "LabSys 3.1", f"LabSys 3.{rng.randint(2, 9)}"))
        elif cls == "sex_specific_ranges":
            need(any(x.code in RANGES for x in r.results))   # ranges already sex-specific; class forces female
            r = make_report(lay, random.Random(seed + 1), accented=accented)
            r.sex = "F"
            r = _rerange(r, rng)
        elif cls == "abnormal_values":
            need(any(x.flag for x in r.results) or _force_abnormal(r, rng))
        elif cls == "accented_name":
            pass
        elif cls == "bold_flag":
            need(lay == "B" and (any(x.flag for x in r.results) or _force_abnormal(r, rng)))
        elif cls == "low_direct_bilirubin":
            need(lay == "C")
            x = next(x for x in r.results if x.code == "DBIL")
            x.value = rng.choice(["0.00", "0.01", "0.02"])
            x.flag = ""
        # ---------------- POLICY
        elif cls == "note_with_number":
            group, expected = "policy", "reject"
            notes.append(note_line(lay, rng.choice(NOTE_NUMERIC)))
            post.append(("note", notes[-1], "after_table"))
        elif cls == "unapproved_note_style":
            group, expected = "policy", "reject"
            notes.append(UNAPPROVED_NOTE.format(t=rng.choice(NOTE_TEXT)))
            post.append(("note", notes[-1], "after_table"))
        elif cls == "static_text_damage":
            group, expected = "policy", "reject"
            post.append(("static_damage",))
        elif cls == "multipage_unapproved":
            need(lay in ("C", "E"))
            group, expected = "policy", "reject"
            post.append(("duplicate_page",))
        elif cls == "long_name_wrapped":
            group, expected = "policy", "reject"
            r.first, r.last = rng.choice(G.LONG_NAMES)
            post.append(("wrap_name",))
        # ---------------- DEFECT (v1 classes reuse the frozen perturbations)
        elif cls in G.PERTURBATIONS and G.PERTURBATIONS[cls] and cls not in ("col_shift", "drop_optional", "page_break", "crlf_trailing", "long_name"):
            group, expected = "defect", "reject"
            res = G.PERTURBATIONS[cls](r, o, rng)
            need(res)
            r, o, exp, op = res
            if op:
                post.append(op)
        elif cls == "header_changed_paged":
            group, expected = "defect", "reject"
            need(G.p_page_break(r, o, rng))
            o.new_header = True
        elif cls == "extra_section_unknown_tests":
            group, expected = "defect", "reject"
            post.append(("extra_section",))
        elif cls == "two_patients_one_job":
            group, expected = "defect", "reject"
            post.append(("concat", seed))
        elif cls == "page_order_swap":
            group, expected = "defect", "reject"
            need(G.p_page_break(r, o, rng))
            post.append(("swap_pages",))
        elif cls == "text_between_rows_with_number":
            group, expected = "defect", "reject"
            post.append(("insert_in_table", "Lot 4471 calibrated 12/03/2026"))
        elif cls == "row_value_swap":
            group, expected = "defect", "reject"
            need(_swap_detectable(r))
        elif cls == "index_inconsistent":
            group, expected = "defect", "reject"
            need(_perturb_index(r, rng))
        elif cls == "bilirubin_inverted":
            group, expected = "defect", "reject"
            need(lay == "C")
            tb = next(x for x in r.results if x.code == "TBIL"); db = next(x for x in r.results if x.code == "DBIL")
            db.value = _round(float(tb.value) * rng.uniform(1.2, 1.8), 2)
            db.flag = "H" if float(db.value) > float(db.high) else ""
        elif cls == "protein_inverted":
            group, expected = "defect", "reject"
            need(lay == "C")
            tp = next(x for x in r.results if x.code == "TP"); al = next(x for x in r.results if x.code == "ALB")
            al.value = _round(float(tp.value) + rng.uniform(0.2, 0.9), 1)
            al.flag = "H" if float(al.value) > float(al.high) else ""
        elif cls == "differential_over_100":
            group, expected = "defect", "reject"
            n = [x for x in r.results if x.code == "NEUT%"]; l_ = [x for x in r.results if x.code == "LYMPH%"]
            need(n and l_)
            l_[0].value = str(int(103 - int(n[0].value) + rng.randint(0, 8)))
            l_[0].flag = "H" if float(l_[0].value) > float(l_[0].high) else ""
        elif cls == "hidden_numeric_result":
            group, expected = "defect", "reject"
            post.append(("hidden", rng.choice(HIDDEN_NUMERIC), rng.choice(["referrer", "note", "field"])))
        elif cls == "hidden_qualitative_result":
            group, expected = "defect", "reject"
            post.append(("hidden", rng.choice(HIDDEN_QUAL), rng.choice(["referrer", "note", "field"])))
        elif cls == "wrong_code_page":
            group, expected = "defect", "reject"
            cp = "cp437"
        elif cls == "comma_decimal":
            group, expected = "defect", "reject"
            x = next((x for x in r.results if "." in x.value), None)
            need(x)
            x.value = x.value.replace(".", ",")
        # ---------------- FOREIGN
        elif cls == "foreign_layout_G":
            group, expected = "foreign", "reject"
        elif cls == "drifted_new_format":
            group, expected = "foreign", "reject"
            o.new_header = True
        else:
            raise ValueError(cls)
    except _NA:
        return None

    lay_r = "G" if cls == "foreign_layout_G" else lay
    if lay_r == "G":
        r = make_report("G", rng)
    text = G.RENDER[lay_r](r, o)
    for op in post:
        text = apply(text, op, r, rng)
        if text is None:
            return None
    raw = encode(text, lay, cp) if lay_r != "G" else text.encode()
    t = truth(r, [n for n in notes]) if group in ("valid", "policy") else None
    return Doc(f"{lay}-{seed}-{cls}", lay, cls, group, expected, raw, QUEUE_CODEPAGE[lay], t)


class _NA(Exception):
    pass


def _force_abnormal(r, rng) -> bool:
    for x in r.results:
        if x.code in ("GLU", "WBC", "ALT", "AST", "UREA", "CREA", "ALP"):
            d = len(x.value.split(".")[1]) if "." in x.value else 0
            x.value = _round(float(x.high) * rng.uniform(1.3, 1.9), d)
            x.flag = "H"
            return True
    return False


def _rerange(r, rng):
    for x in r.results:
        if x.code in RANGES:
            d = len(x.value.split(".")[1]) if "." in x.value else 0
            lo, hi = RANGES[x.code]["F"]
            x.low, x.high = _round(lo, d), _round(hi, d)
            x.flag = "H" if float(x.value) > hi else ("L" if float(x.value) < lo else "")
    return r


def _swap_detectable(r) -> bool:
    """Swap HCT and MCHC values: both stay plausible, only the Hb/Hct/MCHC identity exposes it."""
    h = [x for x in r.results if x.code == "HCT"]; m = [x for x in r.results if x.code == "MCHC"]
    if not (h and m):
        return False
    h[0].value, m[0].value = m[0].value, h[0].value
    for x in (h[0], m[0]):
        x.flag = "H" if float(x.value) > float(x.high) else ("L" if float(x.value) < float(x.low) else "")
    return True


def _perturb_index(r, rng) -> bool:
    need = {"HGB", "HCT", "RBC"}
    have = {x.code for x in r.results}
    cand = [x for x in r.results if x.code in ("MCV", "MCH", "MCHC")]
    if not (need <= have and cand):
        return False
    x = rng.choice(cand)
    x.value = _round(float(x.value) * rng.choice([0.9, 1.1]), 1)
    x.flag = "H" if float(x.value) > float(x.high) else ("L" if float(x.value) < float(x.low) else "")
    return True


def apply(text: str, op, r, rng) -> Optional[str]:
    lay = r.layout
    if isinstance(op, str):
        return G.apply_text_op(text, op, r, rng)
    kind = op[0]
    L = _lines(text)
    if kind == "note":
        line, where = op[1], op[2]
        i = _row_end(L, r, rng.randrange(len(r.results))) if where == "in_table" else _end_line(L, lay)
        L.insert(i + 1, line)
    elif kind == "interp":
        i = _end_line(L, lay)
        L[i + 1:i + 1] = op[1]
    elif kind == "subhead":
        code, line = op[1]
        idx = next(k for k, x in enumerate(r.results) if x.code == code)
        lab = r.results[idx].label
        i = next(k for k, l in enumerate(L) if lab in l)
        L.insert(i, line)
    elif kind == "replace":
        return text.replace(op[1], op[2])
    elif kind == "static_damage":
        toks = [r.patient_id, r.first, r.last, r.first.upper(), r.last.upper()] + [x.label for x in r.results] + [x.value for x in r.results]
        cand = [i for i, ln in enumerate(L) if ln.strip() and not any(t and t in ln for t in toks) and not any(c.isdigit() for c in ln)
                and sum(c.isalpha() for c in ln) >= 4]
        if not cand:
            return None
        i = rng.choice(cand)
        pos = [k for k, c in enumerate(L[i]) if c.isalpha()]
        k = rng.choice(pos)
        L[i] = L[i][:k] + ("Q" if L[i][k] != "Q" else "X") + L[i][k + 1:]
    elif kind == "duplicate_page":
        return text.rstrip("\f\n") + "\n\f" + text
    elif kind == "wrap_name":
        nm = G.printed_name(r)
        parts = nm.split(" ")
        first, rest = " ".join(parts[:-1]), parts[-1]
        i = next(k for k, l in enumerate(L) if nm in l)
        L[i] = L[i].replace(nm, first, 1)
        L.insert(i + 1, " " * 15 + rest)
    elif kind == "extra_section":
        i = _end_line(L, lay)
        L[i + 1:i + 1] = ["ELECTROLYTES", "SERUM SODIUM          138     mmol/L      135 - 145"]
    elif kind == "concat":
        r2 = make_report(lay, random.Random(op[1] + 5000))
        return text + "\n" + G.RENDER[lay](r2, G.Opts())
    elif kind == "swap_pages":
        pages = text.split("\f") if "\f" in text else None
        if not pages or len(pages) < 2:
            return None
        return "\f".join([pages[1], pages[0]] + pages[2:])
    elif kind == "insert_in_table":
        i = _row_end(L, r, 0)
        L.insert(i + 1, op[1])
    elif kind == "hidden":
        phrase, where = op[1], op[2]
        if where == "referrer":
            i = next((k for k, l in enumerate(L) if r.doctor.upper() in l.upper()), None)
            if i is None:
                return None
            L[i] = L[i] + "   " + phrase
        elif where == "note":
            L.insert(_end_line(L, lay) + 1, note_line(lay, phrase))
        else:
            i = next(k for k, l in enumerate(L) if r.patient_id in l)
            L[i] = L[i] + "   " + phrase
    else:
        raise ValueError(kind)
    return "\n".join(L)


# ----------------------------------------------------------------------------- catalogue + corpus
VALID = ["clean", "col_shift", "crlf_trailing", "drop_optional", "page_break", "long_name_overflow", "referrer_variation",
         "approved_note", "interpretive_note", "section_subheading", "footer_version_drift", "sex_specific_ranges",
         "abnormal_values", "accented_name", "bold_flag", "low_direct_bilirubin"]
POLICY = ["note_with_number", "unapproved_note_style", "static_text_damage", "multipage_unapproved", "long_name_wrapped"]
V1_DEFECTS = ["unit_incompatible", "unit_missing", "value_corrupt", "value_implausible", "patient_id_missing",
              "date_invalid", "duplicate_conflict", "unknown_test", "truncated", "layout_drift", "header_changed",
              "flag_inconsistent", "conflicting_patient_id"]
DEFECTS = V1_DEFECTS + ["header_changed_paged", "extra_section_unknown_tests", "two_patients_one_job", "page_order_swap",
                        "text_between_rows_with_number", "row_value_swap", "index_inconsistent", "bilirubin_inverted",
                        "protein_inverted", "differential_over_100", "hidden_numeric_result",
                        "hidden_qualitative_result", "wrong_code_page", "comma_decimal"]
FOREIGN = ["foreign_layout_G", "drifted_new_format"]
COUNTS = {"gen": None, "dev": {"clean": 12, "valid": 2, "policy": 1, "defect": 1},
          "test": {"clean": 25, "valid": 4, "policy": 3, "defect": 3}}


def build_split(split: str, base_seed: int) -> List[Doc]:
    docs = []
    for li, lay in enumerate(LAYOUTS):
        if split == "gen":
            for k in range(2):
                d = build(lay, base_seed + li * 100_000 + k, "clean")
                docs.append(d)
            continue
        C = COUNTS[split]
        for ci, cls in enumerate(VALID + POLICY + DEFECTS):
            group = "valid" if cls in VALID else "policy" if cls in POLICY else "defect"
            n = C["clean"] if cls == "clean" else C[group]
            k = 0
            for s in range(400):
                if k >= n:
                    break
                d = build(lay, base_seed + li * 100_000 + ci * 1000 + s, cls)
                if d is not None:
                    docs.append(d)
                    k += 1
    if split in ("dev", "test"):
        nf = 6 if split == "dev" else 15
        for cls in FOREIGN:
            k = 0
            for s in range(200):
                if k >= nf:
                    break
                lay = LAYOUTS[s % 6]
                d = build(lay, base_seed + 900_000 + (0 if cls == FOREIGN[0] else 10_000) + s, cls)
                if d is not None:
                    docs.append(d)
                    k += 1
    return docs


def write_split(out: Path, split: str, base_seed: int) -> Dict[str, int]:
    docs = build_split(split, base_seed)
    d = out / split
    d.mkdir(parents=True, exist_ok=True)
    for doc in docs:
        p = d / doc.layout / f"{doc.doc_id}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        j = doc.to_json()
        j["split"] = split
        p.write_text(json.dumps(j, indent=1, ensure_ascii=False))
    from collections import Counter
    return dict(Counter((x.group) for x in docs))
