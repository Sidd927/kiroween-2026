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

NAME_RE = regex.compile(r"^[A-Za-z][A-Za-z.,' -]{1,59}$")
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
    return issues
