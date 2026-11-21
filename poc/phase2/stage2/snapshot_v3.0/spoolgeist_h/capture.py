"""RAW / AppSocket (port 9100) print-job capture with store-and-forward.

This is the protocol used by Windows "Standard TCP/IP Port" (RAW mode), CUPS `socket://` and most
network printers: the client opens TCP, streams the job bytes, half-closes, and the server closes.

Behaviour (PoC):
  * listen on a configured interface only (default 127.0.0.1), optional client allow-list
  * a job is COMPLETE only when the client half-closes cleanly (EOF). Resets/timeouts -> 'incomplete':
    kept in quarantine, NOT forwarded and NOT processed (the spooler is expected to resend)
  * hard limits: max bytes per job, idle timeout
  * complete jobs are written to disk (bytes + metadata JSON with SHA-256) BEFORE anything else
  * then forwarded byte-for-byte to the configured printer (store-and-forward).
    v3 (F-02): a job is retried automatically ONLY if no byte reached the printer connection. Once any byte has
    been written, an abnormal close (reset, timeout) marks the job `sent_unconfirmed` and it is NOT resent
    automatically, because the printer may already have printed it. An operator resends explicitly (--resend).
    v3 (F-13): event logs carry reason CODES only (no patient values); spool files are created 0600 in 0700 dirs.
    v3 (F-22): bindings are loaded through the approval registry, not the benchmark module.
  * duplicates (same SHA-256 from the same peer within a window) are forwarded (a reprint is a
    legitimate printer action) but flagged so data is emitted only once
  * finally the job is handed to the deterministic pipeline (no LLM) -> FHIR or review queue
"""
from __future__ import annotations

import argparse
import asyncio
import os
import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]


def _wb(p: Path, data: bytes, fsync: bool = False):
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
        if fsync:
            f.flush()
            os.fsync(f.fileno())


def _wt(p: Path, s: str, fsync: bool = False):
    _wb(p, s.encode(), fsync)


class Capture:
    def __init__(self, spool: Path, listen_host: str, listen_port: int, forward: Optional[str],
                 max_bytes: int = 2_000_000, idle_timeout: float = 10.0, allow: Optional[list] = None,
                 dup_window_s: int = 600, process: bool = True, allow_agent_approval: bool = False):
        self.allow_agent_approval = allow_agent_approval
        self.spool = spool
        spool.mkdir(parents=True, exist_ok=True)
        os.chmod(spool, 0o700)
        for d in ("jobs", "incomplete", "out", "review_queue"):
            (spool / d).mkdir(parents=True, exist_ok=True)
            os.chmod(spool / d, 0o700)
        self.tasks = set()                   # keep references to background forward tasks
        self.listen = (listen_host, listen_port)
        self.forward = forward
        self.max_bytes, self.idle = max_bytes, idle_timeout
        self.allow = set(allow or [])
        self.dup_window = dup_window_s
        self.process_jobs = process
        self.recent = {}                     # (peer_ip, sha) -> (time, job_id)
        self.lock = asyncio.Lock()

    # ------------------------------------------------------------------ receive
    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        peer_ip = peer[0] if peer else "?"
        started = time.time()
        if self.allow and peer_ip not in self.allow:
            self.log("refused_client", peer=peer_ip)
            writer.close()
            return
        buf, complete, reason = bytearray(), False, ""
        try:
            while True:
                chunk = await asyncio.wait_for(reader.read(65536), timeout=self.idle)
                if not chunk:
                    complete = True
                    break
                buf += chunk
                if len(buf) > self.max_bytes:
                    reason = f"exceeds max_bytes={self.max_bytes}"
                    break
        except asyncio.TimeoutError:
            reason = f"idle timeout {self.idle}s"
        except (ConnectionResetError, BrokenPipeError) as e:
            reason = f"connection reset: {e.__class__.__name__}"
        finally:
            try:
                writer.close()
            except Exception:
                pass
        raw = bytes(buf)
        sha = hashlib.sha256(raw).hexdigest()
        job_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        meta = {"job_id": job_id, "peer": peer_ip, "received_at": started, "seconds": round(time.time() - started, 3),
                "bytes": len(raw), "sha256": sha, "complete": complete and not reason, "incomplete_reason": reason or None}
        if not meta["complete"]:
            _wb(self.spool / "incomplete" / f"{job_id}.prn", raw)
            _wt(self.spool / "incomplete" / f"{job_id}.json", json.dumps(meta, indent=1))
            self.log("job_incomplete", **meta)
            return
        async with self.lock:
            key = (peer_ip, sha)
            prev = self.recent.get(key)
            meta["duplicate_of"] = prev[1] if prev and started - prev[0] < self.dup_window else None
            self.recent[key] = (started, job_id)
        from .grid import sniff
        meta["detected_format"] = sniff(raw)
        meta["forward"] = {"target": self.forward, "status": "pending" if self.forward else "disabled", "attempts": 0}
        self._write(job_id, raw, meta)                      # 1. persist first
        self.log("job_captured", **{k: meta[k] for k in ("job_id", "peer", "bytes", "sha256", "detected_format", "duplicate_of")})
        if self.forward:
            task = asyncio.create_task(self.forward_job(job_id))  # 2. forward (async, retried only if safe)
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
        if self.process_jobs:
            await asyncio.get_running_loop().run_in_executor(None, self.process_job, job_id)  # 3. extract

    def _write(self, job_id, raw, meta):
        _wb(self.spool / "jobs" / f"{job_id}.prn", raw, fsync=True)
        _wt(self.spool / "jobs" / f"{job_id}.json", json.dumps(meta, indent=1), fsync=True)

    def _save_meta(self, job_id, meta):
        _wt(self.spool / "jobs" / f"{job_id}.json", json.dumps(meta, indent=1), fsync=True)

    def _meta(self, job_id):
        return json.loads((self.spool / "jobs" / f"{job_id}.json").read_text())

    # ------------------------------------------------------------------ forward
    async def forward_job(self, job_id: str, max_attempts: int = 5, backoff: float = 1.0, operator_resend: bool = False):
        host, port = self.forward.split(":")
        raw = (self.spool / "jobs" / f"{job_id}.prn").read_bytes()
        for attempt in range(1, max_attempts + 1):
            meta = self._meta(job_id)
            st = meta["forward"]["status"]
            if st == "sent" or (st in ("sending", "sent_unconfirmed") and not operator_resend):
                return
            meta["forward"]["attempts"] = meta["forward"].get("attempts", 0) + 1
            try:
                r, w = await asyncio.wait_for(asyncio.open_connection(host, int(port)), timeout=5)
            except (OSError, asyncio.TimeoutError) as e:
                # nothing was written: safe to retry
                meta["forward"].update(status="retrying" if attempt < max_attempts else "failed", last_error=str(e)[:120])
                self._save_meta(job_id, meta)
                self.log("forward_failed", job_id=job_id, attempt=attempt, error=e.__class__.__name__)
                await asyncio.sleep(backoff * attempt)
                continue
            meta["forward"].update(status="sending", sending_since=time.time())
            self._save_meta(job_id, meta)          # persisted BEFORE the first byte: a crash now means "unconfirmed"
            operator_resend = False
            try:
                w.write(raw)
                await w.drain()
                w.write_eof()
                try:
                    await asyncio.wait_for(r.read(), timeout=10)   # printer may send status bytes, then closes
                except asyncio.TimeoutError:
                    pass
                w.close()
            except (OSError, asyncio.TimeoutError) as e:
                meta["forward"].update(status="sent_unconfirmed", last_error=str(e)[:120])
                self._save_meta(job_id, meta)
                self.log("forward_unconfirmed", job_id=job_id, attempt=attempt, error=e.__class__.__name__,
                         action="NOT resent automatically; operator must check the printer and use --resend if needed")
                return
            meta["forward"].update(status="sent", sent_at=time.time(), sha256_sent=hashlib.sha256(raw).hexdigest())
            self._save_meta(job_id, meta)
            self.log("job_forwarded", job_id=job_id, attempt=attempt, sha256=meta["forward"]["sha256_sent"])
            return

    async def retry_pending(self):
        for p in sorted((self.spool / "jobs").glob("*.json")):
            m = json.loads(p.read_text())
            st = m.get("forward", {}).get("status")
            if st == "sending":     # crashed mid-send in a previous run: the printer may have printed it
                m["forward"]["status"] = "sent_unconfirmed"
                self._save_meta(m["job_id"], m)
                self.log("forward_unconfirmed", job_id=m["job_id"], reason="listener stopped during send")
            elif self.forward and st in ("pending", "retrying", "failed"):
                await self.forward_job(m["job_id"])

    # ------------------------------------------------------------------ process (deterministic, no LLM)
    def process_job(self, job_id: str):
        from . import llm
        from .fhir_builder import build_bundle
        from .grid import normalize
        from .pipeline import Pipeline
        llm.FORBID["enabled"] = True
        meta = self._meta(job_id)
        raw = (self.spool / "jobs" / f"{job_id}.prn").read_bytes()
        t0 = time.perf_counter()
        norm = normalize(raw)
        result = {"job_id": job_id, "sha256": meta["sha256"], "llm_calls": 0}
        if meta.get("duplicate_of"):
            result.update(status="DUPLICATE", reasons=[f"same bytes as {meta['duplicate_of']}; data not re-emitted"])
        elif not norm.text:
            result.update(status="REJECT", reasons=norm.notes)
        else:
            oc = Pipeline(allow_agent_approval=self.allow_agent_approval).process_normalized(norm)
            result.update(status=oc.status, binding=oc.binding_id, reasons=oc.reasons)
            if oc.status == "ACCEPT":
                _wt(self.spool / "out" / f"{job_id}.fhir.json", build_bundle(oc.record, norm.text, norm.sha256, abdm=True))
        result["ms"] = round((time.perf_counter() - t0) * 1000, 2)
        dest = "out" if result["status"] == "ACCEPT" else "review_queue"
        _wt(self.spool / dest / f"{job_id}.result.json", json.dumps(result, indent=1))   # full reasons: protected file
        codes = [str(x).split(":")[0].split(" ")[0:2] for x in result.get("reasons") or []]
        self.log("job_processed", **{k: result.get(k) for k in ("job_id", "status", "binding", "ms", "llm_calls")},
                 reason_codes=[" ".join(c) for c in codes])     # F-13: no patient values in the event log

    # ------------------------------------------------------------------ util
    def log(self, event, **kw):
        line = json.dumps({"t": round(time.time(), 3), "event": event, **kw}, default=str)
        print(line, flush=True)
        p = self.spool / "events.jsonl"
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a") as f:
            f.write(line + "\n")

    async def serve(self):
        await self.retry_pending()
        srv = await asyncio.start_server(self.handle, *self.listen)
        self.log("listening", host=self.listen[0], port=self.listen[1], forward=self.forward)
        async with srv:
            await srv.serve_forever()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1", help="interface to bind (never 0.0.0.0 on a public network)")
    ap.add_argument("--port", type=int, default=9100)
    ap.add_argument("--forward", default=None, help="host:port of the real printer (RAW/9100)")
    ap.add_argument("--spool", default=str(ROOT / "runtime_h" / "capture"))
    ap.add_argument("--allow", nargs="*", default=None)
    ap.add_argument("--no-process", action="store_true")
    ap.add_argument("--idle", type=float, default=10.0)
    ap.add_argument("--max-bytes", type=int, default=2_000_000)
    ap.add_argument("--allow-agent-approved-bindings", action="store_true",
                    help="EXPERIMENTS ONLY: also load bindings approved by an AI agent rather than a human")
    ap.add_argument("--resend", metavar="JOB_ID", help="operator: resend one job (e.g. after sent_unconfirmed) and exit")
    a = ap.parse_args()
    c = Capture(Path(a.spool), a.host, a.port, a.forward, allow=a.allow, process=not a.no_process,
                idle_timeout=a.idle, max_bytes=a.max_bytes, allow_agent_approval=a.allow_agent_approved_bindings)
    if a.resend:
        asyncio.run(c.forward_job(a.resend, operator_resend=True))
        return
    asyncio.run(c.serve())


if __name__ == "__main__":
    main()
