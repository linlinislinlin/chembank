#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_w25_qp_14 tagged JSON (MCQ)."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_w25_qp_14/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

CUR = {
 1: (["1.3"], ["1.3-3"], ["recall"], 2, ["He3 2 ion: nucleus/proton/neutron/electron counts"]),
 2: (["1.3"], ["1.3-2"], ["recall"], 2, ["isotopic notation neutrons"]),
 3: (["1.3"], ["1.3-3"], ["recall"], 2, ["electron count in ion"]),
 4: (["2.4","18.1"], ["2.4-1b","18.1-1c"], ["calculate"], 4, ["acid neutralisation emp formula from NaOH mol"]),
 5: (["3.5"], ["3.5-1c"], ["recall"], 3, ["molecules planar arrangement of atoms"]),
 6: (["3.4"], ["3.4-2b"], ["recall"], 3, ["propyne bonding sigma/pi"]),
 7: (["4.2"], ["4.2-1a"], ["explain"], 3, ["H2O vs H2S boiling point hydrogen bonding"]),
 8: (["4.2","9.2"], ["4.2-1b","9.2-4"], ["recall"], 2, ["silicon dioxide giant covalent structure"]),
 9: (["2.4","1.4"], ["2.4-1a"], ["calculate"], 3, ["using given data to compute quantity"]),
 10: (["5.2","7.2"], ["5.2-2a"], ["calculate"], 4, ["enthalpy change of neutralisation HCl/NaOH"]),
 11: (["6.1","2.4"], ["6.1-2"], ["calculate"], 4, ["redox FeC2O4 + MnO4 molar ratio"]),
 12: (["7.1"], ["7.1-8"], ["calculate"], 4, ["Kc from equilibrium amounts NO2 decomposition"]),
 13: (["8.3"], ["8.3-3"], ["explain"], 3, ["Ea forward vs reverse in exothermic reversible"]),
 14: (["8.1"], ["8.1-3"], ["explain"], 3, ["slow reaction mixing aqueous solutions reason"]),
 15: (["8.1"], ["8.1-2b"], ["explain"], 3, ["gas mixture faster at higher temperature"]),
 16: (["9.2"], ["9.2-5"], ["data-analysis"], 4, ["student investigation of Period 3 chloride"]),
 17: (["9.2","9.1"], ["9.1-2"], ["recall"], 3, ["melting point trend Mg/Al/Si/P graph"]),
 18: (["9.1","10.1"], ["10.1-1","10.1-3"], ["explain"], 3, ["Caesium and barium Period 6 predictions"]),
 19: (["10.1"], ["10.1-3"], ["recall"], 3, ["Mg nitrate decomposition white solid"]),
 20: (["10.1","10.2"], ["10.1-3","10.2-3"], ["data-analysis"], 4, ["Group 2 nitrate trends down group"]),
 21: (["9.3","6.1"], ["9.3-1"], ["explain"], 4, ["aqueous solutions X/Y/Z precipitation combinations"]),
 22: (["11.4"], ["11.4-1","11.4-2"], ["recall"], 3, ["chlorine + hot KOH disproportionation"]),
 23: (["12.1"], ["12.1-5"], ["recall"], 2, ["NO and NO2 as pollutants in atmosphere"]),
 24: (["12.1","11.3"], ["12.1-4"], ["recall"], 2, ["ammonium sulfate reagent liberating ammonia"]),
 25: (["15.1","14.2"], ["15.1-1a"], ["explain"], 3, ["alkane + chlorine free radical substitution"]),
 26: (["13.4","16.1"], ["13.4-4"], ["recall"], 3, ["beta-ionone structure functional groups"]),
 27: (["13.4","14.1"], ["13.4-4"], ["recall"], 4, ["structural and stereoisomerism"]),
 28: (["13.4","14.1"], ["13.4-4"], ["recall"], 3, ["testosterone skeletal formula carbonyl/alcohol"]),
 29: (["14.1"], ["14.1-4"], ["recall"], 3, ["pinenes unsaturated alkene structures"]),
 30: (["17.1"], ["17.1-1"], ["recall"], 2, ["carbanion carbon negative charge"]),
 31: (["15.1"], ["15.1-3a","15.1-4"], ["data-analysis"], 3, ["2-chloro vs 2-bromopropane + aqueous NaOH"]),
 32: (["16.1","13.4"], ["16.1-2b"], ["recall"], 3, ["compound X structure identification"]),
 33: (["16.1"], ["16.1-2d","16.1-4"], ["recall"], 3, ["two-step cyclohexanol to cyclohexane-1,2-diol"]),
 34: (["18.1","17.1"], ["18.1-2a"], ["data-analysis"], 3, ["three tests on unknown organic compound"]),
 35: (["17.1"], ["17.1-3"], ["recall"], 3, ["butanone + HCN nucleophilic addition"]),
 36: (["18.2"], ["18.2-1b"], ["recall"], 2, ["CH3CH2COOCH2CH3 structure ester"]),
 37: (["13.4","15.1"], ["13.4-4"], ["recall"], 3, ["three organic compound structures"]),
 38: (["15.1"], ["15.1-3a","15.1-4"], ["recall"], 3, ["bromoethane + NaOH ethanol elimination"]),
 39: (["20.1"], ["20.1-3"], ["recall"], 3, ["PMMA repeat unit polymer"]),
 40: (["22.2"], ["22.2-1","22.2-3"], ["calculate"], 4, ["gallium isotopic abundance Ar"]),
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
