"""Post-freeze red-team review of v3. Written AFTER v3 was frozen; none of these attacks informed v3's design.
Read-only on the system. Each probe runs against v2.1 and v3 (full).

Attack idea: line accounting (F-23 fix) trusts three kinds of lines outside the table: lines touched by a field
match, lines matching a binding skip/anchor regex, and static template lines. Can a printed RESULT hide in one?

usage: .venv/bin/python -m phase2.stage2.redteam_v3
"""
from __future__ import annotations

import copy
import json
import random
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bench import generator as G                          # noqa: E402
from bench.run_benchmark import load_bindings              # noqa: E402
from spoolgeist import interpreter as I2                   # noqa: E402
from spoolgeist.grid import normalize as N2                # noqa: E402
from spoolgeist_h.pipeline import Pipeline                 # noqa: E402

OUT = ROOT / "phase2" / "stage2" / "results"
B2 = load_bindings()
P3 = Pipeline(allow_agent_approval=True)
SMUG = "SODIUM 138 mmol/L"


def v21(t):
    return I2.process(B2, N2(t.encode()).text)


def v3(t):
    return P3.process_bytes(t.encode())


def doc(lay, seed):
    r = G.make_report(lay, random.Random(seed))
    return r, G.RENDER[lay](r, G.Opts())


def lines_of(t):
    return t.split("\n")


def idx(L, pred):
    return next(i for i, l in enumerate(L) if pred(l))


# -- R1: append a result to a line that a FIELD regex touches (patient-ID line)
def r1(lay, r, t):
    L = lines_of(t)
    i = idx(L, lambda l: r.patient_id in l)
    L[i] = L[i] + "   " + SMUG
    return "\n".join(L)


# -- R2: add a NEW line outside the table that matches one of the binding's skip/anchor regexes but carries a result
R2_LINES = {
    "A": "Ref. By      : " + SMUG,                       # skip ^Ref\. By\s*:.*$
    "B": "Referred by : " + SMUG,                        # skip ^Referred by\s*:
    "C": "Consultant : " + SMUG,                         # skip ^Consultant\s*:
    "D": None,                                           # D's free-text skips are field lines (R1 covers)
    "E": SMUG + "   Sex/Age:",                           # anchor 'Sex/Age:' is unanchored
    "F": None,
}


def r2(lay, r, t):
    if not R2_LINES[lay]:
        return None
    L = lines_of(t)
    end_kw = {"A": "END OF REPORT", "B": "End of Report", "C": "-- END --", "E": "Report generated"}[lay]
    i = idx(L, lambda l: end_kw in l)
    L.insert(i + 1, R2_LINES[lay])
    return "\n".join(L)


# -- R3: same, but INSIDE the table region using a skip regex (v2.1 'skip_hides_row' only checks known labels)
R3_LINES = {"A": "Patient Name : " + SMUG, "B": "Name    : " + SMUG, "C": "Consultant : " + SMUG,
            "D": None, "E": None, "F": None}


def r3(lay, r, t):
    if not R3_LINES[lay]:
        return None
    L = lines_of(t)
    lab = r.results[0].label
    i = idx(L, lambda l: lab in l) + (2 if lay == "C" else 0)
    L.insert(i + 1, R3_LINES[lay])
    return "\n".join(L)


# -- R4: duplicate the collected-date line with a result appended (field value identical -> no conflict)
def r4(lay, r, t):
    L = lines_of(t)
    kw = {"A": "Collected :", "B": "Sample collected on", "C": "Collected  :", "D": "Coll. Dt", "E": "Drawn:", "F": "COLLECTED"}[lay]
    i = idx(L, lambda l: kw in l)
    L.insert(i + 1, L[i] + "  " + SMUG)
    return "\n".join(L)


PROBES = {"R1_result_on_field_line": r1, "R2_result_on_skip_or_anchor_line_outside_table": r2,
          "R3_result_on_skip_line_inside_table": r3, "R4_duplicated_field_line_with_result": r4}


def run_text_probes():
    res = {}
    for name, fn in PROBES.items():
        c2, c3, ex = Counter(), Counter(), []
        for lay in "ABCDEF":
            for s in range(10):
                r, t = doc(lay, 910_000 + s)
                m = fn(lay, r, t)
                if m is None:
                    c2["n/a"] += 1
                    c3["n/a"] += 1
                    continue
                o2, o3 = v21(m), v3(m)
                c2[f"{lay}:{o2.status}"] += 1
                c3[f"{lay}:{o3.status}"] += 1
                if o3.status == "ACCEPT" and len(ex) < 2:
                    ex.append({"layout": lay, "dropped": SMUG, "results_extracted": len(o3.record["results"]),
                               "printed_results": len(r.results) + 1})
                elif o3.status == "REJECT" and s == 0:
                    ex.append({"layout": lay, "v3_reason": o3.reasons[0][:90]})
        res[name] = {"v2.1": dict(sorted(c2.items())), "v3": dict(sorted(c3.items())), "examples": ex}
    return res


# -- R5: forged gate report -> does registry.approve trust it?
def r5_forged_gate():
    from spoolgeist_h.registry import Registry, canonical_sha, load_approved
    d = Path(tempfile.mkdtemp(prefix="sg_rt_"))
    try:
        b = json.loads((ROOT / "bindings_h" / "lab-a.v3.json").read_text())
        b["results"]["skip_lines"].append("^.*$")          # skip EVERYTHING inside the table: obviously unsafe
        b["binding_id"], b["version"] = "lab-a", 4
        (d / "lab-a.v4.json").write_text(json.dumps(b))
        forged = {"binding_id": "lab-a", "version": 4, "binding_sha256": canonical_sha(b), "passed": True,
                  "conditions": {}, "warnings_requiring_ack": [], "date_format_confirmation_required": False}
        (d / "g.json").write_text(json.dumps(forged))
        try:
            Registry(d).approve(d / "lab-a.v4.json", d / "g.json", "Mallory", "human", [], False)
            loaded = load_approved(d)
            r, t = doc("A", 1)
            oc = Pipeline(bindings=loaded).process_bytes(t.encode())
            return {"approve_accepted_forged_gate_report": True, "loaded": [x["binding_id"] for x in loaded],
                    "clean_doc_outcome_with_forged_binding": oc.status, "reasons": oc.reasons[:1]}
        except Exception as e:
            return {"approve_accepted_forged_gate_report": False, "error": str(e)[:120]}
    finally:
        shutil.rmtree(d)


# -- R6: revoking the newest version silently falls back to an older approved version?
def r6_revoke_fallback():
    from spoolgeist_h.registry import Registry, canonical_sha, load_approved
    d = Path(tempfile.mkdtemp(prefix="sg_rt_"))
    try:
        for ver in (3, 4):
            b = json.loads((ROOT / "bindings_h" / "lab-a.v3.json").read_text())
            b["version"] = ver
            (d / f"lab-a.v{ver}.json").write_text(json.dumps(b))
            g = json.loads((ROOT / "bindings_h" / "gate_reports" / "lab-a.v3.gate.json").read_text())
            g["binding_sha256"], g["version"] = canonical_sha(b), ver
            (d / f"g{ver}.json").write_text(json.dumps(g))
            Registry(d).approve(d / f"lab-a.v{ver}.json", d / f"g{ver}.json", "T", "human", [], False)
        Registry(d).revoke("lab-a", 4, "T", "v4 found unsafe")
        return {"active_after_revoking_v4": [(x["binding_id"], x["version"]) for x in load_approved(d)]}
    finally:
        shutil.rmtree(d)


# -- R7: a processing exception inside capture (e.g. broken registry) -> is the job recorded anywhere?
def r7_processing_exception():
    import asyncio
    from spoolgeist_h import capture as CAP
    d = Path(tempfile.mkdtemp(prefix="sg_rt_"))
    orig = CAP.Capture.process_job

    def boom(self, job_id):
        from spoolgeist_h.registry import RegistryIntegrityError
        raise RegistryIntegrityError("simulated: approvals.jsonl chain broken")
    CAP.Capture.process_job = boom
    try:
        async def go():
            cap = CAP.Capture(d, "127.0.0.1", 0, None, process=True)
            srv = await asyncio.start_server(cap.handle, "127.0.0.1", 0)
            r_, w = await asyncio.open_connection("127.0.0.1", srv.sockets[0].getsockname()[1])
            w.write(doc("A", 1)[1].encode())
            await w.drain()
            w.write_eof()
            await asyncio.sleep(1.0)
            w.close()
            srv.close()
        loop = asyncio.new_event_loop()
        errs = []
        loop.set_exception_handler(lambda l, c: errs.append(str(c.get("exception"))[:80]))
        loop.run_until_complete(go())
        loop.close()
        return {"job_persisted": len(list((d / "jobs").glob("*.prn"))),
                "review_queue_entries": len(list((d / "review_queue").glob("*"))),
                "out_entries": len(list((d / "out").glob("*"))),
                "event_log_mentions_failure": "error" in (d / "events.jsonl").read_text().lower(),
                "unhandled_exceptions": errs}
    finally:
        CAP.Capture.process_job = orig
        shutil.rmtree(d)


if __name__ == "__main__":
    out = {"text_probes": run_text_probes(), "R5_forged_gate_report": r5_forged_gate(),
           "R6_revoke_fallback": r6_revoke_fallback(), "R7_processing_exception": r7_processing_exception()}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "redteam_v3.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))
