#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_s25_qp_13 tagged JSON.

Reads the mock-generated skeletons (already valid metadata/id/body) and fills in
the academically-correct syllabus codes, learning outcomes, skills, difficulty.
All codes/LOs/titles/texts come from the authoritative syllabus YAML, never
invented. skeleton = draft/9701_s25_qp_13/tagged/qN.json.
"""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
DRAFT = os.path.join(ROOT, "draft/9701_s25_qp_13/tagged")

syl = yaml.safe_load(open(SYL))
# build code -> {title}, id -> text
CODE_TITLE = {}
LO_TEXT = {}
CODE_LOS = {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        los = []
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())
            los.append(lo["id"])
        CODE_LOS[st["code"]] = los

# Question -> (syllabus_codes, learning_outcomes, skills, difficulty, misconceptions)
# skills from ALLOWED_SKILLS: recall, explain, calculate, data-analysis, practical, compare, evaluate, draw
CUR = {
 1: (["1.3"], ["1.3-2", "1.3-8"], ["recall"], 2, ["confusing s-orbital electron count across elements"]),
 2: (["5.1", "8.2"], ["5.1-2", "8.2-3"], ["explain"], 4, ["thinking higher temperature lowers Ea rather than raising energy"]),
 3: (["7.2"], ["7.2-3"], ["explain"], 5, ["counting only first step as acid-base; misreading mechanistic steps"]),
 4: (["6.1", "2.4"], ["6.1-1", "6.1-3"], ["calculate"], 4, ["ignoring silicon ox state +4 to fix Cr ox state"]),
 5: (["7.1"], ["7.1-3", "7.1-8"], ["calculate", "data-analysis"], 4, ["forgetting exothermic shift lowers product on heating"]),
 6: (["5.2"], ["5.2-2a"], ["calculate"], 3, ["wrong sign convention for formation data"]),
 7: (["8.2", "8.3"], ["8.2-2", "8.3-1c"], ["explain"], 4, ["confusing catalyst lowering Ea with higher temperature"]),
 8: (["13.3"], ["13.3-2", "13.3-3", "13.3-4"], ["recall"], 4, ["assuming sugar ring is planar; sigma vs pi bond count"]),
 9: (["4.2"], ["4.2-2", "4.2-1c"], ["recall"], 3, ["confusing covalent bond breaking on melting vs intermolecular forces"]),
 10: (["1.4"], ["1.4-5", "1.4-6"], ["explain"], 4, ["electron removal from Na+ vs Mg+ ion-electron attraction"]),
 11: (["3.5"], ["3.5-1", "3.5-2"], ["explain"], 4, ["predicting bond angle change on dative bond formation"]),
 12: (["5.1"], ["5.1-3a", "5.1-3b"], ["recall"], 3, ["mixing standard conditions; only enthalpy change of formation"]),
 13: (["2.2", "2.4"], ["2.2-1", "2.4-1b", "2.4-1c"], ["calculate"], 3, ["molar volume 24000 cm3 vs concentration confusion"]),
 14: (["4.1"], ["4.1-3"], ["calculate"], 3, ["unit conversion cm3 to m3"]),
 15: (["2.4"], ["2.4-1a", "2.4-1c"], ["calculate", "data-analysis"], 5, ["2:1 acid:NaHCO3 stoichiometry; percentage mass"]),
 16: (["12.1"], ["12.1-2c", "12.1-2a"], ["recall"], 4, ["product of ammonia with salt of ammonium"]),
 17: (["11.3"], ["11.3-2a"], ["recall"], 3, ["AgCl dissolving in ammonia vs other halide precipitates"]),
 18: (["10.1"], ["10.1-2", "10.1-1"], ["recall"], 3, ["Group 2 oxide + water reactions"]),
 19: (["11.2", "11.3"], ["11.3-1", "11.2-3", "11.1-2"], ["explain"], 4, ["hydride thermal stability vs bond strength; halide reducing power"]),
 20: (["9.2"], ["9.2-2", "9.2-4", "9.2-6"], ["recall"], 4, ["max oxidation state trend; which oxides hydrolyse"]),
 21: (["12.1"], ["12.1-4"], ["recall"], 4, ["PAN formation from NOx and hydrocarbons, formula"],
      ),
 22: (["9.1"], ["9.1-1", "9.1-2"], ["recall", "compare"], 4, ["melting point + conductivity across Period 3 set"]),
 23: (["1.1"], ["1.1-7"], ["recall", "compare"], 3, ["ionic radius vs atomic radius; isoelectronic size trend"]),
 24: (["10.1"], ["10.1-4", "10.1-5", "10.1-3"], ["data-analysis", "recall"], 5, ["ordering Group 2 reactivity/solubility then Mr calc"]),
 25: (["20.1"], ["20.1-2", "20.1-3"], ["recall"], 4, ["identifying monomer from repeat unit"]),
 26: (["19.2", "18.1"], ["19.2-3", "18.1-1b"], ["calculate"], 4, ["nitrile hydrolysis stoichiometry and % yield"]),
 27: (["18.1"], ["18.1-2b"], ["recall"], 3, ["dicarboxylic acid + excess NaOH giving dicarboxylate"]),
 28: (["18.2", "21.1"], ["18.2-2", "21.1-1b"], ["data-analysis"], 5, ["ester hydrolysis products; identifying the constituent acids"]),
 29: (["17.1"], ["17.1-3", "19.2-2a"], ["explain"], 4, ["HCN nucleophilic addition; proton transfer to intermediate"]),
 30: (["17.1"], ["17.1-2a", "16.1-1d"], ["recall"], 3, ["NaBH4 reduces ketone to secondary alcohol"]),
 31: (["16.1"], ["16.1-3b", "16.1-2d"], ["recall", "compare"], 4, ["K2Cr2O7 oxidation: which alcohol is not oxidised"]),
 32: (["17.1", "16.1", "13.4"], ["17.1-6", "16.1-4", "13.4-6"], ["recall"], 5, ["counting C5H12O alcohols that give iodoform"]),
 33: (["19.1", "15.1"], ["19.1-1a", "15.1-3c"], ["recall"], 3, ["halogenoalkane + ammonia nucleophilic substitution"]),
 34: (["19.2", "15.1"], ["19.2-1a", "15.1-3b"], ["recall"], 3, ["KCN in ethanol heat produces nitrile"]),
 35: (["14.2"], ["14.2-2b", "14.2-2c"], ["recall"], 4, ["cold vs hot KMnO4 oxidation products of alkene"]),
 36: (["14.1"], ["14.1-3"], ["recall"], 3, ["free-radical substitution initiation/propagation/termination"]),
 37: (["13.4", "17.1"], ["13.4-3", "17.1-5"], ["recall"], 4, ["cis/trans + Fehling positive (aldehyde)"]),
 38: (["13.4"], ["13.4-4", "13.4-5"], ["recall"], 4, ["identifying chiral centres in fructose"]),
 39: (["2.3", "13.4"], ["2.3-3", "13.4-1"], ["recall"], 4, ["empirical formula C2H4O functional group isomerism"]),
 40: (["22.2"], ["22.2-3", "22.2-4", "22.2-5"], ["data-analysis"], 5, ["M+1 isotope peak; fragmentation; m/e ratios"]),
}

def topic_titles_for(codes):
    return [CODE_TITLE[c] for c in codes]

def lo_texts_for(los):
    return [LO_TEXT[x] for x in los]

out = []
for q, (codes, los, skills, diff, miscon) in CUR.items():
    fn = os.path.join(DRAFT, f"q{q}.json")
    with open(fn) as f:
        obj = json.load(f)
    obj["syllabus_codes"] = list(codes)
    obj["topic_titles"] = topic_titles_for(codes)
    obj["learning_outcomes"] = list(los)
    obj["learning_outcome_texts"] = lo_texts_for(los)
    obj["skills"] = list(skills)
    obj["difficulty"] = diff
    obj["misconceptions"] = miscon if miscon else []
    obj["marks"] = 1
    obj["question_type"] = "mcq"
    out.append(obj)
    with open(fn, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"q{q}.json  codes={codes}  los={los}")
print("WROTE", len(out), "tagged qp13 JSONs")
