#!/usr/bin/env python3
"""Locate each homework question inside its original QP PDF and dump stem+options.

Robust strategy: take a distinctive phrase from the vault body, normalise
whitespace/case, find the page that contains it, then slice the question block
around the question-number marker. Writes /tmp/src-<slug>.txt.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz
import yaml

REPO = Path(__file__).resolve().parent.parent
FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)
LETTERS = {"A", "B", "C", "D"}


def load_fm(path: Path) -> dict:
    m = FM_RE.match(path.read_text(encoding="utf-8"))
    return yaml.safe_load(m.group(1)) if m else {}


def norm(s: str) -> str:
    s = re.sub(r"\\[a-zA-Z]+", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def body_text(path: Path) -> str:
    t = path.read_text(encoding="utf-8")
    m = re.search(r"## Question\n(.*?)(?:\n## |\Z)", t, re.S)
    t = m.group(1) if m else t
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"!\[\[[^\]]*\]\]", " ", t)
    t = re.sub(r"<img[^>]*>", " ", t)
    return t


def key_phrase(body: str) -> str:
    n = norm(body)
    # drop a leading question-number token
    n = re.sub(r"^\d+\s+", "", n)
    return n[:70]


def pages_of(pdf: Path):
    doc = fitz.open(str(pdf))
    return [pg.get_text() for pg in doc]


def locate(pages: list[str], body: str, qnum: str | None):
    key = key_phrase(body)
    lo, hi = 55, 70
    while lo >= 25:
        frag = key[:hi]
        for i, txt in enumerate(pages):
            if frag and frag in norm(txt):
                return i + 1, frag
        hi -= 15
        lo -= 15
    # fall back: qnum marker on any page
    if qnum:
        for i, txt in enumerate(pages):
            for ln in txt.splitlines():
                if ln.strip() == qnum:
                    return i + 1, f"<qnum {qnum} only>"
    return None, key


def block(page_text: str, qnum: str | None) -> str:
    lines = [ln.rstrip() for ln in page_text.splitlines()]
    idx = None
    if qnum:
        idx = next((i for i, ln in enumerate(lines) if ln.strip() == qnum), None)
    if idx is None:
        return "\n".join(lines)
    stem: list[str] = []
    for j in range(idx - 1, max(-1, idx - 7), -1):
        s = lines[j].strip()
        if s in LETTERS or s == "":
            break
        stem.insert(0, s)
    return ("STEM: " + " ".join(stem) + "\n"
            + "\n".join(lines[idx: idx + 18]))


def main() -> int:
    slug = sys.argv[1]
    build = json.loads((REPO / "build" / f"{slug}.json").read_text(encoding="utf-8"))
    out: list[str] = []
    for q in build["questions"]:
        qid = q["id"]
        path = None
        for d in ("vault/questions", "vault-structured/questions"):
            p = REPO / d / f"{qid}.md"
            if p.is_file():
                path = p
                break
        if not path:
            out.append(f"\n### {qid} (no md)")
            continue
        src = load_fm(path)
        pdf = REPO / (src.get("source_qp") or "")
        qnum = str(src.get("question")) if src.get("question") else None
        out.append(f"\n{'='*88}\n{qid} | {q.get('question_type')} | {src.get('marks')}m | "
                   f"ms={src.get('ms_answer')} | {src.get('source_qp')}")
        if not pdf.is_file():
            out.append("<no source pdf>")
            continue
        pages = pages_of(pdf)
        page_no, frag = locate(pages, body_text(path), qnum)
        if page_no is None:
            out.append(f"<not located; key='{frag}'>")
            continue
        out.append(f"[page {page_no}] key='{frag[:45]}'")
        ptext = pages[page_no - 1]
        if q.get("question_type") == "mcq":
            out.append(block(ptext, qnum))
        else:
            out.append(ptext)
    dest = Path(f"/tmp/src-{slug}.txt")
    dest.write_text("\n".join(out), encoding="utf-8")
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
