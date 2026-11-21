"""Red-team re-run against v3.1. The text probes R1–R4 are imported unchanged from redteam_v3.py (the v3.0
evidence script, which stays frozen). The governance probes R5–R7 are re-expressed for the v3.1 API, because v3.1
removed the "approve from a gate-report file" path that R5 attacked.

usage: .venv/bin/python -m phase2.stage2.redteam_v31
"""
from __future__ import annotations

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from phase2.stage2 import redteam_v3 as RT            # noqa: E402
from spoolgeist_h.approval import ApprovalError, approve_binding   # noqa: E402
from spoolgeist_h.compile import compile_binding      # noqa: E402
from spoolgeist_h.pipeline import Pipeline            # noqa: E402
from spoolgeist_h.registry import Registry, load_approved   # noqa: E402

BH = ROOT / "bindings_h"


def r5_forgery_paths():
    """(a) hand-edit an unsafe skip into an approvable binding; (b) compile the unsafe skip properly; (c) a forged
    gate report sitting next to the binding (v3.1 never reads it)."""
    out = {}
    d = Path(tempfile.mkdtemp(prefix="sg_rt31_"))
    try:
        b = json.loads((BH / "lab-a.v4.json").read_text())
        hand = json.loads(json.dumps(b))
        hand["results"]["skip_lines"].append("^.*$")
        (d / "lab-a.v4.json").write_text(json.dumps(hand))
        (d / "gate_reports").mkdir()
        (d / "gate_reports" / "lab-a.v4.gate.json").write_text(json.dumps({"passed": True, "forged": True}))
        try:
            approve_binding(d / "lab-a.v4.json", "Mallory", "human", [], False, directory=d)
            out["a_hand_edited_unsafe_binding_approved"] = True
        except ApprovalError as e:
            out["a_hand_edited_unsafe_binding_approved"] = False
            out["a_reason"] = str(e)[:100]
        llm = b["compiled"]["llm_binding"]
        llm["results"]["skip_lines"].append("^.*$")
        docs = [json.loads((ROOT / r["path"]).read_text()) for r in b["compiled"]["sample_refs"]]
        cand, _ = compile_binding(llm, docs, 6, b["compiled"]["sample_refs"], b["compiled"]["regression_refs"])
        (d / "lab-a.v6.json").write_text(json.dumps(cand))
        try:
            approve_binding(d / "lab-a.v6.json", "Mallory", "human", [], False, directory=d)
            out["b_compiled_unsafe_binding_approved"] = True
        except ApprovalError as e:
            out["b_compiled_unsafe_binding_approved"] = False
            out["b_reason"] = str(e)[:100]
        out["registry_entries"] = len(Registry(d).entries())
    finally:
        shutil.rmtree(d)
    return out


def r6_revoke_fallback():
    d = Path(tempfile.mkdtemp(prefix="sg_rt31_"))
    try:
        b = json.loads((BH / "lab-a.v4.json").read_text())
        shutil.copy(BH / "lab-a.v4.json", d / "lab-a.v4.json")
        approve_binding(d / "lab-a.v4.json", "T", "human", [], False, directory=d)
        docs = [json.loads((ROOT / r["path"]).read_text()) for r in b["compiled"]["sample_refs"]]
        cand, _ = compile_binding(b["compiled"]["llm_binding"], docs, 5, b["compiled"]["sample_refs"], b["compiled"]["regression_refs"])
        (d / "lab-a.v5.json").write_text(json.dumps(cand))
        approve_binding(d / "lab-a.v5.json", "T", "human", [], False, directory=d)
        Registry(d).revoke("lab-a", 5, "T", "v5 found unsafe")
        return {"active_after_revoking_v5": [(x["binding_id"], x["version"]) for x in load_approved(d)]}
    finally:
        shutil.rmtree(d)


def r7_processing_exception():
    from spoolgeist_h import capture as CAP
    d = Path(tempfile.mkdtemp(prefix="sg_rt31_"))
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
            w.write(RT.doc("A", 1)[1].encode())
            await w.drain()
            w.write_eof()
            await asyncio.sleep(1.0)
            w.close()
            srv.close()
        asyncio.run(go())
        rq = [json.loads(p.read_text()) for p in (d / "review_queue").glob("*.result.json")]
        return {"job_persisted": len(list((d / "jobs").glob("*.prn"))), "review_queue_entries": len(rq),
                "review_status": [x["status"] for x in rq],
                "event_logged": "job_processing_error" in (d / "events.jsonl").read_text()}
    finally:
        CAP.Capture.process_job = orig
        shutil.rmtree(d)


if __name__ == "__main__":
    out = {"system": "v3.1 (active bindings: " + ", ".join(f"{b['binding_id']} v{b['version']}" for b in RT.P3.bindings) + ")",
           "text_probes": RT.run_text_probes(), "R5_forgery": r5_forgery_paths(), "R6_revoke_fallback": r6_revoke_fallback(),
           "R7_processing_exception": r7_processing_exception()}
    p = ROOT / "phase2" / "stage2" / "results" / "redteam_v31_frozen.json"
    p.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: (v if k != "text_probes" else {n: x["v3"] for n, x in v.items()}) for k, v in out.items()}, indent=1, default=str))
