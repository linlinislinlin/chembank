"""Examiner report parse + merge (qualitative CIE ER; no invented stats)."""

from __future__ import annotations

import json
from pathlib import Path

from chembank.examiner_report import (
    DIFFICULTY_FROM_BAND,
    merge_er_into_question,
    merge_er_into_tagged_dir,
    parse_examiner_report_text,
    write_examiner_report_json,
)
from chembank.export_md import question_to_markdown

SAMPLE_ER = """
Cambridge International Advanced Subsidiary and Advanced Level
9701 Chemistry June 2021
Principal Examiner Report for Teachers

CHEMISTRY

Paper 9701/11
Multiple Choice

Question
Number
Key

Question
Number
Key

1
C

2
C

7
C

8
A

14
A

20
A

General comments

This examination paper provided a difficult challenge to the candidates.

Questions 7, 8, 18 and 23 were found to be easy. Questions 14, 20, 25, 31, 38 and 39 were found to be
particularly difficult.

Comments on specific questions

Question 14

The most commonly chosen incorrect answer was C.
The solid residue does not react with HCl(aq).

Question 20

The most commonly chosen incorrect answer was B.
The product nitrile has the carbon atom of the nitrile group.

Paper 9701/12
Multiple Choice

Question
Number
Key

1
C

General comments

Questions 4, 9 were found to be easy. Questions 3, 7 were found to be particularly difficult.

Comments on specific questions

Question 3

The most commonly chosen incorrect answer was D.
Z does indeed have the highest boiling point.
"""


def test_parse_glued_pdf_tokens_for_bands():
    """Real CIE ER extract often glues 'and23were' / 'Questions14' / 'wasC'."""
    glued = """
9701 Chemistry June 2021
Principal Examiner Report for Teachers
Paper 9701/11
Multiple Choice
1 C
7 C
14 A
General comments
Questions 7, 8, 18 and23were found to be easy. Questions14, 20, 25, 31, 38 and39 were found to be
particularly difficult.
Comments on specific questions
Question 14
The most commonly chosen incorrect answer wasC.
Ruling outC andD.
"""
    data = parse_examiner_report_text(glued, source_name="glued.pdf")
    p11 = data["papers"]["11"]
    assert p11["easy_questions"] == [7, 8, 18, 23]
    assert 14 in p11["difficult_questions"]
    assert p11["questions"]["14"]["common_incorrect"] == "C"
    assert "was C" in p11["questions"]["14"]["examiner_notes"]


def test_parse_june_2021_paper11_bands_and_comments():
    data = parse_examiner_report_text(SAMPLE_ER, source_name="sample.pdf")
    assert data["year"] == 2021
    assert data["session"] == "MJ"
    assert data["season_token"] == "s21"
    assert "11" in data["papers"] and "12" in data["papers"]

    p11 = data["papers"]["11"]
    assert p11["easy_questions"] == [7, 8, 18, 23]
    assert p11["difficult_questions"] == [14, 20, 25, 31, 38, 39]
    assert p11["stats"]["questions_with_numeric_facility"] == 0
    assert p11["stats"]["questions_with_comments"] == 2

    q14 = p11["questions"]["14"]
    assert q14["examiner_band"] == "particularly_difficult"
    assert q14["difficulty"] == DIFFICULTY_FROM_BAND["particularly_difficult"]
    assert q14["facility"] is None
    assert q14["percent_correct"] is None
    assert q14["common_incorrect"] == "C"
    assert q14["er_year"] == 2021
    assert q14["er_session"] == "MJ"
    assert q14["er_paper"] == 11
    assert "solid residue" in (q14["examiner_notes"] or "")

    q7 = p11["questions"]["7"]
    assert q7["examiner_band"] == "easy"
    assert q7["difficulty"] == 2
    assert q7["examiner_notes"] is None


def test_merge_updates_difficulty_only_when_banded():
    base = {
        "id": "cie-9701-2021-mj-p11-q14",
        "question": "14",
        "difficulty": 3,
        "misconceptions": [],
        "syllabus_codes": ["10.1"],
    }
    er_q = {
        "er_year": 2021,
        "er_session": "MJ",
        "er_paper": 11,
        "facility": None,
        "percent_correct": None,
        "discrimination": None,
        "examiner_band": "particularly_difficult",
        "difficulty": 5,
        "difficulty_source": "examiner_report_qualitative",
        "common_incorrect": "C",
        "common_errors": ["Most commonly chosen incorrect answer was C."],
        "examiner_notes": "Notes here.",
    }
    merged = merge_er_into_question(
        base, er_q, source_path="raw/reports/9701_2021_s21_er.pdf"
    )
    assert merged["difficulty"] == 5
    assert merged["er_year"] == 2021
    assert merged["examiner_report"]["year"] == 2021
    assert merged["facility"] is None
    assert merged["common_incorrect"] == "C"
    assert "Common wrong option: C" in merged["misconceptions"]


def test_merge_tagged_dir_year_scoped(tmp_path: Path):
    data = parse_examiner_report_text(SAMPLE_ER, source_name="sample.pdf")
    out = write_examiner_report_json(data, paper=11)
    assert "9701_s21_er_11.json" in str(out)

    tagged = tmp_path / "tagged"
    tagged.mkdir()
    for n, diff in [("7", 3), ("14", 3), ("1", 2)]:
        (tagged / f"q{n}.json").write_text(
            json.dumps(
                {
                    "id": f"cie-9701-2021-mj-p11-q{n}",
                    "question": n,
                    "difficulty": diff,
                    "misconceptions": [],
                    "syllabus_codes": ["1.1"],
                    "body": f"{n} stem",
                    "mark_scheme": "Answer: **C**",
                }
            ),
            encoding="utf-8",
        )

    er = json.loads(out.read_text(encoding="utf-8"))
    merge_er_into_tagged_dir(
        tagged, er, paper=11, source_path="raw/reports/9701_2021_s21_er.pdf"
    )
    q7 = json.loads((tagged / "q7.json").read_text(encoding="utf-8"))
    q14 = json.loads((tagged / "q14.json").read_text(encoding="utf-8"))
    q1 = json.loads((tagged / "q1.json").read_text(encoding="utf-8"))
    assert q7["difficulty"] == 2
    assert q14["difficulty"] == 5
    assert q14["examiner_notes"]
    assert q1["er_year"] == 2021
    assert q1.get("examiner_notes") in (None, "")
    assert q1["difficulty"] == 2  # unchanged — no band


def test_markdown_includes_examiner_section():
    md = question_to_markdown(
        {
            "id": "cie-9701-2021-mj-p11-q14",
            "year": 2021,
            "session": "MJ",
            "paper": 11,
            "question": "14",
            "syllabus_codes": ["10.1"],
            "topic_titles": ["Group 2"],
            "difficulty": 5,
            "difficulty_source": "examiner_report_qualitative",
            "examiner_band": "particularly_difficult",
            "er_year": 2021,
            "er_session": "MJ",
            "er_paper": 11,
            "examiner_report_source": "raw/reports/9701_2021_s21_er.pdf",
            "facility": None,
            "percent_correct": None,
            "common_incorrect": "C",
            "common_errors": ["Most commonly chosen incorrect answer was C."],
            "examiner_notes": "The solid residue does not react with HCl(aq).",
            "body": "14 stem",
            "mark_scheme": "Answer: **A**",
            "ms_answer": "A",
        }
    )
    assert "## Examiner report" in md
    assert "particularly_difficult" in md
    assert "er_year: 2021" in md
    assert "facility: null" in md or "facility:" in md
    assert "year-scoped" in md
