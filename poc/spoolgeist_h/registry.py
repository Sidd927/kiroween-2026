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

    def record_approval(self, binding: dict, binding_file_name: str, gate: dict, approver: str, approver_kind: str,
                        acknowledged_warnings: List[str], date_format_confirmed: bool, note: str = "") -> dict:
        """Low-level append. Call it through spoolgeist_h.approval.approve_binding, which RE-RUNS the gate itself
        (v3.1, review RV-2); a gate report read from disk is never trusted."""
        if approver_kind not in ("human", "agent"):
            raise ValueError("approver_kind must be human or agent")
        b = binding
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
                             "binding_file": binding_file_name, "binding_sha256": sha,
                             "gate_report_sha256": canonical_sha(gate), "gate_rerun_at_approval": True,
                             "approver": approver, "approver_kind": approver_kind,
                             "acknowledged_warnings": sorted(acknowledged_warnings),
                             "date_format_confirmed": bool(date_format_confirmed), "note": note})

    def revoke(self, binding_id: str, version: int, approver: str, reason: str) -> dict:
        return self._append({"action": "revoke", "binding_id": binding_id, "version": version,
                             "approver": approver, "reason": reason})

    def reactivate(self, binding_id: str, version: int, approver: str, reason: str) -> dict:
        approved = {(e["binding_id"], e["version"]) for e in self.entries() if e["action"] == "approve"}
        if (binding_id, version) not in approved:
            raise ValueError(f"{binding_id} v{version} was never approved")
        return self._append({"action": "reactivate", "binding_id": binding_id, "version": version,
                             "approver": approver, "reason": reason})

    def active(self, allow_agent_approval: bool = False) -> Dict[str, dict]:
        """v3.1 (review RV-3): the LAST explicit decision per binding id wins. Revoking the active version leaves the
        id with NO active version (no silent fallback to an older one) until a person approves a new version or
        explicitly reactivates an approved, non-revoked one."""
        approvals: Dict[tuple, dict] = {}
        revoked = set()
        current: Dict[str, Optional[tuple]] = {}
        for e in self.entries():
            key = (e["binding_id"], e["version"])
            if e["action"] == "approve":
                if e["approver_kind"] == "agent" and not allow_agent_approval:
                    continue
                approvals[key] = e
                revoked.discard(key)
                current[e["binding_id"]] = key
            elif e["action"] == "revoke":
                revoked.add(key)
                if current.get(e["binding_id"]) == key:
                    current[e["binding_id"]] = None
            elif e["action"] == "reactivate":
                if key in approvals and key not in revoked:
                    current[e["binding_id"]] = key
        return {bid: approvals[k] for bid, k in current.items() if k}


def load_approved(directory: Path = DEFAULT_DIR, allow_agent_approval: bool = False) -> List[dict]:
    """Load only bindings whose exact content is approved and currently active (see Registry.active)."""
    reg = Registry(directory)
    out = []
    for bid, e in sorted(reg.active(allow_agent_approval).items()):
        if Path(e["binding_file"]).name != e["binding_file"]:
            raise RegistryIntegrityError(f"binding_file must be a plain file name: {e['binding_file']!r}")
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
    a = sub.add_parser("approve", help="re-derives the binding and RE-RUNS the gate, then records the approval")
    a.add_argument("binding_file")
    a.add_argument("--approver", required=True)
    a.add_argument("--kind", choices=["human", "agent"], default="human")
    a.add_argument("--ack", nargs="*", default=[])
    a.add_argument("--confirm-date-format", action="store_true")
    a.add_argument("--note", default="")
    for name in ("revoke", "reactivate"):
        r = sub.add_parser(name)
        r.add_argument("binding_id")
        r.add_argument("version", type=int)
        r.add_argument("--approver", required=True)
        r.add_argument("--reason", required=True)
    sub.add_parser("verify")
    sub.add_parser("list")
    x = ap.parse_args()
    reg = Registry()
    if x.cmd == "approve":
        from .approval import approve_binding
        e, gate = approve_binding(Path(x.binding_file), x.approver, x.kind, x.ack, x.confirm_date_format, x.note)
        print(json.dumps(e, indent=1))
    elif x.cmd == "revoke":
        print(json.dumps(reg.revoke(x.binding_id, x.version, x.approver, x.reason), indent=1))
    elif x.cmd == "reactivate":
        print(json.dumps(reg.reactivate(x.binding_id, x.version, x.approver, x.reason), indent=1))
    elif x.cmd == "verify":
        es = reg.entries()
        print(f"chain OK: {len(es)} entries, head {reg.head()}")
        for b in load_approved(allow_agent_approval=True):
            print("  active+intact:", b["binding_id"], "v", b["version"])
    else:
        for e in reg.entries():
            print(e["seq"], e["action"], e["binding_id"], e.get("version"), e.get("approver_kind", ""), e.get("approver", ""))


if __name__ == "__main__":
    main()
