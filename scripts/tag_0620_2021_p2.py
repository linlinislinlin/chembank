#!/usr/bin/env python3
"""Hand-tag IGCSE 0620 2021 P2 MCQ variants from the 0620 (2026–2028) vocabulary.

Assessed skill, not decorative context. year=2021; MJ=s21, ON=w21, FM=m21.
2021 sat the pre-2023 syllabus; nearest 2026–2028 leaf is used when the item
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
    "0620_s21_qp_21": (
        "MJ",
        21,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 3),
            2: (["12.4"], ["12.4-C1"], ["practical"], 2),
            3: (["12.3"], ["12.3-C1"], ["recall"], 2),
            4: (["2.2", "8.1"], ["2.2-C3", "2.2-C6"], ["data-analysis"], 3),
            5: (["2.5"], ["2.5-C2"], ["recall"], 3),
            6: (["2.6"], ["2.6-C1", "2.6-S3"], ["compare"], 3),
            7: (["2.7"], ["2.7-S2"], ["recall"], 3),
            8: (["2.4", "8.1"], ["2.4-S5", "8.1-C5"], ["compare"], 3),
            9: (["3.3"], ["3.3-S3"], ["calculate"], 4),
            10: (["4.1"], ["4.1-C3", "4.1-C4"], ["recall"], 3),
            11: (["4.1"], ["4.1-S11"], ["recall"], 3),
            12: (["5.1"], ["5.1-C3"], ["data-analysis"], 3),
            13: (["4.2"], ["4.2-C1"], ["recall"], 2),
            14: (["6.1"], ["6.1-C1"], ["recall"], 2),
            15: (["6.2"], ["6.2-S5", "6.2-S6"], ["explain"], 3),
            16: (["6.4"], ["6.4-S13", "6.4-S11"], ["explain"], 4),
            17: (["6.3"], ["6.3-S3"], ["recall"], 2),
            18: (["7.2"], ["7.2-C1"], ["data-analysis"], 3),
            19: (["7.3"], ["7.3-C1"], ["recall"], 2),
            20: (["8.1", "6.4"], ["8.1-C3", "6.4-S10"], ["data-analysis"], 4),
            21: (["7.1"], ["7.1-S9"], ["recall"], 3),
            22: (["8.5"], ["8.5-C1"], ["recall"], 2),
            23: (["8.4"], ["8.4-C1", "8.4-S2"], ["data-analysis"], 3),
            24: (["8.1", "2.5"], ["8.1-C3", "2.5-C1"], ["data-analysis"], 3),
            25: (["9.4"], ["9.4-C2", "9.4-C3"], ["data-analysis"], 4),
            26: (["8.2", "9.4"], ["8.2-C1", "9.4-C1"], ["data-analysis"], 3),
            27: (["9.6"], ["9.6-C3"], ["recall"], 2),
            28: (["9.3"], ["9.3-S5"], ["data-analysis"], 3),
            29: (["6.3"], ["6.3-S4", "6.3-S5"], ["explain"], 4),
            30: (["10.3"], ["10.3-C5"], ["recall"], 2),
            31: (["6.3"], ["6.3-S10"], ["recall"], 2),
            32: (["12.5", "7.1"], ["12.5-C1", "7.1-C1"], ["recall"], 3),
            33: (["11.7", "11.2"], ["11.7-C1", "11.2-S4"], ["recall"], 3),
            34: (["11.7"], ["11.7-S2"], ["recall"], 3),
            35: (["11.1"], ["11.1-C2", "11.1-S8"], ["compare"], 3),
            36: (["11.4"], ["11.4-C2"], ["recall"], 2),
            37: (["11.6"], ["11.6-S4"], ["recall"], 2),
            38: (["11.5", "11.1"], ["11.5-C1", "11.1-C6"], ["compare"], 3),
            39: (["11.8"], ["11.8-S10", "11.8-S9"], ["recall"], 3),
            40: (["11.8"], ["11.8-S12"], ["recall"], 2),
        },
    ),
    "0620_s21_qp_22": (
        "MJ",
        22,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 3),
            2: (["12.3"], ["12.3-S3"], ["recall"], 2),
            3: (["12.3"], ["12.3-C1"], ["recall"], 2),
            4: (["2.2", "8.1"], ["2.2-C3", "2.2-C6"], ["data-analysis"], 3),
            5: (["2.5"], ["2.5-C2"], ["recall"], 3),
            6: (["2.6", "2.4"], ["2.6-S3", "2.4-C4"], ["data-analysis"], 4),
            7: (["2.4"], ["2.4-C3"], ["recall"], 2),
            8: (["2.3"], ["2.3-C1"], ["data-analysis"], 3),
            9: (["3.3"], ["3.3-S2", "3.3-S5"], ["calculate"], 4),
            10: (["4.1"], ["4.1-C3", "4.1-C4"], ["recall"], 3),
            11: (["3.1"], ["3.1-C4"], ["recall"], 3),
            12: (["5.1"], ["5.1-C1"], ["data-analysis"], 3),
            13: (["6.2"], ["6.2-C1", "6.2-C4"], ["data-analysis"], 3),
            14: (["6.1"], ["6.1-C1"], ["recall"], 2),
            15: (["6.2"], ["6.2-S5", "6.2-S6"], ["explain"], 3),
            16: (["6.4"], ["6.4-S13", "6.4-S11"], ["explain"], 4),
            17: (["6.3"], ["6.3-S4"], ["explain"], 4),
            18: (["7.2"], ["7.2-C1"], ["data-analysis"], 3),
            19: (["7.3"], ["7.3-S4", "7.3-C2"], ["data-analysis"], 3),
            20: (["5.1"], ["5.1-S8"], ["calculate"], 4),
            21: (["7.1", "10.3"], ["7.1-C6", "10.3-C3"], ["recall"], 3),
            22: (["8.1", "2.2"], ["8.1-S6", "2.2-C6"], ["recall"], 3),
            23: (["8.2", "8.3"], ["8.2-C1", "8.3-C1"], ["compare"], 3),
            24: (["8.4"], ["8.4-S2"], ["recall"], 3),
            25: (["9.4"], ["9.4-S5"], ["explain"], 3),
            26: (["8.2", "9.4"], ["8.2-C1", "9.4-C1"], ["data-analysis"], 3),
            27: (["9.6"], ["9.6-S5"], ["recall"], 3),
            28: (["9.5", "9.3"], ["9.5-S4", "9.3-C1"], ["recall"], 3),
            29: (["10.1"], ["10.1-C7"], ["recall"], 2),
            30: (["6.3"], ["6.3-S6"], ["recall"], 2),
            31: (["6.3"], ["6.3-S7"], ["recall"], 2),
            32: (["10.3"], ["10.3-C5"], ["recall"], 2),
            33: (["9.6", "10.3"], ["9.6-C2", "10.3-C4"], ["recall"], 3),
            34: (["11.6", "11.7"], ["11.6-C1", "11.7-S3"], ["compare"], 3),
            35: (["11.1"], ["11.1-C2"], ["recall"], 2),
            36: (["11.4"], ["11.4-C2"], ["recall"], 2),
            37: (["11.7", "7.1"], ["11.7-C1", "7.1-S12"], ["recall"], 3),
            38: (["11.3", "11.5"], ["11.3-C5", "11.5-C2"], ["recall"], 3),
            39: (["11.8"], ["11.8-S10", "11.8-S9"], ["recall"], 3),
            40: (["11.8"], ["11.8-S12"], ["recall"], 2),
        },
    ),
    "0620_s21_qp_23": (
        "MJ",
        23,
        {
            1: (["1.2"], ["1.2-S2"], ["compare"], 3),
            2: (["1.1"], ["1.1-C2", "1.1-C3"], ["explain"], 3),
            3: (["12.3"], ["12.3-C1"], ["recall"], 2),
            4: (["2.2", "8.1"], ["2.2-C3", "2.2-C6"], ["data-analysis"], 3),
            5: (["2.5"], ["2.5-C2"], ["recall"], 3),
            6: (["2.7"], ["2.7-S2"], ["recall"], 3),
            7: (["2.3"], ["2.3-C1"], ["recall"], 2),
            8: (["2.6"], ["2.6-S4"], ["recall"], 3),
            9: (["6.4", "3.1"], ["6.4-C1", "3.1-S6"], ["data-analysis"], 3),
            10: (["4.1"], ["4.1-C3", "4.1-C4"], ["recall"], 3),
            11: (["3.3"], ["3.3-S3"], ["calculate"], 3),
            12: (["3.3"], ["3.3-S4"], ["recall"], 3),
            13: (["9.4"], ["9.4-S4"], ["compare"], 3),
            14: (["6.1"], ["6.1-C1"], ["recall"], 2),
            15: (["6.2"], ["6.2-S5", "6.2-S6"], ["explain"], 3),
            16: (["6.4"], ["6.4-S13", "6.4-S11"], ["explain"], 4),
            17: (["5.1"], ["5.1-S8"], ["calculate"], 4),
            18: (["7.2"], ["7.2-C1"], ["data-analysis"], 3),
            19: (["12.4", "7.3"], ["12.4-C1", "7.3-S4"], ["recall"], 2),
            20: (["2.6", "8.1"], ["2.6-S3", "8.1-C3"], ["recall"], 3),
            21: (["8.4"], ["8.4-S2"], ["recall"], 2),
            22: (["8.5"], ["8.5-C1"], ["explain"], 3),
            23: (["10.1"], ["10.1-C6"], ["recall"], 2),
            24: (["9.5"], ["9.5-S4", "9.5-S5"], ["explain"], 3),
            25: (["8.2", "9.4"], ["8.2-C1", "9.4-C1"], ["data-analysis"], 3),
            26: (["9.6", "10.3"], ["9.6-C2", "10.3-C2"], ["recall"], 3),
            27: (["10.3"], ["10.3-C3"], ["recall"], 2),
            28: (["6.3"], ["6.3-S4", "6.3-S5"], ["explain"], 4),
            29: (["9.6"], ["9.6-C2"], ["recall"], 3),
            30: (["6.3"], ["6.3-S10"], ["recall"], 2),
            31: (["9.2", "9.3"], ["9.2-C1", "9.3-C3"], ["recall"], 3),
            32: (["6.4"], ["6.4-S9"], ["calculate"], 3),
            33: (["9.6", "7.1"], ["9.6-C2", "7.1-C1"], ["recall"], 3),
            34: (["11.7"], ["11.7-S2"], ["recall"], 3),
            35: (["11.1"], ["11.1-S8"], ["compare"], 3),
            36: (["11.4"], ["11.4-C2"], ["recall"], 2),
            37: (["11.5", "3.3"], ["11.5-S6", "3.3-S4"], ["calculate"], 4),
            38: (["11.6"], ["11.6-S4"], ["compare"], 3),
            39: (["11.8"], ["11.8-S10", "11.8-S9"], ["recall"], 3),
            40: (["11.8"], ["11.8-S12"], ["recall"], 2),
        },
    ),
    "0620_w21_qp_21": (
        "ON",
        21,
        {
            1: (["1.1"], ["1.1-C3"], ["explain"], 3),
            2: (["12.1"], ["12.1-C1"], ["practical"], 2),
            3: (["12.1"], ["12.1-C3"], ["recall"], 2),
            4: (["2.7"], ["2.7-S2"], ["recall"], 2),
            5: (["9.3"], ["9.3-C1"], ["recall"], 1),
            6: (["3.3"], ["3.3-S3", "3.3-S5"], ["calculate"], 3),
            7: (["2.5"], ["2.5-S5"], ["recall"], 3),
            8: (["2.6"], ["2.6-C1", "2.6-C2"], ["recall"], 3),
            9: (["3.1"], ["3.1-S6"], ["recall"], 3),
            10: (["4.1"], ["4.1-C3", "4.1-S10"], ["recall"], 4),
            11: (["5.1"], ["5.1-S8"], ["calculate"], 4),
            12: (["4.2"], ["4.2-C1"], ["recall"], 3),
            13: (["6.2"], ["6.2-C1", "6.2-S6"], ["explain"], 3),
            14: (["6.3"], ["6.3-S4", "6.3-S5"], ["explain"], 4),
            15: (["6.3", "10.1"], ["6.3-C2", "10.1-C1"], ["recall"], 3),
            16: (["6.4"], ["6.4-S6", "6.4-S8"], ["explain"], 4),
            17: (["7.1"], ["7.1-S9", "7.1-C7"], ["recall"], 2),
            18: (["7.2"], ["7.2-S3"], ["recall"], 2),
            19: (["7.3"], ["7.3-C1"], ["recall"], 2),
            20: (["8.1"], ["8.1-S6"], ["explain"], 3),
            21: (["8.1", "2.2"], ["8.1-C5", "2.2-C6"], ["data-analysis"], 3),
            22: (["8.3"], ["8.3-C1"], ["data-analysis"], 3),
            23: (["8.2", "8.4"], ["8.2-C1", "8.4-S2"], ["compare"], 3),
            24: (["8.5"], ["8.5-C1"], ["explain"], 2),
            25: (["9.1"], ["9.1-C1"], ["recall"], 2),
            26: (["9.6"], ["9.6-C3"], ["recall"], 2),
            27: (["9.4"], ["9.4-S5"], ["explain"], 3),
            28: (["9.4", "6.4"], ["9.4-C1", "6.4-C3"], ["recall"], 3),
            29: (["9.5"], ["9.5-S4", "9.5-S5"], ["explain"], 4),
            30: (["6.3"], ["6.3-S6"], ["recall"], 3),
            31: (["6.3"], ["6.3-S9"], ["recall"], 2),
            32: (["7.1"], ["7.1-C4"], ["recall"], 3),
            33: (["11.5"], ["11.5-C2", "11.5-C4"], ["data-analysis"], 4),
            34: (["11.4"], ["11.4-C2"], ["recall"], 2),
            35: (["11.1", "11.4"], ["11.1-C5", "11.4-C1"], ["recall"], 2),
            36: (["11.4"], ["11.4-S4"], ["recall"], 3),
            37: (["11.8"], ["11.8-C1"], ["recall"], 2),
            38: (["11.5"], ["11.5-S5", "11.5-S6"], ["recall"], 3),
            39: (["11.7"], ["11.7-C1"], ["recall"], 3),
            40: (["11.8"], ["11.8-S8", "11.8-S10"], ["recall"], 4),
        },
    ),
    "0620_w21_qp_22": (
        "ON",
        22,
        {
            1: (["1.2"], ["1.2-S2"], ["explain"], 3),
            2: (["12.1"], ["12.1-C1"], ["practical"], 2),
            3: (["12.1"], ["12.1-C3"], ["recall"], 2),
            4: (["2.2"], ["2.2-C3", "2.2-C4"], ["recall"], 2),
            5: (["9.3"], ["9.3-C1"], ["recall"], 1),
            6: (["2.6"], ["2.6-S4"], ["recall"], 3),
            7: (["2.5"], ["2.5-S5"], ["recall"], 3),
            8: (["2.6"], ["2.6-C1"], ["recall"], 2),
            9: (["3.3"], ["3.3-S4", "3.3-S5"], ["calculate"], 4),
            10: (["4.1"], ["4.1-C6", "4.1-C7"], ["recall"], 3),
            11: (["5.1"], ["5.1-S8"], ["calculate"], 4),
            12: (["8.3"], ["8.3-C3"], ["recall"], 3),
            13: (["4.1"], ["4.1-S10", "4.1-S11"], ["recall"], 3),
            14: (["4.2"], ["4.2-C1"], ["recall"], 3),
            15: (["6.3", "10.1"], ["6.3-C2", "10.1-C1"], ["recall"], 2),
            16: (["6.4"], ["6.4-S6", "6.4-S8"], ["explain"], 4),
            17: (["7.1"], ["7.1-C1", "7.1-C4"], ["recall"], 3),
            18: (["7.2"], ["7.2-C1"], ["data-analysis"], 3),
            19: (["11.4"], ["11.4-S4"], ["recall"], 3),
            20: (["6.3"], ["6.3-S4"], ["explain"], 4),
            21: (["8.1", "2.2"], ["8.1-C5", "2.2-C6"], ["data-analysis"], 3),
            22: (["7.3"], ["7.3-S4", "7.3-C2"], ["data-analysis"], 3),
            23: (["8.4"], ["8.4-C1", "8.4-S2"], ["recall"], 3),
            24: (["8.5"], ["8.5-C1"], ["explain"], 2),
            25: (["9.1"], ["9.1-C1"], ["recall"], 2),
            26: (["9.6"], ["9.6-S5"], ["explain"], 3),
            27: (["9.4"], ["9.4-S5"], ["explain"], 3),
            28: (["9.5"], ["9.5-S4", "9.5-S5"], ["explain"], 3),
            29: (["6.3"], ["6.3-S7"], ["recall"], 2),
            30: (["10.3"], ["10.3-C3"], ["recall"], 3),
            31: (["6.3"], ["6.3-S9"], ["recall"], 3),
            32: (["7.1"], ["7.1-C4"], ["recall"], 3),
            33: (["11.7"], ["11.7-S3"], ["recall"], 3),
            34: (["11.4"], ["11.4-C2"], ["recall"], 2),
            35: (["11.1"], ["11.1-C3"], ["compare"], 3),
            36: (["11.5"], ["11.5-C2"], ["recall"], 3),
            37: (["11.6"], ["11.6-S4"], ["compare"], 3),
            38: (["11.5"], ["11.5-C1", "11.5-C4"], ["recall"], 3),
            39: (["11.8"], ["11.8-S12", "11.8-S10"], ["compare"], 3),
            40: (["11.8"], ["11.8-S8", "11.8-S10"], ["recall"], 4),
        },
    ),
    "0620_w21_qp_23": (
        "ON",
        23,
        {
            1: (["1.2"], ["1.2-C1", "1.2-S2"], ["data-analysis"], 3),
            2: (["12.1"], ["12.1-C1"], ["practical"], 2),
            3: (["12.1"], ["12.1-C3"], ["recall"], 2),
            4: (["2.2"], ["2.2-C3", "2.2-C4"], ["recall"], 3),
            5: (["9.3"], ["9.3-C1"], ["recall"], 1),
            6: (["2.4", "2.2"], ["2.4-C3", "2.2-C5"], ["recall"], 3),
            7: (["2.5"], ["2.5-S5"], ["recall"], 3),
            8: (["2.5"], ["2.5-S4"], ["recall"], 3),
            9: (["3.1"], ["3.1-S6"], ["recall"], 3),
            10: (["4.1"], ["4.1-C3"], ["recall"], 2),
            11: (["5.1"], ["5.1-C3"], ["data-analysis"], 3),
            12: (["5.1"], ["5.1-S8"], ["calculate"], 4),
            13: (["3.3"], ["3.3-C1", "3.3-S5"], ["calculate"], 3),
            14: (["4.2"], ["4.2-C1"], ["recall"], 2),
            15: (["6.3"], ["6.3-S4", "6.3-S8"], ["explain"], 4),
            16: (["6.4"], ["6.4-S6", "6.4-S8"], ["explain"], 4),
            17: (["6.2"], ["6.2-C1", "6.2-C4"], ["data-analysis"], 3),
            18: (["7.2"], ["7.2-C1"], ["recall"], 2),
            19: (["7.2"], ["7.2-S2"], ["data-analysis"], 3),
            20: (["7.1", "6.4"], ["7.1-S9", "6.4-S11"], ["recall"], 3),
            21: (["8.1", "2.2"], ["8.1-C5", "2.2-C6"], ["data-analysis"], 3),
            22: (["8.1"], ["8.1-C5"], ["data-analysis"], 3),
            23: (["8.4"], ["8.4-S2"], ["compare"], 3),
            24: (["8.5"], ["8.5-C1"], ["explain"], 2),
            25: (["9.1"], ["9.1-C1"], ["recall"], 2),
            26: (["9.4"], ["9.4-C2", "9.4-C3"], ["data-analysis"], 4),
            27: (["9.4"], ["9.4-S5"], ["explain"], 3),
            28: (["10.3"], ["10.3-S8"], ["recall"], 3),
            29: (["9.5"], ["9.5-S5"], ["explain"], 3),
            30: (["6.3"], ["6.3-S6"], ["recall"], 2),
            31: (["6.3"], ["6.3-S10"], ["recall"], 2),
            32: (["7.1"], ["7.1-C4"], ["recall"], 3),
            33: (["11.2", "11.6"], ["11.2-S3", "11.6-C1"], ["recall"], 3),
            34: (["11.4"], ["11.4-C2"], ["recall"], 2),
            35: (["11.3"], ["11.3-C2"], ["recall"], 1),
            36: (["11.1"], ["11.1-C4"], ["recall"], 2),
            37: (["11.1"], ["11.1-S8"], ["compare"], 3),
            38: (["11.5"], ["11.5-S6", "11.5-C1"], ["data-analysis"], 3),
            39: (["11.8"], ["11.8-S12", "11.8-S9"], ["recall"], 3),
            40: (["11.8"], ["11.8-S8", "11.8-S10"], ["recall"], 4),
        },
    ),
    "0620_m21_qp_22": (
        "FM",
        22,
        {
            1: (["1.1"], ["1.1-C3", "1.1-S5"], ["recall"], 2),
            2: (["12.4", "8.5"], ["12.4-C1", "8.5-C1"], ["data-analysis"], 3),
            3: (["12.3"], ["12.3-C2", "12.3-S4"], ["data-analysis"], 3),
            4: (["2.3"], ["2.3-C1", "2.3-S3"], ["recall"], 3),
            5: (["2.6"], ["2.6-S3"], ["recall"], 3),
            6: (["2.4", "2.1"], ["2.4-C1", "2.1-C1"], ["recall"], 3),
            7: (["2.5"], ["2.5-S4"], ["recall"], 3),
            8: (["2.4", "2.5"], ["2.4-S7", "2.5-S5"], ["compare"], 3),
            9: (["4.1"], ["4.1-S11"], ["recall"], 3),
            10: (["3.2"], ["3.2-C2"], ["calculate"], 3),
            11: (["9.2"], ["9.2-C1"], ["explain"], 3),
            12: (["4.1"], ["4.1-S11", "4.1-C3"], ["recall"], 3),
            13: (["5.1"], ["5.1-C2", "5.1-C3"], ["data-analysis"], 3),
            14: (["5.1"], ["5.1-S8"], ["calculate"], 4),
            15: (["4.2"], ["4.2-C1"], ["recall"], 3),
            16: (["6.2"], ["6.2-C3"], ["practical"], 2),
            17: (["10.1", "6.3"], ["10.1-C1", "6.3-C2"], ["recall"], 3),
            18: (["6.4"], ["6.4-S11", "6.4-C3"], ["recall"], 3),
            19: (["7.2"], ["7.2-C1"], ["recall"], 2),
            20: (["12.5"], ["12.5-C2"], ["recall"], 3),
            21: (["7.1"], ["7.1-S10"], ["recall"], 3),
            22: (["8.1", "2.4"], ["8.1-C5", "2.4-C3"], ["data-analysis"], 3),
            23: (["8.1"], ["8.1-S6"], ["data-analysis"], 3),
            24: (["9.4"], ["9.4-C3"], ["data-analysis"], 4),
            25: (["9.6"], ["9.6-S5"], ["recall"], 3),
            26: (["9.2", "9.3"], ["9.2-C1", "9.3-C1"], ["recall"], 3),
            27: (["9.4"], ["9.4-C2"], ["recall"], 3),
            28: (["8.4"], ["8.4-C1", "8.4-S2"], ["recall"], 2),
            29: (["10.3"], ["10.3-S8"], ["recall"], 3),
            30: (["10.2"], ["10.2-C2"], ["recall"], 3),
            31: (["10.3"], ["10.3-C5"], ["recall"], 2),
            32: (["10.3"], ["10.3-C2"], ["recall"], 3),
            33: (["9.6"], ["9.6-C2"], ["recall"], 3),
            34: (["11.4"], ["11.4-S4"], ["recall"], 3),
            35: (["11.3"], ["11.3-C2"], ["recall"], 1),
            36: (["11.5"], ["11.5-S5", "11.5-S6"], ["recall"], 3),
            37: (["11.4", "3.1"], ["11.4-C2", "3.1-C4"], ["calculate"], 3),
            38: (["11.7"], ["11.7-S3"], ["recall"], 3),
            39: (["11.8"], ["11.8-C1", "11.8-C3"], ["recall"], 2),
            40: (["11.8"], ["11.8-S12", "11.8-S13"], ["recall"], 3),
        },
    ),
}

SEASON = {"MJ": "s21", "ON": "w21", "FM": "m21"}


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
            "id": f"cie-0620-2021-{sess_slug}-p{paper}-q{q}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2021,
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
