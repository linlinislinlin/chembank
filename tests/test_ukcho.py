"""UKChO tagging foundation: taxonomy, vault parsing, validation, AI-tag merge.

These tests pin the *contract* of the UKChO bank so real papers can be added
without silently breaking the tagging model:

* sub-questions are independent records (never inherit parent tags),
* controlled lists in ``ukcho.py`` match the JSON schema enums,
* AI output is merged as *suggested* tags and can never lock a record.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chembank import ukcho as U

REPO = Path(__file__).resolve().parent.parent
#: Mock records live in fixtures/ (committed) because the real vault content is
#: copyrighted past-paper text and stays local. Tests must never depend on it.
VAULT = REPO / "fixtures" / "ukcho-mock" / "questions"
SCHEMA = REPO / "schema" / "ukcho-question.schema.json"


@pytest.fixture(scope="module")
def records() -> list[dict]:
    loaded = U.load_ukcho_questions(VAULT)
    assert loaded, "fixtures/ukcho-mock/questions should contain the mock records"
    return loaded


@pytest.fixture(scope="module")
def subs(records: list[dict]) -> list[dict]:
    return [r for r in records if r["record_type"] == "ukcho-subquestion"]


def test_taxonomy_matches_schema_enums() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    props = schema["properties"]
    defs = schema["$defs"]

    assert props["primary_as_anchor"]["enum"] == list(U.AS_ANCHORS)
    assert props["primary_skill"]["$ref"] == "#/$defs/skill"
    assert props["question_features"]["items"]["$ref"] == "#/$defs/questionFeature"
    assert props["difficulty_level"]["enum"] == list(U.DIFFICULTY_LEVELS)
    # Schema $defs must not drift from the module's controlled lists.
    assert defs["asAnchor"]["enum"] == list(U.AS_ANCHORS)
    assert defs["skill"]["enum"] == list(U.SKILLS)
    assert defs["questionFeature"]["enum"] == list(U.QUESTION_FEATURES)
    # extension_topics is intentionally open (flexible taxonomy) but typed as strings.
    assert props["extension_topics"]["items"]["type"] == "string"


def test_extension_topics_are_grouped_and_flat_consistently() -> None:
    grouped = [t for topics in U.EXTENSION_TOPIC_GROUPS.values() for t in topics]
    assert grouped == list(U.EXTENSION_TOPICS)
    assert "Molecular Orbital Theory" in U.EXTENSION_TOPICS
    assert "Retrosynthesis" in U.EXTENSION_TOPICS
    assert "Unit Cells" in U.EXTENSION_TOPICS


def test_mock_vault_loads_parents_and_subquestions(records: list[dict], subs: list[dict]) -> None:
    parents = [r for r in records if r["record_type"] == "ukcho-parent"]
    assert parents, "expected at least one parent record"
    assert subs, "expected sub-question records"

    parent_ids = {p["id"] for p in parents}
    for sub in subs:
        assert sub["parent_question_id"] in parent_ids, sub["id"]
        assert sub["source"] == "UKChO"
        assert sub["primary_as_anchor"]
        assert sub["primary_skill"]
        assert sub["difficulty_level"]


def test_every_subquestion_passes_validation(subs: list[dict]) -> None:
    report = U.validate_all(subs + [{"record_type": "ukcho-parent", "id": "x", "source": "UKChO"}])
    assert report["errors"] == {}, report["errors"]
    assert report["ok"] == len(subs)


def test_subquestions_are_tagged_independently(subs: list[dict]) -> None:
    """The core promise: 2025 Q3(a) and Q3(d) must not share a tag set."""
    by_id = {s["id"]: s for s in subs}

    a = by_id["ukcho-2025-q3a"]
    d = by_id["ukcho-2025-q3d"]

    assert a["parent_question_id"] == d["parent_question_id"] == "ukcho-2025-q3"
    assert a["difficulty_level"] != d["difficulty_level"]
    assert a["primary_skill"] != d["primary_skill"]
    assert set(a["extension_topics"]) != set(d["extension_topics"])
    # Q3(d) is cross-topic and flagged; Q3(a) is not.
    assert d["secondary_as_anchors"] == ["Periodicity"]
    assert a["secondary_as_anchors"] == []
    assert d["review_required"] is True
    assert a["review_required"] is False


def test_validation_rejects_uncontrolled_values() -> None:
    bad = U.normalize_record(
        {
            "id": "ukcho-2025-q9a",
            "record_type": "ukcho-subquestion",
            "source": "UKChO",
            "year": 2025,
            "question_number": 9,
            "sub_question": "a",
            "primary_as_anchor": "Not A Real Topic",
            "primary_skill": "Vibes",
            "difficulty_level": "Impossible",
            "question_features": ["Made Up Feature"],
        }
    )
    errors, _warnings = U.validate_question(bad)
    joined = " | ".join(errors)
    assert "primary_as_anchor not in controlled list" in joined
    assert "primary_skill not in controlled list" in joined
    assert "difficulty_level not in" in joined
    assert "question_feature not in controlled list" in joined


def test_unknown_extension_topic_is_a_warning_not_an_error() -> None:
    rec = U.normalize_record(
        {
            "id": "ukcho-2025-q9b",
            "record_type": "ukcho-subquestion",
            "source": "UKChO",
            "year": 2025,
            "question_number": 9,
            "sub_question": "b",
            "primary_as_anchor": "Chemical Bonding",
            "primary_skill": "Deduce",
            "difficulty_level": "Standard",
            "difficulty_reason": "test",
            "extension_topics": ["Some Brand New Olympiad Topic"],
            "prerequisites": ["Atomic orbitals"],
            "question_text": "test",
        }
    )
    errors, warnings = U.validate_question(rec)
    assert errors == []
    assert any("outside the starter taxonomy" in w for w in warnings)


def test_apply_ai_tags_maps_camelcase_and_never_locks() -> None:
    rec = U.normalize_record({"id": "ukcho-2025-q3b", "record_type": "ukcho-subquestion"})
    ai = {
        "primaryASAnchor": "Chemical Bonding",
        "secondaryASAnchors": [],
        "extensionTopics": ["Molecular Orbital Theory", "Paramagnetism"],
        "primarySkill": "Deduce",
        "secondarySkills": ["Explain", "Draw / Represent"],
        "difficultyLevel": "Standard",
        "difficultyReason": "Unfamiliar MO diagram + magnetic behaviour link.",
        "questionFeatures": ["Unfamiliar Context", "Diagram", "Multi-step"],
        "prerequisites": ["Atomic orbitals", "Hund's rule"],
        "requiresExtensionKnowledge": True,
        "reviewRequired": False,
    }
    merged = U.apply_ai_tags(rec, ai)

    assert merged["primary_as_anchor"] == "Chemical Bonding"
    assert merged["extension_topics"] == ["Molecular Orbital Theory", "Paramagnetism"]
    assert merged["secondary_skills"] == ["Explain", "Draw / Represent"]
    assert merged["requires_extension_knowledge"] is True
    assert merged["tag_status"] == "suggested"
    assert merged["tag_source"] == "ai"
    # Never locked: a teacher can still accept/edit.
    assert merged["tag_status"] in U.TAG_STATUSES


def test_apply_ai_tags_records_unmapped_keys() -> None:
    rec = U.normalize_record({"id": "ukcho-2025-q3c", "record_type": "ukcho-subquestion"})
    merged = U.apply_ai_tags(rec, {"primaryASAnchor": "Chemical Bonding", "confidence": 0.82})
    assert merged["_ai_unmapped_keys"] == ["confidence"]


def test_split_body_round_trips_without_growing_the_file() -> None:
    """Re-writing frontmatter must not accumulate blank lines."""
    rec = U.normalize_record({"id": "ukcho-2025-q3a", "record_type": "ukcho-subquestion"})
    body = "# Heading\n\ntext\n"
    text = U.to_frontmatter(U.to_ordered_dict(rec)) + "\n" + body
    for _ in range(3):
        text = U.to_frontmatter(U.to_ordered_dict(rec)) + U.split_body(text)
    assert text.endswith("\n" + body)


def test_split_body_handles_missing_frontmatter() -> None:
    assert U.split_body("no frontmatter here") == "no frontmatter here"


def test_frontmatter_round_trip() -> None:
    rec = U.normalize_record(
        {
            "id": "ukcho-2025-q3b",
            "record_type": "ukcho-subquestion",
            "source": "UKChO",
            "year": 2025,
            "question_number": 3,
            "sub_question": "b",
            "marks": 3,
            "primary_as_anchor": "Chemical Bonding",
            "extension_topics": ["Molecular Orbital Theory"],
            "primary_skill": "Draw / Represent",
            "difficulty_level": "Standard",
            "question_features": ["Diagram", "Multi-step"],
            "requires_extension_knowledge": True,
            "review_required": False,
        }
    )
    text = U.to_frontmatter(U.to_ordered_dict(rec))
    assert text.startswith("---\n") and text.rstrip().endswith("---")
    parsed = U.parse_frontmatter(text + "\n\n# body\n")
    assert parsed["id"] == "ukcho-2025-q3b"
    assert parsed["extension_topics"] == ["Molecular Orbital Theory"]
    assert parsed["requires_extension_knowledge"] is True
    assert parsed["primary_skill"] == "Draw / Represent"


def test_tagging_request_includes_taxonomy_and_question(subs: list[dict]) -> None:
    rec = next(s for s in subs if s["id"] == "ukcho-2025-q3b")
    bundle = U.build_tagging_request(rec)
    assert "asAnchors" in bundle["system"]
    assert "extensionTopics" in bundle["system"]
    assert "N2" in bundle["user"]
    assert bundle["taxonomy"]["asAnchors"] == list(U.AS_ANCHORS)


def test_difficulty_band_fallback_is_sane() -> None:
    assert U.difficulty_band_from_marks(1) == "Foundation"
    assert U.difficulty_band_from_marks(4) == "Standard"
    assert U.difficulty_band_from_marks(10) == "Challenge"
