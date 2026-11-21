"""Raw print-job bytes -> normalised text grid.

Only plain-text / ESC-P style jobs are supported (what Windows' "Generic / Text Only"
driver and DOS-era LPT printing produce). PostScript, PCL graphics, PDF and raster are
detected and REFUSED, never guessed at.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

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
    lines: List[str] = field(default_factory=list)        # v3: text.split("\n")
    ff_page_starts: List[int] = field(default_factory=list)  # v3: line indices that begin a page after a form feed
    bold: Dict[int, Set[int]] = field(default_factory=dict)   # v4: line index -> bold columns


def sniff(raw: bytes, codepage: Optional[str] = None) -> str:
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
    # v4 (F-11): with a declared single-byte code page or UTF-8, bytes >= 0x80 are text, not binary
    hi_ok = codepage not in (None, "ascii")
    printable = sum(1 for b in raw if 32 <= b < 127 or b in (9, 10, 12, 13, 27) or (hi_ok and b >= 0x80))
    if raw and printable / len(raw) > 0.97:
        return "text+escp" if b"\x1b" in raw else "text"
    return "binary-unknown"


BOLD_ON, BOLD_OFF = "\x1e", "\x1f"


def _line_with_bold(s: str):
    """Remove bold sentinels and expand tabs; return (clean_line, set_of_bold_columns)."""
    out, bold, cols, on = [], [], set(), False
    for ch in s:
        if ch == BOLD_ON:
            on = True
        elif ch == BOLD_OFF:
            on = False
        elif ch == "\t":
            n = 8 - (len(out) % 8)
            out += [" "] * n
            bold += [on] * n
        else:
            out.append(ch)
            bold.append(on)
    line = "".join(out).rstrip()
    return line, {c for c, b in enumerate(bold[:len(line)]) if b}


def normalize(raw: bytes, codepage: Optional[str] = None) -> Normalized:
    """v4: decoding uses the print queue's DECLARED code page, strictly (F-11). No guessing: undecodable bytes ->
    REJECT. codepage=None means strict UTF-8 (ASCII is a subset). Bold (ESC E ... ESC F) is preserved as
    per-line column sets in Normalized.bold (F-04). Underline overstrike keeps the letter (F-12)."""
    fmt = sniff(raw, codepage)
    sha = hashlib.sha256(raw).hexdigest()
    if fmt not in ("text", "text+escp"):
        return Normalized("", 0, sha, fmt, [f"unsupported format: {fmt}"])
    enc = {None: "utf-8", "ascii": "ascii"}.get(codepage, codepage)
    b = raw.replace(b"\x1bE", BOLD_ON.encode()).replace(b"\x1bF", BOLD_OFF.encode())
    b = _ESC_SEQ.sub(b"", b)
    b = b.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    # backspace overstrike: underline in either order keeps the letter (F-12); bold "A\bA" -> "A"
    b = re.sub(rb"_\x08([^\x08])", rb"\1", b)
    b = re.sub(rb"([^\x08])\x08_", rb"\1", b)
    while b"\x08" in b:
        nb = re.sub(rb".\x08", b"", b)
        if nb == b:
            break
        b = nb
    pages = b.count(b"\x0c") or 1
    chunks = b.split(b"\x0c")
    lines, ff_starts, bold = [], [], {}
    other = re.compile(rb"[\x00-\x08\x0b\x0e-\x1a\x1c\x1d\x7f]")      # keeps the two bold sentinels
    for ci, ch in enumerate(chunks):
        ch = other.sub(b"", ch)
        try:
            s = ch.decode(enc)
        except (UnicodeDecodeError, LookupError) as e:
            return Normalized("", 0, sha, fmt, [f"decode_error: bytes are not valid {enc} ({e.__class__.__name__})"])
        if ci > 0:
            ff_starts.append(len(lines))
        for raw_line in s.split("\n"):
            ln, bc = _line_with_bold(raw_line)
            if bc:
                bold[len(lines)] = bc
            lines.append(ln)
    while lines and not lines[-1]:
        lines.pop()
    ff_starts = [i for i in ff_starts if i < len(lines)]
    n = Normalized("\n".join(lines), pages, sha, fmt, lines=lines, ff_page_starts=ff_starts)
    n.bold = {k: v for k, v in bold.items() if k < len(lines)}
    return n
