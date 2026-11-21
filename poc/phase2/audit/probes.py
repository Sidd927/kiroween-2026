"""Phase 2 / Stage 1 audit probes against the FROZEN v2.1 system.

Read-only with respect to the system under test: nothing in spoolgeist/, bench/, bindings/ or runtime/ is modified.
Every probe writes into phase2/audit/results/ or a temporary directory.

usage (from poc/):  .venv/bin/python -m phase2.audit.probes [probe ...]
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import random
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bench import generator as G                      # noqa: E402
from bench import run_benchmark as RB                 # noqa: E402
from bench.score import classify, field_checks        # noqa: E402
from spoolgeist import interpreter, llm               # noqa: E402
from spoolgeist.grid import normalize, sniff          # noqa: E402

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)
llm.FORBID["enabled"] = True
BINDINGS = RB.load_bindings()
LAYOUTS = list("ABCDEF")


def run(text: str):
    return interpreter.process(BINDINGS, normalize(text.encode() if isinstance(text, str) else text).text)


def clean(layout: str, seed: int, **kw):
    rng = random.Random(seed)
    r = G.make_report(layout, rng, **kw)
    return r, G.RENDER[layout](r, G.Opts())


# ----------------------------------------------------------------------------- P01 anchors anywhere
def p01_anchor_anywhere():
    """(a) header_changed + page_break per layout (new page-1 header, old continuation header);
    (b) unregistered layout G with another lab's anchor lines appended on a later page."""
    out = {"a_header_changed_with_old_continuation": {}, "b_foreign_doc_with_old_anchor_page": {}}
    for lay in LAYOUTS:
        c = Counter()
        for s in range(200):
            rng = random.Random(10_000 + s)
            r = G.make_report(lay, rng)
            o = G.Opts(new_header=True)
            if lay in G.PAGEABLE and len(r.results) >= 4:
                o.page_break_after = rng.randint(2, len(r.results) - 2)
            else:
                c["not_pageable"] += 1
                continue
            oc = run(G.RENDER[lay](r, o))
            ok = oc.status == "ACCEPT" and all(v for k, v in field_checks(oc.record, G.truth(r)).items() if k.startswith("crit:"))
            c[f"{oc.status}{'(data_correct)' if ok else ''}"] += 1
        out["a_header_changed_with_old_continuation"][lay] = dict(c)
    # (b): take the static anchor lines of each binding from one of its own clean documents
    for lay in LAYOUTS:
        b = next(x for x in BINDINGS if x["binding_id"] == f"lab-{lay.lower()}")
        _, own = clean(lay, 1)
        own_lines = normalize(own.encode()).text.split("\n")
        import regex
        anchor_lines = []
        for a in b["layout"]["anchors"]:
            ln = next((l for l in own_lines if regex.search(a, l)), None)
            if ln:
                anchor_lines.append(ln)
        c = Counter()
        for s in range(20):
            rg, gtxt = clean("G", 90_000 + s)
            oc = run(gtxt + "\n\f" + "\n".join(anchor_lines))
            c[f"{oc.status}:{oc.binding_id}:{(oc.reasons or [''])[0].split(':')[0]}"] += 1
        out["b_foreign_doc_with_old_anchor_page"][lay] = dict(c)
    return out


# ----------------------------------------------------------------------------- P02 truncation sweep
def p02_truncation_sweep():
    """A spooler that closes gracefully after a cancelled/truncated job produces an EOF-terminated prefix,
    which capture.py records as 'complete'. Sweep every line-boundary prefix of clean docs."""
    res = {}
    for lay in LAYOUTS:
        c = Counter()
        examples = []
        for s in range(15):
            r, txt = clean(lay, 20_000 + s)
            full = run(txt)
            lines = txt.split("\n")
            nonblank_total = sum(1 for l in lines if l.strip() and l.strip() != "\f")
            for k in range(1, len(lines)):
                prefix = "\n".join(lines[:k])
                lost = sum(1 for l in lines[k:] if l.strip() and l.strip() != "\f")
                if lost == 0:
                    continue
                oc = run(prefix)
                if oc.status != "ACCEPT":
                    c["reject"] += 1
                    continue
                same = full.status == "ACCEPT" and oc.record == full.record
                c["accept_same_record" if same else "accept_DIFFERENT_record"] += 1
                if len(examples) < 2:
                    examples.append({"seed": 20_000 + s, "kept_lines": k, "lost_nonblank_lines": lost,
                                     "lost_text": [l for l in lines[k:] if l.strip()][:4], "same_record": same})
        res[lay] = {"counts": dict(c), "examples": examples}
    return res


# ----------------------------------------------------------------------------- P03 concatenated jobs
def p03_concatenated_jobs():
    """Two different patients' reports in ONE print job (batch printing). Variant 'damaged': the second
    report's ID and name labels are damaged so field regexes do not see it."""
    res = {}
    for lay in LAYOUTS:
        c = Counter()
        for s in range(40):
            r1, t1 = clean(lay, 30_000 + s)
            r2, t2 = clean(lay, 31_000 + s)
            for variant in ("plain", "damaged"):
                t2v = t2
                if variant == "damaged":
                    for lbl in ("Lab No.", "Patient Name", "Reg. No", "Name", "Patient ID", "Patient", "UHID", "MRN", "PT:",
                                "Sex/Age", "Collected", "Sample collected on", "COLLECTED"):
                        t2v = t2v.replace(lbl, lbl.lower().replace("e", "3"))
                oc = run(t1 + "\n" + t2v)
                cls = "REJECT" if oc.status == "REJECT" else (
                    "ACCEPT_patient1_data_only" if oc.record["results"] and all(v for k, v in field_checks(oc.record, G.truth(r1)).items() if k.startswith("crit:"))
                    else "ACCEPT_MIXED")
                c[f"{variant}:{cls}"] += 1
        res[lay] = dict(c)
    return res


# ----------------------------------------------------------------------------- P04 optional fields silently dropped
def p04_optional_field_damage():
    """Damage one character of the age/sex label: is the document accepted with age/sex = None even though
    the printed report contains them? (not a wrong value, but silent loss of printed data)"""
    labels = {"A": "Age / Sex", "B": "Age  :", "C": "/", "D": "Age/Sex", "E": "Sex/Age", "F": "AGE:"}
    res = {}
    for lay in LAYOUTS:
        c = Counter()
        for s in range(30):
            r, txt = clean(lay, 40_000 + s)
            lab = labels[lay]
            if lab not in txt:
                # find actual label in this layout
                c["label_not_found"] += 1
                continue
            if lay == "C":   # "(M/45)" -> "(M-45)" on the Patient line only
                ln = next(l for l in txt.split("\n") if l.startswith("Patient :"))
                dmg = txt.replace(ln, ln.replace("/", "-"), 1)
            else:
                dmg = txt.replace(lab, lab[:-1] + "#", 1)
            oc = run(dmg)
            if oc.status == "ACCEPT":
                c[f"ACCEPT age={'None' if oc.record['patient_age'] is None else 'set'} sex={'None' if oc.record['patient_sex'] is None else 'set'}"] += 1
            else:
                c["REJECT"] += 1
        res[lay] = dict(c)
    return res


# ----------------------------------------------------------------------------- P05 encodings & overstrike
def p05_encoding_and_overstrike():
    res = {}
    r, txt = clean("B", 50_001)
    name = f"{r.first} {r.last}"
    for label, enc_name in (("utf8_e_acute", "José " + r.last), ("plain_ascii", "Jose " + r.last)):
        t = txt.replace(name, enc_name)
        for codec in ("utf-8", "cp1252"):
            raw = t.encode(codec)
            n = normalize(raw)
            oc = interpreter.process(BINDINGS, n.text) if n.text else None
            res[f"{label}/{codec}"] = {"sniff": sniff(raw), "status": oc.status if oc else "REJECT(normalize)",
                                       "reasons": (oc.reasons if oc else n.notes)[:2],
                                       "extracted_name": (oc.record or {}).get("patient_name") if oc else None}
    # cp437 box-drawing table borders (DOS style) on an otherwise ASCII report
    r, txt = clean("D", 50_002)
    t = txt.replace("+", "┼").replace("|", "│")
    raw = t.encode("cp437")
    n = normalize(raw)
    res["cp437_box_drawing_layoutD"] = {"sniff": sniff(raw), "normalized_ok": bool(n.text), "notes": n.notes}
    # impact-printer overstrike: bold (X\bX) and underline (X\b_) on the patient name
    r, txt = clean("A", 50_003)
    nm = G.printed_name(r)
    bold = "".join(ch + "\b" + ch for ch in nm)
    under = "".join(ch + "\b_" for ch in nm)
    for label, rep in (("bold_overstrike", bold), ("underline_overstrike", under), ("underline_first", "".join("_\b" + ch for ch in nm))):
        oc = run(txt.replace(nm, rep, 1).encode("latin-1"))
        res[label] = {"status": oc.status, "name": (oc.record or {}).get("patient_name"), "reasons": oc.reasons[:1]}
    # CR-only overprint of a line (bold by reprinting the line): "line\rline"
    lines = txt.split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith("Patient Name"))
    lines[i] = lines[i] + "\r" + lines[i]
    oc = run("\n".join(lines))
    res["cr_overprint_line"] = {"status": oc.status, "reasons": oc.reasons[:1]}
    return res


# ----------------------------------------------------------------------------- P06 binding integrity
def p06_binding_integrity():
    """(a) the SHA-256 'pin' lives inside the same file -> an edited binding with a recomputed _meta.sha256 loads;
    (b) load_bindings uses `assert`, which python -O removes."""
    res = {}
    tmp = Path(tempfile.mkdtemp(prefix="sg_audit_"))
    try:
        (tmp / "bindings").mkdir()
        for p in (ROOT / "bindings").glob("*.v1.json"):
            shutil.copy(p, tmp / "bindings" / p.name)
        p = tmp / "bindings" / "lab-a.v1.json"
        b = json.loads(p.read_text())
        meta = b.pop("_meta")
        b["results"]["labels"]["M.C.H."], b["results"]["labels"]["M.C.V."] = "MCV", "MCH"   # silent code swap
        meta["sha256"] = hashlib.sha256(json.dumps(b, sort_keys=True).encode()).hexdigest()
        p.write_text(json.dumps({"_meta": meta, **b}, indent=1))
        old = RB.ROOT
        RB.ROOT = tmp
        try:
            loaded = RB.load_bindings()
        finally:
            RB.ROOT = old
        res["a_tampered_with_recomputed_hash_loads"] = any(x["binding_id"] == "lab-a" and x["results"]["labels"]["M.C.H."] == "MCV" for x in loaded)
        # does the swapped rule produce an ACCEPT with wrong codes? MCV (fL ~80-100) vs MCH (pg ~27-32)
        c = Counter()
        for s in range(30):
            r, txt = clean("A", 60_000 + s)
            oc = interpreter.process(loaded, normalize(txt.encode()).text)
            c[classify(oc.status, oc.record, {"expected": "accept", "truth": G.truth(r)})] += 1
        res["a_tampered_rule_outcomes_on_clean_A"] = dict(c)
        # (b) tamper WITHOUT fixing the hash, run load_bindings under -O and without
        b["results"]["labels"]["M.C.H."] = "MCH"
        p.write_text(json.dumps({"_meta": {**meta, "sha256": "0" * 64}, **b}, indent=1))
        code = ("import sys; sys.path.insert(0, %r); from bench import run_benchmark as RB; from pathlib import Path; "
                "RB.ROOT = Path(%r); print(len(RB.load_bindings()))") % (str(ROOT), str(tmp))
        py = str(ROOT / ".venv" / "bin" / "python")
        for flag in ([], ["-O"]):
            p_ = subprocess.run([py, *flag, "-c", code], capture_output=True, text=True)
            res[f"b_bad_hash_load{'_with_-O' if flag else ''}"] = (p_.stdout.strip() or p_.stderr.strip().splitlines()[-1])
    finally:
        shutil.rmtree(tmp)
    res["c_freeze_manifest_covers"] = RB.FROZEN
    res["c_not_covered"] = ["bindings/*.json", "spoolgeist/fhir_builder.py", "spoolgeist/capture.py", "tests/*"]
    return res


# ----------------------------------------------------------------------------- P07 capture: forward + duplicates + logs
async def _rst_printer(port_holder, received):
    """Fake printer that reads the whole job, then closes with TCP RST (SO_LINGER 0)."""
    async def h(reader, writer):
        data = await reader.read()
        received.append(hashlib.sha256(data).hexdigest())
        sock = writer.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        writer.transport.abort()
    srv = await asyncio.start_server(h, "127.0.0.1", 0)
    port_holder.append(srv.sockets[0].getsockname()[1])
    return srv


async def _send(port, data):
    r, w = await asyncio.open_connection("127.0.0.1", port)
    w.write(data)
    await w.drain()
    w.write_eof()
    try:
        await asyncio.wait_for(r.read(), 3)
    except Exception:
        pass
    w.close()


async def _p07():
    from spoolgeist.capture import Capture
    res = {}
    # (a) printer accepts the job and resets the connection -> forward_job treats it as failure and resends
    received, ph = [], []
    srv = await _rst_printer(ph, received)
    spool = Path(tempfile.mkdtemp(prefix="sg_cap_"))
    cap = Capture(spool, "127.0.0.1", 0, f"127.0.0.1:{ph[0]}", process=False)
    s = await asyncio.start_server(cap.handle, "127.0.0.1", 0)
    lport = s.sockets[0].getsockname()[1]
    job = b"RST TEST JOB\n" * 50
    await _send(lport, job)
    await asyncio.sleep(9)
    metas = [json.loads(p.read_text()) for p in (spool / "jobs").glob("*.json")]
    res["a_printer_RST_after_full_receipt"] = {"copies_received_by_printer": len(received),
                                               "forward_status": [m["forward"] for m in metas]}
    s.close(); srv.close()
    shutil.rmtree(spool)
    # (b) duplicate state is in memory only: restart -> same bytes not flagged; and a deliberate reprint IS flagged
    spool = Path(tempfile.mkdtemp(prefix="sg_cap_"))
    dup = []
    for instance in range(2):
        cap = Capture(spool, "127.0.0.1", 0, None, process=False)
        s = await asyncio.start_server(cap.handle, "127.0.0.1", 0)
        lport = s.sockets[0].getsockname()[1]
        await _send(lport, b"SAME BYTES\n")
        if instance == 0:
            await _send(lport, b"SAME BYTES\n")       # immediate reprint by the user
        await asyncio.sleep(0.3)
        s.close()
    for p in sorted((spool / "jobs").glob("*.json")):
        dup.append(json.loads(p.read_text())["duplicate_of"] is not None)
    res["b_duplicate_flags_[inst0_job1, inst0_reprint, inst1_after_restart]"] = sorted(dup, key=lambda x: x)  # order by name unreliable
    res["b_note"] = "expected by design: reprint flagged True; after restart the same bytes are NOT flagged (state lost)"
    res["b_flags_raw"] = dup
    shutil.rmtree(spool)
    # (c) PHI in logs: process a doc with an implausible name -> reason text is written to events.jsonl
    spool = Path(tempfile.mkdtemp(prefix="sg_cap_"))
    cap = Capture(spool, "127.0.0.1", 0, None, process=True)
    r, txt = clean("A", 70_001)
    nm = G.printed_name(r)
    bad = txt.replace(nm, nm + " 2", 1)  # digit in name -> V2 rejects with the name in the reason
    s = await asyncio.start_server(cap.handle, "127.0.0.1", 0)
    await _send(s.sockets[0].getsockname()[1], bad.encode())
    await asyncio.sleep(1.5)
    s.close()
    ev = (spool / "events.jsonl").read_text()
    res["c_patient_name_in_events_log"] = nm in ev
    res["c_patient_id_in_events_log"] = r.patient_id in ev
    modes = {p.name.split(".")[-1]: oct(p.stat().st_mode & 0o777) for p in (spool / "jobs").iterdir()}
    res["c_file_modes"] = modes
    shutil.rmtree(spool)
    return res


def p07_capture():
    return asyncio.run(_p07())


# ----------------------------------------------------------------------------- P08 PBT false-reject anatomy
def p08_pbt_false_reject_reasons(n=3000, seed=8):
    """Re-create the property-test case mix with a plain RNG and record WHY valid-labelled docs were rejected."""
    sys.path.insert(0, str(ROOT / "tests"))
    import test_property_abstain_or_correct as T
    rng = random.Random(seed)
    by = defaultdict(Counter)
    totals = Counter()
    for i in range(n):
        lay = rng.choice(LAYOUTS)
        valid = rng.sample(T.VALID, rng.randint(0, 3))
        invalid = rng.choice([None] * 3 + T.INVALID)
        fuzz = rng.sample(T.FUZZ, rng.randint(0, 2))
        d = T.build(lay, rng.randint(0, 10**9), valid, invalid, fuzz)
        oc = interpreter.process(BINDINGS, normalize(d["text"].encode()).text)
        cls = classify(oc.status, oc.record, d)
        totals[cls] += 1
        if cls == "false_reject":
            reason = (oc.reasons or ["?"])[0].split(":")[0].split(" ")[0:2]
            key = "+".join(sorted(fuzz)) or "(no fuzz)"
            by[key][" ".join(reason)] += 1
    return {"totals": dict(totals), "false_reject_reasons_by_fuzz": {k: dict(v.most_common(6)) for k, v in sorted(by.items())}}


# ----------------------------------------------------------------------------- P09 scoring blind spots
def p09_scoring_blind_spots():
    """What does an ACCEPT get wrong that the scorer does not count? flags, reference ranges, sex, age, reported."""
    res = {}
    for lay in LAYOUTS:
        c = Counter()
        for s in range(60):
            r, txt = clean(lay, 80_000 + s)
            oc = run(txt)
            if oc.status != "ACCEPT":
                c["reject"] += 1
                continue
            c["accept"] += 1
            rec = oc.record
            if rec["patient_sex"] != ("male" if r.sex == "M" else "female"):
                c["sex_wrong_or_missing"] += 1
            if rec["patient_age"] != r.age:
                c["age_wrong_or_missing"] += 1
            if rec.get("reported") not in (None, r.reported.strftime("%Y-%m-%d")):
                c["reported_wrong"] += 1
            if rec.get("reported") is None:
                c["reported_missing"] += 1
            got = {x["code"]: x for x in rec["results"]}
            for x in r.results:
                g = got.get(x.code)
                if not g:
                    continue
                exp_flag = x.flag
                gf = g.get("flag") or ""
                # layouts B/C/E print a non-H/L marker; compare "abnormal or not" only
                if (gf != "") != (exp_flag != ""):
                    c["flag_presence_wrong"] += 1
                elif lay in G.FLAG_HL and gf != exp_flag:
                    c["flag_direction_wrong"] += 1
                if "ref_low" in g and (g["ref_low"], g["ref_high"]) != (x.low, x.high):
                    c["ref_range_wrong"] += 1
                if "ref_low" not in g:
                    c["ref_range_not_captured"] += 1
        res[lay] = dict(c)
    res["note"] = "score.CRITICAL = patient_id, patient_name, collected + result code/value/unit. Flags, ranges, sex, age, reported are not scored."
    return res


# ----------------------------------------------------------------------------- P10 FHIR round trip
def p10_fhir_roundtrip():
    from spoolgeist.fhir_builder import build_bundle
    from spoolgeist.dictionary import DICT
    from decimal import Decimal
    issues, n = Counter(), 0
    for lay in LAYOUTS:
        for s in range(20):
            r, txt = clean(lay, 85_000 + s)
            norm = normalize(txt.encode())
            oc = interpreter.process(BINDINGS, norm.text)
            if oc.status != "ACCEPT":
                continue
            n += 1
            b = json.loads(build_bundle(oc.record, norm.text, norm.sha256, abdm=True))
            res = {e["resource"]["resourceType"]: e["resource"] for e in b["entry"] if e["resource"]["resourceType"] != "Observation"}
            obs = [e["resource"] for e in b["entry"] if e["resource"]["resourceType"] == "Observation"]
            if res["Patient"]["identifier"][0]["value"] != r.patient_id:
                issues["patient_id"] += 1
            if res["Patient"].get("gender") != ("male" if r.sex == "M" else "female"):
                issues["gender"] += 1
            if not res["DiagnosticReport"]["effectiveDateTime"].startswith(r.collected.strftime("%Y-%m-%d")):
                issues["effective_date"] += 1
            if "T" in res["DiagnosticReport"]["effectiveDateTime"] and not res["DiagnosticReport"]["effectiveDateTime"].startswith(r.collected.strftime("%Y-%m-%dT%H:%M")):
                issues["effective_time"] += 1
            truth = {x.code: x for x in r.results}
            for o in obs:
                code = next(k for k, v in DICT["tests"].items() if v["loinc"] == o["code"]["coding"][0]["code"])
                x = truth.get(code)
                if x is None:
                    issues["observation_not_in_truth"] += 1
                    continue
                f = Decimal(str(DICT["tests"][code]["units"][x.unit]))
                if Decimal(str(o["valueQuantity"]["value"])) != Decimal(x.value) * f:
                    issues["value_conversion"] += 1
                if o["valueQuantity"]["code"] != DICT["tests"][code]["ucum"]:
                    issues["ucum"] += 1
                if bool(o.get("interpretation")) != bool(x.flag):
                    issues["interpretation_presence"] += 1
            if len(obs) != len(r.results):
                issues["observation_count"] += 1
            pf = res["DiagnosticReport"]["presentedForm"][0]
            import base64
            if hashlib.sha256(base64.b64decode(pf["data"])).hexdigest() == norm.sha256:
                issues["_presentedForm_is_raw_bytes"] += 1
            else:
                issues["presentedForm_is_normalised_text_not_original_bytes"] += 1
    return {"bundles_checked": n, "issues": dict(issues)}


PROBES = {k: v for k, v in globals().items() if k.startswith("p") and k[1:3].isdigit()}

if __name__ == "__main__":
    names = sys.argv[1:] or sorted(PROBES)
    allres = {}
    for name in names:
        fn = next(v for k, v in PROBES.items() if k.startswith(name))
        t0 = time.time()
        r = fn()
        allres[fn.__name__] = r
        print(f"=== {fn.__name__} ({time.time() - t0:.1f}s)")
        print(json.dumps(r, indent=1, default=str)[:4000])
        (OUT / f"{fn.__name__}.json").write_text(json.dumps(r, indent=1, default=str))
