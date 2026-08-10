#!/usr/bin/env python3
"""Curate controlled practical-topic tags for draft/9701_s25_qp_31 tagged JSON."""
import json, os
import yaml

ROOT = "/Users/tsinglan-school/Desktop/题库"
SYL = os.path.join(ROOT, "syllabus/cie-9701-as-a-level-chemistry.yaml")
TAGD = os.path.join(ROOT, "draft/9701_s25_qp_31/tagged")

syl = yaml.safe_load(open(SYL))
CODE_TITLE, LO_TEXT = {}, {}
for t in syl["topics"]:
    for st in t["subtopics"]:
        CODE_TITLE[st["code"]] = st["title"]
        for lo in st["learning_outcomes"]:
            LO_TEXT[lo["id"]] = " ".join(lo["text"].split())

# q -> (practical_topic, marks, syllabus_codes, learning_outcomes, skills, difficulty)
CUR = {
 "q1": ("Gas volume experiments", 10,
        ["2.4"], ["2.4-1b","2.4-1c"],
        ["practical","calculate"], 3),
 "q2": ("Titrations", 18,
        ["2.4","2.2"], ["2.4-1d","2.2-1"],
        ["practical","calculate"], 4),
 "q3": ("Qualitative analysis", 12,
        ["11.3","11.2"], ["11.3-2a","11.2-2"],
        ["practical","recall"], 3),
}

n=0
for fn,(topic,marks,codes,los,skills,diff) in CUR.items():
    p=os.path.join(TAGD,fn+".json")
    obj=json.load(open(p))
    obj["question_type"]="practical"
    obj["practical_topic"]=topic
    obj["marks"]=marks
    obj["syllabus_codes"]=list(codes)
    obj["topic_titles"]=[CODE_TITLE[c] for c in codes]
    obj["learning_outcomes"]=list(los)
    obj["learning_outcome_texts"]=[LO_TEXT[x] for x in los]
    obj["skills"]=list(skills)
    obj["difficulty"]=diff
    obj["ms_answer"]=None
    json.dump(obj,open(p,"w"),ensure_ascii=False,indent=2)
    n+=1
print("WROTE",n,"practical JSONs")
