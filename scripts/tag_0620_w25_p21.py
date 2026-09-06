#!/usr/bin/env python3
"""Hand-tag draft/0620_w25_qp_21 (IGCSE Extended P2 MCQ) from 0620 vocabulary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAPER_ID = "0620_w25_qp_21"
DRAFT = ROOT / "draft" / PAPER_ID
TAGGED = DRAFT / "tagged"
QP = "raw/papers/0620_w25_qp_21.pdf"
MS = "raw/papers/0620_w25_ms_21.pdf"
SYL = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

# question -> (syllabus_codes, lo_ids, skills, difficulty)
# Assessed skill, not decorative context. Session ON (w25).
TAGS: dict[int, tuple[list[str], list[str], list[str], int]] = {
    1: (["1.1"], ["1.1-S6", "1.1-C4"], ["explain"], 3),
    2: (["1.2"], ["1.2-S2", "1.2-C1"], ["explain"], 4),
    3: (["2.2"], ["2.2-C3", "2.2-C4", "2.2-C2"], ["calculate"], 3),
    4: (["2.6"], ["2.6-C2", "2.6-C1"], ["compare"], 3),
    5: (["2.3", "2.2"], ["2.3-C2", "2.2-C4"], ["calculate"], 4),
    6: (["2.4"], ["2.4-C3", "2.4-C1"], ["recall"], 2),
    7: (["2.7"], ["2.7-S2", "2.7-S1"], ["explain"], 3),
    8: (["3.3"], ["3.3-S5", "3.3-S6"], ["calculate"], 4),
    9: (["3.1", "3.3"], ["3.1-S5", "3.3-S7"], ["compare"], 3),
    10: (["3.3"], ["3.3-S5"], ["calculate"], 4),
    11: (["3.3"], ["3.3-S2"], ["recall"], 2),
    12: (["4.1"], ["4.1-S9"], ["recall"], 4),
    13: (["4.1"], ["4.1-S10", "4.1-S11"], ["recall"], 4),
    14: (["5.1"], ["5.1-S4", "5.1-C1", "5.1-C2"], ["compare"], 3),
    15: (["5.1"], ["5.1-C3", "5.1-S6"], ["data-analysis"], 3),
    16: (["6.2", "8.4"], ["6.2-C2", "8.4-C1"], ["data-analysis"], 3),
    17: (["6.3"], ["6.3-S8"], ["recall"], 2),
    18: (["6.4"], ["6.4-S9", "6.4-S6"], ["calculate"], 4),
    19: (["6.3"], ["6.3-S4", "6.3-S11"], ["explain"], 4),
    20: (["7.1"], ["7.1-S10", "7.1-S12"], ["recall"], 3),
    21: (["7.3"], ["7.3-C2"], ["data-analysis"], 3),
    22: (["7.2"], ["7.2-S3", "7.2-S2"], ["recall"], 3),
    23: (["8.1"], ["8.1-C3", "8.1-C5"], ["recall"], 3),
    24: (["8.2"], ["8.2-C1"], ["compare"], 2),
    25: (["8.3"], ["8.3-C3"], ["recall"], 3),
    26: (["9.4"], ["9.4-C1"], ["recall"], 2),
    27: (["9.4", "6.4"], ["9.4-S4", "6.4-S13"], ["explain"], 4),
    28: (["9.5"], ["9.5-C2", "9.5-C3"], ["recall"], 2),
    29: (["9.6"], ["9.6-S5"], ["recall"], 4),
    30: (["10.3"], ["10.3-S8", "10.3-C3"], ["explain"], 3),
    31: (["10.3"], ["10.3-C1", "10.3-C2"], ["recall"], 2),
    32: (["11.3"], ["11.3-C7", "11.3-C5"], ["recall"], 3),
    33: (["11.1", "11.2"], ["11.1-C3", "11.2-C2"], ["recall"], 3),
    34: (["11.4"], ["11.4-S3", "11.4-S4"], ["recall"], 3),
    35: (["11.8"], ["11.8-S7", "11.8-C2"], ["recall"], 4),
    36: (["11.5"], ["11.5-S6"], ["recall"], 2),
    37: (["11.7"], ["11.7-S2"], ["recall"], 3),
    38: (["11.8"], ["11.8-S9", "11.8-S12"], ["compare"], 4),
    39: (["12.5"], ["12.5-C4"], ["recall"], 2),
    40: (["12.4", "11.6"], ["12.4-C2", "11.6-C1"], ["recall"], 2),
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
        qid = f"cie-0620-2025-on-p21-q{q}"
        rec = {
            "id": qid,
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2025,
            "session": "ON",
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
    letters = [ms_key[str(i)] for i in range(1, 41)]
    if any(x not in "ABCD" for x in letters) or len(ms_key) != 40:
        print("MS key incomplete", ms_key)
        return 1
    print(f"wrote {len(TAGS)} tagged JSON files to {TAGGED}")
    print("ms_key:", "".join(letters))
    print("Validation OK: all codes + LOs are in the 0620 vocabulary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
