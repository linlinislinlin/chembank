#!/usr/bin/env python3
"""Tag 2024 Paper 3 practicals (FM P33 + ON P31/33–36)."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from apply_9701_tags import apply_tags

R = {
    "rate": {
        "practical_topic": "Rate experiments",
        "syllabus_codes": ["8.1", "8.2"],
        "learning_outcomes": ["8.1-1", "8.1-2", "8.1-3"],
        "skills": ["practical", "calculate", "data-analysis"],
    },
    "thermo": {
        "practical_topic": "Thermometric experiments",
        "syllabus_codes": ["5.1"],
        "learning_outcomes": ["5.1-7"],
        "skills": ["practical", "calculate"],
    },
    "titration": {
        "practical_topic": "Titrations",
        "syllabus_codes": ["2.2", "2.4"],
        "learning_outcomes": ["2.2-1", "2.4-1c", "2.4-1e"],
        "skills": ["practical", "calculate"],
    },
    "grav": {
        "practical_topic": "Gravimetric experiments",
        "syllabus_codes": ["2.2", "2.4"],
        "learning_outcomes": ["2.2-1", "2.4-1a", "2.4-1e"],
        "skills": ["practical", "calculate"],
    },
    "gas": {
        "practical_topic": "Gas volume experiments",
        "syllabus_codes": ["2.2", "2.4"],
        "learning_outcomes": ["2.2-1", "2.4-1b", "2.4-1e"],
        "skills": ["practical", "calculate"],
    },
    "qa": {
        "practical_topic": "Qualitative analysis",
        "syllabus_codes": [],
        "learning_outcomes": [],
        "skills": ["practical"],
    },
}


def spec(kind: str, marks: int) -> dict:
    out = dict(R[kind])
    out["marks"] = marks
    out["question_type"] = "practical"
    out["difficulty"] = 4
    return out


PAPERS = {
    "draft/9701_m24_qp_33": {
        "1": spec("rate", 17),
        "2": spec("thermo", 10),
        "3": spec("qa", 13),
    },
    "draft/9701_w24_qp_31": {
        "1": spec("thermo", 12),
        "2": spec("grav", 14),
        "3": spec("qa", 14),
    },
    "draft/9701_w24_qp_33": {
        "1": spec("grav", 10),
        "2": spec("titration", 15),
        "3": spec("qa", 15),
    },
    "draft/9701_w24_qp_34": {
        "1": spec("rate", 16),
        "2": spec("grav", 12),
        "3": spec("qa", 12),
    },
    "draft/9701_w24_qp_35": {
        "1": spec("thermo", 12),
        "2": spec("grav", 14),
        "3": spec("qa", 14),
    },
    "draft/9701_w24_qp_36": {
        "1": spec("gas", 11),
        "2": spec("grav", 13),
        "3": spec("qa", 16),
    },
}


def main() -> None:
    for draft, tags in PAPERS.items():
        apply_tags(ROOT / draft, tags, as_only=True)


if __name__ == "__main__":
    main()
