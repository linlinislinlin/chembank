#!/usr/bin/env python3
"""Hand-tag IGCSE 0620 2023 P4 structured variants from 0620 vocabulary.

Assessed skill, not list decoration. year=2023.
Export with ``chembank export-vault --no-refresh`` so ingest does not re-split.
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
    "0620_s23_qp_41": (
        "MJ",
        41,
        {
            "1a": (["7.1"], ["7.1-C8"], ["recall"], 2),
            "1b": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "1c": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "1d": (["10.3"], ["10.3-S9"], ["recall"], 2),
            "1e": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "1f": (["11.5"], ["11.5-C2"], ["recall"], 2),
            "2a-i": (["10.3"], ["10.3-C1"], ["recall"], 2),
            "2a-ii": (["2.2"], ["2.2-C5"], ["recall"], 2),
            "2a-iii": (["2.2"], ["2.2-C3"], ["recall"], 2),
            "2a-iv": (["2.6"], ["2.6-C1"], ["recall"], 2),
            "2a-v": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "2a-vi": (["6.4", "8.5"], ["6.4-C1", "8.5-C1"], ["recall"], 2),
            "2b-i": (["2.3"], ["2.3-C1"], ["recall"], 2),
            "2b-ii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "3a-i": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "3a-ii": (["3.1"], ["3.1-S6"], ["recall"], 2),
            "3b": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "3c-i": (["2.4"], ["2.4-S7"], ["explain"], 3),
            "3c-ii": (["2.5"], ["2.5-S5"], ["recall"], 3),
            "4a": (["6.2"], ["6.2-C2"], ["recall"], 2),
            "4b-i": (["6.2"], ["6.2-C3"], ["explain"], 2),
            "4b-ii": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "4b-iii": (["6.2"], ["6.2-C4"], ["explain"], 2),
            "4c": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "4d": (["3.3"], ["3.3-S5"], ["calculate"], 4),
            "4e": (["6.2"], ["6.2-C2"], ["recall"], 2),
            "4f": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5a-i": (["4.1"], ["4.1-C1"], ["recall"], 2),
            "5a-ii": (["2.6"], ["2.6-C2"], ["recall"], 2),
            "5a-iii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "5a-iv": (["4.1"], ["4.1-S8"], ["recall"], 2),
            "5a-v": (["4.1"], ["4.1-S8"], ["recall"], 2),
            "5a-vi": (["4.1"], ["4.1-S10"], ["recall"], 3),
            "5b-i": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "5b-ii": (["9.6"], ["9.6-S5"], ["recall"], 3),
            "5b-iii": (["9.6"], ["9.6-S5"], ["explain"], 3),
            "5c-i": (["4.2"], ["4.2-C1"], ["recall"], 2),
            "5c-ii": (["4.2"], ["4.2-S2"], ["recall"], 2),
            "6a-i": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "6a-ii": (["6.4"], ["6.4-C1"], ["recall"], 2),
            "6b-i": (["6.3"], ["6.3-S4", "6.3-S11"], ["explain"], 4),
            "6b-ii": (["6.3"], ["6.3-S4", "6.3-S11"], ["explain"], 4),
            "6c": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "6d-i": (["7.3"], ["7.3-C2", "7.3-S4"], ["recall"], 3),
            "6d-ii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "6d-iii": (["7.3"], ["7.3-S4"], ["recall"], 3),
            "7a-i": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "7a-ii": (["11.1"], ["11.1-S8"], ["draw"], 3),
            "7b-i": (["3.1"], ["3.1-C2"], ["recall"], 2),
            "7b-ii": (["11.1"], ["11.1-C3"], ["recall"], 2),
            "7b-iii": (["11.5", "11.7"], ["11.5-C4", "11.7-C1"], ["recall"], 3),
            "7b-iv": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "7b-v": (["11.8"], ["11.8-S8"], ["recall"], 2),
        },
    ),
    "0620_s23_qp_42": (
        "MJ",
        42,
        {
            "1a": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "1b": (["2.6"], ["2.6-S3"], ["recall"], 2),
            "1c": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1d": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "1e": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1f": (["9.4"], ["9.4-C1"], ["recall"], 3),
            "2a": (["8.3"], ["8.3-C1"], ["recall"], 1),
            "2b": (["8.1"], ["8.1-C4"], ["explain"], 2),
            "2c": (["8.3"], ["8.3-C2"], ["recall"], 2),
            "2d-i": (["2.2"], ["2.2-C4"], ["recall"], 2),
            "2d-ii": (["2.2", "2.3"], ["2.2-C3", "2.3-C1"], ["recall"], 3),
            "2d-iii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2e-i": (["8.3"], ["8.3-C3"], ["recall"], 3),
            "2e-ii": (["8.3"], ["8.3-C1"], ["explain"], 2),
            "2f-i": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "2f-ii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "3a": (["6.3"], ["6.3-S8"], ["recall"], 1),
            "3b-i": (["6.3"], ["6.3-S9"], ["recall"], 2),
            "3b-ii": (["6.3"], ["6.3-S3"], ["recall"], 3),
            "3b-iii": (["6.3"], ["6.3-S10"], ["recall"], 3),
            "3b-iv": (["6.3"], ["6.3-S4"], ["explain"], 4),
            "3b-v": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "3c": (["6.4"], ["6.4-S9"], ["calculate"], 3),
            "4a": (["7.1"], ["7.1-S9"], ["recall"], 2),
            "4b": (["7.1"], ["7.1-C3"], ["recall"], 1),
            "4c": (["7.1"], ["7.1-C5"], ["recall"], 2),
            "4d": (["7.1"], ["7.1-C4"], ["recall"], 3),
            "4e-i": (["7.2"], ["7.2-S2"], ["recall"], 2),
            "4e-ii": (["7.2"], ["7.2-S3"], ["recall"], 2),
            "4f-i": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "4f-ii": (["7.1"], ["7.1-C7"], ["recall"], 2),
            "4f-iii": (["7.1"], ["7.1-S12"], ["recall"], 3),
            "4f-iv": (["7.1"], ["7.1-C8"], ["recall"], 2),
            "4g": (["3.3"], ["3.3-S6", "3.3-S5"], ["calculate"], 4),
            "5a-i": (["11.4"], ["11.4-S3"], ["recall"], 2),
            "5a-ii": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5a-iii": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5a-iv": (["11.4"], ["11.4-S4"], ["recall"], 3),
            "5b-i": (["11.1"], ["11.1-C6"], ["recall"], 2),
            "5b-ii": (["11.5"], ["11.5-S6"], ["recall"], 3),
            "5c": (["11.5"], ["11.5-S6"], ["draw"], 3),
            "6a": (["11.2"], ["11.2-S4"], ["recall"], 2),
            "6b": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "6c": (["3.1"], ["3.1-S5"], ["recall"], 3),
            "6d-i": (["11.8"], ["11.8-S6"], ["recall"], 3),
            "6d-ii": (["11.8"], ["11.8-S8"], ["draw"], 3),
            "6d-iii": (["11.8"], ["11.8-S10"], ["recall"], 2),
        },
    ),
    "0620_s23_qp_43": (
        "MJ",
        43,
        {
            "1a": (["10.3"], ["10.3-S9"], ["recall"], 2),
            "1b": (["11.5"], ["11.5-S6"], ["recall"], 2),
            "1c": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "1d": (["10.3"], ["10.3-C2"], ["recall"], 2),
            "1e": (["8.3"], ["8.3-C3"], ["recall"], 2),
            "1f": (["11.4"], ["11.4-S3"], ["recall"], 2),
            "2a-i": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "2a-ii": (["8.5"], ["8.5-C1"], ["recall"], 2),
            "2a-iii": (["10.1"], ["10.1-C7"], ["recall"], 2),
            "2a-iv": (["7.2"], ["7.2-S3"], ["recall"], 2),
            "2a-v": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "2a-vi": (["6.4"], ["6.4-S9"], ["recall"], 3),
            "2b-i": (["3.2"], ["3.2-C1"], ["recall"], 2),
            "2b-ii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2c-i": (["2.2"], ["2.2-C4"], ["recall"], 2),
            "2c-ii": (["2.2"], ["2.2-C3"], ["recall"], 2),
            "3a-i": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "3a-ii": (["3.1"], ["3.1-S6"], ["recall"], 2),
            "3a-iii": (["2.4"], ["2.4-S7"], ["explain"], 3),
            "3b": (["2.5"], ["2.5-C2"], ["draw"], 3),
            "3c-i": (["2.5"], ["2.5-S5"], ["recall"], 2),
            "3c-ii": (["2.5"], ["2.5-S5"], ["explain"], 3),
            "4a-i": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "4a-ii": (["6.2"], ["6.2-C4"], ["explain"], 2),
            "4b": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "4c": (["3.3"], ["3.3-S5", "3.3-S4"], ["calculate"], 4),
            "4d-i": (["7.1"], ["7.1-C1"], ["recall"], 3),
            "4d-ii": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "5a-i": (["4.1"], ["4.1-C2"], ["recall"], 2),
            "5a-ii": (["6.4"], ["6.4-C1"], ["recall"], 2),
            "5a-iii": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "5a-iv": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "5a-v": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "5b": (["4.1"], ["4.1-S9"], ["recall"], 3),
            "5c-i": (["4.1"], ["4.1-C6", "4.1-C7"], ["recall"], 3),
            "5c-ii": (["4.1"], ["4.1-C6"], ["recall"], 2),
            "5d-i": (["10.3"], ["10.3-C2"], ["recall"], 2),
            "5d-ii": (["4.2"], ["4.2-S2"], ["recall"], 2),
            "6a-i": (["6.3"], ["6.3-S6"], ["recall"], 2),
            "6a-ii": (["6.3"], ["6.3-S6"], ["recall"], 2),
            "6a-iii": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "6a-iv": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "6a-v": (["6.2"], ["6.2-C2"], ["recall"], 2),
            "6b-i": (["6.3"], ["6.3-S11"], ["explain"], 3),
            "6b-ii": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "6c-i": (["7.1"], ["7.1-C1"], ["recall"], 3),
            "6c-ii": (["7.3"], ["7.3-C1"], ["recall"], 3),
            "6c-iii": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "7a-i": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "7a-ii": (["11.1"], ["11.1-S8"], ["draw"], 3),
            "7b-i": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "7b-ii": (["11.1"], ["11.1-C1"], ["draw"], 3),
            "7c-i": (["11.8"], ["11.8-S8"], ["draw"], 3),
            "7c-ii": (["11.8"], ["11.8-S10"], ["recall"], 2),
            "7c-iii": (["11.8"], ["11.8-S9"], ["recall"], 2),
        },
    ),
    "0620_w23_qp_41": (
        "ON",
        41,
        {
            "1a": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "1b": (["7.1"], ["7.1-C3"], ["recall"], 2),
            "1c": (["8.5"], ["8.5-C1"], ["recall"], 2),
            "1d": (["10.3"], ["10.3-C5"], ["recall"], 2),
            "1e": (["11.8"], ["11.8-C2"], ["recall"], 2),
            "1f": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "2a": (["2.2"], ["2.2-C3", "2.2-C4"], ["recall"], 2),
            "2b-i": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2b-ii": (["3.3"], ["3.3-S3"], ["calculate"], 4),
            "2c-i": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "2c-ii": (["9.6"], ["9.6-S5"], ["recall"], 3),
            "2c-iii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "2c-iv": (["9.6"], ["9.6-S5"], ["explain"], 3),
            "2d": (["9.2"], ["9.2-C1"], ["recall"], 2),
            "2e": (["9.4"], ["9.4-S5"], ["explain"], 3),
            "2f-i": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "2f-ii": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "3a-i": (["9.4"], ["9.4-C3", "9.4-S4"], ["data-analysis"], 4),
            "3a-ii": (["7.3"], ["7.3-C2"], ["recall"], 3),
            "3a-iii": (["9.4"], ["9.4-S4"], ["recall"], 3),
            "3b-i": (["8.3"], ["8.3-C3"], ["recall"], 3),
            "3b-ii": (["8.3"], ["8.3-C3"], ["recall"], 3),
            "3b-iii": (["8.3"], ["8.3-C4"], ["recall"], 3),
            "4a": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "4b-i": (["6.2"], ["6.2-C4"], ["data-analysis"], 3),
            "4b-ii": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "4b-iii": (["6.2"], ["6.2-C1"], ["data-analysis"], 3),
            "4c": (["3.3"], ["3.3-S5", "3.3-S4"], ["calculate"], 4),
            "4d": (["8.4"], ["8.4-C1"], ["recall"], 2),
            "5a": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "5b-i": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "5b-ii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "5b-iii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "5c-i": (["10.3"], ["10.3-C1"], ["recall"], 2),
            "5c-ii": (["10.3"], ["10.3-S7"], ["explain"], 3),
            "6a": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "6b-i": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "6b-ii": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "6b-iii": (["11.5"], ["11.5-S5"], ["recall"], 2),
            "6c-i": (["7.1"], ["7.1-S9"], ["recall"], 2),
            "6c-ii": (["7.1"], ["7.1-S10"], ["recall"], 2),
            "6c-iii": (["6.4"], ["6.4-S9"], ["calculate"], 3),
            "6d": (["11.6"], ["11.6-S4"], ["compare"], 3),
            "6e-i": (["11.7"], ["11.7-S2"], ["recall"], 2),
            "6e-ii": (["6.4"], ["6.4-S12"], ["recall"], 3),
            "6f-i": (["11.7"], ["11.7-C1"], ["recall"], 2),
            "6f-ii": (["11.7"], ["11.7-C1"], ["recall"], 2),
            "6f-iii": (["11.7"], ["11.7-C1"], ["recall"], 2),
        },
    ),
    "0620_w23_qp_42": (
        "ON",
        42,
        {
            "1a": (["8.5"], ["8.5-C1"], ["recall"], 2),
            "1b": (["8.1"], ["8.1-C1"], ["recall"], 2),
            "1c": (["2.2"], ["2.2-C3"], ["recall"], 2),
            "1d": (["8.1"], ["8.1-C4"], ["recall"], 2),
            "1e": (["8.3"], ["8.3-C1"], ["recall"], 2),
            "1f": (["9.1"], ["9.1-C1"], ["recall"], 2),
            "1g": (["8.1"], ["8.1-C3"], ["recall"], 3),
            "1h": (["8.1"], ["8.1-C3"], ["recall"], 3),
            "2a-i": (["2.2"], ["2.2-C3", "2.2-C4"], ["recall"], 2),
            "2a-ii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2b": (["8.4"], ["8.4-C1"], ["compare"], 3),
            "2c-i": (["7.3"], ["7.3-S5"], ["recall"], 2),
            "2c-ii": (["6.3"], ["6.3-C2"], ["recall"], 2),
            "2c-iii": (["6.3"], ["6.3-C2"], ["recall"], 2),
            "2c-iv": (["6.3"], ["6.3-C2"], ["recall"], 2),
            "3a": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "3b-i": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "3b-ii": (["9.6"], ["9.6-S4"], ["recall"], 3),
            "3b-iii": (["6.4"], ["6.4-S9"], ["recall"], 3),
            "3b-iv": (["6.4"], ["6.4-S7"], ["explain"], 3),
            "3c": (["9.6"], ["9.6-S4"], ["recall"], 3),
            "3d-i": (["9.3"], ["9.3-C1"], ["recall"], 2),
            "3d-ii": (["9.3"], ["9.3-C1"], ["recall"], 2),
            "3e": (["9.5"], ["9.5-C1"], ["recall"], 2),
            "3f-i": (["9.5"], ["9.5-S4"], ["recall"], 2),
            "3f-ii": (["9.5"], ["9.5-C2"], ["recall"], 2),
            "3f-iii": (["9.5"], ["9.5-S5"], ["explain"], 3),
            "4a-i": (["7.3"], ["7.3-C2", "7.3-S4"], ["recall"], 3),
            "4a-ii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "4a-iii": (["7.3"], ["7.3-S4"], ["recall"], 3),
            "4b-i": (["2.4"], ["2.4-S7"], ["explain"], 3),
            "4b-ii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "4b-iii": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "4b-iv": (["4.1"], ["4.1-C3"], ["recall"], 2),
            "5a": (["5.1"], ["5.1-S4"], ["recall"], 2),
            "5b-i": (["5.1"], ["5.1-C1"], ["recall"], 2),
            "5b-ii": (["5.1"], ["5.1-C3"], ["data-analysis"], 3),
            "5b-iii": (["5.1"], ["5.1-S6"], ["draw"], 3),
            "5b-iv": (["5.1"], ["5.1-S5"], ["recall"], 2),
            "5b-v": (["6.2"], ["6.2-S7"], ["recall"], 2),
            "5c": (["5.1"], ["5.1-S8"], ["calculate"], 4),
            "6a": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "6b": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "6c-i": (["11.2"], ["11.2-C2"], ["recall"], 2),
            "6c-ii": (["11.1"], ["11.1-C1"], ["draw"], 3),
            "6d-i": (["11.8"], ["11.8-S12"], ["recall"], 3),
            "6d-ii": (["11.8"], ["11.8-S13"], ["draw"], 3),
        },
    ),
    "0620_w23_qp_43": (
        "ON",
        43,
        {
            "1a": (["12.5"], ["12.5-C4"], ["recall"], 2),
            "1b": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "1c": (["7.2"], ["7.2-C1"], ["recall"], 2),
            "1d": (["11.1"], ["11.1-C6"], ["recall"], 2),
            "1e": (["10.3"], ["10.3-C2"], ["recall"], 2),
            "1f": (["10.1"], ["10.1-C1"], ["recall"], 2),
            "2a-i": (["2.2"], ["2.2-C1"], ["recall"], 2),
            "2a-ii": (["2.4"], ["2.4-C1"], ["recall"], 2),
            "2a-iii": (["2.4"], ["2.4-C1"], ["recall"], 2),
            "2b": (["2.2"], ["2.2-C3"], ["recall"], 2),
            "2c": (["2.2"], ["2.2-C4"], ["recall"], 2),
            "2d": (["2.2"], ["2.2-C5"], ["recall"], 2),
            "2e": (["8.1"], ["8.1-C1"], ["recall"], 2),
            "2f": (["8.1"], ["8.1-C1"], ["recall"], 2),
            "3a-i": (["10.3"], ["10.3-C1"], ["recall"], 2),
            "3a-ii": (["6.3"], ["6.3-S6"], ["recall"], 2),
            "3a-iii": (["2.5"], ["2.5-C2"], ["draw"], 3),
            "3a-iv": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "3b-i": (["8.4"], ["8.4-C1"], ["recall"], 3),
            "3b-ii": (["6.4"], ["6.4-S9"], ["recall"], 3),
            "3b-iii": (["6.4"], ["6.4-S6"], ["recall"], 3),
            "3b-iv": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "3b-v": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "3c": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "4a-i": (["3.3"], ["3.3-S5"], ["recall"], 3),
            "4a-ii": (["7.3"], ["7.3-C1"], ["recall"], 3),
            "4a-iii": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "4a-iv": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "4b-i": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "4b-ii": (["12.4"], ["12.4-C1"], ["explain"], 3),
            "4c-i": (["7.3"], ["7.3-C3"], ["recall"], 2),
            "4c-ii": (["12.4"], ["12.4-C3"], ["recall"], 3),
            "4c-iii": (["3.3", "7.3"], ["3.3-S3", "7.3-S5"], ["calculate"], 4),
            "5a-i": (["2.7"], ["2.7-S1"], ["explain"], 3),
            "5a-ii": (["2.7"], ["2.7-S2"], ["explain"], 3),
            "5b-i": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "5b-ii": (["9.6"], ["9.6-C2"], ["recall"], 3),
            "5b-iii": (["9.6"], ["9.6-S4"], ["recall"], 3),
            "5b-iv": (["9.6"], ["9.6-C2"], ["recall"], 3),
            "5c": (["9.3"], ["9.3-S5"], ["explain"], 3),
            "5d-i": (["9.5"], ["9.5-C1"], ["recall"], 2),
            "5d-ii": (["9.5"], ["9.5-S4"], ["recall"], 2),
            "5d-iii": (["9.5"], ["9.5-C3"], ["explain"], 2),
            "5d-iv": (["9.5"], ["9.5-S5"], ["explain"], 3),
            "6a": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "6b": (["11.2"], ["11.2-S4"], ["recall"], 2),
            "6c-i": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "6c-ii": (["3.1"], ["3.1-C2"], ["recall"], 2),
            "6d": (["3.1"], ["3.1-S5"], ["recall"], 3),
            "6e-i": (["11.8"], ["11.8-S9"], ["recall"], 2),
            "6e-ii": (["11.8"], ["11.8-S8"], ["draw"], 3),
            "6f-i": (["11.8"], ["11.8-S12"], ["recall"], 2),
            "6f-ii": (["11.8"], ["11.8-S13"], ["draw"], 3),
        },
    ),
    "0620_m23_qp_42": (
        "FM",
        42,
        {
            "1a": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "1b": (["10.3"], ["10.3-C1"], ["recall"], 2),
            "1c": (["10.3"], ["10.3-C4"], ["recall"], 2),
            "1d": (["10.3"], ["10.3-S8"], ["recall"], 2),
            "1e-i": (["1.2"], ["1.2-S2"], ["recall"], 3),
            "1e-ii": (["1.2"], ["1.2-S2"], ["explain"], 3),
            "1f": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "1g": (["10.3"], ["10.3-C5"], ["recall"], 2),
            "1h": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "2a": (["2.7"], ["2.7-S1"], ["recall"], 2),
            "2b-i": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "2b-ii": (["7.1"], ["7.1-C7"], ["recall"], 2),
            "2b-iii": (["7.1"], ["7.1-C7"], ["recall"], 2),
            "2b-iv": (["8.2"], ["8.2-C1"], ["recall"], 3),
            "2c-i": (["2.3"], ["2.3-C1"], ["recall"], 2),
            "2c-ii": (["2.2"], ["2.2-C3", "2.2-C4"], ["recall"], 2),
            "2c-iii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
            "2d": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "3a": (["6.3"], ["6.3-S6"], ["recall"], 2),
            "3b-i": (["5.1"], ["5.1-S4"], ["recall"], 2),
            "3b-ii": (["5.1"], ["5.1-C1", "5.1-S4"], ["recall"], 2),
            "3b-iii": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "3b-iv": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "3b-v": (["6.3"], ["6.3-S11"], ["explain"], 3),
            "3c-i": (["10.2"], ["10.2-C1"], ["recall"], 2),
            "3c-ii": (["10.2"], ["10.2-C1"], ["recall"], 2),
            "3c-iii": (["3.3"], ["3.3-S8"], ["calculate"], 3),
            "4a-i": (["9.3"], ["9.3-C1"], ["recall"], 2),
            "4a-ii": (["9.3"], ["9.3-C1"], ["recall"], 2),
            "4b-i": (["9.1"], ["9.1-C1"], ["recall"], 2),
            "4b-ii": (["2.7"], ["2.7-S2"], ["recall"], 2),
            "4c-i": (["8.4"], ["8.4-C1"], ["recall"], 2),
            "4c-ii": (["8.4"], ["8.4-C1"], ["recall"], 2),
            "4d-i": (["7.3"], ["7.3-S5"], ["recall"], 2),
            "4d-ii": (["6.3"], ["6.3-C2"], ["recall"], 2),
            "4d-iii": (["7.3"], ["7.3-S5"], ["recall"], 2),
            "4e-i": (["7.2"], ["7.2-C1"], ["recall"], 2),
            "4e-ii": (["6.4"], ["6.4-C1"], ["recall"], 2),
            "4e-iii": (["3.3"], ["3.3-S3"], ["calculate"], 3),
            "4e-iv": (["3.3"], ["3.3-S4"], ["calculate"], 3),
            "4e-v": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5a": (["11.1"], ["11.1-C3", "11.1-C4"], ["explain"], 2),
            "5b": (["11.7"], ["11.7-C1"], ["recall"], 1),
            "5c": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "5d": (["11.1"], ["11.1-S8"], ["draw"], 3),
            "5e-i": (["11.5"], ["11.5-C2"], ["recall"], 3),
            "5e-ii": (["11.5"], ["11.5-C2"], ["recall"], 2),
            "5f-i": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "5f-ii": (["11.8"], ["11.8-C2"], ["recall"], 2),
            "5g-i": (["11.7"], ["11.7-C1"], ["recall"], 2),
            "5g-ii": (["11.7"], ["11.7-C1"], ["recall"], 2),
            "5h-i": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "5h-ii": (["11.2"], ["11.2-S4"], ["recall"], 2),
            "5h-iii": (["11.7"], ["11.7-S3"], ["recall"], 2),
        },
    ),
}

SEASON = {"MJ": "s23", "ON": "w23", "FM": "m23"}
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
            "id": f"cie-0620-2023-{sess_slug}-p{paper}-q{slug}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2023,
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
            "_retag": "assessed-skill-2023-p4",
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
