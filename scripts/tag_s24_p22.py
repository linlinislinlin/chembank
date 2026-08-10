#!/usr/bin/env python3
"""Generate tagged/q*.json for draft/9701_s24_qp_22 (Paper 2 structured) by hand."""
import json
import os
import sys

import yaml

PAPER_ID = "9701_s24_qp_22"
DRAFT = os.path.join("draft", PAPER_ID)
TAGGED = os.path.join(DRAFT, "tagged")
QP = "raw/papers/9701_s24_qp_22.pdf"
MS = "raw/papers/9701_s24_ms_22.pdf"

LEV = {"level": "AS", "session": "MJ", "year": 2024, "paper": 22}

# slug -> (question, parent, part, marks, codes, los, lo_texts, skills, diff, command_words)
PARTS = {
 "1a": ("1(a)", "1", "(a)", 2, ["1.1", "2.2"], ["1.1-6", "1.1-3", "2.2-1"],
        ["determine the numbers of protons, neutrons and electrons present in both atoms and ions",
         "understand the terms atomic and proton number; mass and nucleon number",
         "define and use the term mole in terms of the Avogadro constant"],
        ["construct"], 2, ["Complete"]),
 "1b": ("1(b)", "1", "(b)", 3, ["1.1"], ["1.1-7"],
        ["state and explain qualitatively the variations in atomic radius and ionic radius across a period and down a group"],
        ["state", "explain"], 3, ["State", "Explain"]),
 "1c": ("1(c)", "1", "(c)", 1, ["3.3"], ["3.3-1"],
        ["define metallic bonding as the electrostatic attraction between positive metal ions and delocalised electrons"],
        ["draw", "apply"], 2, ["Draw"]),
 "1d-i": ("1(d)(i)", "1", "(d)(i)", 1, ["9.1", "4.2"], ["9.1-2"],
          ["explain the variation in melting point and electrical conductivity in terms of the structure and bonding of the period 3 elements"],
          ["explain"], 3, ["Explain"]),
 "1d-ii": ("1(d)(ii)", "1", "(d)(ii)", 2, ["9.1"], ["9.1-1", "9.1-2"],
           ["describe qualitatively the variations in melting point of the elements",
            "explain the variation in melting point and electrical conductivity in terms of the structure and bonding"],
           ["apply", "draw"], 3, ["Complete"]),
 "1e-i": ("1(e)(i)", "1", "(e)(i)", 2, ["9.2"], ["9.2-4", "9.2-3"],
          ["describe, explain, and write equations for, the acid / base behaviour of the oxides Na2O, MgO, Al2O3, P4O10, SO2 and SO3",
           "describe, and write equations for, the reactions, if any, of the oxides Na2O, MgO, Al2O3, SiO2, P4O10, SO2 and SO3 with water"],
          ["recall", "deduce"], 4, ["Complete"]),
 "1e-ii": ("1(e)(ii)", "1", "(e)(ii)", 1, ["9.2"], ["9.2-4"],
           ["describe, explain, and write equations for, the acid / base behaviour of the oxides"],
           ["recognise"], 3, ["Name"]),
 "1e-iii": ("1(e)(iii)", "1", "(e)(iii)", 1, ["9.2"], ["9.2-3"],
            ["describe, and write equations for, the reactions, if any, of the oxides with water"],
            ["construct"], 3, ["Write"]),
 "1f-i": ("1(f)(i)", "1", "(f)(i)", 1, ["9.2"], ["9.2-4"],
          ["describe, explain, and write equations for, the acid / base behaviour of the oxides and hydroxides"],
          ["explain"], 2, ["Explain"]),
 "1f-ii": ("1(f)(ii)", "1", "(f)(ii)", 1, ["9.2"], ["9.2-4"],
           ["describe, explain, and write equations for, the acid / base behaviour of the oxides and hydroxides"],
           ["construct"], 3, ["Write"]),
 "2a": ("2(a)", "2", "(a)", 2, ["5.1", "8.2"], ["5.1-2", "8.2-1"],
        ["construct and interpret a reaction pathway diagram, in terms of the enthalpy change of the reaction and of the activation energy",
         "define activation energy, EA, as the minimum energy required for a collision to be effective"],
        ["draw", "apply"], 4, ["Complete", "Label"]),
 "2b-i": ("2(b)(i)", "2", "(b)(i)", 1, ["5.2"], ["5.2-1"],
          ["apply Hess's law to construct simple energy cycles"],
          ["observe"], 2, ["Describe"]),
 "2b-ii": ("2(b)(ii)", "2", "(b)(ii)", 3, ["5.2"], ["5.1-7", "5.2-2a"],
           ["calculate enthalpy changes from appropriate experimental results, including the use of the relationships q = mcΔT",
            "carry out calculations using cycles and relevant energy terms"],
           ["calculate"], 4, ["Calculate"]),
 "2b-iii": ("2(b)(iii)", "2", "(b)(iii)", 2, ["5.2"], ["5.2-1", "5.2-2a"],
            ["apply Hess's law to construct simple energy cycles",
             "carry out calculations using cycles and relevant energy terms"],
            ["calculate"], 4, ["Calculate"]),
 "2c": ("2(c)", "2", "(c)", 2, ["10.1"], ["10.1-3"],
        ["describe, and write equations for, the thermal decomposition of the nitrates and carbonates, to include the trend in thermal stabilities"],
        ["deduce", "construct"], 4, ["Identify", "Write"]),
 "3a": ("3(a)", "3", "(a)", 2, ["7.1"], ["7.1-1b"],
        ["understand what is meant by dynamic equilibrium in terms of the rate of forward and reverse reactions"],
        ["recall", "explain"], 2, ["Describe"]),
 "3b-i": ("3(b)(i)", "3", "(b)(i)", 3, ["7.1"], ["7.1-3", "7.1-7"],
          ["use Le Chatelier's principle to deduce qualitatively the effects of changes in concentration",
           "use the Kc and Kp expressions to carry out calculations"],
          ["deduce", "state"], 4, ["Deduce"]),
 "3b-ii": ("3(b)(ii)", "3", "(b)(ii)", 4, ["7.1"], ["7.1-4", "7.1-7"],
           ["deduce expressions for equilibrium constants in terms of concentrations, Kc",
            "use the Kc and Kp expressions to carry out calculations"],
           ["calculate"], 4, ["Calculate", "State"]),
 "3c": ("3(c)", "3", "(c)", 1, ["1.3"], ["1.3-3"],
        ["describe the electronic configuration of atoms and ions of the first 36 elements"],
        ["recall"], 3, ["Determine"]),
 "3d": ("3(d)", "3", "(d)", 2, ["3.4", "3.5"], ["3.4-1a"],
        ["define covalent bonding as electrostatic attraction between the nuclei of two atoms and a shared pair of electrons"],
        ["draw", "apply"], 3, ["Complete"]),
 "4a": ("4(a)", "4", "(a)", 2, ["13.4"], ["13.4-4", "13.4-2"],
        ["explain what is meant by a chiral centre and that such a centre gives rise to two optical isomers (enantiomers)",
         "describe stereoisomerism and its division into geometrical (cis/trans) and optical isomerism"],
        ["draw", "apply"], 4, ["Draw"]),
 "4b": ("4(b)", "4", "(b)", 3, ["15.1"], ["15.1-5", "15.1-6"],
        ["describe the SN1 and SN2 mechanisms of nucleophilic substitution in halogenoalkanes including the inductive effects of alkyl groups",
         "recall that primary halogenoalkanes tend to react via the SN2 mechanism; tertiary halogenoalkanes via the SN1 mechanism"],
        ["draw", "apply"], 5, ["Complete"]),
 "4c": ("4(c)", "4", "(c)", 3, ["15.1", "14.2", "16.1"], ["15.1-3d", "14.2-3", "16.1-3b"],
        ["describe the reaction with aqueous silver nitrate in ethanol",
         "describe the use of aqueous bromine to show the presence of a C=C bond",
         "state characteristic distinguishing reactions of alcohols"],
        ["recall", "deduce"], 4, ["Complete"]),
 "4d-i": ("4(d)(i)", "4", "(d)(i)", 1, ["15.1"], ["15.1-4"],
          ["describe the elimination reaction with NaOH in ethanol and heat to produce an alkene"],
          ["recall"], 3, ["Name"]),
 "4d-ii": ("4(d)(ii)", "4", "(d)(ii)", 1, ["15.1"], ["15.1-4"],
           ["describe the elimination reaction with NaOH in ethanol and heat to produce an alkene"],
           ["recall"], 3, ["Identify"]),
 "4e-i": ("4(e)(i)", "4", "(e)(i)", 2, ["13.3"], ["13.3-2"],
          ["describe and explain the shape of, and bond angles in, molecules containing sp, sp2 and sp3 hybridised atoms"],
          ["deduce"], 4, ["Complete"]),
 "4e-ii": ("4(e)(ii)", "4", "(e)(ii)", 3, ["13.4"], ["13.4-3", "13.4-5"],
           ["describe geometrical (cis/trans) isomerism in alkenes, and explain its origin in terms of restricted rotation about the C=C bond",
            "identify chiral centres and geometrical (cis/trans) isomerism in a molecule of given structural formula"],
           ["describe", "explain"], 4, ["Describe", "Explain"]),
 "5a-i": ("5(a)(i)", "5", "(a)(i)", 1, ["22.2"], ["22.2-1"],
          ["analyse mass spectra in terms of m/e values and isotopic abundances"],
          ["calculate"], 3, ["Calculate"]),
 "5a-ii": ("5(a)(ii)", "5", "(a)(ii)", 2, ["22.2"], ["22.2-4"],
           ["suggest the identity of molecules formed by simple fragmentation in a given mass spectrum"],
           ["suggest"], 3, ["Suggest"]),
 "5b-i": ("5(b)(i)", "5", "(b)(i)", 1, ["22.1"], ["22.1-1"],
          ["analyse an infrared spectrum of a simple molecule to identify functional groups"],
          ["recall", "analyse"], 3, ["Complete"]),
 "5b-ii": ("5(b)(ii)", "5", "(b)(ii)", 1, ["16.1", "22.1"], ["16.1-2d", "22.1-1"],
           ["describe: oxidation with acidified K2Cr2O7 or acidified KMnO4 to: carbonyl compounds by distillation; carboxylic acids by refluxing",
            "analyse an infrared spectrum of a simple molecule to identify functional groups"],
           ["deduce", "draw"], 4, ["Use"]),
 "5c-i": ("5(c)(i)", "5", "(c)(i)", 1, ["16.1"], ["16.1-3a"],
          ["classify alcohols as primary, secondary and tertiary alcohols"],
          ["deduce"], 3, ["Name"]),
 "5c-ii": ("5(c)(ii)", "5", "(c)(ii)", 1, ["16.1"], ["16.1-2c"],
           ["describe: the reaction with Na(s)"],
           ["construct"], 3, ["Complete"]),
 "5c-iii": ("5(c)(iii)", "5", "(c)(iii)", 1, ["16.1"], ["16.1-3a"],
            ["classify alcohols as primary, secondary and tertiary alcohols"],
            ["deduce", "draw"], 3, ["Draw"]),
}

def main():
    os.makedirs(TAGGED, exist_ok=True)
    for slug, spec in PARTS.items():
        question, parent, part, marks, codes, los, lo_texts, skills, diff = spec[:9]
        command_words = spec[9] if len(spec) > 9 else []
        qid = f"cie-9701-2024-mj-p22-q{slug}"
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
    print(f"wrote {len(PARTS)} tagged JSON files to {TAGGED}")

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
