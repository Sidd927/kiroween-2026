"""Append-only, hash-chained approval registry for bindings (F-07, F-08a).

A binding file is just a candidate until the registry holds an `approve` entry for its exact SHA-256.
Each entry stores the SHA-256 of the previous entry, so editing or deleting history breaks the chain and the
loader refuses to start. Integrity checks raise explicit exceptions, never `assert` (removed by python -O).

Approver kinds:
  human  - a named person ran `python -m spoolgeist_h.registry approve ...`
  agent  - an AI agent recorded the approval for an EXPERIMENT. Production loading refuses these unless
           allow_agent_approval=True is passed explicitly (Phase 2 experiments do; the result docs say so).

This is tamper-EVIDENT, not tamper-proof: an attacker with write access can rewrite the whole chain. Anchoring the
chain head elsewhere (git commit, printed hash, external log) is a production item (report 07).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "bindings_h"
GENESIS = "0" * 64


class RegistryIntegrityError(RuntimeError):
    pass


def canonical_sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def file_sha(p: Path) -> str:
    return canonical_sha(json.loads(p.read_text()))


class Registry:
    def __init__(self, directory: Path = DEFAULT_DIR):
        self.dir = Path(directory)
        self.path = self.dir / "approvals.jsonl"

    def entries(self) -> List[dict]:
        if not self.path.exists():
            return []
        out, prev = [], GENESIS
        for n, line in enumerate(self.path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            e = json.loads(line)
            body = {k: v for k, v in e.items() if k != "entry_sha256"}
            if e.get("prev_sha256") != prev:
                raise RegistryIntegrityError(f"approvals.jsonl line {n}: chain broken (prev hash mismatch)")
            if canonical_sha(body) != e.get("entry_sha256"):
                raise RegistryIntegrityError(f"approvals.jsonl line {n}: entry hash mismatch (entry edited)")
            prev = e["entry_sha256"]
            out.append(e)
        return out

    def head(self) -> str:
        es = self.entries()
        return es[-1]["entry_sha256"] if es else GENESIS

    def _append(self, body: dict) -> dict:
        es = self.entries()
        body = {"seq": len(es) + 1, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **body,
                "prev_sha256": es[-1]["entry_sha256"] if es else GENESIS}
        body["entry_sha256"] = canonical_sha(body)
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(json.dumps(body, sort_keys=True) + "\n")
        return body

    def approve(self, binding_file: Path, gate_report_file: Path, approver: str, approver_kind: str,
                acknowledged_warnings: List[str], date_format_confirmed: bool, note: str = "") -> dict:
        if approver_kind not in ("human", "agent"):
            raise ValueError("approver_kind must be human or agent")
        b = json.loads(Path(binding_file).read_text())
        gate = json.loads(Path(gate_report_file).read_text())
        sha = canonical_sha(b)
        if gate.get("binding_sha256") != sha:
            raise ValueError("gate report was produced for a different binding version")
        if not gate.get("passed"):
            raise ValueError("gate did not pass; refusing to approve")
        missing = sorted(set(gate.get("warnings_requiring_ack", [])) - set(acknowledged_warnings))
        if missing:
            raise ValueError(f"unacknowledged gate warnings: {missing}")
        if gate.get("date_format_confirmation_required") and not date_format_confirmed:
            raise ValueError("date format is not disambiguated by the samples; explicit confirmation required")
        for e in self.entries():
            if e["action"] == "approve" and e["binding_id"] == b["binding_id"] and e["version"] == b["version"] \
                    and e["binding_sha256"] != sha:
                raise ValueError(f"{b['binding_id']} v{b['version']} already approved with different content; bump the version")
        return self._append({"action": "approve", "binding_id": b["binding_id"], "version": b["version"],
                             "binding_file": Path(binding_file).name, "binding_sha256": sha,
                             "gate_report_sha256": canonical_sha(gate), "approver": approver,
                             "approver_kind": approver_kind, "acknowledged_warnings": sorted(acknowledged_warnings),
                             "date_format_confirmed": bool(date_format_confirmed), "note": note})

    def revoke(self, binding_id: str, version: int, approver: str, reason: str) -> dict:
        return self._append({"action": "revoke", "binding_id": binding_id, "version": version,
                             "approver": approver, "reason": reason})

    def active(self, allow_agent_approval: bool = False) -> Dict[tuple, dict]:
        state: Dict[tuple, Optional[dict]] = {}
        for e in self.entries():
            key = (e["binding_id"], e["version"])
            if e["action"] == "approve":
                if e["approver_kind"] == "agent" and not allow_agent_approval:
                    continue
                state[key] = e
            elif e["action"] == "revoke":
                state[key] = None
        return {k: v for k, v in state.items() if v}


def load_approved(directory: Path = DEFAULT_DIR, allow_agent_approval: bool = False) -> List[dict]:
    """Load only bindings whose exact content is approved and not revoked. Latest approved version per id wins."""
    reg = Registry(directory)
    act = reg.active(allow_agent_approval)
    latest: Dict[str, dict] = {}
    for (bid, ver), e in act.items():
        if bid not in latest or ver > latest[bid]["version"]:
            latest[bid] = e
    out = []
    for bid, e in sorted(latest.items()):
        p = Path(directory) / e["binding_file"]
        if not p.exists():
            raise RegistryIntegrityError(f"approved binding file missing: {p.name}")
        b = json.loads(p.read_text())
        if canonical_sha(b) != e["binding_sha256"]:
            raise RegistryIntegrityError(f"{p.name}: content does not match approved SHA-256 (edited after approval)")
        out.append(b)
    return out


def main():
    ap = argparse.ArgumentParser(description="Binding approval registry")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("approve")
    a.add_argument("binding_file")
    a.add_argument("gate_report")
    a.add_argument("--approver", required=True)
    a.add_argument("--kind", choices=["human", "agent"], default="human")
    a.add_argument("--ack", nargs="*", default=[])
    a.add_argument("--confirm-date-format", action="store_true")
    a.add_argument("--note", default="")
    r = sub.add_parser("revoke")
    r.add_argument("binding_id")
    r.add_argument("version", type=int)
    r.add_argument("--approver", required=True)
    r.add_argument("--reason", required=True)
    sub.add_parser("verify")
    sub.add_parser("list")
    x = ap.parse_args()
    reg = Registry()
    if x.cmd == "approve":
        print(json.dumps(reg.approve(Path(x.binding_file), Path(x.gate_report), x.approver, x.kind, x.ack,
                                     x.confirm_date_format, x.note), indent=1))
    elif x.cmd == "revoke":
        print(json.dumps(reg.revoke(x.binding_id, x.version, x.approver, x.reason), indent=1))
    elif x.cmd == "verify":
        es = reg.entries()
        print(f"chain OK: {len(es)} entries, head {reg.head()}")
        for b in load_approved(allow_agent_approval=True):
            print("  approved+intact:", b["binding_id"], "v", b["version"])
    else:
        for e in reg.entries():
            print(e["seq"], e["action"], e["binding_id"], e.get("version"), e.get("approver_kind", ""), e.get("approver", ""))


if __name__ == "__main__":
    main()
