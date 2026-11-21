"""Scoring: compares a pipeline outcome with the independently generated ground truth."""
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional, Tuple

CRITICAL = ("patient_id", "patient_name", "collected")


def _n(s) -> str:
    return " ".join(str(s).split()).upper()


def _results_key(results) -> List[Tuple[str, Decimal, str]]:
    out = []
    for x in results:
        try:
            out.append((x["code"], Decimal(str(x["value"])), x["unit"]))
        except Exception:
            out.append((x.get("code"), None, x.get("unit")))
    return sorted(out, key=lambda t: (str(t[0]), str(t[1]), str(t[2])))


def field_checks(rec: dict, truth: dict) -> Dict[str, bool]:
    """Per-field correctness. Keys prefixed 'crit:' are critical fields."""
    chk = {
        "crit:patient_id": rec.get("patient_id") == truth["patient_id"],
        "crit:patient_name": _n(rec.get("patient_name") or "") == _n(truth["patient_name"]),
        "crit:collected": rec.get("collected") == truth["collected"],
        "patient_age": rec.get("patient_age") in (None, truth["patient_age"]) and rec.get("patient_age") is not None,
        "patient_sex": rec.get("patient_sex") == truth["patient_sex"],
    }
    got = {x["code"]: x for x in rec.get("results") or []}
    for t in truth["results"]:
        g = got.get(t["code"])
        ok = g is not None and Decimal(str(g["value"])) == Decimal(t["value"]) and g["unit"] == t["unit"]
        chk[f"crit:result:{t['code']}"] = ok
    extra = set(got) - {t["code"] for t in truth["results"]}
    for code in extra:
        chk[f"crit:result_extra:{code}"] = False
    return chk


def classify(outcome_status: str, rec: Optional[dict], doc: dict) -> str:
    """correct_accept | silent_error | false_reject | correct_reject | unsafe_accept"""
    if doc["expected"] == "accept":
        if outcome_status == "ACCEPT":
            ok = all(v for k, v in field_checks(rec, doc["truth"]).items() if k.startswith("crit:"))
            return "correct_accept" if ok else "silent_error"
        return "false_reject"
    return "unsafe_accept" if outcome_status == "ACCEPT" else "correct_reject"
