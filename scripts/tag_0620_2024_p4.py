#!/usr/bin/env python3
"""Hand-tag IGCSE 0620 2024 P4 structured variants from 0620 vocabulary.

Assessed skill, not list decoration. year=2024.
P4 export MUST use ``chembank export-vault --no-refresh`` after
``scripts/repair_0620_2024_p4_split.py`` — ``ingest --export`` re-extracts
BEL-glued question numbers and collapses the paper into Q1.
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
    "0620_s24_qp_41": (
        "MJ",
        41,
        {
            "1a": (["6.3"], ["6.3-S8", "6.3-S10"], ["recall"], 2),
            "1b": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "1c": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "1d": (["11.3"], ["11.3-C5"], ["recall"], 2),
            "1e": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "1f": (["11.5"], ["11.5-C2"], ["recall"], 2),
            "1g": (["12.3"], ["12.3-C1"], ["recall"], 2),
            "2a": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["calculate"], 3),
            "3a": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3b-i": (["2.7"], ["2.7-S2"], ["explain"], 3),
            "3b-ii": (["2.5"], ["2.5-C2"], ["draw"], 3),
            "3b-iii": (["1.1"], ["1.1-C1", "1.1-C3"], ["explain"], 3),
            "3b-iv": (["2.4", "2.5"], ["2.4-S7", "2.5-S5"], ["explain"], 4),
            "3c-i": (["4.1"], ["4.1-C1"], ["recall"], 2),
            "3c-ii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "4a": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "4b-i": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4b-ii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4c": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4d": (["6.4"], ["6.4-S9"], ["recall"], 3),
            "4e-i": (["8.4"], ["8.4-C1"], ["recall"], 2),
            "4e-ii": (["6.3"], ["6.3-S4"], ["recall"], 2),
            "4e-iii": (["6.2"], ["6.2-S7"], ["recall"], 2),
            "5a-i": (["7.3"], ["7.3-S4", "7.3-C2"], ["recall"], 3),
            "5a-ii": (["7.3", "12.4"], ["7.3-S4", "12.4-C1"], ["recall"], 3),
            "5a-iii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "5b": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "5c": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5d-i": (["7.3", "12.1"], ["7.3-S5", "12.1-C2"], ["explain"], 3),
            "5d-ii": (["3.3", "7.3"], ["3.3-S3", "7.3-S5"], ["calculate"], 4),
            "6a-i": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-ii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-iii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-iv": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-v": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6b-i": (["1.1"], ["1.1-C1"], ["explain"], 3),
            "6b-ii": (["1.1"], ["1.1-C3"], ["recall"], 2),
            "6c-i": (["9.5"], ["9.5-S4"], ["recall"], 2),
            "6c-ii": (["9.5"], ["9.5-S5"], ["explain"], 3),
            "6d-i": (["7.2"], ["7.2-S2"], ["recall"], 2),
            "6d-ii": (["3.1"], ["3.1-S6"], ["recall"], 3),
            "6d-iii": (["7.1", "3.1"], ["7.1-C1", "3.1-C1"], ["recall"], 2),
            "7a-i": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "7a-ii": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "7b": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "7c": (["11.5", "3.1"], ["11.5-C2", "3.1-C4"], ["recall"], 3),
            "7d-i": (["11.1"], ["11.1-S8"], ["recall"], 2),
            "7d-ii": (["11.7", "11.2"], ["11.7-S3", "11.2-S4"], ["recall"], 3),
            "7d-iii": (["11.2", "11.1"], ["11.2-S3", "11.1-C1"], ["draw"], 3),
        },
    ),
    "0620_s24_qp_42": (
        "MJ",
        42,
        {
            "1a-i": (["11.3"], ["11.3-C2"], ["recall"], 1),
            "1a-ii": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "1a-iii": (["11.5"], ["11.5-C1"], ["recall"], 2),
            "1a-iv": (["8.5"], ["8.5-C1"], ["recall"], 2),
            "1a-v": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1b": (["10.3"], ["10.3-S8"], ["recall"], 3),
            "2a-i": (["2.4"], ["2.4-C2"], ["recall"], 2),
            "2a-ii": (["9.4"], ["9.4-C1"], ["recall"], 2),
            "2a-iii": (["8.4"], ["8.4-C1"], ["recall"], 2),
            "2a-iv": (["9.3"], ["9.3-C1"], ["recall"], 2),
            "2b": (["9.4"], ["9.4-C3"], ["recall"], 3),
            "2c-i": (["9.4"], ["9.4-C2"], ["recall"], 2),
            "2c-ii": (["9.4"], ["9.4-C2"], ["recall"], 2),
            "2c-iii": (["9.4"], ["9.4-C2"], ["recall"], 3),
            "2d": (["3.1"], ["3.1-S7", "3.1-C4"], ["recall"], 4),
            "3a": (["6.3"], ["6.3-S5"], ["recall"], 1),
            "3b": (["5.1"], ["5.1-C1"], ["recall"], 2),
            "3c": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "3d": (["6.2"], ["6.2-C3", "6.2-C1"], ["recall"], 2),
            "3e": (["5.1"], ["5.1-S8"], ["calculate"], 4),
            "3f-i": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3f-ii": (["3.1"], ["3.1-C1"], ["recall"], 1),
            "3f-iii": (["3.3"], ["3.3-S4", "3.3-S3"], ["calculate"], 4),
            "4a": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "4b": (["11.7"], ["11.7-S3"], ["recall"], 3),
            "4c": (["11.7"], ["11.7-S3", "11.2-S3"], ["draw"], 3),
            "4d": (["11.6"], ["11.6-C1", "11.2-S3"], ["recall"], 3),
            "4e": (["6.3"], ["6.3-S4"], ["data-analysis"], 4),
            "4f-i": (["7.1"], ["7.1-C1"], ["explain"], 3),
            "4f-ii": (["7.1"], ["7.1-C1"], ["recall"], 2),
            "4f-iii": (["7.1"], ["7.1-C5"], ["recall"], 2),
            "5a-i": (["2.2"], ["2.2-C3", "2.2-C4"], ["recall"], 2),
            "5a-ii": (["2.3"], ["2.3-S3"], ["explain"], 2),
            "5a-iii": (["3.3"], ["3.3-S2"], ["recall"], 2),
            "5a-iv": (["3.3"], ["3.3-S2"], ["recall"], 1),
            "5a-v": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "5b-i": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "5b-ii": (["2.4"], ["2.4-S7"], ["explain"], 3),
            "5b-iii": (["2.4"], ["2.4-C4"], ["explain"], 2),
            "5c-i": (["7.1"], ["7.1-C1", "3.1-C1"], ["recall"], 3),
            "5c-ii": (["3.1"], ["3.1-C1"], ["recall"], 2),
            "5d-i": (["6.4"], ["6.4-C1"], ["recall"], 2),
            "5d-ii": (["6.4"], ["6.4-S12"], ["recall"], 2),
            "6a-i": (["10.3"], ["10.3-C5"], ["recall"], 1),
            "6a-ii": (["10.3"], ["10.3-S9"], ["recall"], 2),
            "6a-iii": (["10.3"], ["10.3-C5"], ["recall"], 2),
            "6b-i": (["11.6"], ["11.6-C1"], ["recall"], 1),
            "6b-ii": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "6c-i": (["11.6"], ["11.6-S4"], ["recall"], 2),
            "6c-ii": (["11.5"], ["11.5-S5"], ["explain"], 3),
            "6c-iii": (["2.5"], ["2.5-C2"], ["draw"], 3),
        },
    ),
    "0620_s24_qp_43": (
        "MJ",
        43,
        {
            "1a": (["6.3"], ["6.3-S5"], ["recall"], 2),
            "1b": (["4.1"], ["4.1-C1", "4.1-C3"], ["recall"], 2),
            "1c": (["12.4"], ["12.4-C1"], ["recall"], 1),
            "1d": (["11.6"], ["11.6-S4"], ["recall"], 2),
            "1e": (["12.3"], ["12.3-C1"], ["recall"], 1),
            "1f": (["11.3"], ["11.3-C5"], ["recall"], 2),
            "1g": (["12.2"], ["12.2-C1"], ["recall"], 2),
            "2a": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["calculate"], 3),
            "3a-i": (["2.6"], ["2.6-C2"], ["explain"], 3),
            "3a-ii": (["2.5"], ["2.5-C2"], ["draw"], 3),
            "3a-iii": (["1.1"], ["1.1-C1", "1.1-C3"], ["explain"], 3),
            "3a-iv": (["2.6", "2.5"], ["2.6-C1", "2.5-S5"], ["explain"], 4),
            "3b": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3c-i": (["4.1"], ["4.1-C1"], ["recall"], 2),
            "3c-ii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "4a": (["6.3"], ["6.3-S4"], ["recall"], 2),
            "4b": (["1.1"], ["1.1-S6"], ["explain"], 3),
            "4c": (["6.3"], ["6.3-S7"], ["explain"], 3),
            "4d-i": (["6.3", "6.2"], ["6.3-S6", "6.2-C2"], ["data-analysis"], 4),
            "4d-ii": (["6.4"], ["6.4-C1"], ["recall"], 3),
            "5a-i": (["7.3"], ["7.3-S4", "7.3-C2"], ["recall"], 3),
            "5a-ii": (["7.3", "12.4"], ["7.3-S4", "12.4-C1"], ["recall"], 3),
            "5a-iii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "5b": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "5c-i": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "5c-ii": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5d-i": (["7.3"], ["7.3-S5"], ["explain"], 3),
            "5d-ii": (["3.3"], ["3.3-S3", "7.3-S5"], ["calculate"], 4),
            "6a-i": (["9.6"], ["9.6-C1"], ["recall"], 2),
            "6a-ii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-iii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-iv": (["9.6"], ["9.6-C3"], ["explain"], 3),
            "6b-i": (["8.2"], ["8.2-C1"], ["recall"], 3),
            "6b-ii": (["8.4"], ["8.4-C1"], ["recall"], 3),
            "6b-iii": (["9.1"], ["9.1-C1"], ["recall"], 2),
            "6b-iv": (["7.2"], ["7.2-S2"], ["recall"], 3),
            "6c-i": (["9.5"], ["9.5-S5"], ["explain"], 3),
            "6c-ii": (["9.5"], ["9.5-S5"], ["recall"], 2),
            "7a-i": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "7a-ii": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "7b-i": (["11.5"], ["11.5-C1", "11.8-C1"], ["recall"], 2),
            "7b-ii": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "7c": (["11.5"], ["11.5-C2", "3.1-C4"], ["recall"], 3),
            "7d-i": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "7d-ii": (["11.6", "11.2"], ["11.6-C1", "11.2-S3"], ["draw"], 3),
        },
    ),
    "0620_w24_qp_41": (
        "ON",
        41,
        {
            "1a": (["7.1"], ["7.1-C1"], ["recall"], 1),
            "1b": (["6.3"], ["6.3-C1", "6.3-S3"], ["recall"], 2),
            "1c": (["1.1"], ["1.1-C2", "1.1-C3"], ["recall"], 2),
            "1d": (["6.1"], ["6.1-C1"], ["recall"], 2),
            "1e": (["1.2"], ["1.2-C1"], ["recall"], 2),
            "2a": (["2.2"], ["2.2-C4"], ["recall"], 1),
            "2b": (["2.2"], ["2.2-C6"], ["recall"], 2),
            "2c": (["2.2"], ["2.2-C5"], ["recall"], 2),
            "2d": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["calculate"], 3),
            "2e-i": (["2.3"], ["2.3-C1"], ["recall"], 1),
            "2e-ii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2e-iii": (["2.3"], ["2.3-S3"], ["explain"], 2),
            "3a": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3b": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "3c": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "3d-i": (["7.3"], ["7.3-C3"], ["recall"], 1),
            "3d-ii": (["3.1"], ["3.1-C1"], ["recall"], 2),
            "3d-iii": (["7.3"], ["7.3-S5"], ["recall"], 3),
            "3e-i": (["4.1"], ["4.1-C2"], ["explain"], 2),
            "3e-ii": (["4.1"], ["4.1-C3"], ["recall"], 3),
            "3e-iii": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "3e-iv": (["4.1"], ["4.1-S9"], ["recall"], 2),
            "3e-v": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "3e-vi": (["4.1"], ["4.1-S9"], ["compare"], 4),
            "4a-i": (["6.4"], ["6.4-C1"], ["recall"], 3),
            "4a-ii": (["6.4"], ["6.4-S8"], ["recall"], 2),
            "4a-iii": (["3.3"], ["3.3-S4", "3.3-S3"], ["calculate"], 4),
            "4b": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "4c": (["2.5"], ["2.5-C2"], ["draw"], 3),
            "5a-i": (["4.2"], ["4.2-C1"], ["recall"], 2),
            "5a-ii": (["4.2"], ["4.2-S2"], ["recall"], 3),
            "5b-i": (["11.3"], ["11.3-C5"], ["recall"], 2),
            "5b-ii": (["11.5"], ["11.5-C2"], ["recall"], 2),
            "5c": (["3.3"], ["3.3-S2", "3.3-S3"], ["calculate"], 4),
            "5d": (["11.1"], ["11.1-C4", "11.1-S9"], ["recall"], 3),
            "5e-i": (["11.3"], ["11.3-C3"], ["recall"], 1),
            "5e-ii": (["11.5"], ["11.5-C1"], ["recall"], 2),
            "5e-iii": (["11.5"], ["11.5-S6"], ["recall"], 2),
            "5e-iv": (["11.5"], ["11.5-S5"], ["explain"], 3),
            "6a": (["11.8"], ["11.8-S9", "11.8-S12"], ["recall"], 2),
            "6b": (["11.8"], ["11.8-S12"], ["recall"], 1),
            "6c": (["11.8"], ["11.8-S12"], ["draw"], 3),
            "6d": (["11.8"], ["11.8-S13"], ["draw"], 4),
            "6e": (["12.3"], ["12.3-S4"], ["recall"], 2),
            "6f-i": (["12.3"], ["12.3-C1"], ["explain"], 2),
            "6f-ii": (["12.3"], ["12.3-C1"], ["recall"], 2),
            "6f-iii": (["12.3"], ["12.3-C2"], ["explain"], 3),
            "6f-iv": (["12.3"], ["12.3-C2"], ["recall"], 3),
        },
    ),
    "0620_w24_qp_42": (
        "ON",
        42,
        {
            "1a": (["2.5"], ["2.5-S4"], ["recall"], 2),
            "1b": (["10.3"], ["10.3-C5"], ["recall"], 2),
            "1c": (["11.3"], ["11.3-C1"], ["recall"], 2),
            "1d": (["12.5"], ["12.5-C3"], ["recall"], 1),
            "1e": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "1f": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "1g": (["11.5"], ["11.5-C1"], ["recall"], 2),
            "1h-i": (["6.3"], ["6.3-S6"], ["recall"], 2),
            "2a": (["9.6"], ["9.6-S5"], ["recall"], 1),
            "2b": (["9.6"], ["9.6-S5"], ["recall"], 2),
            "2c": (["4.1"], ["4.1-C2"], ["explain"], 3),
            "2d-i": (["9.6"], ["9.6-S5", "4.1-S11"], ["recall"], 3),
            "2d-ii": (["6.4"], ["6.4-S6"], ["explain"], 2),
            "2d-iii": (["9.6"], ["9.6-S5"], ["explain"], 3),
            "2e": (["9.2"], ["9.2-C1"], ["recall"], 2),
            "2f": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "3a": (["2.5"], ["2.5-S5"], ["explain"], 3),
            "3b": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3c": (["2.5"], ["2.5-C2"], ["draw"], 3),
            "3d": (["6.3"], ["6.3-S4"], ["explain"], 4),
            "3e-i": (["5.1"], ["5.1-C3"], ["recall"], 1),
            "3e-ii": (["5.1"], ["5.1-C3"], ["recall"], 1),
            "3e-iii": (["6.2"], ["6.2-S6", "6.2-S5"], ["data-analysis"], 4),
            "3f": (["6.4"], ["6.4-S8", "6.4-S6"], ["explain"], 4),
            "4a": (["7.3"], ["7.3-S4", "3.1-S7"], ["recall"], 2),
            "4b": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "4c": (["3.3"], ["3.3-C1"], ["calculate"], 2),
            "4d": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "4e": (["3.3"], ["3.3-S3"], ["calculate"], 3),
            "4f": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "4g-i": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "4g-ii": (["12.4"], ["12.4-C2"], ["recall"], 3),
            "4h-i": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "4h-ii": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5a": (["11.3"], ["11.3-C4"], ["recall"], 2),
            "5b": (["11.5"], ["11.5-C2"], ["recall"], 2),
            "5c-i": (["11.5"], ["11.5-C2", "3.1-C4"], ["recall"], 3),
            "5c-ii": (["11.5"], ["11.5-C3"], ["recall"], 2),
            "5d-i": (["11.8"], ["11.8-C2"], ["recall"], 2),
            "5d-ii": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "5d-iii": (["11.8"], ["11.8-C1"], ["recall"], 2),
            "6a-i": (["11.8"], ["11.8-S6"], ["recall"], 2),
            "6a-ii": (["11.8"], ["11.8-S8"], ["draw"], 3),
            "6a-iii": (["11.8"], ["11.8-S9"], ["recall"], 2),
            "6a-iv": (["11.8"], ["11.8-S12"], ["recall"], 1),
            "6a-v": (["11.8"], ["11.8-S12"], ["recall"], 2),
            "6a-vi": (["11.8"], ["11.8-S12"], ["draw"], 3),
            "6b-i": (["11.8"], ["11.8-S8"], ["recall"], 2),
            "6b-ii": (["11.8"], ["11.8-S10"], ["draw"], 3),
        },
    ),
    "0620_w24_qp_43": (
        "ON",
        43,
        {
            "1a": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "1b": (["8.5"], ["8.5-C1"], ["recall"], 2),
            "1c": (["10.3"], ["10.3-C5"], ["recall"], 2),
            "1d": (["9.6"], ["9.6-S5"], ["recall"], 2),
            "1e": (["9.6"], ["9.6-C1"], ["recall"], 2),
            "1f": (["6.3"], ["6.3-S6"], ["recall"], 3),
            "1g": (["2.6"], ["2.6-C1"], ["recall"], 2),
            "1h-i": (["12.5"], ["12.5-C3"], ["recall"], 1),
            "2a": (["4.1"], ["4.1-C1"], ["recall"], 1),
            "2b-i": (["4.1"], ["4.1-C3", "4.1-S9"], ["recall"], 3),
            "2b-ii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "2c-i": (["4.1"], ["4.1-S9"], ["explain"], 3),
            "2c-ii": (["4.1"], ["4.1-S9"], ["recall"], 2),
            "2c-iii": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "3a": (["3.3"], ["3.3-S8"], ["calculate"], 2),
            "3b-i": (["7.2"], ["7.2-S3"], ["recall"], 2),
            "3b-ii": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "3c": (["2.4", "2.5"], ["2.4-C4", "2.5-C1"], ["explain"], 3),
            "3d-i": (["2.5"], ["2.5-C2"], ["draw"], 3),
            "3d-ii": (["2.4", "2.5"], ["2.4-S7", "2.5-S5"], ["explain"], 4),
            "3e-i": (["9.4"], ["9.4-S5"], ["explain"], 3),
            "3e-ii": (["9.4"], ["9.4-C3"], ["recall"], 3),
            "3f-i": (["7.3"], ["7.3-C3"], ["recall"], 1),
            "3f-ii": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "4a-i": (["7.1"], ["7.1-C5"], ["recall"], 2),
            "4a-ii": (["12.2"], ["12.2-C2"], ["explain"], 3),
            "4b": (["3.3"], ["3.3-S6"], ["calculate"], 4),
            "4c": (["7.3"], ["7.3-S5"], ["recall"], 3),
            "4d": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "4e-i": (["7.1"], ["7.1-C6"], ["recall"], 1),
            "4e-ii": (["7.1"], ["7.1-C1"], ["recall"], 2),
            "4f-i": (["3.3"], ["3.3-S5"], ["explain"], 4),
            "4f-ii": (["3.3"], ["3.3-S2", "3.3-S4"], ["calculate"], 4),
            "5a-i": (["6.2"], ["6.2-C3"], ["explain"], 2),
            "5a-ii": (["6.2"], ["6.2-C1"], ["explain"], 2),
            "5a-iii": (["6.2"], ["6.2-S8"], ["explain"], 3),
            "5b-i": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "5b-ii": (["6.2"], ["6.2-C4"], ["data-analysis"], 3),
            "5c-i": (["6.4"], ["6.4-C1"], ["recall"], 2),
            "5c-ii": (["6.2"], ["6.2-C2"], ["recall"], 1),
            "5d-i": (["6.3"], ["6.3-S3"], ["explain"], 3),
            "5d-ii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "5d-iii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "6a": (["11.3"], ["11.3-C3"], ["recall"], 1),
            "6b-i": (["11.1"], ["11.1-C1"], ["recall"], 2),
            "6b-ii": (["11.5"], ["11.5-C2"], ["recall"], 2),
            "6c-i": (["11.5"], ["11.5-C1"], ["recall"], 1),
            "6c-ii": (["11.5"], ["11.5-S6"], ["recall"], 3),
            "6d-i": (["3.3"], ["3.3-S7"], ["calculate"], 2),
            "6d-ii": (["11.8"], ["11.8-C1"], ["recall"], 2),
            "6d-iii": (["11.8"], ["11.8-S7"], ["draw"], 3),
        },
    ),
    "0620_m24_qp_42": (
        "FM",
        42,
        {
            "1a-i": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1a-ii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1b-i": (["3.3"], ["3.3-S8"], ["calculate"], 3),
            "1b-ii": (["9.6"], ["9.6-C1"], ["recall"], 1),
            "1b-iii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1b-iv": (["9.6"], ["9.6-C2", "3.1-C4"], ["recall"], 3),
            "1b-v": (["6.4"], ["6.4-S8"], ["recall"], 2),
            "1c": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "1d-i": (["7.1"], ["7.1-S9"], ["explain"], 3),
            "1d-ii": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "1e-i": (["9.4"], ["9.4-C1"], ["explain"], 3),
            "1e-ii": (["9.6"], ["9.6-S5"], ["recall"], 2),
            "1f-i": (["2.2"], ["2.2-C5"], ["recall"], 2),
            "1f-ii": (["2.2"], ["2.2-C3", "2.3-C2"], ["recall"], 2),
            "2a": (["8.3"], ["8.3-C1"], ["recall"], 2),
            "2b": (["8.3"], ["8.3-C2"], ["recall"], 1),
            "2c": (["8.1"], ["8.1-C1", "8.3-C4"], ["recall"], 3),
            "2d-i": (["2.5"], ["2.5-C1"], ["recall"], 1),
            "2d-ii": (["8.3"], ["8.3-C3"], ["recall"], 2),
            "2d-iii": (["8.3"], ["8.3-C3"], ["explain"], 3),
            "2e": (["10.1"], ["10.1-C1"], ["recall"], 2),
            "2f": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "2g-i": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "2g-ii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "2g-iii": (["7.3"], ["7.3-C2"], ["recall"], 2),
            "3a": (["7.1"], ["7.1-S9"], ["recall"], 2),
            "3b": (["7.1"], ["7.1-C3"], ["recall"], 2),
            "3c": (["7.1"], ["7.1-C5"], ["recall"], 2),
            "3d-i": (["7.1"], ["7.1-C7"], ["data-analysis"], 3),
            "3d-ii": (["7.1"], ["7.1-C7"], ["recall"], 2),
            "3e": (["7.1"], ["7.1-S10"], ["recall"], 3),
            "3f": (["7.1"], ["7.1-C8"], ["recall"], 2),
            "3g": (["3.3"], ["3.3-S6"], ["calculate"], 4),
            "4a-i": (["11.1"], ["11.1-C1"], ["recall"], 2),
            "4a-ii": (["3.3"], ["3.3-S7"], ["recall"], 2),
            "4b": (["11.7"], ["11.7-S3", "11.2-S4"], ["draw"], 3),
            "4c-i": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "4c-ii": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "4c-iii": (["6.3"], ["6.3-S4"], ["data-analysis"], 4),
            "5a": (["1.2"], ["1.2-S2"], ["explain"], 3),
            "5b": (["11.4"], ["11.4-C2"], ["recall"], 2),
            "5c-i": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5c-ii": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5c-iii": (["11.4"], ["11.4-S3"], ["recall"], 2),
            "5c-iv": (["11.1"], ["11.1-S8"], ["recall"], 3),
            "5d-i": (["6.2"], ["6.2-C2"], ["recall"], 2),
            "5d-ii": (["11.5"], ["11.5-S6"], ["draw"], 3),
            "5e-i": (["11.8"], ["11.8-C1"], ["recall"], 2),
            "5e-ii": (["11.8"], ["11.8-S7"], ["draw"], 3),
        },
    ),
}

SEASON = {"MJ": "s24", "ON": "w24", "FM": "m24"}


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
    for old in tagged.glob("q*.json"):
        old.unlink()
    idx = json.loads((draft / "index.json").read_text(encoding="utf-8"))
    rows = [r for r in idx if r.get("part_slug") or r.get("file")]
    slugs = []
    for r in rows:
        slug = r.get("part_slug") or str(r.get("question"))
        slugs.append(slug)
        r["_slug"] = slug
    missing = sorted(set(slugs) - set(tags))
    extra = sorted(set(tags) - set(slugs))
    if missing or extra:
        print(f"{paper_id}: TAG mismatch missing={missing} extra={extra}")
        return 1
    season = SEASON[session]
    qp = f"raw/papers/{paper_id}.pdf"
    ms = f"raw/papers/0620_{season}_ms_{paper}.pdf"
    sess_slug = session.lower()
    bad: list[tuple[str, str, str]] = []
    for r in rows:
        slug = r["_slug"]
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
            "id": f"cie-0620-2024-{sess_slug}-p{paper}-q{slug}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2024,
            "session": session,
            "paper": paper,
            "question": slug if not str(slug).isdigit() else str(slug),
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
            "parent_question": r.get("parent_question") or (str(slug)[0] if slug else None),
            "part": r.get("part"),
            "_retag": "assessed-skill-2024-p4",
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
