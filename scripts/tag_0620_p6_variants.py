#!/usr/bin/env python3
"""Hand-tag remaining IGCSE 0620 P6 ATP experiment blocks (0620 vocabulary)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SYL = ROOT / "syllabus" / "cie-0620-igcse-chemistry.yaml"

# paper_id -> (session, paper, {q: (codes, los, skills, diff, practical_topic)})
PAPERS: dict[
    str, tuple[str, int, dict[int, tuple[list[str], list[str], list[str], int, str]]]
] = {
    "0620_s25_qp_62": (
        "MJ",
        62,
        {
            1: (["12.1", "9.4"], ["12.1-C1", "9.4-C2"], ["recall"], 3, "Gas volume experiments"),
            2: (["5.1"], ["5.1-C2", "5.1-C3"], ["data-analysis"], 3, "Thermometric experiments"),
            3: (["12.5"], ["12.5-C2", "12.5-C1"], ["recall"], 3, "Qualitative analysis"),
            4: (["12.4", "7.3"], ["12.4-C1", "12.1-C3"], ["plan"], 4, "Planning"),
        },
    ),
    "0620_s25_qp_63": (
        "MJ",
        63,
        {
            1: (["11.6", "12.1"], ["11.6-C1", "12.1-C1"], ["data-analysis"], 3, "Gas volume experiments"),
            2: (["6.2"], ["6.2-C1", "6.2-C3", "6.2-C4"], ["data-analysis"], 3, "Rate experiments"),
            3: (["12.5"], ["12.5-C2", "12.5-C1"], ["recall"], 3, "Qualitative analysis"),
            4: (["7.3"], ["7.3-S4", "12.4-C1"], ["plan"], 4, "Planning"),
        },
    ),
    "0620_w25_qp_61": (
        "ON",
        61,
        {
            1: (["12.1", "8.3"], ["12.1-C1", "8.3-C2"], ["recall"], 3, "Gas volume experiments"),
            2: (["12.2"], ["12.2-C1", "12.2-C2"], ["data-analysis"], 3, "Titrations"),
            3: (["12.5"], ["12.5-C4", "12.5-C2"], ["recall"], 3, "Qualitative analysis"),
            4: (["9.4", "5.1"], ["9.4-C3", "5.1-C1"], ["plan"], 4, "Planning"),
        },
    ),
    "0620_w25_qp_62": (
        "ON",
        62,
        {
            1: (["3.3", "7.1"], ["3.3-S8", "7.1-C1"], ["calculate"], 4, "Gravimetric experiments"),
            2: (["12.2"], ["12.2-C1", "12.2-C2"], ["data-analysis"], 3, "Titrations"),
            3: (["12.5"], ["12.5-C3", "12.5-C1"], ["recall"], 3, "Qualitative analysis"),
            4: (["5.1", "11.6"], ["5.1-C1", "11.6-C3"], ["plan"], 4, "Planning"),
        },
    ),
    "0620_w25_qp_63": (
        "ON",
        63,
        {
            1: (["10.1", "12.1"], ["10.1-C1", "12.1-C1"], ["recall"], 3, "Measurement and apparatus"),
            2: (["5.1", "6.2"], ["5.1-C1", "6.2-C3"], ["data-analysis"], 3, "Thermometric experiments"),
            3: (["12.5"], ["12.5-C2", "12.5-C1"], ["recall"], 3, "Qualitative analysis"),
            4: (["12.4", "9.4"], ["12.4-C2", "9.4-C2"], ["plan"], 4, "Planning"),
        },
    ),
    "0620_m25_qp_62": (
        "FM",
        62,
        {
            1: (["12.3"], ["12.3-C1", "12.3-C2"], ["data-analysis"], 3, "Chromatography"),
            2: (["5.1", "9.4"], ["5.1-C1", "9.4-C3"], ["data-analysis"], 3, "Thermometric experiments"),
            3: (["12.5"], ["12.5-C2"], ["recall"], 3, "Qualitative analysis"),
            4: (["4.1"], ["4.1-C6", "4.1-C7"], ["plan"], 4, "Planning"),
        },
    ),
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


def tag_paper(
    paper_id: str,
    session: str,
    paper: int,
    tags: dict[int, tuple[list[str], list[str], list[str], int, str]],
    code_titles: dict[str, str],
    lo_texts: dict[str, str],
) -> int:
    draft = ROOT / "draft" / paper_id
    tagged = draft / "tagged"
    tagged.mkdir(parents=True, exist_ok=True)
    season = {"MJ": "s25", "ON": "w25", "FM": "m25"}[session]
    qp = f"raw/papers/{paper_id}.pdf"
    ms = f"raw/papers/0620_{season}_ms_{paper}.pdf"
    sess_slug = session.lower()
    idx = {str(r["question"]): r for r in json.loads((draft / "index.json").read_text())}
    bad: list[tuple[int, str, str]] = []
    for q, (codes, lo_ids, skills, diff, topic) in tags.items():
        for c in codes:
            if c not in code_titles:
                bad.append((q, "code", c))
        for lo in lo_ids:
            if lo not in lo_texts:
                bad.append((q, "lo", lo))
        raw = (draft / f"q{q}.txt").read_text(encoding="utf-8")
        if "\n--- MARK SCHEME ---" in raw:
            body, ms_text = raw.split("\n--- MARK SCHEME ---", 1)
        else:
            body, ms_text = raw, ""
        rec = {
            "id": f"cie-0620-2025-{sess_slug}-p{paper}-q{q}",
            "exam_board": "CIE",
            "syllabus_code": "0620",
            "level": "Extended",
            "year": 2025,
            "session": session,
            "paper": paper,
            "question": str(q),
            "marks": None,
            "syllabus_codes": codes,
            "topic_titles": [code_titles[c] for c in codes],
            "skills": skills,
            "question_type": "practical",
            "difficulty": diff,
            "command_words": [],
            "misconceptions": [],
            "learning_outcomes": lo_ids,
            "learning_outcome_texts": [lo_texts[i] for i in lo_ids],
            "learning_objectives": [],
            "ms_answer": None,
            "source_qp": qp,
            "source_ms": ms,
            "page_qp": (idx.get(str(q)) or {}).get("page_hint"),
            "body": body.strip(),
            "mark_scheme": ms_text.strip(),
            "practical_topic": topic,
            "_provisional": False,
        }
        (tagged / f"q{q}.json").write_text(
            json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if bad:
        print(f"INVALID TAGS {paper_id}:", bad)
        return 1
    print(f"{paper_id}: wrote {len(tags)} tagged JSON blocks")
    return 0


def main(argv: list[str]) -> int:
    wanted = argv[1:] or list(PAPERS)
    code_titles, lo_texts = load_vocab()
    rc = 0
    for paper_id in wanted:
        if paper_id not in PAPERS:
            print("unknown", paper_id)
            return 1
        session, paper, tags = PAPERS[paper_id]
        rc |= tag_paper(paper_id, session, paper, tags, code_titles, lo_texts)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
