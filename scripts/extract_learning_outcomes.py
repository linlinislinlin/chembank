#!/usr/bin/env python3
"""Extract CIE 9701 learning outcomes from the syllabus PDF into YAML.

Source PDF (prefer local):
  raw/papers/9701_syllabus_2025-2027.pdf
  else QLS textbook copy of 664563-2025-2027-syllabus.pdf

Id scheme:
  {subtopic}-{n}           e.g. 3.1-1
  {subtopic}-{n}{letter}   e.g. 2.4-1a  (when syllabus uses (a)(b)…)

Roman-numeral sub-lists (i)(ii)(iii) are folded into the parent lettered LO text.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "raw" / "papers" / "9701_syllabus_2025-2027.pdf"
FALLBACK_PDF = Path(
    "/Users/tsinglan-school/Desktop/QLS/AS/Text Book/664563-2025-2027-syllabus.pdf"
)
DEFAULT_YAML = ROOT / "syllabus" / "cie-9701-as-a-level-chemistry.yaml"

# Subject content pages in the 2025–2027 syllabus booklet (1-indexed).
PAGE_START = 16
PAGE_END = 55

SKIP_EXACT = {
    "AS Level subject content",
    "A Level subject content",
    "Physical chemistry",
    "Inorganic chemistry",
    "Organic chemistry",
    "Analysis",
    "Learning outcomes",
    "Candidates should be able to:",
}
SKIP_PREFIX = (
    "Candidates for Cambridge",
    "Teachers will find",
    "In this syllabus",
    "X to represent",
    "R and R",
)

SUB_RE = re.compile(r"^(\d{1,2}\.\d{1,2})\s+(.*)$")
SUB_ONLY_RE = re.compile(r"^(\d{1,2}\.\d{1,2})$")
TOPIC_RE = re.compile(r"^(\d{1,2})$")
LO_INLINE_RE = re.compile(r"^(\d{1,2})\s+(.+)$")
# Letter parts a–h, j–u, w–z (exclude i/v which CIE uses for roman sub-lists)
LETTER_RE = re.compile(r"^\(([a-hj-uw-z])\)\s*(.*)$")
ROMAN_RE = re.compile(r"^\((i{1,3}|iv|vi{0,3}|v|ix|x)\)\s*(.*)$", re.I)


def clean(s: str) -> str:
    s = s.replace("\u00a0", " ").replace("\t", " ")
    s = s.replace("\u2009", " ").replace("\u200a", " ").replace("\u202f", " ")
    s = s.replace("\ufeff", "").replace("\u00ad", "")
    s = s.replace("\u2011", "-").replace("\u2013", "–").replace("\u2014", "—")
    s = re.sub(r"[\ue000-\uf8ff]", "", s)  # PDF private-use glyphs
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)  # control chars
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def resolve_pdf(path: Path | None) -> Path:
    if path and path.is_file():
        return path
    if DEFAULT_PDF.is_file():
        return DEFAULT_PDF
    if FALLBACK_PDF.is_file():
        return FALLBACK_PDF
    raise FileNotFoundError(
        f"Syllabus PDF not found. Tried {DEFAULT_PDF} and {FALLBACK_PDF}"
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
                x = round(line["bbox"][0], 1)
                if text.startswith("Cambridge International") or text.startswith(
                    "www.cambridge"
                ):
                    continue
                if text == "Back to contents page":
                    continue
                if re.fullmatch(r"\d{1,3}", text) and x > 500:
                    continue
                lines.append({"page": i + 1, "x": x, "text": text})
    pdf.close()
    return lines


def parse_learning_outcomes(
    lines: list[dict[str, Any]],
    existing_subs: dict[str, str],
) -> dict[str, list[dict[str, Any]]]:
    """Return {subtopic_code: [{num, text, parts:[{letter,text}]}]}."""
    by_sub: dict[str, list[dict[str, Any]]] = {c: [] for c in existing_subs}
    current_sub: str | None = None
    current_lo: dict[str, Any] | None = None

    def ensure_sub(code: str, title_hint: str = "") -> None:
        nonlocal current_sub, current_lo
        by_sub.setdefault(code, [])
        current_sub = code
        current_lo = None
        if title_hint and code not in existing_subs:
            existing_subs[code] = title_hint

    def start_lo(num: str, text: str) -> None:
        nonlocal current_lo
        if not current_sub:
            return
        text = clean(text)
        lo: dict[str, Any] = {"num": num, "text": "", "parts": []}
        # LO whose first line is already (a) …
        m = LETTER_RE.match(text)
        if m:
            lo["parts"].append({"letter": m.group(1), "text": clean(m.group(2))})
        else:
            lo["text"] = text
        by_sub.setdefault(current_sub, []).append(lo)
        current_lo = lo

    def append_cont(text: str) -> None:
        if not current_lo:
            return
        if current_lo["parts"]:
            last = current_lo["parts"][-1]
            last["text"] = clean(f"{last['text']} {text}")
        else:
            current_lo["text"] = clean(f"{current_lo['text']} {text}")

    i = 0
    n = len(lines)
    while i < n:
        t = lines[i]["text"]
        x = lines[i]["x"]

        if t in SKIP_EXACT or any(t.startswith(p) for p in SKIP_PREFIX):
            i += 1
            continue
        if x > 200:
            i += 1
            continue

        m = SUB_RE.match(t)
        if x < 75 and m:
            code, title = m.group(1), clean(m.group(2))
            title = re.sub(r"\s*\(continued\)\s*$", "", title, flags=re.I)
            ensure_sub(code, title)
            i += 1
            continue

        if x < 75 and SUB_ONLY_RE.match(t):
            code = t
            title = ""
            j = i + 1
            if j < n and lines[j]["x"] >= 85:
                title = lines[j]["text"]
                j += 1
                while (
                    j < n
                    and lines[j]["x"] >= 88
                    and lines[j]["x"] < 120
                    and lines[j]["text"] not in SKIP_EXACT
                    and not SUB_RE.match(lines[j]["text"])
                    and not SUB_ONLY_RE.match(lines[j]["text"])
                ):
                    title = clean(f"{title} {lines[j]['text']}")
                    j += 1
            ensure_sub(code, title)
            i = j
            continue

        if x < 75 and TOPIC_RE.match(t):
            if i + 1 < n:
                nxt = lines[i + 1]
                if nxt["x"] >= 88 and re.match(r"^[A-Z]", nxt["text"]):
                    i += 2
                    continue
                if current_sub and 70 <= nxt["x"] < 88:
                    start_lo(t, nxt["text"])
                    i += 2
                    continue
            i += 1
            continue

        m = LO_INLINE_RE.match(t)
        if current_sub and x < 75 and m and not SUB_ONLY_RE.match(t):
            start_lo(m.group(1), m.group(2))
            i += 1
            continue

        m = LETTER_RE.match(t)
        if current_lo and 70 <= x < 100 and m:
            current_lo["parts"].append(
                {"letter": m.group(1), "text": clean(m.group(2))}
            )
            i += 1
            continue

        m = ROMAN_RE.match(t)
        if current_lo and x >= 70 and m:
            frag = f"({m.group(1).lower()}) {clean(m.group(2))}"
            append_cont(frag)
            i += 1
            continue

        if current_lo and 70 <= x < 150:
            if (
                SUB_RE.match(t)
                or SUB_ONLY_RE.match(t)
                or t in SKIP_EXACT
                or re.match(r"^In \d", t)
            ):
                i += 1
                continue
            append_cont(t)
            i += 1
            continue

        if current_sub and x < 120 and re.match(
            r"^(In \d|Only the elements|This topic|Notes?:)", t
        ):
            i += 1
            continue

        i += 1

    return by_sub


def expand_los(lo_list: list[dict[str, Any]], sub_code: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for lo in lo_list:
        num = str(lo["num"])
        text = clean(lo.get("text") or "")
        parts = lo.get("parts") or []
        if parts:
            for p in parts:
                letter = p["letter"]
                ptext = clean(p["text"])
                if text:
                    full = f"{text} ({letter}) {ptext}"
                else:
                    full = ptext
                out.append({"id": f"{sub_code}-{num}{letter}", "text": clean(full)})
        elif text:
            out.append({"id": f"{sub_code}-{num}", "text": text})
    return out


def merge_into_syllabus(
    syllabus: dict[str, Any],
    by_sub: dict[str, list[dict[str, Any]]],
    source_pdf_name: str,
) -> tuple[dict[str, Any], dict[str, int]]:
    meta = dict(syllabus.get("meta") or {})
    meta["source_pdf"] = source_pdf_name
    note = meta.get("note") or ""
    lo_note = (
        "Learning outcome ids use {subtopic}-{n} or {subtopic}-{n}{letter} "
        "(syllabus numbering under each subtopic). Tag questions with the most "
        "specific learning_outcomes ids and always keep parent syllabus_codes."
    )
    if "Learning outcome ids" not in note:
        meta["note"] = (note.rstrip() + " " + lo_note).strip()

    stats = {"subtopics": 0, "los": 0, "empty": 0}
    topics_out = []
    for topic in syllabus["topics"]:
        t_entry = {
            "code": str(topic["code"]),
            "title": topic["title"],
            "level": topic.get("level"),
            "group": topic.get("group"),
            "subtopics": [],
        }
        for sub in topic.get("subtopics") or []:
            sc = str(sub["code"])
            expanded = expand_los(by_sub.get(sc, []), sc)
            t_entry["subtopics"].append(
                {
                    "code": sc,
                    "title": sub["title"],
                    "learning_outcomes": expanded,
                }
            )
            stats["subtopics"] += 1
            stats["los"] += len(expanded)
            if not expanded:
                stats["empty"] += 1
        topics_out.append(t_entry)

    return {"meta": meta, "topics": topics_out}, stats


class _IndentDumper(yaml.SafeDumper):
    pass


def _str_representer(dumper: yaml.Dumper, data: str):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    # Quote codes that look numeric so 3.1 stays a string
    if re.fullmatch(r"\d+(\.\d+)?", data) or re.fullmatch(
        r"\d+(\.\d+)?-\d+[a-z]?", data
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
    p.add_argument(
        "--yaml",
        type=Path,
        default=DEFAULT_YAML,
        help="Syllabus YAML to update (keeps topic/subtopic titles)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print stats only; do not write YAML",
    )
    args = p.parse_args(argv)

    pdf_path = resolve_pdf(args.pdf)
    with args.yaml.open(encoding="utf-8") as f:
        syllabus = yaml.safe_load(f)

    existing_subs = {
        str(s["code"]): str(s["title"])
        for t in syllabus["topics"]
        for s in (t.get("subtopics") or [])
    }
    lines = extract_lines(pdf_path)
    by_sub = parse_learning_outcomes(lines, existing_subs)
    merged, stats = merge_into_syllabus(syllabus, by_sub, pdf_path.name)

    print(f"PDF: {pdf_path}")
    print(
        f"Subtopics: {stats['subtopics']}  LOs: {stats['los']}  "
        f"empty: {stats['empty']}"
    )
    # Spot-check 3.1
    for topic in merged["topics"]:
        if topic["code"] != "3":
            continue
        for sub in topic["subtopics"]:
            if sub["code"] == "3.1":
                print("Sample 3.1:")
                for lo in sub["learning_outcomes"]:
                    print(f"  {lo['id']}: {lo['text'][:88]}")

    if args.dry_run:
        return 0
    dump_yaml(merged, args.yaml)
    print(f"Wrote {args.yaml}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
