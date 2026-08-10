#!/usr/bin/env python3
"""Generate tagged/qN.json for draft/9701_s24_qp_13 (Paper 1 MCQ) by hand."""
import json
import os
import sys

import yaml

PAPER_ID = "9701_s24_qp_13"
DRAFT = os.path.join("draft", PAPER_ID)
TAGGED = os.path.join(DRAFT, "tagged")
QP = "raw/papers/9701_s24_qp_13.pdf"
MS = "raw/papers/9701_s24_ms_13.pdf"

ms_key = json.load(open(os.path.join(DRAFT, "ms_key.json")))

# (code, titles, lo_ids, lo_texts, skills, difficulty)
TAGS = {
 1: (["2.4", "10.1"], ["Reacting masses and volumes (of solutions and gases)", "Similarities and trends in the properties of the Group 2 metals, magnesium to barium, and their compounds"],
    ["2.4-1a", "2.4-1e", "10.1-2"],
    ["perform calculations including use of the mole concept, involving: reacting masses",
     "deduce stoichiometric relationships from the data given",
     "describe, and write equations for, the reactions of the oxides, hydroxides and carbonates with water and dilute hydrochloric acid"],
    ["calculate"], 4),
 2: (["2.2", "2.4"], ["The mole and the Avogadro constant", "Reacting masses and volumes (of solutions and gases)"],
    ["2.2-1", "2.4-1a"],
    ["define and use the term mole in terms of the Avogadro constant",
     "perform calculations including use of the mole concept, involving: reacting masses"],
    ["calculate"], 4),
 3: (["1.1", "2.1"], ["Particles in the atom and atomic radius", "Relative masses of atoms and molecules"],
    ["1.1-2", "1.1-6"],
    ["identify and describe protons, neutrons and electrons in terms of their relative charges and relative masses",
     "determine the numbers of protons, neutrons and electrons present in both atoms and ions given atomic or proton number, mass or nucleon number and charge"],
    ["calculate"], 3),
 4: (["1.4", "1.3"], ["Ionisation energy", "Electrons, energy levels and atomic orbitals"],
    ["1.4-3", "1.3-3"],
    ["identify and explain the trends in ionisation energies across a period and down a group of the Periodic Table",
     "describe the electronic configuration of atoms and ions of the first 36 elements"],
    ["data-analysis"], 3),
 5: (["3.5"], ["Shapes of molecules"], ["3.5-2"],
    "predict the shapes of, and bond angles in, molecules and ions analogous to those specified in 3.5.1",
    ["recall"], 4),
 6: (["3.5"], ["Shapes of molecules"], ["3.5-2"],
    "predict the shapes of, and bond angles in, molecules and ions analogous to those specified in 3.5.1",
    ["recall"], 4),
 7: (["4.1"], ["The gaseous state: ideal and real gases and pV = nRT"], ["4.1-3"],
    "state and use the ideal gas equation pV = nRT in calculations, including in the determination of Mr",
    ["calculate"], 3),
 8: (["9.1", "4.2", "3.1"], ["Periodicity of physical properties of the elements in Period 3", "Bonding and structure", "Metallic bonding"],
    ["9.1-1", "4.2-2", "3.1-3"],
    ["describe qualitatively (and indicate the periodicity in) the variations in atomic radius, ionic radius, melting point and electrical conductivity of the elements",
     "describe, interpret and predict the effect of different types of structure and bonding on the physical properties of substances",
     "describe and explain the electrical conductivity of metals"],
    ["compare"], 4),
 9: (["5.1"], ["Enthalpy change, ΔH"], ["5.1-7", "5.1-3b"],
    ["calculate enthalpy changes from appropriate experimental results, including the use of the relationships q = mcΔT",
     "define and use the terms: enthalpy change with particular reference to: reaction, ΔHr, formation, ΔHf, combustion, ΔHc, neutralisation, ΔHneut"],
    ["calculate"], 4),
 10: (["5.1", "8.2"], ["Enthalpy change, ΔH", "Effect of temperature on reaction rates and the concept of activation energy"],
     ["5.1-2", "8.2-1"],
     ["construct and interpret a reaction pathway diagram, in terms of the enthalpy change of the reaction and of the activation energy",
      "define activation energy, EA, as the minimum energy required for a collision to be effective"],
     ["data-analysis"], 5),
 11: (["6.1"], ["Redox processes: electron transfer and changes in oxidation number (oxidation state)"], ["6.1-1"],
     "calculate oxidation numbers of elements in compounds and ions",
     ["calculate"], 4),
 12: (["7.1"], ["Chemical equilibria: reversible reactions, dynamic equilibrium"], ["7.1-10"],
     "describe and explain the conditions used in the Haber process and the Contact process, as examples of the importance of an understanding of dynamic equilibrium in the chemical industry",
     ["explain"], 3),
 13: (["6.1", "2.4"], ["Redox processes: electron transfer and changes in oxidation number (oxidation state)", "Reacting masses and volumes (of solutions and gases)"],
     ["6.1-2", "2.4-1e"],
     ["use changes in oxidation numbers to help balance chemical equations",
      "deduce stoichiometric relationships from the data given"],
     ["calculate"], 4),
 14: (["7.2"], ["Equilibrium constants, Kc and Kp"], ["7.2-2"],
     "deduce expressions for Kp and Kc from a balanced equation",
     ["calculate"], 4),
 15: (["8.2"], ["Effect of temperature on reaction rates and the concept of activation energy"], ["8.2-3", "8.2-2"],
     "explain qualitatively, in terms both of the Boltzmann distribution and of frequency of effective collisions, the effect of temperature changes on reaction rate",
     ["data-analysis"], 3),
 16: (["9.2", "9.1"], ["Periodicity of chemical properties of the elements in Period 3", "Periodicity of physical properties of the elements in Period 3"],
     ["9.2-4", "9.1-1"],
     ["describe, explain, and write equations for, the acid / base behaviour of the oxides Na2O, MgO, Al2O3, P4O10, SO2 and SO3 and the hydroxides NaOH, Mg(OH)2 and Al(OH)3",
      "describe qualitatively (and indicate the periodicity in) the variations in atomic radius, ionic radius, melting point and electrical conductivity of the elements"],
     ["explain"], 4),
 17: (["9.2"], ["Periodicity of chemical properties of the elements in Period 3"], ["9.2-5"],
     "describe, explain, and write equations for, the reactions of the chlorides NaCl, MgCl2, AlCl3, SiCl4, PCl5 with water including the likely pHs of the solutions obtained",
     ["explain"], 3),
 18: (["9.1", "9.2"], ["Periodicity of physical properties of the elements in Period 3", "Periodicity of chemical properties of the elements in Period 3"],
     ["9.1-2", "9.2-1"],
     ["explain the variation in melting point and electrical conductivity in terms of the structure and bonding of the period 3 elements",
      "describe, and write equations for, the reactions of the elements with oxygen"],
     ["recall"], 4),
 19: (["10.1", "2.4"], ["Similarities and trends in the properties of the Group 2 metals, magnesium to barium, and their compounds", "Reacting masses and volumes (of solutions and gases)"],
     ["10.1-3", "2.4-1a"],
     ["describe, and write equations for, the thermal decomposition of the nitrates and carbonates, to include the trend in thermal stabilities",
      "perform calculations including use of the mole concept, involving: reacting masses"],
     ["calculate"], 3),
 20: (["10.1"], ["Similarities and trends in the properties of the Group 2 metals, magnesium to barium, and their compounds"], ["10.1-1", "10.1-4"],
     ["describe, and write equations for, the reactions of the elements with oxygen, water and dilute hydrochloric acid",
      "describe, and make predictions from, the trends in physical and chemical properties of the elements involved in these reactions"],
     ["recall"], 3),
 21: (["11.2", "11.3"], ["The chemical properties of the halogen elements and the hydrogen halides", "Some reactions of the halide ions"],
     ["11.2-3", "11.3-2a", "11.3-2b"],
     ["describe the relative thermal stabilities of the hydrogen halides and explain these in terms of bond strengths",
      "describe and explain the reactions of halide ions with: aqueous silver ions followed by aqueous ammonia",
      "describe and explain the reactions of halide ions with: concentrated sulfuric acid, to include balanced chemical equations"],
     ["explain"], 4),
 22: (["11.4", "6.1"], ["The reactions of chlorine", "Redox processes: electron transfer and changes in oxidation number (oxidation state)"],
     ["11.4-1", "6.1-1"],
     ["describe and interpret, in terms of changes in oxidation number, the reaction of chlorine with cold and with hot aqueous sodium hydroxide and recognise these as disproportionation reactions",
      "calculate oxidation numbers of elements in compounds and ions"],
     ["calculate"], 4),
 23: (["12.1", "6.1"], ["Nitrogen and sulfur", "Redox processes: electron transfer and changes in oxidation number (oxidation state)"],
     ["12.1-2b", "12.1-2a", "6.1-1"],
     ["describe and explain: the structure of the ammonium ion and its formation by an acid-base reaction",
      "describe and explain: the basicity of ammonia, using the Brønsted-Lowry theory",
      "calculate oxidation numbers of elements in compounds and ions"],
     ["recall"], 4),
 24: (["12.1", "2.4"], ["Nitrogen and sulfur", "Reacting masses and volumes (of solutions and gases)"],
     ["12.1-3", "2.4-1e"],
     ["state and explain the natural and man-made occurrences of oxides of nitrogen and their catalytic removal from the exhaust gases of internal combustion engines",
      "deduce stoichiometric relationships from the data given"],
     ["calculate"], 4),
 25: (["13.4"], ["Isomerism: structural isomerism and stereoisomerism"], ["13.4-2", "13.4-3"],
     ["describe stereoisomerism and its division into geometrical (cis/trans) and optical isomerism",
      "describe geometrical (cis/trans) isomerism in alkenes, and explain its origin in terms of restricted rotation about the C=C bond"],
     ["recall"], 3),
 26: (["14.2", "2.4"], ["Alkenes", "Reacting masses and volumes (of solutions and gases)"],
     ["14.2-2c", "2.4-1a"],
     ["describe the reactions of alkenes: the oxidation by hot concentrated acidified KMnO4 leading to the rupture of the carbon-carbon double bond",
      "perform calculations including use of the mole concept, involving: reacting masses"],
     ["recall"], 4),
 27: (["15.1", "13.4"], ["Halogenoalkanes", "Isomerism: structural isomerism and stereoisomerism"],
     ["15.1-1a", "13.4-6"],
     ["recall the reactions by which halogenoalkanes can be produced: the free-radical substitution of an alkane",
      "deduce the possible isomers for an organic molecule of known molecular formula"],
     ["recall"], 4),
 28: (["15.1"], ["Halogenoalkanes"], ["15.1-5"],
     "describe the SN1 and SN2 mechanisms of nucleophilic substitution in halogenoalkanes including the inductive effects of alkyl groups",
     ["explain"], 3),
 29: (["14.2", "16.1"], ["Alkenes", "Alcohols"],
     ["14.2-2b", "14.2-2c", "16.1-2d"],
     ["describe the reactions of alkenes: the oxidation by cold dilute acidified KMnO4 to form the diol",
      "describe the reactions of alkenes: the oxidation by hot concentrated acidified KMnO4 leading to the rupture of the carbon-carbon double bond",
      "describe: oxidation with acidified K2Cr2O7 or acidified KMnO4 to: carbonyl compounds by distillation; carboxylic acids by refluxing"],
     ["recall"], 4),
 30: (["15.1"], ["Halogenoalkanes"], ["15.1-4"],
     "describe the elimination reaction with NaOH in ethanol and heat to produce an alkene as exemplified by bromoethane",
     ["recall"], 3),
 31: (["15.1", "18.1"], ["Halogenoalkanes", "Carboxylic acids"],
     ["15.1-3b", "18.1-1b"],
     ["describe the following nucleophilic substitution reactions: the reaction with KCN in ethanol and heat to produce nitriles",
      "recall the reactions by which carboxylic acids can be produced: hydrolysis of nitriles with dilute acid or dilute alkali"],
     ["explain"], 4),
 32: (["16.1", "17.1"], ["Alcohols", "Aldehydes and ketones"],
     ["16.1-4", "17.1-6"],
     ["deduce the presence of a CH3CH(OH)- group in an alcohol, CH3CH(OH)-R, from its reaction with alkaline iodine, I2(aq)",
      "deduce the presence of a CH3CO- group in an aldehyde or ketone, CH3CO-R, from its reaction with alkaline iodine, I2(aq)"],
     ["recall"], 3),
 33: (["16.1", "18.2"], ["Alcohols", "Esters"],
     ["16.1-2d", "18.2-1a"],
     ["describe: oxidation with acidified K2Cr2O7 or acidified KMnO4 to: carbonyl compounds by distillation; carboxylic acids by refluxing",
      "recall the reaction (reagents and conditions) by which esters can be produced: the condensation reaction between alcohols and carboxylic acids"],
     ["explain"], 5),
 34: (["17.1"], ["Aldehydes and ketones"], ["17.1-4", "17.1-5"],
     ["describe the use of 2,4-dinitrophenylhydrazine (2,4-DNPH reagent) to detect the presence of the carbonyl group",
      "deduce the nature (aldehyde or ketone) of an unknown carbonyl compound from the results of the tests described in 17.1.4"],
     ["recall"], 3),
 35: (["18.1", "18.2"], ["Carboxylic acids", "Esters"],
     ["18.1-2a", "18.1-2c", "18.2-1a"],
     ["describe: the redox reaction with reactive metals to produce a salt and H2(g)",
      "describe: the acid-base reaction with carbonates to produce a salt and H2O(l) and CO2(g)",
      "recall the reaction (reagents and conditions) by which esters can be produced: the condensation reaction between alcohols and carboxylic acids"],
     ["calculate"], 4),
 36: (["18.2"], ["Esters"], ["18.2-2"],
     "describe the hydrolysis of esters by dilute acid and by dilute alkali and heat",
     ["calculate"], 4),
 37: (["20.1"], ["Addition polymerisation"], ["20.1-1", "20.1-3"],
     ["describe addition polymerisation as exemplified by poly(ethene) and poly(chloroethene), PVC",
      "identify the monomer(s) present in a given section of an addition polymer molecule"],
     ["recall"], 3),
 38: (["17.1", "13.4"], ["Aldehydes and ketones", "Isomerism: structural isomerism and stereoisomerism"],
     ["17.1-2a", "17.1-2b", "13.4-4"],
     ["describe: the reduction of aldehydes and ketones using NaBH4 or LiAlH4 to produce alcohols",
      "describe: the reaction of aldehydes and ketones with HCN, KCN as catalyst, and heat to produce hydroxynitriles",
      "explain what is meant by a chiral centre and that such a centre gives rise to two optical isomers (enantiomers)"],
     ["explain"], 4),
 39: (["2.4", "17.1"], ["Reacting masses and volumes (of solutions and gases)", "Aldehydes and ketones"],
     ["2.4-1b", "17.1-4", "17.1-6"],
     ["perform calculations including use of the mole concept, involving: volumes of gases",
      "describe the use of 2,4-dinitrophenylhydrazine (2,4-DNPH reagent) to detect the presence of the carbonyl group",
      "deduce the presence of a CH3CO- group in an aldehyde or ketone, CH3CO-R, from its reaction with alkaline iodine, I2(aq)"],
     ["calculate"], 5),
 40: (["22.1"], ["Infrared spectroscopy"], ["22.1-1"],
     "analyse an infrared spectrum of a simple molecule to identify functional groups",
     ["data-analysis"], 3),
}

LEV = {"level": "AS", "session": "MJ", "year": 2024, "paper": 13}


def main():
    os.makedirs(TAGGED, exist_ok=True)
    for q in range(1, 41):
        qs = str(q)
        codes, titles, los, lo_texts, skills, diff = TAGS[q]
        body = open(os.path.join(DRAFT, f"q{q}.txt")).read().strip()
        if "\n--- MARK SCHEME ---" in body:
            body = body.split("\n--- MARK SCHEME ---")[0].strip()
        for marker in ["Important values, constants and standards", "The Periodic Table of Elements Group"]:
            if marker in body:
                body = body.split(marker)[0].strip()
        ans = ms_key[qs]
        qid = f"cie-9701-2024-mj-p13-q{q}"
        os.makedirs(TAGGED, exist_ok=True)
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
