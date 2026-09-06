#!/usr/bin/env python3
"""Re-split 2024 IGCSE 0620 P2 MCQ drafts that lose questions after combo items.

Statement numbers ``1``–``4`` under ``Which statements`` match ``MAIN_Q_RE``
and steal Q3/Q4. This script rewrites those lines to ``(1) …`` so they are
not main questions. It does **not** edit ``split.py``.

Usage:
  python scripts/repair_0620_2024_p2_split.py
  python scripts/repair_0620_2024_p2_split.py 0620_s24_qp_22
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chembank.extract import extract_pdf_text  # noqa: E402
from chembank.split import write_split_output  # noqa: E402

COMBO_OPEN = re.compile(r"Which statements\b", re.I)
# 2024 options are often one letter per line (``A 1 and 3``), not ``A … B …`` on one row.
OPTION_ROW = re.compile(r"^A\s+(?:\d|1\s+and)")
STMT_LINE = re.compile(r"^([1-4])[ \t]+(\S)")

PAPERS = [
    "0620_s24_qp_21",
    "0620_s24_qp_22",
    "0620_s24_qp_23",
    "0620_w24_qp_21",
    "0620_w24_qp_22",
    "0620_w24_qp_23",
    "0620_m24_qp_22",
]


def wrap_combo_statements(text: str) -> str:
    """Rewrite combo statement numbers ``1 …`` → ``(1) …`` so they are not main Qs."""
    out: list[str] = []
    inside = False
    for line in text.splitlines(keepends=True):
        naked = line.lstrip("\ufeff")
        if COMBO_OPEN.search(naked):
            inside = True
            out.append(line)
            continue
        if inside and OPTION_ROW.match(naked):
            inside = False
            out.append(line)
            continue
        if inside:
            line = STMT_LINE.sub(r"(\1) \2", line, count=1)
        out.append(line)
    return "".join(out)


def repair(paper_id: str) -> int:
    qp = ROOT / "raw" / "papers" / f"{paper_id}.pdf"
    season, paper = paper_id.split("_qp_")[0].removeprefix("0620_"), paper_id.split("_qp_")[1]
    ms = ROOT / "raw" / "papers" / f"0620_{season}_ms_{paper}.pdf"
    text_path = ROOT / "draft" / f"{paper_id}.txt"
    draft = ROOT / "draft" / paper_id
    if not qp.is_file():
        print(f"skip {paper_id}: missing QP")
        return 0
    raw = extract_pdf_text(qp, recover_symbols=True)
    cleaned = wrap_combo_statements(raw)
    text_path.write_text(cleaned, encoding="utf-8")
    ms_text = extract_pdf_text(ms, recover_symbols=True) if ms.is_file() else None
    chunks = write_split_output(
        cleaned,
        draft,
        source_name=paper_id,
        mark_scheme_text=ms_text,
        part_level=False,
    )
    nums = [int(c.question) for c in chunks]
    missing = [i for i in range(1, 41) if i not in nums]
    print(f"{paper_id}: {len(chunks)} questions missing={missing}")
    return 0 if not missing else 1


def main(argv: list[str]) -> int:
    wanted = argv[1:] or [
        p for p in PAPERS if (ROOT / "raw" / "papers" / f"{p}.pdf").is_file()
    ]
    rc = 0
    for paper_id in wanted:
        rc |= repair(paper_id)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
