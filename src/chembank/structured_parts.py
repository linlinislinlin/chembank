"""Part-level helpers for CIE structured papers (Paper 2/3/4/5).

IDs / filenames use compact slugs: ``2(a)(i)`` → ``2a-i`` → draft ``q2a-i.txt``,
vault id ``…-q2a-i``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_ROMAN_VAL = {
    "i": 1,
    "ii": 2,
    "iii": 3,
    "iv": 4,
    "v": 5,
    "vi": 6,
    "vii": 7,
    "viii": 8,
    "ix": 9,
    "x": 10,
}

# Romans before letters so "(i)" is not captured as letter "i".
PART_START_RE = re.compile(
    r"(?m)^(?:"
    r"\((?P<lr_letter>[a-z])\)\s*\((?P<lr_roman>[ivx]+)\)"
    r"|\((?P<roman>iv|ix|vi{0,3}|iii|ii|i|v|x)\)"
    r"|\((?P<letter>[a-z])\)"
    r")",
    re.IGNORECASE,
)

MS_PART_HEAD_RE = re.compile(
    r"(?m)^(?P<label>\d{1,2}\([a-z]\)(?:\([ivx]+\))?)\s*$",
    re.IGNORECASE,
)

QUESTION_LABEL_RE = re.compile(
    r"^(?P<parent>\d{1,2})\((?P<letter>[a-z])\)(?:\((?P<roman>[ivx]+)\))?$",
    re.IGNORECASE,
)

GARBAGE_MS_RE = re.compile(
    r"(?:^|\s)1(?:\s+1){4,}"  # 1 1 1 1 1 mark-grid OCR
    r"|(?:Marks\s+){2,}"
    r"|Cambridge International AS & A Level\s*–\s*Mark Scheme"
    r"|PUBLISHED\s*Answer",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PartId:
    parent: str
    letter: str
    roman: str | None = None

    @property
    def label(self) -> str:
        if self.roman:
            return f"{self.parent}({self.letter})({self.roman})"
        return f"{self.parent}({self.letter})"

    @property
    def part(self) -> str:
        if self.roman:
            return f"({self.letter})({self.roman})"
        return f"({self.letter})"

    @property
    def slug(self) -> str:
        base = f"{self.parent}{self.letter.lower()}"
        if self.roman:
            return f"{base}-{self.roman.lower()}"
        return base

    @property
    def draft_stem(self) -> str:
        return f"q{self.slug}"

    def sort_key(self) -> tuple:
        return (
            int(self.parent),
            self.letter.lower(),
            _ROMAN_VAL.get((self.roman or "").lower(), 0),
        )


def parse_part_id(label_or_slug: str) -> PartId | None:
    """Parse ``2(a)(i)``, ``2a-i``, or ``q2a-i`` into PartId."""
    s = str(label_or_slug).strip()
    if s.startswith("q") and re.match(r"^q\d", s):
        s = s[1:]
    m = QUESTION_LABEL_RE.match(s)
    if m:
        return PartId(
            parent=str(int(m.group("parent"))),
            letter=m.group("letter").lower(),
            roman=(m.group("roman") or "").lower() or None,
        )
    m = re.fullmatch(r"(\d{1,2})([a-z])(?:-([ivx]+))?", s, re.I)
    if m:
        return PartId(
            parent=str(int(m.group(1))),
            letter=m.group(2).lower(),
            roman=(m.group(3) or "").lower() or None,
        )
    return None


def question_id_prefix(qid: str) -> str:
    """``cie-9701-2021-mj-p21-q2a-i`` → ``cie-9701-2021-mj-p21``."""
    m = re.match(r"^(.+)-q.+$", qid)
    return m.group(1) if m else qid


def draft_stem_sort_key(stem: str) -> tuple:
    pid = parse_part_id(stem)
    if pid:
        return pid.sort_key()
    m = re.fullmatch(r"q?(\d+)$", stem)
    if m:
        return (int(m.group(1)), "", 0)
    return (999, stem, 0)


def is_garbage_ms_text(text: str | None) -> bool:
    """True when MS OCR is unusable (prefer *-ms.png instead)."""
    if text is None:
        return True
    s = text.strip()
    if not s:
        return True
    if GARBAGE_MS_RE.search(s):
        return True
    # Dense lone "1" tokens from marks columns
    ones = len(re.findall(r"(?:^|\s)1(?:\s|$)", s))
    if ones >= 8 and "M1" not in s and len(s) < 800:
        return True
    return False


def _normalize_part_layout(text: str) -> str:
    """Ensure part markers sit at line starts (CIE sometimes prints ``5 (a)``)."""
    text = text or ""
    # "5 (a) …" / "5 (a) (i) …" on the question opener line
    text = re.sub(
        r"(?m)^(\d{1,2})\s+(\([a-z]\)(?:\s*\([ivx]+\))?)",
        r"\1\n\2",
        text,
        count=1,
        flags=re.I,
    )
    # CIE prints "(ii) …" / "(e)(ii) …" glued to the "DO NOT WRITE IN THIS
    # MARGIN" trailer at the end of the preceding line. Split it to its own line
    # so the part is recognised as a new unit rather than swallowed by the
    # previous part.
    text = re.sub(
        r"(?m)(DO\s+NOT\s+WRITE\s+IN\s+THIS\s+MARGIN[\s\S]*?)(\([a-z]\)(?:\([ivx]+\))?|\([ivx]+\))(?=\s|\Z)",
        lambda m: m.group(1).rstrip() + "\n" + m.group(2),
        text,
        flags=re.I,
    )
    return text


def split_main_question_into_parts(
    parent: str,
    text: str,
    *,
    start_line: int = 1,
    page_hint: int | None = None,
) -> list[tuple[PartId, str]]:
    """Split one main structured question body into smallest part units.

    Shared stem (before first ``(a)``) and letter preambles (``(a)`` / ``(b)``
    text before the first roman) are prepended to each leaf part for context.

    Part bodies end at the next part marker — the next roman, the next lettered
    stem (``(b)`` / ``(c)``), or end of question — and must not swallow a
    following letter preamble.
    """
    text = _normalize_part_layout(text or "")
    matches = list(PART_START_RE.finditer(text))
    if not matches:
        return []

    nodes: list[tuple[str, str | None, int]] = []
    cur_letter: str | None = None
    for m in matches:
        if m.group("lr_letter"):
            cur_letter = m.group("lr_letter").lower()
            nodes.append((cur_letter, m.group("lr_roman").lower(), m.start()))
        elif m.group("letter"):
            cur_letter = m.group("letter").lower()
            nodes.append((cur_letter, None, m.start()))
        elif m.group("roman") and cur_letter:
            nodes.append((cur_letter, m.group("roman").lower(), m.start()))

    if not nodes:
        return []

    letters_with_romans = {L for L, R, _ in nodes if R}
    leaves: list[tuple[str, str | None, int]] = []
    for L, R, start in nodes:
        if R is not None:
            leaves.append((L, R, start))
        elif L not in letters_with_romans:
            leaves.append((L, None, start))

    stem = text[: nodes[0][2]].strip()
    # Letter preamble: from letter-only marker to first roman of that letter
    letter_starts = {L: start for L, R, start in nodes if R is None}
    first_roman_at: dict[str, int] = {}
    for L, R, start in nodes:
        if R is not None and L not in first_roman_at:
            first_roman_at[L] = start

    # Hard stops include letter stems so (a)(iii) ends at (b), not at (b)(i).
    boundaries = {start for _, _, start in leaves}
    boundaries.update(letter_starts.values())
    boundaries.add(len(text))

    out: list[tuple[PartId, str]] = []
    for L, R, start in leaves:
        later = [b for b in boundaries if b > start]
        end = min(later) if later else len(text)
        part_body = text[start:end].strip()
        # Truncate trailing total line belonging to whole question
        part_body = re.sub(r"\n\s*\[Total:\s*\d+\s*\]\s*$", "", part_body).strip()
        bits: list[str] = []
        if stem:
            bits.append(stem)
        if R is not None and L in letter_starts and L in first_roman_at:
            pre = text[letter_starts[L] : first_roman_at[L]].strip()
            if pre:
                bits.append(pre)
        bits.append(part_body)
        body = "\n".join(bits)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        out.append((PartId(parent=str(parent), letter=L, roman=R), body))
    return out


def parse_structured_ms_parts(text: str, *, max_q: int = 20) -> dict[str, str]:
    """Split clean MS text into ``{ '2(a)(i)': block, ... }``.

    Expects part headers on their own lines (``page.get_text`` without heavy
    symbol recovery). Returns {} if no headers found.
    """
    text = text or ""
    valid: list[re.Match[str]] = []
    for m in MS_PART_HEAD_RE.finditer(text):
        pid = parse_part_id(m.group("label"))
        if pid and 1 <= int(pid.parent) <= max_q:
            valid.append(m)
    if not valid:
        return {}

    blocks: dict[str, str] = {}
    for i, m in enumerate(valid):
        pid = parse_part_id(m.group("label"))
        assert pid is not None
        start = m.start()
        end = valid[i + 1].start() if i + 1 < len(valid) else len(text)
        block = text[start:end].strip()
        block = re.sub(r"\n?----- PAGE \d+ -----\n?", "\n", block)
        # Drop footer noise lightly
        block = re.sub(
            r"(?m)^\s*(?:©\s*UCLES.*|Page \d+ of \d+|9701/\d+.*)\s*$",
            "",
            block,
        )
        block = re.sub(r"\n{3,}", "\n\n", block).strip()
        if block:
            blocks[pid.label] = block
    return blocks


def aggregate_ms_by_parent(parts: dict[str, str]) -> dict[str, str]:
    """Roll part MS blocks up to main-question keys for legacy ``ms_structured.json``."""
    by_parent: dict[str, list[str]] = {}
    for label, block in parts.items():
        pid = parse_part_id(label)
        if not pid:
            continue
        by_parent.setdefault(pid.parent, []).append(block)
    return {p: "\n\n".join(v).strip() for p, v in by_parent.items()}
