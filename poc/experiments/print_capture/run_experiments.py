"""Automated print-capture experiments E1-E9 (no Windows, no CUPS): a RAW/AppSocket client stands in
for the OS spooler's port monitor. See README in this folder for the Windows and CUPS experiments.
usage: .venv/bin/python -m experiments.print_capture.run_experiments
"""
import hashlib, json, shutil, socket, struct, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RT = ROOT / "runtime" / "print_capture"
LP, PP = 19100, 19101
PY = str(ROOT / ".venv" / "bin" / "python")
procs = {}
results = []


def start_listener():
    procs["listener"] = subprocess.Popen([PY, "-m", "spoolgeist.capture", "--port", str(LP), "--forward", f"127.0.0.1:{PP}",
                                          "--spool", str(RT / "spool"), "--idle", "2"], cwd=ROOT,
                                         stdout=open(RT / "listener.log", "a"), stderr=subprocess.STDOUT)
    wait_port(LP)


def start_printer():
    procs["printer"] = subprocess.Popen([PY, "experiments/print_capture/fake_printer.py", "--port", str(PP), "--out",
                                         str(RT / "fake_printer")], cwd=ROOT,
                                        stdout=open(RT / "printer.log", "a"), stderr=subprocess.STDOUT)
    wait_port(PP)


def stop(name):
    p = procs.pop(name, None)
    if p:
        p.terminate(); p.wait(5)


def wait_port(port, t=10):
    end = time.time() + t
    while time.time() < end:
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close()
            return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"port {port} not up")


def raw_send(data: bytes, half_then_reset=False):
    s = socket.create_connection(("127.0.0.1", LP), 3)
    if half_then_reset:
        s.sendall(data[: len(data) // 2])
        time.sleep(0.2)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))  # RST on close
        s.close()
        return
    s.sendall(data)
    s.shutdown(socket.SHUT_WR)
    s.recv(10)   # wait for server close
    s.close()


def events():
    p = RT / "spool" / "events.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


def printed():
    p = RT / "fake_printer" / "printed.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


def doc(doc_id):
    lay = doc_id[0]
    split = "test"
    d = json.loads((ROOT / "data/corpus" / split / lay / f"{doc_id}.json").read_text())
    return d["text"].encode("ascii")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def record(name, ok, **kw):
    results.append({"experiment": name, "pass": ok, **kw})
    print(("PASS " if ok else "FAIL ") + name, json.dumps(kw, default=str)[:300], flush=True)


def wait_for(pred, t=8):
    end = time.time() + t
    while time.time() < end:
        v = pred()
        if v:
            return v
        time.sleep(0.1)
    return None


if __name__ == "__main__":
    shutil.rmtree(RT, ignore_errors=True); RT.mkdir(parents=True)
    start_printer(); start_listener()

    # E1 basic capture + byte-identical forward + deterministic processing
    b = doc("A-11000-clean"); h = sha(b)
    raw_send(b)
    cap = wait_for(lambda: [e for e in events() if e["event"] == "job_captured" and e["sha256"] == h])
    fw = wait_for(lambda: [e for e in events() if e["event"] == "job_forwarded" and e["sha256"] == h])
    pr = wait_for(lambda: [p for p in printed() if p["sha256"] == h])
    proc = wait_for(lambda: [e for e in events() if e["event"] == "job_processed" and cap and e["job_id"] == cap[0]["job_id"]])
    stored = (RT / "spool" / "jobs" / f"{cap[0]['job_id']}.prn").read_bytes() if cap else b""
    record("E1 capture, preserve, forward, process", bool(cap and fw and pr and proc and sha(stored) == h and proc[0]["status"] == "ACCEPT"),
           sent_sha=h, stored_sha=sha(stored), printer_sha=pr[0]["sha256"] if pr else None,
           processing=proc[0] if proc else None)

    # E9 ESC/P job (layout B, contains printer control codes): forwarded byte-identical incl. control codes
    b = doc("B-21000-clean"); h = sha(b)
    raw_send(b)
    pr = wait_for(lambda: [p for p in printed() if p["sha256"] == h])
    proc = wait_for(lambda: [e for e in events() if e["event"] == "job_processed" and e["status"] in ("ACCEPT", "REJECT") and e.get("binding") == "lab-b"])
    record("E9 ESC/P control codes preserved for printer, stripped for extraction", bool(pr and proc and proc[-1]["status"] == "ACCEPT"),
           esc_bytes_in_job=b.count(b"\x1b"), printer_sha_matches=bool(pr), processing=proc[-1] if proc else None)

    # E8 malformed report -> captured + forwarded (the paper still prints) but data goes to review
    b = doc("A-12050-unit_incompatible"); h = sha(b)
    raw_send(b)
    pr = wait_for(lambda: [p for p in printed() if p["sha256"] == h])
    proc = wait_for(lambda: [e for e in events() if e["event"] == "job_processed" and e["status"] == "REJECT" and "unit_not_accepted" in str(e.get("reasons"))])
    record("E8 invalid report: printed normally, data refused to review queue", bool(pr and proc), processing=proc[0] if proc else None)

    # E7 non-text job (PostScript): forwarded, not parsed
    b = b"%!PS-Adobe-3.0\n%%Title: synthetic\n/Courier findfont 10 scalefont setfont 72 720 moveto (SYNTHETIC) show showpage\n"; h = sha(b)
    raw_send(b)
    pr = wait_for(lambda: [p for p in printed() if p["sha256"] == h])
    proc = wait_for(lambda: [e for e in events() if e["event"] == "job_processed" and "unsupported format: postscript" in str(e.get("reasons"))])
    record("E7 PostScript job: forwarded byte-identical, extraction refused (unsupported)", bool(pr and proc), processing=proc[0] if proc else None)

    # E5 duplicate resend: printed twice (legitimate reprint), data emitted once
    b = doc("C-31000-clean"); h = sha(b)
    raw_send(b); time.sleep(0.5); raw_send(b)
    pr = wait_for(lambda: (lambda x: x if len(x) >= 2 else None)([p for p in printed() if p["sha256"] == h]))
    caps = [e for e in events() if e["event"] == "job_captured" and e["sha256"] == h]
    procs_ = wait_for(lambda: (lambda x: x if len(x) >= 2 else None)([e for e in events() if e["event"] == "job_processed" and e["job_id"] in {c["job_id"] for c in caps}]))
    statuses = sorted(e["status"] for e in procs_ or [])
    record("E5 duplicate job: forwarded twice, data emitted once", bool(pr and statuses == ["ACCEPT", "DUPLICATE"]),
           printed_copies=len(pr or []), processing_statuses=statuses)

    # E3 printer unavailable: capture continues, forward retried, delivered exactly once
    stop("printer")
    b = doc("D-41000-clean"); h = sha(b)
    raw_send(b)
    fail = wait_for(lambda: [e for e in events() if e["event"] == "forward_failed"])
    time.sleep(1.5); start_printer()
    fw = wait_for(lambda: [e for e in events() if e["event"] == "job_forwarded" and e["sha256"] == h], t=20)
    time.sleep(3)
    copies = [p for p in printed() if p["sha256"] == h]
    record("E3 printer offline: job kept, forwarded after recovery exactly once", bool(fail and fw and len(copies) == 1),
           failed_attempts_before_success=len([e for e in events() if e["event"] == "forward_failed"]), copies=len(copies))

    # E2 listener unavailable: what the sending side sees
    stop("listener")
    b = doc("E-51000-clean"); h = sha(b)
    try:
        raw_send(b); err = None
    except OSError as e:
        err = f"{e.__class__.__name__}: {e}"
    start_listener()
    raw_send(b)   # emulated spooler retry
    caps = wait_for(lambda: [e for e in events() if e["event"] == "job_captured" and e["sha256"] == h])
    record("E2 listener offline: client gets connection refused; nothing captured until retry", bool(err and caps and len(caps) == 1),
           client_error=err, captured_after_retry=len(caps or []),
           note="Real Windows spooler retry behaviour NOT tested here (needs the Windows VM experiment).")

    # E4 interrupted transfer: incomplete job quarantined, not forwarded, not processed; full resend works
    b = doc("F-61000-clean"); h = sha(b)
    n_before = len(printed())
    raw_send(b, half_then_reset=True)
    inc = wait_for(lambda: [e for e in events() if e["event"] == "job_incomplete"])
    raw_send(b)
    caps = wait_for(lambda: [e for e in events() if e["event"] == "job_captured" and e["sha256"] == h])
    time.sleep(1.5)
    partial_sha = inc[0]["sha256"] if inc else None
    partial_printed = [p for p in printed() if p["sha256"] == partial_sha]
    partial_processed = [e for e in events() if e["event"] == "job_processed" and inc and e["job_id"] == inc[0]["job_id"]]
    record("E4 interrupted transfer: partial job quarantined (not printed/processed), full resend accepted once",
           bool(inc and caps and len(caps) == 1 and not partial_printed and not partial_processed),
           incomplete_reason=inc[0]["incomplete_reason"] if inc else None, partial_bytes=inc[0]["bytes"] if inc else None)

    # E6 limits: oversize job and idle client
    big = b"A" * 2_100_000
    try:
        raw_send(big)
    except OSError:
        pass
    over = wait_for(lambda: [e for e in events() if e["event"] == "job_incomplete" and "max_bytes" in str(e.get("incomplete_reason"))])
    s = socket.create_connection(("127.0.0.1", LP)); s.sendall(b"partial"); time.sleep(3)
    idle = wait_for(lambda: [e for e in events() if e["event"] == "job_incomplete" and "idle" in str(e.get("incomplete_reason"))])
    s.close()
    record("E6 limits: >2 MB job and idle client are cut off and quarantined", bool(over and idle))

    stop("listener"); stop("printer")
    (RT / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print(f"\n{sum(r['pass'] for r in results)}/{len(results)} experiments passed")
