"""Heuristic split of past-paper text into question chunks."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

# Main numbered questions: "1", "1.", "1)" at line start
MAIN_Q_RE = re.compile(
    r"^(?P<num>\d{1,2})(?:\s*[.)]?\s*)$|^(?P<num2>\d{1,2})(?:\s*[.)]\s+|\s+)(?=\S)",
    re.MULTILINE,
)

PART_RE = re.compile(r"^\(([a-z])\)(?:\s*\(([ivx]+)\))?", re.MULTILINE | re.IGNORECASE)
PAGE_RE = re.compile(r"^----- PAGE (?P<page>\d+) -----$", re.MULTILINE)
OPTION_RE = re.compile(r"^([A-D])\s*$", re.MULTILINE)

SKIP_BODY = re.compile(
    r"^(?:candidate|centre|syllabus|paper|session|cambridge|university|"
    r"section\s+[a-d]|instructions|information|blank page|"
    r"permission to reproduce|©\s*ucles|"
    r"hour\b|minute[s]?\b|soft\b|data booklet|total mark|correct answer|"
    # Periodic table end-matter rows often look like "16 8Ooxygen16.0 …"
    r"\d+[A-Z][a-z]+(?:helium|lithium|beryllium|oxygen|fluorine|neon|sodium))",
    re.IGNORECASE,
)

# Paper 3 Qualitative Analysis Notes (end matter) — not exam questions
QA_NOTES_START = re.compile(
    r"^(?:Reactions of (?:aqueous )?cations|Reactions of anions|Tests for gases|"
    r"Qualitative\s+Analysis(?:\s+Notes)?)\b",
    re.IGNORECASE,
)

# Inline stems usually start with these (CIE MCQ / structured)
STEM_START = re.compile(
    r"^(?:Which|What|How|Why|When|Where|Who|The |In |For |An |A |Use |Calculate|"
    r"Explain|Define|Describe|Deduce|Suggest|Identify|State|Give|Draw|Write|"
    r"Compare|Outline|Discuss|Predict|Determine|Show|Sketch|Consider|"
    r"Phosphorus|Sodium|Chlorine|Carbon|Nitrogen|Oxygen|Hydrogen|Ethene|Ethane|"
    r"Butane|Propane|Methane|Ethanol|Benzene|Graphite|Diamond|Ammonia|"
    r"Sulfur|Sulphur|Period|Group|Element|Compound|Molecule|Ion |Ions )",
    re.IGNORECASE,
)
FOOTER_NOISE = re.compile(
    r"^\s*(?:"
    r"©\s*UCLES.*"
    r"|9701/\d+/[A-Z]/J/\d+.*"
    r"|\[Turn over\]"
    r"|Page \d+ of \d+"
    r"|Permission to reproduce\b.*"
    r"|Every\s*reasonable effort has been made\b.*"
    r"|To avoid the issue of disclosure\b.*"
    r"|Cambridge Assessment International Education is part of\b.*"
    r"|Cambridge Assessment is the brand name\b.*"
    r"|BLANK PAGE"
    r")\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# CIE Paper 1 PDFs leak the printed page number as a trailing lone integer.
_TRAILING_PAGE_NUM = re.compile(r"^\d{1,2}$")


def strip_footer_noise(text: str) -> str:
    """Remove CIE footer / trailing page-number lines from a question body."""
    lines = text.splitlines()
    kept: list[str] = []
    for line in lines:
        if FOOTER_NOISE.match(line):
            continue
        # Truncate once the long copyright trailer begins mid-body (last Q).
        if re.match(r"^\s*Permission to reproduce\b", line, re.I):
            break
        if re.match(r"^\s*BLANK PAGE\s*$", line, re.I):
            break
        kept.append(line)
    # Drop trailing blank lines + lone page digits (keep mid-body axis "0"/"50")
    while kept:
        tail = kept[-1].strip()
        if not tail:
            kept.pop()
            continue
        if _TRAILING_PAGE_NUM.fullmatch(tail):
            kept.pop()
            continue
        break
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@dataclass
class QuestionChunk:
    question: str
    text: str
    start_line: int
    page_hint: int | None
    parts: list[str]
    options: list[str]
    paper_style: str  # "mcq" | "structured"
    parent_question: str | None = None
    part: str | None = None
    part_slug: str | None = None


def _page_map(text: str) -> list[tuple[int, int]]:
    return [(m.start(), int(m.group("page"))) for m in PAGE_RE.finditer(text)]


def _page_at(offset: int, pages: list[tuple[int, int]]) -> int | None:
    current: int | None = None
    for pos, page in pages:
        if pos <= offset:
            current = page
        else:
            break
    return current


def _match_num(match: re.Match[str]) -> int:
    raw = match.group("num") or match.group("num2")
    return int(raw)


def _is_plausible_main(
    match: re.Match[str],
    text: str,
    *,
    max_q: int,
    style: str | None = None,
) -> bool:
    num = _match_num(match)
    if num < 1 or num > max_q:
        return False

    line_end = text.find("\n", match.start())
    line = text[match.start() : line_end if line_end != -1 else match.start() + 160]
    # Number-only line (common in CIE MCQ PDFs)
    if re.fullmatch(r"\d{1,2}\s*[.)]?\s*", line):
        rest = text[line_end + 1 :] if line_end != -1 else ""
        for nxt in rest.splitlines():
            nxt = nxt.strip()
            if not nxt:
                continue
            if PAGE_RE.match(nxt) or FOOTER_NOISE.match(nxt):
                continue
            if SKIP_BODY.match(nxt):
                return False
            # Page numbers often sit alone before another lone number / footer
            if re.fullmatch(r"\d{1,2}\s*[.)]?\s*", nxt):
                return False
            # Real stems have words; reject pure option letters leftovers
            if re.fullmatch(r"[A-D]", nxt):
                return False
            if not re.search(r"[A-Za-z]{3,}", nxt):
                return False
            # Structured papers print the page number as a lone digit. Continuations
            # start with (b)/(c)/… or prose; real Qs are "N stem" on one line or
            # a lone N followed by (a).
            if style == "structured":
                if re.match(r"^\d{1,2}\s+\S", nxt):
                    return False  # next line is another main question
                # Part markers: "(a)" / "(a) (i)" — avoid \b after ")" (non-word)
                if re.match(r"^\(a\)(?:\s|$|\()", nxt, re.I):
                    return True
                if re.match(r"^\([b-z]\)(?:\s|$|\()", nxt, re.I):
                    return False  # mid-question continuation
                if re.match(r"^Answer\b", nxt, re.I):
                    return False
                return False
            return True
        return False

    body = re.sub(r"^\d{1,2}\s*[.)]?\s*", "", line).strip()
    if not body:
        return True
    # Front-matter words ("Information", "Instructions"…) only indicate boilerplate
    # when they are short fragments, not a full question stem. A real MCQ stem can
    # legitimately begin with these words (e.g. "Information about two substances…").
    if SKIP_BODY.match(body) and len(body.split()) <= 4 and len(body) < 60:
        return False
    if QA_NOTES_START.match(body):
        return False
    if not re.search(r"[A-Za-z]{3,}", body):
        return False
    # "1 hour" / "2 marks" style front-matter — reject unless stem-like.
    # CIE OCR sometimes glues a long stem into 1–3 tokens; accept those if long.
    if len(body.split()) <= 3 and not STEM_START.match(body) and len(body) < 40:
        return False
    return True

def detect_paper_style(text: str) -> str:
    if re.search(r"Paper\s*1\s*Multiple Choice|forty questions|multiple choice", text, re.I):
        return "mcq"
    # CIE 2023+ Paper 1 covers often use Identity-H fonts where
    # "Paper 1 Multiple Choice" extracts as shifted C0/ASCII (e.g. 3DSHU / 0XOWLSOH).
    if re.search(
        r"3DSHU[\x01\x03\s]*\x14[\x01\x03\s]*0XOWLSOH|0XOWLSOH[\x01\x03\s]*&KRLFH|"
        r"IRUW[\x01\x03\s]*TXHVWLRQV",  # "forty questions" shifted +3
        text,
        re.I,
    ):
        return "mcq"
    option_hits = len(OPTION_RE.findall(text))
    # Many 2023 MCQs put options inline ("A stem…") rather than lone "A" lines.
    inline_hits = len(re.findall(r"(?m)^[A-D]\s+\S", text))
    return "mcq" if max(option_hits, inline_hits) >= 40 else "structured"


def _select_question_matches(
    matches: list[re.Match[str]],
    text: str,
    *,
    style: str,
) -> list[re.Match[str]]:
    """Pick one match per question number in reading order."""
    if style != "mcq":
        selected: list[re.Match[str]] = []
        last_num = 0
        for m in matches:
            num = _match_num(m)
            if not selected:
                if num != 1:
                    continue
                selected.append(m)
                last_num = num
                continue
            if num == last_num + 1:
                selected.append(m)
                last_num = num
            elif num == 1 and last_num >= 3:
                selected.append(m)
                last_num = num
        return selected

    # MCQ: for each N in 1..40 take the first plausible match after the previous
    # hit. Tolerates statement-number false positives and small extract gaps.
    by_num: dict[int, list[re.Match[str]]] = {}
    for m in matches:
        by_num.setdefault(_match_num(m), []).append(m)

    selected = []
    last_pos = -1
    last_num = 0
    for num in range(1, 41):
        cands = [m for m in by_num.get(num, []) if m.start() > last_pos]
        if not cands:
            continue
        # Prefer stems that are not page-number+question merges ("5 9 Bromine…")
        def _score(m: re.Match[str]) -> tuple[int, int]:
            line_end = text.find("\n", m.start())
            line = text[m.start() : line_end if line_end != -1 else m.start() + 160]
            body = re.sub(r"^\d{1,2}\s*[.)]?\s*", "", line).strip()
            # A glued page number before a stem yields a SHORT body ("9 Bromine").
            # Long stems may legitimately begin with a digit ("1 mole of ..."),
            # so only treat short bodies as page-number false starts.
            if re.match(r"^\d{1,2}\s+[A-Za-z]", body) and len(body.split()) <= 3:
                return (2, m.start())  # page number false start
            if re.match(r"^BLANK\s+PAGE\b", body, re.I):
                return (3, m.start())
            if STEM_START.match(body) or len(body.split()) >= 4:
                return (0, m.start())
            return (1, m.start())

        cands.sort(key=_score)
        best = cands[0]
        if _score(best)[0] >= 2:
            continue
        # Allow a small gap (missed extract) but not huge jumps from false hits
        if selected and num > last_num + 3:
            # Still accept if this is the only remaining path forward
            pass
        selected.append(best)
        last_pos = best.start()
        last_num = num
    return selected


def split_questions(text: str, *, max_q: int | None = None) -> list[QuestionChunk]:
    """Split extracted paper text into question chunks."""
    style = detect_paper_style(text)
    if max_q is None:
        max_q = 40 if style == "mcq" else 20

    pages = _page_map(text)
    matches = [
        m
        for m in MAIN_Q_RE.finditer(text)
        if _is_plausible_main(m, text, max_q=max_q, style=style)
    ]
    if not matches:
        return []

    selected = _select_question_matches(matches, text, style=style)

    # Paper 3 end matter (Qualitative Analysis Notes + Periodic Table)
    qa_notes = re.search(
        r"(?im)^\s*Qualitative\s+analysis\s+notes\s*$",
        text,
    )
    paper_end = qa_notes.start() if qa_notes else len(text)

    chunks: list[QuestionChunk] = []
    for i, m in enumerate(selected):
        start = m.start()
        end = selected[i + 1].start() if i + 1 < len(selected) else paper_end
        end = min(end, paper_end)
        if start >= end:
            continue
        block = text[start:end].strip()
        block = re.sub(r"\n?----- PAGE \d+ -----\n?", "\n", block)
        block = strip_footer_noise(block)
        qnum = str(_match_num(m))
        parts = [p.group(0) for p in PART_RE.finditer(block)]
        options = OPTION_RE.findall(block)
        line_no = text.count("\n", 0, start) + 1
        chunks.append(
            QuestionChunk(
                question=qnum,
                text=block,
                start_line=line_no,
                page_hint=_page_at(start, pages),
                parts=parts,
                options=options,
                paper_style=style,
            )
        )
    return chunks


def parse_mcq_mark_scheme(text: str) -> dict[str, str]:
    """Parse Paper 1 MS key table into {question: answer_letter}."""
    answers: dict[str, str] = {}
    # Rows like: 1 C 1   or 12 B 1
    for m in re.finditer(
        r"(?m)^\s*(?P<q>\d{1,2})\s+(?P<ans>[A-D])\s+(?P<marks>\d+)\s*$",
        text,
    ):
        answers[m.group("q")] = m.group("ans")
    return answers


_MS_QUESTION_HEAD_RE = re.compile(
    r"(?m)^(?:Question\s+)?(?P<q>\d{1,2})(?:\s*[.)]|\s+(?=\([a-z]\)))",
    re.IGNORECASE,
)


def _ms_footer_question_nums(line: str, *, max_q: int) -> list[str]:
    """Question numbers listed on a CIE MS page footer line."""
    nums: list[str] = []
    for m in re.finditer(r"Question\s+(\d{1,2})\b", line, re.I):
        n = int(m.group(1))
        if 1 <= n <= max_q:
            q = str(n)
            if q not in nums:
                nums.append(q)
    return nums


def _ms_content_from_last_page(content: str) -> str:
    """Keep only the last PAGE block (drops generic marking principles)."""
    pages = list(PAGE_RE.finditer(content))
    if pages:
        content = content[pages[-1].end() :]
    content = re.sub(r"\n?----- PAGE \d+ -----\n?", "\n", content)
    return strip_footer_noise(content.strip())


def parse_structured_mark_scheme(text: str, *, max_q: int = 20) -> dict[str, str]:
    """Split Paper 2/4 (structured) MS into {question: mark_scheme_block}.

    Keeps (a)/(b)/(i) parts inside each main-question block. Best-effort:
    CIE layouts vary; empty dict means caller should bind MS manually.

    Two layouts are supported:
    - Header style: ``Question 1`` then answers (fixture / clean extracts)
    - Footer style: answers then ``Question 1(a)(i) 1(a)(ii)…`` (CIE table PDFs)
    """
    text = text or ""
    footer_lines = list(
        re.finditer(r"(?m)^(?P<line>Question\s+\d{1,2}\b.*)$", text, re.IGNORECASE)
    )
    # Footer layout: a line lists parts for the preceding page block, often with
    # multiple "Question N" tokens (e.g. "Question 2(d) Question 3(a)(i)…").
    footer_style = any(
        len(_ms_footer_question_nums(m.group("line"), max_q=max_q)) >= 1
        and (
            "(" in m.group("line")
            or len(_ms_footer_question_nums(m.group("line"), max_q=max_q)) > 1
        )
        for m in footer_lines
    )
    if footer_style and footer_lines:
        parts: dict[str, list[str]] = {}
        prev = 0
        for m in footer_lines:
            chunk = _ms_content_from_last_page(text[prev : m.start()])
            qnums = _ms_footer_question_nums(m.group("line"), max_q=max_q)
            if chunk and qnums:
                # Drop generic-principle pages mistakenly kept
                if re.search(r"GENERIC MARKING PRINCIPLE", chunk, re.I):
                    chunk = ""
                if chunk:
                    for q in qnums:
                        parts.setdefault(q, []).append(chunk)
            prev = m.end()
        if parts:
            return {q: "\n\n".join(v).strip() for q, v in parts.items() if v}

    # Prefer explicit "Question N" headings when present
    heads = list(
        re.finditer(r"(?m)^(?:Question\s+)(?P<q>\d{1,2})\b", text, re.IGNORECASE)
    )
    if not heads:
        # Fallback: lines that start a main Q then a part letter, e.g. "1 (a)" / "2."
        candidates: list[re.Match[str]] = []
        last = 0
        for m in _MS_QUESTION_HEAD_RE.finditer(text):
            num = int(m.group("q"))
            if num < 1 or num > max_q:
                continue
            if not candidates:
                if num != 1:
                    continue
                candidates.append(m)
                last = num
                continue
            if num == last + 1:
                candidates.append(m)
                last = num
        heads = candidates

    blocks: dict[str, str] = {}
    for i, m in enumerate(heads):
        q = m.group("q")
        # Normalize "Question 1" → start after the heading line when possible
        start = m.start()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        block = text[start:end].strip()
        block = re.sub(r"\n?----- PAGE \d+ -----\n?", "\n", block)
        block = strip_footer_noise(block)
        if block:
            blocks[str(int(q))] = block
    return blocks


def expand_structured_part_chunks(chunks: list[QuestionChunk]) -> list[QuestionChunk]:
    """Turn main-question chunks into one chunk per smallest part."""
    from chembank.structured_parts import split_main_question_into_parts

    out: list[QuestionChunk] = []
    for chunk in chunks:
        if chunk.paper_style == "mcq":
            out.append(chunk)
            continue
        parts = split_main_question_into_parts(
            chunk.question,
            chunk.text,
            start_line=chunk.start_line,
            page_hint=chunk.page_hint,
        )
        if not parts:
            out.append(chunk)
            continue
        for pid, body in parts:
            out.append(
                QuestionChunk(
                    question=pid.label,
                    text=body,
                    start_line=chunk.start_line,
                    page_hint=chunk.page_hint,
                    parts=[pid.part],
                    options=[],
                    paper_style="structured",
                    parent_question=pid.parent,
                    part=pid.part,
                    part_slug=pid.slug,
                )
            )
    return out


def write_split_output(
    text: str,
    out_dir: Path,
    *,
    source_name: str = "paper",
    mark_scheme_text: str | None = None,
    part_level: bool | None = None,
) -> list[QuestionChunk]:
    """Write one .txt per question (MCQ) or per part (structured) plus index.json.

    Structured papers default to **part-level** drafts (``q2a-i.txt``). Pass
    ``part_level=False`` to keep one file per main question.
    """
    from chembank.structured_parts import (
        aggregate_ms_by_parent,
        is_garbage_ms_text,
        parse_structured_ms_parts,
    )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks = split_questions(text)
    style = chunks[0].paper_style if chunks else detect_paper_style(text)
    if part_level is None:
        part_level = style != "mcq"
    if part_level and style != "mcq":
        chunks = expand_structured_part_chunks(chunks)

    ms_key: dict[str, str] = {}
    ms_structured: dict[str, str] = {}
    ms_parts: dict[str, str] = {}
    if mark_scheme_text:
        if style == "mcq":
            ms_key = parse_mcq_mark_scheme(mark_scheme_text)
        else:
            ms_parts = parse_structured_ms_parts(mark_scheme_text)
            if ms_parts:
                ms_structured = aggregate_ms_by_parent(ms_parts)
            else:
                ms_structured = parse_structured_mark_scheme(mark_scheme_text)

    # Remove stale main-Q drafts when rewriting as parts
    if part_level and style != "mcq":
        for old in out_dir.glob("q*.txt"):
            old.unlink(missing_ok=True)

    index: list[dict] = []
    for chunk in chunks:
        filename = (
            f"q{chunk.part_slug}.txt"
            if chunk.part_slug
            else f"q{chunk.question}.txt"
        )

        body = chunk.text
        ms_answer = ms_key.get(chunk.question) if style == "mcq" else None
        if style == "mcq" and chunk.question in ms_key:
            body = body + f"\n\n--- MARK SCHEME ---\nAnswer: {ms_key[chunk.question]}\n"
        elif style != "mcq":
            ms_block = ""
            if chunk.question in ms_parts:
                ms_block = ms_parts[chunk.question]
            elif (
                not chunk.part_slug
                and chunk.question in ms_structured
            ):
                # Main-question grain (Paper 3 practical): rolled-up MS
                ms_block = ms_structured[chunk.question]
            elif chunk.parent_question and chunk.parent_question in ms_structured:
                # Fallback: do not attach whole-Q salad to a part
                ms_block = ""
            if ms_block and not is_garbage_ms_text(ms_block):
                body = body + "\n\n--- MARK SCHEME ---\n" + ms_block.rstrip() + "\n"
            elif ms_block:
                # Keep a tiny pointer; image export is authoritative
                body = (
                    body
                    + "\n\n--- MARK SCHEME ---\n"
                    + f"[see MS screenshot for {chunk.question}]\n"
                )
        (out_dir / filename).write_text(body + "\n", encoding="utf-8")
        meta = asdict(chunk)
        meta["file"] = filename
        meta["source"] = source_name
        meta["ms_answer"] = ms_answer
        meta["has_mark_scheme"] = bool(
            (style == "mcq" and chunk.question in ms_key)
            or (style != "mcq" and chunk.question in ms_parts)
            or (
                style != "mcq"
                and not chunk.part_slug
                and chunk.question in ms_structured
            )
        )
        meta.pop("text", None)
        index.append(meta)

    (out_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if ms_key:
        (out_dir / "ms_key.json").write_text(
            json.dumps(ms_key, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if ms_structured:
        (out_dir / "ms_structured.json").write_text(
            json.dumps(ms_structured, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if ms_parts:
        (out_dir / "ms_parts.json").write_text(
            json.dumps(ms_parts, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return chunks
