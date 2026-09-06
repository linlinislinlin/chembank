"""MCQ combo keys must close 'Which statements' so Q3/Q4 are not swallowed."""

from __future__ import annotations

from pathlib import Path

from chembank.split import split_questions

ROOT = Path(__file__).resolve().parents[1]

# IGCSE 2024 P2 style: options like "A 1 and 3 B 1 and 4" on one line.
_IGCSE_MIXED_PAIR = """
Paper 2 Multiple Choice
forty questions

1 Which gas has the slowest rate of diffusion?
A H2 B NH3 C CH4 D CO2
2 Which statements about the position of the elements in the Periodic Table are correct?
1 Elements in the same group have similar chemical properties.
2 Elements in the same period have similar chemical properties.
3 Elements in the same group have the same number of electron shells.
4 Elements in the same group have the same number of outer shell electrons.
A 1 and 3 B 1 and 4 C 2 and 3 D 2 and 4
3 Which statements about isotopes are correct?
1 Isotopes are atoms of different elements with the same number of protons.
2 Isotopes of the same element have the same chemical properties.
3 Isotopes are atoms with the same relative atomic mass.
4 Isotopes of the same element have the same electronic configuration.
A 1 and 2 B 1 and 3 C 2 and 4 D 3 and 4
4 Which diagram shows the arrangement of the outer shell electrons in a molecule of water?
A B C D
5 The structures of three substances are shown.
"""


def test_igcse_mixed_pair_combo_key_does_not_swallow_q3():
    chunks = split_questions(_IGCSE_MIXED_PAIR)
    nums = [int(c.question) for c in chunks]
    assert nums[:5] == [1, 2, 3, 4, 5]
    assert chunks[2].text.startswith("3 Which statements about isotopes")
    q4 = chunks[3].text
    assert q4.startswith("4 Which diagram")
    assert "Isotopes of the same element" not in q4.split("4 Which diagram")[0]


def test_classic_section_b_combo_key_still_closes():
    text = """
Paper 1 Multiple Choice
forty questions

1 Which statement is correct?
A foo B bar C baz D qux
2 Which statements are correct?
1 Ice melts at 0 °C.
2 Steam condenses.
3 Carbon is a metal.
A 1, 2 and 3 B 1 and 2 only C 2 and 3 only D 1 only
3 Where in the Periodic Table is helium?
A Group I B Group II C Group VII D Group VIII
"""
    chunks = split_questions(text)
    nums = [int(c.question) for c in chunks]
    assert nums == [1, 2, 3]
    assert "Where in the Periodic Table" in chunks[2].text


def _assert_forty(paper_id: str) -> None:
    path = ROOT / "draft" / f"{paper_id}.txt"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    nums = sorted(int(c.question) for c in split_questions(text))
    assert nums == list(range(1, 41)), f"{paper_id}: {nums}"


def test_regression_existing_0620_p2_drafts_stay_forty():
    for paper_id in (
        "0620_s24_qp_21",
        "0620_s24_qp_22",
        "0620_s24_qp_23",
        "0620_s25_qp_21",
        "0620_w24_qp_21",
        "0620_w24_qp_23",
        "0620_m25_qp_22",
    ):
        _assert_forty(paper_id)
