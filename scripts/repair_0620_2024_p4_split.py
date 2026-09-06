#!/usr/bin/env python3
"""Re-split 2024 IGCSE 0620 P4 drafts after sanitising PDF control chars.

2024 Theory PDFs often insert BEL (U+0007) after a main-question number
(``2\\x07Complete Table``). ``split.MAIN_Q_RE`` needs whitespace there, so
the first ingest collapses the whole paper into Q1. This script does **not**
edit ``split.py``: it replaces C0 controls with spaces, pads short stems,
injects ``(a)`` on letterless table questions, rewrites bare MS ``2`` labels
to ``2(a)``, then re-runs ``write_split_output``.

Usage:
  python scripts/repair_0620_2024_p4_split.py
  python scripts/repair_0620_2024_p4_split.py 0620_s24_qp_41
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chembank.extract import extract_pdf_text  # noqa: E402
from chembank.split import write_split_output  # noqa: E402

CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
SHORT_STEM_RE = re.compile(
    r"(?m)^(?P<num>\d{1,2})(?P<sp>[ \t]+)(?P<rest>\S[^\n]*)$"
)

PAPERS = [
    "0620_s24_qp_41",
    "0620_s24_qp_42",
    "0620_s24_qp_43",
    "0620_w24_qp_41",
    "0620_w24_qp_42",
    "0620_w24_qp_43",
    "0620_m24_qp_42",
]


def sanitize(text: str) -> str:
    return CONTROL_RE.sub(" ", text)


def pad_short_stems(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        rest = m.group("rest").strip()
        words = rest.split()
        if len(words) <= 3 and re.search(r"[A-Za-z]{3,}", rest):
            return (
                f"{m.group('num')}{m.group('sp')}"
                f"{rest} as shown in the question paper."
            )
        return m.group(0)

    return SHORT_STEM_RE.sub(repl, text)


def inject_letterless_a(text: str) -> str:
    """Turn a letterless main Q (``2 Complete Table``) into ``2 (a) Complete``."""
    return re.sub(
        r"(?m)^(?P<num>[2-9]|1[0-9])(?P<sp>[ \t]+)(?P<cmd>Complete|Fill)\b",
        r"\g<num>\g<sp>(a) \g<cmd>",
        text,
    )


def fix_ms_bare_questions(ms_text: str) -> str:
    """``Question\\nAnswer\\nMarks\\n2`` → ``2(a)`` so MS clips bind."""
    return re.sub(
        r"(?m)^(Question\s*\nAnswer\s*\nMarks\s*\n)(\d{1,2})[ \t]*$",
        r"\1\2(a)",
        ms_text,
    )


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
    cleaned = inject_letterless_a(pad_short_stems(sanitize(raw)))
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(cleaned, encoding="utf-8")
    ms_text = extract_pdf_text(ms, recover_symbols=False) if ms.is_file() else None
    if ms_text:
        ms_text = fix_ms_bare_questions(ms_text)
        (ROOT / "draft" / f"{ms.stem}.txt").write_text(ms_text, encoding="utf-8")
    chunks = write_split_output(
        cleaned,
        draft,
        source_name=paper_id,
        mark_scheme_text=ms_text,
        part_level=True,
    )
    slugs = [c.part_slug or str(c.question) for c in chunks]
    parents = sorted(
        {(c.parent_question or str(c.question)) for c in chunks},
        key=lambda x: int(str(x)),
    )
    print(f"{paper_id}: {len(chunks)} parts  parents={parents}  slugs={slugs}")
    return 0


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
