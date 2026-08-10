"""Structured paper kind, MS bind, and vault routing (no PDF required)."""

from __future__ import annotations

from pathlib import Path

from chembank.registry import (
    DEFAULT_VAULT_MCQ,
    DEFAULT_VAULT_PRACTICAL,
    DEFAULT_VAULT_STRUCTURED,
    default_questions_dir_for_paper,
    default_vault_for_paper,
    paper_component,
    paper_kind,
    parse_paper_ref,
)
from chembank.split import (
    detect_paper_style,
    parse_structured_mark_scheme,
    split_questions,
    write_split_output,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_paper_kind_routing():
    assert paper_component(11) == 1
    assert paper_component(21) == 2
    assert paper_component(31) == 3
    assert paper_component(42) == 4
    assert paper_kind(11) == "mcq"
    assert paper_kind(12) == "mcq"
    assert paper_kind(21) == "structured"
    assert paper_kind(23) == "structured"
    assert paper_kind(31) == "practical"
    assert paper_kind(32) == "practical"
    assert paper_kind(35) == "practical"
    assert paper_kind(41) == "structured"
    assert paper_kind(51) == "structured"
    assert default_vault_for_paper(12) == DEFAULT_VAULT_MCQ
    assert default_vault_for_paper(21) == DEFAULT_VAULT_STRUCTURED
    assert default_vault_for_paper(31) == DEFAULT_VAULT_PRACTICAL
    assert default_questions_dir_for_paper(21).name == "questions-structured"
    assert default_questions_dir_for_paper(31).name == "questions-practical"


def test_parse_ref_structured_paths():
    ref = parse_paper_ref("s21", "21")
    assert ref.id == "9701_s21_qp_21"
    assert ref.paper == 21
    assert paper_kind(ref.paper) == "structured"
    assert default_vault_for_paper(ref.paper) == Path("vault-structured")


def test_parse_ref_practical_paths():
    ref = parse_paper_ref("s21", "31")
    assert ref.id == "9701_s21_qp_31"
    assert ref.paper == 31
    assert paper_kind(ref.paper) == "practical"
    assert default_vault_for_paper(ref.paper) == Path("vault-practical")
    assert default_questions_dir_for_paper(ref.paper) == Path("questions-practical")


def test_structured_fixture_split_and_ms(tmp_path: Path):
    from chembank.split import expand_structured_part_chunks
    from chembank.structured_parts import parse_structured_ms_parts

    qp = (FIXTURES / "structured_mini_qp.txt").read_text(encoding="utf-8")
    ms = (FIXTURES / "structured_mini_ms.txt").read_text(encoding="utf-8")
    assert detect_paper_style(qp) == "structured"
    chunks = split_questions(qp)
    assert [c.question for c in chunks] == ["1", "2"]
    assert any("(a)" in p for p in chunks[0].parts)

    parts = expand_structured_part_chunks(chunks)
    labels = [c.question for c in parts]
    assert "1(a)" in labels
    assert "1(b)(i)" in labels
    assert "1(b)(ii)" in labels
    assert "2(a)" in labels
    assert "2(b)" in labels

    blocks = parse_structured_mark_scheme(ms)
    assert "1" in blocks and "2" in blocks
    assert "(a)" in blocks["1"]
    assert "ethene" in blocks["2"].lower() or "C2H4" in blocks["2"] or "displayed" in blocks["2"].lower()

    # Fixture MS uses "Question N" headers — part heads may be empty; still write parts
    out = tmp_path / "draft"
    written = write_split_output(qp, out, source_name="mini", mark_scheme_text=ms)
    assert len(written) >= 5
    assert (out / "q1a.txt").is_file() or (out / "q1b-i.txt").is_file()
    assert (out / "ms_structured.json").is_file()

    # Clean part-headed MS
    clean_ms = (
        "Question\nAnswer\nMarks\n"
        "1(a)\naverage mass (1)\n"
        "1(b)(i)\n1.00 (1)\n"
        "1(b)(ii)\nwater (1)\n"
        "2(a)\ndisplayed C2H4 (1)\n"
        "2(b)\nH2 AND Ni (1)\n"
    )
    ms_parts = parse_structured_ms_parts(clean_ms)
    assert "1(a)" in ms_parts and "2(b)" in ms_parts


def test_split_parts_no_next_letter_bleed_and_shared_stem():
    """(a)(iii) must not swallow (b) preamble; (b)(i) keeps Q stem + (b) text."""
    from chembank.structured_parts import split_main_question_into_parts

    text = (
        "1 Ethanedioic acid, HO2CCO2H, has Mr = 90.0.\n"
        "(a) (i) Define relative molecular mass.\n"
        "[2]\n"
        "(ii) State the empirical formula.\n"
        "[1]\n"
        "(iii) Calculate atoms of carbon in 0.18 g.\n"
        "[3]\n"
        "(b) Solid ethanedioic acid reacts with aqueous calcium ions.\n"
        "CaC2O4 breaks down when heated.\n"
        "(i) Construct an equation for heating CaC2O4.\n"
        "[2]\n"
        "(ii) Identify the reaction type.\n"
        "[1]\n"
    )
    parts = {pid.label: body for pid, body in split_main_question_into_parts("1", text)}
    assert "1(a)(iii)" in parts and "1(b)(i)" in parts

    a_iii = parts["1(a)(iii)"]
    assert "Calculate atoms of carbon" in a_iii
    assert "Mr = 90.0" in a_iii
    assert "Solid ethanedioic acid reacts" not in a_iii
    assert "aqueous calcium ions" not in a_iii

    b_i = parts["1(b)(i)"]
    assert "Mr = 90.0" in b_i
    assert "Solid ethanedioic acid reacts" in b_i
    assert "Construct an equation" in b_i
    assert "Identify the reaction type" not in b_i


def test_structured_band_span_honours_hard_end_on_next_page():
    """Next-page continuation must not pad past end_y (letter/Q bleed)."""
    from types import SimpleNamespace

    from chembank.figures import _structured_band_span

    class _Page:
        def __init__(self):
            self.rect = SimpleNamespace(x1=595.0, y1=842.0)

    doc = [_Page(), _Page()]
    # Part ends just before next marker at y=56.8 on page 1
    bands = _structured_band_span(
        doc, start_page=0, start_y=600.0, end_page=1, end_y=54.8
    )
    # Tiny top sliver on next page must be omitted (would only catch next part)
    assert len(bands) == 1
    assert bands[0].page == 1
    assert bands[0].y1 >= 800.0

    # Real continuation content before next marker is kept, without padding past end
    bands2 = _structured_band_span(
        doc, start_page=0, start_y=600.0, end_page=1, end_y=120.0
    )
    assert len(bands2) == 2
    assert bands2[1].page == 2
    assert bands2[1].y1 == 120.0


def test_clip_contains_next_question_tolerates_pdf_controls():
    from chembank.figures import _clip_contains_next_question

    assert _clip_contains_next_question("…\n[Total: 10]\n\n2\t\x07Carbon monoxide", "1")
    assert not _clip_contains_next_question("option 2 B only", "1")
