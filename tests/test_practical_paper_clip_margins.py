"""Practical paper clips must include CIE right-edge mark grids (I–IV)."""

from __future__ import annotations

from pathlib import Path

import pytest

from chembank.figures import (
    _PAPER_CLIP_RIGHT_INSET_PRACTICAL,
    _paper_clip_x_bounds,
    question_paper_clips,
)

QP31 = Path(__file__).resolve().parents[1] / "raw" / "papers" / "9701_s21_qp_31.pdf"


@pytest.mark.skipif(not QP31.exists(), reason="local QP PDF not present")
def test_practical_clip_uses_wide_right_margin():
    import fitz

    doc = fitz.open(QP31)
    try:
        page = doc[0]
        _x0, x1 = _paper_clip_x_bounds(page, QP31)
        assert page.rect.x1 - x1 == pytest.approx(
            _PAPER_CLIP_RIGHT_INSET_PRACTICAL, abs=0.01
        )
        assert page.rect.x1 - x1 <= 16.0
    finally:
        doc.close()


@pytest.mark.skipif(not QP31.exists(), reason="local QP PDF not present")
def test_s21_p31_q2_includes_right_mark_grid():
    """Gravimetric Q2 has I–IV examiner boxes whose right edge is ~30pt in."""
    import fitz

    clips = question_paper_clips(QP31)
    assert "2" in clips
    doc = fitz.open(QP31)
    try:
        for band in clips["2"].bands:
            page = doc[band.page - 1]
            right_inset = page.rect.x1 - band.x1
            assert right_inset <= 16.0, f"right_inset={right_inset:.1f}"
            # Rightmost vertical strokes of the I–IV grid must fall inside clip
            max_x1 = 0.0
            for d in page.get_drawings():
                r = d.get("rect")
                if r is None:
                    continue
                if r.y1 < band.y0 - 2 or r.y0 > band.y1 + 2:
                    continue
                if r.x1 > page.rect.x1 - 80:
                    max_x1 = max(max_x1, float(r.x1))
            if max_x1:
                assert band.x1 + 0.5 >= max_x1, (
                    f"clip x1={band.x1:.1f} truncates drawing at {max_x1:.1f}"
                )
    finally:
        doc.close()
