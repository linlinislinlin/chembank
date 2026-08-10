#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_m25_qp_22 structured parts."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_m25_qp_22/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

META = {
 "q1a-i":   ("1(a)(i)","1","(a)(i)"), "q1a-ii": ("1(a)(ii)","1","(a)(ii)"), "q1a-iii": ("1(a)(iii)","1","(a)(iii)"), "q1a-iv": ("1(a)(iv)","1","(a)(iv)"),
 "q1b-i":   ("1(b)(i)","1","(b)(i)"), "q1b-ii": ("1(b)(ii)","1","(b)(ii)"), "q1b-iii": ("1(b)(iii)","1","(b)(iii)"), "q1b-iv": ("1(b)(iv)","1","(b)(iv)"), "q1b-v": ("1(b)(v)","1","(b)(v)"),
 "q1c-i":   ("1(c)(i)","1","(c)(i)"), "q1c-ii": ("1(c)(ii)","1","(c)(ii)"),
 "q1d-i":   ("1(d)(i)","1","(d)(i)"), "q1d-ii": ("1(d)(ii)","1","(d)(ii)"),
 "q2a":     ("2(a)","2","(a)"), "q2b-i": ("2(b)(i)","2","(b)(i)"), "q2b-ii": ("2(b)(ii)","2","(b)(ii)"),
 "q2c-i":   ("2(c)(i)","2","(c)(i)"), "q2c-ii": ("2(c)(ii)","2","(c)(ii)"), "q2c-iii": ("2(c)(iii)","2","(c)(iii)"),
 "q2d-i":   ("2(d)(i)","2","(d)(i)"), "q2d-ii": ("2(d)(ii)","2","(d)(ii)"), "q2d-iii": ("2(d)(iii)","2","(d)(iii)"),
 "q3a-i":   ("3(a)(i)","3","(a)(i)"), "q3a-ii": ("3(a)(ii)","3","(a)(ii)"), "q3b": ("3(b)","3","(b)"),
 "q3c-i":   ("3(c)(i)","3","(c)(i)"), "q3c-ii": ("3(c)(ii)","3","(c)(ii)"), "q3c-iii": ("3(c)(iii)","3","(c)(iii)"),
 "q3d-i":   ("3(d)(i)","3","(d)(i)"), "q3d-ii": ("3(d)(ii)","3","(d)(ii)"), "q3d-iii": ("3(d)(iii)","3","(d)(iii)"), "q3d-iv": ("3(d)(iv)","3","(d)(iv)"), "q3d-v": ("3(d)(v)","3","(d)(v)"),
 "q4a":     ("4(a)","4","(a)"), "q4b-i": ("4(b)(i)","4","(b)(i)"), "q4b-ii": ("4(b)(ii)","4","(b)(ii)"), "q4b-iii": ("4(b)(iii)","4","(b)(iii)"),
}
CUR = {
 # Q1 P/Cl periodicity + halogens
 "q1a-i":   (["6.1"], ["6.1-1"], ["recall"], 1),
 "q1a-ii":  (["7.1"], ["7.1-3"], ["explain"], 3),
 "q1a-iii": (["2.3"], ["2.3-3"], ["calculate"], 4),
 "q1a-iv":  (["9.2","4.2"], ["9.2-5","4.2-2"], ["suggest","explain"], 4),
 "q1b-i":   (["9.2"], ["9.2-6"], ["suggest"], 2),
 "q1b-ii":  (["3.5"], ["3.5-1"], ["recall"], 1),
 "q1b-iii": (["9.2"], ["9.2-2"], ["recall"], 2),
 "q1b-iv":  (["9.2"], ["9.2-3"], ["recall"], 2),
 "q1b-v":   (["9.2","3.5"], ["9.2-4","3.5-1"], ["draw"], 2),
 "q1c-i":   (["13.2"], ["13.2-1a"], ["recall"], 1),
 "q1c-ii":  (["15.1"], ["15.1-4"], ["recall"], 2),
 "q1d-i":   (["22.2"], ["22.2-1","22.2-6"], ["data-analysis"], 3),
 "q1d-ii":  (["22.2"], ["22.2-2"], ["suggest"], 3),
 # Q2 Group 2 + atomic structure
 "q2a":     (["3.4"], ["3.4-1a"], ["recall"], 2),
 "q2b-i":   (["1.4","10.1"], ["1.4-6","10.1-4"], ["explain"], 3),
 "q2b-ii":  (["1.4"], ["1.4-1","1.4-5"], ["explain","data-analysis"], 4),
 "q2c-i":   (["1.1"], ["1.1-1","1.1-2"], ["recall"], 2),
 "q2c-ii":  (["1.1","1.2"], ["1.1-3","1.2-1"], ["recall"], 2),
 "q2c-iii": (["1.2"], ["1.2-1"], ["draw"], 2),
 "q2d-i":   (["10.1"], ["10.1-2"], ["recall"], 2),
 "q2d-ii":  (["10.1"], ["10.1-1"], ["recall"], 2),
 "q2d-iii": (["10.1"], ["10.1-5"], ["recall"], 1),
 # Q3 halogens + IBr
 "q3a-i":   (["11.1"], ["11.1-1"], ["recall"], 1),
 "q3a-ii":  (["11.1","4.2"], ["11.1-3","4.2-2"], ["explain"], 3),
 "q3b":     (["11.4"], ["11.4-2"], ["explain"], 3),
 "q3c-i":   (["11.3"], ["11.3-2b"], ["recall"], 3),
 "q3c-ii":  (["11.3"], ["11.3-2b"], ["recall"], 3),
 "q3c-iii": (["11.3"], ["11.3-2a"], ["recall"], 2),
 "q3d-i":   (["4.2"], ["4.2-2"], ["recall"], 2),
 "q3d-ii":  (["14.2"], ["14.2-4"], ["recall"], 1),
 "q3d-iii": (["14.2","13.1"], ["14.2-5","13.1-1"], ["draw"], 3),
 "q3d-iv":  (["13.4"], ["13.4-5"], ["recall"], 2),
 "q3d-v":   (["14.2"], ["14.2-5"], ["explain"], 4),
 # Q4 organic
 "q4a":     (["16.1","6.1","17.1"], ["16.1-4","17.1-6"], ["data-analysis","recall"], 5),
 "q4b-i":   (["17.1"], ["17.1-3"], ["draw"], 4),
 "q4b-ii":  (["17.1"], ["17.1-5"], ["recall"], 2),
 "q4b-iii": (["13.4"], ["13.4-4"], ["recall"], 2),
}
n=0
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
