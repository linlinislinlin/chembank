#!/usr/bin/env python3
"""Hand-tag draft/0620_m25_qp_22 (IGCSE Extended P2 MCQ) from 0620 vocabulary.

Assessed skill, not decorative context. Session FM (March).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAPER_ID = "0620_m25_qp_22"
DRAFT = ROOT / "draft" / PAPER_ID
TAGGED = DRAFT / "tagged"
QP = "raw/papers/0620_m25_qp_22.pdf"
MS = "raw/papers/0620_m25_ms_22.pdf"
SYL = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

# question -> (syllabus_codes, lo_ids, skills, difficulty)
# ER: easiest 1,5,6,7,9,18,19,21,25,30; most demanding 12,24,32,36.
TAGS: dict[int, tuple[list[str], list[str], list[str], int]] = {
    1: (["1.1"], ["1.1-C4", "1.1-S6"], ["explain"], 2),
    2: (["1.1"], ["1.1-S5", "1.1-C2"], ["data-analysis"], 3),
    3: (["1.2"], ["1.2-S2", "1.2-C1"], ["explain"], 3),
    4: (["2.2"], ["2.2-C5"], ["recall"], 3),
    5: (["2.3"], ["2.3-S3", "2.3-C1"], ["recall"], 2),
    6: (["2.4"], ["2.4-S6", "2.4-C1"], ["explain"], 2),
    7: (["2.5"], ["2.5-C2"], ["recall"], 2),
    8: (["2.7"], ["2.7-S1"], ["recall"], 3),
    9: (["3.1"], ["3.1-C1"], ["recall"], 2),
    10: (["3.3"], ["3.3-S5", "3.3-S3"], ["calculate"], 4),
    11: (["3.3", "3.1"], ["3.3-S7", "3.1-S5"], ["calculate"], 4),
    12: (["3.3"], ["3.3-S3", "3.3-S2"], ["calculate"], 5),
    13: (["4.1"], ["4.1-S10", "4.1-C3"], ["recall"], 4),
    14: (["4.1"], ["4.1-S11", "4.1-C3"], ["recall"], 4),
    15: (["4.2"], ["4.2-C1", "4.2-S2"], ["recall"], 3),
    16: (["5.1"], ["5.1-C3", "5.1-S4"], ["data-analysis"], 3),
    17: (["5.1"], ["5.1-S8", "5.1-S7"], ["calculate"], 4),
    18: (["6.1"], ["6.1-C1"], ["recall"], 2),
    19: (["6.2"], ["6.2-S5", "6.2-S6"], ["explain"], 2),
    20: (["6.3"], ["6.3-S4"], ["explain"], 4),
    21: (["6.4"], ["6.4-C3", "6.4-C4"], ["recall"], 2),
    22: (["7.1"], ["7.1-S10", "7.1-S12"], ["compare"], 3),
    23: (["7.2"], ["7.2-C1"], ["recall"], 3),
    24: (["7.3"], ["7.3-S4", "7.3-C2"], ["recall"], 5),
    25: (["8.1", "2.5"], ["8.1-C4", "2.5-C3"], ["recall"], 2),
    26: (["8.3"], ["8.3-C4", "8.3-C1"], ["recall"], 3),
    27: (["9.5"], ["9.5-S5", "9.5-S4"], ["explain"], 3),
    28: (["9.3"], ["9.3-S5", "9.3-C1"], ["explain"], 3),
    29: (["9.4"], ["9.4-S5"], ["explain"], 3),
    30: (["9.6"], ["9.6-S4", "9.6-C2"], ["recall"], 2),
    31: (["10.1"], ["10.1-C1", "10.1-C2"], ["recall"], 3),
    32: (["10.1"], ["10.1-C7"], ["recall"], 5),
    33: (["10.3"], ["10.3-C1"], ["calculate"], 3),
    34: (["10.3", "6.4"], ["10.3-S8", "6.4-C5"], ["explain"], 4),
    35: (["11.7", "11.1"], ["11.7-S2", "11.1-C4"], ["recall"], 3),
    36: (["11.1", "11.4"], ["11.1-S8", "11.4-S4"], ["recall"], 5),
    37: (["11.6"], ["11.6-S4", "11.6-C1"], ["compare"], 3),
    38: (["11.8"], ["11.8-S9", "11.8-S10"], ["recall"], 3),
    39: (["12.5"], ["12.5-C2"], ["recall"], 3),
    40: (["12.3"], ["12.3-S4", "12.3-C1"], ["recall"], 2),
}


def load_vocab() -> tuple[dict[str, str], dict[str, str]]:
    syl = yaml.safe_load(SYL.read_text(encoding="utf-8"))
    codes: dict[str, str] = {}
    los: dict[str, str] = {}
    for t in syl["topics"]:
        codes[str(t["code"])] = str(t["title"])
        for st in t.get("subtopics") or []:
            codes[str(st["code"])] = str(st["title"])
            for lo in st.get("learning_outcomes") or []:
                los[str(lo["id"])] = str(lo["text"])
    return codes, los


def main() -> int:
    code_titles, lo_texts = load_vocab()
    ms_key = json.loads((DRAFT / "ms_key.json").read_text(encoding="utf-8"))
    TAGGED.mkdir(parents=True, exist_ok=True)
    bad: list[tuple[int, str, str]] = []
    for q, (codes, lo_ids, skills, diff) in TAGS.items():
        for c in codes:
            if c not in code_titles:
                bad.append((q, "code", c))
        for lo in lo_ids:
            if lo not in lo_texts:
                bad.append((q, "lo", lo))
        body = (DRAFT / f"q{q}.txt").read_text(encoding="utf-8")
        if "\n--- MARK SCHEME ---" in body:
            body = body.split("\n--- MARK SCHEME ---", 1)[0].strip()
        for marker in ("The Periodic Table", "Important values", "reasonable effort has been made"):
            if marker in body:
                body = body.split(marker)[0].strip()
        ans = str(ms_key[str(q)])
        if ans not in "ABCD":
            print(f"q{q}: bad ms letter {ans!r}")
            return 1
        rec = {
            "id": f"cie-0620-2025-fm-p22-q{q}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2025,
            "session": "FM",
            "paper": 22,
            "question": str(q),
            "marks": 1,
            "syllabus_codes": codes,
            "topic_titles": [code_titles[c] for c in codes],
            "skills": skills,
            "question_type": "mcq",
            "difficulty": diff,
            "command_words": [],
            "misconceptions": [],
            "learning_outcomes": lo_ids,
            "learning_outcome_texts": [lo_texts[i] for i in lo_ids],
            "learning_objectives": [],
            "ms_answer": ans,
            "source_qp": QP,
            "source_ms": MS,
            "page_qp": None,
            "body": body,
            "mark_scheme": f"Answer: **{ans}**",
        }
        (TAGGED / f"q{q}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if bad:
        print("INVALID TAGS:", bad)
        return 1
    letters = "".join(ms_key[str(i)] for i in range(1, 41))
    print(f"wrote {len(TAGS)} tagged JSON files to {TAGGED}")
    print("ms_key:", letters)
    print("Validation OK: all codes + LOs are in the 0620 vocabulary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
