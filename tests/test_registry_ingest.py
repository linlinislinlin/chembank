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
