#!/usr/bin/env python3
"""Tag 2024 Paper 5 planning papers (FM/MJ/ON)."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_9701_tags import apply_tags


def t(*los, skills=("practical",), d=3):
    return {
        "learning_outcomes": list(los),
        "skills": list(skills),
        "difficulty": d,
        "question_type": "structured",
    }


PT = t("1.1-3")  # split leftover periodic-table page
TIT = t("2.4-1c", skills=("practical",))
CALC = t("2.4-1c", "2.4-1a", skills=("calculate",))
ERR = t("2.4-1c", skills=("evaluate",))
RATE = t("8.1-3", "26.1-2c", skills=("data-analysis",))
EA = t("8.2-1", "26.1-6", skills=("calculate",), d=4)
HESS = t("5.1-7", "5.2-1", skills=("calculate",))
SAFE = t("2.4-1c", skills=("practical", "evaluate"))

M24_52 = {
    "1a": TIT, "1b": TIT, "1c": SAFE, "1d": TIT, "1e-i": TIT, "1e-ii": TIT,
    "1f": SAFE, "1g": TIT, "1h-i": TIT, "1h-ii": CALC, "1h-iii": CALC, "1h-iv": ERR,
    "1i": t("2.4-1c", "11.3-2a", skills=("evaluate",)),
    "2a": RATE, "2b": RATE, "2c-i": RATE, "2c-ii": t("8.1-1", skills=("practical",)),
    "2c-iii": t("8.1-1", skills=("practical",)), "2c-iv": ERR, "2c-v": RATE,
    "2c-vi": RATE, "2c-vii": ERR, "3": PT,
}

S24_51 = {
    "1a-i": CALC, "1a-ii": TIT, "1b-i": ERR, "1b-ii": ERR, "1c-i": TIT, "1c-ii": TIT,
    "1d": TIT, "1e": TIT, "1f": CALC, "1g-i": ERR, "1g-ii": ERR, "1h": SAFE,
    "2a": RATE, "2b-i": t("8.2-3", skills=("practical",)), "2b-ii": t("8.2-3", skills=("practical",)),
    "2c": RATE, "2d-i": EA, "2d-ii": EA, "2d-iii": EA, "2d-iv": ERR, "2e": RATE, "3": PT,
}

S24_52 = {
    "1a": HESS, "1b-i": HESS, "1b-ii": HESS, "1c": TIT, "1d": TIT, "1e-i": HESS,
    "1e-ii": HESS, "1f": ERR, "1g": ERR, "1h": HESS, "1s-i": HESS,
    "2a": RATE, "2b": RATE, "2c-i": RATE, "2c-ii": RATE, "2d-i": RATE, "2d-ii": ERR,
    "2e-i": RATE, "2e-ii": RATE, "2e-iii": t("26.1-2b", skills=("data-analysis",)),
    "2e-iv": ERR, "3": PT,
}

W24_51 = {
    "1a": SAFE, "1b": TIT, "1c": TIT, "1d-i": ERR, "1d-ii": TIT, "1d-iii": TIT,
    "1d-iv": TIT, "1e-i": CALC, "1e-ii": CALC, "1f": ERR, "1s-iii": CALC,
    "2a": t("22.1-1", skills=("practical",)),  # colorimetry wavelength
    "2b-i": CALC, "2b-ii": TIT, "2c-i": RATE, "2c-ii": t("8.1-1", skills=("practical",)),
    "2d-i": RATE, "2d-ii": ERR, "2d-iii": RATE, "2d-iv": ERR,
    "2e-i": RATE, "2e-ii": t("26.1-3b", skills=("calculate",)),
    "2e-iii": t("26.1-2b", "26.1-3a", skills=("data-analysis",)), "3": PT,
}

W24_52 = {
    "1a-i": CALC, "1a-ii": TIT, "1b-i": TIT, "1b-ii": TIT, "1b-iii": TIT, "1b-iv": TIT,
    "1c-i": TIT, "1c-ii": ERR, "1d": CALC, "1e": ERR,
    "2a-i": TIT, "2a-ii": SAFE, "2a-iii": TIT, "2b": CALC, "2c": CALC,
    "2d-i": RATE, "2d-ii": ERR, "2e": RATE, "2f": ERR,
    "2g-i": t("2.4-1a", skills=("calculate",)), "2g-ii": ERR, "3": PT,
}

W24_53 = {
    "1a": SAFE, "1b": TIT, "1c": TIT, "1d-i": ERR, "1d-ii": TIT, "1d-iii": TIT,
    "1d-iv": TIT, "1e-i": CALC, "1e-ii": CALC, "1e-iii": CALC, "1f": ERR,
    "2a": t("22.1-1", skills=("practical",)),
    "2b-i": CALC, "2b-ii": TIT, "2c-i": RATE, "2c-ii": t("8.1-1", skills=("practical",)),
    "2d-i": RATE, "2d-ii": ERR, "2d-iii": RATE, "2d-iv": ERR,
    "2e-i": RATE, "2e-ii": t("26.1-3b", skills=("calculate",)),
    "2e-iii": t("26.1-2b", "26.1-3a", skills=("data-analysis",)), "3": PT,
}


def main() -> None:
    apply_tags(ROOT / "draft/9701_m24_qp_52", M24_52, as_only=False)
    apply_tags(ROOT / "draft/9701_s24_qp_51", S24_51, as_only=False)
    apply_tags(ROOT / "draft/9701_s24_qp_52", S24_52, as_only=False)
    apply_tags(ROOT / "draft/9701_s24_qp_53", S24_51, as_only=False)
    apply_tags(ROOT / "draft/9701_w24_qp_51", W24_51, as_only=False)
    apply_tags(ROOT / "draft/9701_w24_qp_52", W24_52, as_only=False)
    apply_tags(ROOT / "draft/9701_w24_qp_53", W24_53, as_only=False)


if __name__ == "__main__":
    main()
