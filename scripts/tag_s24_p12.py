#!/usr/bin/env python3
"""Generate tagged/qN.json for draft/9701_s24_qp_12 (Paper 1 MCQ) by hand."""
import json
import os
import sys

import yaml

PAPER_ID = "9701_s24_qp_12"
DRAFT = os.path.join("draft", PAPER_ID)
TAGGED = os.path.join(DRAFT, "tagged")
QP = "raw/papers/9701_s24_qp_12.pdf"
MS = "raw/papers/9701_s24_ms_12.pdf"

ms_key = json.load(open(os.path.join(DRAFT, "ms_key.json")))

# (code, titles, lo_ids, lo_texts, skills, difficulty)
TAGS = {
 1: (["2.3"], ["Formulae"], ["2.3-1a"],
    "write formulas of ionic compounds from ionic charges and oxidation numbers: the prediction of ionic charge from the position of an element in the Periodic Table",
    ["recall"], 3),
 2: (["2.2"], ["The mole and the Avogadro constant"], ["2.2-1"],
    "define and use the term mole in terms of the Avogadro constant",
    ["calculate"], 2),
 3: (["1.4"], ["Ionisation energy"], ["1.4-7"],
    "deduce the electronic configurations of elements using successive ionisation energy data",
    ["data-analysis"], 4),
 4: (["1.3"], ["Electrons, energy levels and atomic orbitals"], ["1.3-9"],
    "describe a free radical as a species with one or more unpaired electrons",
    ["recall"], 3),
 5: (["3.5"], ["Shapes of molecules"], ["3.5-2"],
    "predict the shapes of, and bond angles in, molecules and ions analogous to those specified in 3.5.1",
    ["recall"], 3),
 6: (["3.4"], ["Covalent bonding and coordinate (dative covalent) bonding"], ["3.4-1b"],
    "understand that elements in period 3 can expand their octet including in the compounds sulfur dioxide, SO2, phosphorus pentachloride, PCl5, and sulfur hexafluoride, SF6",
    ["recall"], 3),
 7: (["4.1"], ["The gaseous state: ideal and real gases and pV = nRT"], ["4.1-3"],
    "state and use the ideal gas equation pV = nRT in calculations, including in the determination of Mr",
    ["calculate"], 3),
 8: (["3.6"], ["Intermolecular forces, electronegativity and bond properties"], ["3.6-3b"],
    "describe the types of van der Waals' forces: instantaneous dipole-induced dipole forces, also called London dispersion forces; permanent dipole-permanent dipole forces, including hydrogen bonding",
    ["compare"], 4),
 9: (["5.1"], ["Enthalpy change, ΔH"], ["5.1-5"],
    "use bond energies (ΔH positive, i.e. bond breaking) to calculate enthalpy change of reaction, ΔHr",
    ["calculate"], 3),
 10: (["5.1"], ["Enthalpy change, ΔH"], ["5.1-3b"],
     "define and use the terms: enthalpy change with particular reference to: reaction, ΔHr, formation, ΔHf, combustion, ΔHc, neutralisation, ΔHneut",
     ["recall"], 3),
 11: (["6.1"], ["Redox processes: electron transfer and changes in oxidation number (oxidation state)"], ["6.1-3"],
     "explain and use the terms redox, oxidation, reduction and disproportionation in terms of electron transfer and changes in oxidation number",
     ["explain"], 3),
 12: (["6.1"], ["Redox processes: electron transfer and changes in oxidation number (oxidation state)"], ["6.1-2"],
     "use changes in oxidation numbers to help balance chemical equations",
     ["calculate"], 4),
 13: (["7.1"], ["Chemical equilibria: reversible reactions, dynamic equilibrium"], ["7.1-10"],
     "describe and explain the conditions used in the Haber process and the Contact process, as examples of the importance of an understanding of dynamic equilibrium in the chemical industry",
     ["explain"], 4),
 14: (["7.1"], ["Chemical equilibria: reversible reactions, dynamic equilibrium"], ["7.1-6"],
     "deduce expressions for equilibrium constants in terms of partial pressures, Kp",
     ["recall"], 3),
 15: (["8.3"], ["Homogeneous and heterogeneous catalysts"], ["8.3-1b"],
     "explain this catalytic effect in terms of the Boltzmann distribution",
     ["explain"], 3),
 16: (["9.2"], ["Periodicity of chemical properties of the elements in Period 3"], ["9.2-5"],
     "describe, explain, and write equations for, the reactions of the chlorides NaCl, MgCl2, AlCl3, SiCl4, PCl5 with water including the likely pHs of the solutions obtained",
     ["recall"], 3),
 17: (["10.1"], ["Similarities and trends in the properties of the Group 2 metals, magnesium to barium, and their compounds"], ["10.1-3"],
     "describe, and write equations for, the thermal decomposition of the nitrates and carbonates, to include the trend in thermal stabilities",
     ["recall"], 3),
 18: (["9.2"], ["Periodicity of chemical properties of the elements in Period 3"], ["9.2-4"],
     "describe, explain, and write equations for, the acid / base behaviour of the oxides Na2O, MgO, Al2O3, P4O10, SO2 and SO3 and the hydroxides NaOH, Mg(OH)2 and Al(OH)3",
     ["explain"], 4),
 19: (["11.4"], ["The reactions of chlorine"], ["11.4-1"],
     "describe and interpret, in terms of changes in oxidation number, the reaction of chlorine with cold and with hot aqueous sodium hydroxide and recognise these as disproportionation reactions",
     ["explain"], 3),
 20: (["9.2"], ["Periodicity of chemical properties of the elements in Period 3"], ["9.2-4"],
     "describe, explain, and write equations for, the acid / base behaviour of the oxides Na2O, MgO, Al2O3, P4O10, SO2 and SO3 and the hydroxides NaOH, Mg(OH)2 and Al(OH)3",
     ["explain"], 4),
 21: (["11.2", "11.3"], ["The chemical properties of the halogen elements and the hydrogen halides", "Some reactions of the halide ions"],
     ["11.2-1", "11.3-2b"],
     ["describe the relative reactivity of the elements as oxidising agents",
      "describe and explain the reactions of halide ions with: concentrated sulfuric acid, to include balanced chemical equations"],
     ["explain"], 4),
 22: (["12.1"], ["Nitrogen and sulfur"], ["12.1-2b"],
     "describe and explain: the structure of the ammonium ion and its formation by an acid-base reaction",
     ["recall"], 3),
 23: (["12.1"], ["Nitrogen and sulfur"], ["12.1-3"],
     "state and explain the natural and man-made occurrences of oxides of nitrogen and their catalytic removal from the exhaust gases of internal combustion engines",
     ["recall"], 3),
 24: (["13.1"], ["Formulas, functional groups and the naming of organic compounds"], ["13.1-3"],
     "understand that the compounds in the table contain a functional group which dictates their physical and chemical properties",
     ["compare"], 3),
 25: (["9.1"], ["Periodicity of physical properties of the elements in Period 3"], ["9.1-1"],
     "describe qualitatively (and indicate the periodicity in) the variations in atomic radius, ionic radius, melting point and electrical conductivity of the elements",
     ["compare"], 3),
 26: (["2.4", "14.2"], ["Reacting masses and volumes (of solutions and gases)", "Alkenes"],
     ["2.4-1b", "14.2-2c"],
     ["perform calculations including use of the mole concept, involving: volumes of gases",
      "describe the following reactions of alkenes: the oxidation by hot concentrated acidified KMnO4 leading to the rupture of the carbon-carbon double bond and the identities of the subsequent products"],
     ["calculate"], 4),
 27: (["16.1"], ["Alcohols"], ["16.1-2d"],
     "describe: oxidation with acidified K2Cr2O7 or acidified KMnO4 to: carbonyl compounds by distillation; carboxylic acids by refluxing",
     ["recall"], 3),
 28: (["15.1"], ["Halogenoalkanes"], ["15.1-5"],
     "describe the SN1 and SN2 mechanisms of nucleophilic substitution in halogenoalkanes including the inductive effects of alkyl groups",
     ["explain"], 4),
 29: (["17.1"], ["Aldehydes and ketones"], ["17.1-1a"],
     "recall the reactions (reagents and conditions) by which aldehydes and ketones can be produced: the oxidation of primary alcohols using acidified K2Cr2O7 or acidified KMnO4 and distillation to produce aldehydes",
     ["recall"], 3),
 30: (["16.1"], ["Alcohols"], ["16.1-2c"],
     "describe: the reaction with Na(s)",
     ["explain"], 4),
 31: (["16.1"], ["Alcohols"], ["16.1-3b"],
     "state characteristic distinguishing reactions, e.g. mild oxidation with acidified K2Cr2O7, colour change from orange to green",
     ["data-analysis"], 4),
 32: (["13.4"], ["Isomerism: structural isomerism and stereoisomerism"], ["13.4-1"],
     "describe structural isomerism and its division into chain, positional and functional group isomerism",
     ["recall"], 3),
 33: (["13.1", "13.3"], ["Formulas, functional groups and the naming of organic compounds", "Shapes of organic molecules; σ and π bonds"],
     ["13.1-3", "13.3-3"],
     ["understand that the compounds in the table contain a functional group which dictates their physical and chemical properties",
      "describe the arrangement of σ and π bonds in molecules containing sp, sp2 and sp3 hybridised atoms"],
     ["recall"], 4),
 34: (["2.4", "14.2"], ["Reacting masses and volumes (of solutions and gases)", "Alkenes"],
     ["2.4-1b", "14.2-2a"],
     ["perform calculations including use of the mole concept, involving: volumes of gases",
      "describe the following reactions of alkenes: the electrophilic addition of hydrogen in a hydrogenation reaction, H2(g) and Pt/Ni catalyst and heat"],
     ["calculate"], 4),
 35: (["15.1"], ["Halogenoalkanes"], ["15.1-4"],
     "describe the elimination reaction with NaOH in ethanol and heat to produce an alkene as exemplified by bromoethane",
     ["recall"], 3),
 36: (["13.4"], ["Isomerism: structural isomerism and stereoisomerism"], ["13.4-5"],
     "identify chiral centres and geometrical (cis/trans) isomerism in a molecule of given structural formula including cyclic compounds",
     ["data-analysis"], 4),
 37: (["17.1", "13.4"], ["Aldehydes and ketones", "Isomerism: structural isomerism and stereoisomerism"],
     ["17.1-2b", "13.4-4"],
     ["describe: the reaction of aldehydes and ketones with HCN, KCN as catalyst, and heat to produce hydroxynitriles",
      "explain what is meant by a chiral centre and that such a centre gives rise to two optical isomers (enantiomers)"],
     ["explain"], 4),
 38: (["18.2"], ["Esters"], ["18.2-2"],
     "describe the hydrolysis of esters by dilute acid and by dilute alkali and heat",
     ["recall"], 3),
 39: (["20.1"], ["Addition polymerisation"], ["20.1-2"],
     "deduce the repeat unit of an addition polymer obtained from a given monomer",
     ["recall"], 3),
 40: (["22.1"], ["Infrared spectroscopy"], ["22.1-1"],
     "analyse an infrared spectrum of a simple molecule to identify functional groups",
     ["data-analysis"], 3),
}

LEV = {"level": "AS", "session": "MJ", "year": 2024, "paper": 12}


def main():
    os.makedirs(TAGGED, exist_ok=True)
    for q in range(1, 41):
        qs = str(q)
        codes, titles, los, lo_texts, skills, diff = TAGS[q]
        body = open(os.path.join(DRAFT, f"q{q}.txt")).read().strip()
        if "\n--- MARK SCHEME ---" in body:
            body = body.split("\n--- MARK SCHEME ---")[0].strip()
        # drop footer noise (periodic table / constants) for the last question
        for marker in ["Important values, constants and standards", "The Periodic Table of Elements Group"]:
            if marker in body:
                body = body.split(marker)[0].strip()
        ans = ms_key[qs]
        qid = f"cie-9701-2024-mj-p12-q{q}"
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

    syl = yaml.safe_load(open("syllabus/cie-9701-as-a-level-chemistry.yaml"))
    valid_codes, valid_los = set(), set()
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
