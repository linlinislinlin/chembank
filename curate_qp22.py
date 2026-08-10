#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_s25_qp_22 structured parts."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_s25_qp_22/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

META = {
 "q1a-i":   ("1(a)(i)","1","(a)(i)"),
 "q1a-ii":  ("1(a)(ii)","1","(a)(ii)"),
 "q1a-iii": ("1(a)(iii)","1","(a)(iii)"),
 "q1b-i":   ("1(b)(i)","1","(b)(i)"),
 "q1b-ii":  ("1(b)(ii)","1","(b)(ii)"),
 "q1b-iii": ("1(b)(iii)","1","(b)(iii)"),
 "q1c-i":   ("1(c)(i)","1","(c)(i)"),
 "q1c-ii":  ("1(c)(ii)","1","(c)(ii)"),
 "q1d-i":   ("1(d)(i)","1","(d)(i)"),
 "q1d-ii":  ("1(d)(ii)","1","(d)(ii)"),
 "q2a-i":   ("2(a)(i)","2","(a)(i)"),
 "q2a-ii":  ("2(a)(ii)","2","(a)(ii)"),
 "q2b":     ("2(b)","2","(b)"),
 "q2c":     ("2(c)","2","(c)"),
 "q2d":     ("2(d)","2","(d)"),
 "q2e":     ("2(e)","2","(e)"),
 "q3a-i":   ("3(a)(i)","3","(a)(i)"),
 "q3a-ii":  ("3(a)(ii)","3","(a)(ii)"),
 "q3a-iii": ("3(a)(iii)","3","(a)(iii)"),
 "q3b-i":   ("3(b)(i)","3","(b)(i)"),
 "q3b-ii":  ("3(b)(ii)","3","(b)(ii)"),
 "q3c":     ("3(c)","3","(c)"),
 "q3d-i":   ("3(d)(i)","3","(d)(i)"),
 "q3d-ii":  ("3(d)(ii)","3","(d)(ii)"),
 "q3e":     ("3(e)","3","(e)"),
 "q4a-i":   ("4(a)(i)","4","(a)(i)"),
 "q4a-ii":  ("4(a)(ii)","4","(a)(ii)"),
 "q4b-i":   ("4(b)(i)","4","(b)(i)"),
 "q4b-ii":  ("4(b)(ii)","4","(b)(ii)"),
 "q4b-iii": ("4(b)(iii)","4","(b)(iii)"),
 "q4b-iv":  ("4(b)(iv)","4","(b)(iv)"),
 "q4c-i":   ("4(c)(i)","4","(c)(i)"),
 "q4c-ii":  ("4(c)(ii)","4","(c)(ii)"),
 "q4c-iii": ("4(c)(iii)","4","(c)(iii)"),
 "q4d-i":   ("4(d)(i)","4","(d)(i)"),
 "q4d-ii":  ("4(d)(ii)","4","(d)(ii)"),
 "q4d-iii": ("4(d)(iii)","4","(d)(iii)"),
 "q5a":     ("5(a)","5","(a)"),
 "q5b-i":   ("5(b)(i)","5","(b)(i)"),
 "q5b-ii":  ("5(b)(ii)","5","(b)(ii)"),
 "q5b-iii": ("5(b)(iii)","5","(b)(iii)"),
}

CUR = {
 "q1a-i":   (["4.2"], ["4.2-1c"], ["recall"], 2),
 "q1a-ii":  (["4.2","3.3"], ["4.2-2","3.3-1"], ["explain"], 3),
 "q1a-iii": (["4.2"], ["4.2-2"], ["explain"], 3),
 "q1b-i":   (["9.2"], ["9.2-5"], ["recall"], 4),
 "q1b-ii":  (["9.2"], ["9.2-7"], ["recall"], 3),
 "q1b-iii": (["9.2"], ["9.2-7"], ["compare"], 3),
 "q1c-i":   (["9.2"], ["9.2-4"], ["recall"], 2),
 "q1c-ii":  (["9.2"], ["9.2-4"], ["recall"], 2),
 "q1d-i":   (["4.2","3.6"], ["4.2-2","3.6-3c"], ["recall"], 4),
 "q1d-ii":  (["4.2","3.6"], ["4.2-2","3.6-3b"], ["evaluate","data-analysis"], 5),
 "q2a-i":   (["2.1"], ["2.1-2"], ["recall"], 2),
 "q2a-ii":  (["2.1","22.2"], ["2.1-2","22.2-2"], ["calculate"], 4),
 "q2b":     (["1.3"], ["1.3-4"], ["recall"], 3),
 "q2c":     (["1.3"], ["1.3-8"], ["draw"], 2),
 "q2d":     (["1.1"], ["1.1-6"], ["recall"], 2),
 "q2e":     (["1.1","1.4"], ["1.1-7","1.4-6"], ["explain"], 3),
 "q3a-i":   (["13.2"], ["13.2-1a"], ["recall"], 1),
 "q3a-ii":  (["14.2"], ["14.2-4"], ["draw"], 4),
 "q3a-iii": (["14.2"], ["14.2-5"], ["explain"], 4),
 "q3b-i":   (["8.1","2.4"], ["8.1-1","2.4-1d"], ["data-analysis"], 4),
 "q3b-ii":  (["8.1"], ["8.1-1"], ["data-analysis"], 3),
 "q3c":     (["5.1"], ["5.1-5"], ["calculate"], 5),
 "q3d-i":   (["8.3"], ["8.3-1c"], ["draw"], 3),
 "q3d-ii":  (["8.3","8.2"], ["8.3-1b","8.2-2"], ["explain"], 4),
 "q3e":     (["14.2","13.1"], ["14.2-2c","13.1-1"], ["recall"], 5),
 "q4a-i":   (["18.1","16.1"], ["18.1-2e","16.1-1e"], ["recall"], 2),
 "q4a-ii":  (["18.1"], ["18.1-2e"], ["recall"], 2),
 "q4b-i":   (["16.1","15.1"], ["16.1-2b","15.1-1c"], ["recall"], 2),
 "q4b-ii":  (["19.2","15.1"], ["19.2-1a","15.1-3b"], ["recall"], 3),
 "q4b-iii": (["19.2"], ["19.2-3"], ["recall"], 4),
 "q4b-iv":  (["19.2"], ["19.2-3"], ["recall"], 2),
 "q4c-i":   (["3.4"], ["3.4-2c"], ["recall"], 2),
 "q4c-ii":  (["16.1"], ["16.1-2c"], ["recall"], 2),
 "q4c-iii": (["16.1","6.1"], ["16.1-2c","6.1-3"], ["explain"], 3),
 "q4d-i":   (["16.1"], ["16.1-3a","16.1-4"], ["data-analysis"], 4),
 "q4d-ii":  (["16.1"], ["16.1-3a","16.1-3b"], ["data-analysis"], 4),
 "q4d-iii": (["17.1","16.1"], ["17.1-6","16.1-4"], ["data-analysis"], 4),
 "q5a":     (["2.3"], ["2.3-5"], ["calculate"], 3),
 "q5b-i":   (["2.4"], ["2.4-1c"], ["calculate"], 3),
 "q5b-ii":  (["2.4"], ["2.4-1a"], ["calculate"], 4),
 "q5b-iii": (["22.1"], ["22.1-1"], ["data-analysis"], 3),
}

ALLOWED = {"recall","explain","calculate","data-analysis","practical","compare","evaluate","draw"}
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
