"""Sub-question label rendering.

``sub_question`` is stored compactly ("b", "b-i") because it is derived from the
extract's part key, but it is shown to students and teachers. The paper writes
nested brackets, so "a-i" must render as ``Q1(a)(i)`` and never ``Q1(a-i)``.

The site, the teacher workspace and the tagging prompt all render labels, so the
implementation is shared: ``ukcho.question_label`` is the single source of truth
and ``build._ukcho_label`` delegates to it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from chembank import ukcho as U

REPO = Path(__file__).resolve().parent.parent
BUILD = REPO / "quiz-app" / "build.py"


def _load_build():
    spec = importlib.util.spec_from_file_location("chembank_build", BUILD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def build():
    return _load_build()


@pytest.mark.parametrize(
    ("sub_question", "expected"),
    [
        ("a", "Q3(a)"),
        ("b", "Q3(b)"),
        ("b-i", "Q3(b)(i)"),
        ("b-ii", "Q3(b)(ii)"),
        ("g-iii", "Q3(g)(iii)"),
        ("", "Q3"),
        (None, "Q3"),
    ],
)
def test_ukcho_label_uses_nested_brackets(sub_question, expected) -> None:
    rec = {"question_number": 3, "sub_question": sub_question}
    assert U.question_label(rec) == expected


def test_label_never_leaks_the_hyphen_form() -> None:
    # The old bug: "a-i" rendered as "Q1(a-i)".
    assert "a-i" not in U.question_label({"question_number": 1, "sub_question": "a-i"})


def test_full_label_prefixes_the_year_for_prompts() -> None:
    rec = {"year": 2025, "question_number": 6, "sub_question": "b-ii"}
    assert U.full_label(rec) == "UKChO 2025 Q6(b)(ii)"
    # A missing year must not render as "UKChO None".
    assert U.full_label({"question_number": 2, "sub_question": "a"}) == "Q2(a)"


def test_build_delegates_to_the_shared_helper(build) -> None:
    """Guards against the site drifting from the vault/workspace naming."""
    rec = {"year": 2025, "question_number": 3, "sub_question": "b-i"}
    assert build._ukcho_label(rec) == U.question_label(rec) == "Q3(b)(i)"


def test_the_prompt_uses_the_same_label() -> None:
    from chembank import ukcho_ingest as G

    manifest = {
        "prefix": "ukcho-2025",
        "parts": [
            {"question": 6, "part": "b", "subpart": "ii", "key": "6b-ii", "text": "t", "clips": []}
        ],
    }
    prompt = G.build_paper_prompt(manifest)
    assert prompt["parts"][0]["label"] == "Q6(b)(ii)"

