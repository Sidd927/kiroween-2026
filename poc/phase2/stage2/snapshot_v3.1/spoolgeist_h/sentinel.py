"""Result sentinel (v3.1, fixes review finding RV-1 / audit F-23). NO LLM, binding-independent.

After a binding has extracted its result rows, every character of the document that was NOT consumed by a parsed
result row is scanned for result-like content. If any is found, the document is REJECTED: a printed value that the
record does not contain must never be dropped silently.

It does not trust the binding's skip/anchor regexes or field lines (which the LLM wrote); it only uses the
human-curated dictionary plus a fixed list of common clinical units and analyte words, like the validators.

Result-like content:
  R-A  a number immediately followed by a unit spelling        e.g. "138 mmol/L", "9.8 g/dL", "45 %"
  R-B  an analyte word followed on the same line by a number   e.g. "SODIUM 138", "repeat Hb 9.8 advised"

Trade-off: header or footer text that happens to look like this is rejected too (false rejection, never unsafe).
The false-rejection cost is measured on the valid sets and reported.
"""
from __future__ import annotations

from typing import Iterable, List

import regex

from .dictionary import DICT

EXTRA_UNITS = ["mmol/L", "mmol/l", "umol/L", "µmol/L", "mEq/L", "meq/L", "mg/L", "ng/mL", "ng/ml", "ng/dL",
               "pg/mL", "ug/dL", "µg/dL", "mcg/dL", "IU/mL", "U/mL", "mIU/L", "mIU/mL", "uIU/mL", "µIU/mL",
               "mm/hr", "mm/1st hr", "cells/uL", "/HPF", "/hpf", "/LPF", "sec", "secs", "seconds", "mOsm/kg"]
ANALYTES = ["SODIUM", "POTASSIUM", "CHLORIDE", "BICARBONATE", "CALCIUM", "PHOSPHORUS", "MAGNESIUM", "ESR", "HBA1C",
            "CHOLESTEROL", "TRIGLYCERIDE", "TRIGLYCERIDES", "HDL", "LDL", "VLDL", "TSH", "T3", "T4", "FT3", "FT4",
            "UREA", "BUN", "CREATININE", "URIC ACID", "BILIRUBIN", "GLUCOSE", "SUGAR", "HAEMOGLOBIN", "HEMOGLOBIN",
            "HB", "HGB", "PLATELET", "PLATELETS", "WBC", "RBC", "TLC", "DLC", "PCV", "HCT", "MCV", "MCH", "MCHC",
            "NEUTROPHILS", "LYMPHOCYTES", "EOSINOPHILS", "MONOCYTES", "BASOPHILS", "SGOT", "SGPT", "ALT", "AST",
            "ALP", "ALBUMIN", "GLOBULIN", "PROTEIN", "INR", "APTT", "CRP", "FERRITIN", "IRON", "VITAMIN"]
NUM = r"(?<![\w.])\d+(?:[.,]\d+)?"


def _units() -> List[str]:
    us = {u for t in DICT["tests"].values() for u in t["units"]} | set(EXTRA_UNITS)
    return sorted(us, key=len, reverse=True)


UNIT_RE = regex.compile(NUM + r"\s?(?:" + "|".join(regex.escape(u) for u in _units()) + r")(?![\w/])", regex.I)


def _analyte_re(extra_labels: Iterable[str]):
    words = {w.upper() for w in ANALYTES} | {" ".join(l.split()).upper() for l in extra_labels if len(l.strip()) >= 2}
    alt = "|".join(regex.escape(w) for w in sorted(words, key=len, reverse=True))
    return regex.compile(r"(?<![\w.])(?:" + alt + r")(?![\w])[^\n]{0,40}?" + NUM, regex.I)


def unconsumed_text(text: str, consumed_rows: List[str]) -> str:
    rest = text
    for row in consumed_rows:
        i = rest.find(row)
        if i >= 0:                      # if a row match cannot be located verbatim, its text stays -> fail closed
            rest = rest[:i] + "\n" + rest[i + len(row):]
    return rest


def scan(text: str, consumed_rows: List[str], labels: Iterable[str]) -> List[str]:
    rest = unconsumed_text(text, consumed_rows)
    hits = []
    for m in UNIT_RE.finditer(rest, timeout=1.0):
        hits.append(f"R-A value+unit {m.group(0)!r}")
        break
    m = _analyte_re(labels).search(rest, timeout=1.0)
    if m:
        hits.append(f"R-B analyte+number {' '.join(m.group(0).split())[:40]!r}")
    return hits
