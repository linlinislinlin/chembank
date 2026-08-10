#!/usr/bin/env python3
"""Generate tagged/q*.json for draft/9701_s24_qp_21 (Paper 2 structured) by hand."""
import json
import os
import sys

import yaml

PAPER_ID = "9701_s24_qp_21"
DRAFT = os.path.join("draft", PAPER_ID)
TAGGED = os.path.join(DRAFT, "tagged")
QP = "raw/papers/9701_s24_qp_21.pdf"
MS = "raw/papers/9701_s24_ms_21.pdf"

LEV = {"level": "AS", "session": "MJ", "year": 2024, "paper": 21}

# slug -> (question_label, parent, part, marks, codes, los, lo_texts, skills, diff, command_words)
PARTS = {
 "1a": ("1(a)", "1", "(a)", 1, ["11.1"], ["11.1-1"],
        ["describe the colours and the trend in volatility of chlorine, bromine and iodine"],
        ["remember"], 2, ["Complete"]),
 "1b": ("1(b)", "1", "(b)", 3, ["11.1"], ["11.1-1", "11.1-3"],
        ["describe the colours and the trend in volatility of chlorine, bromine and iodine",
         "interpret the volatility of the elements in terms of instantaneous dipole-induced dipole forces"],
        ["explain"], 3, ["State", "Explain"]),
 "1c-i": ("1(c)(i)", "1", "(c)(i)", 1, ["11.2"], ["11.2-1"],
          ["describe the relative reactivity of the elements as oxidising agents"],
          ["apply", "construct"], 2, ["Construct"]),
 "1c-ii": ("1(c)(ii)", "1", "(c)(ii)", 1, ["11.2", "6.1"], ["11.2-1", "6.1-4"],
           ["describe the relative reactivity of the elements as oxidising agents",
            "explain and use the terms oxidising agent and reducing agent"],
           ["explain"], 2, ["State", "Explain"]),
 "1d-i": ("1(d)(i)", "1", "(d)(i)", 1, ["11.3"], ["11.3-2b"],
          ["describe and explain the reactions of halide ions with concentrated sulfuric acid, to include balanced chemical equations"],
          ["construct"], 2, ["Write"]),
 "1d-ii": ("1(d)(ii)", "1", "(d)(ii)", 3, ["11.3"], ["11.3-1", "11.3-2b"],
           ["describe the relative reactivity of halide ions as reducing agents",
            "describe and explain the reactions of halide ions with concentrated sulfuric acid, to include balanced chemical equations"],
           ["explain", "deduce"], 4, ["Deduce", "Explain"]),
 "2a-i": ("2(a)(i)", "2", "(a)(i)", 1, ["9.2"], ["9.2-5"],
          ["describe, explain, and write equations for, the reactions of the chlorides NaCl, MgCl2, AlCl3, SiCl4, PCl5 with water including the likely pHs of the solutions obtained"],
          ["recall"], 3, ["Identify"]),
 "2a-ii": ("2(a)(ii)", "2", "(a)(ii)", 1, ["9.2"], ["9.2-5"],
           ["describe, explain, and write equations for, the reactions of the chlorides NaCl, MgCl2, AlCl3, SiCl4, PCl5 with water including the likely pHs of the solutions obtained"],
           ["recall"], 3, ["Name"]),
 "2b-i": ("2(b)(i)", "2", "(b)(i)", 2, ["3.5", "3.4"], ["3.5-1", "3.4-1a"],
          ["describe and explain the shape of, and bond angles in, molecules of up to six electron pairs (including lone pairs)",
           "define covalent bonding as electrostatic attraction between the nuclei of two atoms and a shared pair of electrons"],
          ["apply", "draw"], 3, ["Complete"]),
 "2b-ii": ("2(b)(ii)", "2", "(b)(ii)", 2, ["3.5"], ["3.5-1", "3.5-2"],
           ["describe and explain the shape of, and bond angles in, molecules of up to six electron pairs (including lone pairs)",
            "predict the shapes of, and bond angles in, molecules and ions analogous to those specified in 3.5.1"],
           ["apply", "predict"], 3, ["Predict"]),
 "2c-i": ("2(c)(i)", "2", "(c)(i)", 1, ["6.1"], ["6.1-1"],
          ["calculate oxidation numbers of elements in compounds and ions"],
          ["deduce"], 2, ["Deduce"]),
 "2c-ii": ("2(c)(ii)", "2", "(c)(ii)", 1, ["12.1"], ["12.1-2c"],
           ["describe and explain: the displacement of ammonia from ammonium salts by an acid-base reaction"],
           ["construct"], 3, ["Construct"]),
 "2c-iii": ("2(c)(iii)", "2", "(c)(iii)", 2, ["12.1"], ["12.1-2a", "12.1-2c"],
            ["describe and explain: the basicity of ammonia, using the Brønsted-Lowry theory",
             "describe and explain: the displacement of ammonia from ammonium salts by an acid-base reaction"],
            ["explain"], 3, ["Explain"]),
 "2d-i": ("2(d)(i)", "2", "(d)(i)", 1, ["2.3"], ["2.3-1a"],
          ["write formulas of ionic compounds from ionic charges and oxidation numbers"],
          ["deduce"], 2, ["Deduce"]),
 "2d-ii": ("2(d)(ii)", "2", "(d)(ii)", 1, ["4.2"], ["4.2-1c"],
           ["describe, in simple terms, the lattice structure of a crystalline solid which is: a giant covalent"],
           ["suggest"], 3, ["Suggest"]),
 "3a": ("3(a)", "3", "(a)", 2, ["7.1"], ["7.1-2"],
        ["define Le Chatelier's principle as: if a change is made to a system at dynamic equilibrium"],
        ["remember"], 2, ["Define"]),
 "3b": ("3(b)", "3", "(b)", 3, ["7.1"], ["7.1-3", "7.1-9"],
        ["use Le Chatelier's principle to deduce qualitatively the effect of changes in conditions on a system",
         "state whether changes in temperature, concentration or pressure or the presence of a catalyst affect the value of Kc"],
        ["deduce", "explain"], 4, ["Deduce"]),
 "3c-i": ("3(c)(i)", "3", "(c)(i)", 2, ["7.1", "2.4"], ["7.1-8", "2.4-1c"],
          ["calculate the quantities present at equilibrium, given appropriate data",
           "perform calculations including use of the mole concept, involving: volumes and concentrations of solutions"],
          ["calculate"], 4, ["Calculate"]),
 "3c-ii": ("3(c)(ii)", "3", "(c)(ii)", 2, ["7.1", "7.2"], ["7.1-7", "7.2-1"],
           ["use the Kc and Kp expressions to carry out calculations",
            "deduce expressions for equilibrium constants in terms of concentrations, Kc"],
           ["calculate"], 4, ["Calculate", "State"]),
 "4a": ("4(a)", "4", "(a)", 2, ["5.1"], ["5.1-3b"],
        ["define and use the terms: enthalpy change with particular reference to: reaction, formation, combustion, neutralisation"],
        ["remember"], 2, ["Define"]),
 "4b-i": ("4(b)(i)", "4", "(b)(i)", 2, ["5.1"], ["5.1-3b"],
          ["define and use the terms: enthalpy change with particular reference to: reaction, formation, combustion, neutralisation"],
          ["construct"], 3, ["Complete"]),
 "4b-ii": ("4(b)(ii)", "4", "(b)(ii)", 2, ["5.2"], ["5.2-1", "5.2-2a"],
           ["apply Hess's law to construct simple energy cycles",
            "carry out calculations using cycles and relevant energy terms"],
           ["calculate"], 4, ["Calculate"]),
 "5a": ("5(a)", "5", "(a)", 1, ["3.4"], ["3.4-1a"],
        ["define covalent bonding as electrostatic attraction between the nuclei of two atoms and a shared pair of electrons"],
        ["remember"], 2, ["Define"]),
 "5b-i": ("5(b)(i)", "5", "(b)(i)", 1, ["13.3", "3.4"], ["13.3-2", "3.4-2c"],
          ["describe and explain the shape of, and bond angles in, molecules containing sp, sp2 and sp3 hybridised atoms",
           "use the concept of hybridisation to describe sp, sp2 and sp3 orbitals"],
          ["recall"], 3, ["Identify"]),
 "5b-ii": ("5(b)(ii)", "5", "(b)(ii)", 2, ["13.3"], ["13.3-3"],
           ["describe the arrangement of σ and π bonds in molecules containing sp, sp2 and sp3 hybridised atoms"],
           ["draw"], 3, ["Draw"]),
 "5c-i": ("5(c)(i)", "5", "(c)(i)", 1, ["3.4", "14.2"], ["3.4-2a"],
          ["describe covalent bonds in terms of orbital overlap giving σ and π bonds"],
          ["suggest", "explain"], 3, ["Suggest"]),
 "5c-ii": ("5(c)(ii)", "5", "(c)(ii)", 4, ["14.2"], ["14.2-4", "14.2-2a"],
           ["describe the mechanism of electrophilic addition in alkenes, using bromine/ethene and hydrogen bromide/propene",
            "describe the electrophilic addition of hydrogen in a hydrogenation reaction"],
           ["draw", "apply"], 5, ["Complete"]),
 "6a-i": ("6(a)(i)", "6", "(a)(i)", 1, ["13.4"], ["13.4-2"],
          ["describe stereoisomerism and its division into geometrical (cis/trans) and optical isomerism"],
          ["remember"], 2, ["Explain"]),
 "6a-ii": ("6(a)(ii)", "6", "(a)(ii)", 2, ["13.4"], ["13.4-5", "13.4-4"],
           ["identify chiral centres and geometrical (cis/trans) isomerism in a molecule of given structural formula including cyclic compounds",
            "explain what is meant by a chiral centre and that such a centre gives rise to two optical isomers (enantiomers)"],
           ["deduce", "explain"], 4, ["Deduce", "Explain"]),
 "6a-iii": ("6(a)(iii)", "6", "(a)(iii)", 1, ["2.3"], ["2.3-2a"],
            ["write formulas of ionic compounds from ionic charges and oxidation numbers"],
            ["deduce"], 3, ["Deduce"]),
 "6a-iv": ("6(a)(iv)", "6", "(a)(iv)", 1, ["13.1"], ["13.1-2"],
           ["understand that the compounds in the table contain a functional group which dictates their physical and chemical properties"],
           ["recall"], 3, ["Name"]),
 "6b-i": ("6(b)(i)", "6", "(b)(i)", 1, ["17.1", "6.1"], ["17.1-2a", "6.1-4"],
          ["describe: the reduction of aldehydes and ketones using NaBH4 or LiAlH4 to produce alcohols",
           "explain and use the terms oxidising agent and reducing agent"],
          ["identify"], 3, ["Identify"]),
 "6b-ii": ("6(b)(ii)", "6", "(b)(ii)", 1, ["17.1"], ["17.1-2a"],
           ["describe: the reduction of aldehydes and ketones using NaBH4 or LiAlH4 to produce alcohols"],
           ["suggest"], 3, ["Suggest"]),
 "6c-i": ("6(c)(i)", "6", "(c)(i)", 2, ["21.1"], ["21.1-1a"],
          ["recall the reactions for mass spectra"],
          ["calculate", "analyse"], 4, ["Calculate"]),
 "6c-ii": ("6(c)(ii)", "6", "(c)(ii)", 1, ["17.1"], ["17.1-4"],
           ["describe the use of 2,4-dinitrophenylhydrazine (2,4-DNPH reagent) to detect the presence of the carbonyl group"],
           ["recall"], 3, ["Complete"]),
 "6c-iii": ("6(c)(iii)", "6", "(c)(iii)", 2, ["16.1", "2.4"], ["16.1-2c", "2.4-1a"],
            ["describe: the reaction with Na(s)",
             "perform calculations including use of the mole concept, involving: reacting masses"],
            ["calculate"], 4, ["Calculate"]),
 "6c-iv": ("6(c)(iv)", "6", "(c)(iv)", 2, ["22.1"], ["22.1-1"],
           ["analyse an infrared spectrum of a simple molecule to identify functional groups"],
           ["describe", "explain"], 4, ["Describe", "Explain"]),
}

COMMANDS_BY_SKILL = {
    "remember": ["State", "Define", "Recall"],
    "explain": ["Explain"],
    "calculate": ["Calculate"],
    "construct": ["Construct", "Write"],
    "deduce": ["Deduce", "Suggest"],
    "apply": ["Apply"],
    "draw": ["Draw", "Complete"],
    "predict": ["Predict"],
    "identify": ["Identify", "Name"],
    "analyse": ["Analyse"],
    "forget": [],
}

SLUG = {
 "1a": "q1a", "1b": "q1b",
}


def slug_for(part_label: str) -> str:
    # map "1(a)(i)" -> "1a-i"
    s = part_label
    # parent
    import re
    m = re.match(r"^(\d+)(.+)$", s)
    parent, rest = m.group(1), m.group(2)
    out = parent
    # letters
    for token in re.findall(r"\(([a-z]+)\)\(([ivx]+)\)|\(([a-z]+)\)", rest):
        if token[0]:
            out += token[0]
            out += ("-" + token[1]) if token[1] else ""
        else:
            out += token[2]
    return "q" + out


def main():
    os.makedirs(TAGGED, exist_ok=True)
    written = 0
    for slug, spec in PARTS.items():
        question, parent, part, marks, codes, los, lo_texts, skills, diff = spec[:9]
        command_words = spec[9] if len(spec) > 9 else []
        qid = f"cie-9701-2024-mj-p21-q{slug}"
        rec = {
            "id": qid,
            "exam_board": "CIE",
            "syllabus_code": "9701",
            "level": LEV["level"],
            "year": LEV["year"],
            "session": LEV["session"],
            "paper": LEV["paper"],
            "question": question,
            "parent_question": parent,
            "part": part,
            "marks": marks,
            "syllabus_codes": codes,
            "topic_titles": [],
            "skills": skills,
            "question_type": "structured",
            "difficulty": diff,
            "command_words": command_words,
            "misconceptions": [],
            "learning_objectives": [],
            "learning_outcomes": los,
            "learning_outcome_texts": [],
            "ms_answer": None,
            "source_qp": QP,
            "source_ms": MS,
            "page_qp": None,
            "page_ms": None,
            "body": "",
            "mark_scheme": "",
            "figures": [],
        }
        with open(os.path.join(TAGGED, f"q{slug}.json"), "w") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        written += 1
    print(f"wrote {written} tagged JSON files to {TAGGED}")

    syl = yaml.safe_load(open("syllabus/cie-9701-as-a-level-chemistry.yaml"))
    valid_codes, valid_los = set(), set()
    for t in syl["topics"]:
        valid_codes.add(str(t["code"]))
        for st in t["subtopics"]:
            valid_codes.add(str(st["code"]))
            for lo in st["learning_outcomes"]:
                valid_los.add(str(lo["id"]))
    bad = []
    for slug, spec in PARTS.items():
        for c in spec[4]:
            if c not in valid_codes:
                bad.append((slug, "code", c))
        for lo in spec[5]:
            if lo not in valid_los:
                bad.append((slug, "lo", lo))
    if bad:
        print("INVALID TAGS:", bad)
        sys.exit(1)
    print("Validation OK: all codes + LOs are in the controlled vocabulary.")


if __name__ == "__main__":
    main()
