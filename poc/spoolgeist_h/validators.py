"""Independent validators. They know NOTHING about the binding that produced the record;
they only use the human-curated dictionary and universal sanity rules. The LLM never
writes or edits this file at runtime.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

import regex

from .dictionary import DICT, unit_factor

# v4 (F-11 fixed first): decoding is now strict with a declared code page, so Unicode letters are safe to allow
NAME_RE = regex.compile(r"^\p{L}[\p{L}\p{M}.,' -]{1,59}$")
_SCRIPTS = ["Latin", "Greek", "Cyrillic", "Devanagari", "Bengali", "Gurmukhi", "Gujarati", "Tamil", "Telugu",
            "Kannada", "Malayalam", "Arabic", "Hebrew", "Han", "Hiragana", "Katakana", "Hangul", "Thai"]


def _scripts(name: str) -> set:
    """v4 (F-11, found by tests_h/test_v4.py): a real name is written in one script; mis-decoded bytes typically
    produce a mix (e.g. 'Zoδ' = cp1252 'Zoë' read as cp437)."""
    out = set()
    for ch in name:
        if ch.isalpha():
            out.add(next((s for s in _SCRIPTS if regex.match(r"\p{Script=" + s + r"}", ch)), "Other"))
    return out


ID_RE = regex.compile(r"^[A-Za-z0-9/_.-]{3,30}$")


def validate(rec: dict, today: date = None) -> List[str]:
    today = today or date.today()
    issues: List[str] = []
    # --- required + identity fields
    pid, name = rec.get("patient_id"), rec.get("patient_name")
    if not pid:
        issues.append("V1 missing patient_id")
    elif not ID_RE.match(pid) or not regex.search(r"[0-9]", pid):
        issues.append(f"V3 implausible patient_id {pid!r}")
    if not name:
        issues.append("V1 missing patient_name")
    elif not NAME_RE.match(name) or "  " in name or ":" in name:
        issues.append(f"V2 implausible patient_name {name!r}")
    elif len(_scripts(name)) > 1:
        issues.append(f"V2 patient_name mixes writing systems {sorted(_scripts(name))} (likely wrong code page)")
    elif regex.search(r"\b(MR|MRS|MS|SMT|SHRI|KUM|DR)\b\.?", name, regex.I) and regex.match(r"^(MR|MRS|MS|SMT|SHRI|KUM|DR)\b", name, regex.I):
        issues.append(f"V2 honorific left in patient_name {name!r}")
    # --- dates
    c = rec.get("collected")
    if not c:
        issues.append("V1 missing collected date")
    else:
        cd = date.fromisoformat(c)
        if not (date(2000, 1, 1) <= cd <= today + timedelta(days=1)):
            issues.append(f"V4 collected date out of window {c}")
        r = rec.get("reported")
        if r:
            rd = date.fromisoformat(r)
            if rd < cd or (rd - cd).days > 30:
                issues.append(f"V4 reported {r} inconsistent with collected {c}")
    # --- demographics
    age = rec.get("patient_age")
    if age is not None and not (0 <= age <= 120):
        issues.append(f"V8 implausible age {age}")
    if rec.get("patient_sex") not in (None, "male", "female", "other", "unknown"):
        issues.append(f"V8 bad sex {rec.get('patient_sex')!r}")
    # --- results
    results = rec.get("results") or []
    if not results:
        issues.append("V1 no results")
    seen = {}
    for x in results:
        code = x["code"]
        spec = DICT["tests"].get(code)
        if spec is None:
            issues.append(f"V5 unknown test code {code}")
            continue
        if code in seen:
            issues.append(f"V5 duplicate test {code} ({seen[code]} vs {x['value']})")
        seen[code] = x["value"]
        f = unit_factor(code, x["unit"])
        if f is None:
            issues.append(f"V5 unit {x['unit']!r} not valid for {code}")
            continue
        v = Decimal(x["value"])
        vc = v * f
        lo, hi = (Decimal(str(z)) for z in spec["plausible"])
        if not (lo <= vc <= hi):
            issues.append(f"V5 implausible {code}={vc} {spec['ucum']} (limits {lo}-{hi})")
        rl, rh = x.get("ref_low"), x.get("ref_high")
        if rl is not None and rh is not None:
            rl, rh = Decimal(rl), Decimal(rh)
            if rl > rh:
                issues.append(f"V7 reference range inverted for {code}")
            # column-confusion guard: value wildly off the printed reference interval
            elif rh > 0 and (v > rh * 50 or (rl > 0 and v < rl / 50)):
                issues.append(f"V7 {code} value {v} incompatible with reference {rl}-{rh}")
            fl = x.get("flag") or ""
            if fl == "H" and not v > rh:
                issues.append(f"V6 flag H but {code}={v} not above {rh}")
            if fl == "L" and not v < rl:
                issues.append(f"V6 flag L but {code}={v} not below {rl}")
            if fl == "A" and rl <= v <= rh:
                issues.append(f"V6 flag A but {code}={v} within {rl}-{rh}")
    issues += domain_consistency(results)
    return issues


# ----------------------------------------------------------------------------- V9 domain consistency (v4)
def _interval(x: dict):
    """Printed value -> [lo, hi] in canonical units, from its printed precision (half a unit of the last digit)."""
    v = Decimal(x["value"])
    d = -v.as_tuple().exponent if v.as_tuple().exponent < 0 else 0
    h = Decimal(5) / (Decimal(10) ** (d + 1))
    f = unit_factor(x["code"], x["unit"])
    return (v - h) * f, (v + h) * f


def domain_consistency(results: list) -> List[str]:
    """Definitional relationships only (report 03): every check uses interval arithmetic on the printed precision,
    so rounding can never trigger it. Approximate clinical relationships are deliberately NOT checked."""
    by = {}
    for x in results:
        if x["code"] in by or unit_factor(x["code"], x["unit"]) is None:
            continue
        by[x["code"]] = _interval(x)
    out = []

    def div(a, b, k):                       # k * a / b for positive intervals
        return k * a[0] / b[1], k * a[1] / b[0]

    def check(name, derived, code):
        lo, hi = by[code]
        if hi < derived[0] or lo > derived[1]:
            out.append(f"V9 {code} inconsistent with {name} (printed {lo:.2f}-{hi:.2f}, implied {derived[0]:.2f}-{derived[1]:.2f})")

    pos = all(by.get(c, (1, 1))[0] > 0 for c in ("HCT", "RBC"))
    if pos and {"HCT", "RBC", "MCV"} <= set(by):
        check("HCT x 10 / RBC", div(by["HCT"], by["RBC"], 10), "MCV")
    if pos and {"HGB", "RBC", "MCH"} <= set(by):
        check("HGB x 10 / RBC", div(by["HGB"], by["RBC"], 10), "MCH")
    if pos and {"HGB", "HCT", "MCHC"} <= set(by):
        check("HGB x 100 / HCT", div(by["HGB"], by["HCT"], 100), "MCHC")
    if {"NEUT%", "LYMPH%"} <= set(by) and by["NEUT%"][0] + by["LYMPH%"][0] > 100:
        out.append("V9 NEUT% + LYMPH% exceed 100% of the leucocyte differential")
    if {"DBIL", "TBIL"} <= set(by) and by["DBIL"][0] > by["TBIL"][1]:
        out.append("V9 direct bilirubin exceeds total bilirubin")
    if {"ALB", "TP"} <= set(by) and by["ALB"][0] >= by["TP"][1]:
        out.append("V9 albumin is not less than total protein")
    return out
