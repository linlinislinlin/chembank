#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_s25_qp_14 tagged JSON."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
DRAFT = os.path.join(ROOT, "draft/9701_s25_qp_14/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

CUR = {
 1: (["1.4"], ["1.4-7", "1.4-8"], ["data-analysis"], 4, ["counting big jump wrongly; misidentifying element from IE graph"]),
 2: (["2.3"], ["2.3-3"], ["recall"], 2, ["confusing empirical vs molecular formula"]),
 3: (["3.5"], ["3.5-1", "3.5-2"], ["recall", "compare"], 4, ["forgetting H3O+ lone pair / H2O 104.5 vs 107"]),
 4: (["4.1", "2.4"], ["4.1-3", "2.4-1a"], ["calculate"], 5, ["neglecting volume quadrupling and temperature ratio"]),
 5: (["5.1", "5.2"], ["5.1-5", "5.2-2b"], ["calculate"], 5, ["mis-applying S8 atomisation energy per S=O bond"]),
 6: (["6.1"], ["6.1-1", "6.1-2"], ["calculate"], 4, ["computing average oxidation states in S2O3/2-/S2O4/2-"]),
 7: (["7.1"], ["7.1-3", "7.1-6"], ["explain"], 4, ["Le Chatelier pressure/temperature; Kp expression errors"]),
 8: (["8.2"], ["8.2-2"], ["explain"], 4, ["confusing most probable energy with total rate; pressure effect"]),
 9: (["1.3", "9.1"], ["1.3-4", "1.3-6"], ["recall"], 4, ["unpaired electron count trend across Period 3"]),
 10: (["2.4", "12.1"], ["2.4-1b", "12.1-3"], ["calculate"], 5, ["NO2 decomposition stoichiometry and partial pressure"]),
 11: (["3.5"], ["3.5-1"], ["recall"], 3, ["PF5 d orbitals and lone-pair geometry"]),
 12: (["3.4", "3.2"], ["3.4-1c", "3.2-1"], ["recall"], 4, ["ionic+covalent vs coordinate bonding"]),
 13: (["5.1"], ["5.1-3b"], ["recall"], 3, ["standard enthalpy of formation definition conditions"]),
 14: (["6.1", "2.4"], ["6.1-1", "6.1-2", "2.4-1a"], ["calculate"], 5, ["oxidation number bookkeeping for K2MnO4 + HCl redox"]),
 15: (["7.1"], ["7.1-3", "7.1-6", "7.1-8"], ["calculate"], 5, ["partial pressures on reaction; mole fractions"]),
 16: (["8.1", "18.2"], ["8.1-1", "18.2-2"], ["data-analysis"], 5, ["average rate between two times; ester hydrolysis products"]),
 17: (["3.5", "3.4"], ["3.5-1", "3.4-1c"], ["recall"], 3, ["bond pair / lone pair counting"]),
 18: (["11.1", "11.2", "11.3"], ["11.1-3", "11.2-3", "11.3-1"], ["explain"], 4, ["halogen vdW forces / oxidising power"]),
 19: (["10.1"], ["10.1-1", "10.1-2"], ["recall"], 3, ["Group 2 element/oxide reaction with water"]),
 20: (["12.1", "2.3"], ["12.1-2a", "2.3-3"], ["data-analysis"], 5, ["deducing ionic compound with NH empirical formula/conduction"]),
 21: (["9.2"], ["9.2-3", "9.2-4", "9.2-5"], ["data-analysis"], 5, ["inferring Period 3 element from oxide/chloride reactions"]),
 22: (["10.1"], ["10.1-3", "10.1-2"], ["recall"], 4, ["Group 2 carbonate/nitrate thermal stability + oxide-water"]),
 23: (["11.4"], ["11.4-1"], ["recall"], 3, ["chlorine + cold alkali disproportionation products"]),
 24: (["9.2"], ["9.2-2"], ["recall"], 3, ["highest oxidation number in oxide across Period 3"]),
 25: (["7.2", "3.5"], ["7.2-6", "3.5-1"], ["explain"], 4, ["ammonium ion weak acid; bond angles/dative bond"]),
 26: (["16.1", "2.3"], ["16.1-2d", "2.3-5"], ["calculate"], 5, ["alcohol oxidation + empirical formula to identify alcohol"]),
 27: (["16.1"], ["16.1-3a"], ["recall"], 3, ["primary/secondary/tertiary alcohol classification"]),
 28: (["15.1"], ["15.1-3b", "15.1-5"], ["recall"], 4, ["SN2 transition state; KCN nitrile formation"]),
 29: (["14.2", "2.4"], ["14.2-2a", "2.4-1a"], ["calculate"], 4, ["alkyne/alkene hydrogenation stoichiometry"]),
 30: (["14.2"], ["14.2-2c"], ["recall"], 5, ["hot KMnO4 oxidative cleavage of alkene"]),
 31: (["13.4"], ["13.4-4", "13.4-5"], ["recall"], 4, ["counting chiral centres in steroid"]),
 32: (["13.3", "3.6"], ["13.3-2", "3.6-2"], ["explain"], 4, ["quinone planarity + dipole moment"]),
 33: (["15.1"], ["15.1-4"], ["recall"], 3, ["elimination to alkene: ethanolic vs aqueous base"]),
 34: (["16.1", "17.1"], ["16.1-2d", "17.1-2b"], ["recall"], 5, ["distillation propanal then HCN → hydroxynitrile"]),
 35: (["17.1"], ["17.1-5", "17.1-6"], ["recall"], 5, ["iodoform + Tollens positive carbonyl compound"]),
 36: (["18.2", "13.4"], ["18.2-1a", "13.4-1", "13.4-6"], ["recall"], 5, ["counting isomeric esters of methanoic acid"]),
 37: (["2.4", "18.1"], ["2.4-1a", "18.1-2c"], ["calculate"], 5, ["citric acid titration stoichiometry with Na2CO3"]),
 38: (["19.1", "19.2", "15.1"], ["19.1-1a", "19.2-1a", "15.1-3b"], ["recall"], 4, ["halogenoalkane + NH3/KCN routes"]),
 39: (["20.1"], ["20.1-2", "20.1-3"], ["recall"], 4, ["polymer repeat unit → monomer"]),
 40: (["22.2"], ["22.2-1", "22.2-2"], ["data-analysis"], 4, ["reading Ar from mass spectrum"]),
}

out = 0
for q, (codes, los, skills, diff, miscon) in CUR.items():
    fn = os.path.join(DRAFT, f"q{q}.json")
    with open(fn) as f:
        obj = json.load(f)
    obj["syllabus_codes"] = list(codes)
    obj["topic_titles"] = [CODE_TITLE[c] for c in codes]
    obj["learning_outcomes"] = list(los)
    obj["learning_outcome_texts"] = [LO_TEXT[x] for x in los]
    obj["skills"] = list(skills)
    obj["difficulty"] = diff
    obj["misconceptions"] = miscon if miscon else []
    obj["marks"] = 1
    obj["question_type"] = "mcq"
    with open(fn, "w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    out += 1
print("WROTE", out, "tagged qp14 JSONs")
