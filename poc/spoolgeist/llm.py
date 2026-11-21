"""The ONLY place where an LLM is called. Used for (a) rule generation / repair and
(b) the direct-extraction baseline. Never used by the deterministic pipeline.

Implementation: the Claude Code CLI in headless mode (`claude -p`), with all tools
disabled and the default system prompt replaced, run from an EMPTY temporary directory so
the model cannot read any project file (in particular the held-out test set).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Optional

SYNTH = "SYNTHETIC SAMPLE - NOT A REAL PATIENT"
LOG = Path(__file__).resolve().parents[1] / "runtime" / "llm_calls.jsonl"
CALLS = {"count": 0, "cost_usd": 0.0}
FORBID = {"enabled": False}   # set True during deterministic evaluation: any call raises


class LLMForbidden(RuntimeError):
    pass


def presend_guard(documents: List[str]) -> None:
    """Refuse to send any document that is not explicitly marked synthetic.
    (In a real deployment this is where the synthetic-twin check would sit; see report 13.)"""
    for d in documents:
        if SYNTH not in d:
            raise PermissionError("pre-send guard: document is not marked synthetic; refusing to send to LLM")


def call(prompt: str, documents: List[str], purpose: str, model: str = "sonnet",
         system: str = "You are a precise engineer. Output only what is asked.", timeout: int = 600) -> dict:
    if FORBID["enabled"]:
        raise LLMForbidden(f"LLM call attempted during deterministic evaluation ({purpose})")
    presend_guard(documents)
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="sg_llm_") as empty:
        p = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--output-format", "json", "--tools", "",
             "--system-prompt", system, "--no-session-persistence"],
            cwd=empty, capture_output=True, text=True, timeout=timeout)
    dt = time.time() - t0
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"LLM CLI failed: rc={p.returncode} {p.stderr[:400]} {p.stdout[:400]}")
    CALLS["count"] += 1
    CALLS["cost_usd"] += out.get("total_cost_usd") or 0
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({"ts": t0, "purpose": purpose, "model": list((out.get("modelUsage") or {}).keys()),
                            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                            "seconds": round(dt, 1), "cost_usd": out.get("total_cost_usd"),
                            "is_error": out.get("is_error")}) + "\n")
    return {"text": out.get("result") or "", "seconds": dt, "cost_usd": out.get("total_cost_usd"),
            "model": list((out.get("modelUsage") or {}).keys())}


def extract_json(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    s = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(s)
