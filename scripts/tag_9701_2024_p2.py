#!/usr/bin/env python3
"""Tag 2024 Paper 2 structured: FM P22 + ON P21/P22/P23."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_9701_tags import apply_tags


def t(*los, skills=("recall",), d=3):
    return {
        "learning_outcomes": list(los),
        "skills": list(skills),
        "difficulty": d,
        "question_type": "structured",
    }


M24_22 = {
    "1a": t("3.3-1", skills=("draw",)),
    "1b-i": t("2.3-2a", skills=("explain",)),
    "1b-ii": t("4.2-3", "4.2-2"),
    "1c-i": t("6.1-1"),
    "1c-ii": t("6.1-4"),
    "1d-i": t("6.1-4"),
    "1d-ii": t("14.2-2b"),
    "1d-iii": t("17.1-5", "17.1-4"),
    "1d-iv": t("2.3-2a", "17.1-2a"),
    "1e": t("2.4-1c", "2.4-1e", skills=("calculate",), d=4),
    "2a": t("9.2-5", "9.2-7"),
    "2b-i": t("6.1-3", "11.4-1"),
    "2b-ii": t("11.4-1"),
    "2b-iii": t("11.4-1", "2.3-2a"),
    "2b-iv": t("11.3-2a"),
    "2c-i": t("3.5-1", "3.5-2"),
    "2c-ii": t("9.2-5", "13.2-1f"),
    "2d-i": t("14.2-4", skills=("draw",)),
    "2d-ii": t("15.1-4"),
    "2d-iii": t("20.1-2", skills=("draw",)),
    "3a": t("12.1-1"),
    "3b-i": t("12.1-3", "2.3-2a"),
    "3b-ii": t("12.1-5"),
    "3b-iii": t("12.1-4"),
    "3c-i": t("5.1-3b"),
    "3c-ii": t("8.3-1a", "7.1-10"),
    "3c-iii": t("8.1-2", "7.1-10", skills=("explain",)),
    "3d-i": t("3.7-1", skills=("draw",)),
    "3d-ii": t("3.4-2c"),
    "3d-iii": t("3.4-2a", skills=("draw",)),
    "4a": t("13.4-2", "13.4-5"),
    "4b-i": t("15.1-1a", skills=("draw",)),
    "4b-ii": t("15.1-5", "13.2-2c"),
    "4b-iii": t("19.2-3", "2.3-2a"),
    "4c-i": t("22.2-5", skills=("calculate",)),
    "4c-ii": t("22.1-1", skills=("data-analysis",)),
    "4c-iii": t("18.2-1a", "21.1-1a", skills=("draw",)),
}

W24_21 = {
    "1a-i": t("1.3-4"),
    "1a-ii": t("1.3-8", skills=("draw",)),
    "1a-iii": t("1.3-7"),
    "1b": t("1.1-6", "1.2-1"),
    "1c-i": t("2.1-2"),
    "1c-ii": t("2.1-2", skills=("calculate",)),
    "1d-i": t("2.3-4", "2.4-1a", skills=("calculate",)),
    "1d-ii": t("13.4-2"),
    "1d-iii": t("13.2-1f"),
    "1d-iv": t("13.4-3", skills=("draw",)),
    "2a-i": t("11.1-1"),
    "2a-ii": t("11.2-1"),
    "2a-iii": t("11.2-2"),
    "2a-iv": t("11.2-3"),
    "2b-i": t("1.3-9", "13.2-1d"),
    "2b-ii": t("14.1-2b"),
    "2b-iii": t("14.1-3"),
    "2c-i": t("11.4-1"),
    "2c-ii": t("6.1-3"),
    "2c-iii": t("11.4-1", "2.3-2a"),
    "2c-iv": t("15.1-3d", "11.3-2a"),
    "3a-i": t("4.2-2", "4.2-3"),
    "3a-ii": t("4.2-2"),
    "3a-iii": t("4.2-1a", "4.2-1d"),
    "3b-i": t("10.1-2", "2.3-2a"),
    "3b-ii": t("10.1-3"),
    "3b-iii": t("12.1-2c", "7.2-3"),
    "3c-i": t("1.4-4", "1.4-8"),
    "3c-ii": t("1.4-4", "1.4-7"),
    "3d-i": t("3.6-3a", "3.6-3b", skills=("explain",)),
    "3d-ii": t("3.6-3b"),
    "3e-i": t("9.2-1", "2.3-2a"),
    "3e-ii": t("9.2-5"),
    "3e-iii": t("4.2-2", "9.2-7"),
    "3f": t("9.2-4"),
    "4a-i": t("17.1-2b", "17.1-3"),
    "4a-ii": t("17.1-3", skills=("draw",)),
    "4b": t("19.2-3"),
    "4c-i": t("17.1-2a"),
    "4c-ii": t("16.1-3a"),
    "4d": t("17.1-4"),
    "4e": t("17.1-5"),
    "4f-i": t("22.1-1", skills=("data-analysis",)),
    "4f-ii": t("16.1-4", "17.1-6"),
}

W24_22 = {
    "1a-i": t("1.3-1"),
    "1a-ii": t("1.3-7", skills=("draw",)),
    "1a-iii": t("1.3-2"),
    "1b-i": t("1.2-1", "1.1-6"),
    "1b-ii": t("2.1-2"),
    "1b-iii": t("2.1-2", skills=("calculate",)),
    "2a-i": t("9.2-1", "2.3-2a"),
    "2a-ii": t("3.7-1", skills=("draw",)),
    "2a-iii": t("9.2-2", skills=("explain",)),
    "2b-i": t("9.2-3"),
    "2b-ii": t("19.2-3", "2.3-2a"),
    "2b-iii": t("14.2-2a", "16.1-1a", skills=("draw",)),
    "2b-iv": t("16.1-5"),
    "2c-i": t("3.6-3b", skills=("explain",)),
    "2c-ii": t("3.6-1b"),
    "3a-i": t("12.1-3"),
    "3a-ii": t("12.1-5", "2.3-2a"),
    "3a-iii": t("12.1-4"),
    "3a-iv": t("9.2-4", "2.3-2a"),
    "3a-v": t("10.1-3"),
    "3b-i": t("6.1-1"),
    "3b-ii": t("6.1-3"),
    "3b-iii": t("12.1-2a"),
    "3b-iv": t("3.5-2"),
    "3c-i": t("1.4-4", "1.4-8"),
    "3c-ii": t("1.4-7"),
    "3d": t("4.2-2", "9.1-2"),
    "3e": t("4.2-1b"),
    "3f-i": t("3.4-2a"),
    "3f-ii": t("3.4-2c"),
    "4a": t("14.2-4", skills=("draw",)),
    "4b": t("5.2-2a", "5.1-3b", skills=("calculate",)),
    "4c-i": t("15.1-3a", "15.1-4"),
    "4c-ii": t("20.1-2", skills=("draw",)),
    "4c-iii": t("15.1-4"),
    "4d-i": t("13.4-1"),
    "4d-ii": t("13.2-1a"),
    "4d-iii": t("15.1-3a"),
    "4e-i": t("22.1-1", "22.2-3", skills=("data-analysis",)),
    "4e-ii": t("21.1-3"),
}


def main() -> None:
    apply_tags(ROOT / "draft/9701_m24_qp_22", M24_22, as_only=True)
    apply_tags(ROOT / "draft/9701_w24_qp_21", W24_21, as_only=True)
    apply_tags(ROOT / "draft/9701_w24_qp_22", W24_22, as_only=True)
    apply_tags(ROOT / "draft/9701_w24_qp_23", W24_21, as_only=True)


if __name__ == "__main__":
    main()
