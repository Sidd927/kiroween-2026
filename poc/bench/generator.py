"""Synthetic "legacy lab" report generator + perturbation catalogue + ground truth.

EVERYTHING here is synthetic. Names are drawn from small generic lists and combined
randomly; IDs are random. Every document carries the line
"SYNTHETIC SAMPLE - NOT A REAL PATIENT".

Layouts A, B, C are DEVELOPMENT layouts (the system may be tuned on their dev split).
Layouts D, E, F are UNSEEN layouts: the system is frozen before any D/E/F document is
shown to the rule generator or the interpreter.
Layout G has no binding: it is only used as a "foreign / unregistered layout" negative.

Ground truth is computed from the structured Report object, never from the rendered text,
so it is independent of the parser.
"""
from __future__ import annotations

import copy
import dataclasses
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

ESC = "\x1b"
SYNTH = "SYNTHETIC SAMPLE - NOT A REAL PATIENT"

FIRST = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Ananya", "Kiran", "Meera", "Arjun", "Pooja",
         "Rahul", "Divya", "Sameer", "Neha", "Aditya", "Kavya", "Nikhil", "Isha", "Omkar", "Tanvi"]
LAST = ["Kulkarni", "Deshmukh", "Patil", "Joshi", "Shinde", "Pawar", "Iyer", "Nair", "Rao", "Gupta",
        "Sharma", "Mehta", "Bhosale", "Jadhav", "Khan", "Fernandes", "Reddy", "Chavan", "More", "Gaikwad"]
LONG_NAMES = [("Venkataramana", "Subramanian Iyer"), ("Anantharaman", "Krishnaswamy"),
              ("Bhagyashree", "Deshpande-Kulkarni"), ("Rajalakshmi", "Chandrasekaran")]
DOCTORS = ["S. Joshi", "A. Rao", "M. Kulkarni", "P. Nair", "R. Shah", "V. Gupta"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


@dataclass
class Result:
    code: str
    label: str
    value: str          # printed value string
    unit: str           # printed unit string
    low: str            # printed reference low
    high: str           # printed reference high
    flag: str = ""      # "H" / "L" / "" (abnormal marker rendered per layout)
    method: str = ""    # layout C only


@dataclass
class Report:
    layout: str
    patient_id: str
    title: str
    first: str
    last: str
    age: int
    sex: str            # "M" / "F"
    collected: datetime
    reported: datetime
    doctor: str
    sample_id: str
    results: List[Result]
    collected_override: Optional[str] = None   # printed collected-date string override (invalid dates)
    page2_patient_id: Optional[str] = None     # conflicting ID on page 2 header (layout B)


@dataclass
class Opts:
    page_break_after: Optional[int] = None
    swap_value_ref: bool = False
    new_header: bool = False


# ----------------------------------------------------------------------------- test specs
# (code, label, unit, decimals, low, high, optional, method)
PANELS: Dict[str, List[Tuple]] = {
    "A": [("HGB", "HAEMOGLOBIN", "gm/dL", 1, 13.0, 17.0, False, ""),
          ("RBC", "R.B.C. COUNT", "mill/cumm", 2, 4.50, 5.50, False, ""),
          ("HCT", "P.C.V.", "%", 1, 40.0, 50.0, False, ""),
          ("MCV", "M.C.V.", "fL", 1, 83.0, 101.0, False, ""),
          ("MCH", "M.C.H.", "pg", 1, 27.0, 32.0, False, ""),
          ("MCHC", "M.C.H.C.", "g/dL", 1, 31.5, 34.5, False, ""),
          ("WBC", "TOTAL LEUCOCYTE COUNT", "/cumm", 0, 4000, 11000, False, ""),
          ("NEUT%", "NEUTROPHILS", "%", 0, 40, 80, True, ""),
          ("LYMPH%", "LYMPHOCYTES", "%", 0, 20, 40, True, ""),
          ("PLT", "PLATELET COUNT", "lakh/cumm", 2, 1.50, 4.10, False, "")],
    "B": [("HGB", "Haemoglobin", "g/dL", 1, 13.0, 17.0, False, ""),
          ("RBC", "RBC Count", "million/cumm", 2, 4.5, 5.5, False, ""),
          ("HCT", "PCV / Haematocrit", "%", 1, 40.0, 50.0, False, ""),
          ("MCV", "MCV", "fl", 1, 83.0, 101.0, False, ""),
          ("MCH", "MCH", "pg", 1, 27.0, 32.0, False, ""),
          ("MCHC", "MCHC", "g/dl", 1, 31.5, 34.5, False, ""),
          ("WBC", "Total WBC Count", "cells/cumm", 0, 4000, 11000, False, ""),
          ("NEUT%", "Neutrophils", "%", 0, 40, 80, True, ""),
          ("LYMPH%", "Lymphocytes", "%", 0, 20, 40, True, ""),
          ("PLT", "Platelet Count", "10^3/uL", 0, 150, 410, False, "")],
    "C": [("TBIL", "BILIRUBIN TOTAL", "mg/dl", 2, 0.20, 1.20, False, "Diazo method"),
          ("DBIL", "BILIRUBIN DIRECT", "mg/dl", 2, 0.00, 0.30, False, "Diazo method"),
          ("ALT", "SGPT (ALT)", "U/L", 0, 0, 40, False, "IFCC"),
          ("AST", "SGOT (AST)", "U/L", 0, 0, 40, False, "IFCC"),
          ("ALP", "ALKALINE PHOSPHATASE", "IU/L", 0, 40, 130, False, "PNPP-AMP"),
          ("TP", "TOTAL PROTEINS", "g/dl", 1, 6.0, 8.3, False, "Biuret"),
          ("ALB", "ALBUMIN", "g/dl", 1, 3.5, 5.2, False, "BCG"),
          ("CREA", "SERUM CREATININE", "mg/dl", 2, 0.60, 1.30, True, "Jaffe kinetic"),
          ("UREA", "BLOOD UREA", "mg/dl", 0, 15, 45, True, "Urease-GLDH")],
    "D": [("GLU", "Glucose (Fasting)", "mg/dL", 0, 70, 100, False, ""),
          ("CREA", "Serum Creatinine", "mg/dL", 2, 0.60, 1.20, False, ""),
          ("UREA", "Blood Urea", "mg/dL", 0, 15, 40, False, ""),
          ("HGB", "Haemoglobin", "g/dl", 1, 12.0, 16.0, False, ""),
          ("WBC", "Total Count (WBC)", "/cumm", 0, 4000, 11000, False, ""),
          ("PLT", "Platelets", "lakhs/cumm", 2, 1.50, 4.50, True, "")],
    "E": [("HGB", "Hb", "g/dL", 1, 13.0, 17.0, False, ""),
          ("RBC", "RBC", "x10^6/uL", 2, 4.50, 5.50, False, ""),
          ("WBC", "WBC", "x10^3/uL", 1, 4.0, 11.0, False, ""),
          ("PLT", "PLT", "x10^3/uL", 0, 150, 410, False, ""),
          ("HCT", "HCT", "%", 1, 40.0, 50.0, False, ""),
          ("MCV", "MCV", "fL", 1, 83.0, 101.0, False, ""),
          ("MCH", "MCH", "pg", 1, 27.0, 32.0, True, ""),
          ("MCHC", "MCHC", "g/dL", 1, 31.5, 34.5, True, "")],
    "F": [("HGB", "HEMOGLOBIN", "g/dL", 1, 12.0, 15.5, False, ""),
          ("HCT", "HEMATOCRIT", "%", 1, 36.0, 46.0, False, ""),
          ("WBC", "WBC", "K/uL", 1, 4.0, 11.0, False, ""),
          ("RBC", "RBC", "M/uL", 2, 4.00, 5.20, False, ""),
          ("PLT", "PLATELETS", "K/uL", 0, 150, 400, False, ""),
          ("MCV", "MCV", "fL", 1, 80.0, 100.0, False, ""),
          ("GLU", "GLUCOSE, FASTING", "mg/dL", 0, 70, 99, False, ""),
          ("CREA", "CREATININE", "mg/dL", 2, 0.50, 1.10, False, ""),
          ("ALT", "ALT", "U/L", 0, 7, 56, True, ""),
          ("AST", "AST", "U/L", 0, 10, 40, True, "")],
    "G": [("HGB", "Hemoglobin", "g/dL", 1, 13.0, 17.0, False, ""),
          ("WBC", "WBC", "K/uL", 1, 4.0, 11.0, False, ""),
          ("PLT", "Platelets", "K/uL", 0, 150, 400, False, "")],
}


def fmt_num(x: float, d: int) -> str:
    return f"{x:.{d}f}"


def gen_value(rng: random.Random, low: float, high: float, d: int) -> float:
    span = high - low if high > low else max(high, 1)
    lo = max(0.0, low - 0.35 * span)
    hi = high + 0.35 * span
    v = rng.uniform(lo, hi)
    if d == 0:
        v = round(v)
    return v


def make_report(layout: str, rng: random.Random, force_day_gt12: bool = False,
                force_day_le12: bool = False) -> Report:
    sex = rng.choice("MF")
    first, last = rng.choice(FIRST), rng.choice(LAST)
    day = rng.randint(13, 28) if force_day_gt12 else (rng.randint(1, 12) if force_day_le12 else rng.randint(1, 28))
    collected = datetime(2026, rng.randint(1, 10), day, rng.randint(7, 11), rng.choice([0, 5, 10, 15, 20, 30, 40, 45, 50]))
    reported = collected + timedelta(hours=rng.randint(3, 40), minutes=rng.choice([0, 10, 25, 35, 50]))
    title = {"A": ("MR." if sex == "M" else rng.choice(["MS.", "MRS."])),
             "D": ("SHRI" if sex == "M" else rng.choice(["SMT.", "KUM."]))}.get(layout, "")
    pid = {
        "A": f"SP/26/{rng.randint(1, 999999):06d}",
        "B": f"CDC-{rng.randint(100000, 999999)}",
        "C": f"{rng.randint(0, 9999999):07d}",
        "D": f"26-{rng.randint(0, 9999999):07d}",
        "E": f"LL-2026-{rng.randint(10000, 99999)}",
        "F": f"{rng.randint(0, 99999999):08d}",
        "G": f"GH{rng.randint(1000, 9999)}",
    }[layout]
    results = []
    for code, label, unit, d, low, high, optional, method in PANELS[layout]:
        if optional and rng.random() < 0.3:
            continue
        v = gen_value(rng, low, high, d)
        vs = fmt_num(v, d)
        flag = "H" if float(vs) > high else ("L" if float(vs) < low else "")
        results.append(Result(code, label, vs, unit, fmt_num(low, d), fmt_num(high, d), flag, method))
    return Report(layout, pid, title, first, last, rng.randint(1, 89), sex, collected, reported,
                  rng.choice(DOCTORS), f"S-{rng.randint(10000, 99999)}", results)


# ----------------------------------------------------------------------------- truth
def printed_name(r: Report) -> str:
    """Patient name exactly as the layout prints it (without honorific)."""
    if r.layout in ("A", "D"):
        return f"{r.first} {r.last}".upper()
    if r.layout == "C":
        return f"{r.last}, {r.first}"
    if r.layout == "F":
        return f"{r.last} {r.first}".upper()
    return f"{r.first} {r.last}"


def truth(r: Report) -> dict:
    return {
        "patient_id": r.patient_id,
        "patient_name": printed_name(r),
        "patient_age": r.age,
        "patient_sex": "male" if r.sex == "M" else "female",
        "collected": r.collected.strftime("%Y-%m-%d"),
        "results": [{"code": x.code, "value": x.value, "unit": x.unit, "label": x.label} for x in r.results],
    }


# ----------------------------------------------------------------------------- layouts
def L(s: str = "") -> str:
    return s.rstrip()


def render_A(r: Report, o: Opts) -> str:
    coll = r.collected_override or r.collected.strftime("%d/%m/%Y %H:%M")
    rep = r.reported.strftime("%d/%m/%Y %H:%M")
    name = f"{r.title} {printed_name(r)}".strip()
    if o.new_header:
        head = ["SUNRISE DIAGNOSTICS & PATHOLOGY PVT. LTD.".center(80),
                "NABL-style format v2  |  Gangapur Road, Nashik".center(80), "=" * 80]
    else:
        head = ["SUNRISE PATHOLOGY LABORATORY".center(80),
                "12, Station Road, Nashik - 422001  Ph: 0253-2345678".center(80), "-" * 80]
    hdr = head + [
        f"Patient Name : {name:<32} Lab No.   : {r.patient_id}",
        f"Age / Sex    : {str(r.age) + ' Yrs / ' + r.sex:<32} Collected : {coll}",
        f"Ref. By      : {'DR. ' + r.doctor.upper():<32} Reported  : {rep}",
        "-" * 80,
        "HAEMATOLOGY - COMPLETE BLOOD COUNT".center(80),
        "-" * 80,
    ]
    colhdr = (f"{'TEST':<30}{'REFERENCE RANGE':<18}{'RESULT':<12}{'UNIT'}" if o.swap_value_ref
              else f"{'TEST':<30}{'RESULT':<12}{'UNIT':<14}{'REFERENCE RANGE'}")
    lines = hdr + [colhdr, "-" * 80]
    for i, x in enumerate(r.results):
        if o.page_break_after is not None and i == o.page_break_after:
            lines += ["", f"{'Continued on next page...':>80}", "\f" + "SUNRISE PATHOLOGY LABORATORY".center(80),
                      f"Patient Name : {name:<32} Lab No.   : {r.patient_id}", "-" * 80, colhdr, "-" * 80]
        res = f"{x.value} {x.flag}".strip()
        rng_s = f"{x.low} - {x.high}"
        if o.swap_value_ref:
            lines.append(f"{x.label:<30}{rng_s:<18}{res:<12}{x.unit}")
        else:
            lines.append(f"{x.label:<30}{res:<12}{x.unit:<14}{rng_s}")
    lines += ["-" * 80, "*** END OF REPORT ***".center(80), SYNTH.center(80), "\f"]
    return "\n".join(L(s) for s in lines)


def render_B(r: Report, o: Opts) -> str:
    coll = r.collected_override or (r.collected.strftime("%d-%b-%Y %I:%M %p"))
    date = r.reported.strftime("%d-%b-%Y")
    title = "CITY DIAGNOSTIC CENTRE" if not o.new_header else "CITY DIAGNOSTICS (A UNIT OF CDC HEALTHCARE)"
    sexw = "Male" if r.sex == "M" else "Female"

    def header(page: int, pid: str) -> List[str]:
        return [ESC + "@" + ESC + "E" + title.center(64) + ESC + "F",
                "Plot 7, MIDC Area, Aurangabad - 431001".center(64),
                f"Reg. No : {pid:<22}Date : {date}",
                f"Name    : {printed_name(r):<22}Age  : {r.age} Y   Sex : {sexw}",
                f"Sample collected on : {coll}",
                f"Referred by : Dr. {r.doctor}",
                f"{'Page ' + str(page) + ' of 2':>64}",
                "=" * 64]

    def colhdr() -> str:
        return (f"{'Investigation':<26}{'Biological Ref.':<17}{'Value':<9}{'Units'}" if o.swap_value_ref
                else f"{'Investigation':<26}{'Value':<9}{'Units':<14}{'Biological Ref.'}")

    brk = o.page_break_after if o.page_break_after is not None else 6
    lines = header(1, r.patient_id) + [colhdr(), "-" * 64]
    for i, x in enumerate(r.results):
        if i == brk:
            lines += ["-" * 64, f"{'(continued)':>64}", "\f"]
            lines += header(2, r.page2_patient_id or r.patient_id) + [colhdr(), "-" * 64]
        dots = (x.label + " ").ljust(25, ".") + " "
        val = x.value
        if x.flag:  # abnormal values are printed in bold (ESC E ... ESC F); no H/L letters
            valtxt = ESC + "E" + f"{val:<9}" + ESC + "F"
        else:
            valtxt = f"{val:<9}"
        rng_s = f"{x.low}-{x.high}"
        if o.swap_value_ref:
            lines.append(dots + f"{rng_s:<17}" + valtxt + x.unit)
        else:
            lines.append(dots + valtxt + f"{x.unit:<14}" + rng_s)
    lines += ["-" * 64, "Values in bold are outside the biological reference interval.",
              "--- End of Report ---".center(64), SYNTH, "\f"]
    return "\n".join(L(s) for s in lines)


def render_C(r: Report, o: Opts) -> str:
    coll = r.collected_override or r.collected.strftime("%Y-%m-%d %H:%M")
    title = "DR. MEHTA'S CLINICAL LABORATORY" if not o.new_header else "MEHTA PATHCARE DIAGNOSTICS LLP"
    lines = [f"{title:<44}Report Date: {r.reported.strftime('%Y-%m-%d')}",
             f"Patient : {printed_name(r)} ({r.sex}/{r.age})",
             f"Patient ID : {r.patient_id:<14}Sample : {r.sample_id}",
             f"Collected  : {coll}",
             f"Consultant : Dr. {r.doctor}",
             "",
             "BIOCHEMISTRY",
             "  Test / Method",
             ("      Normal Range      Result     Units" if o.swap_value_ref else "      Result     Units     Normal Range"),
             "  " + "-" * 40]
    for x in r.results:
        lines.append(f"  {x.label}")
        lines.append(f"      ({x.method})")
        val = f"{x.value} *" if x.flag else x.value
        rng_s = f"{x.low} - {x.high}"
        if o.swap_value_ref:
            lines.append(f"      {rng_s:<18}{val:<11}{x.unit}")
        else:
            lines.append(f"      {val:<11}{x.unit:<10}{rng_s}")
    lines += ["  " + "-" * 40, "  * Value outside normal range", "", "Checked by: Lab Technologist",
              "                           -- END --", SYNTH, "\f"]
    return "\n".join(L(s) for s in lines)


def render_D(r: Report, o: Opts) -> str:
    coll = r.collected_override or r.collected.strftime("%d.%m.%y")
    title = "SHREE SAI DIAGNOSTICS" if not o.new_header else "SHREE SAI HEALTH LABS (NEW FORMAT)"
    name = f"{r.title} {printed_name(r)}"
    border = "+" + "-" * 21 + "+" + "-" * 9 + "+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 6 + "+"
    top = "+" + "-" * 64 + "+"

    def row(a, b, c, d, e):
        return f"| {a:<19} | {b:<7} | {c:<10} | {d:<10} | {e:<4} |"

    def headblock():
        return [top, f"|{title:^64}|", f"|{'Near Bus Stand, Shirdi Road, Kopargaon':^64}|", top,
                f"| UHID : {r.patient_id:<22}| Coll. Dt : {coll:<20}|",
                f"| Name : {name:<22}| Age/Sex : {str(r.age) + '/' + r.sex:<21}|"]

    colh = row("PARAMETER", "RANGE", "UNIT", "VALUE", "FLAG") if o.swap_value_ref else row("PARAMETER", "VALUE", "UNIT", "RANGE", "FLAG")
    lines = headblock() + [border, colh, border]
    for i, x in enumerate(r.results):
        if o.page_break_after is not None and i == o.page_break_after:
            lines += [border, "\f"] + headblock() + [border, colh, border]
        rng_s = f"{x.low}-{x.high}"
        if o.swap_value_ref:
            lines.append(row(x.label, rng_s, x.unit, x.value, x.flag))
        else:
            lines.append(row(x.label, x.value, x.unit, rng_s, x.flag))
    lines += [border, f"|{'** End of Report **':^64}|", top, SYNTH, "\f"]
    return "\n".join(L(s) for s in lines)


def render_E(r: Report, o: Opts) -> str:
    coll = r.collected_override or f"{MONTHS[r.collected.month - 1]} {r.collected.day}, {r.collected.year}"
    title = "LIFELINE PATHOLOGY & IMAGING" if not o.new_header else "LIFELINE LABS - DIGITAL REPORT"
    lines = [f"{title:<52}Lab ID: {r.patient_id}",
             f"Patient: {printed_name(r):<22}Sex/Age: {r.sex}/{r.age:<10}Drawn: {coll}",
             "_" * 78,
             "HAEMOGRAM"]

    def cell(x: Result) -> str:
        v = f"{x.value} !" if x.flag else x.value
        if o.swap_value_ref:
            return f"{x.label:<8}[{x.low}-{x.high}] {v} {x.unit}"
        return f"{x.label:<8}{v:>7} {x.unit:<9}[{x.low}-{x.high}]"

    res = r.results
    for i in range(0, len(res), 2):
        left = cell(res[i])
        right = cell(res[i + 1]) if i + 1 < len(res) else ""
        lines.append(f"{left:<39}{right}")
    lines += ["_" * 78, "! = outside reference interval        Report generated by LabSys 3.1",
              SYNTH, "\f"]
    return "\n".join(L(s) for s in lines)


def render_F(r: Report, o: Opts) -> str:
    coll = r.collected_override or r.collected.strftime("%m/%d/%Y %H%M")
    recv = r.reported.strftime("%m/%d/%Y %H%M")
    title = "MEDILINK REFERENCE LAB" if not o.new_header else "MEDILINK LABORATORIES INC"
    acc = r.sample_id.replace("S-", "44")

    def head():
        return [f"{title}  -  ACCESSION {acc}",
                f"PT: {printed_name(r):<22} MRN {r.patient_id}    AGE: {r.age}Y  SEX: {r.sex}",
                f"COLLECTED {coll}   RECEIVED {recv}",
                "=" * 72]

    colh = (f"{'TEST NAME (UNITS)':<36}{'REF':<14}{'RESULT':<10}FLAG" if o.swap_value_ref
            else f"{'TEST NAME (UNITS)':<36}{'RESULT':<10}{'FLAG':<7}REF")
    lines = head() + [colh, "-" * 72]
    for i, x in enumerate(r.results):
        if o.page_break_after is not None and i == o.page_break_after:
            lines += ["\f"] + head() + [colh, "-" * 72]
        name = f"{x.label} ({x.unit})" if x.unit else x.label
        if o.swap_value_ref:
            lines.append(f"{name:<36}{x.low + '-' + x.high:<14}{x.value:<10}{x.flag}")
        else:
            lines.append(f"{name:<36}{x.value:<10}{x.flag:<7}{x.low}-{x.high}")
    lines += ["-" * 72, "END OF REPORT", SYNTH, "\f"]
    return "\n".join(L(s) for s in lines)


def render_G(r: Report, o: Opts) -> str:
    lines = ["GOOD HEALTH CLINIC LAB", f"Patient {printed_name(r)}  ID {r.patient_id}",
             f"Date {r.collected.strftime('%Y/%m/%d')}", ""]
    for x in r.results:
        lines.append(f"{x.label}: {x.value} {x.unit} (ref {x.low}-{x.high})")
    lines += ["", SYNTH, "\f"]
    return "\n".join(lines)


RENDER: Dict[str, Callable[[Report, Opts], str]] = {
    "A": render_A, "B": render_B, "C": render_C, "D": render_D, "E": render_E, "F": render_F, "G": render_G}

INVALID_DATE = {"A": "31/02/2026 09:10", "B": "31-Feb-2026 09:10 AM", "C": "2026-02-31 09:10",
                "D": "31.02.26", "E": "February 31, 2026", "F": "02/31/2026 0910"}
WRONG_UNIT = {"U/L": "mg/dL"}  # default wrong unit is "U/L" unless the test already is an enzyme
PAGEABLE = {"A", "B", "D", "F"}
FLAG_HL = {"A", "D", "F"}   # layouts printing explicit H/L letters


# ----------------------------------------------------------------------------- perturbations
def _pick(rng, results, pred=lambda x: True):
    c = [i for i, x in enumerate(results) if pred(x)]
    return rng.choice(c) if c else None


def p_col_shift(r, o, rng):
    return r, o, "accept", "text:col_shift"


def p_drop_optional(r, o, rng):
    i = _pick(rng, r.results[1:])
    if i is None:
        return None
    del r.results[i + 1]
    return r, o, "accept", None


def p_page_break(r, o, rng):
    if r.layout not in PAGEABLE or len(r.results) < 4:
        return None
    o.page_break_after = rng.randint(2, len(r.results) - 2)
    return r, o, "accept", None


def p_crlf(r, o, rng):
    return r, o, "accept", "text:crlf"


def p_long_name(r, o, rng):
    r.first, r.last = rng.choice(LONG_NAMES)
    return r, o, "accept", None


def p_unit_incompatible(r, o, rng):
    i = _pick(rng, r.results)
    x = r.results[i]
    x.unit = "mg/dL" if x.unit in ("U/L", "IU/L") else "U/L"
    return r, o, "reject", None


def p_unit_missing(r, o, rng):
    r.results[_pick(rng, r.results)].unit = ""
    return r, o, "reject", None


def p_value_corrupt(r, o, rng):
    x = r.results[_pick(rng, r.results)]
    v = x.value
    choices = []
    if "0" in v:
        choices.append(v.replace("0", "O", 1))
    if "1" in v:
        choices.append(v.replace("1", "l", 1))
    if "." in v:
        choices.append(v.replace(".", "..", 1))
    choices += ["--", "####"]
    x.value = rng.choice(choices)
    return r, o, "reject", None


def p_value_implausible(r, o, rng, dictionary=None):
    from spoolgeist.dictionary import DICT
    for idx in rng.sample(range(len(r.results)), len(r.results)):
        x = r.results[idx]
        spec = DICT["tests"][x.code]
        f = Decimal(str(spec["units"].get(x.unit, 1)))
        lo, hi = spec["plausible"]
        for cand in (x.value.replace(".", ""), x.value + "00", "9" + x.value.replace(".", "") + "0"):
            try:
                nv = Decimal(cand) * f
            except Exception:
                continue
            if nv > Decimal(str(hi)) or nv < Decimal(str(lo)):
                x.value = cand
                return r, o, "reject", None
    return None


def p_patient_id_missing(r, o, rng):
    r.patient_id = ""
    return r, o, "reject", None


def p_date_invalid(r, o, rng):
    r.collected_override = INVALID_DATE[r.layout]
    return r, o, "reject", None


def p_duplicate_conflict(r, o, rng):
    i = _pick(rng, r.results)
    dup = copy.deepcopy(r.results[i])
    d = len(dup.value.split(".")[1]) if "." in dup.value else 0
    dup.value = fmt_num(float(dup.value) * rng.choice([0.8, 1.25]) + (1 if d == 0 else 0), d)
    r.results.insert(i + 1, dup)
    return r, o, "reject", None


def p_unknown_test(r, o, rng):
    i = _pick(rng, r.results, lambda x: len(x.label) >= 5)
    x = r.results[i if i is not None else _pick(rng, r.results)]
    if len(x.label) < 5:
        x.label = x.label[:-1] + "X"
        return r, o, "reject", None
    labels = {y.label for y in r.results}
    for _ in range(10):
        k = rng.randint(1, len(x.label) - 2)
        cand = x.label[:k] + x.label[k + 1:]
        if cand not in labels and cand.strip() == cand and cand.replace(" ", ""):
            x.label = cand
            return r, o, "reject", None
    x.label = x.label + "X"
    return r, o, "reject", None


def p_truncated(r, o, rng):
    return r, o, "reject", "text:truncate"


def p_layout_drift(r, o, rng):
    o.swap_value_ref = True
    return r, o, "reject", None


def p_header_changed(r, o, rng):
    o.new_header = True
    return r, o, "reject", None


def p_flag_inconsistent(r, o, rng):
    if r.layout not in FLAG_HL:
        return None
    i = _pick(rng, r.results, lambda x: x.flag == "")
    if i is None:
        return None
    r.results[i].flag = rng.choice("HL")
    return r, o, "reject", None


def p_conflicting_id(r, o, rng):
    if r.layout != "B" or len(r.results) <= 6:
        return None
    r.page2_patient_id = f"CDC-{rng.randint(100000, 999999)}"
    return r, o, "reject", None


PERTURBATIONS = {
    # valid variations: a correct system should ACCEPT with exactly the ground truth (or abstain)
    "col_shift": p_col_shift, "drop_optional": p_drop_optional, "page_break": p_page_break,
    "crlf_trailing": p_crlf, "long_name": p_long_name,
    # invalid / ambiguous documents: a correct system must REJECT
    "unit_incompatible": p_unit_incompatible, "unit_missing": p_unit_missing,
    "value_corrupt": p_value_corrupt, "value_implausible": p_value_implausible,
    "patient_id_missing": p_patient_id_missing, "date_invalid": p_date_invalid,
    "duplicate_conflict": p_duplicate_conflict, "unknown_test": p_unknown_test,
    "truncated": p_truncated, "layout_drift": p_layout_drift, "header_changed": p_header_changed,
    "flag_inconsistent": p_flag_inconsistent, "conflicting_patient_id": p_conflicting_id,
}


def apply_text_op(text: str, op: Optional[str], r: Report, rng: random.Random) -> str:
    if op is None:
        return text
    if op == "text:crlf":
        return "\r\n".join(line + " " * rng.randint(0, 3) for line in text.split("\n"))
    if op == "text:truncate":
        lines = text.split("\n")
        cut = int(len(lines) * rng.uniform(0.45, 0.7))
        return "\n".join(lines[:cut])
    if op == "text:col_shift":
        import re
        labels = [x.label for x in r.results]
        out = []
        for line in text.split("\n"):
            if any(lb in line for lb in labels):
                runs = [m for m in re.finditer(r" {3,}", line)]
                if runs:
                    m = rng.choice(runs)
                    delta = rng.choice([-1, 1, 2])
                    n = max(2, len(m.group()) + delta)
                    line = line[:m.start()] + " " * n + line[m.end():]
            out.append(line)
        return "\n".join(out)
    raise ValueError(op)


def build_doc(layout: str, seed: int, perturbation: Optional[str] = None, **kw) -> Optional[dict]:
    rng = random.Random(seed)
    r = make_report(layout, rng, **kw)
    o = Opts()
    expected, op = "accept", None
    if perturbation:
        res = PERTURBATIONS[perturbation](r, o, rng)
        if res is None:
            return None
        r, o, expected, op = res
    text = RENDER[layout](r, o)
    text = apply_text_op(text, op, r, rng)
    return {
        "doc_id": f"{layout}-{seed}-{perturbation or 'clean'}",
        "layout": layout,
        "perturbation": perturbation or "clean",
        "expected": expected,
        "expected_layout": None if (perturbation == "header_changed" or layout == "G") else layout,
        "truth": truth(r) if expected == "accept" else None,
        "text": text,
    }


# ----------------------------------------------------------------------------- corpus
DEV_LAYOUTS = ["A", "B", "C"]
UNSEEN_LAYOUTS = ["D", "E", "F"]


def build_corpus(out: Path) -> dict:
    """Splits per layout (disjoint seeds):
       gen   : 2 clean docs given to the rule generator (the only docs the LLM sees for that layout)
       dev   : 8 clean + 1 of each applicable perturbation (activation gate + repair feedback)
       test  : 20 clean + 2 of each applicable perturbation (held out; never used for generation or repair)
    """
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"splits": {}}
    for lay in DEV_LAYOUTS + UNSEEN_LAYOUTS:
        base = {"A": 1000, "B": 2000, "C": 3000, "D": 4000, "E": 5000, "F": 6000}[lay] * 10
        splits = {"gen": [], "dev": [], "test": []}
        # gen: for F the generator samples include one day>12 date so that MM/DD is inferable
        splits["gen"].append(build_doc(lay, base + 1, force_day_gt12=True))
        splits["gen"].append(build_doc(lay, base + 2))
        for k in range(8):
            splits["dev"].append(build_doc(lay, base + 100 + k))
        for j, p in enumerate(PERTURBATIONS):
            d = build_doc(lay, base + 200 + j, p)
            if d:
                splits["dev"].append(d)
        for k in range(20):
            # half of the held-out clean docs have day<=12 to expose DD/MM vs MM/DD confusions
            splits["test"].append(build_doc(lay, base + 1000 + k, force_day_le12=(k % 2 == 0)))
        for j, p in enumerate(PERTURBATIONS):
            for rep in range(2):
                d = build_doc(lay, base + 2000 + 10 * j + rep, p)
                if d:
                    splits["test"].append(d)
        for name, docs in splits.items():
            for d in docs:
                d["split"] = name
                p = out / name / lay / f"{d['doc_id']}.json"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(d, indent=1))
            manifest["splits"].setdefault(name, {})[lay] = [d["doc_id"] for d in docs]
    # unregistered layout G: negatives only, in test split
    gdocs = [build_doc("G", 90000 + k) for k in range(10)]
    for d in gdocs:
        d["split"] = "test"
        d["expected"] = "reject"
        d["truth"] = None
        p = out / "test" / "G" / f"{d['doc_id']}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(d, indent=1))
    manifest["splits"]["test"]["G"] = [d["doc_id"] for d in gdocs]
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    m = build_corpus(Path(__file__).resolve().parents[1] / "data" / "corpus")
    for s, lays in m["splits"].items():
        print(s, {k: len(v) for k, v in lays.items()})
