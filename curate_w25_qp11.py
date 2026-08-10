#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_w25_qp_11 tagged JSON (MCQ)."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_w25_qp_11/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

CUR = {
 1: (["1.3"], ["1.3-3","1.3-4"], ["recall"], 2, ["confusing ion electron config with atom; isotope handling"]),
 2: (["1.4","9.1"], ["1.4-1"], ["data-analysis"], 4, ["reading IE big-jump to fix element identity"]),
 3: (["2.4"], ["2.4-1a"], ["calculate"], 3, ["converting L/atom count; per-molecule O atoms"]),
 4: (["2.4"], ["2.4-1a","2.4-1e"], ["calculate"], 4, ["limiting reagent; volume of gas at room conditions"]),
 5: (["4.2","9.1"], ["9.1-1"], ["explain"], 3, ["metallic bonding strength Na vs K different melting point"]),
 6: (["3.4"], ["3.4-1c","3.4-2b"], ["explain"], 3, ["dative/coordinate bond + ionic NH4CN"]),
 7: (["5.1"], ["5.1-2","5.1-4"], ["explain"], 3, ["exothermic bond energy balance in neutralisation"]),
 8: (["5.2"], ["5.2-2b"], ["calculate"], 4, ["q=mcT with % efficiency; per gram fuel"]),
 9: (["6.1"], ["6.1-2"], ["explain"], 4, ["sulfite redox with zinc and MnO2; oxidation state change"]),
 10: (["6.1"], ["6.1-1"], ["recall"], 3, ["H2 as oxidising agent; oxidation number change of H"]),
 11: (["4.1"], ["4.1-3"], ["calculate"], 4, ["ideal gas law; mass to moles to pressure"]),
 12: (["7.1"], ["7.1-8"], ["calculate"], 4, ["Kc from equilibrium concentrations with 4:1 ratio"]),
 13: (["7.2","6.1"], ["7.2-2"], ["calculate"], 4, ["acid/alkali same concentration pH/neutralisation"]),
 14: (["7.1","3.4"], ["7.1-9"], ["suggest"], 3, ["reversible photochromic equilibrium shift"]),
 15: (["8.3"], ["8.3-1a","8.3-1c"], ["explain"], 4, ["catalyst lowering Ea in reversible esterification"]),
 16: (["1.1","9.1"], ["1.1-7","9.1-1"], ["data-analysis"], 4, ["comparing atomic vs ionic radii in Period 3"]),
 17: (["2.4"], ["2.4-1a"], ["calculate"], 3, ["stoichiometric coefficients in balanced equations"]),
 18: (["4.2","9.2"], ["4.2-2","9.2-5"], ["recall"], 3, ["simple vs giant molecular oxide structure"]),
 19: (["10.1"], ["10.1-3"], ["explain"], 3, ["predicting radium properties from Group 2 trends"]),
 20: (["10.1"], ["10.1-3"], ["calculate","data-analysis"], 5, ["thermal decomposition products; % mass loss comparison"]),
 21: (["11.3"], ["11.3-2b"], ["explain"], 3, ["halide ion Q- with conc H2SO4 redox"]),
 22: (["11.2"], ["11.2-3"], ["recall"], 2, ["displacement: iodine + sodium bromide no reaction"]),
 23: (["9.2","3.5"], ["9.2-5"], ["recall"], 3, ["general periodicity statement correctness"]),
 24: (["11.4","2.4"], ["11.4-2","2.4-1b"], ["calculate"], 4, ["NH4Cl formation; volumes of gases"]),
 25: (["13.4","16.1"], ["13.4-1","16.1-3a"], ["recall"], 4, ["isomers C6H12O: carbonyl/alcohol functional groups"]),
 26: (["13.4","13.1"], ["13.4-1"], ["recall"], 3, ["identifying functional groups in skeletal structures"]),
 27: (["14.2"], ["14.2-3"], ["recall"], 3, ["carbocation stability; intermediate ion in HBr addition"]),
 28: (["15.1","14.2"], ["15.1-1a"], ["explain"], 3, ["free-radical substitution of alkanes with bromine"]),
 29: (["12.1"], ["12.1-5"], ["recall"], 2, ["petrol exhaust pollutants identification"]),
 30: (["15.1","17.1"], ["15.1-1c","15.1-4"], ["explain"], 3, ["halogenoalkane + warm aqueous NaOH hydrolysis"]),
 31: (["15.1"], ["15.1-4"], ["suggest"], 4, ["elimination of 1,4-dibromobutane with ethanolic NaOH"]),
 32: (["20.1"], ["20.1-3"], ["recall"], 4, ["polymer from two monomers; repeat unit segments"]),
 33: (["16.1"], ["16.1-2d"], ["calculate"], 4, ["K2Cr2O7 oxidation stoichiometry of X"]),
 34: (["16.1","18.2"], ["16.1-2e"], ["recall"], 3, ["reflux conditions identifying product"]),
 35: (["18.2"], ["18.2-1a","18.2-2"], ["recall"], 3, ["ester hydrolysis products"]),
 36: (["17.1"], ["17.1-3"], ["recall"], 3, ["HCN + carbonyl producing 4-carbon product"]),
 37: (["19.1","19.2"], ["19.2-3"], ["recall"], 3, ["reagent/product table identification"]),
 38: (["17.1","16.1"], ["17.1-5"], ["explain"], 3, ["aldehydes/ketones tests distinguishing"]),
 39: (["19.2","15.1"], ["19.2-1a"], ["explain"], 3, ["compound X properties: nitrile/halogenoalkane"]),
 40: (["22.2"], ["22.2-1","22.2-3"], ["calculate"], 4, ["isotopic abundance to relative atomic mass"]),
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
