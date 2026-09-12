"""UKChO extract + ingest contract.

``ukcho_extract`` reads a real PDF, so these tests drive it with a fake document
that mimics PyMuPDF's ``page.get_text("dict")`` shape. That keeps the *structural*
rules pinned without shipping a copyrighted past paper:

* sub-part labels create independent parts (never folded into the part letter),
* ``(a)`` immediately followed by ``(a)(i)`` is a container, not a record,
* the image-credits page is not mistaken for a question,
* text sharing the label line ("(ii) State the value.") is kept.

``ukcho_ingest`` is pure data shuffling, so it is tested end-to-end on a tmp vault.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from chembank import ukcho as U
from chembank import ukcho_extract as X
from chembank import ukcho_ingest as G

PAGE_H = 800.0


class FakePage:
    """Minimal stand-in for a PyMuPDF page."""

    def __init__(self, lines: list[tuple[float, float, str]]) -> None:
        self._lines = lines
        self.rect = type("Rect", (), {"height": PAGE_H})()

    def get_text(self, kind: str) -> dict:
        assert kind == "dict"
        return {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {
                            "bbox": (x, y, x + 220.0, y + 12.0),
                            "spans": [{"text": text}],
                        }
                    ],
                }
                for y, x, text in self._lines
            ]
        }


class FakeDoc:
    def __init__(self, pages: list[list[tuple[float, float, str]]]) -> None:
        self._pages = [FakePage(p) for p in pages]

    @property
    def page_count(self) -> int:
        return len(self._pages)

    def __getitem__(self, i: int) -> FakePage:
        return self._pages[i]


@pytest.fixture
def doc() -> FakeDoc:
    """A one-question paper exercising every label shape."""
    return FakeDoc(
        [
            [
                (60.0, 40.0, "Q1 This question is about the chemistry of nitrogen."),
                (100.0, 50.0, "(a)"),
                (120.0, 50.0, "Nitrogen gas is unreactive at room temperature."),
                (150.0, 50.0, "(b)"),
                (170.0, 50.0, "The table shows some bond enthalpy data."),
                (200.0, 110.0, "(i)"),
                (220.0, 110.0, "Describe the trend in the data."),
                (250.0, 110.0, "(ii) State the value of the bond enthalpy."),
            ],
            [
                (50.0, 40.0, "Q2 A question about a transition metal complex."),
                (80.0, 50.0, "(a) Calculate the mass of the complex."),
            ],
        ]
    )


# --- label detection ------------------------------------------------------


def test_credits_page_is_not_treated_as_a_question() -> None:
    credits = FakeDoc([[(60.0, 40.0, "Q1 The image is © Royal Society of Chemistry")]])
    assert X.find_labels(credits) == []


def test_labels_capture_same_line_trailing_text(doc: FakeDoc) -> None:
    labels = {lb.text: lb for lb in X.find_labels(doc)}
    # "(ii) State the value ..." shares its line with the question text, and the
    # trailing text must be kept (it is the whole sub-question).
    shared = labels["(ii) State the value of the bond enthalpy."]
    assert shared.subpart == "ii"
    assert shared.rest == "State the value of the bond enthalpy."
    q1 = next(lb for lb in X.find_labels(doc) if lb.kind == "question")
    assert q1.question == 1
    assert q1.rest == "This question is about the chemistry of nitrogen."


def test_label_geometry_separates_parts_from_subparts(doc: FakeDoc) -> None:
    kinds = {(lb.kind, lb.text): (lb.x, lb.y) for lb in X.find_labels(doc)}
    assert kinds[("part", "(a)")][0] <= X.LEFT_X_MAX
    assert X.SUBPART_X_MIN <= kinds[("subpart", "(i)")][0] <= X.SUBPART_X_MAX


# --- splitting ------------------------------------------------------------


def test_split_parts_makes_subparts_independent_records(doc: FakeDoc) -> None:
    parts, stems = X.split_parts(doc)
    keys = [p.key for p in parts]

    # (b) is a container for (i)/(ii) and must not become its own record.
    assert keys == ["1a", "1b-i", "1b-ii", "2a"]
    assert "1b" not in keys

    by_key = {p.key: p for p in parts}
    assert by_key["1b-i"].subpart == "i"
    assert by_key["1b-i"].part == "b"
    # Container text is folded into the first sub-part, not dropped.
    assert "The table shows some bond enthalpy data." in by_key["1b-i"].text
    assert "Describe the trend in the data." in by_key["1b-i"].text
    # The next sub-part must not inherit the container text.
    assert "The table shows some bond enthalpy data." not in by_key["1b-ii"].text

    assert stems[1].startswith("This question is about the chemistry of nitrogen.")
    assert stems[2].startswith("A question about a transition metal complex.")


def test_part_labels_and_keys() -> None:
    p = X.Part(question=6, part="b", subpart="ii", page=0, y=1.0, text="t", end_page=0, end_y=2.0)
    assert p.key == "6b-ii"
    assert p.label == "(6b)(ii)"
    plain = X.Part(question=4, part="g", subpart=None, page=0, y=1.0, text="t", end_page=0, end_y=2.0)
    assert plain.key == "4g"
    assert plain.label == "(4g)"
    assert plain.to_dict()["page"] == 1  # 1-based in the manifest


def test_part_ending_at_top_of_next_page_stays_on_its_own_page(doc: FakeDoc) -> None:
    parts, _ = X.split_parts(doc)
    # Q2's (a) is the last label; Q1(b)(ii) must end on page 1 (0-based 0).
    last = next(p for p in parts if p.key == "1b-ii")
    assert last.end_page == 0
    assert last.end_page == last.page


# --- table rows are not sub-questions -------------------------------------
#
# "Complete the table in the answer booklet with the number of peaks in the 13C
# NMR spectrum of: (i) Cubane (ii) Cubane-carboxylic acid ..." labels the rows of
# one table, and the mark scheme grades that table as a single item ("3 marks for
# all five correct"). Those roman labels must not become records of their own.
# The trap is the reverse case: a stem that merely introduces a list, such as
# "Write the number of conjugated C=C bonds in: (i) alpha-carotene (ii)
# beta-carotene", which the mark scheme scores "one mark each" and so keeps both
# items as separate sub-questions.


def test_table_rows_are_folded_into_the_part() -> None:
    table = FakeDoc(
        [
            [
                (60.0, 40.0, "Q3 This question is about cubane"),
                (100.0, 50.0, "(b)"),
                (120.0, 50.0, "Complete the table in the answer booklet with the number of"),
                (135.0, 50.0, "peaks in the 13C NMR spectrum of:"),
                (170.0, 110.0, "(i)"),
                (170.0, 142.0, "Cubane"),
                (195.0, 110.0, "(ii)"),
                (195.0, 142.0, "Cubane-carboxylic acid"),
            ]
        ]
    )
    parts, _ = X.split_parts(table)
    # One record for the whole table, not one per row.
    assert [p.key for p in parts] == ["3b"]
    # The rows survive as text inside that record rather than being lost.
    assert "Cubane" in parts[0].text
    assert "Cubane-carboxylic acid" in parts[0].text


def test_a_two_column_answer_table_is_folded_in_too() -> None:
    """Q2(d) of 2023 writes its rows in two columns, so (iv) precedes (ii)."""
    table = FakeDoc(
        [
            [
                (60.0, 40.0, "Q2 This question is about electronegativity"),
                (100.0, 50.0, "(d) Identify the letter in the answer booklet which represents the"),
                (115.0, 50.0, "position of the following substances."),
                (145.0, 110.0, "(i)"),
                (145.0, 142.0, "AlP"),
                (145.0, 310.0, "(iv)"),
                (145.0, 342.0, "HgO"),
                (170.0, 110.0, "(ii)"),
                (170.0, 142.0, "CsH"),
            ]
        ]
    )
    parts, _ = X.split_parts(table)
    assert [p.key for p in parts] == ["2d"]


def test_a_list_of_items_that_shares_a_stem_is_not_a_table() -> None:
    """The 2026 paper's "one mark each" list must stay two sub-questions."""
    listing = FakeDoc(
        [
            [
                (60.0, 40.0, "Q4 This question is about rice, spice, and mice"),
                (100.0, 50.0, "(b)"),
                (120.0, 50.0, "Write the number of conjugated C=C bonds in:"),
                (150.0, 110.0, "(i)"),
                (150.0, 142.0, "alpha-carotene"),
                (175.0, 110.0, "(ii)"),
                (175.0, 142.0, "beta-carotene"),
            ]
        ]
    )
    parts, _ = X.split_parts(listing)
    assert [p.key for p in parts] == ["4b-i", "4b-ii"]


def test_the_word_table_alone_does_not_condemn_a_run() -> None:
    """2023 Q2(f): "...trends in electronegativity in the periodic table..." is
    prose, and the mark scheme gives "one mark each" for (i)/(ii)/(iii)."""
    prose = FakeDoc(
        [
            [
                (60.0, 40.0, "Q2 This question is about electronegativity"),
                (100.0, 50.0, "(f)"),
                (120.0, 50.0, "Based on trends in electronegativity in the periodic table, identify"),
                (135.0, 50.0, "which point A-P describes."),
                (145.0, 110.0, "(i)"),
                (145.0, 142.0, "CsCl"),
                (170.0, 110.0, "(ii)"),
                (170.0, 142.0, "NaK"),
            ]
        ]
    )
    parts, _ = X.split_parts(prose)
    assert [p.key for p in parts] == ["2f-i", "2f-ii"]


def test_a_run_that_opens_with_an_instruction_is_not_a_table() -> None:
    """A cell is a name or a formula; prose means a real sub-question."""
    instructions = FakeDoc(
        [
            [
                (60.0, 40.0, "Q5 This question is about a synthesis"),
                (100.0, 50.0, "(a)"),
                (110.0, 50.0, "Complete the table in the answer booklet."),
                (130.0, 110.0, "(i)"),
                (130.0, 142.0, "Draw the structure of A."),
                (155.0, 110.0, "(ii)"),
                (155.0, 142.0, "Draw the structure of B."),
            ]
        ]
    )
    parts, _ = X.split_parts(instructions)
    assert [p.key for p in parts] == ["5a-i", "5a-ii"]


def test_credits_page_wording_in_the_plural_is_dropped() -> None:
    """2022 and 2024 write "The images are (c) ..."."""
    credits = FakeDoc([[(60.0, 40.0, "Q4 The images are © Scott Ollington")]])
    assert X.find_labels(credits) == []


# --- table rows are not sub-questions -------------------------------------
#
# Older papers ask the candidate to complete a table, printing the rows on
# indented roman labels: "(i) Cubane", "(ii) Cubane-carboxylic acid". The mark
# scheme grades the whole table as one item ("3 marks for all five correct"), so
# those rows must stay inside their part instead of becoming records of their own.


def _qp(*lines: tuple[float, float, str]) -> FakeDoc:
    """A one-page question paper built from ``(y, x, text)`` lines."""
    return FakeDoc([list(lines)])


def test_table_rows_do_not_become_sub_questions() -> None:
    """2022 Q3(b): five table rows are one sub-question worth three marks."""
    doc = _qp(
        (60.0, 40.0, "Q1 This question is about cubane."),
        (100.0, 50.0, "(b)"),
        (120.0, 50.0, "Complete the table in the answer booklet with the number of"),
        (132.0, 50.0, "peaks in the 13C NMR spectrum of:"),
        (160.0, 108.0, "(i)"),
        (160.0, 143.0, "Cubane"),
        (185.0, 108.0, "(ii)"),
        (185.0, 143.0, "Cubane-carboxylic acid"),
        (210.0, 108.0, "(iii)"),
        (210.0, 143.0, "Cubane-1,2-dicarboxylic acid"),
        (240.0, 50.0, "(c) Explain why cubane is strained."),
    )
    parts, _ = X.split_parts(doc)
    assert [p.key for p in parts] == ["1b", "1c"]
    # The rows stay in the part's own text, so nothing is lost from the paper.
    assert "Complete the table" in parts[0].text
    assert "Cubane-1,2-dicarboxylic acid" in parts[0].text


def test_short_items_sharing_a_stem_stay_sub_questions() -> None:
    """2026 Q4(b): items marked "one mark each" are sub-questions in their own right."""
    doc = _qp(
        (60.0, 40.0, "Q1 This question is about carotene."),
        (100.0, 50.0, "(b)"),
        (120.0, 50.0, "Write the number of conjugated C=C bonds in:"),
        (160.0, 108.0, "(i)"),
        (160.0, 143.0, "a-carotene"),
        (185.0, 108.0, "(ii)"),
        (185.0, 143.0, "b-carotene"),
    )
    parts, _ = X.split_parts(doc)
    assert [p.key for p in parts] == ["1b-i", "1b-ii"]


def test_table_lead_in_does_not_swallow_real_sub_questions() -> None:
    """A table lead-in only merges rows; instruction-bearing labels still split."""
    doc = _qp(
        (60.0, 40.0, "Q1 This question is about something."),
        (100.0, 50.0, "(b)"),
        (120.0, 50.0, "Complete the table below."),
        (160.0, 108.0, "(i)"),
        (160.0, 143.0, "Draw the structure of A."),
        (185.0, 108.0, "(ii)"),
        (185.0, 143.0, "Draw the structure of B."),
    )
    parts, _ = X.split_parts(doc)
    assert [p.key for p in parts] == ["1b-i", "1b-ii"]


def test_periodic_table_is_not_a_table_lead_in() -> None:
    """2023 Q2(f): "trends ... in the periodic table" introduces three sub-questions."""
    doc = _qp(
        (60.0, 40.0, "Q1 This question is about bonding."),
        (100.0, 50.0, "(f)"),
        (120.0, 50.0, "Based on trends in electronegativity in the periodic table,"),
        (132.0, 50.0, "identify where the following substances would be located."),
        (160.0, 108.0, "(i)"),
        (160.0, 143.0, "CsCl"),
        (185.0, 108.0, "(ii)"),
        (185.0, 143.0, "NaK"),
    )
    parts, _ = X.split_parts(doc)
    assert [p.key for p in parts] == ["1f-i", "1f-ii"]


def test_a_lone_short_label_is_not_a_table() -> None:
    """A label with no run to belong to is left alone rather than silently merged."""
    doc = _qp(
        (60.0, 40.0, "Q1 This question is about something."),
        (100.0, 50.0, "(b)"),
        (120.0, 50.0, "Complete the table below."),
        (160.0, 108.0, "(i)"),
        (160.0, 143.0, "Cubane"),
    )
    parts, _ = X.split_parts(doc)
    assert [p.key for p in parts] == ["1b-i"]


def test_credits_page_plural_wording_is_not_a_question() -> None:
    """2022 and 2024 word the credits "The images are © ..."."""
    credits = FakeDoc(
        [[(60.0, 40.0, "Q4 The images are © Scott Ollington and © Dr Alex Thom")]]
    )
    assert X.find_labels(credits) == []


# --- id helpers -----------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("3a", "ukcho-2025-q3a"),
        ("3b-i", "ukcho-2025-q3b-i"),
        ("6b-ii", "ukcho-2025-q6b-ii"),
        ("10c", "ukcho-2025-q10c"),
    ],
)
def test_sub_id_round_trips_the_part_key(key: str, expected: str) -> None:
    assert G.sub_id("ukcho-2025", key) == expected


def test_ingest_ids_match_the_vault_convention() -> None:
    # ukcho_ingest builds ids; ukcho.py parses them back for filtering.
    sid = G.sub_id("ukcho-2025", "3b-ii")
    rec = U.normalize_record({"id": sid, "record_type": "ukcho-subquestion"})
    assert rec["id"] == "ukcho-2025-q3b-ii"


def test_part_sort_key_orders_parts_naturally() -> None:
    keys = ["3b", "3a", "10a", "3b-ii", "3b-i"]
    assert sorted(keys, key=G._part_sort_key) == ["3a", "3b", "3b-i", "3b-ii", "10a"]


# --- build_records --------------------------------------------------------


def _manifest() -> dict:
    return {
        "stems": {"3": "This question is about phenol."},
        "parts": [
            {"question": 3, "part": "a", "subpart": None, "key": "3a", "label": "(3a)",
             "page": 1, "end_page": 1, "text": "raw pdf text a", "clips": ["clips/ukcho-2025-3a-paper.png"]},
            {"question": 3, "part": "b", "subpart": "i", "key": "3b-i", "label": "(3b)(i)",
             "page": 1, "end_page": 1, "text": "raw pdf text b i", "clips": ["clips/ukcho-2025-3b-i-paper.png"]},
            {"question": 3, "part": "b", "subpart": "ii", "key": "3b-ii", "label": "(3b)(ii)",
             "page": 2, "end_page": 2, "text": "raw pdf text b ii", "clips": []},
        ],
    }


def _tagging(omit: str | None = None) -> dict:
    """A complete tagging sheet; ``omit`` leaves one part untagged on purpose."""
    parts: dict = {
        "3a": {"marks": 2, "primary_as_anchor": "Organic Synthesis", "primary_skill": "Deduce",
               "difficulty_level": "Foundation", "question_text": "transcribed a"},
        "3b-i": {"marks": 4, "primary_as_anchor": "Organic Synthesis", "primary_skill": "Draw / Represent",
                 "difficulty_level": "Standard", "question_text": "transcribed b i",
                 "answer": "A", "mark_scheme": "1 mark for curly arrow"},
        # Tagged, but no question_text -> the raw PDF text layer is the fallback.
        "3b-ii": {"marks": 3, "primary_as_anchor": "Organic Synthesis", "primary_skill": "Explain",
                  "difficulty_level": "Standard"},
    }
    if omit:
        parts.pop(omit)
    return {
        "prefix": "ukcho-2025",
        "year": 2025,
        "source_qp": "ukcho_2025_r1_qp.pdf",
        "source_ms": "ukcho_2025_r1_ms.pdf",
        "parents": [{"question_number": 3, "title": "Phenol", "total_marks": 9,
                     "overall_themes": ["Organic"]}],
        "parts": parts,
    }


def test_build_records_derives_ids_links_and_clips() -> None:
    parents, subs, problems = G.build_records(_manifest(), _tagging(omit="3b-ii"))

    assert [p["id"] for p in parents] == ["ukcho-2025-q3"]
    assert parents[0]["sub_question_ids"] == ["ukcho-2025-q3a", "ukcho-2025-q3b-i", "ukcho-2025-q3b-ii"]
    assert parents[0]["stems"] == "This question is about phenol."

    by_id = {s["id"]: s for s in subs}
    assert by_id["ukcho-2025-q3b-i"]["parent_question_id"] == "ukcho-2025-q3"
    assert by_id["ukcho-2025-q3b-i"]["sub_question"] == "b-i"
    # Clips come from the extract, never the tagging sheet.
    assert by_id["ukcho-2025-q3a"]["figures"] == ["assets/ukcho-2025-3a-paper.png"]
    assert by_id["ukcho-2025-q3b-ii"]["figures"] == []

    assert problems == ["part '3b-ii' is in the extract but has no tags (review_required set)"]


def test_build_records_keeps_transcribed_text_over_raw_pdf_text() -> None:
    _parents, subs, _problems = G.build_records(_manifest(), _tagging())
    by_id = {s["id"]: s for s in subs}
    assert by_id["ukcho-2025-q3a"]["question_text"] == "transcribed a"
    # No transcription supplied -> raw text layer is the fallback.
    assert by_id["ukcho-2025-q3b-ii"]["question_text"] == "raw pdf text b ii"


def test_untagged_part_is_flagged_for_review_not_dropped() -> None:
    _parents, subs, _problems = G.build_records(_manifest(), _tagging(omit="3b-ii"))
    by_id = {s["id"]: s for s in subs}
    assert by_id["ukcho-2025-q3b-ii"]["review_required"] is True
    assert by_id["ukcho-2025-q3a"]["review_required"] is False


def test_tagged_parts_are_suggested_not_locked() -> None:
    _parents, subs, _problems = G.build_records(_manifest(), _tagging())
    for sub in subs:
        assert sub["tag_status"] == "suggested"
        assert sub["tag_source"] == "ai"


def test_tagging_sheet_entry_missing_from_extract_is_reported() -> None:
    tagging = _tagging()
    tagging["parts"]["9z"] = {"marks": 1}
    _parents, _subs, problems = G.build_records(_manifest(), tagging)
    assert any("9z" in p for p in problems)


def test_parent_total_marks_falls_back_to_sum_of_parts() -> None:
    tagging = _tagging()
    tagging["parents"][0].pop("total_marks")
    parents, _subs, _problems = G.build_records(_manifest(), tagging)
    # 2 + 4 + 3 — read from the tagging sheet, where the marks actually live.
    assert parents[0]["total_marks"] == 9


def test_build_records_output_validates() -> None:
    parents, subs, _problems = G.build_records(_manifest(), _tagging())
    report = U.validate_all(parents + subs)
    assert report["errors"] == {}, report["errors"]


# --- ingest_paper ---------------------------------------------------------


@pytest.fixture
def paper_dirs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    manifest_dir = tmp_path / "extract"
    (manifest_dir / "clips").mkdir(parents=True)
    (manifest_dir / "parts.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    for clip in ("ukcho-2025-3a-paper.png", "ukcho-2025-3b-i-paper.png"):
        (manifest_dir / "clips" / clip).write_bytes(b"\x89PNG\r\n\x1a\nfake")

    tagging_path = tmp_path / "tagging.json"
    tagging_path.write_text(json.dumps(_tagging()), encoding="utf-8")

    return manifest_dir, tagging_path, tmp_path / "vault", manifest_dir / "clips"


def test_ingest_paper_writes_records_and_clips(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    report = G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    assert report["parents"] == 1
    assert report["subquestions"] == 3
    assert report["clips"] == 2
    assert report["written"] == 4
    assert report["errors"] == 0, report["errors"]
    assert report["needs_tags"] == []  # _tagging() fills every core tag

    assert (vault / "questions" / "ukcho-2025-q3.md").exists()
    assert (vault / "questions" / "ukcho-2025-q3b-i.md").exists()
    assert (vault / "assets" / "ukcho-2025-3a-paper.png").exists()

    text = (vault / "questions" / "ukcho-2025-q3b-i.md").read_text(encoding="utf-8")
    assert "assets/ukcho-2025-3a-paper.png" not in text  # only its own clip
    assert "![[assets/ukcho-2025-3b-i-paper.png]]" in text
    assert "[[ukcho-2025-q3]]" in text


def test_ingest_headings_use_nested_bracket_labels(paper_dirs) -> None:
    """Bodies are read by teachers and in Obsidian, so labels must match the paper."""
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    sub = (vault / "questions" / "ukcho-2025-q3b-i.md").read_text(encoding="utf-8")
    assert sub.startswith("---\n")
    assert "# UKChO 2025 Q3(b)(i) —" in sub
    assert "Q3b-i" not in sub

    parent = (vault / "questions" / "ukcho-2025-q3.md").read_text(encoding="utf-8")
    assert "[[ukcho-2025-q3b-i|Q3(b)(i)]]" in parent
    assert "[[ukcho-2025-q3a|Q3(a)]]" in parent


def test_ingest_paper_is_idempotent(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    first = {p.name: p.read_text(encoding="utf-8") for p in sorted((vault / "questions").glob("*.md"))}

    second_report = G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    second = {p.name: p.read_text(encoding="utf-8") for p in sorted((vault / "questions").glob("*.md"))}

    assert first == second
    assert len(list((vault / "questions").glob("*.md"))) == 4
    assert second_report["written"] == 4


def test_ingest_paper_reports_missing_clips(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    (clips / "ukcho-2025-3a-paper.png").unlink()
    report = G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    assert any("missing clip" in p for p in report["problems"])
    assert report["errors"] > 0


# ---------------------------------------------------------------------------
# extract -> tagging-sheet hand-off
#
# Ingesting a new year used to require hand-writing a ~45-entry sheet, which is
# what made "upload another past paper" impractical. `ukcho prompt --manifest`
# pre-creates the sheet instead; these tests pin that round trip and, critically,
# that an unfilled sheet can never masquerade as tagged work.
# ---------------------------------------------------------------------------

def _manifest_with_prefix() -> dict:
    m = _manifest()
    m["prefix"] = "ukcho-2025"
    m["source_pdf"] = "raw/ukcho/ukcho_2025_r1_qp.pdf"
    # A real extract knows nothing about marks — they live in the mark scheme.
    for part in m["parts"]:
        assert "marks" not in part
    return m


def test_year_is_read_from_the_prefix() -> None:
    assert G.year_from_prefix("ukcho-2025") == 2025
    assert G.year_from_prefix("ukcho_2024_r1") == 2024
    assert G.year_from_prefix("ukcho") is None
    assert G.year_from_prefix("") is None


def test_prefix_is_recovered_from_an_older_extract() -> None:
    """Extracts made before the manifest carried a prefix must still be taggable."""
    manifest = _manifest()
    assert "prefix" not in manifest
    for part in manifest["parts"]:
        part["text_path"] = f"parts/ukcho-2025-{part['key']}.txt"

    assert G.prefix_from_manifest(manifest) == "ukcho-2025"
    assert G.resolve_prefix(manifest) == "ukcho-2025"
    assert G.resolve_prefix(manifest, "ukcho-2024") == "ukcho-2024"
    # And it is good enough to name the parts correctly.
    sheet = G.build_sheet_skeleton(manifest)
    assert sheet["prefix"] == "ukcho-2025"
    assert sheet["year"] == 2025


def test_prefix_recovery_falls_back_to_clip_names() -> None:
    manifest = {"parts": [{"key": "3b-i", "clips": ["clips/ukcho-2025-3b-i-paper.png"]}]}
    assert G.prefix_from_manifest(manifest) == "ukcho-2025"


def test_prefix_recovery_gives_up_gracefully() -> None:
    assert G.prefix_from_manifest({"parts": []}) == ""
    assert G.resolve_prefix({"parts": []}) == "ukcho"
    assert G.build_sheet_skeleton({"parts": []})["prefix"] == "ukcho"


def test_skeleton_pre_creates_every_part_key_in_paper_order() -> None:
    sheet = G.build_sheet_skeleton(_manifest_with_prefix())

    assert sheet["prefix"] == "ukcho-2025"
    assert sheet["year"] == 2025
    assert sheet["source_qp"] == "raw/ukcho/ukcho_2025_r1_qp.pdf"
    # Order matters: the sheet is read top-to-bottom by a human tagger.
    assert list(sheet["parts"]) == ["3a", "3b-i", "3b-ii"]


def test_skeleton_gives_every_slot_an_empty_value_of_the_right_shape() -> None:
    sheet = G.build_sheet_skeleton(_manifest_with_prefix())
    entry = sheet["parts"]["3a"]

    assert entry["marks"] is None  # not derivable from the question paper
    assert entry["primary_as_anchor"] is None
    assert entry["difficulty_reason"] is None
    assert entry["requires_extension_knowledge"] is False
    for field in ("secondary_as_anchors", "extension_topics", "secondary_skills",
                  "question_features", "prerequisites"):
        assert entry[field] == [], field
    assert entry["answer"] is None
    assert entry["mark_scheme"] is None
    assert set(entry) == set(G.TAGGABLE_FIELDS) | set(G.EXTRA_SLOT_FIELDS) | {"marks"}


def test_skeleton_omits_question_text_so_the_extract_remains_the_source() -> None:
    """The sheet must not become a second, drifting copy of the paper text."""
    sheet = G.build_sheet_skeleton(_manifest_with_prefix())
    assert "question_text" not in sheet["parts"]["3a"]
    assert "review_required" not in sheet["parts"]["3a"]  # inferred, not asserted


def test_skeleton_scaffolds_one_parent_per_question() -> None:
    sheet = G.build_sheet_skeleton(_manifest_with_prefix())
    assert sheet["parents"] == [
        {"question_number": 3, "title": "", "total_marks": None, "overall_themes": []}
    ]


def test_skeleton_total_marks_is_null_so_ingest_sums_the_filled_parts() -> None:
    # A pre-filled 0 would be a lie until the tagger fills marks in.
    sheet = G.build_sheet_skeleton(_manifest_with_prefix())
    assert sheet["parents"][0]["total_marks"] is None


def test_unfilled_skeleton_marks_every_part_as_needing_review(tmp_path) -> None:
    """The safety property: a fresh sheet must not look like finished work."""
    manifest = _manifest_with_prefix()
    sheet = G.build_sheet_skeleton(manifest)
    sheet_path = tmp_path / "tagging.json"
    sheet_path.write_text(json.dumps(sheet), encoding="utf-8")

    _parents, subs, _problems = G.build_records(manifest, json.loads(sheet_path.read_text()))
    assert subs, "skeleton must still produce records"
    assert all(s["review_required"] is True for s in subs), [
        s["id"] for s in subs if not s["review_required"]
    ]
    assert all(s["tag_status"] == "suggested" for s in subs)


def test_filling_the_core_tags_clears_review() -> None:
    manifest = _manifest_with_prefix()
    sheet = G.build_sheet_skeleton(manifest)
    sheet["parts"]["3a"].update(
        {"marks": 2, "primary_as_anchor": "Organic Synthesis",
         "primary_skill": "Deduce", "difficulty_level": "Foundation"}
    )
    _parents, subs, _problems = G.build_records(manifest, sheet)
    by_id = {s["id"]: s for s in subs}
    assert by_id["ukcho-2025-q3a"]["review_required"] is False
    assert by_id["ukcho-2025-q3b-i"]["review_required"] is True


def test_partial_tags_still_flag_review() -> None:
    # Two of three core tags is not tagged: difficulty_level is still missing.
    manifest = _manifest_with_prefix()
    sheet = G.build_sheet_skeleton(manifest)
    sheet["parts"]["3a"].update(
        {"primary_as_anchor": "Organic Synthesis", "primary_skill": "Deduce"}
    )
    _parents, subs, _problems = G.build_records(manifest, sheet)
    assert next(s for s in subs if s["id"] == "ukcho-2025-q3a")["review_required"] is True


def test_explicit_review_clear_is_respected_even_with_missing_tags() -> None:
    manifest = _manifest_with_prefix()
    sheet = G.build_sheet_skeleton(manifest)
    sheet["parts"]["3a"]["review_required"] = False
    _parents, subs, _problems = G.build_records(manifest, sheet)
    assert next(s for s in subs if s["id"] == "ukcho-2025-q3a")["review_required"] is False


def test_filled_skeleton_ingests_cleanly(paper_dirs) -> None:
    """End to end: skeleton -> tags -> ingest, no hand-written sheet."""
    manifest_dir, _old_tagging, vault, clips = paper_dirs
    manifest = json.loads((manifest_dir / "parts.json").read_text(encoding="utf-8"))
    manifest["prefix"] = "ukcho-2025"
    (manifest_dir / "parts.json").write_text(json.dumps(manifest), encoding="utf-8")

    sheet = G.build_sheet_skeleton(manifest)
    sheet["parents"][0].update({"title": "Phenol", "overall_themes": ["Organic"]})
    for key, marks in (("3a", 2), ("3b-i", 4), ("3b-ii", 3)):
        sheet["parts"][key].update(
            {"marks": marks, "primary_as_anchor": "Organic Synthesis",
             "primary_skill": "Deduce", "difficulty_level": "Standard"}
        )
    sheet_path = manifest_dir / "tagging.json"
    sheet_path.write_text(json.dumps(sheet), encoding="utf-8")

    report = G.ingest_paper(manifest_dir, sheet_path, vault, clips)

    assert report["parents"] == 1
    assert report["subquestions"] == 3
    assert report["problems"] == []
    assert report["errors"] == 0
    parent = (vault / "questions" / "ukcho-2025-q3.md").read_text(encoding="utf-8")
    assert "**Total marks:** 9" in parent


def test_prompt_covers_the_whole_paper_with_stems_and_taxonomy() -> None:
    prompt = G.build_paper_prompt(_manifest_with_prefix())

    assert "asAnchors" in prompt["system"]
    assert "extensionTopics" in prompt["system"]
    assert prompt["taxonomy"]["asAnchors"] == list(U.AS_ANCHORS)
    assert prompt["paper"] == {
        "prefix": "ukcho-2025",
        "year": 2025,
        "source_pdf": "raw/ukcho/ukcho_2025_r1_qp.pdf",
        "questions": 1,
        "parts": 3,
    }
    # Later parts depend on earlier deductions, so the stem travels with the paper.
    assert prompt["questions"][0]["stem"].startswith("This question is about phenol.")
    assert prompt["questions"][0]["part_keys"] == ["3a", "3b-i", "3b-ii"]
    # Every part carries the text a tagger must read.
    keys = [p["key"] for p in prompt["parts"]]
    assert keys == ["3a", "3b-i", "3b-ii"]
    assert all(p["text"] for p in prompt["parts"])
    assert prompt["response_schema"]["parts"]["<key>"]["marks"] is None


def test_prompt_labels_use_nested_brackets() -> None:
    prompt = G.build_paper_prompt(_manifest_with_prefix())
    labels = {p["key"]: p["label"] for p in prompt["parts"]}
    assert labels["3b-i"] == "Q3(b)(i)"
    assert labels["3a"] == "Q3(a)"
    assert all("-" not in label for label in labels.values())


# --- write_sheet (the CLI's `prompt --manifest`) ---------------------------


@pytest.fixture
def extracted(tmp_path: Path) -> Path:
    """A manifest dir as `ukcho extract` leaves it (clips included)."""
    manifest_dir = tmp_path / "2025"
    (manifest_dir / "clips").mkdir(parents=True)
    (manifest_dir / "parts.json").write_text(
        json.dumps(_manifest_with_prefix()), encoding="utf-8"
    )
    return manifest_dir


def test_write_sheet_writes_prompt_and_sheet(extracted: Path) -> None:
    result = G.write_sheet(extracted)

    assert result["parts"] == 3
    assert result["questions"] == 1
    assert result["year"] == 2025
    assert result["sheet_written"] is True
    assert (extracted / "prompt.json").exists()
    assert (extracted / "tagging.json").exists()
    sheet = json.loads((extracted / "tagging.json").read_text(encoding="utf-8"))
    assert list(sheet["parts"]) == ["3a", "3b-i", "3b-ii"]


def test_write_sheet_never_clobbers_existing_tags(extracted: Path) -> None:
    """Re-running to refresh the prompt must not destroy the tag work."""
    G.write_sheet(extracted)
    sheet_path = extracted / "tagging.json"
    sheet = json.loads(sheet_path.read_text(encoding="utf-8"))
    sheet["parts"]["3a"].update(
        {"primary_as_anchor": "Organic Synthesis", "primary_skill": "Deduce",
         "difficulty_level": "Foundation", "marks": 2}
    )
    sheet_path.write_text(json.dumps(sheet), encoding="utf-8")

    result = G.write_sheet(extracted)

    assert result["sheet_written"] is False
    assert "kept" in result["sheet_status"]
    survived = json.loads(sheet_path.read_text(encoding="utf-8"))
    assert survived["parts"]["3a"]["primary_as_anchor"] == "Organic Synthesis"
    assert survived["parts"]["3a"]["marks"] == 2


def test_write_sheet_force_resets_the_sheet(extracted: Path) -> None:
    G.write_sheet(extracted)
    sheet_path = extracted / "tagging.json"
    sheet = json.loads(sheet_path.read_text(encoding="utf-8"))
    sheet["parts"]["3a"]["primary_as_anchor"] = "Organic Synthesis"
    sheet_path.write_text(json.dumps(sheet), encoding="utf-8")

    result = G.write_sheet(extracted, force=True)

    assert result["sheet_written"] is True
    reset = json.loads(sheet_path.read_text(encoding="utf-8"))
    assert reset["parts"]["3a"]["primary_as_anchor"] is None


def test_write_sheet_reads_prefix_from_the_manifest(extracted: Path) -> None:
    # No --prefix: the extract now records it, so a new year needs no extra flags.
    result = G.write_sheet(extracted, source_ms="raw/ukcho/ukcho_2025_r1_ms.pdf")
    assert result["prefix"] == "ukcho-2025"
    sheet = json.loads((extracted / "tagging.json").read_text(encoding="utf-8"))
    assert sheet["source_qp"] == "raw/ukcho/ukcho_2025_r1_qp.pdf"
    assert sheet["source_ms"] == "raw/ukcho/ukcho_2025_r1_ms.pdf"


def test_write_sheet_can_write_prompt_elsewhere(extracted: Path, tmp_path: Path) -> None:
    out = tmp_path / "handoff"
    result = G.write_sheet(extracted, out_dir=out)
    assert result["prompt_path"] == out / "prompt.json"
    assert (out / "prompt.json").exists()
    assert not (out / "parts.json").exists()  # only the two hand-off files


# ---------------------------------------------------------------------------
# Teacher edits must survive a re-ingest
#
# `ingest` is designed to be re-run (refresh the prompt, fill more tags, regenerate
# the vault). It used to blindly overwrite every record, which silently reverted a
# teacher's corrections. These tests pin the provenance rule that fixes it.
# ---------------------------------------------------------------------------

def _teacher_stamps() -> list[dict]:
    return [
        {"tag_source": "teacher", "tag_status": "edited"},
        {"tag_source": "teacher", "tag_status": "accepted"},
        # Hand-edited in Obsidian: only the status was re-stamped.
        {"tag_status": "accepted"},
        {"tag_status": "teacher"},
    ]


@pytest.mark.parametrize("stamp", _teacher_stamps())
def test_is_teacher_authored_detects_reviewed_records(stamp) -> None:
    assert U.is_teacher_authored(stamp) is True


@pytest.mark.parametrize(
    "stamp",
    [
        {"tag_source": "ai", "tag_status": "suggested"},
        {"tag_source": "none", "tag_status": "unset"},
        {},
    ],
)
def test_ai_records_are_not_treated_as_reviewed(stamp) -> None:
    assert U.is_teacher_authored(stamp) is False


def test_reingest_does_not_revert_a_teacher_correction(paper_dirs) -> None:
    """The regression that motivated the provenance rule."""
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    md = vault / "questions" / "ukcho-2025-q3a.md"
    corrected = md.read_text(encoding="utf-8").replace(
        "primary_as_anchor: Organic Synthesis", "primary_as_anchor: Chemical Bonding"
    )
    corrected = corrected.replace("tag_status: suggested", "tag_status: edited")
    corrected = corrected.replace("tag_source: ai", "tag_source: teacher")
    md.write_text(corrected, encoding="utf-8")

    report = G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    rec = U.normalize_record(U.parse_frontmatter(md.read_text(encoding="utf-8")))
    assert rec["primary_as_anchor"] == "Chemical Bonding"
    assert rec["tag_source"] == "teacher"
    assert report["preserved"] == 1


def test_reingest_still_refreshes_ai_records(paper_dirs) -> None:
    """The sheet stays authoritative for records no teacher has touched."""
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    md = vault / "questions" / "ukcho-2025-q3a.md"
    md.write_text(
        md.read_text(encoding="utf-8").replace(
            "primary_as_anchor: Organic Synthesis", "primary_as_anchor: Chemical Bonding"
        ),
        encoding="utf-8",
    )  # edited without stamping provenance -> not a teacher decision

    report = G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    rec = U.normalize_record(U.parse_frontmatter(md.read_text(encoding="utf-8")))
    assert rec["primary_as_anchor"] == "Organic Synthesis"
    assert report["preserved"] == 0


def test_reingest_refreshes_derived_fields_even_when_preserving(paper_dirs) -> None:
    """Preservation must not freeze ids, parent links or figure paths."""
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    md = vault / "questions" / "ukcho-2025-q3b-i.md"
    text = md.read_text(encoding="utf-8")
    tampered = (text
                .replace("tag_source: ai", "tag_source: teacher")
                .replace("parent_question_id: ukcho-2025-q3", "parent_question_id: ukcho-2025-q99"))
    md.write_text(tampered, encoding="utf-8")

    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    rec = U.normalize_record(U.parse_frontmatter(md.read_text(encoding="utf-8")))
    assert rec["parent_question_id"] == "ukcho-2025-q3"  # derived -> always corrected
    assert rec["figures"] == ["assets/ukcho-2025-3b-i-paper.png"]


def test_reingest_keeps_parent_title_when_the_sheet_is_blank(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    parent_md = vault / "questions" / "ukcho-2025-q3.md"
    parent_md.write_text(
        parent_md.read_text(encoding="utf-8").replace("title: Phenol", "title: Phenol chemistry"),
        encoding="utf-8",
    )

    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    # The sheet's title is set, so it wins; a blank sheet must not blank the vault.
    rec = U.normalize_record(U.parse_frontmatter(parent_md.read_text(encoding="utf-8")))
    assert rec["title"] == "Phenol"


def test_blank_sheet_title_does_not_blank_a_teacher_title() -> None:
    """A silent sheet must not erase a title the teacher supplied.

    build_records deliberately stores "" rather than inventing "Question 3", which
    would look non-blank and block the restore.
    """
    parent, _subs, _problems = G.build_records(_manifest(), _tagging())  # sheet has a title
    assert parent[0]["title"] == "Phenol"

    silent = _tagging()
    silent["parents"][0].pop("title")
    parent, _subs, _problems = G.build_records(_manifest(), silent)
    assert parent[0]["title"] == ""  # no invented placeholder

    G._carry_over_parent(parent[0], {"title": "Phenol chemistry", "total_marks": 9})
    assert parent[0]["title"] == "Phenol chemistry"


def test_unfilled_skeleton_leaves_parent_title_empty() -> None:
    sheet = G.build_sheet_skeleton(_manifest_with_prefix())
    assert sheet["parents"][0]["title"] == ""
    parent, _subs, _problems = G.build_records(_manifest_with_prefix(), sheet)
    assert parent[0]["title"] == ""


# ---------------------------------------------------------------------------
# import_edits: workspace download -> vault
# ---------------------------------------------------------------------------

def _edited_download(vault: Path) -> dict:
    """Shape of the tagging workspace's `ukcho-teacher-edits.json`."""
    rec = U.normalize_record(
        U.parse_frontmatter(
            (vault / "questions" / "ukcho-2025-q3a.md").read_text(encoding="utf-8")
        )
    )
    rec.update(
        {
            "primary_as_anchor": "Chemical Bonding",
            "secondary_as_anchors": ["Periodicity"],
            "difficulty_reason": "Requires connecting bonding to periodicity.",
            "tag_status": "edited",
            "tag_source": "teacher",
            # UI-only fields the site adds; import must ignore these.
            "label": "Q3(a)",
            "figure_urls": ["assets/ukcho-2025-3a-paper.png"],
        }
    )
    return {"generated": "chembank-ukcho-teacher-edits", "records": [rec]}


def test_import_edits_writes_teacher_edits_to_the_vault(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    edits = paper_dirs[2].parent / "edits.json"
    edits.write_text(json.dumps(_edited_download(vault)), encoding="utf-8")

    summary = G.import_edits(edits, vault)

    assert summary["updated"] == ["ukcho-2025-q3a"]
    assert summary["missing"] == []
    assert summary["errors"] == {}
    rec = U.normalize_record(U.parse_frontmatter(
        (vault / "questions" / "ukcho-2025-q3a.md").read_text(encoding="utf-8")))
    assert rec["primary_as_anchor"] == "Chemical Bonding"
    assert rec["secondary_as_anchors"] == ["Periodicity"]
    # Stamped as reviewed, which is what protects it from a later re-ingest.
    assert rec["tag_source"] == "teacher"
    assert U.is_teacher_authored(rec) is True


def test_imported_edits_survive_a_reingest(paper_dirs) -> None:
    """The whole point of the loop: edit -> import -> re-ingest -> edit still there."""
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    edits = vault.parent / "edits.json"
    edits.write_text(json.dumps(_edited_download(vault)), encoding="utf-8")
    G.import_edits(edits, vault)

    G.ingest_paper(manifest_dir, tagging_path, vault, clips)

    rec = U.normalize_record(U.parse_frontmatter(
        (vault / "questions" / "ukcho-2025-q3a.md").read_text(encoding="utf-8")))
    assert rec["primary_as_anchor"] == "Chemical Bonding"
    assert rec["secondary_as_anchors"] == ["Periodicity"]


def test_import_does_not_pollute_frontmatter_with_ui_fields(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    edits = vault.parent / "edits.json"
    edits.write_text(json.dumps(_edited_download(vault)), encoding="utf-8")

    G.import_edits(edits, vault)

    fm = U.parse_frontmatter((vault / "questions" / "ukcho-2025-q3a.md").read_text(encoding="utf-8"))
    assert "label" not in fm
    assert "figure_urls" not in fm


def test_import_preserves_the_markdown_body(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    md = vault / "questions" / "ukcho-2025-q3a.md"
    before = md.read_text(encoding="utf-8")
    body_before = before[before.find("\n---", 3) + 4 :]

    edits = vault.parent / "edits.json"
    edits.write_text(json.dumps(_edited_download(vault)), encoding="utf-8")
    G.import_edits(edits, vault)

    after = md.read_text(encoding="utf-8")
    assert after[after.find("\n---", 3) + 4 :] == body_before
    assert "![[assets/ukcho-2025-3a-paper.png]]" in after


def test_import_reports_records_missing_from_the_vault(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    edits = vault.parent / "edits.json"
    payload = _edited_download(vault)
    payload["records"].append({"id": "ukcho-2024-q9z", "primary_as_anchor": "Chemical Bonding"})
    edits.write_text(json.dumps(payload), encoding="utf-8")

    summary = G.import_edits(edits, vault)

    assert summary["missing"] == ["ukcho-2024-q9z"]
    assert summary["updated"] == ["ukcho-2025-q3a"]


def test_import_is_idempotent(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    edits = vault.parent / "edits.json"
    edits.write_text(json.dumps(_edited_download(vault)), encoding="utf-8")

    G.import_edits(edits, vault)
    second = G.import_edits(edits, vault)

    assert second["updated"] == []
    assert second["unchanged"] == ["ukcho-2025-q3a"]


def test_import_accepts_a_bare_list_and_a_single_record(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    payload = _edited_download(vault)

    as_list = vault.parent / "list.json"
    as_list.write_text(json.dumps(payload["records"]), encoding="utf-8")
    assert G.import_edits(as_list, vault)["updated"] == ["ukcho-2025-q3a"]

    # Re-import the same edit as a bare object: no change, but no crash either.
    single = vault.parent / "single.json"
    single.write_text(json.dumps(payload["records"][0]), encoding="utf-8")
    assert G.import_edits(single, vault)["unchanged"] == ["ukcho-2025-q3a"]


def test_import_stamps_provenance_even_if_the_payload_omits_it(paper_dirs) -> None:
    """Toggling only review_required produces an override with no tag_source."""
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    edits = vault.parent / "edits.json"
    edits.write_text(
        json.dumps({"records": [{"id": "ukcho-2025-q3a", "review_required": False}]}),
        encoding="utf-8",
    )

    G.import_edits(edits, vault)

    rec = U.normalize_record(U.parse_frontmatter(
        (vault / "questions" / "ukcho-2025-q3a.md").read_text(encoding="utf-8")))
    assert rec["review_required"] is False
    assert rec["tag_source"] == "teacher"


def test_import_flags_invalid_tags_rather_than_hiding_them(paper_dirs) -> None:
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    edits = vault.parent / "edits.json"
    edits.write_text(
        json.dumps({"records": [{"id": "ukcho-2025-q3a", "primary_skill": "Vibes",
                                 "tag_source": "teacher"}]}),
        encoding="utf-8",
    )

    summary = G.import_edits(edits, vault)

    assert "ukcho-2025-q3a" in summary["errors"]
    assert any("primary_skill" in e for e in summary["errors"]["ukcho-2025-q3a"])


# ---------------------------------------------------------------------------
# Tag snapshots (the committed backup of the tagging work)
#
# The vault is gitignored because it embeds past-paper text, so a crash would lose
# every tagging decision. A snapshot keeps the decisions and drops the text. These
# tests pin both halves: nothing copyrighted can leak, and a snapshot restores the
# bank exactly.
# ---------------------------------------------------------------------------

def _tagged_vault(paper_dirs) -> Path:
    """The shared fixture vault, plus one teacher-reviewed record."""
    manifest_dir, tagging_path, vault, clips = paper_dirs
    G.ingest_paper(manifest_dir, tagging_path, vault, clips)
    md = vault / "questions" / "ukcho-2025-q3a.md"
    md.write_text(
        md.read_text(encoding="utf-8")
        .replace("primary_as_anchor: Organic Synthesis", "primary_as_anchor: Chemical Bonding")
        .replace("tag_status: suggested", "tag_status: edited")
        .replace("tag_source: ai", "tag_source: teacher"),
        encoding="utf-8",
    )
    return vault


def test_snapshot_prefix_identifies_the_paper() -> None:
    assert G.snapshot_prefix("ukcho-2025-q3b-i") == "ukcho-2025"
    assert G.snapshot_prefix("ukcho-2024-q10") == "ukcho-2024"
    assert G.snapshot_prefix("weird") == "weird"


def test_part_key_inverts_the_sheet_key() -> None:
    # The snapshot must be loadable by `ingest --tagging`, which keys by "3b-i".
    rec = {"question_number": 3, "sub_question": "b-i"}
    assert G.part_key(rec) == "3b-i"
    assert G.part_key({"question_number": 6, "sub_question": "a"}) == "6a"
    # Round trip through the id builder used by build_records.
    assert G.sub_id("ukcho-2025", G.part_key(rec)) == "ukcho-2025-q3b-i"


def test_snapshot_omits_all_past_paper_content(paper_dirs) -> None:
    vault = _tagged_vault(paper_dirs)
    snap = G.build_snapshot(vault, "ukcho-2025")

    for entry in snap["parts"].values():
        for field in G.SNAPSHOT_EXCLUDED_FIELDS:
            assert field not in entry, field
    assert G.find_content_leaks(snap) == []


def test_snapshot_keeps_the_tagging_decisions(paper_dirs) -> None:
    vault = _tagged_vault(paper_dirs)
    snap = G.build_snapshot(vault, "ukcho-2025")

    assert snap["generated"] == "chembank-ukcho-tag-snapshot"
    assert snap["prefix"] == "ukcho-2025"
    assert snap["year"] == 2025
    assert list(snap["parts"]) == ["3a", "3b-i", "3b-ii"]

    entry = snap["parts"]["3a"]
    assert entry["primary_as_anchor"] == "Chemical Bonding"  # the teacher's value
    assert entry["primary_skill"] == "Deduce"
    assert entry["difficulty_level"] == "Foundation"
    assert entry["marks"] == 2
    # Provenance travels, so a restore does not regress the record to "ai suggested".
    assert entry["tag_source"] == "teacher"
    assert entry["tag_status"] == "edited"


def test_snapshot_includes_parent_metadata(paper_dirs) -> None:
    vault = _tagged_vault(paper_dirs)
    snap = G.build_snapshot(vault, "ukcho-2025")
    assert snap["parents"] == [
        {"question_number": 3, "title": "Phenol", "total_marks": 9,
         "overall_themes": ["Organic"]}
    ]


def test_snapshot_restores_the_vault_exactly(paper_dirs, tmp_path) -> None:
    """The whole point: a snapshot is a faithful, complete restore medium."""
    vault = _tagged_vault(paper_dirs)
    manifest_dir, _tagging, _vault, clips = paper_dirs

    snap_path = tmp_path / "snapshot.json"
    G.write_snapshot(vault, tmp_path)
    snap_path = tmp_path / "ukcho-2025-tags.json"
    assert snap_path.exists()

    # Rebuild from the extract using ONLY the snapshot as the tagging sheet.
    restored = tmp_path / "restored"
    report = G.ingest_paper(manifest_dir, snap_path, restored, clips)
    assert report["errors"] == 0
    assert report["needs_tags"] == []

    fields = list(G.SNAPSHOT_PART_FIELDS)
    def tags(v):
        return {
            r["id"]: {f: r.get(f) for f in fields}
            for r in U.load_ukcho_questions(v / "questions")
            if r["record_type"] == "ukcho-subquestion"
        }
    assert tags(vault) == tags(restored)


def test_restore_keeps_teacher_provenance(paper_dirs, tmp_path) -> None:
    """A restored snapshot must not look like fresh AI output."""
    vault = _tagged_vault(paper_dirs)
    manifest_dir, _tagging, _vault, clips = paper_dirs
    G.write_snapshot(vault, tmp_path)

    restored = tmp_path / "restored"
    G.ingest_paper(manifest_dir, tmp_path / "ukcho-2025-tags.json", restored, clips)

    rec = U.normalize_record(U.parse_frontmatter(
        (restored / "questions" / "ukcho-2025-q3a.md").read_text(encoding="utf-8")))
    assert rec["tag_source"] == "teacher"
    assert U.is_teacher_authored(rec) is True


def test_restore_regenerates_the_paper_content_from_the_extract(paper_dirs, tmp_path) -> None:
    """The snapshot carries no text, so the body must come back from the extract."""
    vault = _tagged_vault(paper_dirs)
    manifest_dir, _tagging, _vault, clips = paper_dirs
    G.write_snapshot(vault, tmp_path)

    restored = tmp_path / "restored"
    G.ingest_paper(manifest_dir, tmp_path / "ukcho-2025-tags.json", restored, clips)

    body = (restored / "questions" / "ukcho-2025-q3a.md").read_text(encoding="utf-8")
    assert "raw pdf text a" in body          # question text back from the extract
    assert "![[assets/ukcho-2025-3a-paper.png]]" in body  # clips re-linked
    assert "A" in body                        # answer restored from the sheet


def test_write_snapshot_splits_papers_by_prefix(paper_dirs, tmp_path) -> None:
    vault = _tagged_vault(paper_dirs)
    # A second paper in the same vault must land in its own file.
    other = vault / "questions" / "ukcho-2024-q1a.md"
    other.write_text(
        U.to_frontmatter(U.to_ordered_dict(U.normalize_record({
            "id": "ukcho-2024-q1a", "record_type": "ukcho-subquestion", "source": "UKChO",
            "year": 2024, "question_number": 1, "sub_question": "a",
            "parent_question_id": "ukcho-2024-q1",
            "marks": 1, "primary_as_anchor": "Chemical Bonding",
            "primary_skill": "Deduce", "difficulty_level": "Foundation",
        }))),
        encoding="utf-8",
    )

    summary = G.write_snapshot(vault, tmp_path)

    prefixes = sorted(s["prefix"] for s in summary["snapshots"])
    assert prefixes == ["ukcho-2024", "ukcho-2025"]
    assert (tmp_path / "ukcho-2024-tags.json").exists()
    assert (tmp_path / "ukcho-2025-tags.json").exists()
    # Filtering to one paper.
    assert [s["prefix"] for s in G.write_snapshot(vault, tmp_path, prefix="ukcho-2024")["snapshots"]] == ["ukcho-2024"]


def test_write_snapshot_refuses_when_there_is_nothing_to_back_up(tmp_path) -> None:
    with pytest.raises(ValueError):
        G.write_snapshot(tmp_path / "empty", tmp_path / "out")


def test_write_snapshot_refuses_a_contaminated_snapshot(monkeypatch, paper_dirs, tmp_path) -> None:
    """A hard guard: leaking paper text into a committed file must be impossible."""
    vault = _tagged_vault(paper_dirs)
    real = G.build_snapshot

    def leaky(vault_dir, prefix):
        snap = real(vault_dir, prefix)
        snap["parts"]["3a"]["question_text"] = "Explain why the sample effervesces."
        return snap

    monkeypatch.setattr(G, "build_snapshot", leaky)
    with pytest.raises(ValueError, match="past-paper content"):
        G.write_snapshot(vault, tmp_path)


def test_find_content_leaks_detects_a_contaminated_entry() -> None:
    snap = {"parts": {"3a": {"mark_scheme": "M1 curly arrow"}, "3b": {"answer": ""}}}
    assert G.find_content_leaks(snap) == ["part 3a: mark_scheme"]


def test_verbatim_quote_detector_flags_a_quoted_clause() -> None:
    """A tag field may be safe while its value quotes the paper."""
    rec = {
        "id": "ukcho-2025-q1f",
        "record_type": "ukcho-subquestion",
        "question_text": "Assume that the only products are carbon dioxide and water vapour.",
        "difficulty_reason": (
            "Students must derive it from the constraint that the only products "
            "are carbon dioxide and water vapour."
        ),
    }
    findings = G.find_verbatim_quotes_from([rec])
    assert [f["id"] for f in findings] == ["ukcho-2025-q1f"]
    assert [f["field"] for f in findings] == ["difficulty_reason"]
    # The flagged run must genuinely be a stretch of the paper's own words.
    paper = " ".join(re.findall(r"[a-z0-9]+", rec["question_text"].lower()))
    assert findings[0]["quote"] in paper


def test_verbatim_quote_detector_ignores_original_wording() -> None:
    rec = {
        "id": "ukcho-2025-q3a",
        "record_type": "ukcho-subquestion",
        "question_text": "Assume that the only products are carbon dioxide and water vapour.",
        "difficulty_reason": "One step: generalise the epoxide formula from the examples given.",
    }
    assert G.find_verbatim_quotes_from([rec]) == []


def test_verbatim_quote_detector_tolerates_missing_text() -> None:
    rec = {"id": "x", "question_text": "", "difficulty_reason": "Anything at all here."}
    assert G.find_verbatim_quotes_from([rec]) == []


# ---------------------------------------------------------------------------
# Mark scheme clips
#
# The MS is a second PDF with its own layout. Its one real trap is that a roman
# label means different things depending on indentation, so these tests pin the
# disambiguation: it must follow the QP's known part list, never guess.
# ---------------------------------------------------------------------------

class _FakePage:
    """Minimal stand-in for a PyMuPDF page: lines plus a page height."""

    def __init__(self, lines, height=800.0):
        self._lines = lines
        self.rect = type("R", (), {"height": height, "width": 595.0})()

    def get_text(self, kind="text", clip=None):
        if kind != "dict":
            return ""
        # Mirror the shape `_lines_in_order` walks.
        return {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {
                            "bbox": (x, y, x + 200.0, y + 12.0),
                            "spans": [{"text": text}],
                        }
                        for y, x, text in self._lines
                    ],
                }
            ]
        }


class _FakeMsDoc:
    def __init__(self, pages):
        self._pages = pages
        self.page_count = len(pages)

    def __getitem__(self, i):
        return self._pages[i]


def _line(y, x, text):
    return (y, x, text)


def test_ms_labels_only_match_bare_labels() -> None:
    doc = _FakeMsDoc([
        _FakePage([
            _line(42.8, 49.1, "1. This question is about epoxides"),
            _line(75.2, 46.9, "(a)"),
            _line(75.2, 84.3, "(i)"),
            _line(93.8, 112.3, "State symbols are not required."),
            _line(119.0, 82.9, "(ii)"),
            # Page furniture that must not be read as a label.
            _line(788.7, 294.6, "2"),
            _line(74.9, 526.9, "\uf0fe"),
        ])
    ])
    labels = X.find_ms_labels(doc)
    assert [(lb.kind, lb.part, lb.subpart) for lb in labels] == [
        ("question", None, None),
        ("part", "a", None),
        ("subpart", "a", "i"),   # indented => sub-part, and it knows its parent
        ("subpart", "a", "ii"),
    ]
    assert labels[0].question == 1


def test_ms_roman_label_at_the_margin_is_a_part() -> None:
    """Q3 and Q6 use (i)/(ii) as question-level parts, not sub-parts."""
    doc = _FakeMsDoc([
        _FakePage([
            _line(42.8, 48.6, "(i)"),
            _line(142.2, 76.6, "One mark."),
        ])
    ])
    labels = X.find_ms_labels(doc)
    assert [(lb.kind, lb.part) for lb in labels] == [("part", "i")]


def test_mark_scheme_bands_follow_the_qp_part_list() -> None:
    """The MS cannot say whether (i) is a part or sub-part, so the QP list decides."""
    from chembank.ukcho_extract import Part as XPart

    doc = _FakeMsDoc([
        _FakePage([
            _line(44.0, 49.1, "1. This question is about clay pigeon shooting"),
            _line(75.2, 46.9, "(a)"),
            _line(75.2, 84.3, "(i)"),      # sub-part of (a)
            _line(119.0, 82.9, "(ii)"),    # sub-part of (a)
            _line(213.1, 46.9, "(b)"),     # a part in its own right
        ]),
    ])
    parts = [
        XPart(question=1, part="a", subpart="i", page=0, y=0, text="", end_page=0, end_y=0),
        XPart(question=1, part="a", subpart="ii", page=0, y=0, text="", end_page=0, end_y=0),
        XPart(question=1, part="b", subpart=None, page=0, y=0, text="", end_page=0, end_y=0),
    ]
    bands = X.mark_scheme_bands(doc, parts)
    assert bands["1a-i"][:2] == (0, 75.2)
    assert bands["1a-ii"][:2] == (0, 119.0)
    assert bands["1b"][:2] == (0, 213.1)
    # Bands are contiguous: each ends where the next begins.
    assert bands["1a-i"][2:] == (0, 119.0)
    assert bands["1a-ii"][2:] == (0, 213.1)


def test_mark_scheme_bands_skip_a_part_with_no_ms_label() -> None:
    from chembank.ukcho_extract import Part as XPart

    doc = _FakeMsDoc([
        _FakePage([_line(44.0, 49.1, "1. This question is about something"), _line(75.2, 46.9, "(a)")])
    ])
    parts = [
        XPart(question=1, part="a", subpart=None, page=0, y=0, text="", end_page=0, end_y=0),
        XPart(question=1, part="z", subpart=None, page=0, y=0, text="", end_page=0, end_y=0),
    ]
    bands = X.mark_scheme_bands(doc, parts)
    assert "1a" in bands
    assert "1z" not in bands  # visible gap, never a silently wrong clip


def test_mark_scheme_bands_never_invert_on_the_last_question() -> None:
    """The last question has no successor; its band must not end before it starts."""
    from chembank.ukcho_extract import Part as XPart

    doc = _FakeMsDoc([
        _FakePage([_line(44.0, 49.1, "1. First")]),
        _FakePage([_line(42.8, 48.2, "(a)"), _line(500.0, 46.7, "(b)")]),
    ])
    parts = [
        XPart(question=1, part="a", subpart=None, page=1, y=42.8, text="", end_page=1, end_y=0),
        XPart(question=1, part="b", subpart=None, page=1, y=500.0, text="", end_page=1, end_y=0),
    ]
    bands = X.mark_scheme_bands(doc, parts)
    for key, (sp, sy, ep, ey) in bands.items():
        assert (ep, ey) > (sp, sy), f"{key} band inverts: {bands[key]}"


def test_a_part_label_and_a_subpart_on_one_line_stay_together() -> None:
    """The MS writes "(f)   (i)   B" as three cells of one line, and the two labels
    can land a fraction of a point apart. The sort then reads (i) *before* (f), so
    (i) would be fathered on the previous part — here (e) — and its own line would
    cut the band to nothing. 2023 Q2(f) is exactly this shape.
    """
    from chembank.ukcho_extract import Part as XPart

    doc = _FakeMsDoc([
        _FakePage([
            _line(44.1, 49.0, "2."),
            _line(75.2, 46.9, "(e)"),
            _line(95.0, 76.8, "AlP"),
            _line(109.8, 76.8, "(i)"),     # same line as (f), 0.2 above it
            _line(110.0, 46.9, "(f)"),
            _line(110.0, 84.3, "B"),
            _line(134.7, 76.8, "(ii)"),
            _line(140.0, 84.3, "N"),
            _line(159.3, 76.8, "(iii)"),
            _line(165.0, 84.3, "E"),
            _line(215.9, 46.9, "(g)"),
        ]),
    ])
    labels = X.find_ms_labels(doc)
    parent = {(lb.part, lb.subpart): lb.part for lb in labels if lb.kind == "subpart"}
    assert parent[("f", "i")] == "f", "the (i) on (f)'s line must belong to (f)"

    parts = [
        XPart(question=2, part="e", subpart=None, page=0, y=0, text="", end_page=0, end_y=0),
        XPart(question=2, part="f", subpart="i", page=0, y=0, text="", end_page=0, end_y=0),
        XPart(question=2, part="f", subpart="ii", page=0, y=0, text="", end_page=0, end_y=0),
        XPart(question=2, part="f", subpart="iii", page=0, y=0, text="", end_page=0, end_y=0),
        XPart(question=2, part="g", subpart=None, page=0, y=0, text="", end_page=0, end_y=0),
    ]
    bands = X.mark_scheme_bands(doc, parts)
    assert bands["2f-i"][:2] == (0, 109.8)
    # Not 110.0: the (f) label is on (i)'s own line, so it must not become the end.
    assert bands["2f-i"][2:] == (0, 134.7)
    assert bands["2f-ii"][2:] == (0, 159.3)
    assert bands["2f-iii"][2:] == (0, 215.9)


def test_a_two_column_run_of_items_is_split_not_merged() -> None:
    """2023 Q2(f) prints its three items in two columns, so (iii) sits at x≈313.

    It is a real sub-question — the MS gives "One mark each" — so the wider
    sub-part band must find it (it used to be lost, folding its mark into 2f-ii)
    while the lead-in, which merely mentions the periodic table in prose, must not
    condemn the run the way "complete the table" does.
    """
    two_column = FakeDoc([[
        (60.0, 40.0, "Q2 This question is about electronegativity"),
        (100.0, 50.0, "(f)"),
        (115.0, 50.0, "Three substances have been marked on the plot below. Based on your"),
        (128.0, 50.0, "knowledge of trends in electronegativity in the periodic table, identify"),
        (141.0, 50.0, "which point A-P describes where the following substances would be located."),
        (170.0, 107.5, "(i)"),
        (170.0, 142.9, "CsCl"),
        (170.0, 313.1, "(iii)"),
        (170.0, 348.5, "GaN"),
        (195.0, 107.5, "(ii)"),
        (195.0, 142.9, "NaK"),
    ]])
    parts, _ = X.split_parts(two_column)
    # Reading order: (i) and (iii) share the first row, (ii) is on the second.
    assert [p.key for p in parts] == ["2f-i", "2f-iii", "2f-ii"]
    # Two columns jumble which part carries which cell text, so only the union is
    # guaranteed; the rendered clip is what the student sees.
    joined = " ".join(p.text or "" for p in parts)
    assert all(name in joined for name in ("CsCl", "GaN", "NaK"))
    assert all((p.text or "").strip() for p in parts)


def test_ms_question_heading_may_be_a_bare_number() -> None:
    """Q6's MS puts "6." alone on a line with the title on the next one."""
    doc = _FakeMsDoc([_FakePage([_line(42.3, 49.1, "6."), _line(44.1, 76.8, "This question is about iodination")])])
    labels = X.find_ms_labels(doc)
    assert labels[0].kind == "question" and labels[0].question == 6


def test_band_covers_whole_part_when_ms_merges_its_subparts() -> None:
    """The MS often answers (d)(i) and (d)(ii) under one (d).

    Both must fall back to that single band, and — crucially — must not consume the
    labels belonging to the *next* part. A cursor-based matcher did exactly that:
    it ate (f)(i)/(f)(ii) to satisfy (d)(i) and lost every later part.
    """
    from chembank.ukcho_extract import Part as XPart

    doc = _FakeMsDoc([
        _FakePage([
            _line(44.1, 49.0, "3."),
            _line(75.2, 46.8, "(a)"),
            _line(128.0, 46.8, "(b)"),
            _line(371.1, 47.0, "(c)"),
            _line(594.8, 46.8, "(d)"),      # answers (d)(i) and (d)(ii)
        ]),
        _FakePage([
            _line(42.8, 46.8, "(e)"),
            _line(148.2, 48.2, "(f)"),
            _line(148.2, 80.2, "(i)"),
            _line(216.9, 78.7, "(ii)"),
        ]),
    ])
    order = [
        ("a", None), ("b", None), ("c", None), ("d", "i"), ("d", "ii"),
        ("e", None), ("f", "i"), ("f", "ii"),
    ]
    parts = [
        XPart(question=3, part=p, subpart=s, page=0, y=0, text="", end_page=0, end_y=0)
        for p, s in order
    ]
    bands = X.mark_scheme_bands(doc, parts)

    assert set(bands) == {f"3{p}-{s}" if s else f"3{p}" for p, s in order}
    # (d)(i) and (d)(ii) share the (d) region rather than borrowing (f)'s labels.
    assert bands["3d-i"] == bands["3d-ii"]
    assert bands["3d-i"][:2] == (0, 594.8)
    # ...and that region is clamped at (d)'s own page, so it never becomes a sliver
    # of the next page's header.
    assert bands["3d-i"][2:] == (0, 800.0)
    # (f)'s own sub-parts keep their own, distinct, undamaged bands.
    assert bands["3f-i"] == (1, 148.2, 1, 216.9)
    assert bands["3f-ii"][:2] == (1, 216.9)
    # (e) is unaffected by the fallback that happened before it.
    assert bands["3e"][:2] == (1, 42.8)


def test_band_falls_back_only_to_the_same_part() -> None:
    """A missing sub-part must not silently borrow a different part's answer."""
    from chembank.ukcho_extract import Part as XPart

    doc = _FakeMsDoc([
        _FakePage([
            _line(44.1, 49.0, "3."),
            _line(75.2, 46.8, "(a)"),
        ]),
    ])
    parts = [
        XPart(question=3, part="a", subpart=None, page=0, y=0, text="", end_page=0, end_y=0),
        # The MS never labels (b) at all, so (b)(i) has nothing honest to point at.
        XPart(question=3, part="b", subpart="i", page=0, y=0, text="", end_page=0, end_y=0),
    ]
    bands = X.mark_scheme_bands(doc, parts)
    assert bands["3a"][:2] == (0, 75.2)
    assert "3b-i" not in bands


def test_band_runs_past_mark_scheme_rows_the_paper_never_asked_for() -> None:
    """2023 Q2(d): the MS labels its answer-table rows (i)-(v), but the paper
    asks one question, so the band must reach (e) instead of stopping at (i)."""
    from chembank.ukcho_extract import Part as XPart

    doc = _FakeMsDoc([
        _FakePage([
            _line(44.1, 49.0, "2."),
            _line(75.2, 46.8, "(d)"),
            _line(119.0, 84.3, "(i)"),
            _line(130.0, 90.0, "I"),
            _line(141.0, 84.3, "(ii)"),
            _line(152.0, 90.0, "E"),
            _line(300.0, 46.8, "(e)"),
            _line(320.0, 90.0, "AlP"),
        ]),
    ])
    parts = [
        XPart(question=2, part="d", subpart=None, page=0, y=0, text="", end_page=0, end_y=0),
        XPart(question=2, part="e", subpart=None, page=0, y=0, text="", end_page=0, end_y=0),
    ]
    bands = X.mark_scheme_bands(doc, parts)
    start_page, start_y, end_page, end_y = bands["2d"]
    assert (start_page, start_y) == (0, 75.2)
    # The band absorbs the table rows and stops at (e), not at row (i).
    assert end_y > 152.0
    assert end_y <= 300.0
    assert bands["2e"][:2] == (0, 300.0)
