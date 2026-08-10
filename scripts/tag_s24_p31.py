#!/usr/bin/env python3
"""Generate tagged/q*.json for draft/9701_s24_qp_31 (Paper 3 practical) by hand."""
import json
import os
import sys

import yaml

PAPER_ID = "9701_s24_qp_31"
DRAFT = os.path.join("draft", PAPER_ID)
TAGGED = os.path.join(DRAFT, "tagged")
QP = "raw/papers/9701_s24_qp_31.pdf"
MS = "raw/papers/9701_s24_ms_31.pdf"

# question -> (marks, topic, codes, los, skills, diff)
BLOCKS = {
 "1": (13, "Thermometric experiments", ["5.1", "5.2"],
       ["5.1-7", "5.2-1", "5.2-2a"],
       ["practical", "calculate"], 4),
 "2": (14, "Titrations", ["2.2", "2.3", "2.4"],
       ["2.2-1", "2.3-4", "2.4-1b", "2.4-1e"],
       ["practical", "calculate"], 4),
 "3": (13, "Qualitative analysis", [], [],
       ["practical", "observe", "deduce"], 4),
}

def main():
    os.makedirs(TAGGED, exist_ok=True)
    for q, spec in BLOCKS.items():
        marks, topic, codes, los, skills, diff = spec
        qid = f"cie-9701-2024-mj-p31-q{q}"
        rec = {
            "id": qid,
            "exam_board": "CIE",
            "syllabus_code": "9701",
            "level": "AS",
            "year": 2024,
            "session": "MJ",
            "paper": 31,
            "question": q,
            "parent_question": q,
            "part": None,
            "marks": marks,
            "syllabus_codes": codes,
            "topic_titles": [],
            "skills": skills,
            "question_type": "practical",
            "practical_topic": topic,
            "difficulty": diff,
            "command_words": [],
            "misconceptions": [],
            "learning_objectives": [],
            "learning_outcomes": los,
            "learning_outcome_texts": [],
            "ms_answer": None,
            "source_qp": QP,
            "source_ms": MS,
            "page_qp": None,
            "page_ms": None,
            "body": "",
            "mark_scheme": "",
            "figures": [],
        }
        with open(os.path.join(TAGGED, f"q{q}.json"), "w") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(BLOCKS)} tagged JSON files to {TAGGED}")

    syl = yaml.safe_load(open("syllabus/cie-9701-as-a-level-chemistry.yaml"))
    valid_codes, valid_los = set(), set()
    for t in syl["topics"]:
        valid_codes.add(str(t["code"]))
        for st in t["subtopics"]:
            valid_codes.add(str(st["code"]))
            for lo in st["learning_outcomes"]:
                valid_los.add(str(lo["id"]))
    bad = []
    for q, spec in BLOCKS.items():
        codes, los = spec[2], spec[3]
        for c in codes:
            if c not in valid_codes:
                bad.append((q, "code", c))
        for lo in los:
            if lo not in valid_los:
                bad.append((q, "lo", lo))
    if bad:
        print("INVALID TAGS:", bad)
        sys.exit(1)
    allowed = {"Titrations", "Thermometric experiments", "Gravimetric experiments",
               "Gas volume experiments", "Rate experiments", "Qualitative analysis"}
    for q, spec in BLOCKS.items():
        if spec[1] not in allowed:
            print("INVALID practical_topic:", q, spec[1])
            sys.exit(1)
    print("Validation OK: codes + LOs + practical_topic all in controlled vocabulary.")


if __name__ == "__main__":
    main()
