"""Duplicate A–D under paper embed + next-question bleed guards."""

from __future__ import annotations

from pathlib import Path

import pytest

from chembank.export_vault import _strip_duplicate_mcq_options
from chembank.figures import (
    _clip_contains_next_question,
    assign_figures_to_questions,
)

ROOT = Path(__file__).resolve().parents[1]
M21_QP12 = ROOT / "raw" / "papers" / "9701_m21_qp_12.pdf"
S21_QP11 = ROOT / "raw" / "papers" / "9701_s21_qp_11.pdf"


def test_strip_duplicate_mcq_options_packed_line():
    body = (
        "1 The table shows particles W, X, Y, and Z.\n"
        "Which pair represents isotopes?\n"
        "A W and Y B W and Z C X and Y D X and Z\n"
    )
    out = _strip_duplicate_mcq_options(body, has_paper_clip=True)
    assert "A W and Y" not in out
    assert "isotopes" in out
    assert _strip_duplicate_mcq_options(body, has_paper_clip=False) == body


def test_strip_duplicate_mcq_options_vertical():
    body = "1 Stem?\nA one\nB two\nC three\nD four\n"
    out = _strip_duplicate_mcq_options(body, has_paper_clip=True)
    assert out == "1 Stem?"


def test_clip_contains_next_question():
    assert _clip_contains_next_question(
        "1 The table…\nA W and Y\n2 Where in the Periodic Table",
        "1",
    )
    assert not _clip_contains_next_question(
        "1 The table…\nA W and Y\nB W and Z\nC X and Y\nD X and Z",
        "1",
    )
    # Group/Period option grid must not look like q3 bleed
    assert not _clip_contains_next_question(
        "2 Where…\nGroup\nPeriod\nA\n13\n3\nB\n13\n4\nC\n15\n3\nD\n15\n4\n",
        "2",
    )


@pytest.mark.skipif(not M21_QP12.exists(), reason="local QP PDF not present")
def test_m21_q1_no_prose_option_or_table_focus():
    """Isotope data-table Q1: paper clip only — no redundant Diagram crops."""
    assigned = assign_figures_to_questions(M21_QP12)
    assert assigned.get("1") in (None, [])


@pytest.mark.skipif(not S21_QP11.exists(), reason="local QP PDF not present")
def test_structure_mcq_still_gets_focus_crop():
    assigned = assign_figures_to_questions(S21_QP11)
    assert assigned.get("21"), "structure options should still produce a focus crop"
