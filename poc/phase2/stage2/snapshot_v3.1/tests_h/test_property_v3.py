"""Property-based test for v3 (same property as the PoC; not weakened):
for ANY generated report of an active layout with ANY combination of valid variations, optional invalid defect and
fuzz operations, the v3 pipeline must REJECT, or ACCEPT with exactly the ground-truth critical fields; documents
with an invalid defect must be REJECTED.

Case construction is imported unchanged from the PoC property test (tests/test_property_abstain_or_correct.build).
Labels are therefore identical to the PoC run, including its known labelling issues (F-19: comment lines and static
character damage are labelled 'valid'); those affect only the false-rejection count, never unsafe/silent counts.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, seed, settings, strategies as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import test_property_abstain_or_correct as T     # noqa: E402
from bench.score import classify, field_checks   # noqa: E402
from spoolgeist_h import llm                      # noqa: E402
from spoolgeist_h.pipeline import Pipeline        # noqa: E402

P = Pipeline(allow_agent_approval=True)
STATS, FAILS = Counter(), []
PBT_SEED = os.environ.get("PBT_SEED")
PBT_N = int(os.environ.get("PBT_N", "3000"))


def _maybe_seed(f):
    return seed(int(PBT_SEED))(f) if PBT_SEED else f


@_maybe_seed
@settings(max_examples=PBT_N, deadline=None, derandomize=PBT_SEED is None, database=None,
          suppress_health_check=list(HealthCheck))
@given(layout=st.sampled_from(list("ABCDEF")), seed=st.integers(0, 10**9),
       valid=st.lists(st.sampled_from(T.VALID), max_size=3, unique=True),
       invalid=st.one_of(st.none(), st.sampled_from(T.INVALID)),
       fuzz=st.lists(st.sampled_from(T.FUZZ), max_size=2, unique=True))
def test_v3_abstain_or_exactly_correct(layout, seed, valid, invalid, fuzz):
    llm.FORBID["enabled"] = True
    d = T.build(layout, seed, valid, invalid, fuzz)
    oc = P.process_bytes(d["text"].encode())
    cls = classify(oc.status, oc.record, d)
    STATS[cls] += 1
    STATS[f"{layout}:{cls}"] += 1
    for f in fuzz:
        STATS[f"fuzz:{f}:{cls}"] += 1
    for v in valid:
        STATS[f"valid:{v}:{cls}"] += 1
    if cls in ("silent_error", "unsafe_accept"):
        ok = all(v for k, v in field_checks(oc.record, d["truth_if_valid"]).items() if k.startswith("crit:"))
        STATS[f"{cls}:data_correct={ok}"] += 1
        FAILS.append({"doc_id": d["doc_id"], "cls": cls, "perturbation": d["perturbation"], "data_correct": ok,
                      "text": d["text"]})


def test_zz_v3_no_silent_errors_or_unsafe_accepts():
    assert sum(STATS[k] for k in ("correct_accept", "false_reject", "correct_reject", "silent_error", "unsafe_accept")) > 0
    assert not FAILS, f"{len(FAILS)} silent errors / unsafe accepts, first: {FAILS[0]['perturbation']}"


@pytest.fixture(scope="module", autouse=True)
def dump_stats():
    yield
    out = ROOT / "phase2" / "stage2" / "results" / f"pbt_v3{os.environ.get('PBT_TAG', '')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"seed": PBT_SEED or "derandomized-default", "n": PBT_N,
                               "stats": dict(sorted(STATS.items())), "failures": FAILS[:20]}, indent=1, default=str))
