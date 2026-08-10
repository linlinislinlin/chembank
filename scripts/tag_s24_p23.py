#!/usr/bin/env python3
"""Generate tagged/q*.json for draft/9701_s24_qp_23 (Paper 2 structured) by hand."""
import json
import os
import sys

import yaml

PAPER_ID = "9701_s24_qp_23"
DRAFT = os.path.join("draft", PAPER_ID)
TAGGED = os.path.join(DRAFT, "tagged")
QP = "raw/papers/9701_s24_qp_23.pdf"
MS = "raw/papers/9701_s24_ms_23.pdf"

LEV = {"level": "AS", "session": "MJ", "year": 2024, "paper": 23}

# slug -> (question, parent, part, marks, codes, los, lo_texts, skills, diff, command_words)
PARTS = {
 "1a-i": ("1(a)(i)", "1", "(a)(i)", 2, ["12.1", "4.2"], ["12.1-1", "4.2-1c"],
          ["explain the lack of reactivity of nitrogen, with reference to the triple bond and the non-polarity of nitrogen",
           "describe, in simple terms, the lattice structure of a giant covalent solid"],
          ["state", "explain"], 3, ["Explain"]),
 "1a-ii": ("1(a)(ii)", "1", "(a)(ii)", 4, ["13.3"], ["13.3-3", "13.3-2"],
           ["describe the arrangement of sigma and pi bonds in molecules containing sp, sp2 and sp3 hybridised atoms",
            "describe and explain the shape of, and bond angles in, molecules containing sp, sp2 and sp3 hybridised atoms"],
           ["complete", "recall"], 4, ["Complete"]),
 "1b-i": ("1(b)(i)", "1", "(b)(i)", 1, ["6.1"], ["6.1-1"],
          ["calculate oxidation numbers of elements in compounds and ions"],
          ["state"], 2, ["State"]),
 "1b-ii": ("1(b)(ii)", "1", "(b)(ii)", 1, ["9.2"], ["9.2-2"],
           ["state and explain the variation in the oxidation number of the oxides in Period 3"],
           ["state"], 3, ["State"]),
 "1c-i": ("1(c)(i)", "1", "(c)(i)", 1, ["9.2"], ["9.2-3"],
          ["describe, and write equations for, the reactions, if any, of the oxides of Period 3 elements "],
          ["give"], 3, ["Give"]),
 "1c-ii": ("1(c)(ii)", "1", "(c)(ii)", 2, ["9.2"], ["9.2-4"],
           ["describe, explain, and write equations for, the acid / base behaviour of the oxides"],
           ["construct"], 4, ["Write"]),
 "1d-i": ("1(d)(i)", "1", "(d)(i)", 1, ["6.1"], ["6.1-1"],
          ["calculate oxidation numbers of elements in compounds and ions"],
          ["deduce"], 3, ["Deduce"]),
 "1d-ii": ("1(d)(ii)", "1", "(d)(ii)", 1, ["10.1"], ["10.1-3"],
           ["describe, and write equations for, the thermal decomposition of the nitrates and carbonates"],
           ["identify"], 3, ["Identify"]),
 "2a": ("2(a)", "2", "(a)", 1, ["7.1", "8.3"], ["7.1-10", "8.3-1a"],
        ["describe and explain the conditions used in the Haber process and the reasons for these conditions",
         "explain and use the terms catalyst and catalysis"],
        ["describe", "explain"], 3, ["Describe", "Explain"]),
 "2b-i": ("2(b)(i)", "2", "(b)(i)", 1, ["7.1"], ["7.1-10", "7.1-3"],
          ["describe and explain the conditions used in the Haber process and the reasons for these conditions",
           "use Le Chatelier's principle to deduce qualitatively the effects of changes in temperature"],
          ["describe", "explain"], 4, ["Describe", "Explain"]),
 "2b-ii": ("2(b)(ii)", "2", "(b)(ii)", 2, ["8.2", "8.1"], ["8.2-3", "8.1-2"],
           ["explain qualitatively, in terms of the Boltzmann distribution and the frequency of effective collisions, the effect of temperature change on reaction rate",
            "explain qualitatively, in terms of collisions, why the rate of a reaction changes"],
           ["describe", "explain"], 4, ["Describe", "Explain"]),
 "2c-i": ("2(c)(i)", "2", "(c)(i)", 2, ["7.1"], ["7.1-6", "7.1-7"],
          ["deduce expressions for equilibrium constants in terms of partial pressures, Kp",
           "use the Kc and Kp expressions to carry out calculations"],
          ["write", "state"], 4, ["Write", "State"]),
 "2c-ii": ("2(c)(ii)", "2", "(c)(ii)", 2, ["7.1"], ["7.1-5", "7.1-7"],
           ["use the terms mole fraction and partial pressure",
            "use the Kc and Kp expressions to carry out calculations"],
           ["calculate"], 4, ["Calculate"]),
 "2c-iii": ("2(c)(iii)", "2", "(c)(iii)", 1, ["7.1"], ["7.1-5", "7.1-7"],
            ["use the terms mole fraction and partial pressure",
             "use the Kc and Kp expressions to carry out calculations"],
            ["calculate"], 4, ["Calculate"]),
 "2d-i": ("2(d)(i)", "2", "(d)(i)", 3, ["12.1"], ["12.1-5", "12.1-4"],
          ["describe the role of NO and NO2 in the formation of acid rain both directly and as catalysts",
           "understand that atmospheric oxides of nitrogen (NO and NO2) can react with oxygen, water and cloud droplets to form acidic solutions"],
          ["construct", "explain"], 4, ["Identify", "Write"]),
 "2d-ii": ("2(d)(ii)", "2", "(d)(ii)", 2, ["12.1"], ["12.1-4"],
           ["understand that atmospheric oxides of nitrogen (NO and NO2) can react with oxygen, water and cloud droplets to form acidic solutions"],
           ["outline"], 3, ["Outline"]),
 "3a": ("3(a)", "3", "(a)", 2, ["5.1"], ["5.1-3b", "5.1-1"],
        ["define and use the term: enthalpy change of formation",
         "understand that chemical reactions are accompanied by enthalpy changes"],
        ["construct"], 3, ["Write"]),
 "3b": ("3(b)", "3", "(b)", 2, ["5.2"], ["5.2-1", "5.2-2b"],
        ["apply Hess's law to construct simple energy cycles",
         "carry out calculations using cycles and relevant energy terms, including enthalpies of formation"],
        ["calculate"], 4, ["Calculate"]),
 "3c-i": ("3(c)(i)", "3", "(c)(i)", 1, ["4.2"], ["4.2-1c", "4.2-3"],
          ["describe, in simple terms, the lattice structure of a giant covalent solid",
           "deduce the type of structure and bonding present in a substance from given information"],
          ["suggest"], 3, ["Suggest"]),
 "3c-ii": ("3(c)(ii)", "3", "(c)(ii)", 2, ["2.2"], ["2.2-1", "1.2-2"],
           ["define and use the term mole in terms of the Avogadro constant",
            "determine the empirical formula of a compound"],
           ["calculate"], 4, ["Calculate"]),
 "4a": ("4(a)", "4", "(a)", 2, ["12.1", "3.4"], ["12.1-2b", "3.4-1a"],
        ["describe and explain the structure of the ammonium ion and its formation",
         "define covalent bonding as electrostatic attraction between the nuclei of two atoms and a shared pair of electrons"],
        ["apply", "construct"], 4, ["Draw"]),
 "4b-i": ("4(b)(i)", "4", "(b)(i)", 1, ["7.2", "12.1"], ["7.2-7", "12.1-2c"],
          ["understand that neutralisation reactions occur when H+(aq) and OH-(aq) form H2O(l)",
           "describe and explain the displacement of ammonia from ammonium salts"],
          ["identify"], 3, ["Identify"]),
 "4b-ii": ("4(b)(ii)", "4", "(b)(ii)", 1, ["12.1"], ["12.1-2c"],
           ["describe and explain the displacement of ammonia from ammonium salts"],
           ["construct"], 3, ["Construct"]),
 "4c-i": ("4(c)(i)", "4", "(c)(i)", 1, ["15.1"], ["15.1-3a"],
          ["describe the nucleophilic substitution reactions of halogenoalkanes"],
          ["name"], 3, ["Name"]),
 "4c-ii": ("4(c)(ii)", "4", "(c)(ii)", 1, ["15.1"], ["15.1-3a", "15.1-7"],
           ["describe the nucleophilic substitution reactions of halogenoalkanes",
            "describe and explain the different reactivities of halogenoalkanes"],
           ["suggest", "explain"], 4, ["Suggest", "Explain"]),
 "4d": ("4(d)", "4", "(d)", 2, ["15.1", "5.1"], ["15.1-5", "8.2-1"],
        ["describe the SN1 and SN2 mechanisms of nucleophilic substitution in halogenoalkanes",
         "define activation energy, EA, as the minimum energy required for a collision to be effective"],
        ["sketch", "apply"], 5, ["Sketch"]),
 "4e-i": ("4(e)(i)", "4", "(e)(i)", 3, ["15.1"], ["15.1-5", "15.1-3b"],
          ["describe the SN1 and SN2 mechanisms of nucleophilic substitution in halogenoalkanes",
           "describe the nucleophilic substitution reaction of halogenoalkanes with ammonia"],
          ["draw", "complete"], 5, ["Complete"]),
 "4e-ii": ("4(e)(ii)", "4", "(e)(ii)", 1, ["15.1"], ["15.1-3b"],
           ["describe the nucleophilic substitution reaction of halogenoalkanes with ammonia"],
           ["identify"], 3, ["Identify"]),
 "4e-iii": ("4(e)(iii)", "4", "(e)(iii)", 1, ["13.2"], ["13.2-2a"],
            ["use terminology associated with nomenclature of organic compounds"],
            ["name"], 3, ["Name"]),
 "4f-i": ("4(f)(i)", "4", "(f)(i)", 1, ["15.1"], ["15.1-5"],
          ["describe the SN1 and SN2 mechanisms of nucleophilic substitution in halogenoalkanes"],
          ["draw"], 4, ["Draw"]),
 "4f-ii": ("4(f)(ii)", "4", "(f)(ii)", 2, ["15.1"], ["15.1-6", "15.1-5"],
           ["recall that tertiary halogenoalkanes tend to react via the SN1 mechanism",
            "describe the SN1 and SN2 mechanisms of nucleophilic substitution in halogenoalkanes"],
           ["explain"], 5, ["Identify", "Explain"]),
 "5a": ("5(a)", "5", "(a)", 1, ["14.2"], ["14.2-2b"],
        ["describe the oxidation of alkenes by cold dilute acidified KMnO4 to form a diol"],
        ["identify"], 4, ["Identify"]),
 "5b-i": ("5(b)(i)", "5", "(b)(i)", 2, ["14.2", "16.1"], ["14.2-2a", "16.1-2b"],
          ["describe the electrophilic addition of bromine to an alkene",
           "describe the substitution of an alcohol to form a halogenoalkane"],
          ["identify"], 4, ["Identify"]),
 "5b-ii": ("5(b)(ii)", "5", "(b)(ii)", 1, ["14.2"], ["14.2-4"],
           ["describe the mechanism of electrophilic addition in alkenes, using bromine/ethene",
            "name the mechanism"],
           ["name"], 3, ["Name"]),
 "5c": ("5(c)", "5", "(c)", 2, ["22.1"], ["22.1-1"],
        ["analyse an infrared spectrum of a simple molecule to identify functional groups"],
        ["analyse", "identify"], 3, ["Add", "Identify"]),
 "5d-i": ("5(d)(i)", "5", "(d)(i)", 1, ["15.1"], ["15.1-1a", "15.1-3b"],
          ["recall the reactions by which halogenoalkanes can be produced",
           "describe the nucleophilic substitution reaction of halogenoalkanes with cyanide ions"],
          ["draw"], 4, ["Draw"]),
 "5d-ii": ("5(d)(ii)", "5", "(d)(ii)", 1, ["18.1"], ["18.1-1b"],
           ["recall the reactions by which carboxylic acids can be produced, including by hydrolysis of nitriles"],
           ["identify"], 4, ["Identify"]),
 "5d-iii": ("5(d)(iii)", "5", "(d)(iii)", 1, ["18.1"], ["18.1-2e"],
            ["describe the reduction by LiAlH4 of a carboxylic acid to form a primary alcohol"],
            ["construct"], 4, ["Complete"]),
 "5d-iv": ("5(d)(iv)", "5", "(d)(iv)", 1, ["18.1", "17.1"], ["18.1-2e", "17.1-2a"],
           ["describe the reduction by LiAlH4 of a carboxylic acid to form a primary alcohol",
            "describe the reduction of aldehydes and ketones using NaBH4 or LiAlH4"],
           ["identify"], 4, ["Identify"]),
}

def main():
    os.makedirs(TAGGED, exist_ok=True)
    for slug, spec in PARTS.items():
        question, parent, part, marks, codes, los, lo_texts, skills, diff = spec[:9]
        command_words = spec[9] if len(spec) > 9 else []
        qid = f"cie-9701-2024-mj-p23-q{slug}"
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
