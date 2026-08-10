"""Symbol recovery against the local June 2021 Paper 11 (if present)."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
QP = ROOT / "raw" / "papers" / "9701_s21_qp_11.pdf"


@pytest.mark.skipif(not QP.exists(), reason="local QP PDF not present")
def test_q4_delta_h_symbols_recovered():
    from chembank.extract import extract_pdf_text
    from chembank.split import split_questions

    text = extract_pdf_text(QP)
    chunks = {c.question: c for c in split_questions(text)}
    q4 = chunks["4"].text

    assert "ΔH₁⦵" in q4
    assert "ΔH₂⦵" in q4
    assert "ΔH₃⦵" in q4
    assert "ΔHc⦵" in q4
    assert "2 ΔH₃⦵" in q4 or "2ΔH₃⦵" in q4
    # Must not leave the old blank-hole stem
    assert "        is the standard enthalpy" not in q4


@pytest.mark.skipif(not QP.exists(), reason="local QP PDF not present")
def test_multiply_sign_normalized():
    from chembank.extract import extract_pdf_text

    text = extract_pdf_text(QP)
    assert "×" in text
    assert "\uf0b4" not in text
