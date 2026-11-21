"""Regression tests: approval registry (F-07), gate v2 conditions (F-08), date precision (F-03), FHIR label (F-16).
Each gate test builds a deliberately bad candidate and checks that the specific condition refuses it."""
from __future__ import annotations

import copy
import glob
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bench import generator as G                                   # noqa: E402
from spoolgeist_h.compile import compile_binding                   # noqa: E402
from spoolgeist_h.gate import run_gate                             # noqa: E402
from spoolgeist_h.grid import normalize                            # noqa: E402
from spoolgeist_h.pipeline import Pipeline                         # noqa: E402
from spoolgeist_h.registry import (Registry, RegistryIntegrityError, canonical_sha,  # noqa: E402
                                   load_approved)

BH = ROOT / "bindings_h"


def corpus(split, lay):
    return [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / f"data/corpus/{split}/{lay}/*.json")))]


def v1(lay):
    b = json.loads((ROOT / "bindings" / f"lab-{lay.lower()}.v1.json").read_text())
    b.pop("_meta")
    return b


def gate_for(cand_v1, lay, version=9, active=(), samples=None, approved=None):
    gen, dev = corpus("gen", lay), corpus("dev", lay)
    approved = approved if approved is not None else [d for d in gen + dev if d["expected"] == "accept"]
    cand, crep = compile_binding(cand_v1, approved, version)
    return cand, run_gate(cand, gen, dev, list(active), samples or {}, crep)


# ----------------------------------------------------------------------------- registry
@pytest.fixture
def regdir(tmp_path):
    d = tmp_path / "bh"
    d.mkdir()
    (d / "gate_reports").mkdir()
    shutil.copy(BH / "lab-a.v3.json", d / "lab-a.v3.json")
    shutil.copy(BH / "gate_reports" / "lab-a.v3.gate.json", d / "gate_reports" / "lab-a.v3.gate.json")
    return d


def approve(d, kind="human", **kw):
    return Registry(d).approve(d / "lab-a.v3.json", d / "gate_reports" / "lab-a.v3.gate.json", "Test Person", kind,
                               kw.get("ack", []), kw.get("confirm", False))


def test_unapproved_binding_is_not_loaded(regdir):
    assert load_approved(regdir) == []


def test_human_approval_loads(regdir):
    approve(regdir)
    assert [b["binding_id"] for b in load_approved(regdir)] == ["lab-a"]


def test_agent_approval_requires_explicit_flag(regdir):
    approve(regdir, kind="agent")
    assert load_approved(regdir) == []
    assert len(load_approved(regdir, allow_agent_approval=True)) == 1


def test_edit_after_approval_is_detected(regdir):
    approve(regdir)
    b = json.loads((regdir / "lab-a.v3.json").read_text())
    b["results"]["labels"]["M.C.H."], b["results"]["labels"]["M.C.V."] = "MCV", "MCH"
    (regdir / "lab-a.v3.json").write_text(json.dumps(b))
    with pytest.raises(RegistryIntegrityError):
        load_approved(regdir)


def test_registry_history_edit_breaks_chain(regdir):
    approve(regdir)
    Registry(regdir).revoke("lab-a", 3, "Test Person", "test")
    lines = (regdir / "approvals.jsonl").read_text().splitlines()
    e = json.loads(lines[0])
    e["approver"] = "Someone Else"
    lines[0] = json.dumps(e, sort_keys=True)
    (regdir / "approvals.jsonl").write_text("\n".join(lines) + "\n")
    with pytest.raises(RegistryIntegrityError):
        load_approved(regdir)


def test_revoke_deactivates(regdir):
    approve(regdir)
    Registry(regdir).revoke("lab-a", 3, "Test Person", "layout retired")
    assert load_approved(regdir) == []


def test_approve_refuses_failed_gate_and_unacked_warnings(regdir):
    g = json.loads((regdir / "gate_reports" / "lab-a.v3.gate.json").read_text())
    g2 = dict(g, passed=False)
    (regdir / "gate_reports" / "lab-a.v3.gate.json").write_text(json.dumps(g2))
    with pytest.raises(ValueError, match="gate did not pass"):
        approve(regdir)
    g3 = dict(g, warnings_requiring_ack=["unsupported_variation:long_name"])
    (regdir / "gate_reports" / "lab-a.v3.gate.json").write_text(json.dumps(g3))
    with pytest.raises(ValueError, match="unacknowledged"):
        approve(regdir)
    approve(regdir, ack=["unsupported_variation:long_name"])


def test_same_version_different_content_refused(regdir):
    approve(regdir)
    b = json.loads((regdir / "lab-a.v3.json").read_text())
    b["description"] += " (edited)"
    (regdir / "lab-a.v3.json").write_text(json.dumps(b))
    g = json.loads((regdir / "gate_reports" / "lab-a.v3.gate.json").read_text())
    g["binding_sha256"] = canonical_sha(b)
    (regdir / "gate_reports" / "lab-a.v3.gate.json").write_text(json.dumps(g))
    with pytest.raises(ValueError, match="bump the version"):
        approve(regdir)


def test_integrity_checks_survive_python_O(regdir):
    approve(regdir)
    b = json.loads((regdir / "lab-a.v3.json").read_text())
    b["description"] += "x"
    (regdir / "lab-a.v3.json").write_text(json.dumps(b))
    code = (f"import sys; sys.path.insert(0, {str(ROOT)!r}); from pathlib import Path; "
            f"from spoolgeist_h.registry import load_approved; load_approved(Path({str(regdir)!r}))")
    p = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True)
    assert p.returncode != 0 and "RegistryIntegrityError" in p.stderr


# ----------------------------------------------------------------------------- gate conditions
def test_gate_passes_real_binding():
    _, g = gate_for(v1("A"), "A")
    assert g["passed"], {k: v for k, v in g["conditions"].items() if not v["passed"]}


def test_G3_wrong_code_mapping_fails():
    b = v1("A")
    b["results"]["labels"]["M.C.H."], b["results"]["labels"]["M.C.V."] = "MCV", "MCH"
    _, g = gate_for(b, "A")
    assert not g["passed"] and not g["conditions"]["G4_clean_acceptance"]["passed"]


def test_G2_no_header_identity_fails():
    b = v1("A")
    b["layout"]["anchors"] = ["^TEST\\s+RESULT", "END OF REPORT"]
    gen, dev = corpus("gen", "A"), corpus("dev", "A")
    # samples whose first line varies and is matched by no anchor/skip -> no header template
    appr = [dict(d, text=f"PRINTED {i:04d}\n" + d["text"]) for i, d in enumerate(d for d in gen + dev if d["expected"] == "accept")]
    _, g = gate_for(b, "A", approved=appr)
    assert not g["conditions"]["G2_compiled"]["passed"]


def test_G6_permissive_skip_fails():
    b = v1("A")
    b["results"]["skip_lines"].append("^UNEXPECTED.*$")
    _, g = gate_for(b, "A")
    assert not g["conditions"]["G6_self_adversarial"]["passed"]


def test_G7_collision_fails():
    a3 = json.loads((BH / "lab-a.v3.json").read_text())
    b = v1("A")
    b["binding_id"] = "lab-x"
    samples = {"lab-a": [d for d in corpus("gen", "A") + corpus("dev", "A") if d["perturbation"] == "clean"]}
    _, g = gate_for(b, "A", active=[a3], samples=samples)
    assert not g["conditions"]["G7_collision"]["passed"]


def test_G8_ambiguous_dates_require_confirmation(tmp_path):
    # rebuild layout-A samples whose days are all <= 12 (DD/MM indistinguishable from MM/DD)
    docs, seed = [], 990_000
    while len(docs) < 10:
        seed += 1
        r = G.make_report("A", random.Random(seed), force_day_le12=True)
        if r.reported.day <= 12:          # both printed dates must be ambiguous
            docs.append(G.build_doc("A", seed, force_day_le12=True))
    cand, g = gate_for(v1("A"), "A", approved=docs)
    assert g["date_format_confirmation_required"]
    d = tmp_path
    (d / "b.json").write_text(json.dumps(cand))
    g["passed"] = True
    (d / "g.json").write_text(json.dumps(g))
    with pytest.raises(ValueError, match="date format"):
        Registry(d).approve(d / "b.json", d / "g.json", "T", "human", g["warnings_requiring_ack"], False)
    Registry(d).approve(d / "b.json", d / "g.json", "T", "human", g["warnings_requiring_ack"], True)


def test_F06_optional_fields_promoted():
    a3 = json.loads((BH / "lab-a.v3.json").read_text())
    assert {"patient_age", "patient_sex"} <= set(a3["compiled"]["promoted_required"])
    from spoolgeist_h.interpreter import Reject, execute
    r = G.make_report("A", random.Random(40_000))
    t = G.RENDER["A"](r, G.Opts()).replace("Age / Sex", "Age / Se#", 1)
    with pytest.raises(Reject, match="missing_field"):        # extraction layer alone now refuses
        execute(a3, normalize(t.encode()).text)
    oc = Pipeline(allow_agent_approval=True).process_bytes(t.encode())
    assert oc.status == "REJECT"                               # (the page-1 header template also refuses it)


# ----------------------------------------------------------------------------- precision / FHIR
@pytest.mark.parametrize("lay,has_time", [("A", True), ("B", True), ("C", True), ("D", False), ("E", False), ("F", True)])
def test_F03_no_invented_time(lay, has_time):
    from spoolgeist_h.fhir_builder import build_bundle
    r = G.make_report(lay, random.Random(85_000))
    t = G.RENDER[lay](r, G.Opts())
    n = normalize(t.encode())
    oc = Pipeline(allow_agent_approval=True).process_normalized(n)
    assert oc.status == "ACCEPT", oc.reasons
    assert ("collected_dt" in oc.record) == has_time
    b = json.loads(build_bundle(oc.record, n.text, n.sha256, abdm=True))
    dr = next(e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "DiagnosticReport")
    assert ("T" in dr["effectiveDateTime"]) == has_time
    if has_time:
        assert dr["effectiveDateTime"].startswith(r.collected.strftime("%Y-%m-%dT%H:%M"))
    else:
        assert dr["effectiveDateTime"] == r.collected.strftime("%Y-%m-%d")
    assert dr["presentedForm"][0]["title"].startswith("Normalised text")
