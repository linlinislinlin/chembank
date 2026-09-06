#!/usr/bin/env python3
"""Hand-tag remaining IGCSE 0620 P4 structured variants from 0620 vocabulary.

Creates tagged JSON from draft q*.txt + index.json. Assessed skill, not list decoration.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SYL = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

# paper_id -> (session, paper, {slug: (codes, los, skills, difficulty)})
PAPERS: dict[str, tuple[str, int, dict[str, tuple[list[str], list[str], list[str], int]]]] = {
    "0620_w25_qp_41": (
        "ON",
        41,
        {
            "1a": (["2.2"], ["2.2-C2"], ["recall"], 2),
            "1b-i": (["2.3"], ["2.3-C1"], ["recall"], 2),
            "1b-ii": (["2.3"], ["2.3-S3"], ["explain"], 3),
            "1c": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["calculate"], 3),
            "1d": (["2.2"], ["2.2-C4"], ["recall"], 1),
            "1e": (["3.3"], ["3.3-S3", "3.3-S2"], ["calculate"], 3),
            "2a": (["8.1"], ["8.1-C5"], ["recall"], 3),
            "2b": (["2.7"], ["2.7-S1"], ["explain"], 3),
            "2c-i": (["9.4", "7.1"], ["9.4-C2", "7.1-C7"], ["recall"], 3),
            "2c-ii": (["9.4"], ["9.4-C2"], ["recall"], 2),
            "2d-i": (["12.5"], ["12.5-C4"], ["recall"], 2),
            "2d-ii": (["3.1", "9.1"], ["3.1-C4", "9.1-C2"], ["recall"], 3),
            "2e-i": (["7.3"], ["7.3-S5"], ["recall"], 2),
            "2e-ii": (["3.3"], ["3.3-S3", "3.3-S7"], ["calculate"], 4),
            "3a": (["3.1", "7.1"], ["3.1-S7", "7.1-C8"], ["recall"], 3),
            "3b": (["7.1"], ["7.1-C8"], ["recall"], 1),
            "3c": (["3.3"], ["3.3-S3"], ["calculate"], 3),
            "3d": (["12.2"], ["12.2-C1"], ["recall"], 2),
            "3e": (["3.3"], ["3.3-S6"], ["calculate"], 3),
            "3f": (["7.1"], ["7.1-C5"], ["recall"], 2),
            "3g": (["7.3"], ["7.3-C1"], ["explain"], 3),
            "3h-i": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "3h-ii": (["12.4"], ["12.4-C1"], ["explain"], 3),
            "3h-iii": (["12.4"], ["12.4-C1"], ["suggest"], 3),
            "4a": (["5.1"], ["5.1-S6", "5.1-C3"], ["draw"], 3),
            "4b": (["5.1"], ["5.1-S8"], ["calculate"], 4),
            "4c": (["6.3"], ["6.3-S4"], ["explain"], 4),
            "4d": (["6.2"], ["6.2-S6", "6.2-S5"], ["explain"], 4),
            "5a-i": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "5a-ii": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "5b-i": (["11.6"], ["11.6-C1", "11.6-S4"], ["recall"], 3),
            "5b-ii": (["11.6"], ["11.6-C1"], ["recall"], 3),
            "5b-iii": (["11.6"], ["11.6-C1"], ["recall"], 3),
            "5c-i": (["3.1"], ["3.1-C2"], ["recall"], 2),
            "5c-ii": (["11.7"], ["11.7-S3"], ["recall"], 3),
            "5d-i": (["3.1"], ["3.1-S5"], ["calculate"], 3),
            "5d-ii": (["11.7", "7.1"], ["11.7-C1", "7.1-C1"], ["recall"], 2),
            "5e-i": (["11.8"], ["11.8-S8", "11.8-S10"], ["draw"], 4),
            "5e-ii": (["11.8"], ["11.8-S9"], ["recall"], 2),
        },
    ),
    "0620_w25_qp_42": (
        "ON",
        42,
        {
            "1a": (["1.1"], ["1.1-C2"], ["recall"], 2),
            "1b": (["1.1"], ["1.1-C3"], ["recall"], 2),
            "1c-i": (["1.2"], ["1.2-C1"], ["explain"], 2),
            "1c-ii": (["1.2"], ["1.2-S2"], ["recall"], 3),
            "1d": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "1e-i": (["10.3"], ["10.3-S8"], ["recall"], 3),
            "1e-ii": (["10.3"], ["10.3-S8"], ["recall"], 3),
            "2a-i": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "2a-ii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "2a-iii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "2a-iv": (["9.6"], ["9.6-S4"], ["recall"], 3),
            "2a-v": (["9.6"], ["9.6-S4", "9.6-C2"], ["recall"], 3),
            "2b": (["2.3"], ["2.3-C1"], ["explain"], 2),
            "2c-i": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["calculate"], 3),
            "2c-ii": (["12.5"], ["12.5-C2"], ["recall"], 3),
            "2d-i": (["6.4"], ["6.4-S11"], ["recall"], 2),
            "2d-ii": (["6.4"], ["6.4-S6"], ["explain"], 3),
            "2d-iii": (["6.4"], ["6.4-S10"], ["recall"], 3),
            "2e": (["6.4"], ["6.4-S13", "6.4-S10"], ["suggest"], 4),
            "3a": (["3.1", "7.3"], ["3.1-S7", "7.3-S4"], ["recall"], 3),
            "3b": (["3.3"], ["3.3-S3"], ["calculate"], 3),
            "3c": (["3.3"], ["3.3-C1", "3.3-S3"], ["calculate"], 3),
            "3d": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "3e": (["12.1"], ["12.1-C3"], ["recall"], 1),
            "3f": (["12.4", "7.3"], ["12.4-C1", "7.3-S4"], ["explain"], 3),
            "3g": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "3h": (["7.3"], ["7.3-C2", "7.3-S4"], ["recall"], 3),
            "4a-i": (["7.1"], ["7.1-C6"], ["recall"], 1),
            "4a-ii": (["7.1"], ["7.1-S10"], ["explain"], 3),
            "4a-iii": (["7.1"], ["7.1-C7", "7.1-S10"], ["recall"], 3),
            "4a-iv": (["7.1"], ["7.1-C2"], ["recall"], 2),
            "4a-v": (["7.1"], ["7.1-S11", "7.1-S12"], ["recall"], 3),
            "4a-vi": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "4a-vii": (["11.7", "7.1"], ["11.7-C1", "7.1-C1"], ["recall"], 3),
            "4b-i": (["7.1"], ["7.1-S9"], ["recall"], 2),
            "4b-ii": (["7.1"], ["7.1-C3"], ["recall"], 2),
            "4b-iii": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "4b-iv": (["6.4"], ["6.4-S9"], ["calculate"], 4),
            "5a": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "5b-i": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "5b-ii": (["11.1"], ["11.1-S9"], ["recall"], 3),
            "5c": (["11.1"], ["11.1-C5"], ["recall"], 2),
            "5d-i": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5d-ii": (["11.4", "11.2"], ["11.4-S4", "11.2-S3"], ["recall"], 4),
            "5d-iii": (["11.1"], ["11.1-S8"], ["recall"], 2),
            "6a": (["11.7"], ["11.7-S3"], ["draw"], 2),
            "6b": (["11.2"], ["11.2-S4"], ["recall"], 3),
            "6c": (["3.1"], ["3.1-S5"], ["calculate"], 3),
            "6d-i": (["11.7"], ["11.7-S3"], ["recall"], 3),
            "6d-ii": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "6e": (["11.2", "11.1"], ["11.2-S4", "11.1-S8"], ["recall"], 4),
            "6f": (["3.1"], ["3.1-C4"], ["recall"], 3),
        },
    ),
    "0620_w25_qp_43": (
        "ON",
        43,
        {
            "1a": (["2.2"], ["2.2-C2"], ["recall"], 2),
            "1b": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["calculate"], 3),
            "1c-i": (["3.2"], ["3.2-C1"], ["recall"], 2),
            "1c-ii": (["2.3"], ["2.3-S4"], ["calculate"], 4),
            "2a-i": (["2.5"], ["2.5-C3"], ["data-analysis"], 3),
            "2a-ii": (["2.7"], ["2.7-S2"], ["data-analysis"], 3),
            "2a-iii": (["2.4"], ["2.4-C4"], ["data-analysis"], 3),
            "2b-i": (["2.6"], ["2.6-C1", "2.6-S4"], ["explain"], 3),
            "2b-ii": (["2.4"], ["2.4-S7"], ["explain"], 3),
            "3a-i": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "3a-ii": (["9.6"], ["9.6-S5"], ["recall"], 2),
            "3a-iii": (["9.6"], ["9.6-S5"], ["recall"], 2),
            "3a-iv": (["9.6"], ["9.6-S5"], ["recall"], 3),
            "3b-i": (["9.4"], ["9.4-S5"], ["explain"], 3),
            "3b-ii": (["9.4", "3.1"], ["9.4-S4", "3.1-S7"], ["recall"], 3),
            "3b-iii": (["6.4"], ["6.4-S9"], ["recall"], 2),
            "3b-iv": (["6.4"], ["6.4-S7"], ["recall"], 2),
            "3c-i": (["5.1"], ["5.1-S4"], ["recall"], 2),
            "3c-ii": (["5.1"], ["5.1-C1"], ["recall"], 2),
            "3d": (["7.2"], ["7.2-S2"], ["recall"], 2),
            "3e": (["7.2", "3.1"], ["7.2-S2", "3.1-C4"], ["recall"], 4),
            "3f": (["3.1"], ["3.1-S6"], ["recall"], 3),
            "4a-i": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "4a-ii": (["6.3"], ["6.3-S4"], ["explain"], 4),
            "4a-iii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4b": (["5.1"], ["5.1-S8"], ["calculate"], 4),
            "4c": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "4d-i": (["7.1"], ["7.1-C1"], ["recall"], 2),
            "4d-ii": (["3.3"], ["3.3-S4", "3.3-S6"], ["calculate"], 4),
            "4g": (["3.3"], ["3.3-S4"], ["calculate"], 4),
            "5a-i": (["7.3", "3.1"], ["7.3-S4", "3.1-S7"], ["recall"], 3),
            "5a-ii": (["7.3"], ["7.3-C2"], ["recall"], 2),
            "5a-iii": (["7.3"], ["7.3-C2"], ["recall"], 2),
            "5a-iv": (["12.1"], ["12.1-C3"], ["recall"], 1),
            "5a-v": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "5b-i": (["8.2", "9.1"], ["8.2-C1", "9.1-C1"], ["compare"], 3),
            "5b-ii": (["8.4"], ["8.4-C1", "8.4-S2"], ["compare"], 3),
            "6a": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "6b": (["3.3", "3.1"], ["3.3-S7", "3.1-C2"], ["calculate"], 3),
            "6c-i": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "6c-ii": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "6c-iii": (["11.2"], ["11.2-S4"], ["recall"], 3),
            "6d-i": (["11.8"], ["11.8-C2"], ["recall"], 2),
            "6d-ii": (["11.8"], ["11.8-C1"], ["explain"], 3),
            "6d-iii": (["11.8"], ["11.8-S6"], ["recall"], 2),
            "6d-iv": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "6e-i": (["11.8"], ["11.8-S12"], ["draw"], 3),
            "6e-ii": (["11.8"], ["11.8-S10", "11.8-S13"], ["recall"], 3),
            "6e-iii": (["11.8"], ["11.8-S12"], ["recall"], 2),
        },
    ),
    "0620_s25_qp_42": (
        "MJ",
        42,
        {
            "1a": (["10.3"], ["10.3-C1"], ["recall"], 1),
            "1b": (["6.3"], ["6.3-S10"], ["recall"], 2),
            "1c": (["8.1"], ["8.1-C2"], ["recall"], 2),
            "1d": (["8.3"], ["8.3-C1"], ["recall"], 2),
            "1e": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "1f": (["11.5", "11.1"], ["11.5-C4", "11.1-S8"], ["recall"], 4),
            "1g": (["11.6", "2.5"], ["11.6-C1", "2.5-C2"], ["recall"], 3),
            "1h": (["11.2"], ["11.2-S4"], ["recall"], 3),
            "2a": (["2.5"], ["2.5-C1"], ["recall"], 2),
            "2b-i": (["6.4"], ["6.4-C1"], ["recall"], 2),
            "2b-ii": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "2b-iii": (["2.5"], ["2.5-S5"], ["explain"], 4),
            "2b-iv": (["2.5"], ["2.5-C3"], ["explain"], 3),
            "2c-i": (["2.6"], ["2.6-C2"], ["recall"], 2),
            "2c-ii": (["2.6"], ["2.6-C2"], ["recall"], 2),
            "2c-iii": (["2.6"], ["2.6-S3"], ["draw"], 3),
            "3a": (["4.1"], ["4.1-C1"], ["recall"], 2),
            "3b-i": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "3b-ii": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "3b-iii": (["4.1"], ["4.1-S9"], ["recall"], 2),
            "3b-iv": (["4.1"], ["4.1-S11"], ["recall"], 4),
            "3c-i": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "3c-ii": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "3d-i": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "3d-ii": (["9.6"], ["9.6-S5"], ["recall"], 2),
            "3d-iii": (["9.6"], ["9.6-S5"], ["explain"], 3),
            "4a-i": (["3.1", "9.6"], ["3.1-C4", "9.6-C1"], ["recall"], 3),
            "4a-ii": (["9.6"], ["9.6-C1"], ["suggest"], 3),
            "4b": (["9.3"], ["9.3-C1"], ["recall"], 1),
            "4c-i": (["6.4"], ["6.4-S9"], ["recall"], 3),
            "4c-ii": (["6.4"], ["6.4-S9"], ["calculate"], 4),
            "4c-iii": (["3.3"], ["3.3-S4", "3.3-S3"], ["calculate"], 4),
            "5a": (["8.2"], ["8.2-C1"], ["recall"], 1),
            "5b-i": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "5b-ii": (["8.2"], ["8.2-C2"], ["recall"], 3),
            "5b-iii": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "5b-iv": (["12.5"], ["12.5-C4"], ["recall"], 2),
            "5b-v": (["10.2"], ["10.2-C2"], ["recall"], 2),
            "5c": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "5d-i": (["2.3"], ["2.3-C1"], ["recall"], 2),
            "5d-ii": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["calculate"], 3),
            "5d-iii": (["2.3"], ["2.3-S4"], ["calculate"], 4),
            "6a": (["11.1"], ["11.1-C4"], ["recall"], 2),
            "6b": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "6c": (["11.5"], ["11.5-C1"], ["recall"], 3),
            "6d-i": (["6.3"], ["6.3-S4"], ["explain"], 4),
            "6d-ii": (["6.2"], ["6.2-S6", "6.2-S5"], ["explain"], 4),
            "6e-i": (["3.1"], ["3.1-C2"], ["recall"], 3),
            "6e-ii": (["11.1"], ["11.1-C6"], ["recall"], 3),
            "6e-iii": (["11.8"], ["11.8-S7"], ["draw"], 4),
            "6e-iv": (["11.7"], ["11.7-S3"], ["recall"], 3),
            "6e-v": (["3.3"], ["3.3-S6"], ["calculate"], 4),
        },
    ),
    "0620_s25_qp_43": (
        "MJ",
        43,
        {
            "1a": (["2.6"], ["2.6-S3"], ["recall"], 2),
            "1b": (["11.1", "11.5"], ["11.1-C6", "11.5-C1"], ["recall"], 2),
            "1c": (["7.2"], ["7.2-S3"], ["recall"], 2),
            "1d": (["2.6"], ["2.6-C2"], ["recall"], 2),
            "1e": (["3.1"], ["3.1-C1"], ["recall"], 3),
            "1f": (["9.6"], ["9.6-C2"], ["recall"], 3),
            "1g": (["11.1", "11.4"], ["11.1-C2", "11.4-C1"], ["recall"], 2),
            "1h-i": (["11.6", "10.3"], ["11.6-C1", "10.3-C1"], ["recall"], 3),
            "2a": (["2.2"], ["2.2-C1"], ["recall"], 1),
            "2b-i": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["calculate"], 3),
            "2b-ii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2b-iii": (["3.2"], ["3.2-C1"], ["recall"], 2),
            "2c": (["2.2"], ["2.2-C5"], ["recall"], 3),
            "3a-i": (["2.7"], ["2.7-S1"], ["recall"], 2),
            "3a-ii": (["2.7"], ["2.7-S1"], ["recall"], 2),
            "3a-iii": (["2.7"], ["2.7-S2"], ["recall"], 2),
            "3b-i": (["9.3"], ["9.3-C1"], ["recall"], 2),
            "3b-ii": (["9.3"], ["9.3-C1"], ["recall"], 1),
            "3c-i": (["7.3"], ["7.3-C1"], ["recall"], 3),
            "3c-ii": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "3c-iii": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "3c-iv": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "3c-v": (["6.2"], ["6.2-S6", "6.2-S5"], ["explain"], 4),
            "3c-vi": (["7.3"], ["7.3-C3"], ["recall"], 2),
            "4a-i": (["6.3", "3.1"], ["6.3-S9", "3.1-C4"], ["recall"], 4),
            "4a-ii": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "4b-i": (["6.3"], ["6.3-S10"], ["recall"], 3),
            "4b-ii": (["6.3"], ["6.3-S8"], ["recall"], 3),
            "4b-iii": (["6.3"], ["6.3-S8"], ["recall"], 3),
            "4c": (["6.4"], ["6.4-S9"], ["recall"], 3),
            "4d": (["3.3"], ["3.3-S4", "3.3-S3"], ["calculate"], 4),
            "4g": (["3.3"], ["3.3-S4"], ["calculate"], 4),
            "5a": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "5b-i": (["6.3"], ["6.3-S11"], ["explain"], 4),
            "5b-ii": (["6.3"], ["6.3-S4"], ["explain"], 4),
            "5b-iii": (["8.4", "6.2"], ["8.4-C1", "6.2-C2"], ["recall"], 3),
            "5c-i": (["11.7", "11.2"], ["11.7-C1", "11.2-S3"], ["recall"], 2),
            "5c-ii": (["11.1"], ["11.1-C2"], ["recall"], 3),
            "5d-i": (["11.7", "11.1"], ["11.7-S3", "11.1-C1"], ["draw"], 4),
            "5d-ii": (["11.2"], ["11.2-S4"], ["recall"], 3),
            "5e": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "6a": (["8.2"], ["8.2-C1"], ["recall"], 1),
            "6b": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "6c-i": (["8.2", "9.4"], ["8.2-C1", "9.4-C2"], ["recall"], 2),
            "6c-ii": (["3.1", "8.2"], ["3.1-C4", "8.2-C1"], ["recall"], 3),
            "6d": (["8.2", "8.4"], ["8.2-C1", "8.4-C1"], ["compare"], 3),
            "6e-i": (["8.3"], ["8.3-C2"], ["recall"], 2),
            "6e-ii": (["8.3"], ["8.3-C3"], ["recall"], 3),
            "6e-iii": (["5.1"], ["5.1-S8"], ["calculate"], 4),
            "6g": (["5.1"], ["5.1-S8"], ["calculate"], 4),
        },
    ),
}


def load_vocab() -> tuple[dict[str, str], dict[str, str]]:
    syl = yaml.safe_load(SYL.read_text(encoding="utf-8"))
    codes: dict[str, str] = {}
    los: dict[str, str] = {}
    for t in syl["topics"]:
        codes[str(t["code"])] = str(t["title"])
        for st in t.get("subtopics") or []:
            codes[str(st["code"])] = str(st["title"])
            for lo in st.get("learning_outcomes") or []:
                los[str(lo["id"])] = str(lo["text"])
    return codes, los


def _marks_from_body(body: str) -> int | None:
    hits = re.findall(r"\[(\d+)\]", body)
    return int(hits[-1]) if hits else None


def tag_paper(
    paper_id: str,
    session: str,
    paper: int,
    tags: dict[str, tuple[list[str], list[str], list[str], int]],
    code_titles: dict[str, str],
    lo_texts: dict[str, str],
) -> int:
    draft = ROOT / "draft" / paper_id
    tagged = draft / "tagged"
    tagged.mkdir(parents=True, exist_ok=True)
    idx = json.loads((draft / "index.json").read_text(encoding="utf-8"))
    rows = [r for r in idx if r.get("part_slug")]
    slugs = {r["part_slug"] for r in rows}
    missing = sorted(slugs - set(tags))
    extra = sorted(set(tags) - slugs)
    if missing or extra:
        print(f"{paper_id}: TAG mismatch missing={missing} extra={extra}")
        return 1
    season = "s25" if session == "MJ" else "w25"
    qp = f"raw/papers/{paper_id}.pdf"
    ms = f"raw/papers/0620_{season}_ms_{paper}.pdf"
    sess_slug = session.lower()
    bad: list[tuple[str, str, str]] = []
    for r in rows:
        slug = r["part_slug"]
        codes, lo_ids, skills, diff = tags[slug]
        for c in codes:
            if c not in code_titles:
                bad.append((slug, "code", c))
        for lo in lo_ids:
            if lo not in lo_texts:
                bad.append((slug, "lo", lo))
        raw = (draft / r["file"]).read_text(encoding="utf-8")
        if "\n--- MARK SCHEME ---" in raw:
            body, ms_text = raw.split("\n--- MARK SCHEME ---", 1)
        else:
            body, ms_text = raw, ""
        body = body.strip()
        for marker in ("The Periodic Table of Elements", "The Periodic Table", "Important values"):
            if marker in body:
                body = body.split(marker)[0].strip()
        rec = {
            "id": f"cie-0620-2025-{sess_slug}-p{paper}-q{slug}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2025,
            "session": session,
            "paper": paper,
            "question": slug,
            "marks": _marks_from_body(body),
            "syllabus_codes": codes,
            "topic_titles": [code_titles[c] for c in codes],
            "skills": skills,
            "question_type": "structured",
            "difficulty": diff,
            "command_words": [],
            "misconceptions": [],
            "learning_outcomes": lo_ids,
            "learning_outcome_texts": [lo_texts[i] for i in lo_ids],
            "learning_objectives": [],
            "ms_answer": None,
            "source_qp": qp,
            "source_ms": ms,
            "page_qp": r.get("page_hint"),
            "body": body,
            "mark_scheme": ms_text.strip(),
            "parent_question": r.get("parent_question"),
            "part": r.get("part"),
            "_retag": "assessed-skill-p4-variants",
        }
        (tagged / f"q{slug}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if bad:
        print(f"INVALID TAGS {paper_id}:", bad)
        return 1
    print(f"{paper_id}: wrote {len(rows)} tagged JSON parts")
    return 0


def main(argv: list[str]) -> int:
    wanted = argv[1:] or list(PAPERS)
    code_titles, lo_texts = load_vocab()
    rc = 0
    for paper_id in wanted:
        if paper_id not in PAPERS:
            print("unknown paper", paper_id)
            return 1
        session, paper, tags = PAPERS[paper_id]
        rc |= tag_paper(paper_id, session, paper, tags, code_titles, lo_texts)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
