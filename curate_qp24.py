#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_s25_qp_24 structured parts."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_s25_qp_24/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

META = {
 "q1a": ("1(a)","1","(a)"), "q1b": ("1(b)","1","(b)"),
 "q1c-i": ("1(c)(i)","1","(c)(i)"), "q1c-ii": ("1(c)(ii)","1","(c)(ii)"),
 "q1c-iii": ("1(c)(iii)","1","(c)(iii)"), "q1c-iv": ("1(c)(iv)","1","(c)(iv)"),
 "q1d-i": ("1(d)(i)","1","(d)(i)"), "q1d-ii": ("1(d)(ii)","1","(d)(ii)"),
 "q2a-i": ("2(a)(i)","2","(a)(i)"), "q2a-ii": ("2(a)(ii)","2","(a)(ii)"),
 "q2b-i": ("2(b)(i)","2","(b)(i)"), "q2b-ii": ("2(b)(ii)","2","(b)(ii)"), "q2b-iii": ("2(b)(iii)","2","(b)(iii)"),
 "q3a-i": ("3(a)(i)","3","(a)(i)"), "q3a-ii": ("3(a)(ii)","3","(a)(ii)"),
 "q3b": ("3(b)","3","(b)"), "q3c": ("3(c)","3","(c)"),
 "q3d-i": ("3(d)(i)","3","(d)(i)"), "q3d-ii": ("3(d)(ii)","3","(d)(ii)"), "q3d-iii": ("3(d)(iii)","3","(d)(iii)"),
 "q4a": ("4(a)","4","(a)"), "q4b": ("4(b)","4","(b)"),
 "q4c-i": ("4(c)(i)","4","(c)(i)"), "q4c-ii": ("4(c)(ii)","4","(c)(ii)"), "q4c-iii": ("4(c)(iii)","4","(c)(iii)"),
 "q4d-i": ("4(d)(i)","4","(d)(i)"), "q4d-ii": ("4(d)(ii)","4","(d)(ii)"), "q4d-iii": ("4(d)(iii)","4","(d)(iii)"),
 "q5a": ("5(a)","5","(a)"),
 "q5b-i": ("5(b)(i)","5","(b)(i)"), "q5b-ii": ("5(b)(ii)","5","(b)(ii)"),
 "q5c": ("5(c)","5","(c)"),
 "q5d-i": ("5(d)(i)","5","(d)(i)"), "q5d-ii": ("5(d)(ii)","5","(d)(ii)"),
 "q6a-i": ("6(a)(i)","6","(a)(i)"), "q6a-ii": ("6(a)(ii)","6","(a)(ii)"), "q6a-iii": ("6(a)(iii)","6","(a)(iii)"),
 "q6b": ("6(b)","6","(b)"),
 "q6c-i": ("6(c)(i)","6","(c)(i)"), "q6c-ii": ("6(c)(ii)","6","(c)(ii)"), "q6c-iii": ("6(c)(iii)","6","(c)(iii)"),
}

CUR = {
 # Q1 Period 3 trends
 "q1a": (["4.2","9.1"], ["4.2-2","9.1-1"], ["recall"], 3),
 "q1b": (["9.1"], ["9.1-2"], ["explain"], 3),
 "q1c-i": (["1.4"], ["1.4-2"], ["recall"], 2),
 "q1c-ii": (["1.4"], ["1.4-6"], ["recall"], 2),
 "q1c-iii": (["1.4"], ["1.4-5","1.4-6"], ["explain","data-analysis"], 3),
 "q1c-iv": (["1.3"], ["1.3-4"], ["draw"], 2),
 "q1d-i": (["9.2"], ["9.2-1","9.2-2"], ["recall"], 2),
 "q1d-ii": (["9.2"], ["9.2-4"], ["recall"], 2),
 # Q2 SCl2 shape / redox / hydrolysis
 "q2a-i": (["3.5"], ["3.5-1"], ["recall"], 1),
 "q2a-ii": (["3.5"], ["3.5-2"], ["recall"], 1),
 "q2b-i": (["9.3"], ["9.3-1"], ["recall"], 2),
 "q2b-ii": (["6.1"], ["6.1-1"], ["calculate"], 2),
 "q2b-iii": (["9.3"], ["9.3-1"], ["recall"], 1),
 # Q3 equilibria / Kc
 "q3a-i": (["2.4"], ["2.4-1c"], ["calculate"], 3),
 "q3a-ii": (["2.4"], ["2.4-1c"], ["calculate"], 4),
 "q3b": (["7.1"], ["7.1-8"], ["calculate"], 4),
 "q3c": (["7.1"], ["7.1-7"], ["calculate"], 3),
 "q3d-i": (["3.4"], ["3.4-1a"], ["recall"], 1),
 "q3d-ii": (["11.2","3.4"], ["11.2-3","3.4-3a"], ["explain"], 3),
 "q3d-iii": (["7.1"], ["7.1-9"], ["evaluate"], 2),
 # Q4 esters / nitriles
 "q4a": (["13.1","18.2"], ["13.1-2","18.2-1a"], ["recall"], 1),
 "q4b": (["13.1"], ["13.1-4"], ["recall"], 2),
 "q4c-i": (["18.2"], ["18.2-1a"], ["recall"], 1),
 "q4c-ii": (["18.2","16.1"], ["18.2-1a","16.1-2f"], ["recall"], 3),
 "q4c-iii": (["13.1"], ["13.1-4"], ["recall"], 2),
 "q4d-i": (["19.2"], ["19.2-3"], ["recall"], 2),
 "q4d-ii": (["16.1"], ["16.1-3a"], ["draw"], 3),
 "q4d-iii": (["15.1","19.2"], ["15.1-1c","19.2-1a"], ["recall"], 3),
 # Q5 alkenes / stereoisomerism / oxidation
 "q5a": (["13.4"], ["13.4-1","13.4-6"], ["recall"], 3),
 "q5b-i": (["13.4"], ["13.4-3"], ["recall"], 1),
 "q5b-ii": (["13.4"], ["13.4-3"], ["explain"], 1),
 "q5c": (["13.4"], ["13.4-3"], ["draw"], 1),
 "q5d-i": (["14.2","6.1"], ["14.2-2c","6.1-3"], ["recall"], 2),
 "q5d-ii": (["14.2"], ["14.2-2c"], ["recall"], 1),
 # Q6 empirical formula / gas law / mass spec
 "q6a-i": (["2.3"], ["2.3-3"], ["recall"], 1),
 "q6a-ii": (["2.3"], ["2.3-5"], ["calculate"], 3),
 "q6a-iii": (["13.1","14.2"], ["13.1-1","14.2-1a"], ["recall"], 2),
 "q6b": (["4.1"], ["4.1-3"], ["calculate"], 4),
 "q6c-i": (["22.2"], ["22.2-5"], ["data-analysis"], 4),
 "q6c-ii": (["22.2"], ["22.2-3"], ["data-analysis"], 3),
 "q6c-iii": (["22.2"], ["22.2-4"], ["data-analysis"], 3),
}

n = 0
for fn,(q,parent,part) in META.items():
    codes,los,skills,diff = CUR[fn]
    p=os.path.join(TAGD,fn+".json")
    obj=json.load(open(p))
    obj["question"]=q; obj["parent_question"]=parent; obj["part"]=part
    obj["question_type"]="structured"
    obj["syllabus_codes"]=list(codes)
    obj["topic_titles"]=[CODE_TITLE[c] for c in codes]
    obj["learning_outcomes"]=list(los)
    obj["learning_outcome_texts"]=[LO_TEXT[x] for x in los]
    obj["skills"]=list(skills)
    obj["difficulty"]=diff
    obj["ms_answer"]=None
    json.dump(obj,open(p,"w"),ensure_ascii=False,indent=2)
    n+=1
print("WROTE",n,"structured JSONs")
