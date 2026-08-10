"""Extract CIE Principal Examiner Report (ER) stats/comments for ChemBank.

CIE Paper 1 ERs typically give **qualitative** difficulty bands and per-question
comments — not numeric facility / % correct. Never invent statistics.

Difficulty mapping (qualitative → ChemBank 1–5), only when the report says so:

| ER wording                         | `examiner_band`           | `difficulty` |
|------------------------------------|---------------------------|--------------|
| found to be easy                   | easy                      | 2            |
| found to be particularly difficult | particularly_difficult    | 5            |
| (no band mentioned)                | null                      | leave as-is  |

ER data is **year/session/paper scoped**. A 2021 report must not be treated as
universal difficulty for the same LO in other years.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from chembank.extract import extract_pdf_text

# Qualitative band → ChemBank difficulty (1–5). Documented; not invented %.
DIFFICULTY_FROM_BAND: dict[str, int] = {
    "easy": 2,
    "particularly_difficult": 5,
}

HEADER_NOISE = re.compile(
    r"(?:Cambridge International Advanced Subsidiary and Advanced Level|"
    r"9701 Chemistry (?:June|November|March) \d{4}|"
    r"Principal Examiner Report for Teachers|"
    r"©\s*\d{4})\s*",
    re.IGNORECASE,
)

PAPER_START = re.compile(
    r"Paper\s+9701/(?P<paper>\d+)\s*\n\s*(?P<title>[^\n]+)?",
    re.IGNORECASE,
)

# PDF extract often glues tokens: "and23were", "Questions14", "wasC"
EASY_RE = re.compile(
    r"Questions?\s*([0-9,\s]+(?:and\s*\d+)?)\s*were\s+found\s+to\s+be\s+easy",
    re.IGNORECASE,
)
HARD_RE = re.compile(
    r"Questions?\s*([0-9,\s]+(?:and\s*\d+)?)\s*were\s+found\s+to\s+be\s+"
    r"(?:particularly\s+)?difficult",
    re.IGNORECASE,
)

Q_COMMENT_SPLIT = re.compile(r"(?=Question\s+(\d+)\b)", re.IGNORECASE)
COMMON_WRONG = re.compile(
    r"most commonly chosen incorrect answer was\s*([A-D])",
    re.IGNORECASE,
)
SESSION_RE = re.compile(
    r"9701\s+Chemistry\s+(June|November|March)\s+(\d{4})",
    re.IGNORECASE,
)


def _session_code(month: str) -> str:
    m = month.strip().lower()
    if m == "june":
        return "MJ"
    if m == "november":
        return "ON"
    if m == "march":
        return "FM"
    return month.upper()[:2]


def _cie_season_token(session: str, year: int) -> str:
    """Map MJ/ON/FM + year → CIE filename token, e.g. s21 / w21 / m21."""
    yy = year % 100
    s = session.upper()
    if s == "MJ":
        return f"s{yy:02d}"
    if s == "ON":
        return f"w{yy:02d}"
    if s == "FM":
        return f"m{yy:02d}"
    return f"x{yy:02d}"


def _parse_question_list(blob: str) -> list[int]:
    """Parse '7, 8, 18 and 23' or glued '7, 8, 18 and23' → [7, 8, 18, 23]."""
    cleaned = re.sub(r"\band\b", ",", blob, flags=re.IGNORECASE)
    # Pull every integer token (handles residual glue)
    return [int(x) for x in re.findall(r"\d{1,2}", cleaned)]


def _unglue_pdf_tokens(text: str) -> str:
    """Insert spaces where PDF extract glued tokens (and23, wasC, outC)."""
    text = re.sub(r"([0-9])([A-Za-z])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", text)
    # MCQ option letters glued to prior word: wasC / outC / isA
    text = re.sub(r"([a-z])([A-D])\b", r"\1 \2", text)
    return text


def _clean_block(text: str) -> str:
    text = HEADER_NOISE.sub(" ", text)
    text = _unglue_pdf_tokens(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _extract_answer_key(section: str) -> dict[str, str]:
    """Parse MCQ key table: Question Number / Key columns."""
    # After normalizing whitespace, look for "N X" pairs in the key region
    # Prefer the block before "General comments".
    head = section
    gc = re.search(r"General comments", section, re.IGNORECASE)
    if gc:
        head = section[: gc.start()]
    # Collapse to lines; keys appear as standalone number then letter lines
    # or "N\nX" patterns. Also handle "1 C 11 C ..." after whitespace collapse.
    flat = re.sub(r"[ \t]+", " ", head)
    flat = re.sub(r"\n+", "\n", flat)
    # Capture sequences like "1\nC" or "1 C"
    pairs = re.findall(
        r"(?:^|\n|\s)(\d{1,2})\s*\n?\s*([A-D])(?=\s|\n|$)",
        flat,
    )
    key: dict[str, str] = {}
    for n, letter in pairs:
        qn = int(n)
        if 1 <= qn <= 40 and str(qn) not in key:
            key[str(qn)] = letter.upper()
    return key


def _extract_general_comments(section: str) -> str:
    m = re.search(
        r"General comments\s*(.*?)\s*(?:Comments on specific questions|$)",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return ""
    return _clean_block(m.group(1))


def _extract_question_comments(section: str) -> dict[str, dict[str, Any]]:
    m = re.search(
        r"Comments on specific questions\s*(.*)$",
        section,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return {}
    body = m.group(1)
    parts = Q_COMMENT_SPLIT.split(body)
    # split yields: preamble, qnum, text, qnum, text, ...
    out: dict[str, dict[str, Any]] = {}
    i = 1
    while i + 1 < len(parts):
        qnum = parts[i].strip()
        text = parts[i + 1]
        # Lookahead split leaves "Question N" at the start of the chunk
        text = re.sub(
            rf"^Question\s+{re.escape(qnum)}\s*",
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        text = _clean_block(text)
        # Drop trailing next-paper / page bleed if any
        text = re.split(r"\nCHEMISTRY\s*\n", text, maxsplit=1)[0].strip()
        text = re.split(r"\nPaper\s+9701/\d+", text, maxsplit=1)[0].strip()
        text = re.split(r"\n----- PAGE \d+ -----", text, maxsplit=1)[0].strip()
        if not qnum.isdigit() or not text:
            i += 2
            continue
        wrong = None
        wm = COMMON_WRONG.search(text)
        if wm:
            wrong = wm.group(1).upper()
        common_errors: list[str] = []
        if wrong:
            common_errors.append(
                f"Most commonly chosen incorrect answer was {wrong}."
            )
        out[qnum] = {
            "examiner_notes": text,
            "common_incorrect": wrong,
            "common_errors": common_errors,
            "facility": None,
            "percent_correct": None,
            "discrimination": None,
        }
        i += 2
    return out


def _split_paper_sections(full_text: str) -> list[tuple[str, str, str]]:
    """Return list of (paper, title, section_text)."""
    matches = list(PAPER_START.finditer(full_text))
    sections: list[tuple[str, str, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        paper = m.group("paper")
        title = (m.group("title") or "").strip()
        sections.append((paper, title, full_text[start:end]))
    return sections


def parse_examiner_report_text(text: str, *, source_name: str = "") -> dict[str, Any]:
    """Parse full ER PDF text into structured year-scoped report data."""
    sm = SESSION_RE.search(text)
    if not sm:
        raise ValueError(
            "Could not detect session/year header "
            "(expected e.g. '9701 Chemistry June 2021')"
        )
    session = _session_code(sm.group(1))
    year = int(sm.group(2))
    season = _cie_season_token(session, year)

    papers_out: dict[str, Any] = {}
    for paper, title, section in _split_paper_sections(text):
        general = _extract_general_comments(section)
        easy: list[int] = []
        hard: list[int] = []
        for em in EASY_RE.finditer(general):
            easy.extend(_parse_question_list(em.group(1)))
        for hm in HARD_RE.finditer(general):
            hard.extend(_parse_question_list(hm.group(1)))
        # Deduplicate preserving order
        easy = list(dict.fromkeys(easy))
        hard = list(dict.fromkeys(hard))

        comments = _extract_question_comments(section)
        answer_key = _extract_answer_key(section)

        # Build per-question records for every mentioned q + answer key
        qnums = sorted(
            {
                *map(str, easy),
                *map(str, hard),
                *comments.keys(),
                *answer_key.keys(),
            },
            key=lambda x: int(x),
        )
        questions: dict[str, Any] = {}
        for qn in qnums:
            band = None
            if int(qn) in hard:
                band = "particularly_difficult"
            elif int(qn) in easy:
                band = "easy"
            c = comments.get(qn, {})
            difficulty = DIFFICULTY_FROM_BAND.get(band) if band else None
            questions[qn] = {
                "question": qn,
                "er_year": year,
                "er_session": session,
                "er_paper": int(paper) if paper.isdigit() else paper,
                "facility": c.get("facility"),
                "percent_correct": c.get("percent_correct"),
                "discrimination": c.get("discrimination"),
                "examiner_band": band,
                "difficulty": difficulty,
                "difficulty_source": (
                    "examiner_report_qualitative" if difficulty is not None else None
                ),
                "ms_key": answer_key.get(qn),
                "common_incorrect": c.get("common_incorrect"),
                "common_errors": c.get("common_errors") or [],
                "examiner_notes": c.get("examiner_notes"),
            }

        papers_out[paper] = {
            "paper": int(paper) if paper.isdigit() else paper,
            "title": title,
            "er_year": year,
            "er_session": session,
            "general_comments": general,
            "easy_questions": easy,
            "difficult_questions": hard,
            "answer_key": answer_key,
            "questions": questions,
            "stats": {
                "questions_with_numeric_facility": sum(
                    1
                    for q in questions.values()
                    if q.get("facility") is not None
                    or q.get("percent_correct") is not None
                ),
                "questions_with_comments": sum(
                    1 for q in questions.values() if q.get("examiner_notes")
                ),
                "questions_with_band_only": sum(
                    1
                    for q in questions.values()
                    if q.get("examiner_band") and not q.get("examiner_notes")
                ),
                "questions_total_in_key": len(answer_key),
            },
        }

    return {
        "exam_board": "CIE",
        "syllabus_code": "9701",
        "year": year,
        "session": session,
        "season_token": season,
        "report_title": f"9701 Chemistry {year} Principal Examiner Report",
        "source": source_name,
        "has_numeric_facility": False,  # CIE ER PDFs usually qualitative only
        "difficulty_mapping": {
            "easy": DIFFICULTY_FROM_BAND["easy"],
            "particularly_difficult": DIFFICULTY_FROM_BAND["particularly_difficult"],
            "note": (
                "No numeric facility/% correct in this ER. "
                "difficulty is mapped only from qualitative bands; "
                "scoped to this year/session/paper — not universal LO difficulty."
            ),
        },
        "papers": papers_out,
    }


def extract_examiner_report(
    pdf: Path,
    *,
    paper: str | int | None = None,
) -> dict[str, Any]:
    """Extract ER from PDF; optionally filter to one paper variant."""
    pdf = Path(pdf)
    text = extract_pdf_text(pdf)
    data = parse_examiner_report_text(text, source_name=pdf.name)
    if paper is not None:
        p = str(paper)
        if p not in data["papers"]:
            raise KeyError(
                f"Paper {p} not in ER; available: {sorted(data['papers'], key=int)}"
            )
        data = {
            **data,
            "papers": {p: data["papers"][p]},
            "filtered_paper": p,
        }
    return data


def er_json_path(year: int, session: str, paper: str | int) -> Path:
    """Year-scoped draft path, e.g. draft/er/9701_s21_er_11.json."""
    season = _cie_season_token(session, year)
    return Path("draft") / "er" / f"9701_{season}_er_{paper}.json"


def suggested_pdf_name(year: int, session: str) -> str:
    """Clean gitignored name under raw/reports/, e.g. 9701_2021_s21_er.pdf."""
    season = _cie_season_token(session, year)
    return f"9701_{year}_{season}_er.pdf"


def write_examiner_report_json(
    data: dict[str, Any],
    out_path: Path | None = None,
    *,
    paper: str | int | None = None,
) -> Path:
    """Write structured ER JSON under draft/er/ (year-scoped)."""
    year = int(data["year"])
    session = str(data["session"])
    if paper is None:
        papers = list(data["papers"].keys())
        if len(papers) == 1:
            paper = papers[0]
        else:
            # Multi-paper dump
            season = data.get("season_token") or _cie_season_token(session, year)
            out_path = Path(out_path) if out_path else Path("draft") / "er" / f"9701_{season}_er.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return out_path
    out_path = Path(out_path) if out_path else er_json_path(year, session, paper)
    # If multi-paper data but writing one paper file, slice
    payload = data
    p = str(paper)
    if p in data.get("papers", {}) and (
        len(data["papers"]) > 1 or data.get("filtered_paper") != p
    ):
        payload = {**data, "papers": {p: data["papers"][p]}, "filtered_paper": p}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def question_er_fields(
    er_q: dict[str, Any],
    *,
    source_path: str,
) -> dict[str, Any]:
    """Map one ER question record → fields to merge onto a ChemBank question."""
    return {
        "examiner_report_source": source_path,
        "examiner_report": {
            "year": er_q.get("er_year"),
            "session": er_q.get("er_session"),
            "paper": er_q.get("er_paper"),
            "source": source_path,
        },
        "er_year": er_q.get("er_year"),
        "er_session": er_q.get("er_session"),
        "er_paper": er_q.get("er_paper"),
        "facility": er_q.get("facility"),
        "percent_correct": er_q.get("percent_correct"),
        "discrimination": er_q.get("discrimination"),
        "examiner_band": er_q.get("examiner_band"),
        "difficulty_source": er_q.get("difficulty_source"),
        "common_incorrect": er_q.get("common_incorrect"),
        "common_errors": list(er_q.get("common_errors") or []),
        "examiner_notes": er_q.get("examiner_notes"),
    }


def merge_er_into_question(
    question: dict[str, Any],
    er_q: dict[str, Any],
    *,
    source_path: str,
    update_difficulty: bool = True,
) -> dict[str, Any]:
    """Merge ER fields into a tagged question dict (year-scoped; no inventing)."""
    out = dict(question)
    fields = question_er_fields(er_q, source_path=source_path)
    for k, v in fields.items():
        if v is None and k in (
            "facility",
            "percent_correct",
            "discrimination",
            "examiner_notes",
            "examiner_band",
            "difficulty_source",
            "common_incorrect",
        ):
            # Keep explicit nulls only for numeric slots; skip empty notes
            if k in ("facility", "percent_correct", "discrimination"):
                out[k] = None
            continue
        out[k] = v

    if update_difficulty and er_q.get("difficulty") is not None:
        out["difficulty"] = er_q["difficulty"]
        out["difficulty_source"] = er_q.get(
            "difficulty_source", "examiner_report_qualitative"
        )

    # Enrich misconceptions from common incorrect (do not wipe existing)
    misc = list(out.get("misconceptions") or [])
    for err in fields.get("common_errors") or []:
        if err and err not in misc:
            misc.append(err)
    if er_q.get("common_incorrect"):
        tip = f"Common wrong option: {er_q['common_incorrect']}"
        if tip not in misc:
            misc.append(tip)
    out["misconceptions"] = misc
    return out


def merge_er_into_tagged_dir(
    tagged_dir: Path,
    er_data: dict[str, Any],
    *,
    paper: str | int | None = None,
    source_path: str | None = None,
    update_difficulty: bool = True,
) -> list[Path]:
    """Merge ER into draft/.../tagged/qN.json files. Returns updated paths."""
    tagged_dir = Path(tagged_dir)
    papers = er_data["papers"]
    if paper is not None:
        p = str(paper)
    elif len(papers) == 1:
        p = next(iter(papers))
    else:
        raise ValueError("Multiple papers in ER data; pass paper= explicitly")
    paper_block = papers[p]
    questions = paper_block["questions"]
    src = source_path or er_data.get("source") or ""

    updated: list[Path] = []
    from chembank.structured_parts import draft_stem_sort_key

    for path in sorted(tagged_dir.glob("q*.json"), key=lambda x: draft_stem_sort_key(x.stem)):
        data = json.loads(path.read_text(encoding="utf-8"))
        qn = str(
            data.get("parent_question")
            or data.get("question")
            or path.stem[1:]
        )
        # Part notes: ER is keyed by main question number
        if "(" in qn:
            qn = qn.split("(", 1)[0]
        er_q = questions.get(qn)
        if not er_q:
            # No ER mention — leave facility/notes empty; do not invent
            data.setdefault("facility", None)
            data.setdefault("percent_correct", None)
            data.setdefault("er_year", er_data.get("year"))
            data.setdefault("er_session", er_data.get("session"))
            data.setdefault("er_paper", paper_block.get("paper"))
            data.setdefault(
                "examiner_report_source",
                src or None,
            )
            data.setdefault(
                "examiner_report",
                {
                    "year": er_data.get("year"),
                    "session": er_data.get("session"),
                    "paper": paper_block.get("paper"),
                    "source": src or None,
                },
            )
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            updated.append(path)
            continue
        merged = merge_er_into_question(
            data, er_q, source_path=src, update_difficulty=update_difficulty
        )
        path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        updated.append(path)
    return updated
