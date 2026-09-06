#!/usr/bin/env python3
"""Hand-tag IGCSE 0620 2022 P4 structured variants from 0620 vocabulary.

Assessed skill, not list decoration. year=2022.
Export with ``chembank ingest --export`` (or export-vault --no-refresh).
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
    "0620_s22_qp_41": (
        "MJ",
        41,
        {
            "1a": (["10.3"], ["10.3-C5"], ["recall"], 2),
            "1b": (["9.6"], ["9.6-C3"], ["recall"], 2),
            "1c": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "1d": (["11.6"], ["11.6-C3"], ["recall"], 2),
            "1e": (["9.3"], ["9.3-C1"], ["recall"], 2),
            "1f": (["10.3"], ["10.3-S7"], ["recall"], 2),
            "1g": (["10.3"], ["10.3-C1"], ["recall"], 1),
            "1h": (["2.6"], ["2.6-C1"], ["recall"], 1),
            "2a-i": (["2.2"], ["2.2-C2"], ["recall"], 2),
            "2a-ii": (["2.3"], ["2.3-C1"], ["recall"], 2),
            "2a-iii": (["2.4"], ["2.4-C1"], ["explain"], 2),
            "2b": (["2.2"], ["2.2-C5"], ["recall"], 3),
            "3a-i": (["2.7"], ["2.7-S1"], ["recall"], 3),
            "3a-ii": (["2.7"], ["2.7-S2"], ["explain"], 2),
            "3b-i": (["2.4"], ["2.4-C2"], ["recall"], 1),
            "3b-ii": (["2.4"], ["2.4-S7"], ["explain"], 3),
            "3c-i": (["12.2"], ["12.2-C1"], ["recall"], 2),
            "3c-ii": (["12.2"], ["12.2-C2"], ["recall"], 2),
            "3c-iii": (["12.2"], ["12.2-C1"], ["recall"], 2),
            "3c-iv": (["3.3"], ["3.3-S6"], ["calculate"], 4),
            "4a-i": (["6.3"], ["6.3-S9"], ["recall"], 2),
            "4a-ii": (["6.3"], ["6.3-S8"], ["recall"], 2),
            "4a-iii": (["6.3"], ["6.3-S8"], ["recall"], 3),
            "4a-iv": (["6.3"], ["6.3-S8"], ["recall"], 3),
            "4b-i": (["2.5"], ["2.5-C2"], ["draw"], 3),
            "4b-ii": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "5a": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "5b": (["6.3"], ["6.3-S11"], ["explain"], 4),
            "5c": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "5d": (["8.4"], ["8.4-C1"], ["recall"], 2),
            "5e": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "5f": (["11.2"], ["11.2-S3"], ["draw"], 3),
            "5g-i": (["11.2"], ["11.2-S4"], ["recall"], 2),
            "5g-ii": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "5h-i": (["3.3"], ["3.3-S7"], ["calculate"], 4),
            "6a-i": (["9.6"], ["9.6-C1"], ["recall"], 2),
            "6a-ii": (["6.4"], ["6.4-C3"], ["recall"], 3),
            "6a-iii": (["9.6"], ["9.6-C1"], ["recall"], 2),
            "6a-iv": (["1.1"], ["1.1-C3"], ["explain"], 3),
            "6a-v": (["1.1"], ["1.1-C3"], ["recall"], 2),
            "6b-i": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "6b-ii": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "6b-iii": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "6b-iv": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "6b-v": (["7.3"], ["7.3-C3"], ["recall"], 3),
            "7a-i": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "7a-ii": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "7b": (["8.4"], ["8.4-C1"], ["compare"], 2),
            "7c": (["8.3"], ["8.3-C4"], ["recall"], 2),
            "7d-i": (["8.3"], ["8.3-C3"], ["recall"], 2),
            "7d-ii": (["6.4"], ["6.4-S6"], ["explain"], 3),
            "7e": (["5.1"], ["5.1-S8"], ["calculate"], 4),
        },
    ),
    "0620_s22_qp_42": (
        "MJ",
        42,
        {
            "1a": (["8.1"], ["8.1-C3"], ["recall"], 2),
            "1b": (["8.5"], ["8.5-C1"], ["recall"], 2),
            "1c": (["10.1"], ["10.1-C7"], ["recall"], 2),
            "1d": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1e": (["10.2"], ["10.2-C2"], ["recall"], 2),
            "1f": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "1g": (["9.2"], ["9.2-C1"], ["recall"], 2),
            "1h": (["9.6"], ["9.6-C1"], ["recall"], 2),
            "2a-i": (["9.4"], ["9.4-C2"], ["recall"], 3),
            "2a-ii": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "2b-i": (["7.1"], ["7.1-C7"], ["recall"], 2),
            "2b-ii": (["7.1"], ["7.1-C6"], ["recall"], 2),
            "2c-i": (["12.5"], ["12.5-C3"], ["recall"], 1),
            "2c-ii": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "2c-iii": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "2c-iv": (["12.5"], ["12.5-C2"], ["recall"], 2),
            "2d-i": (["12.2"], ["12.2-C1"], ["recall"], 2),
            "2d-ii": (["7.1"], ["7.1-C8"], ["recall"], 2),
            "2d-iii": (["12.2"], ["12.2-C2"], ["recall"], 2),
            "2d-iv": (["3.3"], ["3.3-S6"], ["calculate"], 4),
            "3a-i": (["2.3"], ["2.3-C1"], ["recall"], 1),
            "3a-ii": (["2.2"], ["2.2-C4"], ["recall"], 2),
            "3a-iii": (["2.2"], ["2.2-C3", "2.2-C4"], ["recall"], 3),
            "3b-i": (["8.4"], ["8.4-C1"], ["recall"], 2),
            "3b-ii": (["8.4"], ["8.4-C1", "8.4-S2"], ["recall"], 2),
            "3c-i": (["2.7"], ["2.7-S2"], ["explain"], 3),
            "3c-ii": (["9.1"], ["9.1-C1"], ["recall"], 1),
            "3d": (["8.4"], ["8.4-C1"], ["compare"], 2),
            "4a": (["8.3"], ["8.3-C4"], ["recall"], 2),
            "4b": (["3.3"], ["3.3-S7"], ["calculate"], 4),
            "4c": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "4d": (["2.4"], ["2.4-C3"], ["draw"], 3),
            "4e": (["2.4", "2.5"], ["2.4-S7", "2.5-S5"], ["explain"], 4),
            "5a": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "5b": (["11.6"], ["11.6-C2"], ["recall"], 3),
            "5c-i": (["11.5"], ["11.5-C1"], ["recall"], 2),
            "5c-ii": (["11.5"], ["11.5-S5"], ["recall"], 2),
            "5c-iii": (["11.5"], ["11.5-S6"], ["recall"], 3),
            "5d-i": (["11.5"], ["11.5-S6"], ["recall"], 3),
            "5d-ii": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "5e-i": (["11.7"], ["11.7-S2"], ["recall"], 2),
            "5e-ii": (["11.7"], ["11.7-C1"], ["recall"], 2),
            "5e-iii": (["11.1"], ["11.1-C1"], ["draw"], 3),
            "6a-i": (["11.8"], ["11.8-S8"], ["recall"], 3),
            "6a-ii": (["11.8"], ["11.8-S8"], ["draw"], 3),
            "6a-iii": (["11.8"], ["11.8-S10"], ["recall"], 2),
            "6b": (["11.8"], ["11.8-S8"], ["recall"], 3),
            "6c-i": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "6c-ii": (["11.8"], ["11.8-S9"], ["recall"], 2),
        },
    ),
    "0620_s22_qp_43": (
        "MJ",
        43,
        {
            "1a": (["10.3"], ["10.3-C5"], ["recall"], 2),
            "1b": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1c": (["10.1"], ["10.1-C1"], ["recall"], 2),
            "1d": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "1e": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "1f": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1g": (["9.1"], ["9.1-C1"], ["recall"], 2),
            "1h": (["10.3"], ["10.3-C1"], ["recall"], 1),
            "2a-i": (["2.3"], ["2.3-C1"], ["recall"], 2),
            "2a-ii": (["2.2"], ["2.2-C3"], ["explain"], 2),
            "2a-iii": (["2.3"], ["2.3-S3"], ["explain"], 2),
            "2b-i": (["2.4"], ["2.4-C1"], ["explain"], 2),
            "2b-ii": (["2.2"], ["2.2-C5"], ["recall"], 3),
            "3a-i": (["2.5"], ["2.5-C1"], ["recall"], 2),
            "3a-ii": (["2.5"], ["2.5-S5"], ["explain"], 3),
            "3a-iii": (["2.5"], ["2.5-S5"], ["explain"], 2),
            "3b": (["6.3"], ["6.3-S5", "6.3-S7"], ["recall"], 3),
            "3c": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3d": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "3e-i": (["7.1"], ["7.1-S9"], ["recall"], 2),
            "3e-ii": (["7.1"], ["7.1-S9"], ["recall"], 3),
            "4a": (["6.2"], ["6.2-C2"], ["recall"], 1),
            "4b": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4c-i": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "4c-ii": (["11.1"], ["11.1-S9"], ["recall"], 2),
            "4c-iii": (["11.2"], ["11.2-S3"], ["draw"], 3),
            "4d-i": (["11.6"], ["11.6-C1"], ["recall"], 2),
            "4d-ii": (["11.6"], ["11.6-S4"], ["compare"], 3),
            "4e": (["11.6"], ["11.6-C3"], ["recall"], 2),
            "4f": (["11.7"], ["11.7-S2"], ["recall"], 2),
            "5a": (["2.7"], ["2.7-S1"], ["recall"], 3),
            "5b": (["4.1"], ["4.1-C7"], ["recall"], 2),
            "5c": (["7.3"], ["7.3-C1", "7.3-C3"], ["recall"], 2),
            "5d": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "5e": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "5f": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "5g": (["12.4"], ["12.4-C1"], ["recall"], 1),
            "5h-i": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "6a-i": (["8.2", "8.4"], ["8.2-C1", "8.4-C1"], ["compare"], 3),
            "6a-ii": (["8.2"], ["8.2-C1"], ["recall"], 3),
            "6b": (["8.4"], ["8.4-C1"], ["compare"], 2),
            "6c-i": (["8.3"], ["8.3-C3"], ["recall"], 2),
            "6c-ii": (["6.4"], ["6.4-C2"], ["recall"], 2),
            "6c-iii": (["6.4"], ["6.4-S11"], ["explain"], 3),
            "6d": (["8.3"], ["8.3-C2"], ["recall"], 2),
        },
    ),
    "0620_w22_qp_41": (
        "ON",
        41,
        {
            "1a": (["10.3"], ["10.3-C5"], ["recall"], 2),
            "1b": (["10.3"], ["10.3-C1"], ["recall"], 2),
            "1c": (["7.2"], ["7.2-C1"], ["recall"], 2),
            "1d": (["10.2"], ["10.2-C2"], ["recall"], 2),
            "1e": (["1.2"], ["1.2-S2"], ["recall"], 3),
            "1f": (["12.5"], ["12.5-C4"], ["recall"], 2),
            "1g": (["2.2"], ["2.2-C5"], ["recall"], 2),
            "1h": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "2a": (["2.7"], ["2.7-S1"], ["recall"], 3),
            "2b-i": (["2.4"], ["2.4-C4"], ["recall"], 2),
            "2b-ii": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "2c-i": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "2c-ii": (["7.1"], ["7.1-S10"], ["recall"], 2),
            "2c-iii": (["7.1"], ["7.1-C5"], ["recall"], 2),
            "2c-iv": (["3.3"], ["3.3-S4"], ["calculate"], 3),
            "2d-i": (["7.1"], ["7.1-C1"], ["recall"], 2),
            "2d-ii": (["7.1"], ["7.1-C8"], ["recall"], 2),
            "2d-iii": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "2e-i": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "2e-ii": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "2e-iii": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "3a": (["6.3"], ["6.3-S5"], ["recall"], 1),
            "3b": (["6.3"], ["6.3-S6"], ["recall"], 2),
            "3c": (["6.3"], ["6.3-C1"], ["recall"], 1),
            "3d": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "3e": (["6.3"], ["6.3-S7"], ["recall"], 2),
            "3f": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "3g": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "3h": (["10.2"], ["10.2-C1"], ["recall"], 2),
            "4a": (["7.1"], ["7.1-C1"], ["recall"], 2),
            "4b": (["7.1"], ["7.1-C1"], ["recall"], 2),
            "4c": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "4d-i": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "4d-ii": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "4e-i": (["7.3"], ["7.3-S5"], ["recall"], 2),
            "4e-ii": (["3.3"], ["3.3-S3"], ["calculate"], 4),
            "4f": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5a": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "5b": (["11.5"], ["11.5-C4"], ["recall"], 2),
            "5c": (["11.5"], ["11.5-S5"], ["recall"], 2),
            "5d-i": (["5.1"], ["5.1-S6"], ["draw"], 3),
            "5d-ii": (["5.1"], ["5.1-S4"], ["recall"], 2),
            "6a-i": (["11.2"], ["11.2-S4"], ["recall"], 2),
            "6a-ii": (["3.1"], ["3.1-S5"], ["recall"], 3),
            "6b": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "6c": (["11.7"], ["11.7-S3"], ["recall"], 3),
            "6d-i": (["11.1"], ["11.1-S8"], ["recall"], 2),
            "6d-ii": (["11.1"], ["11.1-S8"], ["recall"], 3),
        },
    ),
    "0620_w22_qp_42": (
        "ON",
        42,
        {
            "1a": (["2.6"], ["2.6-C1"], ["recall"], 1),
            "1b": (["2.6"], ["2.6-C1"], ["recall"], 2),
            "1c": (["2.6"], ["2.6-S3"], ["recall"], 2),
            "1d": (["2.6"], ["2.6-C1"], ["recall"], 2),
            "1e": (["2.6"], ["2.6-C2"], ["explain"], 2),
            "1f": (["3.2"], ["3.2-C2"], ["calculate"], 3),
            "1g": (["12.5"], ["12.5-C3"], ["recall"], 1),
            "2a": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "2b-i": (["6.4"], ["6.4-C3"], ["recall"], 2),
            "2b-ii": (["8.2"], ["8.2-C1"], ["recall"], 2),
            "2b-iii": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "2b-iv": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "2c-i": (["7.1"], ["7.1-S9"], ["explain"], 2),
            "2c-ii": (["7.1"], ["7.1-C7"], ["recall"], 2),
            "2c-iii": (["7.1"], ["7.1-C5"], ["recall"], 2),
            "2c-iv": (["3.3"], ["3.3-S4"], ["calculate"], 3),
            "2d-i": (["7.3"], ["7.3-S4"], ["recall"], 2),
            "2d-ii": (["12.5"], ["12.5-C2"], ["recall"], 2),
            "2d-iii": (["12.5"], ["12.5-C2"], ["recall"], 2),
            "2d-iv": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "3a": (["6.3"], ["6.3-S9"], ["recall"], 2),
            "3b": (["6.3"], ["6.3-S9"], ["recall"], 2),
            "3c": (["6.3"], ["6.3-S8"], ["recall"], 1),
            "3d-i": (["6.3"], ["6.3-S10"], ["recall"], 2),
            "3d-ii": (["6.3"], ["6.3-S10"], ["recall"], 2),
            "3d-iii": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "3d-iv": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "3d-v": (["6.3"], ["6.3-S11"], ["explain"], 3),
            "3e": (["10.2"], ["10.2-C1"], ["recall"], 2),
            "4a": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "4b": (["7.3"], ["7.3-C1"], ["recall"], 2),
            "4c": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "4d-i": (["12.1"], ["12.1-C3"], ["recall"], 2),
            "4d-ii": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "4e-i": (["7.3"], ["7.3-S5"], ["recall"], 2),
            "4e-ii": (["3.3"], ["3.3-S3"], ["calculate"], 4),
            "4f": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "5a": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "5b": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5c": (["11.4"], ["11.4-S3"], ["recall"], 2),
            "5d": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5e-i": (["5.1"], ["5.1-S6"], ["draw"], 3),
            "5e-ii": (["5.1"], ["5.1-S4"], ["recall"], 2),
            "5e-iii": (["5.1"], ["5.1-S5"], ["recall"], 2),
            "5f": (["11.1"], ["11.1-C1"], ["draw"], 3),
            "6a": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "6b": (["11.2"], ["11.2-C1"], ["recall"], 2),
            "6c": (["3.1"], ["3.1-C2"], ["recall"], 2),
            "6d": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "6e-i": (["11.2"], ["11.2-S4"], ["draw"], 3),
            "6e-ii": (["11.7"], ["11.7-S3"], ["recall"], 2),
            "6e-iii": (["11.7"], ["11.7-S3"], ["recall"], 2),
        },
    ),
    "0620_w22_qp_43": (
        "ON",
        43,
        {
            "1a": (["2.2"], ["2.2-C2"], ["recall"], 2),
            "1b": (["2.2", "2.3"], ["2.2-C3", "2.3-C2"], ["recall"], 3),
            "2a-i": (["1.1"], ["1.1-C1"], ["data-analysis"], 2),
            "2a-ii": (["1.1"], ["1.1-C1"], ["data-analysis"], 2),
            "2a-iii": (["2.5"], ["2.5-C3"], ["data-analysis"], 3),
            "2b": (["2.4"], ["2.4-C4"], ["data-analysis"], 3),
            "2c": (["2.7"], ["2.7-S2"], ["explain"], 3),
            "2d": (["2.6"], ["2.6-C1"], ["data-analysis"], 3),
            "3a": (["9.6"], ["9.6-C3"], ["recall"], 1),
            "3b": (["4.1"], ["4.1-C1"], ["recall"], 2),
            "3c-i": (["9.6"], ["9.6-S5"], ["recall"], 2),
            "3c-ii": (["9.6"], ["9.6-S5"], ["recall"], 3),
            "3c-iii": (["9.6"], ["9.6-S5"], ["explain"], 3),
            "3d": (["9.4"], ["9.4-S5"], ["explain"], 3),
            "3e-i": (["7.2"], ["7.2-S2"], ["recall"], 2),
            "3e-ii": (["7.2"], ["7.2-S3"], ["recall"], 3),
            "3f": (["8.1"], ["8.1-C5"], ["recall"], 3),
            "4a-i": (["6.3"], ["6.3-S3"], ["recall"], 2),
            "4a-ii": (["6.3"], ["6.3-S4"], ["explain"], 3),
            "4b": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "4c": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "4d": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "4e": (["3.3"], ["3.3-S7"], ["calculate"], 3),
            "5a-i": (["6.3"], ["6.3-S10"], ["recall"], 2),
            "5a-ii": (["6.3"], ["6.3-S8"], ["recall"], 3),
            "5a-iii": (["6.3"], ["6.3-S8"], ["recall"], 3),
            "5b": (["6.4"], ["6.4-C3"], ["recall"], 3),
            "5c-i": (["3.3"], ["3.3-S6"], ["calculate"], 4),
            "5c-ii": (["3.3"], ["3.3-S6"], ["calculate"], 3),
            "5d-i": (["12.5"], ["12.5-C4"], ["recall"], 2),
            "5d-ii": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "5d-iii": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "5e": (["3.1"], ["3.1-S7"], ["recall"], 3),
            "6a-i": (["5.1"], ["5.1-S8"], ["calculate"], 4),
            "6a-ii": (["5.1"], ["5.1-S4"], ["recall"], 2),
            "6b-i": (["11.8"], ["11.8-C1"], ["recall"], 2),
            "6b-ii": (["11.8"], ["11.8-S7"], ["draw"], 3),
            "6b-iii": (["3.1"], ["3.1-S5"], ["recall"], 3),
            "6c-i": (["11.8"], ["11.8-S12"], ["recall"], 2),
            "6c-ii": (["11.8"], ["11.8-S12"], ["recall"], 3),
            "6c-iii": (["12.3"], ["12.3-S3"], ["recall"], 3),
            "6d-i": (["11.8"], ["11.8-S10"], ["recall"], 2),
            "6d-ii": (["11.8"], ["11.8-S8"], ["recall"], 3),
        },
    ),
    "0620_m22_qp_42": (
        "FM",
        42,
        {
            "1a": (["10.3"], ["10.3-C1"], ["recall"], 1),
            "1b": (["2.2"], ["2.2-C5"], ["recall"], 2),
            "1c": (["9.6"], ["9.6-C2"], ["recall"], 2),
            "1d": (["2.6"], ["2.6-S3"], ["recall"], 2),
            "1e": (["1.2"], ["1.2-S2"], ["recall"], 3),
            "1f": (["10.1"], ["10.1-C1"], ["recall"], 2),
            "1g": (["12.5"], ["12.5-C1"], ["recall"], 2),
            "1h-i": (["12.5"], ["12.5-C2"], ["recall"], 3),
            "1j": (["9.5"], ["9.5-S4"], ["recall"], 2),
            "2a": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "2b": (["2.4"], ["2.4-S6"], ["draw"], 3),
            "2c": (["2.5"], ["2.5-S4"], ["draw"], 3),
            "2d-i": (["6.2"], ["6.2-C4"], ["data-analysis"], 2),
            "2d-ii": (["6.2"], ["6.2-S6"], ["explain"], 3),
            "2d-iii": (["6.2"], ["6.2-C1"], ["data-analysis"], 3),
            "2e": (["3.3"], ["3.3-S4", "3.3-S5"], ["calculate"], 4),
            "3a": (["10.3"], ["10.3-S8"], ["explain"], 3),
            "3b": (["10.3"], ["10.3-C3"], ["recall"], 2),
            "3c-i": (["6.1"], ["6.1-C1"], ["recall"], 2),
            "3c-ii": (["3.1"], ["3.1-C4"], ["recall"], 3),
            "3c-iii": (["12.5"], ["12.5-C3"], ["recall"], 2),
            "3d-i": (["3.1"], ["3.1-C4"], ["recall"], 2),
            "3d-ii": (["6.4"], ["6.4-S7"], ["explain"], 3),
            "3d-iii": (["6.4"], ["6.4-C2"], ["recall"], 2),
            "3e": (["3.3"], ["3.3-S3"], ["calculate"], 3),
            "3f-i": (["10.3"], ["10.3-C2"], ["recall"], 2),
            "3f-ii": (["10.3"], ["10.3-S8"], ["recall"], 3),
            "4a-i": (["9.4"], ["9.4-C3"], ["recall"], 3),
            "4a-ii": (["4.1"], ["4.1-S11"], ["recall"], 3),
            "4b-i": (["9.4"], ["9.4-C1"], ["recall"], 3),
            "4b-ii": (["9.4"], ["9.4-C1"], ["recall"], 3),
            "4c-i": (["4.2"], ["4.2-C1"], ["recall"], 2),
            "4c-ii": (["4.2"], ["4.2-C1"], ["recall"], 2),
            "4d-i": (["4.1"], ["4.1-C1"], ["recall"], 1),
            "4d-ii": (["4.1"], ["4.1-S8"], ["explain"], 2),
            "4e-i": (["4.1"], ["4.1-C3"], ["recall"], 3),
            "4e-ii": (["4.1"], ["4.1-C5"], ["recall"], 3),
            "5a-i": (["11.5"], ["11.5-C2"], ["recall"], 2),
            "5a-ii": (["11.5"], ["11.5-C2"], ["recall"], 3),
            "5b-i": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5b-ii": (["11.4"], ["11.4-S4"], ["recall"], 2),
            "5c-i": (["11.5"], ["11.5-S5"], ["recall"], 2),
            "5c-ii": (["11.1"], ["11.1-C1"], ["draw"], 3),
            "6a-i": (["11.1"], ["11.1-C4"], ["recall"], 2),
            "6a-ii": (["11.1"], ["11.1-C3"], ["explain"], 2),
            "6a-iii": (["11.1"], ["11.1-C2"], ["recall"], 2),
            "6a-iv": (["11.2"], ["11.2-S4"], ["recall"], 3),
            "6b": (["12.4"], ["12.4-C1"], ["recall"], 2),
            "6c-i": (["11.2"], ["11.2-S4"], ["draw"], 3),
            "6c-ii": (["11.2"], ["11.2-S3"], ["recall"], 2),
            "6d-i": (["11.1"], ["11.1-S8"], ["recall"], 2),
            "6d-ii": (["11.1"], ["11.1-S8"], ["recall"], 3),
            "6e-i": (["11.8"], ["11.8-S8"], ["draw"], 4),
            "6e-ii": (["11.8"], ["11.8-S9"], ["recall"], 2),
            "6e-iii": (["11.8"], ["11.8-S10"], ["recall"], 2),
        },
    ),
}

SEASON = {"MJ": "s22", "ON": "w22", "FM": "m22"}
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
            "id": f"cie-0620-2022-{sess_slug}-p{paper}-q{slug}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2022,
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
            "_retag": "assessed-skill-2022-p4",
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
