"""Mock syllabus-tag heuristics (no API key).

Fixtures encode mis-tag patterns from
`.cursor/skills/chembank-ingest/spot-check-notes.md`.
"""

from __future__ import annotations

import pytest

from chembank.tag import _split_stem_options, mock_tag_question


def test_split_stem_skips_prose_a_single():
    body = (
        "13 The gaseous products of heating a mixture of Ca(OH)₂ and NH₄Cl "
        "are passed through solid CaO.\n"
        "A single gaseous product, W, is collected.\n"
        "A sample of W reacts with Cl₂(g) to produce two gases, X and Y.\n"
        "What are X and Z?\n"
        "A N₂ CaCl₂\n"
        "B N₂ NH₄Cl\n"
        "C O₂ CaCl₂\n"
        "D O₂ NH₄Cl\n"
    )
    stem, options = _split_stem_options(body)
    assert "A single gaseous product" in stem
    assert "reacts with Cl₂" in stem
    assert options.startswith("A N₂")


@pytest.mark.parametrize(
    "body,expected",
    [
        (
            # Stoichiometry: mole/Avogadro count → 2.2 only (not 2.4)
            "1 Which contains the largest number of hydrogen atoms?\n"
            "A 0.10 mol of pentane\n"
            "B 0.20 mol of but-2-ene\n"
            "C 1.00 mol of hydrogen molecules\n"
            "D 6.02 × 10²³ hydrogen atoms\n",
            ["2.2"],
        ),
        (
            # Bonding keyword over-tag: shape ask → 3.5 only
            "3 Phosphorus(III) chloride is a covalent liquid. "
            "Phosphorus(V) chloride is an ionic solid.\n"
            "What is the shape of the PCl₃ molecule and the [PCl₄]⁺ ion?\n"
            "A pyramidal square planar\n"
            "B pyramidal tetrahedral\n"
            "C tetrahedral square planar\n"
            "D trigonal planar tetrahedral\n",
            ["3.5"],
        ),
        (
            # Option-keyword steal: IE stem, orbital only in options → 1.4
            "7 Why is the first ionisation energy of oxygen less than that of nitrogen?\n"
            "A The nitrogen atom has its outer electron in a different subshell.\n"
            "B The nuclear charge on the oxygen atom is greater.\n"
            "C The oxygen atom has a pair of electrons in one p orbital that repel.\n"
            "D There is more shielding in an oxygen atom.\n",
            ["1.4"],
        ),
        (
            # Option-keyword steal: ideal gas stem, ammonia in options → 4.1
            "8 Which gas would behave most like an ideal gas under room conditions?\n"
            "A helium\n"
            "B nitrogen\n"
            "C ammonia\n"
            "D krypton\n",
            ["4.1"],
        ),
        (
            # Haber / heat exchanger → 8.1 + 12.1 (not equilibrium steal)
            "10 The diagram represents the Haber process for the manufacture of ammonia.\n"
            "What is the purpose of the heat exchanger?\n"
            "A to cool the incoming gas mixture\n"
            "B to cool the reaction products\n"
            "C to warm the incoming gas mixture and speed up the reaction\n"
            "D to maintain equilibrium yield\n",
            ["8.1", "12.1"],
        ),
        (
            # Reagent over-tag: Ca(OH)₂/CaO present but ask is N/S + Cl₂ → 12.1, 11.4
            "13 The gaseous products of heating a mixture of Ca(OH)₂ and NH₄Cl "
            "are passed through solid CaO.\n"
            "A single gaseous product, W, is collected.\n"
            "A sample of W reacts with Cl₂(g) to produce two gases, X and Y.\n"
            "What are X and Z?\n"
            "A N₂ CaCl₂\n"
            "B N₂ NH₄Cl\n"
            "C O₂ CaCl₂\n"
            "D O₂ NH₄Cl\n",
            ["12.1", "11.4"],
        ),
        (
            # Composition / formula ID; Period 3 is option context → 2.3, 2.4
            "19 R is an oxide of Period 3 element T. 5.00 g of R contains 2.50 g of T.\n"
            "What is T?\n"
            "A magnesium\n"
            "B aluminium\n"
            "C silicon\n"
            "D sulfur\n",
            ["2.3", "2.4"],
        ),
        (
            # Structure class over-tag: molecular formula ask → 13.1 only
            "23 Limonene is a hydrocarbon found in citrus fruits.\n"
            "What is the molecular formula of limonene?\n"
            "A C₁₀H₁₂\n"
            "B C₁₀H₁₄\n"
            "C C₁₀H₁₆\n"
            "D C₁₀H₁₈\n",
            ["13.1"],
        ),
        (
            # Multi-functional group: citric acid OH + COOH + mole count
            "27 How many moles of hydrogen, H₂, are evolved when an excess of sodium "
            "metal is added to one mole of citric acid?\n"
            "citric acid contains CO₂H and HO groups\n"
            "A 0.5\n"
            "B 1.5\n"
            "C 2\n"
            "D 4\n",
            ["18.1", "16.1", "2.2"],
        ),
        (
            # Boltzmann → 8.2 (not 1.1 fallback)
            "5 The diagram shows the Boltzmann distribution for the same gas "
            "at two different temperatures, T1 and T2.\n"
            "What is plotted on the y-axis and which line represents the higher temperature?\n"
            "A number of molecules T1\n"
            "B number of molecules T2\n"
            "C molecular energy T1\n"
            "D molecular energy T2\n",
            ["8.2"],
        ),
        (
            # Combustion mass/volume → 2.4
            "6 What is the minimum mass of oxygen required to ensure the complete "
            "combustion of 12 dm3 of propane measured under room conditions?\n"
            "A 60 g\n"
            "B 80 g\n"
            "C 120 g\n"
            "D 160 g\n",
            ["2.4"],
        ),
    ],
)
def test_mock_tag_spot_check_patterns(body: str, expected: list[str]):
    got = mock_tag_question(body)["syllabus_codes"]
    assert got == expected


def test_mock_fallback_avoids_bare_1_1():
    tags = mock_tag_question("Which statement is correct?\nA one\nB two\nC three\nD four\n")
    assert tags["syllabus_codes"] != ["1.1"]
    assert tags.get("_mock_fallback") is True
