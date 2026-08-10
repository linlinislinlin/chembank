#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_s25_qp_23 structured parts."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_s25_qp_23/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

META = {
 "q1a-i":   ("1(a)(i)","1","(a)(i)"), "q1a-ii": ("1(a)(ii)","1","(a)(ii)"), "q1a-iii": ("1(a)(iii)","1","(a)(iii)"),
 "q1b-i":   ("1(b)(i)","1","(b)(i)"), "q1b-ii": ("1(b)(ii)","1","(b)(ii)"), "q1b-iii": ("1(b)(iii)","1","(b)(iii)"),
 "q2a":     ("2(a)","2","(a)"), "q2b": ("2(b)","2","(b)"),
 "q2c-i":   ("2(c)(i)","2","(c)(i)"), "q2c-ii": ("2(c)(ii)","2","(c)(ii)"),
 "q2d":     ("2(d)","2","(d)"), "q2e-i": ("2(e)(i)","2","(e)(i)"), "q2e-ii": ("2(e)(ii)","2","(e)(ii)"),
 "q3a-i":   ("3(a)(i)","3","(a)(i)"), "q3a-ii": ("3(a)(ii)","3","(a)(ii)"),
 "q3b-i":   ("3(b)(i)","3","(b)(i)"), "q3b-ii": ("3(b)(ii)","3","(b)(ii)"), "q3b-iii": ("3(b)(iii)","3","(b)(iii)"),
 "q4a-i":   ("4(a)(i)","4","(a)(i)"), "q4a-ii": ("4(a)(ii)","4","(a)(ii)"), "q4a-iii": ("4(a)(iii)","4","(a)(iii)"),
 "q4a-iv":  ("4(a)(iv)","4","(a)(iv)"), "q4a-v": ("4(a)(v)","4","(a)(v)"),
 "q4b-i":   ("4(b)(i)","4","(b)(i)"), "q4b-ii": ("4(b)(ii)","4","(b)(ii)"),
 "q5a-i":   ("5(a)(i)","5","(a)(i)"), "q5a-ii": ("5(a)(ii)","5","(a)(ii)"),
 "q5b-i":   ("5(b)(i)","5","(b)(i)"), "q5b-ii": ("5(b)(ii)","5","(b)(ii)"), "q5b-iii": ("5(b)(iii)","5","(b)(iii)"),
 "q5b-iv":  ("5(b)(iv)","5","(b)(iv)"), "q5b-v": ("5(b)(v)","5","(b)(v)"), "q5b-vi": ("5(b)(vi)","5","(b)(vi)"),
 "q5c":     ("5(c)","5","(c)"),
 "q6a-i":   ("6(a)(i)","6","(a)(i)"), "q6a-ii": ("6(a)(ii)","6","(a)(ii)"), "q6a-iii": ("6(a)(iii)","6","(a)(iii)"),
 "q6b":     ("6(b)","6","(b)"),
 "q6c-i":   ("6(c)(i)","6","(c)(i)"), "q6c-ii": ("6(c)(ii)","6","(c)(ii)"), "q6c-iii": ("6(c)(iii)","6","(c)(iii)"),
}

CUR = {
 # Q1 atomic structure / ionisation energy / ionic radius
 "q1a-i": (["1.3"], ["1.3-4"], ["recall"], 1),
 "q1a-ii": (["1.3"], ["1.3-1"], ["recall"], 2),
 "q1a-iii": (["1.3"], ["1.3-8"], ["draw"], 1),
 "q1b-i": (["1.4"], ["1.4-2"], ["recall"], 2),
 "q1b-ii": (["1.4"], ["1.4-4","1.4-6"], ["explain"], 4),
 "q1b-iii": (["1.1"], ["1.1-7"], ["explain"], 3),
 # Q2 periodicity of oxides
 "q2a": (["9.2"], ["9.2-3"], ["recall"], 1),
 "q2b": (["9.2"], ["9.2-4"], ["recall"], 3),
 "q2c-i": (["9.2","6.1"], ["9.2-2","6.1-1"], ["recall"], 3),
 "q2c-ii": (["9.2","4.2"], ["9.2-6","4.2-2"], ["evaluate","data-analysis"], 5),
 "q2d": (["7.2"], ["7.2-3"], ["recall"], 2),
 "q2e-i": (["9.2"], ["9.2-4"], ["recall"], 2),
 "q2e-ii": (["9.2"], ["9.2-4"], ["recall"], 2),
 # Q3 hydrocarbons / catalytic cracking / smog / kinetics
 "q3a-i": (["14.1","15.1"], ["14.1-1b","15.1-1a"], ["recall"], 1),
 "q3a-ii": (["14.1"], ["14.1-6"], ["explain"], 3),
 "q3b-i": (["14.2","8.3"], ["14.2-2a"], ["recall"], 1),
 "q3b-ii": (["8.2"], ["8.2-1"], ["recall"], 1),
 "q3b-iii": (["8.3","8.2"], ["8.3-1b","8.2-2"], ["explain"], 3),
 # Q4 kinetics / rate graphs / SO2
 "q4a-i": (["8.1"], ["8.1-2"], ["data-analysis","calculate"], 4),
 "q4a-ii": (["8.1","2.4"], ["8.1-1","2.4-1d"], ["data-analysis"], 3),
 "q4a-iii": (["8.1"], ["8.1-1"], ["explain"], 2),
 "q4a-iv": (["2.4","6.1"], ["2.4-1a"], ["calculate"], 4),
 "q4a-v": (["12.1","8.1"], ["12.1-5","8.1-1"], ["explain"], 3),
 "q4b-i": (["3.5"], ["3.5-1","3.5-2"], ["recall"], 2),
 "q4b-ii": (["3.6"], ["3.6-2"], ["explain"], 3),
 # Q5 vitamin / carbonyl / ester polymer / IR
 "q5a-i": (["2.3"], ["2.3-5"], ["calculate"], 3),
 "q5a-ii": (["16.1","14.2","13.1"], ["16.1-2c","14.2-3","13.1-1"], ["recall"], 4),
 "q5b-i": (["13.3"], ["13.3-3"], ["recall"], 4),
 "q5b-ii": (["17.1","16.1"], ["17.1-2a","16.1-1d"], ["draw"], 3),
 "q5b-iii": (["18.1","16.1"], ["18.1-2e","16.1-1e"], ["recall"], 1),
 "q5b-iv": (["18.2"], ["18.2-1a"], ["recall"], 2),
 "q5b-v": (["22.1"], ["22.1-1"], ["data-analysis"], 3),
 "q5b-vi": (["20.1"], ["20.1-2"], ["draw"], 2),
 "q5c": (["14.1","14.2"], ["14.2-1c","14.2-2a"], ["explain"], 3),
 # Q6 HOCl / electrophilic addition / synthesis
 "q6a-i": (["13.2","14.2"], ["13.2-1a"], ["recall"], 1),
 "q6a-ii": (["11.4"], ["11.4-1"], ["recall"], 2),
 "q6a-iii": (["11.4"], ["11.4-2"], ["recall"], 1),
 "q6b": (["14.2"], ["14.2-4"], ["draw"], 4),
 "q6c-i": (["19.2","15.1"], ["19.2-1a","15.1-3b"], ["recall"], 3),
 "q6c-ii": (["19.2"], ["19.2-3"], ["recall"], 2),
 "q6c-iii": (["19.2"], ["19.2-3"], ["recall"], 2),
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
