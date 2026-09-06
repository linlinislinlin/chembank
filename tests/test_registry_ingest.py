"""Unit tests for paper registry parsing (no PDF required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from chembank.registry import (
    default_paths,
    parse_paper_ref,
    parse_season,
    paper_id,
    save_papers_yaml,
    upsert_paper,
    write_manifest,
)


def test_parse_season_s21():
    letter, year, session = parse_season("s21")
    assert letter == "s"
    assert year == 2021
    assert session == "MJ"


def test_parse_refs():
    a = parse_paper_ref("s21", "12")
    assert a.id == "9701_s21_qp_12"
    assert a.year == 2021
    assert a.session == "MJ"
    assert a.paper == 12
    assert a.qp.endswith("9701_s21_qp_12.pdf")
    assert a.ms.endswith("9701_s21_ms_12.pdf")
    assert a.er and a.er.endswith("9701_2021_s21_er.pdf")

    b = parse_paper_ref("9701_s21_qp_11")
    assert b.id == "9701_s21_qp_11"
    assert b.paper == 11

    c = parse_paper_ref("s21:11")
    assert c.id == "9701_s21_qp_11"


def test_0620_paper_kind_and_paths():
    from chembank.registry import (
        paper_kind,
        default_vault_for_paper,
        default_questions_dir_for_paper,
        parse_paper_ref,
    )

    ref = parse_paper_ref("0620_s25_qp_21")
    assert ref.syllabus_code == "0620"
    assert ref.year == 2025
    assert ref.session == "MJ"
    assert ref.paper == 21
    assert paper_kind(21, "0620") == "mcq"
    assert paper_kind(41, "0620") == "structured"
    assert paper_kind(61, "0620") == "practical"
    # 9701 mapping must stay inverted relative to 0620
    assert paper_kind(21, "9701") == "structured"
    assert paper_kind(11, "9701") == "mcq"
    assert default_vault_for_paper(21, "0620").name == "vault-igcse"
    assert default_vault_for_paper(41, "0620").name == "vault-igcse-structured"
    assert default_vault_for_paper(61, "0620").name == "vault-igcse-practical"
    assert default_questions_dir_for_paper(21, "0620").name == "questions-igcse"


def test_0620_lo_parent():
    from chembank.syllabus import parent_code_for_lo, syllabus_path_for

    assert parent_code_for_lo("1.1-C1") == "1.1"
    assert parent_code_for_lo("3.3-S4") == "3.3"
    assert parent_code_for_lo("3.1-1") == "3.1"
    assert syllabus_path_for("0620").name == "cie-0620-igcse-chemistry.yaml"


def test_default_paths_w22():
    ref = default_paths(season="w22", paper=13)
    assert ref.session == "ON"
    assert ref.year == 2022
    assert ref.id == "9701_w22_qp_13"
    assert paper_id("9701", "w22", 13) == ref.id


def test_upsert_and_manifest(tmp_path: Path):
    reg = tmp_path / "papers.yaml"
    man = tmp_path / "manifest.json"
    ref = parse_paper_ref("s21", "11")
    ref.status = "extracted"
    upsert_paper(ref, reg)
    data = reg.read_text(encoding="utf-8")
    assert "9701_s21_qp_11" in data
    write_manifest([ref], path=man)
    assert "9701_s21_qp_11" in man.read_text(encoding="utf-8")


def test_bad_ref():
    with pytest.raises(ValueError):
        parse_paper_ref("not-a-paper")
