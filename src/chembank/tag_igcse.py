"""Heuristic tagging for CIE 0620 (IGCSE) drafts.

Maps question text onto the 0620 Core/Supplement vocabulary. Output is
**provisional** until a human or skill pass re-tags by assessed skill.
"""

from __future__ import annotations

import re
from typing import Any

from chembank.syllabus import flatten_codes, flatten_learning_outcomes, parent_code_for_lo

_STOP = {
    "the", "and", "or", "of", "a", "an", "to", "in", "on", "for", "with", "from",
    "that", "this", "as", "is", "are", "be", "by", "at", "it", "its", "their",
    "which", "what", "how", "when", "where", "who", "why", "using", "used",
    "use", "into", "not", "only", "each", "both", "between", "given", "shown",
    "following", "following", "limited", "include", "including", "state",
    "describe", "explain", "define", "identify", "calculate", "predict",
    "suggest", "draw", "write", "name", "give", "show",
}

_SUBTOPIC_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(diffusion|kinetic particle|heating curve|cooling curve)\b", re.I), "1.2"),
    (re.compile(r"\b(solid|liquid|gas|melting|boiling|evaporat|condensing|freezing)\b", re.I), "1.1"),
    (re.compile(r"\b(isotope|relative atomic mass|abundance)\b", re.I), "2.3"),
    (re.compile(r"\b(ionic bond|cation|anion|giant lattice)\b", re.I), "2.4"),
    (re.compile(r"\b(covalent|dot-and-cross|simple molecular)\b", re.I), "2.5"),
    (re.compile(r"\b(graphite|diamond|silicon\(IV\) oxide|giant covalent)\b", re.I), "2.6"),
    (re.compile(r"\b(metallic bond|delocalised|malleab|ductil)\b", re.I), "2.7"),
    (re.compile(r"\b(proton|neutron|electron|electronic configuration|nucleon|atomic number)\b", re.I), "2.2"),
    (re.compile(r"\b(element|compound|mixture)\b", re.I), "2.1"),
    (re.compile(r"\b(mole|avogadro|mol\b|dm3|limiting reactant|percentage yield|empirical formula)\b", re.I), "3.3"),
    (re.compile(r"\b(relative molecular mass|relative formula mass|Mr\b|Ar\b)\b", re.I), "3.2"),
    (re.compile(r"\b(empirical|molecular formula|word equation|symbol equation|ionic equation)\b", re.I), "3.1"),
    (re.compile(r"\b(electrolys|anode|cathode|electroplate|electrolyte)\b", re.I), "4.1"),
    (re.compile(r"\b(fuel cell)\b", re.I), "4.2"),
    (re.compile(r"\b(exothermic|endothermic|enthalpy|bond energy|activation energy|pathway diagram)\b", re.I), "5.1"),
    (re.compile(r"\b(rate of reaction|catalyst|collision|concentration.*rate)\b", re.I), "6.2"),
    (re.compile(r"\b(equilibrium|reversible|haber|contact process)\b", re.I), "6.3"),
    (re.compile(r"\b(redox|oxidation|reduction|oxidising|reducing agent|oxidation number)\b", re.I), "6.4"),
    (re.compile(r"\b(physical and chemical change|physical change)\b", re.I), "6.1"),
    (re.compile(r"\b(acid|alkali|base|neutrali|pH|proton donor)\b", re.I), "7.1"),
    (re.compile(r"\b(acidic oxide|basic oxide|amphoteric)\b", re.I), "7.2"),
    (re.compile(r"\b(preparation of salt|soluble salt|insoluble salt|crystallis)\b", re.I), "7.3"),
    (re.compile(r"\b(group I|alkali metal|lithium|sodium|potassium).*(react|trend)\b", re.I), "8.2"),
    (re.compile(r"\b(group VII|halogen|chlorine|bromine|iodine|displacement)\b", re.I), "8.3"),
    (re.compile(r"\b(transition element|coloured compound|catalyst)\b", re.I), "8.4"),
    (re.compile(r"\b(noble gas)\b", re.I), "8.5"),
    (re.compile(r"\b(periodic table|group number|period number)\b", re.I), "8.1"),
    (re.compile(r"\b(alloy)\b", re.I), "9.3"),
    (re.compile(r"\b(reactivity series|displacement of metal)\b", re.I), "9.4"),
    (re.compile(r"\b(rust|corrosion|galvanis|sacrificial)\b", re.I), "9.5"),
    (re.compile(r"\b(blast furnace|extraction of|haematite|bauxite)\b", re.I), "9.6"),
    (re.compile(r"\b(uses of (aluminium|copper|steel)|electrical wiring)\b", re.I), "9.2"),
    (re.compile(r"\b(malleable|ductile|metal).*(propert)\b", re.I), "9.1"),
    (re.compile(r"\b(fertiliser|npk|ammonia.*crop)\b", re.I), "10.2"),
    (re.compile(r"\b(greenhouse|climate|acid rain|photosynthesis|pollutant|carbon monoxide)\b", re.I), "10.3"),
    (re.compile(r"\b(potable|water treatment|chlorination)\b", re.I), "10.1"),
    (re.compile(r"\b(homologous|functional group|isomer|displayed formula|unsaturated|saturated compound)\b", re.I), "11.1"),
    (re.compile(r"\b(name.*alkane|IUPAC|propan|butan|-oic acid|-ene|-ol)\b", re.I), "11.2"),
    (re.compile(r"\b(fractional distillation|petroleum|fossil fuel|refinery)\b", re.I), "11.3"),
    (re.compile(r"\b(alkane|substitution.*ultraviolet|methane)\b", re.I), "11.4"),
    (re.compile(r"\b(alkene|addition polymerisation|unsaturated hydrocarbon|bromine water)\b", re.I), "11.5"),
    (re.compile(r"\b(alcohol|ethanol|fermentation|oxid.*ethanoic)\b", re.I), "11.6"),
    (re.compile(r"\b(carboxylic|ethanoic acid|ester)\b", re.I), "11.7"),
    (re.compile(r"\b(polymer|nylon|poly\(ethene\)|condensation polymer|PET|protein)\b", re.I), "11.8"),
    (re.compile(r"\b(titration|burette|pipette|end-point)\b", re.I), "12.2"),
    (re.compile(r"\b(chromatograph|Rf\b|rf value)\b", re.I), "12.3"),
    (re.compile(r"\b(filtration|crystallisation|distillation|separating funnel)\b", re.I), "12.4"),
    (re.compile(r"\b(flame test|anion|cation|limewater|litmus.*gas)\b", re.I), "12.5"),
    (re.compile(r"\b(apparatus|measuring cylinder|gas syringe|stop-watch)\b", re.I), "12.1"),
]


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]*", text.lower())
    return {w for w in words if w not in _STOP and len(w) > 2}


def mock_tag_igcse(
    body: str,
    *,
    question_type: str = "mcq",
    syllabus: dict[str, Any],
) -> dict[str, Any]:
    """Pick 1–2 0620 LOs by subtopic hint then token overlap. Provisional."""
    lo_lookup = flatten_learning_outcomes(syllabus)
    code_titles = flatten_codes(syllabus)
    hinted: list[str] = []
    for pat, code in _SUBTOPIC_HINTS:
        if pat.search(body) and code not in hinted:
            hinted.append(code)
            if len(hinted) >= 2:
                break

    body_tok = _tokens(body)
    scored: list[tuple[float, str]] = []
    for lo_id, text in lo_lookup.items():
        parent = parent_code_for_lo(lo_id)
        if hinted and parent not in hinted and parent.split(".")[0] not in hinted:
            continue
        overlap = len(body_tok & _tokens(text))
        bonus = 4.0 if hinted and parent in hinted else 0.0
        if overlap or bonus:
            scored.append((overlap + bonus, lo_id))
    scored.sort(key=lambda x: (-x[0], x[1]))

    lo_ids: list[str] = []
    if scored:
        lo_ids.append(scored[0][1])
        if len(scored) > 1 and scored[1][0] >= scored[0][0] * 0.7:
            lo_ids.append(scored[1][1])
    elif hinted:
        # first LO under hinted subtopic
        for lo_id in lo_lookup:
            if parent_code_for_lo(lo_id) == hinted[0]:
                lo_ids.append(lo_id)
                break
    if not lo_ids:
        # last-resort: 2.1-C1 (elements/compounds/mixtures) — flag fallback
        fallback = "2.1-C1" if "2.1-C1" in lo_lookup else next(iter(lo_lookup))
        lo_ids = [fallback]

    codes: list[str] = []
    for lo_id in lo_ids:
        parent = parent_code_for_lo(lo_id)
        if parent in code_titles and parent not in codes:
            codes.append(parent)

    skills = ["recall"]
    if re.search(r"\b(calculate|how many|what is the mass|volume of)\b", body, re.I):
        skills = ["calculate"]
    elif re.search(r"\b(explain|why|because)\b", body, re.I):
        skills = ["explain"]
    elif re.search(r"\b(which (statement|diagram|structure))\b", body, re.I):
        skills = ["compare"]

    qtype = question_type if question_type in {
        "mcq", "structured", "extended", "practical", "data"
    } else "mcq"

    out: dict[str, Any] = {
        "syllabus_codes": codes,
        "skills": skills,
        "question_type": qtype,
        "difficulty": 3,
        "command_words": [],
        "misconceptions": [],
        "learning_outcomes": lo_ids,
        "learning_objectives": [],
        "_provisional": True,
    }
    return out


def infer_practical_topic(body: str) -> str:
    """Map ATP / P6 text onto the controlled practical_topic enum."""
    if re.search(r"\b(titration|burette|end-point)\b", body, re.I):
        return "Titrations"
    if re.search(r"\b(flame test|cation|anion|unknown|solid [A-Z]|solution [A-Z])\b", body, re.I):
        return "Qualitative analysis"
    if re.search(r"\b(plan an investigation|your plan must)\b", body, re.I):
        return "Planning"
    if re.search(r"\b(temperature|exothermic|endothermic|enthalpy)\b", body, re.I):
        return "Thermometric experiments"
    if re.search(r"\b(rate|clock reaction|time taken)\b", body, re.I):
        return "Rate experiments"
    if re.search(r"\b(gas syringe|volume of gas)\b", body, re.I):
        return "Gas volume experiments"
    if re.search(r"\b(chromatograph|Rf)\b", body, re.I):
        return "Chromatography"
    if re.search(r"\b(salt|crystallis|filtrat)\b", body, re.I):
        return "Salt preparation"
    if re.search(r"\b(plan|method|procedure)\b", body, re.I):
        return "Planning"
    if re.search(r"\b(mass|weigh|crucible)\b", body, re.I):
        return "Gravimetric experiments"
    return "Measurement and apparatus"
