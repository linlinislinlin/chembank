"""Vault quality audit gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from chembank.audit import (
    AuditResult,
    Finding,
    _audit_markdown,
    format_audit_report,
)
from chembank.syllabus import flatten_codes, flatten_learning_outcomes, load_syllabus

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "vault"


@pytest.mark.skipif(
    not (VAULT / "questions").exists()
    or not list((VAULT / "questions").glob("cie-9701-2021-mj-p11-q*.md")),
    reason="vault p11 exports not present",
)
def test_audit_p11_passes():
    from chembank.audit import audit_papers

    result = audit_papers(paper_refs=["s21:11"], vault_dir=VAULT, questions_dir=ROOT / "questions")
    assert result.checked == 40
    assert result.failed == 0, format_audit_report(result)


def test_audit_flags_empty_lo(tmp_path: Path):
    qdir = tmp_path / "questions"
    qdir.mkdir()
    assets = tmp_path / "assets"
    assets.mkdir()
    qid = "cie-9701-2021-mj-p11-q99"
    (assets / f"{qid}-paper.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    md = qdir / f"{qid}.md"
    md.write_text(
        "---\n"
        "id: cie-9701-2021-mj-p11-q99\n"
        "question: '99'\n"
        "syllabus_codes: ['3.1']\n"
        "learning_outcomes: []\n"
        "facility: 55\n"
        "percent_correct: 55\n"
        "---\n\n"
        "## Question\n\n"
        f"![[assets/{qid}-paper.png]]\n\n"
        "99 Stem here\n"
        "A one\nB two\nC three\nD four\n",
        encoding="utf-8",
    )
    syl = load_syllabus()
    findings = _audit_markdown(
        md,
        vault_dir=tmp_path,
        questions_dir=None,
        allowed_codes=flatten_codes(syl),
        allowed_los=flatten_learning_outcomes(syl),
    )
    codes = {f.code for f in findings}
    assert "empty_LO" in codes
    assert "invented_facility" in codes


def test_format_audit_report_empty():
    r = AuditResult(checked=2, passed=2)
    text = format_audit_report(r)
    assert "2 pass" in text
    assert "All checks passed" in text
    r2 = AuditResult(checked=1, passed=0, findings=[Finding("q1", "empty_LO")])
    assert "FAIL" in format_audit_report(r2)


def test_audit_flags_tiny_png_and_empty_body(tmp_path: Path):
    qdir = tmp_path / "questions"
    qdir.mkdir()
    assets = tmp_path / "assets"
    assets.mkdir()
    qid = "cie-9701-2021-mj-p11-q98"
    (assets / f"{qid}-paper.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
    md = qdir / f"{qid}.md"
    md.write_text(
        "---\n"
        "id: cie-9701-2021-mj-p11-q98\n"
        "question: '98'\n"
        "syllabus_codes: ['3.1']\n"
        "learning_outcomes: ['3.1-1']\n"
        "---\n\n"
        "## Question\n\n"
        f"![[assets/{qid}-paper.png]]\n\n",
        encoding="utf-8",
    )
    syl = load_syllabus()
    findings = _audit_markdown(
        md,
        vault_dir=tmp_path,
        questions_dir=None,
        allowed_codes=flatten_codes(syl),
        allowed_los=flatten_learning_outcomes(syl),
    )
    codes = {f.code for f in findings}
    assert "tiny_paper_png" in codes
    assert "empty_question_body" in codes


def test_clip_option_letters_abcd():
    from chembank.figures import (
        _clip_has_option_letters_abcd,
        _clip_option_letters_found,
    )

    horiz = "2 In which pair…\nA  Ar+   B  B   C  F   D  Se-"
    assert {"A", "B", "C", "D"} <= _clip_option_letters_found(horiz)
    assert _clip_has_option_letters_abcd(horiz)

    section_b = (
        "36 Which statements are correct?\n"
        "1 Magnesium…\n2 Calcium…\n3 Calcium…\n"
        "The responses A to D should be selected on the basis of\n"
        "A  1, 2 and 3 are correct\n"
        "B  1 and 2 only are correct\n"
        "C  2 and 3 only are correct\n"
        "D  1 only is correct\n"
    )
    assert _clip_has_option_letters_abcd(section_b)

    truncated = "31 Which statements…\n1 foo\n2 bar\n3 baz"
    assert not _clip_has_option_letters_abcd(truncated)
