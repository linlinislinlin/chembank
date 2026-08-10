#!/usr/bin/env python3
"""Generate tagged/qN.json for draft/9701_s24_qp_11 (Paper 1 MCQ) by hand.

Controlled syllabus_codes + learning_outcomes from
syllabus/cie-9701-as-a-level-chemistry.yaml. ms_answer from MS key.
Assessed-skill tagging (not decorative context).
"""
import json
import os
import re
import sys

import yaml

PAPER_ID = "9701_s24_qp_11"
DRAFT = os.path.join("draft", PAPER_ID)
TAGGED = os.path.join(DRAFT, "tagged")
QP = "raw/papers/9701_s24_qp_11.pdf"
MS = "raw/papers/9701_s24_ms_11.pdf"

# ms_answer from ms_key.json
ms_key = json.load(open(os.path.join(DRAFT, "ms_key.json")))

# (code, titles, lo_ids, lo_texts, skills, difficulty)
TAGS = {
 1: (["2.4"], ["Reacting masses and volumes (of solutions and gases)"], ["2.4-1c"],
     "perform calculations including use of the mole concept... volumes and concentrations of solutions",
     ["calculate"], 3),
 2: (["2.4"], ["Reacting masses and volumes (of solutions and gases)"], ["2.4-1b"],
     "perform calculations including use of the mole concept... volumes of gases",
     ["calculate"], 3),
 3: (["1.4"], ["Ionisation energy"], ["1.4-4"],
     "identify and explain the variation in successive ionisation energies of an element",
     ["data-analysis"], 4),
 4: (["1.1"], ["Particles in the atom and atomic radius"], ["1.1-6"],
     "determine the numbers of protons, neutrons and electrons present in both atoms and ions given atomic or proton number, mass or nucleon number and charge",
     ["recall"], 2),
 5: (["3.4"], ["Covalent bonding and coordinate (dative covalent) bonding"], ["3.4-1c"],
     "describe coordinate (dative covalent) bonding, including in the reaction between ammonia and hydrogen chloride gases to form the ammonium ion",
     ["recall"], 3),
 6: (["3.5"], ["Shapes of molecules"], ["3.5-2"],
     "predict the shapes of, and bond angles in, molecules and ions analogous to those specified in 3.5.1",
     ["recall"], 2),
 7: (["4.1"], ["The gaseous state: ideal and real gases and pV = nRT"], ["4.1-3"],
     "state and use the ideal gas equation pV = nRT in calculations, including in the determination of Mr",
     ["calculate"], 3),
 8: (["3.6"], ["Intermolecular forces, electronegativity and bond properties"], ["3.6-1a"],
     "describe hydrogen bonding, limited to molecules containing N-H and O-H groups, including ammonia and water as simple examples",
     ["explain"], 3),
 9: (["5.2"], ["Hess's law"], ["5.2-1"],
     "apply Hess's law to construct simple energy cycles",
     ["data-analysis"], 4),
 10: (["5.1"], ["Enthalpy change, ΔH"], ["5.1-2"],
      "construct and interpret a reaction pathway diagram, in terms of the enthalpy change of the reaction and of the activation energy",
      ["explain"], 3),
 11: (["6.1"], ["Redox processes: electron transfer and changes in oxidation number (oxidation state)"], ["6.1-1"],
      "calculate oxidation numbers of elements in compounds and ions",
      ["data-analysis"], 3),
 12: (["6.1", "2.4"], ["Redox processes: electron transfer and changes in oxidation number (oxidation state)", "Reacting masses and volumes (of solutions and gases)"],
      ["6.1-3", "2.4-1a"],
      ["explain and use the terms redox, oxidation, reduction and disproportionation in terms of electron transfer and changes in oxidation number",
       "perform calculations including use of the mole concept, involving: reacting masses (from formulas and equations) including percentage yield calculations"],
      ["calculate"], 4),
 13: (["7.1"], ["Chemical equilibria: reversible reactions, dynamic equilibrium"], ["7.1-7"],
      "use the Kc and Kp expressions to carry out calculations",
      ["calculate"], 4),
 14: (["7.1"], ["Chemical equilibria: reversible reactions, dynamic equilibrium"], ["7.1-10"],
      "describe and explain the conditions used in the Haber process and the Contact process, as examples of the importance of an understanding of dynamic equilibrium in the chemical industry and the application of Le Chatelier's principle",
      ["explain"], 3),
 15: (["8.2", "8.3"], ["Effect of temperature on reaction rates and the concept of activation energy", "Homogeneous and heterogeneous catalysts"],
      ["8.2-2", "8.3-1b"],
      ["sketch and use the Boltzmann distribution to explain the significance of activation energy",
       "explain this catalytic effect in terms of the Boltzmann distribution"],
      ["explain"], 3),
 16: (["9.2"], ["Periodicity of chemical properties of the elements in Period 3"], ["9.2-5"],
      "describe, explain, and write equations for, the reactions of the chlorides NaCl, MgCl2, AlCl3, SiCl4, PCl5 with water including the likely pHs of the solutions obtained",
      ["explain"], 4),
 17: (["9.2"], ["Periodicity of chemical properties of the elements in Period 3"], ["9.2-7"],
      "suggest the types of chemical bonding present in the chlorides and oxides from observations of their chemical and physical properties",
      ["data-analysis"], 3),
 18: (["9.1"], ["Periodicity of physical properties of the elements in Period 3"], ["9.1-1"],
      "describe qualitatively (and indicate the periodicity in) the variations in atomic radius, ionic radius, melting point and electrical conductivity of the elements",
      ["compare"], 3),
 19: (["10.1"], ["Similarities and trends in the properties of the Group 2 metals, magnesium to barium, and their compounds"], ["10.1-5"],
      "state the variation in the solubilities of the hydroxides and sulfates",
      ["data-analysis"], 4),
 20: (["2.4", "10.1"], ["Reacting masses and volumes (of solutions and gases)", "Similarities and trends in the properties of the Group 2 metals, magnesium to barium, and their compounds"],
      ["2.4-1b", "10.1-3"],
      ["perform calculations including use of the mole concept, involving: volumes of gases",
       "describe, and write equations for, the thermal decomposition of the nitrates and carbonates, to include the trend in thermal stabilities"],
      ["calculate"], 3),
 21: (["11.3", "11.1"], ["Some reactions of the halide ions", "Physical properties of the Group 17 elements"],
      ["11.3-2b", "11.1-3"],
      ["describe and explain the reactions of halide ions with: concentrated sulfuric acid, to include balanced chemical equations",
       "interpret the volatility of the elements in terms of instantaneous dipole-induced dipole forces"],
      ["explain"], 4),
 22: (["11.3"], ["Some reactions of the halide ions"], ["11.3-2a"],
      "describe and explain the reactions of halide ions with: aqueous silver ions followed by aqueous ammonia",
      ["recall"], 3),
 23: (["12.1"], ["Nitrogen and sulfur"], ["12.1-5"],
      "describe the role of NO and NO2 in the formation of acid rain both directly and in their catalytic role in the oxidation of atmospheric sulfur dioxide",
      ["recall"], 3),
 24: (["3.5"], ["Shapes of molecules"], ["3.5-1"],
      "state and explain the shapes of, and bond angles in, molecules by using VSEPR theory, including as simple examples: NH3 (pyramidal, 107°)",
      ["recall"], 2),
 25: (["13.4"], ["Isomerism: structural isomerism and stereoisomerism"], ["13.4-2"],
      "describe stereoisomerism and its division into geometrical (cis/trans) and optical isomerism",
      ["data-analysis"], 5),
 26: (["13.3", "3.4"], ["Shapes of organic molecules; σ and π bonds", "Covalent bonding and coordinate (dative covalent) bonding"],
      ["13.3-2", "3.4-2c"],
      ["describe and explain the shape of, and bond angles in, molecules containing sp, sp2 and sp3 hybridised atoms",
       "use the concept of hybridisation to describe sp, sp2 and sp3 orbitals"],
      ["recall"], 4),
 27: (["13.1"], ["Formulas, functional groups and the naming of organic compounds"], ["13.1-6"],
      "deduce the molecular and/or empirical formula of a compound, given its structural, displayed or skeletal formula",
      ["recall"], 3),
 28: (["14.1"], ["Alkanes"], ["14.1-2b"],
      "describe: the free-radical substitution of alkanes by Cl2 or Br2 in the presence of ultraviolet light, as exemplified by the reactions of ethane",
      ["recall"], 3),
 29: (["14.2"], ["Alkenes"], ["14.2-2b"],
      "describe the following reactions of alkenes: the oxidation by cold dilute acidified KMnO4 to form the diol",
      ["recall"], 3),
 30: (["15.1"], ["Halogenoalkanes"], ["15.1-5"],
      "describe the SN1 and SN2 mechanisms of nucleophilic substitution in halogenoalkanes including the inductive effects of alkyl groups",
      ["explain"], 4),
 31: (["15.1", "14.2"], ["Halogenoalkanes", "Alkenes"],
      ["15.1-4", "14.2-2a"],
      ["describe the elimination reaction with NaOH in ethanol and heat to produce an alkene as exemplified by bromoethane",
       "describe the following reactions of alkenes: the electrophilic addition of a halogen, X2"],
      ["recall"], 4),
 32: (["16.1", "13.4"], ["Alcohols", "Isomerism: structural isomerism and stereoisomerism"],
      ["16.1-2e", "13.4-4"],
      ["describe: dehydration to an alkene, by using a heated catalyst, e.g. Al2O3 or a concentrated acid",
       "explain what is meant by a chiral centre and that such a centre gives rise to two optical isomers (enantiomers)"],
      ["recall"], 4),
 33: (["16.1"], ["Alcohols"], ["16.1-2b"],
      "describe: substitution to form halogenoalkanes, e.g. by reaction with HX(g); or with KCl and concentrated H2SO4",
      ["recall"], 3),
 34: (["17.1", "13.4"], ["Aldehydes and ketones", "Isomerism: structural isomerism and stereoisomerism"],
      ["17.1-2a", "13.4-6"],
      ["describe: the reduction of aldehydes and ketones using NaBH4 or LiAlH4 to produce alcohols",
       "deduce the possible isomers for an organic molecule of known molecular formula"],
      ["data-analysis"], 5),
 35: (["17.1"], ["Aldehydes and ketones"], ["17.1-5"],
      "deduce the nature (aldehyde or ketone) of an unknown carbonyl compound from the results of simple tests (Fehling's and Tollens' reagents; ease of oxidation)",
      ["data-analysis"], 4),
 36: (["17.1", "19.2"], ["Aldehydes and ketones", "Nitriles and hydroxynitriles"],
      ["17.1-2b", "19.2-3"],
      ["describe: the reaction of aldehydes and ketones with HCN, KCN as catalyst, and heat to produce hydroxynitriles",
       "describe the hydrolysis of nitriles with dilute acid or dilute alkali followed by acidification to produce a carboxylic acid"],
      ["recall"], 4),
 37: (["18.1"], ["Carboxylic acids"], ["18.1-2e"],
      "describe: reduction by LiAlH4 to form a primary alcohol",
      ["recall"], 4),
 38: (["18.2"], ["Esters"], ["18.2-2"],
      "describe the hydrolysis of esters by dilute acid and by dilute alkali and heat",
      ["recall"], 3),
 39: (["20.1"], ["Addition polymerisation"], ["20.1-3"],
      "identify the monomer(s) present in a given section of an addition polymer molecule",
      ["recall"], 4),
 40: (["2.1", "22.2"], ["Relative masses of atoms and molecules", "Mass spectrometry"],
      ["2.1-2", "22.2-2"],
      ["define relative atomic mass, Ar, relative isotopic mass, relative molecular mass, Mr, and relative formula mass in terms of the unified atomic mass unit",
       "calculate the relative atomic mass of an element given the relative abundances of its isotopes, or its mass spectrum"],
      ["calculate"], 3),
}

LEV = {"level": "AS", "session": "MJ", "year": 2024, "paper": 11}


def main():
    os.makedirs(TAGGED, exist_ok=True)
    for q in range(1, 41):
        qs = str(q)
        codes, titles, los, lo_texts, skills, diff = TAGS[q]
        body = open(os.path.join(DRAFT, f"q{q}.txt")).read().strip()
        # trim trailing MARK SCHEME section
        if "\n--- MARK SCHEME ---" in body:
            body = body.split("\n--- MARK SCHEME ---")[0].strip()
        ans = ms_key[qs]
        qid = f"cie-9701-2024-mj-p11-q{q}"
        rec = {
            "id": qid,
            "exam_board": "CIE",
            "syllabus_code": "9701",
            "level": LEV["level"],
            "year": LEV["year"],
            "session": LEV["session"],
            "paper": LEV["paper"],
            "question": qs,
            "marks": 1,
            "syllabus_codes": codes,
            "topic_titles": titles,
            "skills": skills,
            "question_type": "mcq",
            "difficulty": diff,
            "command_words": [],
            "misconceptions": [],
            "learning_outcomes": los,
            "learning_outcome_texts": lo_texts if isinstance(lo_texts, list) else [lo_texts],
            "learning_objectives": [],
            "ms_answer": ans,
            "source_qp": QP,
            "source_ms": MS,
            "page_qp": None,
            "body": body,
            "mark_scheme": f"Answer: **{ans}**",
            "figures": [f"assets/{qid}-paper.png"],
        }
        with open(os.path.join(TAGGED, f"q{q}.json"), "w") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(TAGS)} tagged JSON files to {TAGGED}")

    # validate LOs against syllabus
    syl = yaml.safe_load(open("syllabus/cie-9701-as-a-level-chemistry.yaml"))
    valid_codes = set()
    valid_los = set()
    for t in syl["topics"]:
        valid_codes.add(str(t["code"]))
        for st in t["subtopics"]:
            valid_codes.add(str(st["code"]))
            for lo in st["learning_outcomes"]:
                valid_los.add(str(lo["id"]))
    bad = []
    for qs, (codes, _, los, *_ ) in TAGS.items():
        for c in codes:
            if c not in valid_codes:
                bad.append((qs, "code", c))
        for lo in los:
            if lo not in valid_los:
                bad.append((qs, "lo", lo))
    if bad:
        print("INVALID TAGS:", bad)
        sys.exit(1)
    print("Validation OK: all codes + LOs are in the controlled vocabulary.")


if __name__ == "__main__":
    main()
