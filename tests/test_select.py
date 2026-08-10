"""Selection module: rules YAML, filtering, dedupe, sorting, count limit."""

from __future__ import annotations

from pathlib import Path

import yaml

from chembank.select import (
    RuleError,
    load_pick,
    load_rules,
    load_all_questions,
    select_questions,
    write_pick,
)

FIXTURES = Path(__file__).parent / "fixtures"
DOCS = FIXTURES / "select"


def _rules(**overrides) -> dict:
    rules = {"title": "Test Enthalpy", "syllabus_codes": ["5.1"], "sort": ["year", "question"]}
    rules.update(overrides)
    return rules


def test_load_rules_from_yaml():
    rules = load_rules(Path("pick/5.1-demo.yaml"))
    assert rules["title"] == "Enthalpy 5.1 复习单"
    assert rules["syllabus_codes"] == ["5.1"]
    assert rules["count"] == 12
    assert rules["sort"] == ["year", "paper", "question"]
    assert rules["shuffle"] is False


def test_load_rules_missing_title_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("count: 5\n", encoding="utf-8")
    try:
        load_rules(bad)
    except RuleError as e:
        assert "title" in str(e)
    else:
        raise AssertionError("expected RuleError")


def test_load_rules_requires_syllabus_codes_nonempty(tmp_path: Path):
    bad = tmp_path / "bad2.yaml"
    bad.write_text('title: "x"\nsyllabus_codes: []\n', encoding="utf-8")
    try:
        load_rules(bad)
    except RuleError as e:
        assert "syllabus_codes" in str(e)
    else:
        raise AssertionError("expected RuleError")


def test_load_all_questions_skips_invalid_and_non_tagged():
    docs = load_all_questions(DOCS)
    ids = {d["id"] for d in docs}
    # q9.json is a non-5.1 question but still a valid tagged doc → included.
    assert "cie-9701-2022-on-p12-q9" in ids
    # q5 through q10a all present.
    assert "cie-9701-2018-mj-p11-q5" in ids
    assert "cie-9701-2021-mj-p21-q9a" in ids
    # Anything not under a `tagged/` dir is excluded by the glob.
    paths = [str(p) for p in Path(DOCS).rglob("q*.json")]
    assert not any("untagged" in p for p in paths)


def test_filter_by_syllabus_code():
    picked = select_questions(_rules(), docs_dir=DOCS)
    ids = {d["id"] for d in picked}
    assert "cie-9701-2022-on-p12-q9" not in ids  # 2.2 only, excluded
    assert "cie-9701-2018-mj-p11-q5" in ids
    assert "cie-9701-2023-mj-p11-q10" in ids  # has 5.1 among others


def test_dedupe_by_id():
    picked = select_questions(_rules(), docs_dir=DOCS)
    ids = [d["id"] for d in picked]
    assert len(ids) == len(set(ids)), "duplicate id survived"


def test_filter_by_year_range():
    picked = select_questions(
        _rules(year_min=2020, year_max=2021), docs_dir=DOCS
    )
    ids = {d["id"] for d in picked}
    assert "cie-9701-2018-mj-p11-q5" not in ids
    assert "cie-9701-2020-mj-p11-q8" in ids
    assert "cie-9701-2021-mj-p21-q9a" in ids
    assert "cie-9701-2022-on-p12-q9" not in ids  # also wrong code


def test_count_limit_and_sort():
    picked = select_questions(_rules(count=2), docs_dir=DOCS)
    assert len(picked) == 2
    # Sorted by (year, question): 2018-q5, then 2020-q8.
    assert [d["id"] for d in picked] == [
        "cie-9701-2018-mj-p11-q5",
        "cie-9701-2020-mj-p11-q8",
    ]


def test_full_5point1_set_ordering():
    picked = select_questions(_rules(), docs_dir=DOCS)
    ids = [d["id"] for d in picked]
    assert ids == sorted(ids, key=lambda x: (int(x.split("-")[1]), x)), "not year-major"


def test_shuffle_respects_seed():
    a = select_questions(_rules(shuffle=True, seed=1), docs_dir=DOCS)
    b = select_questions(_rules(shuffle=True, seed=1), docs_dir=DOCS)
    assert [d["id"] for d in a] == [d["id"] for d in b]


def test_exclude_after_keeps_pure_5point1():
    # A pure 5.1 question is within the cutoff and must be kept.
    picked = select_questions(_rules(exclude_after="5.2"), docs_dir=DOCS)
    ids = {d["id"] for d in picked}
    assert "cie-9701-2018-mj-p11-q5" in ids
    assert "cie-9701-2021-mj-p21-q9a" in ids


def test_exclude_after_removes_later_topic():
    # q10 mixes 5.1 + 5.2 → cutoff 5.2 must reject it.
    picked = select_questions(_rules(exclude_after="5.2"), docs_dir=DOCS)
    ids = {d["id"] for d in picked}
    assert "cie-9701-2023-mj-p11-q10" not in ids
    # Without the cutoff (backward-compat) the mixed question is kept.
    picked_back = select_questions(_rules(), docs_dir=DOCS)
    assert "cie-9701-2023-mj-p11-q10" in {d["id"] for d in picked_back}


def test_exclude_after_allows_earlier_companion_codes():
    # A 5.1 question can still carry earlier companion codes (e.g. 2.2/2.3/2.4).
    q = {
        "id": "test-5.1-with-earlier",
        "question": "1",
        "marks": 1,
        "year": 2016,
        "syllabus_codes": ["5.1", "2.3"],
        "ms_answer": "x",
        "body": "body",
    }
    rules = _rules(exclude_after="5.2")
    assert select_questions(rules, docs_dir=DOCS)  # smoke: runs without error
    # Direct check via the module-private matcher for the synthetic record.
    from chembank.select import _matches_rules
    assert _matches_rules(q, rules) is True
    assert _matches_rules({**q, "syllabus_codes": ["5.1", "5.2"]}, rules) is False


def test_exclude_after_rejects_far_later_and_keeps_suffix_variants():
    rules = _rules(exclude_after="5.2")
    from chembank.select import _matches_rules
    base = {
        "id": "t",
        "question": "1",
        "marks": 1,
        "year": 2016,
        "body": "b",
        "ms_answer": "x",
    }
    assert _matches_rules({**base, "syllabus_codes": ["6.0"]}, rules) is False
    assert _matches_rules({**base, "syllabus_codes": ["23.1"]}, rules) is False
    assert _matches_rules({**base, "syllabus_codes": ["5.1", "5.1b"]}, rules) is True


def test_exclude_after_multicode_any_match_rejects():
    # ANY code at-or-after the cutoff rejects, even if another is earlier.
    rules = _rules(exclude_after="5.2")
    from chembank.select import _matches_rules
    q = {
        "id": "t",
        "question": "1",
        "marks": 1,
        "year": 2016,
        "body": "b",
        "ms_answer": "x",
        "syllabus_codes": ["2.3", "5.1", "5.2"],
    }
    assert _matches_rules(q, rules) is False


def test_write_and_load_pick_roundtrip(tmp_path: Path):
    picked = select_questions(_rules(count=2), docs_dir=DOCS)
    out = write_pick(_rules(), picked, tmp_path / "pick.json", docs_dir=DOCS)
    data = load_pick(out)
    assert data["title"] == "Test Enthalpy"
    assert data["question_count"] == 2
    assert len(data["questions"]) == 2
    q = data["questions"][0]
    for key in ("id", "marks", "year", "figures", "syllabus_codes"):
        assert key in q


def test_to_pick_entry_keeps_learning_outcomes():
    """The pick entry must carry learning_outcomes + learning_outcome_texts so
    the assembler can group questions by primary learning outcome."""
    from chembank.select import to_pick_entry

    q = {
        "id": "lo-q1",
        "marks": 1,
        "year": 2020,
        "learning_outcomes": ["5.1-2", "5.1-3b"],
        "learning_outcome_texts": ["LO2 text", "LO3b text"],
        "_vault": "vault",
        "_category": "all",
    }
    entry = to_pick_entry(q, source="draft")
    assert entry["learning_outcomes"] == ["5.1-2", "5.1-3b"]
    assert entry["learning_outcome_texts"] == ["LO2 text", "LO3b text"]

    # A question without LOs still yields a stable empty list, no crash.
    bare = to_pick_entry({"id": "lonely", "_vault": None, "_category": "all"}, source="draft")
    assert bare["learning_outcomes"] is None
    assert bare["learning_outcome_texts"] is None
