#!/usr/bin/env python3
"""Re-tag draft/0620_s25_qp_41 parts by assessed skill (0620 vocabulary)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "draft" / "0620_s25_qp_41"
TAGGED = DRAFT / "tagged"
SYL = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

# stem -> (syllabus_codes, lo_ids, skills, difficulty)
# Tag the command-word skill, not the shared substance list / copper intro.
TAGS: dict[str, tuple[list[str], list[str], list[str], int]] = {
    "1a": (["7.2"], ["7.2-C1"], ["recall"], 2),
    "1b": (["2.6", "2.1"], ["2.6-C1", "2.1-C1"], ["recall"], 2),
    "1c": (["11.6"], ["11.6-C1"], ["recall"], 2),
    "1d": (["10.3"], ["10.3-C2"], ["recall"], 2),
    "1e": (["9.6"], ["9.6-C3"], ["recall"], 2),
    "1f": (["10.3"], ["10.3-C3"], ["recall"], 2),
    "1g": (["11.4", "3.1"], ["11.4-C1", "3.1-C1"], ["recall"], 3),
    "1h-i": (["9.6", "10.3"], ["9.6-C2", "10.3-C1"], ["recall"], 3),
    "1j": (["11.8", "11.5"], ["11.8-C1", "11.5-C1"], ["recall"], 3),
    "2a": (["2.2"], ["2.2-C2"], ["recall"], 2),
    "2b-i": (["2.3", "2.2"], ["2.3-C2", "2.2-C3", "2.2-C4"], ["calculate"], 3),
    "2b-ii": (["2.3"], ["2.3-S4"], ["calculate"], 3),
    "2b-iii": (["2.3", "2.2"], ["2.3-C1", "2.2-C4"], ["explain"], 3),
    "2c": (["2.2"], ["2.2-C5"], ["recall"], 4),
    "3a-i": (["2.7"], ["2.7-S1"], ["explain"], 3),
    "3a-ii": (["2.7"], ["2.7-S2"], ["explain"], 3),
    "3b-i": (["9.3"], ["9.3-C2"], ["recall"], 2),
    "3b-ii": (["9.3"], ["9.3-C1"], ["recall"], 2),
    "3c-i": (["7.1"], ["7.1-C1"], ["recall"], 2),
    "3c-ii": (["7.3"], ["7.3-C1"], ["explain"], 2),
    "3c-iii": (["12.1"], ["12.1-C3"], ["recall"], 2),
    "3c-iv": (["7.3"], ["7.3-C1"], ["recall"], 3),
    "3c-v": (["12.1"], ["12.1-C3"], ["recall"], 2),
    "3c-vi": (["6.2"], ["6.2-S6", "6.2-S5"], ["explain"], 4),
    "3c-vii": (["7.3"], ["7.3-C3"], ["recall"], 2),
    "4a": (["2.5"], ["2.5-S4"], ["draw"], 3),
    "4b-i": (["6.3"], ["6.3-S7"], ["recall"], 2),
    "4b-ii": (["6.3"], ["6.3-S5"], ["recall"], 2),
    "4c-i": (["3.1"], ["3.1-C4"], ["calculate"], 2),
    "4c-ii": (["6.4"], ["6.4-S9"], ["recall"], 3),
    "4c-iii": (["6.4"], ["6.4-S6"], ["recall"], 2),
    "4c-iv": (["3.1"], ["3.1-S8"], ["recall"], 4),
    "4d": (["3.3"], ["3.3-S4", "3.3-S5", "3.3-S3"], ["calculate"], 4),
    "5a": (["6.3"], ["6.3-S3"], ["explain"], 3),
    "5b-i": (["6.3"], ["6.3-S4", "6.3-S11"], ["explain"], 4),
    "5b-ii": (["6.3"], ["6.3-S4"], ["data-analysis"], 4),
    "5c-i": (["11.1"], ["11.1-S9"], ["recall"], 2),
    "5c-ii": (["11.1"], ["11.1-C2"], ["recall"], 3),
    "5d-i": (["11.7", "11.1"], ["11.7-S3", "11.1-C1"], ["draw"], 4),
    "5d-ii": (["11.7", "11.2"], ["11.7-S3", "11.2-S4"], ["recall"], 3),
    "5e": (["3.3", "3.1"], ["3.3-S7", "3.1-S5"], ["calculate"], 4),
    "5g-iii": (["6.3", "5.1"], ["6.3-S4", "5.1-C1"], ["explain"], 4),
    "5g-iv": (["8.4", "6.2"], ["8.4-C1", "6.2-C2"], ["recall"], 3),
    "6a": (["8.3"], ["8.3-C1"], ["recall"], 1),
    "6b": (["8.3"], ["8.3-C1"], ["recall"], 2),
    "6c": (["8.3"], ["8.3-C2"], ["recall"], 2),
    "6d-i": (["8.3", "3.1"], ["8.3-C3", "3.1-S7"], ["recall"], 4),
    "6d-ii": (["5.1"], ["5.1-S8", "5.1-S7"], ["calculate"], 4),
    "6e-i": (["8.2", "9.4"], ["8.2-C1", "9.4-C2"], ["recall"], 2),
    "6e-ii": (["7.1"], ["7.1-C5"], ["recall"], 2),
    # leftover split of the 6(d)(ii) bond-energy working
    "6g": (["5.1"], ["5.1-S8"], ["calculate"], 4),
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
    bad: list[tuple[str, str, str]] = []
    changed = 0
    missing = []
    for stem, (codes, lo_ids, skills, diff) in TAGS.items():
        path = TAGGED / f"q{stem}.json"
        if not path.exists():
            missing.append(stem)
            continue
        for c in codes:
            if c not in code_titles:
                bad.append((stem, "code", c))
        for lo in lo_ids:
            if lo not in lo_texts:
                bad.append((stem, "lo", lo))
        rec = json.loads(path.read_text(encoding="utf-8"))
        rec["syllabus_codes"] = codes
        rec["topic_titles"] = [code_titles[c] for c in codes]
        rec["learning_outcomes"] = lo_ids
        rec["learning_outcome_texts"] = [lo_texts[i] for i in lo_ids]
        rec["skills"] = skills
        rec["difficulty"] = diff
        rec["question_type"] = "structured"
        rec["level"] = "Extended"
        rec["syllabus_code"] = "0620"
        rec.pop("_provisional", None)
        rec["_retag"] = "assessed-skill-2026-08-23"
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed += 1
    extra = sorted(
        p.stem[1:]
        for p in TAGGED.glob("q*.json")
        if p.stem[1:] not in TAGS
    )
    if bad:
        print("INVALID TAGS:", bad)
        return 1
    if missing:
        print("MISSING tagged files:", missing)
        return 1
    print(f"updated {changed} tagged JSON files in {TAGGED}")
    if extra:
        print("untouched extras:", extra)
    print("Validation OK: all codes + LOs are in the 0620 vocabulary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
