#!/usr/bin/env python3
"""Curate controlled-vocabulary tags for draft/9701_s25_qp_21 structured parts."""
import json, os, re
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
DRAFT = os.path.join(ROOT, "draft/9701_s25_qp_21")
TAGD = os.path.join(DRAFT, "tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

# Map split file -> (question_label, parent, part)
# label uses (a)(i) notation; parent is main Q number; part is the part-notation string
META = {
 "q1a-i":   ("1(a)(i)",  "1", "(a)(i)"),
 "q1a-ii":  ("1(a)(ii)", "1", "(a)(ii)"),
 "q1a-iii": ("1(a)(iii)","1", "(a)(iii)"),
 "q1b-i":   ("1(b)(i)",  "1", "(b)(i)"),
 "q1b-ii":  ("1(b)(ii)", "1", "(b)(ii)"),
 "q1b-iii": ("1(b)(iii)","1", "(b)(iii)"),
 "q1c":     ("1(c)",     "1", "(c)"),
 "q1d":     ("1(d)",     "1", "(d)"),
 "q2a":     ("2(a)",     "2", "(a)"),
 "q2b-i":   ("2(b)(i)",  "2", "(b)(i)"),
 "q2b-ii":  ("2(b)(ii)", "2", "(b)(ii)"),
 "q2c":     ("2(c)",     "2", "(c)"),
 "q2d":     ("2(d)",     "2", "(d)"),
 "q2e":     ("2(e)",     "2", "(e)"),
 "q3a-i":   ("3(a)(i)",  "3", "(a)(i)"),
 "q3a-ii":  ("3(a)(ii)", "3", "(a)(ii)"),
 "q3a-iii": ("3(a)(iii)","3", "(a)(iii)"),
 "q3a-iv":  ("3(a)(iv)", "3", "(a)(iv)"),
 "q3b":     ("3(b)",     "3", "(b)"),
 "q3c":     ("3(c)",     "3", "(c)"),
 "q4a":     ("4(a)",     "4", "(a)"),
 "q4b-i":   ("4(b)(i)",  "4", "(b)(i)"),
 "q4b-ii":  ("4(b)(ii)", "4", "(b)(ii)"),
 "q4b-iii": ("4(b)(iii)","4", "(b)(iii)"),
 "q4b-iv":  ("4(b)(iv)", "4", "(b)(iv)"),
 "q4c":     ("4(c)",     "4", "(c)"),
 "q5a":     ("5(a)",     "5", "(a)"),
 "q5b":     ("5(b)",     "5", "(b)"),
 "q5c-i":   ("5(c)(i)",  "5", "(c)(i)"),
 "q5c-ii":  ("5(c)(ii)", "5", "(c)(ii)"),
 "q5d-i":   ("5(d)(i)",  "5", "(d)(i)"),
 "q5d-ii":  ("5(d)(ii)", "5", "(d)(ii)"),
 "q5e-i":   ("5(e)(i)",  "5", "(e)(i)"),
 "q5e-ii":  ("5(e)(ii)", "5", "(e)(ii)"),
 "q5e-iii": ("5(e)(iii)","5", "(e)(iii)"),
 "q6a":     ("6(a)",     "6", "(a)"),
 "q6b":     ("6(b)",     "6", "(b)"),
 "q6c-i":   ("6(c)(i)",  "6", "(c)(i)"),
 "q6c-ii":  ("6(c)(ii)", "6", "(c)(ii)"),
 "q6c-iii": ("6(c)(iii)","6", "(c)(iii)"),
}

# file -> (syllabus_codes, learning_outcomes, skills, difficulty)
CUR = {
 "q1a-i":   (["3.3","3.2"], ["3.3-1","3.2-1"], ["recall"], 2),
 "q1a-ii":  (["3.3"], ["3.3-1"], ["explain"], 3),
 "q1a-iii": (["3.2"], ["3.2-2"], ["explain"], 3),
 "q1b-i":   (["9.2","10.1"], ["9.2-3","10.1-1"], ["recall"], 2),
 "q1b-ii":  (["9.2"], ["9.2-3"], ["recall"], 2),
 "q1b-iii": (["10.1","9.2"], ["10.1-2","9.2-3"], ["compare","recall"], 3),
 "q1c":     (["6.1"], ["6.1-1","6.1-3"], ["calculate"], 4),
 "q1d":     (["9.1","9.2"], ["9.1-1","9.2-2"], ["evaluate","data-analysis"], 5),
 "q2a":     (["1.2"], ["1.2-1"], ["recall"], 1),
 "q2b-i":   (["2.1","22.2"], ["2.1-2","22.2-2"], ["calculate"], 4),
 "q2b-ii":  (["1.1"], ["1.1-3","1.1-6"], ["recall"], 2),
 "q2c":     (["1.3"], ["1.3-1"], ["recall"], 3),
 "q2d":     (["1.4"], ["1.4-2"], ["recall"], 2),
 "q2e":     (["1.4"], ["1.4-4","1.4-6"], ["explain"], 4),
 "q3a-i":   (["8.2"], ["8.2-2"], ["draw"], 3),
 "q3a-ii":  (["8.2"], ["8.2-3"], ["explain"], 3),
 "q3a-iii": (["8.3"], ["8.3-1a"], ["recall"], 1),
 "q3a-iv":  (["8.3","8.2"], ["8.3-1c"], ["draw"], 3),
 "q3b":     (["7.1"], ["7.1-2"], ["recall"], 2),
 "q3c":     (["7.1"], ["7.1-3","7.1-9"], ["data-analysis"], 4),
 "q4a":     (["2.3"], ["2.3-3"], ["calculate"], 3),
 "q4b-i":   (["2.4"], ["2.4-1c"], ["calculate"], 3),
 "q4b-ii":  (["2.4"], ["2.4-1a"], ["calculate"], 4),
 "q4b-iii": (["6.1"], ["6.1-3"], ["recall"], 2),
 "q4b-iv":  (["14.2","16.1"], ["14.2-2c","16.1-2d"], ["explain"], 4),
 "q4c":     (["22.1"], ["22.1-1"], ["recall"], 3),
 "q5a":     (["18.2"], ["18.2-1a"], ["draw"], 4),
 "q5b":     (["18.2"], ["18.2-2"], ["recall"], 2),
 "q5c-i":   (["18.1"], ["18.1-2c"], ["recall"], 3),
 "q5c-ii":  (["18.1"], ["18.1-2c"], ["explain"], 3),
 "q5d-i":   (["15.1","16.1"], ["15.1-3a","16.1-2d"], ["recall"], 4),
 "q5d-ii":  (["16.1"], ["16.1-2d"], ["recall"], 2),
 "q5e-i":   (["18.1","16.1"], ["18.1-2e","16.1-1e"], ["recall"], 2),
 "q5e-ii":  (["18.1"], ["18.1-2e"], ["calculate"], 4),
 "q5e-iii": (["13.1","16.1"], ["13.1-1"], ["recall"], 2),
 "q6a":     (["17.1","13.1"], ["17.1-1b","13.1-2"], ["recall"], 1),
 "q6b":     (["17.1"], ["17.1-4"], ["recall"], 2),
 "q6c-i":   (["17.1"], ["17.1-5"], ["data-analysis"], 4),
 "q6c-ii":  (["17.1"], ["17.1-6"], ["recall"], 2),
 "q6c-iii": (["17.1"], ["17.1-6"], ["suggest"], 3) if False else (["17.1"], ["17.1-6"], ["recall"], 3),
}

ALLOWED_SKILLS = {"recall","explain","calculate","data-analysis","practical","compare","evaluate","draw","suggest"}

n = 0
for fn, (q, parent, part) in META.items():
    codes, los, skills, diff = CUR[fn]
    p = os.path.join(TAGD, fn + ".json")
    if not os.path.exists(p):
        print("MISSING skeleton", fn); continue
    obj = json.load(open(p))
    obj["question"] = q
    obj["parent_question"] = parent
    obj["part"] = part
    obj["question_type"] = "structured"
    obj["syllabus_codes"] = list(codes)
    obj["topic_titles"] = [CODE_TITLE[c] for c in codes]
    obj["learning_outcomes"] = list(los)
    obj["learning_outcome_texts"] = [LO_TEXT[x] for x in los]
    obj["skills"] = list(skills)
    obj["difficulty"] = diff
    obj["ms_answer"] = None
    json.dump(obj, open(p, "w"), ensure_ascii=False, indent=2)
    n += 1
print("WROTE", n, "structured tagged JSONs")
