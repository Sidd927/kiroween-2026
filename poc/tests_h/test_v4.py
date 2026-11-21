"""v4 regression tests (Stage 3): independence, notes, V9 domain consistency, bold flags, code pages, overstrike,
note-continuation bug (EXPERIMENT_LOG 56-57), FHIR notes."""
from __future__ import annotations

import ast
import base64
import glob
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bench import generator as G                       # noqa: E402
from bench2 import generator as B2                     # noqa: E402
from spoolgeist_h import validators                    # noqa: E402
from spoolgeist_h.grid import normalize                # noqa: E402
from spoolgeist_h.pipeline import Pipeline             # noqa: E402

P = Pipeline(allow_agent_approval=True)
RUNTIME_MODULES = ["interpreter", "validators", "grid", "sentinel", "pipeline", "capture", "compile", "gate",
                   "registry", "approval", "fhir_builder", "dictionary", "llm"]


def _doc(lay, seed=970_000, **kw):
    r = B2.make_report(lay, random.Random(seed), **kw)
    return r, G.RENDER[lay](r, G.Opts())


def run(text, lay="A", cp=None):
    return P.process_bytes(B2.encode(text, lay) if cp is None else text.encode(cp), B2.QUEUE_CODEPAGE[lay] if cp is None else cp)


# ----------------------------------------------------------------------------- independence
@pytest.mark.parametrize("mod", RUNTIME_MODULES)
def test_system_never_imports_benchmark_code(mod):
    tree = ast.parse((ROOT / "spoolgeist_h" / f"{mod}.py").read_text())
    names = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module] + \
            [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not [x for x in names if x.split(".")[0] in ("bench", "bench2", "tests", "tests_h", "phase2")], names


# ----------------------------------------------------------------------------- notes
@pytest.mark.parametrize("lay", list("ABCDEF"))
def test_approved_note_preserved_not_dropped(lay):
    r, t = _doc(lay)
    L = t.split("\n")
    i = B2._end_line(L, lay)
    note = B2.note_line(lay, "Clinical correlation advised.")
    L.insert(i + 1, note)
    oc = run("\n".join(L), lay)
    assert oc.status == "ACCEPT", oc.reasons
    assert any("clinical correlation advised." in n.casefold() for n in oc.record["notes"])


def test_in_table_note_never_swallows_rows_layout_C():
    """EXPERIMENT_LOG 56: an in-table note followed by C's indented rows swallowed 4 results (silent error)."""
    for s in range(15):
        r, t = _doc("C", 971_000 + s)
        L = t.split("\n")
        i = B2._row_end(L, r, 1)
        L.insert(i + 1, B2.note_line("C", "Fasting status not stated."))
        oc = run("\n".join(L), "C")
        if oc.status == "ACCEPT":
            assert {x["code"] for x in oc.record["results"]} == {x.code for x in r.results}


@pytest.mark.parametrize("text", ["Repeat after 2 days.", "HIV reactive", "Hb was low, HAEMOGLOBIN rechecked"])
def test_note_with_number_qualitative_or_label_rejected(text):
    r, t = _doc("A")
    L = t.split("\n")
    L.insert(B2._end_line(L, "A") + 1, "Note: " + text)
    assert run("\n".join(L)).status == "REJECT"


def test_unapproved_note_style_rejected():
    r, t = _doc("A")
    L = t.split("\n")
    L.insert(B2._end_line(L, "A") + 1, "*** Sample slightly haemolysed. ***")
    assert run("\n".join(L)).status == "REJECT"


# ----------------------------------------------------------------------------- V9
def _rec(**vals):
    units = {"HGB": "g/dL", "HCT": "%", "RBC": "x10^6/uL", "MCV": "fL", "MCH": "pg", "MCHC": "g/dL", "NEUT%": "%",
             "LYMPH%": "%", "TBIL": "mg/dL", "DBIL": "mg/dL", "TP": "g/dL", "ALB": "g/dL"}
    return [{"code": k.replace("NEUT", "NEUT%").replace("LYMPH", "LYMPH%") if k in ("NEUT", "LYMPH") else k,
             "value": v, "unit": units[k + "%" if k in ("NEUT", "LYMPH") else k]} for k, v in vals.items()]


def test_V9_consistent_cbc_passes_including_rounding():
    # Hb 14.0, RBC 4.80, MCV 90.0 -> Hct 43.2, MCH 29.2, MCHC 32.4 (rounded)
    assert validators.domain_consistency(_rec(HGB="14.0", RBC="4.80", HCT="43.2", MCV="90.0", MCH="29.2", MCHC="32.4")) == []


@pytest.mark.parametrize("field,val", [("MCV", "99.0"), ("MCH", "32.5"), ("MCHC", "36.0")])
def test_V9_inconsistent_index_rejected(field, val):
    vals = dict(HGB="14.0", RBC="4.80", HCT="43.2", MCV="90.0", MCH="29.2", MCHC="32.4")
    vals[field] = val
    assert any(field in i for i in validators.domain_consistency(_rec(**vals)))


def test_V9_hct_mchc_swap_rejected():
    assert validators.domain_consistency(_rec(HGB="14.0", RBC="4.80", HCT="32.4", MCV="90.0", MCH="29.2", MCHC="43.2"))


def test_V9_definitional_bounds():
    assert validators.domain_consistency(_rec(NEUT="70", LYMPH="35"))
    assert validators.domain_consistency(_rec(TBIL="0.80", DBIL="1.10"))
    assert validators.domain_consistency(_rec(TP="6.5", ALB="6.9"))
    assert validators.domain_consistency(_rec(NEUT="60", LYMPH="35", TBIL="1.10", DBIL="0.00", TP="7.0", ALB="4.2")) == []


# ----------------------------------------------------------------------------- bold flags, code pages, overstrike
def test_bold_abnormal_marker_layout_B():
    hit = 0
    for s in range(30):
        r, t = _doc("B", 972_000 + s)
        oc = run(t, "B")
        assert oc.status == "ACCEPT", oc.reasons
        exp = {x.code: bool(x.flag) for x in r.results}
        got = {x["code"]: bool(x["flag"]) for x in oc.record["results"]}
        assert got == exp
        hit += any(exp.values())
    assert hit > 0


def test_accented_name_with_declared_code_page():
    r = B2.make_report("C", random.Random(973_000), accented=True)
    t = G.RENDER["C"](r, G.Opts())
    oc = P.process_bytes(t.encode("cp1252"), "cp1252")
    assert oc.status == "ACCEPT", oc.reasons
    assert oc.record["patient_name"] == G.printed_name(r)


@pytest.mark.parametrize("bytes_cp,queue_cp", [("cp1252", None), ("cp1252", "ascii"), ("cp437", "cp1252"), ("cp1252", "cp437")])
def test_wrong_code_page_never_accepted_with_wrong_name(bytes_cp, queue_cp):
    r = B2.make_report("C", random.Random(973_001), accented=True)
    t = G.RENDER["C"](r, G.Opts())
    oc = P.process_bytes(t.encode(bytes_cp), queue_cp)
    assert oc.status == "REJECT" or oc.record["patient_name"] == G.printed_name(r)


def test_overstrike_underline_keeps_letters():
    r, t = _doc("A")
    nm = G.printed_name(r)
    under = "".join(ch + "\b_" for ch in nm)
    oc = P.process_bytes(t.replace(nm, under, 1).encode("latin-1"))
    assert oc.status == "ACCEPT" and oc.record["patient_name"] == nm


# ----------------------------------------------------------------------------- FHIR notes
def test_fhir_conclusion_carries_notes():
    from spoolgeist_h.fhir_builder import build_bundle
    r, t = _doc("A")
    L = t.split("\n")
    L.insert(B2._end_line(L, "A") + 1, "Note: Lipaemic sample.")
    n = normalize("\n".join(L).encode())
    oc = P.process_normalized(n)
    assert oc.status == "ACCEPT"
    b = json.loads(build_bundle(oc.record, n.text, n.sha256, abdm=True))
    dr = next(e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "DiagnosticReport")
    assert "Lipaemic sample." in dr["conclusion"]


# ----------------------------------------------------------------------------- mutation-testing gap tests (Stage 3)
def test_qualitative_result_inside_referrer_slot_rejected():
    """Gap found by mutation testing: the qualitative-word check on a trusted line's variable slot was never
    exercised (prefix/suffix checks fired first in every existing test). The referrer name is REPLACED, so the
    line keeps its approved shape and only the vocabulary check can refuse it."""
    for s in range(6):
        r, t = _doc("A", 974_000 + s)
        nm = r.doctor.upper()
        if len(nm.split()) != 2:
            continue
        t2 = t.replace("DR. " + nm, "DR. HIV REACTIVE", 1)
        oc = run(t2)
        assert oc.status == "REJECT" and oc.reasons[0].startswith(("qualitative_text_on_trusted_line", "unapproved_line_shape")), oc.reasons
        return
    pytest.skip("no 2-token referrer in the sampled seeds")


def test_bold_marks_exactly_the_value_characters():
    """Gap found by mutation testing: an off-by-one in the bold -> column mapping survived because layout B bolds the
    value plus its padding. Here only the digits are bold, and a bold label must NOT set a flag."""
    r, t = _doc("B", 975_000)
    x = next(x for x in r.results if not x.flag)
    L = t.split("\n")
    i = next(k for k, l in enumerate(L) if l.startswith(x.label + " ") and x.value in l)
    L[i] = L[i].replace(x.value, "\x1bE" + x.value + "\x1bF", 1)
    oc = P.process_bytes("\n".join(L).encode(), None)
    # the value is inside its printed range, so a bold (= "abnormal") marker must be detected AND refused by V6
    assert oc.status == "REJECT" and any(f"V6 flag A but {x.code}" in rr for rr in oc.reasons), oc.reasons
    L = t.split("\n")
    L[i] = L[i].replace(x.label, "\x1bE" + x.label + "\x1bF", 1)
    oc = P.process_bytes("\n".join(L).encode(), None)
    assert oc.status == "ACCEPT", oc.reasons
    assert {y["code"]: y["flag"] for y in oc.record["results"]}[x.code] == ""


# ----------------------------------------------------------------------------- validator boundary tests (mutation gaps)
from datetime import date as _date  # noqa: E402


def _base_rec(**kw):
    r = {"patient_id": "SP/26/000123", "patient_name": "Aarav Mehta", "collected": "2026-04-10", "reported": "2026-04-11",
         "patient_age": 45, "patient_sex": "male",
         "results": [{"code": "GLU", "value": "90", "unit": "mg/dL"}]}
    r.update(kw)
    return r


TODAY = _date(2026, 11, 22)


@pytest.mark.parametrize("age,ok", [(0, True), (120, True), (121, False), (-1, False)])
def test_V8_age_bounds(age, ok):
    issues = validators.validate(_base_rec(patient_age=age), TODAY)
    assert (not any("V8" in i for i in issues)) == ok, issues


@pytest.mark.parametrize("collected,reported,ok", [("2026-04-10", "2026-05-10", True), ("2026-04-10", "2026-05-11", False),
                                                   ("2026-04-10", "2026-04-09", False), ("2026-04-10", "2026-04-10", True)])
def test_V4_reported_window(collected, reported, ok):
    issues = validators.validate(_base_rec(collected=collected, reported=reported), TODAY)
    assert (not any("V4" in i for i in issues)) == ok, issues


@pytest.mark.parametrize("collected,ok", [("2000-01-01", True), ("1999-12-31", False), ("2026-11-23", True), ("2026-11-24", False)])
def test_V4_collected_window(collected, ok):
    issues = validators.validate(_base_rec(collected=collected, reported=None), TODAY)
    assert (not any("V4" in i for i in issues)) == ok, issues


def test_V2_two_script_name_rejected():
    assert any("writing systems" in i for i in validators.validate(_base_rec(patient_name="Zoδ Mascarenhas"), TODAY))
    assert not any("V2" in i for i in validators.validate(_base_rec(patient_name="Zoë Mascarenhas"), TODAY))
