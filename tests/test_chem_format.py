import re

from chembank.chem_format import (
    fix_reaction_arrows,
    format_chemistry_text,
    format_mcq_option_lines,
    format_mcq_options_table,
)
from chembank.split import strip_footer_noise


def test_delta_h_plimsoll_to_mathjax():
    out = format_chemistry_text("ΔH₁⦵ is formation")
    assert r"$\Delta H_{1}^{\ominus}$" in out


def test_reaction_arrow_and_dhc():
    raw = (
        "ΔHc⦵\n"
        "CH₄(g) + 2O₂(g) CO₂(g) + 2H₂O(l)\n"
        "Which expression is equivalent to ΔHc⦵?"
    )
    out = format_chemistry_text(raw)
    assert "→" in out or r"\xrightarrow" in out
    assert r"\Delta H_{\mathrm{c}}^{\ominus}" in out


def test_pua_and_equiv_become_arrow():
    assert "→" in fix_reaction_arrows("8HI + H₂SO₄ \uf0ae H₂S + 4H₂O + 4I₂")
    assert "→" in fix_reaction_arrows("8HI + H₂SO₄ ≡ H₂S + 4I₂")
    out = format_chemistry_text("8HI + H₂SO₄ \uf0ae H₂S + 4H₂O + 4I₂")
    assert "→" in out
    assert "\uf0ae" not in out
    assert "≡" not in out


def test_symbol_pua_degree_delta_pi_sigma():
    assert "°" in format_chemistry_text("120\uf0b0")
    assert r"\Delta H" in format_chemistry_text("\uf044H = +180")
    assert "π-bond" in format_chemistry_text("\uf070-bond")
    assert "σ-bond" in format_chemistry_text("\uf073-bond")
    assert "\uf0b0" not in format_chemistry_text("120\uf0b0")


def test_ion_charge_superscript_and_showboth():
    out = format_chemistry_text(
        "What is the shape of the PCl₃ molecule and the [PCl₄]+ ion?"
    )
    assert r"[PCl_{4}]^{+}" in out
    assert r"[PCl_{4}]+" not in out
    assert "show both" in format_chemistry_text(
        "Which compound could showboth cis-trans isomerism?"
    )


def test_mcq_options_one_per_line():
    raw = "2 In which pair?\nA Ar⁺ and C– B B and Ti⁺ C F and Ga D Se– and Si–"
    out = format_mcq_option_lines(raw)
    lines = [ln for ln in out.splitlines() if ln.startswith(("A ", "B ", "C ", "D "))]
    assert [ln[0] for ln in lines] == ["A", "B", "C", "D"]


def test_mcq_two_column_shape_table():
    raw = (
        "3 Phosphorus forms two chlorides.\n"
        "What is the shape of the PCl₃ molecule and the [PCl₄]⁺ ion?\n"
        "PCl₃ [PCl₄]⁺\n"
        "A pyramidal square planar\n"
        "B pyramidal tetrahedral\n"
        "C tetrahedral square planar\n"
        "D trigonal planar tetrahedral\n"
    )
    out = format_mcq_options_table(raw)
    assert "| | PCl₃ | [PCl₄]⁺ |" in out
    assert "| A | pyramidal | square planar |" in out
    assert "| B | pyramidal | tetrahedral |" in out
    assert "| D | trigonal planar | tetrahedral |" in out
    # Full pipeline keeps the table structure
    full = format_chemistry_text(raw)
    assert "| A |" in full and "square planar" in full


def test_strip_trailing_page_number():
    raw = (
        "15 Which substance will not be a product?\n"
        "A dinitrogen monoxide\n"
        "B magnesium oxide\n"
        "C oxygen\n"
        "D steam\n"
        "\n"
        "7\n"
    )
    out = strip_footer_noise(raw)
    assert not out.rstrip().endswith("7")
    assert "D steam" in out
    assert "© UCLES" not in strip_footer_noise("body\n© UCLES 2021\n")


def test_strip_q22_atom_salad_when_figure_present():
    from chembank.export_vault import _strip_diagram_label_noise

    raw = (
        "22 Which compound could show both cis-trans isomerism?\n"
        "A B C D\n"
        "Cl H Cl H O Br Cl H\n"
        "Br Br\n"
        "C Br C Br C C Br C\n"
        "C C Br C C Br C C Cl C C I\n"
        "Br H I H Cl H Br H\n"
    )
    out = _strip_diagram_label_noise(raw, has_figure=True)
    assert "Br" not in out
    assert "Cl" not in out
    assert "A B C D" not in out
    assert "cis-trans" in out


def test_strip_mechanism_option_salad_and_controls():
    from chembank.export_vault import _is_atom_salad_line, _strip_diagram_label_noise

    assert _is_atom_salad_line("A C C H C C⁺ H C C Br")
    assert not _is_atom_salad_line("A C")
    assert not _is_atom_salad_line("C P")

    raw = (
        "22 What is the correct mechanism for the addition of hydrogen bromide to ethene?\n"
        "H H H H H H\n"
        "A C C H C C⁺ H C C Br\n"
        "H–\n"
        "Br\x01⁺\n"
        "H\x01–\n"
        "B C C H C C⁺ H C C Br\n"
    )
    out = _strip_diagram_label_noise(raw, has_figure=True)
    assert "hydrogen bromide" in out
    assert "C C H" not in out
    assert "\x01" not in out

    tick = (
        "19 Which row is correct?\n"
        "increased plant photochemical\n"
        "growth in rivers smog\n"
        "A \x1a \x1a\n"
        "B \x16 \x1a\n"
        "C \x1a \x16\n"
        "D \x16 \x16\n"
    )
    out2 = _strip_diagram_label_noise(tick, has_figure=True)
    assert "Which row" in out2
    assert "\x1a" not in out2
    assert not re.search(r"^[A-D]\s*$", out2, re.M)
