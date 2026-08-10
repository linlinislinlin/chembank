#!/usr/bin/env python3
"""Generate tagged/q*.json for draft/9701_s24_qp_41 (Paper 4 structured, A Level) by hand."""
import json
import os
import sys

import yaml

PAPER_ID = "9701_s24_qp_41"
DRAFT = os.path.join("draft", PAPER_ID)
TAGGED = os.path.join(DRAFT, "tagged")
QP = "raw/papers/9701_s24_qp_41.pdf"
MS = "raw/papers/9701_s24_ms_41.pdf"

LEV = {"level": "AL", "session": "MJ", "year": 2024, "paper": 41}

# slug -> (question, parent, part, marks, codes, los, skills, diff, command)
PARTS = {
 # Q1 Group 2 + Ksp
 "1a-i": ("1(a)(i)", "1", "(a)(i)", 3, ["27"], ["27.1-2"], ["describe", "explain"], 3, ["Describe", "Explain"]),
 "1a-ii": ("1(a)(ii)", "1", "(a)(ii)", 2, ["27", "25"], ["27.1-2", "25.1-4b"], ["suggest", "explain"], 4, ["Suggest", "Explain"]),
 "1b": ("1(b)", "1", "(b)", 4, ["25", "2"], ["25.1-4b", "25.1-4a", "2.2-1"], ["calculate"], 4, ["Calculate"]),
 "1c-i": ("1(c)(i)", "1", "(c)(i)", 1, ["25"], ["25.1-7", "25.1-8"], ["write"], 3, ["Write"]),
 "1c-ii": ("1(c)(ii)", "1", "(c)(ii)", 2, ["25"], ["25.1-9"], ["calculate"], 4, ["Calculate"]),
 # Q2 transition + complex + electrochem
 "2a-i": ("2(a)(i)", "2", "(a)(i)", 1, ["28"], ["28.1-1"], ["recall"], 3, ["Define"]),
 "2a-ii": ("2(a)(ii)", "2", "(a)(ii)", 1, ["28"], ["28.1-6"], ["explain"], 3, ["Explain"]),
 "2b-i": ("2(b)(i)", "2", "(b)(i)", 1, ["28"], ["28.3-1"], ["define"], 3, ["Define"]),
 "2b-ii": ("2(b)(ii)", "2", "(b)(ii)", 1, ["28"], ["28.1-2"], ["draw", "sketch"], 3, ["Sketch"]),
 "2c": ("2(c)", "2", "(c)", 2, ["28", "24"], ["28.2-1", "24.2-7"], ["construct"], 4, ["Construct"]),
 "2d": ("2(d)", "2", "(d)", 2, ["28"], ["28.2-5", "28.2-3a"], ["state", "recall"], 4, ["State"]),
 "2e": ("2(e)", "2", "(e)", 2, ["24"], ["24.2-7", "24.2-5a"], ["construct"], 4, ["Complete"]),
 "2f": ("2(f)", "2", "(f)", 3, ["28"], ["28.2-4", "28.2-3b", "28.2-6b"], ["draw", "apply"], 5, ["Complete"]),
 # Q3 Group 2 + colour + buffer + fuel cell
 "3a": ("3(a)", "3", "(a)", 1, ["27", "2"], ["27.1-1", "2.3-2a"], ["construct"], 3, ["Complete"]),
 "3b": ("3(b)", "3", "(b)", 2, ["27"], ["27.1-1"], ["suggest", "explain"], 4, ["Suggest", "Explain"]),
 "3c": ("3(c)", "3", "(c)", 3, ["28"], ["28.3-3", "28.3-2a"], ["explain"], 4, ["Explain"]),
 "3d": ("3(d)", "3", "(d)", 1, ["28", "6"], ["28.2-10", "6.1-2"], ["complete"], 3, ["Complete"]),
 "3e": ("3(e)", "3", "(e)", 2, ["28"], ["28.4-1a", "28.4-1b"], ["draw", "complete"], 5, ["Complete"]),
 "3f": ("3(f)", "3", "(f)", 2, ["25"], ["25.1-5c", "25.1-5b"], ["construct"], 4, ["Write"]),
 "3g": ("3(g)", "3", "(g)", 2, ["24"], ["24.2-7", "24.2-4", "24.2-1b"], ["construct", "calculate"], 5, ["Deduce", "Calculate"]),
 # Q4 electrochem + lattice
 "4a": ("4(a)", "4", "(a)", 2, ["24"], ["24.2-1a", "24.2-2"], ["define"], 3, ["Define"]),
 "4b-i": ("4(b)(i)", "4", "(b)(i)", 3, ["24"], ["24.2-3b", "24.2-2"], ["draw", "apply"], 4, ["Draw"]),
 "4b-ii": ("4(b)(ii)", "4", "(b)(ii)", 2, ["24"], ["24.2-8"], ["suggest", "explain"], 4, ["Suggest", "Explain"]),
 "4c": ("4(c)", "4", "(c)", 1, ["23"], ["23.2-1"], ["define"], 3, ["Define"]),
 "4d-i": ("4(d)(i)", "4", "(d)(i)", 2, ["23"], ["23.2-2", "23.1-1b"], ["complete", "apply"], 4, ["Complete"]),
 "4d-ii": ("4(d)(ii)", "4", "(d)(ii)", 1, ["23"], ["23.2-3"], ["calculate"], 4, ["Calculate"]),
 "4e": ("4(e)", "4", "(e)", 2, ["23"], ["23.1-5", "23.2-4"], ["suggest", "explain"], 4, ["Suggest", "Explain"]),
 # Q5 kinetics
 "5a-i": ("5(a)(i)", "5", "(a)(i)", 2, ["26"], ["26.1-2b", "26.1-2c", "26.1-2d"], ["read", "calculate"], 4, ["Deduce"]),
 "5a-ii": ("5(a)(ii)", "5", "(a)(ii)", 2, ["26"], ["26.1-2b", "26.1-2d", "26.1-4a"], ["calculate"], 4, ["Calculate"]),
 "5b": ("5(b)", "5", "(b)", 2, ["26", "28"], ["26.1-5d", "26.2-3a", "28.1-5"], ["construct"], 4, ["Write"]),
 "5c": ("5(c)", "5", "(c)", 1, ["26"], ["26.1-6"], ["describe"], 3, ["Describe"]),
 "5d": ("5(d)", "5", "(d)", 1, ["26"], ["26.1-3a", "26.1-3b"], ["calculate"], 4, ["Calculate"]),
 "5e": ("5(e)", "5", "(e)", 3, ["26"], ["26.1-5a", "26.1-5e", "26.1-5b"], ["suggest", "state"], 5, ["Suggest", "State"]),
 # Q6 partition + benzene + NMR + Friedel-Crafts
 "6a-i": ("6(a)(i)", "6", "(a)(i)", 1, ["25"], ["25.2-1"], ["state"], 3, ["State"]),
 "6a-ii": ("6(a)(ii)", "6", "(a)(ii)", 2, ["25"], ["25.2-2", "2.2-1"], ["calculate"], 4, ["Calculate"]),
 "6b": ("6(b)", "6", "(b)", 3, ["29", "30"], ["29.3-1", "13.3-2"], ["predict", "complete"], 5, ["Complete"]),
 "6c": ("6(c)", "6", "(c)", 2, ["30", "29"], ["30.1-4", "29.3-1"], ["describe"], 4, ["Describe"]),
 "6d": ("6(d)", "6", "(d)", 1, ["30"], ["29.3-1"], ["suggest"], 3, ["Suggest"]),
 "6e": ("6(e)", "6", "(e)", 1, ["37"], ["37.4-2", "37.4-1a"], ["predict", "complete"], 4, ["Complete"]),
 "6f-i": ("6(f)(i)", "6", "(f)(i)", 2, ["30"], ["30.1-1a", "30.1-2b"], ["deduce", "construct"], 5, ["Deduce"]),
 "6f-ii": ("6(f)(ii)", "6", "(f)(ii)", 2, ["30"], ["30.1-1a", "30.1-3"], ["explain", "state"], 5, ["Explain"]),
 "6f-iii": ("6(f)(iii)", "6", "(f)(iii)", 2, ["30"], ["30.1-1a"], ["deduce"], 4, ["Deduce"]),
 # Q7 esters + GLC + NMR
 "7a": ("7(a)", "7", "(a)", 1, ["33", "29"], ["33.2-1a", "29.1-3"], ["name"], 3, ["Name"]),
 "7b-i": ("7(b)(i)", "7", "(b)(i)", 2, ["37", "33"], ["37.2-1c", "37.2-2"], ["interpret", "use"], 4, ["Use"]),
 "7b-ii": ("7(b)(ii)", "7", "(b)(ii)", 2, ["37"], ["37.2-3", "37.1-3"], ["explain"], 4, ["Explain"]),
 "7c-i": ("7(c)(i)", "7", "(c)(i)", 2, ["37", "33"], ["37.4-2", "37.4-1a"], ["predict"], 5, ["Predict"]),
 "7c-ii": ("7(c)(ii)", "7", "(c)(ii)", 2, ["37"], ["37.4-2", "37.4-1a"], ["deduce"], 5, ["Deduce"]),
 "7d": ("7(d)", "7", "(d)", 7, ["37", "33", "13"], ["37.4-1a", "37.4-1c", "33.2-1a", "29.1-3", "13.4-2"], ["deduce", "construct"], 5, ["Deduce", "Explain"]),
 # Q8 neotame (amino acids / peptides)
 "8a-i": ("8(a)(i)", "8", "(a)(i)", 2, ["34", "35"], ["34.4-2", "35.1-2c"], ["identify", "draw"], 5, ["Identify"]),
 "8a-ii": ("8(a)(ii)", "8", "(a)(ii)", 2, ["34"], ["34.4-1", "29.1-3"], ["state", "name"], 4, ["State"]),
 "8b-i": ("8(b)(i)", "8", "(b)(i)", 2, ["34"], ["34.4-3"], ["interpret", "suggest"], 5, ["Suggest"]),
 "8b-ii": ("8(b)(ii)", "8", "(b)(ii)", 2, ["34", "37"], ["34.4-2", "37.4-1a"], ["deduce"], 5, ["Deduce"]),
 # Q9 phenol + salicylic acid + Diels-Alder
 "9a-i": ("9(a)(i)", "9", "(a)(i)", 1, ["32"], ["32.2-2a", "32.2-3"], ["construct"], 3, ["Write"]),
 "9a-ii": ("9(a)(ii)", "9", "(a)(ii)", 3, ["32", "30"], ["32.2-2b", "30.1-1c"], ["draw"], 4, ["Draw"]),
 "9b": ("9(b)", "9", "(b)", 7, ["32", "33", "37"], ["32.2-7", "33.1-4", "32.2-3", "37.4-2"], ["deduce", "explain"], 5, ["Deduce", "Explain"]),
 "9c-i": ("9(c)(i)", "9", "(c)(i)", 2, ["36", "29"], ["36.1-2", "29.2-1b"], ["draw", "complete"], 5, ["Complete"]),
 "9c-ii": ("9(c)(ii)", "9", "(c)(ii)", 1, ["36", "29"], ["36.1-2", "29.2-1b"], ["predict", "draw"], 4, ["Predict"]),
}

def main():
    os.makedirs(TAGGED, exist_ok=True)
    for slug, spec in PARTS.items():
        question, parent, part, marks, codes, los, skills, diff = spec[:8]
        command_words = spec[8] if len(spec) > 8 else []
        qid = f"cie-9701-2024-mj-p41-q{slug}"
        rec = {
            "id": qid,
            "exam_board": "CIE",
            "syllabus_code": "9701",
            "level": LEV["level"],
            "year": LEV["year"],
            "session": LEV["session"],
            "paper": LEV["paper"],
            "question": question,
            "parent_question": parent,
            "part": part,
            "marks": marks,
            "syllabus_codes": codes,
            "topic_titles": [],
            "skills": skills,
            "question_type": "structured",
            "difficulty": diff,
            "command_words": command_words,
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
        with open(os.path.join(TAGGED, f"q{slug}.json"), "w") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(PARTS)} tagged JSON files to {TAGGED}")

    syl = yaml.safe_load(open("syllabus/cie-9701-as-a-level-chemistry.yaml"))
    valid_codes, valid_los = set(), set()
    for t in syl["topics"]:
        valid_codes.add(str(t["code"]))
        for st in t["subtopics"]:
            valid_codes.add(str(st["code"]))
            for lo in st["learning_outcomes"]:
                valid_los.add(str(lo["id"]))
    bad = []
    for slug, spec in PARTS.items():
        for c in spec[4]:
            if c not in valid_codes:
                bad.append((slug, "code", c))
        for lo in spec[5]:
            if lo not in valid_los:
                bad.append((slug, "lo", lo))
    if bad:
        print("INVALID TAGS:", bad)
        sys.exit(1)
    print("Validation OK: all codes + LOs are in the controlled vocabulary.")


if __name__ == "__main__":
    main()
