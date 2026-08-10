#!/usr/bin/env python3
"""Batch-tag structured Paper 2 drafts with controlled AS LO codes (no API)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from chembank.structured_parts import parse_part_id, question_id_prefix
from chembank.syllabus import (
    flatten_codes,
    flatten_learning_outcomes,
    load_syllabus,
    resolve_learning_outcomes,
    validate_learning_outcomes,
)

_SKILL_MAP = {
    "predict": "explain",
    "identify": "recall",
    "construct": "recall",
    "define": "recall",
}


def _norm_skills(skills: list[str]) -> list[str]:
    out: list[str] = []
    for s in skills:
        s = _SKILL_MAP.get(s, s)
        if s in ALLOWED_SKILLS and s not in out:
            out.append(s)
    return out or ["recall"]
from chembank.tag import (
    ALLOWED_SKILLS,
    allowed_code_list,
    infer_paper_meta_from_name,
    mock_tag_question,
    validate_tag_fields,
)

ROOT = Path(__file__).resolve().parents[1]

# Explicit per-paper overrides: question label -> (codes, los, skills, marks|None)
# Marks default from [n] in body when None.
OVERRIDES: dict[str, dict[str, tuple[list[str], list[str], list[str], int | None]]] = {
    "9701_s21_qp_22": {
        "1(a)": (["11.3"], ["11.3-2a"], ["recall"], 2),
        "1(b)": (["2.3"], ["2.3-2a"], ["construct"], 1),
        "1(c)": (["2.4", "2.1"], ["2.4-1a", "2.1-2"], ["calculate"], 3),
        "1(d)(i)": (["11.2"], ["11.2-1"], ["recall"], 1),
        "1(d)(ii)": (["11.2"], ["11.2-1"], ["recall"], 1),
        "1(e)": (["11.3"], ["11.3-2b"], ["recall"], 2),
        "1(f)(i)": (["10.1"], ["10.1-3"], ["explain"], 3),
        "1(f)(ii)": (["1.3"], ["1.3-6"], ["recall"], 1),
        "1(g)": (["10.1"], ["10.1-2"], ["compare"], 2),
        "2(a)(i)": (["3.2"], ["3.2-1"], ["recall"], 1),
        "2(a)(ii)": (["4.2", "3.2"], ["4.2-2", "3.2-1"], ["explain"], 2),
        "2(b)(i)": (["3.4"], ["3.4-1c"], ["explain"], 1),
        "2(b)(ii)": (["3.7"], ["3.7-1"], ["draw"], 2),
        "2(c)(i)": (["4.1"], ["4.1-2"], ["recall"], 2),
        "2(c)(ii)": (["4.1"], ["4.1-2"], ["explain"], 2),
        "2(c)(iii)": (["3.6"], ["3.6-3b"], ["recall"], 2),
        "2(c)(iv)": (["3.6"], ["3.6-2"], ["explain"], 1),
        "3(a)": (["8.1"], ["8.1-1"], ["explain"], 1),
        "3(b)(i)": (["8.2"], ["8.2-2"], ["draw"], 1),
        "3(b)(ii)": (["8.2"], ["8.2-3"], ["draw"], 2),
        "3(b)(iii)": (["8.2"], ["8.2-1"], ["recall"], 1),
        "3(c)(i)": (["15.1"], ["15.1-5"], ["draw"], 3),
        "3(c)(ii)": (["13.2", "15.1"], ["13.2-2c", "15.1-5"], ["recall"], 1),
        "3(d)": (["15.1"], ["15.1-7"], ["predict", "explain"], 2),
        "4(a)(i)": (["13.1", "13.4"], ["13.1-5", "13.4-3"], ["recall"], 4),
        "4(a)(ii)": (["13.4"], ["13.4-2"], ["explain"], 1),
        "4(b)(i)": (["14.2"], ["14.2-5"], ["identify"], 1),
        "4(b)(ii)": (["14.2"], ["14.2-5"], ["draw", "explain"], 3),
        "4(c)": (["14.2", "16.1"], ["14.2-1b", "16.1-2e"], ["identify"], 1),
        "4(d)(i)": (["16.1", "13.2"], ["16.1-2d", "13.2-1g"], ["recall"], 1),
        "4(d)(ii)": (["17.1"], ["17.1-5"], ["identify"], 1),
        "5(a)": (["13.1", "16.1"], ["13.1-4", "16.1-3a"], ["draw"], 1),
        "5(b)(i)": (["13.1"], ["13.1-5"], ["recall"], 1),
        "5(b)(ii)": (["13.2", "16.1"], ["13.2-1f", "16.1-2b"], ["recall"], 1),
        "5(b)(iii)": (["15.1"], ["15.1-3b"], ["recall"], 2),
        "5(b)(iv)": (["18.1"], ["18.1-1b"], ["construct"], 2),
        "5(b)(v)": (["22.1"], ["22.1-1"], ["explain"], 1),
    },
    "9701_s21_qp_23": {
        "1(a)(i)": (["11.1", "3.6"], ["11.1-3", "3.6-3b"], ["recall"], 1),
        "1(a)(ii)": (["11.1"], ["11.1-1"], ["explain"], 1),
        "1(b)": (["11.3"], ["11.3-2a"], ["recall", "explain"], 3),
        "1(c)": (["11.2", "6.1"], ["11.2-1", "6.1-3"], ["construct"], 1),
        "1(d)(i)": (["7.2"], ["7.2-3"], ["define"], 1),
        "1(d)(ii)": (["7.2"], ["7.2-3"], ["construct"], 1),
        "1(e)": (["11.3"], ["11.3-1"], ["explain"], 3),
        "1(f)": (["6.1"], ["6.1-2"], ["construct"], 2),
        "2(a)": (["3.6", "3.4"], ["3.6-1a", "3.4-1a"], ["explain"], 3),
        "2(b)(i)": (["4.1"], ["4.1-1"], ["explain"], 2),
        "2(b)(ii)": (["4.1", "3.6"], ["4.1-1", "3.6-3a"], ["explain"], 1),
        "2(b)(iii)": (["3.6"], ["3.6-1a"], ["explain"], 2),
        "2(c)(i)": (["7.1"], ["7.1-1b"], ["explain"], 2),
        "2(c)(ii)": (["7.1"], ["7.1-5"], ["calculate"], 2),
        "2(c)(iii)": (["7.1"], ["7.1-6"], ["calculate"], 2),
        "3(a)(i)": (["9.2"], ["9.2-3"], ["recall"], 4),
        "3(a)(ii)": (["9.2"], ["9.2-3"], ["identify"], 1),
        "3(a)(iii)": (["9.2"], ["9.2-5"], ["recall"], 1),
        "3(b)(i)": (["9.2", "4.2"], ["9.2-7", "4.2-1c"], ["recall"], 1),
        "3(b)(ii)": (["9.2"], ["9.2-7"], ["recall"], 1),
        "3(c)": (["9.2"], ["9.2-4"], ["explain"], 3),
        "4(a)(i)": (["13.1"], ["13.1-5"], ["recall"], 1),
        "4(a)(ii)": (["13.1"], ["13.1-3"], ["recall"], 1),
        "4(a)(iii)": (["16.1"], ["16.1-2d"], ["recall"], 1),
        "4(b)": (["14.2", "15.1"], ["14.2-2a", "15.1-1b"], ["draw"], 4),
        "4(c)": (["21.1", "15.1"], ["21.1-2", "15.1-3b"], ["construct"], 5),
        "5(a)": (["13.1", "18.1"], ["13.1-4", "18.1-2a"], ["draw", "calculate"], 3),
        "5(b)(i)": (["18.1", "16.1"], ["18.1-2c", "16.1-2c"], ["construct"], 2),
        "5(b)(ii)": (["16.1", "18.1"], ["16.1-2d", "18.1-1a"], ["explain"], 2),
        "5(c)": (["22.1"], ["22.1-1"], ["explain"], 2),
        "5(d)": (["13.4"], ["13.4-4"], ["identify"], 1),
    },
}

# Extra keyword → (codes, preferred LO ids) applied when no override
_EXTRA_RULES: list[tuple[re.Pattern[str], list[str], list[str], list[str]]] = [
    (re.compile(r"\bstereoisomer", re.I), ["13.4"], ["13.4-2"], ["explain"]),
    (re.compile(r"\bcoordinate bond|dative", re.I), ["3.4"], ["3.4-1c"], ["explain"]),
    (re.compile(r"\bdot[- ]and[- ]cross|dot and cross", re.I), ["3.7"], ["3.7-1"], ["draw"]),
    (re.compile(r"\bBr[oø]nsted", re.I), ["7.2"], ["7.2-3"], ["define"]),
    (re.compile(r"\bweak acid", re.I), ["7.2"], ["7.2-4"], ["recall"]),
    (re.compile(r"\bstrong .{0,20}acid", re.I), ["7.2"], ["7.2-4"], ["recall"]),
    (re.compile(r"\bconjugate base", re.I), ["7.2"], ["7.2-3"], ["recall"]),
    (re.compile(r"\bdynamic equilibrium", re.I), ["7.1"], ["7.1-1b"], ["explain"]),
    (re.compile(r"\bKp\b", re.I), ["7.1"], ["7.1-6"], ["calculate"]),
    (re.compile(r"\bKc\b", re.I), ["7.1"], ["7.1-4"], ["calculate"]),
    (re.compile(r"\bpartial pressure|mole fraction", re.I), ["7.1"], ["7.1-5"], ["calculate"]),
    (re.compile(r"\bideal gas", re.I), ["4.1"], ["4.1-2"], ["explain"]),
    (re.compile(r"\bpV\s*=\s*nRT|ideal gas equation", re.I), ["4.1"], ["4.1-3"], ["calculate"]),
    (re.compile(r"\bvapour pressure", re.I), ["4.1"], ["4.1-1"], ["explain"]),
    (re.compile(r"\bBoltzmann|activation energy|Eₐ|Ea\b", re.I), ["8.2"], ["8.2-2"], ["explain"]),
    (re.compile(r"\brate of reaction", re.I), ["8.1"], ["8.1-1"], ["explain"]),
    (re.compile(r"\bhomogeneous", re.I), ["8.3"], ["8.3-1a"], ["explain"]),
    (re.compile(r"\bionisation energy|ionization energy", re.I), ["1.4"], ["1.4-3"], ["explain"]),
    (re.compile(r"\belectron configuration|1s²|1s2", re.I), ["1.3"], ["1.3-6"], ["recall"]),
    (re.compile(r"\bhybridis|hybridiz|sp²|sp2|sp³|sp3|\bsp\b", re.I), ["3.4"], ["3.4-2c"], ["recall"]),
    (re.compile(r"\bbond angle", re.I), ["3.5"], ["3.5-1"], ["recall"]),
    (re.compile(r"\bvan der Waals|intermolecular|instantaneous dipole|permanent dipole", re.I), ["3.6"], ["3.6-3b"], ["explain"]),
    (re.compile(r"\bhydrogen bond", re.I), ["3.6"], ["3.6-1a"], ["explain"]),
    (re.compile(r"\bdipole moment|electronegativ", re.I), ["3.6", "3.1"], ["3.6-2", "3.1-1"], ["explain"]),
    (re.compile(r"\bgiant ionic|lattice structure|melting point", re.I), ["4.2"], ["4.2-2"], ["explain"]),
    (re.compile(r"\bGroup 2|thermal (stability|decomposition).*nitrate|Ca\(OH\)|calcium hydroxide", re.I), ["10.1"], ["10.1-3"], ["recall"]),
    (re.compile(r"\bGroup 17|halogen|AgNO₃|AgNO3|cream precipitate|AgBr", re.I), ["11.3"], ["11.3-2a"], ["recall"]),
    (re.compile(r"\bconcentrated sulfuric|conc\.?\s*H2SO4|concentrated H₂SO₄", re.I), ["11.3"], ["11.3-2b"], ["recall"]),
    (re.compile(r"\bdisproportionation", re.I), ["6.1"], ["6.1-3"], ["define"]),
    (re.compile(r"\boxidation number|oxidation state|redox", re.I), ["6.1"], ["6.1-3"], ["explain"]),
    (re.compile(r"\bPeriod 3|P4O10|P₄O₁₀|ceramic|amphoteric", re.I), ["9.2"], ["9.2-4"], ["explain"]),
    (re.compile(r"\banionic radius|atomic radius|ionic radius", re.I), ["1.1", "9.1"], ["1.1-7", "9.1-1"], ["explain"]),
    (re.compile(r"\benthalpy change of combustion|ΔHc|∆Hc", re.I), ["5.1"], ["5.1-3b"], ["define"]),
    (re.compile(r"\benthalpy change of formation|ΔHf|∆Hf|standard enthalpy", re.I), ["5.1"], ["5.1-3b"], ["define"]),
    (re.compile(r"\bbond energy|Hess", re.I), ["5.1", "5.2"], ["5.1-5"], ["calculate"]),
    (re.compile(r"\binfrared|IR spectrum|wavenumber", re.I), ["22.1"], ["22.1-1"], ["explain"]),
    (re.compile(r"\bTollens|Fehling|2,4-DNPH|2,4-dinitrophenylhydrazine", re.I), ["17.1"], ["17.1-5"], ["recall"]),
    (re.compile(r"\bnucleophilic substitution|SN1|SN2", re.I), ["15.1", "13.2"], ["15.1-5", "13.2-2c"], ["recall"]),
    (re.compile(r"\belectrophilic addition|Markovnikov|carbocation", re.I), ["14.2"], ["14.2-5"], ["explain"]),
    (re.compile(r"\bfree[- ]radical|initiation|propagation|termination|ultraviolet|UV light", re.I), ["14.1", "13.2"], ["14.1-3", "13.2-2a"], ["recall"]),
    (re.compile(r"\bdehydrat|concentrated sulfuric acid.*propene|alkene.*alcohol", re.I), ["14.2", "16.1"], ["14.2-1b"], ["recall"]),
    (re.compile(r"\bNaCN|KCN|nitrile|C≡N|C→N", re.I), ["15.1", "18.1"], ["15.1-3b"], ["recall"]),
    (re.compile(r"\bNaBH4|NaBH₄|LiAlH4|LiAlH₄|reduc", re.I), ["17.1"], ["17.1-2a"], ["recall"]),
    (re.compile(r"\bCr2O7|Cr₂O₇|acidified.*oxid", re.I), ["16.1"], ["16.1-2d"], ["recall"]),
    (re.compile(r"\bSOCl2|SOCl₂|PBr3|PBr₃|halogenoalkane", re.I), ["15.1", "16.1"], ["15.1-1c"], ["recall"]),
    (re.compile(r"\bpolymer|addition polymerisation", re.I), ["20.1"], ["20.1-1"], ["recall"]),
    (re.compile(r"\bvolatile", re.I), ["11.1", "3.6"], ["11.1-3"], ["recall"]),
    (re.compile(r"\benvironmental consequences|acid rain|SO2\(g\)", re.I), ["12.1", "14.1"], ["12.1-5"], ["recall"]),
    (re.compile(r"\bnitrogen.*reactivity|lack of reactivity of nitrogen", re.I), ["12.1"], ["12.1-1"], ["explain"]),
    (re.compile(r"\bsystematic name", re.I), ["13.1"], ["13.1-5"], ["recall"]),
    (re.compile(r"\bdisplayed formula|skeletal formula", re.I), ["13.1"], ["13.1-4"], ["draw"]),
    (re.compile(r"\bchiral|optical isomer", re.I), ["13.4"], ["13.4-4"], ["identify"]),
]


def _default_los_for_codes(codes: list[str], lo_lookup: dict[str, str]) -> list[str]:
    out: list[str] = []
    for c in codes:
        matches = sorted(k for k in lo_lookup if k.startswith(c + "-"))
        if matches:
            out.append(matches[0])
    return out


def _extract_marks(body: str) -> int | None:
    marks = re.findall(r"\[(\d+)\]", body)
    return int(marks[-1]) if marks else None


def _extract_command_words(body: str) -> list[str]:
    words = [
        "Explain",
        "State",
        "Calculate",
        "Construct",
        "Identify",
        "Suggest",
        "Describe",
        "Define",
        "Draw",
        "Name",
        "Complete",
        "Predict",
        "Compare",
        "Deduce",
        "Give",
        "Write",
        "Label",
        "Sketch",
    ]
    found: list[str] = []
    for w in words:
        if re.search(rf"\b{w}\b", body, re.I):
            found.append(w)
    return found


def _choose_tags(body: str, allowed: set[str], lo_lookup: dict[str, str]):
    for pattern, codes, los, skills in _EXTRA_RULES:
        if pattern.search(body):
            codes = [c for c in codes if c in allowed]
            los = [x for x in los if x in lo_lookup]
            if codes and los:
                return codes, los, [s for s in skills if s in ALLOWED_SKILLS] or ["recall"]

    raw = mock_tag_question(body, question_type="structured")
    codes = [c for c in (raw.get("syllabus_codes") or []) if c in allowed]
    if not codes:
        codes = ["13.1"] if re.search(r"\b(organic|alkene|alcohol|C\d+H)", body, re.I) else ["2.3"]
        codes = [c for c in codes if c in allowed] or [sorted(allowed)[0]]
    los = _default_los_for_codes(codes, lo_lookup)
    skills = [s for s in (raw.get("skills") or []) if s in ALLOWED_SKILLS] or ["recall"]
    return codes, los, skills


def tag_paper(draft_name: str) -> int:
    draft_dir = ROOT / "draft" / draft_name
    index = json.loads((draft_dir / "index.json").read_text(encoding="utf-8"))
    meta = infer_paper_meta_from_name(draft_name)
    meta.level = "AS"
    syllabus = load_syllabus()
    allowed = {c for c, _ in allowed_code_list(as_only=True)}
    lo_lookup = flatten_learning_outcomes(syllabus)
    titles = flatten_codes(syllabus)
    overrides = OVERRIDES.get(draft_name, {})

    # Build a sample id prefix via first part slug
    sample_q = index[0]["question"]
    sample_pid = parse_part_id(sample_q)
    sample_id = f"cie-9701-{meta.year}-{(meta.session or 'xx').lower()}-p{meta.paper}-q{sample_pid.slug}"
    prefix = question_id_prefix(sample_id)

    out_dir = draft_dir / "tagged"
    out_dir.mkdir(parents=True, exist_ok=True)
    # clear old
    for old in out_dir.glob("q*.json"):
        old.unlink()

    count = 0
    for row in index:
        label = str(row["question"])
        pid = parse_part_id(label)
        if not pid:
            raise RuntimeError(f"{draft_name}: cannot parse part {label}")
        path = draft_dir / row["file"]
        text = path.read_text(encoding="utf-8")
        body, _, ms = text.partition("--- MARK SCHEME ---")
        body = body.strip()
        ms = ms.strip()

        if label in overrides:
            codes, los, skills, marks = overrides[label]
        else:
            codes, los, skills = _choose_tags(body, allowed, lo_lookup)
            marks = _extract_marks(body)
        skills = _norm_skills(skills)

        codes = [c for c in codes if c in allowed]
        if not codes:
            raise RuntimeError(f"{draft_name} {label}: no allowed codes")
        try:
            los = validate_learning_outcomes(los, syllabus=syllabus)
        except ValueError:
            los = []
        if not los:
            los = validate_learning_outcomes(
                _default_los_for_codes(codes, lo_lookup), syllabus=syllabus
            )
        if not los:
            raise RuntimeError(f"{draft_name} {label}: empty LO after validate")

        validated = validate_tag_fields(
            {
                "syllabus_codes": codes,
                "skills": skills,
                "question_type": "structured",
                "difficulty": 3,
                "command_words": _extract_command_words(body),
                "misconceptions": [],
                "learning_objectives": [],
                "learning_outcomes": los,
            },
            allowed_codes=allowed,
            syllabus=syllabus,
        )
        validated["topic_titles"] = [titles[c] for c in validated["syllabus_codes"] if c in titles]
        validated["learning_outcome_texts"] = resolve_learning_outcomes(
            validated["learning_outcomes"], syllabus
        )

        qid = f"{prefix}-q{pid.slug}"
        record = {
            "id": qid,
            "exam_board": "CIE",
            "syllabus_code": "9701",
            "level": "AS",
            "year": meta.year,
            "session": meta.session,
            "paper": int(meta.paper) if str(meta.paper).isdigit() else meta.paper,
            "question": label,
            "parent_question": pid.parent,
            "part": row.get("part") or (
                f"({pid.letter})" + (f"({pid.roman})" if pid.roman else "")
            ),
            "marks": marks if marks is not None else _extract_marks(body),
            **validated,
            "ms_answer": None,
            "source_qp": meta.source_qp,
            "source_ms": meta.source_ms,
            "page_qp": row.get("page_hint"),
            "page_ms": None,
            "body": body,
            "mark_scheme": ms,
            "figures": [],
        }
        (out_dir / f"{pid.draft_stem}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        count += 1
    return count


def main() -> None:
    papers = [
        "9701_s21_qp_22",
        "9701_s21_qp_23",
        "9701_m21_qp_22",
        "9701_w21_qp_21",
        "9701_w21_qp_22",
        "9701_w21_qp_23",
    ]
    for p in papers:
        n = tag_paper(p)
        print(f"{p}: tagged {n} parts")


if __name__ == "__main__":
    main()
