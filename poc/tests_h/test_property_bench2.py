"""Property test v2 (spec 02 section 6): combinations drawn from catalogue v2 plus an extra VALID text operation
(CRLF / column shift / approved note). Property (unchanged): a DEFECT or FOREIGN document must be REJECTED; an
accepted VALID or POLICY document must have exactly correct tier-1/tier-2 data. False rejections and policy
refusals are counted, never asserted away."""
from __future__ import annotations

import base64
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, seed, settings, strategies as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bench import generator as G          # noqa: E402
from bench2 import generator as B2        # noqa: E402
from bench2.evaluate import classify      # noqa: E402
from spoolgeist_h.pipeline import Pipeline  # noqa: E402

P = Pipeline(allow_agent_approval=True)
CLASSES = B2.VALID + B2.POLICY + B2.DEFECTS + B2.FOREIGN
STATS, FAILS = Counter(), []
PSEED = os.environ.get("PBT2_SEED")
N = int(os.environ.get("PBT2_N", "2000"))


def _maybe_seed(f):
    return seed(int(PSEED))(f) if PSEED else f


@_maybe_seed
@settings(max_examples=N, deadline=None, database=None, derandomize=PSEED is None, suppress_health_check=list(HealthCheck))
@given(lay=st.sampled_from(B2.LAYOUTS), s=st.integers(0, 10**9), cls=st.sampled_from(CLASSES),
       extra=st.sampled_from(["none", "crlf", "col_shift", "note"]))
def test_bench2_combinations(lay, s, cls, extra):
    d = B2.build(lay, s, cls)
    if d is None:
        return
    doc = d.to_json()
    cp = None if doc["queue_codepage"] == "ascii" else doc["queue_codepage"]
    raw = d.raw
    if extra != "none" and cls != "wrong_code_page":
        try:
            text = raw.decode(cp or "utf-8")
        except UnicodeDecodeError:
            return
        if extra in ("crlf", "col_shift"):
            r = B2.make_report(lay, random.Random(s))   # only used for row labels in col_shift
            text = G.apply_text_op(text, "text:" + extra, r, random.Random(s + 1))
        else:
            L = text.split("\n")
            try:
                i = B2._end_line(L, lay)
            except StopIteration:
                return
            note = B2.note_line(lay, "Verified twice.")
            L.insert(i + 1, note)
            text = "\n".join(L)
            if doc["truth"]:
                doc["truth"] = dict(doc["truth"], notes=doc["truth"]["notes"] + [" ".join(note.split())])
        raw = text.encode(cp or "utf-8")
    oc = P.process_bytes(raw, doc["queue_codepage"])
    c = classify(doc, oc.status, oc.record)
    STATS[c["outcome"]] += 1
    STATS[f"{doc['group']}:{c['outcome']}"] += 1
    if c["outcome"] in ("unsafe_accept", "silent_error", "policy_accept_WRONG"):
        FAILS.append({"doc": doc["doc_id"], "extra": extra, "outcome": c["outcome"], "fields": c.get("failed_fields")})


def test_zz_property_holds():
    assert sum(STATS.values()) > 0
    assert not FAILS, FAILS[:5]


@pytest.fixture(scope="module", autouse=True)
def dump():
    yield
    out = ROOT / "phase2" / "stage3" / "results" / f"pbt_bench2{os.environ.get('PBT2_TAG', '')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"seed": PSEED or "derandomized", "n": N, "stats": dict(sorted(STATS.items())),
                               "failures": FAILS[:30]}, indent=1))
