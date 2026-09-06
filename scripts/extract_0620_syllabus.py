#!/usr/bin/env python3
"""Extract CIE 0620 (IGCSE Chemistry 2026–2028) Core/Supplement LOs into YAML.

Source PDF (official 59-page booklet):
  QLS copy: 697205-2026-2028-syllabus-2.pdf
  optional: raw/papers/0620_syllabus_2026-2028.pdf

Id scheme (stable, traces to printed numbering):
  {subtopic}-C{n}   Core column, official number n     e.g. 1.1-C1
  {subtopic}-S{n}   Supplement column, official number n e.g. 1.1-S5

Within a subtopic Core and Supplement share one printed number sequence
(Core 1–4 then Supplement 5–6 on 1.1). Letter parts (a)(b) are folded into
the parent LO text — they are not separate leaf ids.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = Path(
    "/Users/tsinglan-school/Desktop/QLS/Qingyun/Text Books/"
    "697205-2026-2028-syllabus-2.pdf"
)
LOCAL_PDF = ROOT / "raw" / "papers" / "0620_syllabus_2026-2028.pdf"
DEFAULT_YAML = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

PAGE_START = 12  # 1-indexed "3 Subject content"
PAGE_END = 39  # last subject-content page (12.5 Identification of ions…)

COL_SPLIT = 295.0  # Supplement column starts ~309pt

SKIP_EXACT = {
    "Core",
    "Supplement",
    "Subject content",
    "3 Subject content",
    "Learning outcomes",
    "Candidates should be able to:",
}
SKIP_PREFIX = (
    "Cambridge IGCSE",
    "www.cambridge",
    "Back to contents page",
    "This syllabus gives",
    "Where appropriate",
    "All candidates should",
    "Scientific subjects",
    "Practical work helps",
    "Candidates aiming",
    "The Extended subject",
)

TOPIC_TITLES = {
    "1": "States of matter",
    "2": "Atoms, elements and compounds",
    "3": "Stoichiometry",
    "4": "Electrochemistry",
    "5": "Chemical energetics",
    "6": "Chemical reactions",
    "7": "Acids, bases and salts",
    "8": "The Periodic Table",
    "9": "Metals",
    "10": "Chemistry of the environment",
    "11": "Organic chemistry",
    "12": "Experimental techniques and chemical analysis",
}

SUB_RE = re.compile(r"^(\d{1,2}\.\d{1,2})\s+(.*)$")
TOPIC_NUM_RE = re.compile(r"^(\d{1,2})$")
TOPIC_INLINE_RE = re.compile(r"^(\d{1,2})\s+(.+)$")
LO_NUM_RE = re.compile(r"^(\d{1,2})$")
LO_INLINE_RE = re.compile(r"^(\d{1,2})\s+(.+)$")
LETTER_RE = re.compile(r"^\(([a-z])\)\s*(.*)$", re.I)
# Polymer / displayed-formula OCR crumbs from structure diagrams
DIAGRAM_CRUMB_RE = re.compile(r"^[A-Z][a-z]?$")


def clean(s: str) -> str:
    s = s.replace("\u00a0", " ").replace("\t", " ")
    s = s.replace("\u2009", " ").replace("\u200a", " ").replace("\u202f", " ")
    s = s.replace("\ufeff", "").replace("\u00ad", "")
    s = s.replace("\u2011", "-").replace("\u2013", "–").replace("\u2014", "—")
    s = re.sub(r"[\ue000-\uf8ff]", "", s)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def resolve_pdf(path: Path | None) -> Path:
    if path and path.is_file():
        return path
    if LOCAL_PDF.is_file():
        return LOCAL_PDF
    if DEFAULT_PDF.is_file():
        return DEFAULT_PDF
    raise FileNotFoundError(
        f"0620 syllabus PDF not found. Tried {LOCAL_PDF} and {DEFAULT_PDF}"
    )


def extract_lines(pdf_path: Path) -> list[dict[str, Any]]:
    import fitz

    pdf = fitz.open(pdf_path)
    lines: list[dict[str, Any]] = []
    for i in range(PAGE_START - 1, PAGE_END):
        page = pdf[i]
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                text = clean("".join(span["text"] for span in line["spans"]))
                if not text:
                    continue
                x0, y0, x1, y1 = line["bbox"]
                if text.startswith("Cambridge IGCSE") or text.startswith("www.cambridge"):
                    continue
                if text == "Back to contents page":
                    continue
                if re.fullmatch(r"\d{1,3}", text) and x0 > 500:
                    continue
                lines.append(
                    {
                        "page": i + 1,
                        "x": round(x0, 1),
                        "x1": round(x1, 1),
                        "y": round(y0, 1),
                        "text": text,
                    }
                )
    pdf.close()
    return lines


def _is_header(text: str) -> bool:
    t = text.replace("\u2003", " ").replace(" ", " ").strip()
    t = re.sub(r"\s+", " ", t)
    if t in SKIP_EXACT or t in {"3 Subject content"}:
        return True
    if any(t.startswith(p) for p in SKIP_PREFIX):
        return True
    if t.startswith("3 ") and "Subject content" in t:
        return True
    if t.startswith("•"):
        return True
    return False


def parse_subject_content(lines: list[dict[str, Any]]) -> dict[str, Any]:
    """Build {topic: {title, subtopics: {code: {title, core:[], supp:[]}}}}."""
    topics: dict[str, dict[str, Any]] = {
        k: {"title": v, "subtopics": {}} for k, v in TOPIC_TITLES.items()
    }
    current_topic: str | None = None
    current_sub: str | None = None
    current_lo: dict[str, Any] | None = None
    current_col: str | None = None  # "C" or "S"

    def ensure_sub(code: str, title: str) -> None:
        nonlocal current_topic, current_sub, current_lo, current_col
        major = code.split(".")[0]
        current_topic = major
        current_sub = code
        current_lo = None
        current_col = None
        bucket = topics[major]["subtopics"]
        title = re.sub(r"\s*\(continued\)\s*$", "", title, flags=re.I).strip()
        if code not in bucket:
            bucket[code] = {"title": title, "los": []}
        elif title and not bucket[code]["title"]:
            bucket[code]["title"] = title

    def start_lo(col: str, num: str) -> None:
        nonlocal current_lo, current_col
        if not current_sub:
            return
        current_col = col
        lo = {
            "id": f"{current_sub}-{col}{num}",
            "column": col,
            "num": int(num),
            "text": "",
        }
        topics[current_sub.split(".")[0]]["subtopics"][current_sub]["los"].append(lo)
        current_lo = lo

    def append_text(text: str) -> None:
        if not current_lo:
            return
        text = clean(text)
        if not text:
            return
        current_lo["text"] = clean(f"{current_lo['text']} {text}")

    i = 0
    n = len(lines)
    while i < n:
        t = lines[i]["text"]
        x = lines[i]["x"]
        if _is_header(t):
            i += 1
            continue

        # Subtopic "1.1 Solids, liquids and gases" (left column only)
        m = SUB_RE.match(t)
        if x < 120 and m:
            ensure_sub(m.group(1), clean(m.group(2)))
            i += 1
            continue

        # Topic heading: "11 Organic chemistry" (tab-separated) or "1" + title
        m_inline_topic = TOPIC_INLINE_RE.match(t)
        if x < 90 and m_inline_topic and m_inline_topic.group(1) in TOPIC_TITLES:
            rest = clean(m_inline_topic.group(2))
            expected = TOPIC_TITLES[m_inline_topic.group(1)]
            if rest.lower().startswith(expected.split()[0].lower()) or rest == expected:
                current_topic = m_inline_topic.group(1)
                current_sub = None
                current_lo = None
                current_col = None
                i += 1
                continue

        m = TOPIC_NUM_RE.fullmatch(t)
        if m and x < 75 and m.group(1) in TOPIC_TITLES:
            nxt_title = None
            if i + 1 < n and 80 <= lines[i + 1]["x"] < 200:
                cand = lines[i + 1]["text"]
                expected = TOPIC_TITLES[m.group(1)]
                if cand.lower().startswith(expected.split()[0].lower()) or cand == expected:
                    nxt_title = cand
            if nxt_title:
                current_topic = m.group(1)
                current_sub = None
                current_lo = None
                current_col = None
                i += 2
                continue
            # Core LO number (lone digit)
            if current_sub:
                start_lo("C", m.group(1))
            i += 1
            continue

        # Supplement LO: lone "8" or inline "10 Describe and draw…"
        if x >= 300:
            m_inline = LO_INLINE_RE.match(t)
            m_lone = LO_NUM_RE.fullmatch(t)
            if m_lone and x < 325:
                start_lo("S", m_lone.group(1))
                i += 1
                continue
            if m_inline and x < 340:
                start_lo("S", m_inline.group(1))
                rest = clean(m_inline.group(2))
                if rest:
                    append_text(rest)
                i += 1
                continue

        # Core LO number that wasn't a topic
        m = LO_NUM_RE.fullmatch(t)
        if m and x < 75 and current_sub:
            start_lo("C", m.group(1))
            i += 1
            continue
        m_core_inline = LO_INLINE_RE.match(t)
        if m_core_inline and x < 75 and current_sub:
            start_lo("C", m_core_inline.group(1))
            rest = clean(m_core_inline.group(2))
            if rest and not SUB_RE.match(t):
                append_text(rest)
            i += 1
            continue

        # Body text
        if current_lo:
            same_col = (
                (current_lo["column"] == "C" and x < COL_SPLIT)
                or (current_lo["column"] == "S" and x >= COL_SPLIT)
            )
            if same_col:
                if x < 120 and SUB_RE.match(t):
                    i += 1
                    continue
                if DIAGRAM_CRUMB_RE.fullmatch(t):
                    i += 1
                    continue
                append_text(t)
                i += 1
                continue

        i += 1

    return topics


def to_yaml_doc(topics: dict[str, Any], source_name: str) -> dict[str, Any]:
    out_topics = []
    n_sub = 0
    n_lo = 0
    empty = []
    for code in sorted(topics, key=lambda c: int(c)):
        t = topics[code]
        subs = []
        for sc in sorted(t["subtopics"], key=lambda c: tuple(int(x) for x in c.split("."))):
            sub = t["subtopics"][sc]
            los = []
            ordered = sorted(sub["los"], key=lambda lo: (0 if lo["column"] == "C" else 1, lo["num"]))
            seen: set[str] = set()
            for lo in ordered:
                text = clean(lo["text"])
                if not text or lo["id"] in seen:
                    continue
                seen.add(lo["id"])
                los.append(
                    {
                        "id": lo["id"],
                        "text": text,
                        "level": "Core" if lo["column"] == "C" else "Supplement",
                    }
                )
            n_sub += 1
            n_lo += len(los)
            if not los:
                empty.append(sc)
            subs.append(
                {
                    "code": sc,
                    "title": sub["title"],
                    "learning_outcomes": los,
                }
            )
        out_topics.append(
            {
                "code": code,
                "title": t["title"],
                "level": "IGCSE",
                "subtopics": subs,
            }
        )
    doc = {
        "meta": {
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "IGCSE",
            "title": "Cambridge IGCSE Chemistry",
            "syllabus_years": "2026-2028",
            "source_pdf": source_name,
            "note": (
                "Codes follow official Subject content numbering. "
                "Leaf learning_outcomes use {subtopic}-C{n} (Core) or {subtopic}-S{n} "
                "(Supplement), where n is the printed number in that column. "
                "Extended papers (P2/P4/P6) may tag Core and Supplement LOs. "
                "Parent syllabus_codes are topic (1) or subtopic (1.1). "
                "Never invent codes; never reuse 9701 ids."
            ),
        },
        "topics": out_topics,
    }
    return doc, {"subtopics": n_sub, "los": n_lo, "empty": empty}


class _IndentDumper(yaml.SafeDumper):
    pass


def _str_representer(dumper: yaml.Dumper, data: str):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    if re.fullmatch(r"\d+(\.\d+)?", data) or re.fullmatch(
        r"\d+(\.\d+)?-[CS]\d+", data
    ):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_IndentDumper.add_representer(str, _str_representer)


def dump_yaml(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            Dumper=_IndentDumper,
            allow_unicode=True,
            sort_keys=False,
            width=100,
            indent=2,
        )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf", type=Path, help="Syllabus PDF path")
    p.add_argument("--yaml", type=Path, default=DEFAULT_YAML)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    pdf_path = resolve_pdf(args.pdf)
    lines = extract_lines(pdf_path)
    topics = parse_subject_content(lines)
    doc, stats = to_yaml_doc(topics, pdf_path.name)
    print(f"PDF: {pdf_path}")
    print(
        f"Topics: {len(doc['topics'])}  subtopics: {stats['subtopics']}  "
        f"LOs: {stats['los']}  empty: {stats['empty'] or 0}"
    )
    # Spot-check 1.1
    for topic in doc["topics"]:
        if topic["code"] != "1":
            continue
        for sub in topic["subtopics"]:
            print(f"Sample {sub['code']} {sub['title']}:")
            for lo in sub["learning_outcomes"]:
                print(f"  {lo['id']}: {lo['text'][:90]}")
    if args.dry_run:
        return 0
    dump_yaml(doc, args.yaml)
    print(f"Wrote {args.yaml}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
