#!/usr/bin/env python3
"""Hand-tag IGCSE 0620 2022 P2 MCQ variants from the 0620 (2026–2028) vocabulary.

Assessed skill, not decorative context. year=2022; MJ=s22, ON=w22, FM=m22.
2022 sat the pre-2023 syllabus; nearest 2026–2028 leaf is used when the item
has no exact modern counterpart (see report: 可能对口旧考纲).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SYL = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

# paper_id -> (session, paper_num, tags)
# tags: q -> (syllabus_codes, lo_ids, skills, difficulty)
PAPERS: dict[str, tuple[str, int, dict[int, tuple[list[str], list[str], list[str], int]]]] = {
    "0620_s22_qp_21": (
        "MJ",
        21,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 3),
            2: (["12.1"], ["12.1-C1"], ["practical"], 2),
            3: (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C1"], ["data-analysis"], 3),
            4: (["12.4"], ["12.4-C3"], ["recall"], 2),
            5: (["2.4", "2.7"], ["2.4-C4", "2.7-S2"], ["compare"], 3),
            6: (["2.5"], ["2.5-S4"], ["recall"], 3),
            7: (["3.1"], ["3.1-C4"], ["recall"], 2),
            8: (["3.2"], ["3.2-C1"], ["recall"], 2),
            9: (["3.3"], ["3.3-S5"], ["calculate"], 4),
            10: (["4.1"], ["4.1-S10", "4.1-C3"], ["recall"], 3),
            11: (["4.1"], ["4.1-S11", "4.1-S9"], ["recall"], 3),
            12: (["6.1"], ["6.1-C1"], ["compare"], 2),
            13: (["5.1"], ["5.1-S7"], ["explain"], 3),
            14: (["12.5"], ["12.5-C1"], ["data-analysis"], 3),
            15: (["6.3"], ["6.3-C2"], ["recall"], 2),
            16: (["6.4"], ["6.4-S8", "6.4-S13"], ["explain"], 4),
            17: (["7.1"], ["7.1-S9", "7.1-S10"], ["recall"], 3),
            18: (["7.2"], ["7.2-C1"], ["data-analysis"], 3),
            19: (["7.3"], ["7.3-C1"], ["recall"], 2),
            20: (["2.2", "8.1"], ["2.2-C5", "8.1-C5"], ["recall"], 3),
            21: (["8.1"], ["8.1-S6"], ["data-analysis"], 3),
            22: (["8.4"], ["8.4-S2"], ["recall"], 3),
            23: (["9.6"], ["9.6-S5"], ["recall"], 3),
            24: (["9.5"], ["9.5-S4", "9.5-S5"], ["explain"], 3),
            25: (["8.5"], ["8.5-C1"], ["recall"], 2),
            26: (["9.1"], ["9.1-C1", "9.1-C2"], ["recall"], 2),
            27: (["9.4"], ["9.4-C3", "9.6-C1"], ["data-analysis"], 3),
            28: (["12.5"], ["12.5-C3"], ["data-analysis"], 3),
            29: (["10.1"], ["10.1-C7"], ["recall"], 2),
            30: (["6.3"], ["6.3-S4", "6.3-S11"], ["explain"], 4),
            31: (["10.2"], ["10.2-C2"], ["recall"], 2),
            32: (["6.3", "4.1"], ["6.3-S8", "4.1-C3"], ["recall"], 3),
            33: (["12.5", "6.4"], ["12.5-C3", "6.4-S10"], ["recall"], 3),
            34: (["9.6"], ["9.6-C2"], ["recall"], 2),
            35: (["11.2"], ["11.2-S4"], ["recall"], 3),
            36: (["11.6"], ["11.6-S4"], ["compare"], 3),
            37: (["11.3", "11.7"], ["11.3-C3", "11.7-C1"], ["data-analysis"], 3),
            38: (["11.5"], ["11.5-C1", "11.1-C6"], ["recall"], 3),
            39: (["11.7"], ["11.7-S2"], ["recall"], 2),
            40: (["11.8"], ["11.8-S10"], ["recall"], 2),
        },
    ),
    "0620_s22_qp_22": (
        "MJ",
        22,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 3),
            2: (["12.1"], ["12.1-C1"], ["practical"], 2),
            3: (["12.3"], ["12.3-S4"], ["calculate"], 3),
            4: (["2.3"], ["2.3-C1"], ["recall"], 3),
            5: (["2.6"], ["2.6-C1", "2.6-S3"], ["recall"], 3),
            6: (["2.5"], ["2.5-C2"], ["recall"], 2),
            7: (["3.1"], ["3.1-C4"], ["recall"], 2),
            8: (["3.3"], ["3.3-S4", "3.3-S5"], ["calculate"], 4),
            9: (["3.2"], ["3.2-C2"], ["calculate"], 3),
            10: (["4.1"], ["4.1-S10", "4.1-C3"], ["recall"], 3),
            11: (["4.1"], ["4.1-S8"], ["recall"], 3),
            12: (["6.1"], ["6.1-C1"], ["compare"], 2),
            13: (["6.2"], ["6.2-S6", "6.2-S5"], ["explain"], 3),
            14: (["6.3"], ["6.3-C1"], ["recall"], 2),
            15: (["6.3"], ["6.3-C2"], ["recall"], 2),
            16: (["5.1"], ["5.1-C3"], ["recall"], 2),
            17: (["4.2"], ["4.2-C1"], ["recall"], 3),
            18: (["7.2"], ["7.2-C1"], ["data-analysis"], 3),
            19: (["7.3"], ["7.3-C1"], ["recall"], 2),
            20: (["6.4"], ["6.4-S7", "6.4-S11"], ["recall"], 3),
            21: (["8.1"], ["8.1-S6"], ["data-analysis"], 3),
            22: (["7.1"], ["7.1-S9"], ["recall"], 3),
            23: (["8.4"], ["8.4-C1", "8.4-S2"], ["recall"], 2),
            24: (["8.2", "8.3"], ["8.2-C1", "8.3-C1"], ["compare"], 3),
            25: (["9.4"], ["9.4-C3"], ["data-analysis"], 3),
            26: (["2.3"], ["2.3-C1"], ["data-analysis"], 3),
            27: (["9.3"], ["9.3-C4"], ["recall"], 2),
            28: (["12.5"], ["12.5-C3"], ["data-analysis"], 3),
            29: (["9.6"], ["9.6-C1"], ["recall"], 3),
            30: (["9.5"], ["9.5-S4"], ["recall"], 2),
            31: (["10.2"], ["10.2-C2"], ["recall"], 2),
            32: (["10.3"], ["10.3-C2", "10.3-C5"], ["recall"], 3),
            33: (["6.3"], ["6.3-S10"], ["recall"], 2),
            34: (["9.6"], ["9.6-C2"], ["recall"], 2),
            35: (["11.2"], ["11.2-S4"], ["recall"], 3),
            36: (["11.5"], ["11.5-S6"], ["recall"], 2),
            37: (["11.5"], ["11.5-C2"], ["recall"], 3),
            38: (["11.1"], ["11.1-C5", "11.1-C6"], ["compare"], 3),
            39: (["11.4"], ["11.4-S4"], ["recall"], 3),
            40: (["11.8"], ["11.8-S10", "11.8-S6"], ["recall"], 3),
        },
    ),
    "0620_s22_qp_23": (
        "MJ",
        23,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 3),
            2: (["12.1"], ["12.1-C1"], ["practical"], 2),
            3: (["2.6"], ["2.6-S4"], ["recall"], 3),
            4: (["12.3"], ["12.3-C2"], ["data-analysis"], 3),
            5: (["2.3"], ["2.3-C1"], ["recall"], 3),
            6: (["2.7"], ["2.7-S2"], ["recall"], 3),
            7: (["3.1"], ["3.1-C4"], ["recall"], 2),
            8: (["3.3"], ["3.3-S4", "3.3-S5"], ["calculate"], 3),
            9: (["9.6"], ["9.6-S5"], ["recall"], 3),
            10: (["4.1"], ["4.1-S10", "4.1-C3"], ["recall"], 3),
            11: (["4.2"], ["4.2-C1"], ["recall"], 3),
            12: (["6.1"], ["6.1-C1"], ["compare"], 2),
            13: (["9.1", "6.4"], ["9.1-C2", "6.4-C3"], ["recall"], 3),
            14: (["6.2"], ["6.2-S6"], ["explain"], 3),
            15: (["6.3"], ["6.3-C2"], ["recall"], 2),
            16: (["7.1"], ["7.1-C7"], ["recall"], 2),
            17: (["7.2"], ["7.2-C1"], ["recall"], 3),
            18: (["7.2"], ["7.2-C1"], ["data-analysis"], 3),
            19: (["7.3"], ["7.3-C1"], ["recall"], 2),
            20: (["12.5"], ["12.5-C2"], ["recall"], 3),
            21: (["8.1"], ["8.1-S6"], ["data-analysis"], 3),
            22: (["8.1"], ["8.1-C2", "8.1-C5"], ["data-analysis"], 3),
            23: (["8.3"], ["8.3-C4"], ["recall"], 3),
            24: (["8.4"], ["8.4-C1"], ["recall"], 2),
            25: (["8.5"], ["8.5-C1"], ["recall"], 2),
            26: (["9.1"], ["9.1-C1", "9.1-C2"], ["data-analysis"], 3),
            27: (["9.6"], ["9.6-C1"], ["recall"], 2),
            28: (["12.5"], ["12.5-C3"], ["data-analysis"], 3),
            29: (["10.3"], ["10.3-S8"], ["recall"], 3),
            30: (["9.5"], ["9.5-S5"], ["recall"], 2),
            31: (["10.2"], ["10.2-C2"], ["recall"], 2),
            32: (["10.3"], ["10.3-C2"], ["recall"], 3),
            33: (["6.3"], ["6.3-S4"], ["explain"], 4),
            34: (["9.6"], ["9.6-C2"], ["recall"], 2),
            35: (["11.2"], ["11.2-S4"], ["recall"], 3),
            36: (["11.4"], ["11.4-S3"], ["recall"], 2),
            37: (["11.1"], ["11.1-S8"], ["recall"], 3),
            38: (["11.5"], ["11.5-C2", "11.5-C4"], ["explain"], 3),
            39: (["3.3"], ["3.3-S8"], ["calculate"], 4),
            40: (["11.8"], ["11.8-S12"], ["recall"], 2),
        },
    ),
    "0620_w22_qp_21": (
        "ON",
        21,
        {
            1: (["1.1"], ["1.1-C3"], ["recall"], 2),
            2: (["12.3"], ["12.3-S4"], ["calculate"], 3),
            3: (["12.4"], ["12.4-C2"], ["recall"], 3),
            4: (["2.3"], ["2.3-S3"], ["recall"], 2),
            5: (["2.7"], ["2.7-S2"], ["recall"], 3),
            6: (["2.4"], ["2.4-C4"], ["recall"], 2),
            7: (["2.6"], ["2.6-S4"], ["recall"], 2),
            8: (["3.1"], ["3.1-C2"], ["recall"], 3),
            9: (["3.3"], ["3.3-S5"], ["calculate"], 4),
            10: (["4.1"], ["4.1-C2"], ["recall"], 2),
            11: (["5.1", "7.1"], ["5.1-C1", "7.1-C8"], ["recall"], 2),
            12: (["11.3"], ["11.3-C3"], ["data-analysis"], 3),
            13: (["5.1"], ["5.1-S8"], ["calculate"], 4),
            14: (["6.2"], ["6.2-C4", "6.2-S6"], ["data-analysis"], 3),
            15: (["6.3"], ["6.3-S4"], ["explain"], 3),
            16: (["6.4"], ["6.4-C3", "6.4-S6"], ["recall"], 3),
            17: (["7.3"], ["7.3-C1"], ["recall"], 3),
            18: (["7.1"], ["7.1-S9"], ["recall"], 3),
            19: (["7.3"], ["7.3-C1"], ["recall"], 2),
            20: (["7.2"], ["7.2-C1"], ["recall"], 3),
            21: (["8.2"], ["8.2-C2"], ["recall"], 3),
            22: (["8.2"], ["8.2-C1"], ["data-analysis"], 3),
            23: (["8.4"], ["8.4-C1", "8.4-S2"], ["recall"], 2),
            24: (["9.6"], ["9.6-S5"], ["recall"], 3),
            25: (["12.5"], ["12.5-C3"], ["data-analysis"], 3),
            26: (["9.3"], ["9.3-C1"], ["recall"], 3),
            27: (["9.5"], ["9.5-S4"], ["recall"], 1),
            28: (["10.1"], ["10.1-C7"], ["recall"], 2),
            29: (["10.3"], ["10.3-C3"], ["recall"], 2),
            30: (["6.3"], ["6.3-S11"], ["explain"], 3),
            31: (["6.3"], ["6.3-S10"], ["recall"], 2),
            32: (["10.3"], ["10.3-C2"], ["recall"], 3),
            33: (["9.6"], ["9.6-C2"], ["recall"], 2),
            34: (["11.2"], ["11.2-C1"], ["recall"], 1),
            35: (["11.1"], ["11.1-S8"], ["recall"], 2),
            36: (["11.1"], ["11.1-S9"], ["recall"], 2),
            37: (["11.5"], ["11.5-S6"], ["recall"], 3),
            38: (["11.7"], ["11.7-S2"], ["recall"], 2),
            39: (["11.8"], ["11.8-S10"], ["recall"], 3),
            40: (["11.8"], ["11.8-S8"], ["recall"], 3),
        },
    ),
    "0620_w22_qp_22": (
        "ON",
        22,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 3),
            2: (["1.1"], ["1.1-C2"], ["recall"], 3),
            3: (["12.3"], ["12.3-C2"], ["data-analysis"], 3),
            4: (["2.3"], ["2.3-S3"], ["recall"], 2),
            5: (["2.4"], ["2.4-S7"], ["recall"], 3),
            6: (["2.5"], ["2.5-C1"], ["recall"], 3),
            7: (["2.7"], ["2.7-S1"], ["recall"], 2),
            8: (["3.1"], ["3.1-C2"], ["recall"], 3),
            9: (["3.3"], ["3.3-S2", "3.3-S3"], ["calculate"], 3),
            10: (["4.1"], ["4.1-S10", "4.1-C3"], ["recall"], 3),
            11: (["5.1", "7.1"], ["5.1-C1", "7.1-C8"], ["recall"], 2),
            12: (["11.3"], ["11.3-C3"], ["data-analysis"], 3),
            13: (["9.4"], ["9.4-C3"], ["data-analysis"], 3),
            14: (["4.1"], ["4.1-S10"], ["recall"], 3),
            15: (["6.2"], ["6.2-C4"], ["data-analysis"], 3),
            16: (["6.3"], ["6.3-S4"], ["explain"], 3),
            17: (["6.4"], ["6.4-C3"], ["recall"], 3),
            18: (["7.2"], ["7.2-C1"], ["data-analysis"], 3),
            19: (["7.1"], ["7.1-S9"], ["recall"], 3),
            20: (["7.3"], ["7.3-C1", "7.3-S4"], ["recall"], 3),
            21: (["8.2", "8.3"], ["8.2-C1", "8.3-C3"], ["recall"], 3),
            22: (["8.1"], ["8.1-C2"], ["recall"], 3),
            23: (["8.4"], ["8.4-C1"], ["recall"], 2),
            24: (["9.4"], ["9.4-S4"], ["data-analysis"], 3),
            25: (["9.5", "9.3"], ["9.5-C1", "9.3-C3"], ["data-analysis"], 3),
            26: (["9.4"], ["9.4-C2"], ["recall"], 2),
            27: (["9.5", "9.3"], ["9.5-S4", "9.3-C1"], ["recall"], 3),
            28: (["10.1"], ["10.1-C7"], ["recall"], 2),
            29: (["10.3"], ["10.3-C3"], ["recall"], 2),
            30: (["7.1", "10.2"], ["7.1-C4", "10.2-C1"], ["recall"], 3),
            31: (["6.3"], ["6.3-S10"], ["recall"], 2),
            32: (["10.3"], ["10.3-C2"], ["recall"], 3),
            33: (["9.6"], ["9.6-C2"], ["recall"], 2),
            34: (["11.1"], ["11.1-S9"], ["recall"], 3),
            35: (["11.4"], ["11.4-S4"], ["recall"], 3),
            36: (["11.5"], ["11.5-S6"], ["recall"], 3),
            37: (["11.7"], ["11.7-S2"], ["recall"], 2),
            38: (["11.8"], ["11.8-S12"], ["recall"], 3),
            39: (["11.5"], ["11.5-C1"], ["recall"], 2),
            40: (["11.8"], ["11.8-S8"], ["recall"], 3),
        },
    ),
    "0620_w22_qp_23": (
        "ON",
        23,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 3),
            2: (["12.3"], ["12.3-S4"], ["data-analysis"], 2),
            3: (["2.4"], ["2.4-S5"], ["recall"], 2),
            4: (["2.2"], ["2.2-C5"], ["recall"], 3),
            5: (["2.3"], ["2.3-S3"], ["recall"], 2),
            6: (["2.5"], ["2.5-C1"], ["calculate"], 3),
            7: (["2.6"], ["2.6-C2"], ["recall"], 3),
            8: (["3.1"], ["3.1-C2"], ["recall"], 3),
            9: (["3.3"], ["3.3-S5"], ["calculate"], 3),
            10: (["4.1"], ["4.1-C7"], ["recall"], 2),
            11: (["5.1"], ["5.1-C1"], ["recall"], 2),
            12: (["11.3"], ["11.3-C3"], ["data-analysis"], 3),
            13: (["6.3"], ["6.3-S4"], ["explain"], 3),
            14: (["6.2"], ["6.2-C4"], ["data-analysis"], 3),
            15: (["6.3"], ["6.3-C2"], ["recall"], 2),
            16: (["6.4"], ["6.4-C3"], ["recall"], 3),
            17: (["5.1"], ["5.1-S8"], ["calculate"], 4),
            18: (["7.1"], ["7.1-S9"], ["recall"], 3),
            19: (["12.5"], ["12.5-C2"], ["data-analysis"], 3),
            20: (["7.1", "6.3"], ["7.1-S9", "6.3-S3"], ["recall"], 3),
            21: (["8.2", "8.3"], ["8.2-C1", "8.3-C1"], ["compare"], 3),
            22: (["8.4"], ["8.4-S2"], ["recall"], 2),
            23: (["8.1"], ["8.1-C2"], ["recall"], 3),
            24: (["9.6"], ["9.6-C1"], ["recall"], 3),
            25: (["9.4"], ["9.4-C2"], ["recall"], 3),
            26: (["3.3"], ["3.3-S5"], ["calculate"], 4),
            27: (["6.3"], ["6.3-S5", "6.3-S6"], ["recall"], 3),
            28: (["10.1"], ["10.1-C7"], ["recall"], 2),
            29: (["10.3"], ["10.3-C3"], ["recall"], 2),
            30: (["10.3"], ["10.3-S8"], ["explain"], 3),
            31: (["6.3"], ["6.3-S10"], ["recall"], 2),
            32: (["10.3"], ["10.3-C2"], ["recall"], 3),
            33: (["9.6"], ["9.6-C2"], ["recall"], 2),
            34: (["11.2"], ["11.2-S4"], ["recall"], 3),
            35: (["11.1"], ["11.1-C2"], ["recall"], 2),
            36: (["11.5"], ["11.5-S6"], ["recall"], 2),
            37: (["11.4"], ["11.4-S3"], ["recall"], 2),
            38: (["11.8"], ["11.8-S8"], ["recall"], 3),
            39: (["11.8"], ["11.8-S7"], ["recall"], 3),
            40: (["11.8"], ["11.8-S8"], ["recall"], 3),
        },
    ),
    "0620_m22_qp_22": (
        "FM",
        22,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 2),
            2: (["1.1"], ["1.1-C2"], ["recall"], 3),
            3: (["2.3"], ["2.3-S3"], ["recall"], 2),
            4: (["2.4"], ["2.4-S6"], ["recall"], 3),
            5: (["12.4"], ["12.4-C1"], ["recall"], 2),
            6: (["2.7"], ["2.7-S2"], ["recall"], 2),
            7: (["2.6"], ["2.6-C1", "2.6-C2"], ["compare"], 3),
            8: (["3.1"], ["3.1-C4"], ["recall"], 3),
            9: (["3.3"], ["3.3-S7"], ["calculate"], 4),
            10: (["2.4"], ["2.4-C4"], ["recall"], 2),
            11: (["4.1"], ["4.1-S8"], ["recall"], 3),
            12: (["3.3"], ["3.3-S5"], ["calculate"], 3),
            13: (["4.1"], ["4.1-S10", "4.1-C4"], ["recall"], 3),
            14: (["4.1"], ["4.1-C7"], ["recall"], 2),
            15: (["5.1"], ["5.1-C2"], ["recall"], 2),
            16: (["4.2"], ["4.2-S2"], ["recall"], 3),
            17: (["5.1"], ["5.1-S7"], ["recall"], 3),
            18: (["6.3"], ["6.3-S3"], ["recall"], 2),
            19: (["6.2"], ["6.2-S5"], ["recall"], 3),
            20: (["7.1"], ["7.1-C2"], ["recall"], 2),
            21: (["7.2"], ["7.2-S2", "7.2-S3"], ["recall"], 2),
            22: (["7.3"], ["7.3-S4"], ["recall"], 3),
            23: (["7.1"], ["7.1-S10", "7.1-C8"], ["recall"], 3),
            24: (["8.5"], ["8.5-C1"], ["recall"], 1),
            25: (["9.4"], ["9.4-C1"], ["recall"], 3),
            26: (["9.6"], ["9.6-S5"], ["recall"], 3),
            27: (["9.3"], ["9.3-C1"], ["recall"], 1),
            28: (["8.4"], ["8.4-C1"], ["data-analysis"], 3),
            29: (["6.3"], ["6.3-S6", "6.3-S7"], ["recall"], 3),
            30: (["7.1"], ["7.1-S9"], ["recall"], 4),
            31: (["6.3"], ["6.3-S10"], ["recall"], 2),
            32: (["10.3"], ["10.3-C2", "10.3-S7"], ["recall"], 3),
            33: (["11.2"], ["11.2-S4"], ["recall"], 3),
            34: (["10.3"], ["10.3-C4"], ["recall"], 3),
            35: (["11.2"], ["11.2-S3"], ["recall"], 3),
            36: (["11.8"], ["11.8-S7"], ["recall"], 3),
            37: (["11.7"], ["11.7-S2"], ["recall"], 2),
            38: (["11.5"], ["11.5-S6"], ["recall"], 2),
            39: (["11.6"], ["11.6-C3"], ["recall"], 3),
            40: (["11.8"], ["11.8-S10"], ["recall"], 3),
        },
    ),
}

SEASON = {"MJ": "s22", "ON": "w22", "FM": "m22"}


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


def tag_paper(
    paper_id: str,
    session: str,
    paper: int,
    tags: dict[int, tuple[list[str], list[str], list[str], int]],
    code_titles: dict[str, str],
    lo_texts: dict[str, str],
) -> int:
    draft = ROOT / "draft" / paper_id
    tagged = draft / "tagged"
    qp = f"raw/papers/{paper_id}.pdf"
    season = SEASON[session]
    ms = f"raw/papers/0620_{season}_ms_{paper}.pdf"
    sess_slug = session.lower()
    ms_key = json.loads((draft / "ms_key.json").read_text(encoding="utf-8"))
    tagged.mkdir(parents=True, exist_ok=True)
    bad: list[tuple[int, str, str]] = []
    if set(tags) != set(range(1, 41)):
        print(f"{paper_id}: TAGS must be 1..40, got {sorted(tags)}")
        return 1
    for q, (codes, lo_ids, skills, diff) in tags.items():
        for c in codes:
            if c not in code_titles:
                bad.append((q, "code", c))
        for lo in lo_ids:
            if lo not in lo_texts:
                bad.append((q, "lo", lo))
        body = (draft / f"q{q}.txt").read_text(encoding="utf-8")
        if "\n--- MARK SCHEME ---" in body:
            body = body.split("\n--- MARK SCHEME ---", 1)[0].strip()
        for marker in ("The Periodic Table", "Important values", "reasonable effort has been made"):
            if marker in body:
                body = body.split(marker)[0].strip()
        ans = str(ms_key[str(q)])
        if ans not in "ABCD":
            print(f"{paper_id} q{q}: bad ms letter {ans!r}")
            return 1
        rec = {
            "id": f"cie-0620-2022-{sess_slug}-p{paper}-q{q}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2022,
            "session": session,
            "paper": paper,
            "question": str(q),
            "marks": 1,
            "syllabus_codes": codes,
            "topic_titles": [code_titles[c] for c in codes],
            "skills": skills,
            "question_type": "mcq",
            "difficulty": diff,
            "command_words": [],
            "misconceptions": [],
            "learning_outcomes": lo_ids,
            "learning_outcome_texts": [lo_texts[i] for i in lo_ids],
            "learning_objectives": [],
            "ms_answer": ans,
            "source_qp": qp,
            "source_ms": ms,
            "page_qp": None,
            "body": body,
            "mark_scheme": f"Answer: **{ans}**",
        }
        (tagged / f"q{q}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if bad:
        print(f"INVALID TAGS {paper_id}:", bad)
        return 1
    letters = "".join(ms_key[str(i)] for i in range(1, 41))
    print(f"{paper_id}: wrote 40 tagged JSON  ms_key={letters}")
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
