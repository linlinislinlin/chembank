#!/usr/bin/env python3
"""Reading-order text extraction from a QP page (fixes sub/superscript jumbling).

PyMuPDF's plain get_text() interleaves subscripts and superscripts, which
corrupts chemistry expressions such as  ΔHf(CH4).  This groups words into lines
by their baseline (y) and sorts by x, reconstructing the true reading order.
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz


def page_lines_ordered(pdf: str, page_no: int, tol: float = 3.0) -> list[str]:
    doc = fitz.open(pdf)
    page = doc[page_no - 1]
    words = page.get_text("words")  # x0, y0, x1, y1, word, block, line, word_no
    rows: list[list] = []
    for w in sorted(words, key=lambda w: (w[1], w[0])):
        placed = False
        for r in rows:
            if abs(r[0] - w[1]) <= tol:
                r[1].append(w)
                placed = True
                break
        if not placed:
            rows.append([w[1], [w]])
    rows.sort(key=lambda r: r[0])
    out = []
    for _, ws in rows:
        ws.sort(key=lambda w: w[0])
        out.append(" ".join(w[4] for w in ws))
    return out


def main() -> int:
    pdf = sys.argv[1]
    page = int(sys.argv[2])
    needle = sys.argv[3] if len(sys.argv) > 3 else None
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    lines = page_lines_ordered(pdf, page)
    if needle:
        try:
            i = next(k for k, ln in enumerate(lines) if needle in ln)
        except StopIteration:
            print("\n".join(lines[:n]))
            return 1
        lines = lines[max(0, i - 1): i + n]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
