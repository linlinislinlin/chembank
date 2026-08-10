"""Tile handout renderer: frontmatter, grid, image resolution, placeholders."""

from __future__ import annotations

from pathlib import Path

import yaml

from chembank.assemble import render_tiles, resolve_asset_path
from chembank.select import select_questions, to_pick_entry

FIXTURES = Path(__file__).parent / "fixtures"
DOCS = FIXTURES / "select"
VAULT = FIXTURES / "vault"
VAULT_STRUCTURED = FIXTURES / "vault-structured"


def _rules(count: int = 2, **overrides) -> dict:
    rules = {"title": "Test Enthalpy", "syllabus_codes": ["5.1"], "sort": ["year", "question"]}
    rules.update(overrides)
    if "count" not in overrides:
        rules["count"] = count
    return rules


def _make_pick(count: int = 2) -> dict:
    picked = select_questions(_rules(count=count), docs_dir=DOCS)
    payload = {
        "title": _rules()["title"],
        "slug": "test-enthalpy",
        "rules": _rules(),
        "question_count": len(picked),
        "questions": [to_pick_entry(q, source="draft") for q in picked],
    }
    return payload


def _read_note(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_render_frontmatter(tmp_path: Path):
    pick = _make_pick()
    out = tmp_path / "handouts" / "test-enthalpy.md"
    render_tiles(pick, vault_root=VAULT, out_path=out)
    note = _read_note(out)
    fm = yaml.safe_load(note.split("---")[1])
    assert fm["type"] == "handout"
    assert fm["template"] == "tiles"
    assert fm["title"] == "Test Enthalpy"
    assert fm["question_count"] == 2
    assert fm["total_marks"] == 2  # two 1-mark questions
    assert "5.1" in fm["syllabus_codes"]
    assert "Enthalpy" in sorted(fm["topic_titles"])[0]


def test_tile_embeds_own_vault_image(tmp_path: Path):
    pick = _make_pick()
    out = tmp_path / "note.md"
    render_tiles(pick, vault_root=VAULT, out_path=out)
    note = _read_note(out)
    # 2018 q5 has its PNG → rendered as an HTML <img> with an absolute file URL
    # (avoids the pipe-in-table-cell split). Filename must be present.
    assert "cie-9701-2018-mj-p11-q5-paper.png" in note
    assert "<img" in note
    # The detail note exists in vault/questions → clickable wikilink caption.
    assert "[[questions/cie-9701-2018-mj-p11-q5]]" in note


def test_cross_vault_asset_uses_relative_image(tmp_path: Path):
    pick = _make_pick(count=4)
    out = tmp_path / "note.md"
    render_tiles(pick, vault_root=VAULT, out_path=out)
    note = _read_note(out)
    # q9a (paper 21) asset lives in a sibling vault → still rendered as <img>
    # with the sibling asset filename embedded in the absolute URL.
    assert "q9a-paper.png" in note
    assert "vault-structured" in note
    # In-vault asset also uses <img>.
    assert "cie-9701-2018-mj-p11-q5-paper.png" in note


def test_missing_image_placeholder(tmp_path: Path):
    # A question with no figures must render a （无图） placeholder, no crash.
    q = {
        "id": "test-q-no-fig",
        "question": "1",
        "marks": 1,
        "year": 2020,
        "figures": [],
        "body": "No diagram here",
    }
    pick = {"title": "NoFig", "rules": {"title": "NoFig"}, "questions": [q]}
    out = tmp_path / "note.md"
    render_tiles(pick, vault_root=VAULT, out_path=out)
    note = _read_note(out)
    assert "（无图）" in note
    assert "No diagram here" in note


def test_resolve_asset_path_variants():
    # figures entry may be `assets/x.png`, `![[assets/x.png]]`, or bare name.
    assert resolve_asset_path(
        "assets/cie-9701-2018-mj-p11-q5-paper.png", vault_root=VAULT
    ).is_file()
    assert resolve_asset_path(
        "![[assets/cie-9701-2018-mj-p11-q5-paper.png]]", vault_root=VAULT
    ).is_file()
    assert resolve_asset_path(
        "cie-9701-2018-mj-p11-q5-paper.png", vault_root=VAULT
    ).is_file()
    assert resolve_asset_path("does-not-exist.png", vault_root=VAULT) is None


def test_answer_section_uses_sequential_numbers(tmp_path: Path):
    pick = _make_pick()
    out = tmp_path / "note.md"
    render_tiles(pick, vault_root=VAULT, out_path=out)
    note = _read_note(out)
    assert "## 答案区" in note
    # The answer-section labels are the handout-internal sequential numbers
    # (第1题, 第2题, …), not the original exam question numbers.
    assert "- **第1题**: " in note
    assert "- **第2题**: " in note
    # Original exam labels must NOT leak into the answer key.
    assert "- **Q5**" not in note
    assert "- **Q8**" not in note


def test_tile_caption_has_seq_year_session_question_marks(tmp_path: Path):
    pick = _make_pick(count=2)
    out = tmp_path / "note.md"
    render_tiles(pick, vault_root=VAULT, out_path=out)
    note = _read_note(out)
    assert "第1题 · 2018 MJ · Q5 · 1 分" in note
    assert "第2题 · 2020 MJ · Q8 · 1 分" in note


def test_tile_seq_matches_answer_section(tmp_path: Path):
    """The Nth tile and the Nth answer-key entry share the same sequential
    number, so a user can pair a question with its answer by counting 1,2,3…
    (matches only the questions that actually carry a Mark Scheme answer)."""
    pick = _make_pick(count=4)  # 3 of the 4 questions have an ms_answer.
    out = tmp_path / "note.md"
    render_tiles(pick, vault_root=VAULT, out_path=out)
    note = _read_note(out)
    grid, answers = note.split("## 答案区", 1)

    # Every tile carries its sequential number in order.
    for i in range(1, 5):
        assert "第%d题" % i in grid, f"tile {i} missing sequential caption"

    # Answer entries are labelled with the same sequential numbers, ascending,
    # and each one must refer to a real tile so question ↔ answer pairing holds.
    bodies = answers.split("- **")
    labels = [b.split("**:")[0].strip() for b in bodies if b and "**: " in b]
    assert labels
    assert labels == sorted(labels, key=lambda s: int(s[1:-1]))  # 第1题 < 第2题 …
    for label in labels:
        assert label in grid, f"answer {label} not found on any tile"
        assert label in answers


def _lo_pick(*questions: dict) -> dict:
    """Build a pick whose questions carry the given dicts verbatim."""
    return {
        "title": "LO Group Test",
        "slug": "lo-group-test",
        "rules": {"title": "LO Group Test"},
        "question_count": len(questions),
        "questions": list(questions),
    }


def _lo_question(qid: str, los: list[str], lo_texts: list[str], *, year: int, question_txt: str) -> dict:
    """Synthetic question carrying learning outcomes + texts + paper."""
    return {
        "id": qid,
        "question": question_txt,
        "marks": 1,
        "year": year,
        "paper": 11,
        "ms_answer": "A",
        "body": f"body of {qid}",
        "learning_outcomes": los,
        "learning_outcome_texts": lo_texts,
        "figures": [],
    }


def test_render_groups_by_primary_lo(tmp_path: Path):
    """Questions are grouped under their primary (numerically smallest) LO, in
    ascending LO order, each rendered exactly once."""
    # Note the mixed order of the input:
    #   q-a: ["5.1-2","5.1-3b"]  → primary 5.1-2
    #   q-b: ["5.1-1"]           → primary 5.1-1
    #   q-c: ["5.1-3b"]          → primary 5.1-3b
    #   q-d: ["5.1-2"]           → primary 5.1-2
    qa = _lo_question("q-a", ["5.1-2", "5.1-3b"], ["LO2 text", "LO3b text"], year=2020, question_txt="7")
    qb = _lo_question("q-b", ["5.1-1"], ["LO1 text"], year=2019, question_txt="3")
    qc = _lo_question("q-c", ["5.1-3b"], ["LO3b text"], year=2018, question_txt="1")
    qd = _lo_question("q-d", ["5.1-2"], ["LO2 text"], year=2019, question_txt="4")
    out = tmp_path / "note.md"
    render_tiles(_lo_pick(qa, qb, qc, qd), vault_root=VAULT, out_path=out)
    note = _read_note(out)

    # Group headers appear in ascending order: 5.1-1, then 5.1-2, then 5.1-3b.
    assert "### 5.1-1" in note
    assert "### 5.1-2" in note
    assert "### 5.1-3b" in note
    assert note.index("### 5.1-1") < note.index("### 5.1-2") < note.index("### 5.1-3b")

    # The two-LO question q-a appears exactly once, under 5.1-2 (its smallest LO).
    count = note.count("q-a-paper") + note.count("body of q-a")
    assert count == 1, f"q-a rendered {count} times"
    # q-a sits after the 5.1-2 header but before the 5.1-3b header.
    assert note.index("### 5.1-2") < note.index("body of q-a") < note.index("### 5.1-3b")

    # No cross-LO duplication: each question id's body appears exactly once.
    for qid in ("q-a", "q-b", "q-c", "q-d"):
        assert note.count(f"body of {qid}") == 1, f"{qid} not rendered exactly once"


def test_render_groups_ordering_numeric(tmp_path: Path):
    """LO ids sort numerically so 5.1-10 comes after 5.1-2 (not as a string)."""
    q_small = _lo_question("q-small", ["5.1-2"], ["two"], year=2020, question_txt="1")
    q_big = _lo_question("q-big", ["5.1-10"], ["ten"], year=2020, question_txt="2")
    out = tmp_path / "note.md"
    render_tiles(_lo_pick(q_big, q_small), vault_root=VAULT, out_path=out)
    note = _read_note(out)
    assert note.index("### 5.1-2") < note.index("### 5.1-10")
    assert note.count("### 5.1-2") == 1
    assert note.count("### 5.1-10") == 1


def test_render_groups_within_group_sorted_by_year_paper_question(tmp_path: Path):
    """Within a group, questions order by (year, paper, question)."""
    qa = _lo_question("q-a", ["5.1-1"], ["x"], year=2021, question_txt="9",)
    qb = _lo_question("q-b", ["5.1-1"], ["x"], year=2018, question_txt="2")
    qc = _lo_question("q-c", ["5.1-1"], ["x"], year=2018, question_txt="1")
    out = tmp_path / "note.md"
    render_tiles(_lo_pick(qb, qa, qc), vault_root=VAULT, out_path=out)
    note = _read_note(out)
    grp = note[note.index("### 5.1-1") : note.index("## 答案区")]
    assert grp.index("body of q-c") < grp.index("body of q-b") < grp.index("body of q-a")


def test_render_groups_no_lo_fallback(tmp_path: Path):
    """A question with no learning_outcomes lands in the （未标 LO） fallback
    group, still rendered exactly once, and never crashes."""
    q_tagged = _lo_question("q-tagged", ["5.1-1"], ["x"], year=2019, question_txt="1")
    q_untagged = {
        "id": "q-untagged",
        "question": "2",
        "marks": 1,
        "year": 2020,
        "paper": 22,
        "ms_answer": "B",
        "body": "body of q-untagged",
        "figures": [],
        # NO learning_outcomes key at all
    }
    out = tmp_path / "note.md"
    render_tiles(_lo_pick(q_untagged, q_tagged), vault_root=VAULT, out_path=out)
    note = _read_note(out)
    # Fallback group header present and rendered once.
    assert note.count("### （未标 LO）") == 1
    # Tagged question rendered under its LO; untagged once in fallback.
    assert note.count("body of q-tagged") == 1
    assert note.count("body of q-untagged") == 1


def test_render_groups_sequential_numbering_is_global(tmp_path: Path):
    """Sequential numbering (第N题) stays continuous across all LO groups, so
    question↔answer pairing holds even when questions are regrouped."""
    qa = _lo_question("q-a", ["5.1-3b"], ["x"], year=2020, question_txt="1")
    qb = _lo_question("q-b", ["5.1-1"], ["x"], year=2019, question_txt="2")
    qc = _lo_question("q-c", ["5.1-2"], ["x"], year=2018, question_txt="3")
    qd = _lo_question("q-d", ["5.1-1"], ["x"], year=2017, question_txt="4")
    out = tmp_path / "note.md"
    render_tiles(_lo_pick(qa, qb, qc, qd), vault_root=VAULT, out_path=out)
    note = _read_note(out)

    # Grid order after grouping by primary LO is: 5.1-1 (q-b, q-d), 5.1-2 (q-c),
    # 5.1-3b (q-a). Sequential captions must be global & unique 1..4.
    for i in range(1, 5):
        assert f"第{i}题" in note, f"sequential caption 第{i}题 missing"

    # Answer section uses the same global numbering: every 第N题 in the answer
    # area corresponds to the Nth tile, without any per-group reset.
    grid, answers = note.split("## 答案区", 1)
    for i in range(1, 5):
        assert f"第{i}题" in grid
        assert f"**第{i}题**" in answers


def test_primary_lo_numeric_smallest(tmp_path: Path):
    """The primary LO is the numerically smallest, ignoring suffix letters."""
    from chembank.assemble import _primary_lo
    assert _primary_lo({"learning_outcomes": ["5.1-2", "5.1-3b"]}) == "5.1-2"
    assert _primary_lo({"learning_outcomes": ["5.1-10", "5.1-2"]}) == "5.1-2"
    assert _primary_lo({"learning_outcomes": ["5.1-3a", "5.1-3b", "5.1-3"]}) == "5.1-3"
    assert _primary_lo({"learning_outcomes": []}) == ""
    assert _primary_lo({}) == ""
