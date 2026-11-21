"""v3 deterministic pipeline entry point: print-job bytes -> normalised text -> approved bindings -> Outcome. NO LLM."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from . import interpreter
from .grid import normalize
from .interpreter import Outcome
from .registry import DEFAULT_DIR, load_approved


class Pipeline:
    def __init__(self, bindings: Optional[List[dict]] = None, directory: Path = DEFAULT_DIR,
                 recognition: str = "full", allow_agent_approval: bool = False):
        if recognition not in interpreter.MODES:
            raise ValueError(recognition)
        self.mode = recognition
        self.bindings = bindings if bindings is not None else load_approved(directory, allow_agent_approval)

    def process_bytes(self, raw: bytes) -> Outcome:
        norm = normalize(raw)
        if not norm.text:
            return Outcome("REJECT", None, reasons=norm.notes or ["empty document"])
        return interpreter.process(self.bindings, norm.text, self.mode, norm.ff_page_starts)

    def process_normalized(self, norm) -> Outcome:
        return interpreter.process(self.bindings, norm.text, self.mode, norm.ff_page_starts)
