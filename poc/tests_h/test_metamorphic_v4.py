"""Metamorphic relations (spec 02 section 6) on bench2 valid reports. No new labels needed: if the system accepts
both the source and the transformed document, the stated relation must hold. A pair where only one side is
accepted is an 'instability': counted and reported, not hidden. A broken relation fails the test."""
from __future__ import annotations

import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bench import generator as G           # noqa: E402
from bench2 import generator as B2         # noqa: E402
from spoolgeist_h.pipeline import Pipeline  # noqa: E402

P = Pipeline(allow_agent_approval=True)
STATS, VIOL = Counter(), []
N = int(os.environ.get("MR_N", "300"))


def proc(text, lay):
    return P.process_bytes(B2.encode(text, lay), B2.QUEUE_CODEPAGE[lay])


def core(rec):
    return {k: rec.get(k) for k in ("patient_id", "patient_name", "patient_age", "patient_sex", "collected",
                                    "collected_dt", "reported")} | {"results": sorted((x["code"], x["value"], x["unit"], x["flag"]) for x in rec["results"])}


def relation(name, lay, src, dst, expect):
    a, b = proc(src, lay), proc(dst, lay)
    STATS[f"{name}:pairs"] += 1
    if a.status == "ACCEPT" and b.status == "ACCEPT":
        STATS[f"{name}:both_accepted"] += 1
        ok, why = expect(a.record, b.record)
        if not ok:
            VIOL.append({"relation": name, "layout": lay, "why": why})
    elif a.status != b.status:
        STATS[f"{name}:instability"] += 1
    else:
        STATS[f"{name}:both_rejected"] += 1


def same(ra, rb):
    return core(ra) == core(rb), "records differ"


@settings(max_examples=N, deadline=None, database=None, suppress_health_check=list(HealthCheck))
@given(lay=st.sampled_from(list("ABCDEF")), seed=st.integers(0, 10**9), which=st.sampled_from(
    ["rename", "crlf", "move_break", "add_note", "referrer", "col_shift"]))
def test_metamorphic(lay, seed, which):
    rng = random.Random(seed)
    r = B2.make_report(lay, rng)
    o = G.Opts()
    src = G.RENDER[lay](r, o)
    if which == "rename":
        r2 = __import__("copy").deepcopy(r)
        r2.first, r2.last = rng.choice(G.FIRST), rng.choice(G.LAST)
        if (r2.first, r2.last) == (r.first, r.last):
            return
        dst = G.RENDER[lay](r2, o)
        exp = G.printed_name(r2)
        relation(which, lay, src, dst, lambda a, b: (core(a) | {"patient_name": None} == core(b) | {"patient_name": None}
                                                    and b["patient_name"] == exp, "only the name may change"))
    elif which == "crlf":
        relation(which, lay, src, G.apply_text_op(src, "text:crlf", r, rng), same)
    elif which == "col_shift":
        relation(which, lay, src, G.apply_text_op(src, "text:col_shift", r, rng), same)
    elif which == "move_break":
        if lay not in G.PAGEABLE or len(r.results) < 5:
            return
        o1, o2 = G.Opts(page_break_after=2), G.Opts(page_break_after=len(r.results) - 2)
        relation(which, lay, G.RENDER[lay](r, o1), G.RENDER[lay](r, o2), same)
    elif which == "add_note":
        L = src.split("\n")
        L.insert(B2._end_line(L, lay) + 1, B2.note_line(lay, rng.choice(B2.NOTE_TEXT)))
        relation(which, lay, src, "\n".join(L), lambda a, b: (core(a) == core(b) and len(b["notes"]) == len(a["notes"]) + 1,
                                                             "record must be identical plus one note"))
    elif which == "referrer":
        r2 = __import__("copy").deepcopy(r)
        r2.doctor = rng.choice([d for d in B2.REFERRERS if d != r.doctor])
        relation(which, lay, src, G.RENDER[lay](r2, o), same)


def test_zz_no_relation_violated():
    assert sum(v for k, v in STATS.items() if k.endswith(":pairs")) > 0
    assert not VIOL, VIOL[:5]


@pytest.fixture(scope="module", autouse=True)
def dump():
    yield
    out = ROOT / "phase2" / "stage3" / "results" / f"metamorphic_v4{os.environ.get('MR_TAG', '')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"n": N, "stats": dict(sorted(STATS.items())), "violations": VIOL[:50]}, indent=1))
