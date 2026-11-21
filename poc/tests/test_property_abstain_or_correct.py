"""Property-based test (Hypothesis): for ANY generated report of an active layout, with ANY combination
of valid variations, optional invalid defect and fuzz operations, the deterministic pipeline must either
REJECT, or ACCEPT with exactly the ground-truth critical fields. Documents with an invalid defect must
be REJECTED.

This test was written AFTER the system freeze and after the first held-out results; it was not used to
change the system. Combinations and fuzz operations (comment lines, blank lines, digit changes, random
character damage on static lines) are new relative to the held-out benchmark.
"""
from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

import pytest
import os
from hypothesis import HealthCheck, given, seed, settings, strategies as st

from bench import generator as G
from bench.score import classify
from spoolgeist import interpreter, llm
from spoolgeist.grid import normalize

ROOT = Path(__file__).resolve().parents[1]
VALID = ["col_shift", "drop_optional", "page_break", "crlf_trailing", "long_name"]
INVALID = [k for k in G.PERTURBATIONS if k not in VALID]
FUZZ = ["comment_line", "blank_lines", "digit_change", "static_char_damage"]
STATS = Counter()
FAILS = []


def load_bindings():
    out = []
    for p in sorted((ROOT / "bindings").glob("*.v1.json")):
        b = json.loads(p.read_text())
        if b.pop("_meta", {}).get("status") == "active":
            out.append(b)
    return out


BINDINGS = load_bindings()


def build(layout, seed, valid, invalid, fuzz):
    rng = random.Random(seed)
    r = G.make_report(layout, rng)
    o = G.Opts()
    ops, expected = [], "accept"
    if "digit_change" in fuzz:   # valid content change: truth follows the new value
        x = r.results[rng.randrange(len(r.results))]
        digits = [i for i, ch in enumerate(x.value) if ch.isdigit()]
        i = rng.choice(digits)
        nd = str((int(x.value[i]) + rng.randint(1, 9)) % 10)
        if not (i == 0 and nd == "0" and len(x.value) > 1 and x.value[1] != "."):
            x.value = x.value[:i] + nd + x.value[i + 1:]
            lo, hi = float(x.low), float(x.high)
            x.flag = "H" if float(x.value) > hi else ("L" if float(x.value) < lo else "")
    for p in list(valid) + ([invalid] if invalid else []):
        res = G.PERTURBATIONS[p](r, o, rng)
        if res is None:
            continue
        r, o, exp, op = res
        if exp == "reject":
            expected = "reject"
        if op:
            ops.append(op)
    text = G.RENDER[layout](r, o)
    for op in ops:
        text = G.apply_text_op(text, op, r, rng)
    lines = text.split("\n")
    labels = [x.label for x in r.results]
    if "comment_line" in fuzz:
        idx = [i for i, ln in enumerate(lines) if any(lb in ln for lb in labels)]
        if idx:
            lines.insert(rng.choice(idx) + 1, rng.choice(["Note: sample slightly haemolysed.",
                                                          "  Remark - repeat test advised", "Comment: verified twice"]))
    if "blank_lines" in fuzz:
        idx = [i for i, ln in enumerate(lines) if any(lb in ln for lb in labels)]
        if idx:
            lines.insert(rng.choice(idx) + 1, "")
    if "static_char_damage" in fuzz:
        tokens = [r.patient_id, r.first, r.last, r.first.upper(), r.last.upper()] + labels + [x.value for x in r.results]
        cand = [i for i, ln in enumerate(lines) if ln.strip() and not any(t and t in ln for t in tokens)
                and not any(ch.isdigit() for ch in ln)]
        if cand:
            i = rng.choice(cand)
            ln = lines[i]
            pos = [k for k, ch in enumerate(ln) if ch.strip()]
            k = rng.choice(pos)
            lines[i] = ln[:k] + rng.choice("#?xQ") + ln[k + 1:]
    text = "\n".join(lines)
    truth = G.truth(r) if expected == "accept" else None
    return {"truth_if_valid": G.truth(r), "doc_id": f"pbt-{layout}-{seed}", "perturbation": "+".join(list(valid) + [invalid or ""] + list(fuzz)),
            "expected": expected, "truth": truth, "text": text, "layout": layout}


PBT_SEED = os.environ.get("PBT_SEED")          # unset -> derandomized default run (reproducible)
PBT_N = int(os.environ.get("PBT_N", "3000"))


def _maybe_seed(f):
    return seed(int(PBT_SEED))(f) if PBT_SEED else f


@_maybe_seed
@settings(max_examples=PBT_N, deadline=None, derandomize=PBT_SEED is None, database=None,
          suppress_health_check=list(HealthCheck))
@given(layout=st.sampled_from(list("ABCDEF")), seed=st.integers(0, 10**9),
       valid=st.lists(st.sampled_from(VALID), max_size=3, unique=True),
       invalid=st.one_of(st.none(), st.sampled_from(INVALID)),
       fuzz=st.lists(st.sampled_from(FUZZ), max_size=2, unique=True))
def test_abstain_or_exactly_correct(layout, seed, valid, invalid, fuzz):
    llm.FORBID["enabled"] = True
    d = build(layout, seed, valid, invalid, fuzz)
    oc = interpreter.process(BINDINGS, normalize(d["text"].encode()).text)
    cls = classify(oc.status, oc.record, d)
    STATS[cls] += 1
    STATS[f"{layout}:{cls}"] += 1
    for f in fuzz:
        STATS[f"fuzz:{f}:{cls}"] += 1
    if cls in ("silent_error", "unsafe_accept"):
        from bench.score import field_checks
        data_ok = all(v for k, v in field_checks(oc.record, d["truth_if_valid"]).items() if k.startswith("crit:"))
        STATS[f"{cls}:data_correct={data_ok}"] += 1
        FAILS.append({"doc_id": d["doc_id"], "cls": cls, "perturbation": d["perturbation"], "data_correct": data_ok,
                      "record": oc.record, "truth": d["truth"], "text": d["text"]})
    # no assert here: we survey all 3000 cases, then assert in the next test (so stats cover every case)


def test_zz_no_silent_errors_in_survey():
    assert sum(STATS[k] for k in ("correct_accept", "false_reject", "correct_reject", "silent_error", "unsafe_accept")) > 0
    assert not FAILS, f"{len(FAILS)} silent errors / unsafe accepts, first: {FAILS[0]['perturbation']}"


@pytest.fixture(scope="module", autouse=True)
def dump_stats():
    yield
    out = ROOT / "runtime" / f"pbt_stats{os.environ.get('PBT_TAG', '')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"stats": dict(sorted(STATS.items())), "failures": FAILS[:20]}, indent=1, default=str))
