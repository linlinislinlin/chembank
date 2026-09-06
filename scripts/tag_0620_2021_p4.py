#!/usr/bin/env python3
"""Hand-tag IGCSE 0620 2021 P4 structured variants from 0620 vocabulary.

Assessed skill, not list decoration. year=2021.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SYL = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

PAPERS: dict[str, tuple[str, int, dict[str, tuple[list[str], list[str], list[str], int]]]] = {
    "0620_s21_qp_41": (
        "MJ",
        41,
        {
            "1a": (["6.3"], ["6.3-S5"], ["recall"], 2),
            "1b": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "1c": (["4.1"], ["4.1-C1"], ["recall"], 2),
            "1d": (["12.4"], ["12.4-C1"], ["recall"], 1),
            "1e": (["11.8"], ["11.8-S12"], ["recall"], 3),
            "1f": (["12.3"], ["12.3-S3"], ["recall"], 2),
            "2": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["data-analysis"], 3),
            "3a": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3b": (["2.4"], ["2.4-C3"], ["draw"], 3),
            "3c-i": (["4.1"], ["4.1-C1"], ["recall"], 2),
            "3c-ii": (["4.1"], ["4.1-C5"], ["recall"], 2),
            "3d-i": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "3d-ii": (["4.1"], ["4.1-S10"], ["recall"], 2),
            "3d-iii": (["4.1"], ["4.1-S10"], ["recall"], 3),
            "3e": (["2.5"], ["2.5-C2"], ["draw"], 2),
            "3f-i": (["1.1"], ["1.1-C1"], ["explain"], 3),
            "3f-ii": (["2.4", "2.5"], ["2.4-S7", "2.5-S5"], ["explain"], 4),
            "4a": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "4b-i": (["6.3"], ["6.3-S4"], ["explain"], 4),
            "4b-ii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4c-i": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4c-ii": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "5a": (["7.3"], ["7.3-S4"], ["practical"], 4),
            "5b-i": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "5b-ii": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5c-i": (["7.3"], ["7.3-C3"], ["practical"], 3),
            "5c-ii": (["3.3"], ["3.3-S7"], ["calculate"], 4),
            "6a-i": (["9.6"], ["9.6-C2"], ["recall"], 1),
            "6a-ii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-iii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-iv": (["9.6"], ["9.6-C2"], ["recall"], 3),
            "6b": (["3.1"], ["3.1-S6"], ["recall"], 3),
            "6c-i": (["8.4"], ["8.4-C1", "8.4-S2"], ["compare"], 3),
            "6c-ii": (["9.1"], ["9.1-C1"], ["compare"], 2),
            "6d-i": (["9.5"], ["9.5-S5"], ["explain"], 3),
            "6d-ii": (["9.5"], ["9.5-S5"], ["explain"], 3),
            "7a": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "7b": (["3.3"], ["3.3-S7"], ["calculate"], 2),
            "7c-i": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "7c-ii": (["11.2", "11.1"], ["11.2-S3", "11.1-C1"], ["draw"], 3),
            "7c-iii": (["11.1"], ["11.1-C4"], ["recall"], 1),
            "7d-i": (["11.5"], ["11.5-C4"], ["recall"], 2),
            "7d-ii": (["11.5"], ["11.5-C2"], ["recall"], 3),
            "7d-iii": (["11.8"], ["11.8-C2"], ["recall"], 2),
            "7d-iv": (["11.8"], ["11.8-S7"], ["draw"], 3),
        },
    ),
    "0620_s21_qp_42": (
        "MJ",
        42,
        {
            "1a": (["9.1"], ["9.1-C1"], ["recall"], 1),
            "1b": (["2.2"], ["2.2-C6"], ["recall"], 2),
            "1c": (["10.3"], ["10.3-C2"], ["recall"], 2),
            "1d": (["8.1"], ["8.1-C5"], ["recall"], 2),
            "1e": (["9.6"], ["9.6-C3"], ["recall"], 1),
            "1f": (["8.5"], ["8.5-C1"], ["recall"], 2),
            "1g": (["2.6"], ["2.6-S3"], ["recall"], 2),
            "1h": (["7.2"], ["7.2-S3"], ["recall"], 2),
            "1i": (["8.3"], ["8.3-C1"], ["recall"], 2),
            "1j": (["7.1"], ["7.1-S11"], ["recall"], 3),
            "2a-i": (["2.3"], ["2.3-C1"], ["recall"], 1),
            "2a-ii": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["data-analysis"], 3),
            "2a-iii": (["3.2"], ["3.2-C1"], ["recall"], 2),
            "2a-iv": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2b": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "2c-i": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "2c-ii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "2d": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "2e": (["11.4"], ["11.4-S4"], ["recall"], 3),
            "2f-i": (["11.4"], ["11.4-C2"], ["recall"], 2),
            "2f-ii": (["11.4"], ["11.4-S4"], ["recall"], 3),
            "3a": (["6.1"], ["6.1-C1"], ["recall"], 2),
            "3b": (["3.3"], ["3.3-S4", "3.3-S5"], ["calculate"], 4),
            "3c": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "4a": (["4.1"], ["4.1-C2"], ["recall"], 1),
            "4b-i": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "4b-ii": (["6.4"], ["6.4-S6"], ["explain"], 3),
            "4c": (["4.1"], ["4.1-C3"], ["recall"], 2),
            "4d": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "4e-i": (["4.1"], ["4.1-S10"], ["recall"], 3),
            "4e-ii": (["4.1", "7.1"], ["4.1-S10", "7.1-C5"], ["explain"], 3),
            "4f": (["4.1"], ["4.1-C3"], ["recall"], 2),
            "5a-i": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "5a-ii": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "5b-i": (["5.1"], ["5.1-S8"], ["calculate"], 4),
            "5b-ii": (["5.1"], ["5.1-S4"], ["explain"], 2),
            "5b-iii": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "5c": (["2.4", "2.5"], ["2.4-S7", "2.5-S5"], ["explain"], 4),
            "5d-i": (["3.3"], ["3.3-S8"], ["calculate"], 3),
            "5d-ii": (["10.2"], ["10.2-C1"], ["recall"], 1),
            "5d-iii": (["7.1"], ["7.1-C4"], ["recall"], 2),
            "5e-i": (["7.1"], ["7.1-S9"], ["recall"], 2),
            "5e-ii": (["7.1"], ["7.1-C7"], ["recall"], 2),
            "6a-i": (["11.1"], ["11.1-C3"], ["recall"], 1),
            "6a-ii": (["11.8"], ["11.8-S8"], ["draw"], 4),
            "6a-iii": (["11.8"], ["11.8-S9"], ["recall"], 2),
            "6b-i": (["11.8"], ["11.8-S6"], ["draw"], 3),
            "6b-ii": (["11.8"], ["11.8-S12"], ["recall"], 3),
            "6b-iii": (["12.3"], ["12.3-S3"], ["recall"], 2),
            "6c-i": (["11.6"], ["11.6-C1"], ["recall"], 1),
            "6c-ii": (["11.6"], ["11.6-C1"], ["recall"], 3),
        },
    ),
    "0620_s21_qp_43": (
        "MJ",
        43,
        {
            "1a": (["11.8"], ["11.8-C1"], ["recall"], 1),
            "1b": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "1c": (["11.6"], ["11.6-C1"], ["recall"], 1),
            "1d": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "1e": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "1f": (["12.3"], ["12.3-S3"], ["recall"], 2),
            "1g": (["12.4"], ["12.4-C1"], ["recall"], 1),
            "2": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["data-analysis"], 3),
            "3a": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3b": (["2.4"], ["2.4-C3"], ["draw"], 3),
            "3c-i": (["4.1"], ["4.1-C1"], ["recall"], 2),
            "3c-ii": (["4.1"], ["4.1-S10"], ["recall"], 3),
            "3d-i": (["4.1"], ["4.1-C5"], ["recall"], 2),
            "3d-ii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "3e": (["2.5"], ["2.5-C2"], ["draw"], 2),
            "3f-i": (["1.1"], ["1.1-C1"], ["explain"], 3),
            "3f-ii": (["2.4", "2.5"], ["2.4-S7", "2.5-S5"], ["explain"], 4),
            "4a": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "4b-i": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4b-ii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4c-i": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4c-ii": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "5a": (["7.3"], ["7.3-C1"], ["practical"], 4),
            "5b-i": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "5b-ii": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5c-i": (["7.3"], ["7.3-C3"], ["practical"], 3),
            "5c-ii": (["3.3"], ["3.3-S7"], ["calculate"], 4),
            "6a-i": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-ii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-iii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-iv": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "6a-v": (["9.6"], ["9.6-C2"], ["recall"], 3),
            "6b-i": (["9.6"], ["9.6-C1"], ["recall"], 3),
            "6b-ii": (["1.1"], ["1.1-C3"], ["recall"], 2),
            "6c": (["9.3"], ["9.3-C1"], ["recall"], 1),
            "6d-i": (["8.4"], ["8.4-C1", "8.4-S2"], ["compare"], 3),
            "6d-ii": (["9.1"], ["9.1-C1"], ["compare"], 2),
            "7a": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "7b": (["3.3"], ["3.3-S7"], ["calculate"], 2),
            "7c-i": (["11.1"], ["11.1-S8"], ["recall"], 2),
            "7c-ii": (["11.1"], ["11.1-C4"], ["recall"], 2),
            "7c-iii": (["11.2"], ["11.2-S4"], ["draw"], 3),
            "7c-iv": (["11.2"], ["11.2-S3"], ["draw"], 3),
            "7d": (["11.5", "11.6"], ["11.5-C2", "11.6-C1"], ["recall"], 4),
        },
    ),
    "0620_w21_qp_41": (
        "ON",
        41,
        {
            "1a-i": (["2.1"], ["2.1-C1"], ["recall"], 1),
            "1a-ii": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "1a-iii": (["9.3"], ["9.3-C1"], ["recall"], 1),
            "1a-iv": (["2.2"], ["2.2-C6"], ["recall"], 2),
            "1a-v": (["9.3"], ["9.3-C1"], ["recall"], 2),
            "1a-vi": (["8.4"], ["8.4-S2"], ["recall"], 3),
            "1b-i": (["9.6"], ["9.6-C1"], ["recall"], 2),
            "1b-ii": (["9.6"], ["9.6-C3"], ["recall"], 1),
            "1c": (["9.4"], ["9.4-S5"], ["explain"], 3),
            "1d": (["9.6"], ["9.6-C1"], ["recall"], 3),
            "1e-i": (["9.4"], ["9.4-S4"], ["recall"], 2),
            "1e-ii": (["9.4"], ["9.4-S4"], ["recall"], 2),
            "1e-iii": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "1e-iv": (["6.2"], ["6.2-C1"], ["recall"], 2),
            "2a-i": (["2.3"], ["2.3-C1"], ["recall"], 1),
            "2a-ii": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["data-analysis"], 3),
            "2a-iii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2b-i": (["10.1"], ["10.1-C1"], ["recall"], 2),
            "2b-ii": (["6.3"], ["6.3-C2"], ["recall"], 2),
            "2b-iii": (["6.3"], ["6.3-C2"], ["recall"], 2),
            "2b-iv": (["10.1"], ["10.1-C2"], ["recall"], 2),
            "2c-i": (["12.5"], ["12.5-C2"], ["recall"], 2),
            "2c-ii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "2d": (["3.3"], ["3.3-S4", "3.3-S5"], ["calculate"], 4),
            "2e": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "3a-i": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "3a-ii": (["6.4"], ["6.4-S6"], ["explain"], 3),
            "3b": (["4.1"], ["4.1-C3"], ["recall"], 2),
            "3c": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "3d-i": (["7.1"], ["7.1-C7"], ["recall"], 2),
            "3d-ii": (["4.1", "7.1"], ["4.1-S10", "7.1-C6"], ["explain"], 3),
            "3e": (["4.1"], ["4.1-C3"], ["recall"], 3),
            "3f": (["2.6"], ["2.6-C2"], ["recall"], 2),
            "4a": (["6.3"], ["6.3-S9"], ["recall"], 3),
            "4b-i": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "4b-ii": (["6.3"], ["6.3-S10"], ["recall"], 2),
            "4b-iii": (["6.3"], ["6.3-S10"], ["recall"], 1),
            "4b-iv": (["6.2"], ["6.2-C2"], ["recall"], 2),
            "4b-v": (["6.3"], ["6.3-S4"], ["explain"], 4),
            "4c": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5a": (["11.1"], ["11.1-C4"], ["recall"], 1),
            "5b": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "5c-i": (["11.5"], ["11.5-C4"], ["recall"], 2),
            "5c-ii": (["11.5"], ["11.5-S5"], ["recall"], 2),
            "5c-iii": (["11.5"], ["11.5-S6"], ["recall"], 3),
            "5c-iv": (["11.8"], ["11.8-C2"], ["recall"], 2),
            "5c-v": (["11.1", "11.2"], ["11.1-S8", "11.2-S3"], ["draw"], 3),
            "5d-i": (["3.1"], ["3.1-S5"], ["recall"], 2),
            "5d-ii": (["11.7"], ["11.7-C1"], ["recall"], 3),
            "5d-iii": (["11.7"], ["11.7-S3"], ["draw"], 3),
        },
    ),
    "0620_w21_qp_42": (
        "ON",
        42,
        {
            "1a": (["1.1"], ["1.1-C2"], ["recall"], 2),
            "1b-i": (["1.1"], ["1.1-C3"], ["compare"], 3),
            "1b-ii": (["1.1"], ["1.1-C3"], ["recall"], 2),
            "1c": (["1.1"], ["1.1-S5"], ["draw"], 3),
            "1d-i": (["12.1"], ["12.1-C3"], ["recall"], 1),
            "1d-ii": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "2a-i": (["7.1"], ["7.1-S10"], ["recall"], 2),
            "2a-ii": (["7.1"], ["7.1-S11"], ["recall"], 3),
            "2a-iii": (["7.1"], ["7.1-C2"], ["recall"], 2),
            "2b-i": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "2b-ii": (["3.3"], ["3.3-S5"], ["calculate"], 4),
            "3a": (["2.2"], ["2.2-C2"], ["recall"], 2),
            "3b": (["2.2", "2.3"], ["2.2-C3", "2.2-C4", "2.3-C2"], ["data-analysis"], 3),
            "4a": (["5.1"], ["5.1-S7"], ["explain"], 3),
            "4b-i": (["5.1"], ["5.1-S6"], ["draw"], 3),
            "4b-ii": (["6.2"], ["6.2-C2"], ["recall"], 2),
            "4c-i": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4c-ii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4d": (["5.1"], ["5.1-S8"], ["calculate"], 4),
            "4e": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "5a": (["2.7"], ["2.7-S1"], ["recall"], 3),
            "5b-i": (["9.1"], ["9.1-C1"], ["recall"], 1),
            "5b-ii": (["2.7"], ["2.7-S2"], ["explain"], 3),
            "5b-iii": (["9.2"], ["9.2-C1"], ["recall"], 2),
            "5c": (["8.4"], ["8.4-C1"], ["compare"], 3),
            "5d-i": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "5d-ii": (["8.2"], ["8.2-C2"], ["recall"], 3),
            "5d-iii": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "5d-iv": (["12.5"], ["12.5-C4"], ["recall"], 2),
            "5d-v": (["8.2"], ["8.2-C2"], ["recall"], 3),
            "5e-i": (["6.3"], ["6.3-S5"], ["recall"], 2),
            "5e-ii": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "6a": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "6b": (["11.3"], ["11.3-C3"], ["recall"], 2),
            "6c-i": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "6c-ii": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "6d": (["11.6"], ["11.6-C2"], ["recall"], 3),
            "6e-i": (["3.1"], ["3.1-S5"], ["recall"], 2),
            "6e-ii": (["11.7"], ["11.7-S3"], ["draw"], 3),
            "6e-iii": (["11.7"], ["11.7-S3"], ["recall"], 1),
            "6f-i": (["11.7"], ["11.7-S2"], ["recall"], 3),
            "6f-ii": (["11.7"], ["11.7-S2"], ["draw"], 3),
        },
    ),
    "0620_w21_qp_43": (
        "ON",
        43,
        {
            "1a": (["2.1"], ["2.1-C1"], ["recall"], 1),
            "1b": (["9.6"], ["9.6-C3"], ["recall"], 1),
            "1c": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "1d": (["11.6"], ["11.6-C3"], ["recall"], 2),
            "1e": (["2.4"], ["2.4-C4"], ["recall"], 2),
            "1f": (["6.3"], ["6.3-S5"], ["recall"], 1),
            "1g": (["10.3"], ["10.3-C2"], ["recall"], 2),
            "1h": (["10.3"], ["10.3-C2"], ["recall"], 2),
            "1i": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "2a": (["4.1"], ["4.1-C2"], ["recall"], 2),
            "2b-i": (["4.1"], ["4.1-C3", "4.1-S10"], ["data-analysis"], 3),
            "2b-ii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "2b-iii": (["2.6"], ["2.6-C2"], ["recall"], 2),
            "2b-iv": (["2.7"], ["2.7-S2"], ["recall"], 2),
            "3a": (["3.2"], ["3.2-C2"], ["calculate"], 2),
            "3b": (["3.3"], ["3.3-S8"], ["calculate"], 3),
            "3c": (["3.3"], ["3.3-S8"], ["compare"], 3),
            "3d": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3e": (["7.1"], ["7.1-C1"], ["recall"], 3),
            "3f-i": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "3f-ii": (["2.4", "2.5"], ["2.4-S7", "2.5-S5"], ["explain"], 4),
            "3g": (["9.4"], ["9.4-S4"], ["explain"], 3),
            "3h-i": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "3h-ii": (["9.4"], ["9.4-C1"], ["recall"], 3),
            "4a": (["2.3"], ["2.3-C1", "2.2-C4"], ["data-analysis"], 2),
            "4b": (["2.6"], ["2.6-C1"], ["recall"], 2),
            "4c-i": (["3.3"], ["3.3-S3"], ["calculate"], 3),
            "4c-ii": (["3.3"], ["3.3-S4"], ["calculate"], 3),
            "5a-i": (["12.2"], ["12.2-C2"], ["recall"], 2),
            "5a-ii": (["12.2"], ["12.2-C1"], ["recall"], 2),
            "5b": (["7.3"], ["7.3-C1"], ["practical"], 4),
            "5c-i": (["12.5"], ["12.5-C4"], ["recall"], 2),
            "5c-ii": (["7.1"], ["7.1-C1"], ["recall"], 3),
            "5c-iii": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "6a": (["6.2"], ["6.2-C2"], ["recall"], 2),
            "6b-i": (["6.2"], ["6.2-C4"], ["data-analysis"], 3),
            "6b-ii": (["6.2"], ["6.2-C3"], ["explain"], 3),
            "6c-i": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "6c-ii": (["6.2"], ["6.2-C4"], ["draw"], 3),
            "7a": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "7b-i": (["11.5"], ["11.5-C2"], ["recall"], 1),
            "7b-ii": (["11.5"], ["11.5-C2"], ["recall"], 3),
            "7b-iii": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "7b-iv": (["11.5"], ["11.5-S5"], ["recall"], 2),
            "7b-v": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "7c": (["11.6"], ["11.6-S4"], ["compare"], 3),
            "7d-i": (["11.4"], ["11.4-S3"], ["recall"], 3),
            "7d-ii": (["11.8"], ["11.8-C2"], ["recall"], 2),
            "7d-iii": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "7e": (["11.8"], ["11.8-S12"], ["draw"], 4),
        },
    ),
    "0620_m21_qp_42": (
        "FM",
        42,
        {
            "1a-i": (["2.4"], ["2.4-C1"], ["recall"], 2),
            "1a-ii": (["2.4"], ["2.4-C1"], ["recall"], 2),
            "1a-iii": (["8.5"], ["8.5-C1"], ["recall"], 2),
            "1a-iv": (["8.3"], ["8.3-C1"], ["recall"], 2),
            "1a-v": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "1a-vi": (["2.2"], ["2.2-C4"], ["data-analysis"], 3),
            "1a-vii": (["7.1"], ["7.1-C6"], ["recall"], 3),
            "1a-viii": (["3.2"], ["3.2-C1"], ["recall"], 2),
            "1b": (["2.3"], ["2.3-C1"], ["explain"], 2),
            "2a": (["8.3"], ["8.3-C2"], ["recall"], 1),
            "2b": (["8.3"], ["8.3-C1"], ["recall"], 2),
            "2c-i": (["1.2"], ["1.2-C1"], ["explain"], 2),
            "2c-ii": (["1.2"], ["1.2-S2"], ["explain"], 3),
            "2d-i": (["10.3"], ["10.3-C1"], ["recall"], 1),
            "2d-ii": (["10.3"], ["10.3-C1"], ["recall"], 2),
            "2d-iii": (["10.3"], ["10.3-C1"], ["recall"], 2),
            "2d-iv": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "3a-i": (["6.3"], ["6.3-S5"], ["recall"], 1),
            "3a-ii": (["6.3"], ["6.3-C1"], ["recall"], 2),
            "3a-iii": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "3a-iv": (["6.3"], ["6.3-S7"], ["recall"], 1),
            "3a-v": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "3a-vi": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "3b": (["10.2"], ["10.2-C1"], ["recall"], 3),
            "4a": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "4b": (["7.3"], ["7.3-C1"], ["explain"], 2),
            "4c": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "4d": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "4e": (["12.4"], ["12.4-C1"], ["explain"], 3),
            "4f": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "4g": (["9.4"], ["9.4-C2"], ["explain"], 3),
            "4h-i": (["12.2"], ["12.2-C1"], ["recall"], 2),
            "4h-ii": (["3.3"], ["3.3-S6"], ["calculate"], 4),
            "5a": (["11.1"], ["11.1-C6"], ["recall"], 2),
            "5b": (["11.5"], ["11.5-C4"], ["recall"], 2),
            "5c-i": (["11.2"], ["11.2-S3"], ["recall"], 2),
            "5c-ii": (["11.1"], ["11.1-S8"], ["draw"], 3),
            "5d-i": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "5d-ii": (["11.5"], ["11.5-C2"], ["recall"], 3),
            "5e": (["11.5"], ["11.5-S6"], ["recall"], 3),
            "5f-i": (["11.7"], ["11.7-S2"], ["recall"], 2),
            "5f-ii": (["11.7"], ["11.7-S2"], ["recall"], 2),
            "5g-i": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "5g-ii": (["11.7", "11.2"], ["11.7-S3", "11.2-S4"], ["draw"], 3),
            "5g-iii": (["3.1"], ["3.1-C2"], ["recall"], 2),
            "6a": (["11.8"], ["11.8-C1"], ["recall"], 1),
            "6b-i": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "6b-ii": (["11.8"], ["11.8-C2"], ["recall"], 2),
            "6c-i": (["11.8"], ["11.8-S12"], ["recall"], 2),
            "6c-ii": (["11.8"], ["11.8-S13"], ["draw"], 4),
            "6c-iii": (["11.8"], ["11.8-S12"], ["recall"], 3),
        },
    ),
}

SEASON = {"MJ": "s21", "ON": "w21", "FM": "m21"}
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


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
        body = CONTROL_RE.sub(" ", body).replace("\uf0b8", "/").strip()
        for marker in ("The Periodic Table of Elements", "The Periodic Table", "Important values"):
            if marker in body:
                body = body.split(marker)[0].strip()
        rec = {
            "id": f"cie-0620-2021-{sess_slug}-p{paper}-q{slug}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2021,
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
            "mark_scheme": CONTROL_RE.sub(" ", ms_text).strip(),
            "parent_question": r.get("parent_question") or (str(slug)[0] if slug else None),
            "part": r.get("part"),
            "_retag": "assessed-skill-2021-p4",
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
