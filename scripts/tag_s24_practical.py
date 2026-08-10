#!/usr/bin/env python3
"""Generate tagged/q*.json for Paper 3 practical papers by hand.

Usage: tag_s24_practical.py <paper>  (e.g. 32, 33, 34, 35)
"""
import json
import os
import sys

import yaml

# paper -> {question: (marks, practical_topic, codes, los, skills, diff)}
PAPERS = {
 32: {
   "1": (11, "Thermometric experiments", ["5.1", "5.2"], ["5.1-7", "5.2-1", "5.2-2a"], ["practical", "explain", "calculate"], 4),
   "2": (15, "Titrations", ["2.2", "2.4", "6.1"], ["2.2-1", "2.4-1b", "2.4-1e", "6.1-3"], ["practical", "calculate"], 4),
   "3": (14, "Qualitative analysis", [], [], ["practical", "observe", "deduce"], 4),
  },
 33: {
   "1": (15, "Titrations", ["2.2", "2.4", "12.1"], ["2.2-1", "2.4-1b", "2.4-1e", "12.1-2c"], ["practical", "calculate"], 4),
   "2": (10, "Thermometric experiments", ["5.1", "5.2"], ["5.1-7", "5.2-2a"], ["practical", "calculate"], 4),
   "3": (15, "Qualitative analysis", ["12.1"], ["12.1-2a"], ["practical", "observe", "deduce"], 4),
  },
 34: {
   "1": (15, "Titrations", ["2.2", "2.4"], ["2.2-1", "2.4-1b", "2.4-1e"], ["practical", "calculate"], 4),
   "2": (11, "Gravimetric experiments", ["2.2", "2.4", "10.1"], ["2.2-1", "2.4-1a", "10.1-3"], ["practical", "calculate"], 4),
   "3": (14, "Qualitative analysis", [], [], ["practical", "observe", "deduce"], 4),
  },
 35: {
   "1": (11, "Rate experiments", ["8.1", "8.2"], ["8.1-1", "8.1-2", "8.2-3"], ["practical", "calculate", "explain"], 4),
   "2": (14, "Thermometric experiments", ["5.1", "5.2"], ["5.1-7", "5.2-2a"], ["practical", "calculate"], 4),
   "3": (15, "Qualitative analysis", [], [], ["practical", "observe", "deduce"], 4),
  },
}

def main():
    if len(sys.argv) < 2:
        print("usage: tag_s24_practical.py <paper>")
        sys.exit(1)
    paper = int(sys.argv[1])
    blocks = PAPERS[paper]
    paper_id = f"9701_s24_qp_{paper}"
    draft = os.path.join("draft", paper_id)
    tagged = os.path.join(draft, "tagged")
    qp = f"raw/papers/9701_s24_qp_{paper}.pdf"
    ms = f"raw/papers/9701_s24_ms_{paper}.pdf"
    os.makedirs(tagged, exist_ok=True)
    for q, spec in blocks.items():
        marks, topic, codes, los, skills, diff = spec
        qid = f"cie-9701-2024-mj-p{paper}-q{q}"
        rec = {
            "id": qid,
            "exam_board": "CIE",
            "syllabus_code": "9701",
            "level": "AS",
            "year": 2024,
            "session": "MJ",
            "paper": paper,
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
            "source_qp": qp,
            "source_ms": ms,
            "page_qp": None,
            "page_ms": None,
            "body": "",
            "mark_scheme": "",
            "figures": [],
        }
        with open(os.path.join(tagged, f"q{q}.json"), "w") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(blocks)} tagged JSON files to {tagged}")

    syl = yaml.safe_load(open("syllabus/cie-9701-as-a-level-chemistry.yaml"))
    valid_codes, valid_los = set(), set()
    for t in syl["topics"]:
        valid_codes.add(str(t["code"]))
        for st in t["subtopics"]:
            valid_codes.add(str(st["code"]))
            for lo in st["learning_outcomes"]:
                valid_los.add(str(lo["id"]))
    allowed = {"Titrations", "Thermometric experiments", "Gravimetric experiments",
               "Gas volume experiments", "Rate experiments", "Qualitative analysis"}
    bad = []
    for q, spec in blocks.items():
        codes, los, topic = spec[2], spec[3], spec[1]
        if topic not in allowed:
            bad.append((q, "topic", topic))
        for c in codes:
            if c not in valid_codes:
                bad.append((q, "code", c))
        for lo in los:
            if lo not in valid_los:
                bad.append((q, "lo", lo))
    if bad:
        print("INVALID TAGS:", bad)
        sys.exit(1)
    print("Validation OK: codes + LOs + practical_topic all in controlled vocabulary.")


if __name__ == "__main__":
    main()
