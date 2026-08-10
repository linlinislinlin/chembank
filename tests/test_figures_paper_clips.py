"""Paper-clip geometry: question numbers vs Section B statement digits."""

from __future__ import annotations

from pathlib import Path

import pytest

from chembank.figures import (
    _clip_has_option_letters_ad,
    _has_abcd_combo_options,
    _paper_clip_matches_question,
    _paper_clip_text,
    question_paper_clips,
)

QP11 = Path(__file__).resolve().parents[1] / "raw" / "papers" / "9701_s21_qp_11.pdf"
QP12 = Path(__file__).resolve().parents[1] / "raw" / "papers" / "9701_s21_qp_12.pdf"


@pytest.mark.skipif(not QP11.exists(), reason="local QP PDF not present")
def test_q3_paper_clip_is_phosphorus_not_calcium():
    clips = question_paper_clips(QP11)
    assert "3" in clips
    fig = clips["3"]
    assert fig.page == 2
    import fitz

    doc = fitz.open(QP11)
    try:
        page = doc[fig.page - 1]
        clip = fitz.Rect(fig.x0, fig.y0, fig.x1, fig.y1)
        text = page.get_text("text", clip=clip)
    finally:
        doc.close()
    assert "Phosphorus" in text
    assert "PCl" in text
    assert "pyramidal" in text
    assert "Calcium is a stronger reducing agent" not in text


@pytest.mark.skipif(not QP11.exists(), reason="local QP PDF not present")
def test_q1_and_q36_not_cross_contaminated():
    clips = question_paper_clips(QP11)
    import fitz

    doc = fitz.open(QP11)
    try:
        t1 = _paper_clip_text(doc, clips["1"])
        t36 = _paper_clip_text(doc, clips["36"])
    finally:
        doc.close()
    assert "largest number of hydrogen" in t1
    assert "Magnesium carbonate" not in t1
    assert "36" in t36 and "Magnesium carbonate" in t36
    assert "Calcium is a stronger reducing agent" in t36


def test_reject_foreign_statement_crop():
    assert _paper_clip_matches_question(
        "3", "3 Phosphorus forms two chlorides.\nA pyramidal\nB tetrahedral\nC x\nD y"
    )
    assert not _paper_clip_matches_question(
        "3", "3 Calcium is a stronger reducing agent than magnesium."
    )
    assert not _paper_clip_matches_question("3", "1 Magnesium carbonate decomposes.")


@pytest.mark.skipif(not QP11.exists(), reason="local QP PDF not present")
def test_section_b_clips_include_abcd_combo_key():
    """Statement-combo crops must include A–D (1,2 and 3 / 1 and 2 only)."""
    import fitz

    clips = question_paper_clips(QP11)
    doc = fitz.open(QP11)
    try:
        for q in ("31", "35", "36"):
            assert q in clips, f"missing paper clip for q{q}"
            text = _paper_clip_text(doc, clips[q])
            assert _has_abcd_combo_options(text), f"q{q} missing A–D combo key"
            assert _clip_has_option_letters_ad(text), f"q{q} missing A/D letters"
            assert len(clips[q].bands) >= 2, f"q{q} should stitch key under stem"
    finally:
        doc.close()


@pytest.mark.skipif(not QP12.exists(), reason="local QP PDF not present")
def test_p12_q31_ions_clip_includes_abcd():
    import fitz

    clips = question_paper_clips(QP12)
    assert "31" in clips
    doc = fitz.open(QP12)
    try:
        text = _paper_clip_text(doc, clips["31"])
    finally:
        doc.close()
    assert "electrons equal to the number of neutrons" in text
    assert _has_abcd_combo_options(text)
    assert _clip_has_option_letters_ad(text)
    assert clips["31"].bands[-1].y1 > clips["31"].bands[0].y0 or len(
        clips["31"].bands
    ) == 2
