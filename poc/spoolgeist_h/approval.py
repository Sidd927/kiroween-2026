"""Approval workflow (v3.1, review RV-2). A gate report on disk is NEVER trusted.

approve_binding():
  1. loads the binding file and the exact operator-verified documents it references (path + SHA-256); any missing
     or changed document -> refuse
  2. RE-COMPILES the binding from its stored original LLM output and those samples; the result must be identical to
     the file (proves the compiled block was produced by the compiler, not hand-edited)
  3. RE-RUNS gate v2 against the currently active bindings and their samples
  4. only if the fresh gate passes (and warnings are acknowledged, dates confirmed where required) is the approval
     appended to the hash-chained registry, with the fresh gate report's hash; the fresh report is written to
     gate_reports/ for the reviewer's reference
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Tuple

from .compile import compile_binding
from .gate import run_gate
from .registry import DEFAULT_DIR, Registry, canonical_sha, load_approved

ROOT = Path(__file__).resolve().parents[1]


class ApprovalError(RuntimeError):
    pass


def ref_for(path: Path) -> dict:
    return {"path": str(Path(path).resolve().relative_to(ROOT)), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def load_refs(refs: List[dict]) -> List[dict]:
    docs = []
    for r in refs:
        p = ROOT / r["path"]
        if not p.exists():
            raise ApprovalError(f"referenced sample missing: {r['path']}")
        if hashlib.sha256(p.read_bytes()).hexdigest() != r["sha256"]:
            raise ApprovalError(f"referenced sample changed since compilation: {r['path']}")
        docs.append(json.loads(p.read_text()))
    return docs


def gate_binding(b: dict, directory: Path = DEFAULT_DIR, allow_agent_approval: bool = True) -> Tuple[dict, dict]:
    C = b.get("compiled") or {}
    if not C.get("llm_binding") or not C.get("sample_refs") or not C.get("regression_refs"):
        raise ApprovalError("binding lacks compiler provenance (llm_binding / sample_refs / regression_refs)")
    approved = load_refs(C["sample_refs"])
    regression = load_refs(C["regression_refs"])
    again, crep = compile_binding(C["llm_binding"], approved, b["version"], C["sample_refs"], C["regression_refs"])
    if canonical_sha(again) != canonical_sha(b):
        raise ApprovalError("re-compilation does not reproduce this binding: the compiled block was edited or the "
                            "compiler changed; recompile and re-review")
    gen = [d for d in regression if d.get("split") == "gen"]
    dev = [d for d in regression if d.get("split") == "dev"]
    active = load_approved(directory, allow_agent_approval)
    samples = {}
    for ab in active:
        docs = load_refs(ab["compiled"].get("sample_refs", []))
        from .compile import sample_class
        samples[ab["binding_id"]] = [d for d in docs if sample_class(d) == "clean"]
    gate = run_gate(b, gen, dev, active, samples, crep)
    gate["compile_report"] = crep
    return gate, crep


def approve_binding(binding_file: Path, approver: str, kind: str, acks: List[str], date_confirmed: bool,
                    note: str = "", directory: Path = DEFAULT_DIR) -> Tuple[dict, dict]:
    binding_file = Path(binding_file)
    b = json.loads(binding_file.read_text())
    gate, _ = gate_binding(b, directory, allow_agent_approval=True)
    gdir = Path(directory) / "gate_reports"
    gdir.mkdir(parents=True, exist_ok=True)
    (gdir / f"{b['binding_id']}.v{b['version']}.gate.json").write_text(json.dumps(gate, indent=1, default=str))
    if not gate["passed"]:
        failed = [k for k, v in gate["conditions"].items() if not v["passed"]]
        raise ApprovalError(f"gate (re-run at approval) failed: {failed}")
    e = Registry(directory).record_approval(b, binding_file.name, gate, approver, kind, acks, date_confirmed, note)
    return e, gate
