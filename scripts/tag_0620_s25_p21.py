#!/usr/bin/env python3
"""Hand-tag draft/0620_s25_qp_21 (IGCSE Extended P2 MCQ) from 0620 vocabulary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAPER_ID = "0620_s25_qp_21"
DRAFT = ROOT / "draft" / PAPER_ID
TAGGED = DRAFT / "tagged"
QP = "raw/papers/0620_s25_qp_21.pdf"
MS = "raw/papers/0620_s25_ms_21.pdf"
SYL = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

# question -> (syllabus_codes, lo_ids, skills, difficulty)
# Assessed skill, not decorative context.
TAGS: dict[int, tuple[list[str], list[str], list[str], int]] = {
    1: (["1.1"], ["1.1-S6", "1.1-C2"], ["explain"], 3),
    2: (["1.1"], ["1.1-S5", "1.1-C3"], ["data-analysis"], 3),
    3: (["2.2"], ["2.2-C3", "2.2-C4"], ["recall"], 2),
    4: (["2.3"], ["2.3-S4"], ["calculate"], 4),
    5: (["2.4"], ["2.4-C4", "2.4-S7"], ["explain"], 3),
    6: (["2.5"], ["2.5-S4"], ["recall"], 3),
    7: (["2.6"], ["2.6-S3", "2.6-S4"], ["compare"], 3),
    8: (["3.1", "3.3"], ["3.1-S5", "3.3-S7"], ["calculate"], 3),
    9: (["3.3"], ["3.3-S5", "3.3-S4"], ["calculate"], 4),
    10: (["4.1"], ["4.1-C7", "4.1-C6"], ["recall"], 2),
    11: (["4.1"], ["4.1-S11", "4.1-C3"], ["recall"], 4),
    12: (["4.2"], ["4.2-C1"], ["recall"], 2),
    13: (["5.1"], ["5.1-C1", "5.1-C3"], ["data-analysis"], 3),
    14: (["6.3", "11.7"], ["6.3-C1", "11.7-S3"], ["recall"], 3),
    15: (["6.2"], ["6.2-C3", "6.2-S5"], ["data-analysis"], 3),
    16: (["6.3"], ["6.3-S11", "6.3-S7"], ["explain"], 4),
    17: (["11.6", "6.4"], ["11.6-S4", "6.4-S10"], ["recall"], 3),
    18: (["7.1"], ["7.1-S10"], ["compare"], 4),
    19: (["7.3"], ["7.3-S4", "7.3-S5"], ["recall"], 3),
    20: (["3.1"], ["3.1-C1"], ["recall"], 2),
    21: (["8.1"], ["8.1-C4", "8.1-C5"], ["recall"], 2),
    22: (["8.3"], ["8.3-C2"], ["recall"], 2),
    23: (["8.4", "8.2"], ["8.4-C1", "8.4-S2"], ["compare"], 4),
    24: (["8.5"], ["8.5-C1"], ["explain"], 3),
    25: (["9.2"], ["9.2-C1"], ["recall"], 2),
    26: (["9.4"], ["9.4-C1", "9.4-C3"], ["recall"], 3),
    27: (["9.4"], ["9.4-C2", "9.4-S4"], ["data-analysis"], 3),
    28: (["9.6"], ["9.6-C2"], ["recall"], 2),
    29: (["9.5"], ["9.5-S4", "9.5-S5"], ["explain"], 3),
    30: (["10.2"], ["10.2-C1"], ["recall"], 2),
    31: (["10.3"], ["10.3-S7"], ["explain"], 4),
    32: (["10.3"], ["10.3-S8"], ["recall"], 2),
    33: (["11.1"], ["11.1-S8"], ["compare"], 4),
    34: (["11.4", "2.5"], ["11.4-C1", "2.5-C1"], ["recall"], 3),
    35: (["11.6"], ["11.6-C2", "11.6-C3"], ["compare"], 3),
    36: (["11.7", "11.1"], ["11.7-C1", "11.1-C3"], ["recall"], 3),
    37: (["11.8"], ["11.8-S8"], ["recall"], 4),
    38: (["12.1", "12.2"], ["12.1-C1", "12.2-C1"], ["recall"], 2),
    39: (["12.4"], ["12.4-C2"], ["recall"], 2),
    40: (["12.3"], ["12.3-C2", "12.3-S3"], ["explain"], 3),
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
        for marker in ("The Periodic Table", "Important values"):
            if marker in body:
                body = body.split(marker)[0].strip()
        ans = str(ms_key[str(q)])
        qid = f"cie-0620-2025-mj-p21-q{q}"
        rec = {
            "id": qid,
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2025,
            "session": "MJ",
            "paper": 21,
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
    print(f"wrote {len(TAGS)} tagged JSON files to {TAGGED}")
    print("Validation OK: all codes + LOs are in the 0620 vocabulary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
