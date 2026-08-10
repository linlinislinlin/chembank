#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_w25_qp_12 tagged JSON (MCQ)."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_w25_qp_12/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

CUR = {
 1: (["1.3"], ["1.3-3"], ["recall"], 2, ["spin direction/order in Fe3+ 3d orbitals"]),
 2: (["1.4"], ["1.4-2"], ["recall"], 1, ["first ionisation energy equation selection"]),
 3: (["2.4","6.1"], ["2.4-1a"], ["calculate"], 3, ["H2S+SO2 limiting; sulfur volume/moles"]),
 4: (["1.4","9.1"], ["1.4-1"], ["recall"], 3, ["general statement about IE/isoelectronic"]),
 5: (["3.4"], ["3.4-2b"], ["recall"], 3, ["hybridisation of N2 sigma/pi overlap"]),
 6: (["3.5"], ["3.5-1","3.5-2"], ["recall"], 2, ["ordering bond angles in molecule"]),
 7: (["9.1"], ["9.1-1"], ["data-analysis"], 3, ["Period 3 element X/Y comparison"]),
 8: (["4.1"], ["4.1-3"], ["calculate"], 4, ["ideal gas Mr from density"]),
 9: (["5.2"], ["5.2-2b"], ["calculate"], 4, ["q=mcT combustion energy"]),
 10: (["5.1","6.1"], ["5.1-4","6.1-2"], ["explain"], 3, ["heat pad iron oxidation exothermic"]),
 11: (["6.1"], ["6.1-1"], ["calculate"], 3, ["average oxidation number of S highest"]),
 12: (["7.1"], ["7.1-8"], ["explain"], 3, ["equilibrium Kc/position reasoning"]),
 13: (["7.1"], ["7.1-7"], ["explain"], 3, ["Contact process yield/conditions"]),
 14: (["8.1"], ["8.1-1"], ["calculate"], 4, ["rate of decomposition; mol/s from gas vol"]),
 15: (["7.1","8.3"], ["7.1-6","8.3-1a"], ["recall"], 3, ["reaction pathway diagram endothermic multi-step"]),
 16: (["12.1"], ["12.1-5"], ["recall"], 2, ["NOx in photochemical smog/acid rain"]),
 17: (["9.1","1.3"], ["9.1-1"], ["calculate"], 3, ["Na2S ionic compound electron transfer"]),
 18: (["9.2"], ["9.2-4"], ["data-analysis"], 4, ["identifying Period 3 oxide X"]),
 19: (["10.1"], ["10.1-3"], ["recall"], 3, ["Mg nitrate thermal decomposition products"]),
 20: (["9.3","11.3"], ["9.3-1"], ["explain"], 3, ["ionic compound R aqueous reactions"]),
 21: (["11.4"], ["11.4-1","11.4-2"], ["calculate"], 5, ["chlorine + hot NaOH NaClO3 stoichiometry"]),
 22: (["11.2"], ["11.2-1"], ["recall"], 2, ["sodium halide salts X/Y displacement"]),
 23: (["9.2"], ["9.2-5"], ["explain"], 4, ["E chloride reaction with water hydrolysis"]),
 24: (["8.1"], ["8.1-2"], ["data-analysis"], 3, ["reaction mixtures rate/order comparison"]),
 25: (["13.4","3.5"], ["13.4-1"], ["recall"], 3, ["methanal molecule statements"]),
 26: (["1.3","13.4"], ["13.4-4"], ["recall"], 3, ["disodium cromoglycate structure"]),
 27: (["14.2"], ["14.2-3"], ["recall"], 3, ["major product HBr addition carbocation"]),
 28: (["14.2"], ["14.2-2a"], ["recall"], 3, ["cold dilute KMnO4 diol product"]),
 29: (["13.4","14.1"], ["13.4-1"], ["recall"], 3, ["limonene structure alkene bonds"]),
 30: (["19.2","15.1"], ["19.2-1a"], ["recall"], 3, ["reaction producing nitrile"]),
 31: (["15.1"], ["15.1-3a"], ["recall"], 3, ["SN1 reaction identification"]),
 32: (["16.1"], ["16.1-2b"], ["recall"], 3, ["reaction producing primary alcohol"]),
 33: (["16.1"], ["16.1-2d","16.1-4"], ["explain"], 4, ["HOCH2CHO oxidation with excess K2Cr2O7"]),
 34: (["17.1","19.1"], ["17.1-6"], ["recall"], 3, ["organometallic RLi nucleophile reaction"]),
 35: (["13.4","16.1"], ["13.4-4"], ["recall"], 3, ["naturally occurring compound Q"]),
 36: (["18.1"], ["18.1-2e"], ["recall"], 3, ["starting material to propanoic acid"]),
 37: (["16.1","18.1"], ["16.1-2c","18.1-2b"], ["calculate"], 5, ["gas volumes from 1mol compound with Na/Na2CO3/NaOH"]),
 38: (["19.2","15.1"], ["19.2-3"], ["recall"], 2, ["butanenitrile + H2 reduction to butylamine"]),
 39: (["20.1"], ["20.1-3"], ["recall"], 3, ["addition polymer repeat unit"]),
 40: (["22.1"], ["22.1-1"], ["data-analysis"], 3, ["IR spectroscopy purity determination"]),
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
