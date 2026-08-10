"""Normalize chemistry text for Obsidian (MathJax) display."""

from __future__ import annotations

import re

# Unicode subscript / superscript digits → ASCII
_SUB_TO_ASCII = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋", "0123456789+-")
_SUP_TO_ASCII = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")

# Common state symbols kept outside \mathrm
_STATE = r"(?:\((?:g|l|s|aq)\))"

# ΔH₁⦵ / ΔH1⦵ / ΔHc⦵ / ΔH_c^⦵
_DELTA_H_RE = re.compile(
    r"ΔH"
    r"(?:_\{?([0-9]+|[cCfF])\}?|"
    r"([₀₁₂₃₄₅₆₇₈₉]+)|"
    r"([0-9]+)|"
    r"([cC]))?"
    r"(?:\^\{?⦵\}?|⦵|°|⊖)?"
)

# Formulae like CH₄, O₂, H₂O, CO₂, PCl₃, [PCl₄]+
_FORMULA_RE = re.compile(
    r"(?<![A-Za-z\\])"
    r"(\[?)([A-Z][a-z]?(?:[₀₁₂₃₄₅₆₇₈₉0-9]*)(?:[A-Z][a-z]?(?:[₀₁₂₃₄₅₆₇₈₉0-9]*))*)"
    r"(\]?)"
    r"([₀₁₂₃₄₅₆₇₈₉0-9]*)"
    r"([⁺⁻+\-]*)"
    r"(?=\(|\s|$|[–—+\-=×·]|,|;|:|\?)"
)


def _sub_ascii(s: str) -> str:
    return s.translate(_SUB_TO_ASCII)


def delta_h_to_latex(match: re.Match[str]) -> str:
    sub = match.group(1) or match.group(2) or match.group(3) or match.group(4) or ""
    sub = _sub_ascii(sub)
    if sub.lower() == "c":
        return r"$\Delta H_{\mathrm{c}}^{\ominus}$"
    if sub.lower() == "f":
        return r"$\Delta H_{\mathrm{f}}^{\ominus}$"
    if sub.isdigit():
        return "$\\Delta H_{" + sub + "}^{\\ominus}$"
    return r"$\Delta H^{\ominus}$"


def formula_to_latex(raw: str) -> str:
    """Convert a simple formula token with unicode/ascii subscripts to math."""
    s = raw.strip()
    if not s or s.startswith("$"):
        return raw
    # Already mostly fine unicode — still wrap for consistent rendering
    s = s.replace("⁺", "+").replace("⁻", "-")
    # unicode subdigits → _{n}
    out: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "₀₁₂₃₄₅₆₇₈₉":
            digits = []
            while i < len(s) and s[i] in "₀₁₂₃₄₅₆₇₈₉":
                digits.append(_sub_ascii(s[i]))
                i += 1
            out.append(f"_{{{''.join(digits)}}}")
            continue
        if ch.isdigit() and out and out[-1].isalpha():
            digits = []
            while i < len(s) and s[i].isdigit():
                digits.append(s[i])
                i += 1
            out.append(f"_{{{''.join(digits)}}}")
            continue
        out.append(ch)
        i += 1
    body = "".join(out)
    # charge (include ] so [PCl_{4}]+ → [PCl_{4}]^{+})
    body = re.sub(r"([}\]\w])\+$", r"\1^{+}", body)
    body = re.sub(r"([}\]\w])\-$", r"\1^{-}", body)
    return f"$\\mathrm{{{body}}}$"


def fix_reaction_arrows(text: str) -> str:
    """Normalize PDF arrow artifacts (≡, Symbol PUA, bare =) to →."""
    # Private-use / mis-decoded Symbol font arrows (often display as ≡)
    for ch in ("\uf0ae", "\uf0d7", "\u2261", "≡", "＝"):
        text = text.replace(ch, "→")

    # Bare "=" used as a reaction arrow between formula-like tokens
    # e.g. 8HI + H2SO4 = H2S + ...  (not n = 2 / oxidation tables)
    text = re.sub(
        r"(?<=[A-Za-z0-9₀₁₂₃₄₅₆₇₈₉⁺⁻+\])\}])"
        r"\s*=\s*"
        r"(?=[A-Z][A-Za-z0-9₀₁₂₃₄₅₆₇₈₉⁺⁻]*)",
        " → ",
        text,
    )
    # Collapse "→ →" if both PUA and = fired
    text = re.sub(r"(?:→\s*){2,}", "→ ", text)
    return text


# Longest-first so "trigonal planar" wins over "planar"
_SHAPE_PHRASES = (
    "trigonal bipyramidal",
    "square planar",
    "trigonal planar",
    "tetrahedral",
    "octahedral",
    "pyramidal",
    "non-linear",
    "linear",
    "bent",
)


def _split_two_shape_cells(body: str) -> tuple[str, str] | None:
    """Split 'pyramidal square planar' into two VSEPR shape cells."""
    s = " ".join(body.split())
    if not s:
        return None
    lower = s.lower()
    for phrase in _SHAPE_PHRASES:
        if lower.startswith(phrase):
            rest = s[len(phrase) :].strip()
            if rest:
                return s[: len(phrase)], rest
    # Fallback: split on last two-word / one-word boundary mid-string
    parts = s.split()
    if len(parts) >= 2:
        # Prefer splitting so the right cell is a known shape
        for phrase in _SHAPE_PHRASES:
            plen = len(phrase.split())
            if len(parts) > plen and " ".join(parts[-plen:]).lower() == phrase:
                left = " ".join(parts[:-plen])
                right = " ".join(parts[-plen:])
                if left:
                    return left, right
    return None


def format_mcq_options_table(text: str) -> str:
    """Rebuild two-column shape/options tables (e.g. PCl₃ / [PCl₄]⁺).

    Detects a header line of two formulae followed by A–D rows with two
    shape phrases each, and emits a markdown table matching the paper layout.
    """
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Header: two formula-like tokens, no leading A–D
        header_m = re.match(
            r"^(?P<a>(?:\[[^\]]+\][⁺+\-]*|[A-Z][A-Za-z0-9₀₁₂₃₄₅₆₇₈₉⁺⁻+\-]*)(?:\([^)]*\))?)"
            r"\s+"
            r"(?P<b>(?:\[[^\]]+\][⁺+\-]*|[A-Z][A-Za-z0-9₀₁₂₃₄₅₆₇₈₉⁺⁻+\-]*)(?:\([^)]*\))?)"
            r"\s*$",
            line.strip(),
        )
        if (
            header_m
            and i + 4 < len(lines)
            and all(
                re.match(r"^[A-D]\s+\S", lines[i + 1 + k].strip()) for k in range(4)
            )
        ):
            rows: list[tuple[str, str, str]] = []
            ok = True
            for k in range(4):
                opt = lines[i + 1 + k].strip()
                om = re.match(r"^([A-D])\s+(.+)$", opt)
                if not om:
                    ok = False
                    break
                cells = _split_two_shape_cells(om.group(2))
                if cells is None:
                    ok = False
                    break
                rows.append((om.group(1), cells[0], cells[1]))
            if ok and len(rows) == 4:
                col_a = header_m.group("a")
                col_b = header_m.group("b")
                out.append(f"| | {col_a} | {col_b} |")
                out.append("| --- | --- | --- |")
                for letter, c1, c2 in rows:
                    out.append(f"| {letter} | {c1} | {c2} |")
                i += 5
                continue
        out.append(line)
        i += 1
    return "\n".join(out)


def format_mcq_option_lines(text: str) -> str:
    """Ensure MCQ options A–D each start on their own line."""
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        split = _split_inline_abcd_line(line)
        if split is None:
            out.append(line)
        else:
            out.extend(split)
    return "\n".join(out)


def _split_inline_abcd_line(line: str) -> list[str] | None:
    """Split a single line that packs A/B/C/D options horizontally."""
    s = line.strip()
    if not s:
        return None

    # Bare "A B C D" (structure options covered by a figure)
    if re.fullmatch(r"A\s+B\s+C\s+D", s):
        return ["A", "B", "C", "D"]

    # Inline: [prefix]? A <a> B <b> C <c> D <d>
    m = re.match(
        r"^(?P<pre>.*?)"
        r"(?<![A-Za-z])A\s+(?P<a>\S.*?)\s+"
        r"B\s+(?P<b>\S.*?)\s+"
        r"C\s+(?P<c>\S.*?)\s+"
        r"D\s+(?P<d>\S.*?)\s*$",
        s,
    )
    if not m:
        return None
    pre = m.group("pre").strip()
    opts = [
        f"A {m.group('a').strip()}",
        f"B {m.group('b').strip()}",
        f"C {m.group('c').strip()}",
        f"D {m.group('d').strip()}",
    ]
    if pre:
        return [pre, *opts]
    return opts


def fix_reaction_layout(text: str) -> str:
    """Merge orphan ΔHc lines and insert missing reaction arrows."""
    text = fix_reaction_arrows(text)

    # Fix split water first
    text = re.sub(r"2H[₂2]\s*O\(l\)", "2H₂O(l)", text)
    text = re.sub(r"H[₂2]\s*O\(l\)", "H₂O(l)", text)

    # Orphan ΔHc / ΔH_c line immediately above an equation missing an arrow
    text = re.sub(
        r"(?:^|\n)(?:ΔH[cC]⦵|ΔH_c\^⦵)\s*\n"
        r"([^\n]*?\([^)\n]+\))\s+([A-Z][^\n]*\([^)\n]+\))",
        r"\n\1 → \2",
        text,
    )

    # Same-line: ...O₂(g) CO₂(g)...
    text = re.sub(
        r"(O[₂2]\(g\))\s+(CO[₂2]\(g\))",
        r"\1 → \2",
        text,
    )
    # Broader: ...(g) CO₂(g)... with no operator between state and next formula
    text = re.sub(
        r"(\((?:g|l|s|aq)\))\s{1,6}([A-Z][A-Za-z0-9₀₁₂₃₄₅₆₇₈₉]*\((?:g|l|s|aq)\))",
        r"\1 → \2",
        text,
    )
    return text


_SKIP_FORMULA_ATOMS = {"T", "X", "Y", "R", "Z"}


def _collapse_thermochemical_line(text: str) -> str:
    """Turn 'reactants ΔHc → products' into a single MathJax xrightarrow line."""
    # After delta_h conversion the label is already latex.
    pat = re.compile(
        r"(?P<left>(?:\$\\mathrm\{[^}]+\}(?:\([glsaq]\))?(?:\s*\+\s*)?)+)"
        r"\s*"
        r"(?P<dh>\$\\Delta H(?:_\{[^}]+\})?\{\^\{\\ominus\}\}|\$\\Delta H_\{\\mathrm\{[cf]\}\}\^\{\\ominus\}\$)"
        r"\s*→\s*"
        r"(?P<right>(?:\$\\mathrm\{[^}]+\}(?:\([glsaq]\))?(?:\s*\+\s*)?)+)"
    )

    def repl(m: re.Match[str]) -> str:
        left = m.group("left").replace("$", "").replace("\\mathrm{", "").replace("}", "")
        right = m.group("right").replace("$", "").replace("\\mathrm{", "").replace("}", "")
        # Keep a readable xrightarrow with c/f/n index
        dh = m.group("dh")
        if r"\mathrm{c}" in dh:
            label = r"\Delta H_{\mathrm{c}}^{\ominus}"
        elif r"\mathrm{f}" in dh:
            label = r"\Delta H_{\mathrm{f}}^{\ominus}"
        else:
            label = r"\Delta H^{\ominus}"
        return (
            f"${left.strip()} "
            f"\\xrightarrow{{{label}}} "
            f"{right.strip()}$"
        )

    # Simpler, robust pattern for the common extracted shape
    simple = re.compile(
        r"(\$\\mathrm\{CH_\{4\}\}\$\(g\) \+ 2\$\\mathrm\{O_\{2\}\}\$\(g\))"
        r"\s*(?:\$\\Delta H_\{\\mathrm\{c\}\}\^\{\\ominus\}\$)?\s*→\s*"
        r"(\$\\mathrm\{CO_\{2\}\}\$\(g\) \+ 2\$\\mathrm\{H_\{2\}O\}\$\(l\))"
    )
    text = simple.sub(
        r"$\\mathrm{CH_4}(g)+2\\mathrm{O_2}(g)"
        r"\\xrightarrow{\\Delta H_{\\mathrm{c}}^{\\ominus}}"
        r"\\mathrm{CO_2}(g)+2\\mathrm{H_2O}(l)$",
        text,
    )
    return text


# Common CIE PDF word-glue artifacts (no space between words)
_GLUE_FIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bshowboth\b", re.I), "show both"),
    (re.compile(r"\bofeach\b", re.I), "of each"),
    (re.compile(r"\bandare\b", re.I), "and are"),
    (re.compile(r"\bthestatements\b", re.I), "the statements"),
    (re.compile(r"\bresponsesA\s*toD\b", re.I), "responses A to D"),
    (re.compile(r"\b1,\s*2\s+and3\b", re.I), "1, 2 and 3"),
)


def _fix_pdf_word_glue(text: str) -> str:
    for pat, repl in _GLUE_FIXES:
        text = pat.sub(repl, text)
    return text


def format_chemistry_text(text: str) -> str:
    """Best-effort Obsidian/MathJax formatting for extracted chemistry text."""
    if not text:
        return text

    from chembank.symbols import normalize_chars

    text = normalize_chars(text)
    text = _fix_pdf_word_glue(text)
    text = fix_reaction_layout(text)
    text = format_mcq_option_lines(text)
    text = format_mcq_options_table(text)

    # Enthalpy symbols first (before formula wrapping eats ΔH)
    text = _DELTA_H_RE.sub(delta_h_to_latex, text)

    # Wrap common molecular formulae that still have unicode subscripts
    def _wrap_formula(m: re.Match[str]) -> str:
        whole = m.group(0)
        if "$" in whole:
            return whole
        core = m.group(2)
        core_alpha = re.sub(r"[₀₁₂₃₄₅₆₇₈₉0-9]+", "", core)
        if core_alpha in _SKIP_FORMULA_ATOMS:
            return whole
        if len(core) < 2 and not any(ch in core for ch in "₀₁₂₃₄₅₆₇₈₉"):
            return whole
        if not re.search(r"[₀₁₂₃₄₅₆₇₈₉0-9]|[A-Z][a-z]?[A-Z]", core + (m.group(4) or "")):
            return whole
        return formula_to_latex(whole)

    text = _FORMULA_RE.sub(_wrap_formula, text)
    # Safety net: ion charges left as ]+ / ]- inside \mathrm{...}
    text = re.sub(r"(\\mathrm\{[^}]*\])\+\}", r"\1^{+}}", text)
    text = re.sub(r"(\\mathrm\{[^}]*\])\-\}", r"\1^{-}}", text)
    text = _collapse_thermochemical_line(text)

    # Temperature labels: keep unicode, fix glue
    text = re.sub(r"\band\s*T([₁₂12])\b", r"and T\1", text)
    text = re.sub(r"temperatures,\s*T", "temperatures, T", text)
    text = re.sub(r"on\s*the\s*y-axis", "on the y-axis", text)
    text = re.sub(r"ony-axis", "on y-axis", text)

    text = re.sub(r" +", " ", text)
    text = re.sub(r" +([,.;:?])", r"\1", text)
    text = re.sub(r"\s*→\s*", " → ", text)
    return text.strip()
