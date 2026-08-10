#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_m25_qp_12 tagged JSON (MCQ)."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_m25_qp_12/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

# q_n -> (syllabus_codes, learning_outcomes, skills, difficulty, misconceptions)
# skills from ALLOWED_SKILLS: recall, explain, calculate, data-analysis, practical, compare, evaluate, draw, suggest
CUR = {
 1: (["8.2"], ["8.2-2"], ["explain"], 3, ["thinking lower T flattens curve; confusing number of particles at EA"]),
 2: (["2.4"], ["2.4-1a","2.4-1c"], ["calculate"], 4, ["limiting reagent; acid-starved 1:4 mole ratio"]),
 3: (["1.4","9.2"], ["1.4-4"], ["data-analysis"], 4, ["reading big jump in 8th IE to fix group"]),
 4: (["1.1","1.3"], ["1.1-3","1.3-1"], ["recall"], 2, ["confusing proton/electron counts in ion"]),
 5: (["3.5"], ["3.5-1","3.5-2"], ["explain"], 4, ["ordering bond angles around N atoms with lone pairs"]),
 6: (["7.1"], ["7.1-8"], ["calculate"], 4, ["mis-stoichiometry esterification back-titration"]),
 7: (["4.2","9.2"], ["4.2-1c"], ["recall"], 3, ["identifying P ionic vs Q covalent structures"]),
 8: (["4.1"], ["4.1-3"], ["calculate"], 4, ["volume of gas at 100kPa/293K vs m3"]),
 9: (["8.1"], ["8.1-1"], ["calculate"], 4, ["rate in mol/min; converting gas volume to moles"]),
 10: (["7.1"], ["7.1-7"], ["explain"], 3, ["Le Chatelier pressure/steam effect on equilibrium"]),
 11: (["6.1","2.4"], ["6.1-1","2.4-1a"], ["calculate"], 4, ["KClO3 decomposition stoichiometry / Mr"]),
 12: (["5.2"], ["5.2-2b"], ["calculate"], 4, ["q=mcT; per mole NaOH; J vs kJ conversion"]),
 13: (["7.1"], ["7.1-8"], ["calculate"], 4, ["Kc for CO+MeOH->ethanoic acid"]),
 14: (["6.1"], ["6.1-1"], ["calculate"], 5, ["balancing oxidation states; nitrogen oxide state"]),
 15: (["3.4","5.1"], ["5.1-4"], ["explain"], 3, ["bond energy comparison + exothermic sign"]),
 16: (["3.4","13.4","14.1"], ["13.4-1","14.1-1a"], ["explain"], 3, ["pi bond count in propene/HCN/CO2"]),
 17: (["1.4","9.1"], ["9.1-1"], ["data-analysis","recall"], 4, ["deducing Period 3 element from IE data"]),
 18: (["10.1"], ["10.1-2"], ["recall"], 3, ["Group 2 reactions with water/oxygen"]),
 19: (["11.1","11.2"], ["11.2-3"], ["data-analysis"], 4, ["interpreting halogen displacement reaction grid"]),
 20: (["9.2","4.2"], ["9.2-5"], ["recall"], 4, ["distinguishing MgCl2 vs AlCl3 covalency"]),
 21: (["11.3"], ["11.3-2a"], ["explain"], 3, ["identifying ppt-forming ions in river water"]),
 22: (["12.1"], ["12.1-5"], ["recall"], 2, ["atmospheric pollutants identification"]),
 23: (["11.1","11.2"], ["11.2-2"], ["data-analysis"], 3, ["reading Group 17 trend graph"]),
 24: (["2.4","11.2"], ["2.4-1a"], ["calculate"], 4, ["gas from NH4Cl+CaO; amount of gas"]),
 25: (["10.1"], ["10.1-3"], ["recall"], 3, ["nitrate thermal decomposition; identifying the gas"]),
 26: (["2.3","13.4"], ["2.3-3","13.4-1"], ["recall"], 4, ["empirical formula C2H4O; functional group"]),
 27: (["17.1"], ["17.1-3"], ["recall"], 2, ["HCN + propanone nucleophilic addition mechanism"]),
 28: (["14.2"], ["14.2-1a"], ["recall"], 3, ["addition reaction product from C4H8 alkene"]),
 29: (["13.4","18.2"], ["13.4-4"], ["recall"], 3, ["COOH-containing compound G structure"]),
 30: (["16.1","17.1"], ["17.1-5"], ["explain"], 4, ["tests on compound T: carbonyl/oxidation products"]),
 31: (["16.1"], ["16.1-3a","16.1-3b"], ["explain"], 4, ["distinguishing structural isomers by oxidation"]),
 32: (["15.1"], ["15.1-5"], ["recall"], 3, ["halogenoalkane hydrolysis precipitate / hydrolysis"]),
 33: (["16.1","15.1"], ["16.1-2b","15.1-4"], ["recall"], 3, ["converting alcohol to chloropropane via substitution"]),
 34: (["13.1"], ["13.1-2"], ["recall"], 3, ["identifying functional groups in skeletal formulae"]),
 35: (["15.1"], ["15.1-3a"], ["compare"], 4, ["comparing hydrolysis of chlorinated alkanes"]),
 36: (["13.4","16.1","17.1"], ["13.4-3","17.1-6"], ["recall"], 4, ["progesterone structure; ketone/stereochemistry"]),
 37: (["14.1"], ["14.1-6"], ["recall"], 3, ["cracking of hexane products"]),
 38: (["16.1","6.1","18.1"], ["16.1-4","18.1-2c"], ["explain"], 4, ["isomeric dicarboxylic acids oxidation behaviour"]),
 39: (["3.4"], ["3.4-2c"], ["calculate"], 4, ["counting sp3 orbitals in but-2-ene hybridisation"]),
 40: (["22.2"], ["22.2-5"], ["data-analysis"], 5, ["M+1 isotope peak to count carbon atoms"]),
}
n=0
for qn,(codes,los,skills,diff,mis) in CUR.items():
    p=os.path.join(TAGD,f"q{qn}.json")
    obj=json.load(open(p))
    obj["syllabus_codes"]=list(codes)
    obj["topic_titles"]=[CODE_TITLE[c] for c in codes]
    obj["learning_outcomes"]=list(los)
    obj["learning_outcome_texts"]=[LO_TEXT[x] for x in los]
    obj["skills"]=list(skills)
    obj["difficulty"]=diff
    obj["misconceptions"]=list(mis)
    obj["question_type"]="mcq"
    json.dump(obj,open(p,"w"),ensure_ascii=False,indent=2)
    n+=1
print("WROTE",n,"MCQ JSONs")
