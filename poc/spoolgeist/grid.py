"""Raw print-job bytes -> normalised text grid.

Only plain-text / ESC-P style jobs are supported (what Windows' "Generic / Text Only"
driver and DOS-era LPT printing produce). PostScript, PCL graphics, PDF and raster are
detected and REFUSED, never guessed at.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import List

# ESC/P and ESC/P2 sequences commonly emitted by text-mode applications.
_ESC_SEQ = re.compile(
    rb"\x1b(?:"
    rb"[@EFGH45MPgO]"            # init, bold on/off, double-strike on/off, italic, pitch...
    rb"|[-WwxkltpQlNC!3Aa]."      # one-parameter commands (underline, double-width, NLQ, margins, line spacing...)
    rb"|\$..|\\..|J.|D[^\x00]*\x00|B[^\x00]*\x00"   # positioning / tab stops
    rb")",
    re.S,
)
_OTHER_CTRL = re.compile(rb"[\x00-\x08\x0b\x0e-\x1a\x1c-\x1f\x7f]")


@dataclass
class Normalized:
    text: str
    pages: int
    sha256: str
    detected_format: str
    notes: List[str] = field(default_factory=list)


def sniff(raw: bytes) -> str:
    head = raw[:64].lstrip(b"\x1b%-12345X@PJL \r\n")
    if raw.startswith(b"\x1b%-12345X") or b"@PJL" in raw[:200]:
        if b"LANGUAGE=POSTSCRIPT" in raw[:2000] or b"%!PS" in raw[:4000]:
            return "pjl+postscript"
        if b"LANGUAGE=PCL" in raw[:2000]:
            return "pjl+pcl"
    if head.startswith(b"%!PS") or raw.startswith(b"%!PS"):
        return "postscript"
    if raw.startswith(b"%PDF") or head.startswith(b"%PDF"):
        return "pdf"
    if raw.startswith(b"RaS2") or raw.startswith(b"UNIRAST"):
        return "raster"
    if b"\x1bE\x1b&" in raw[:200] or re.search(rb"\x1b[&*][a-z]", raw[:2000]):
        return "pcl"
    printable = sum(1 for b in raw if 32 <= b < 127 or b in (9, 10, 12, 13, 27))
    if raw and printable / len(raw) > 0.97:
        return "text+escp" if b"\x1b" in raw else "text"
    return "binary-unknown"


def normalize(raw: bytes) -> Normalized:
    fmt = sniff(raw)
    sha = hashlib.sha256(raw).hexdigest()
    if fmt not in ("text", "text+escp"):
        return Normalized("", 0, sha, fmt, [f"unsupported format: {fmt}"])
    b = _ESC_SEQ.sub(b"", raw)
    b = b.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    # backspace overstrike (bold/underline on impact printers): "A\bA" -> "A"
    while b"\x08" in b:
        nb = re.sub(rb".\x08", b"", b)
        if nb == b:
            break
        b = nb
    pages = b.count(b"\x0c") or 1
    b = b.replace(b"\x0c", b"\n")
    b = _OTHER_CTRL.sub(b"", b)
    try:
        s = b.decode("utf-8")
    except UnicodeDecodeError:
        s = b.decode("cp437")
    s = s.expandtabs(8)
    lines = [ln.rstrip() for ln in s.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return Normalized("\n".join(lines), pages, sha, fmt)
