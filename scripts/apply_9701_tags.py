#!/usr/bin/env python3
"""Write ChemBank tagged JSON from an explicit per-question tag map.

Used by ingest skills: codes + LOs must come from the 9701 wordlist.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chembank.registry import paper_kind
from chembank.syllabus import (
    as_only_codes,
    flatten_codes,
    flatten_learning_outcomes,
    list_codes,
    load_syllabus,
    parent_code_for_lo,
    resolve_titles,
    validate_learning_outcomes,
)
from chembank.tag import (
    ALLOWED_SKILLS,
    ALLOWED_QUESTION_TYPES,
    _load_index,
    _load_ms_key,
    infer_paper_meta_from_name,
    iter_draft_questions,
)


def _strip_ms_section(text: str) -> tuple[str, str | None]:
    m = re.search(r"(?m)^---\s*MARK SCHEME\s*---\s*$", text)
    if not m:
        return text.strip(), None
    return text[: m.start()].strip(), text[m.end() :].strip() or None


def _slug_to_question_label(slug: str, index: dict) -> tuple[str, str | None, str | None]:
    row = index.get(slug) or index.get(f"q{slug}.txt") or {}
    label = str(row.get("question") or slug)
    parent = row.get("parent_question")
    part = row.get("part")
    if parent is None and "(" in label:
        parent = label.split("(", 1)[0]
        part = "(" + label.split("(", 1)[1]
    return label, (str(parent) if parent else None), (str(part) if part else None)


def apply_tags(draft_dir: Path, tag_map: dict[str, dict], *, as_only: bool | None = None) -> int:
    draft_dir = Path(draft_dir)
    meta = infer_paper_meta_from_name(draft_dir.name)
    kind = paper_kind(meta.paper or 0, str(meta.syllabus_code))
    if as_only is None:
        as_only = kind == "mcq" or (kind == "structured" and int(str(meta.paper)[0]) == 2)
    syllabus = load_syllabus()
    vocab = as_only_codes() if as_only else list_codes()
    allowed = {c for c, _ in vocab}
    all_titles = flatten_codes(syllabus)
    lo_lookup = flatten_learning_outcomes(syllabus)

    ms_key = _load_ms_key(draft_dir)
    index = _load_index(draft_dir)
    out_dir = draft_dir / "tagged"
    out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    missing = []
    for slug, path in iter_draft_questions(draft_dir):
        spec = tag_map.get(slug) or tag_map.get(str(int(slug)) if slug.isdigit() else slug)
        if spec is None:
            missing.append(slug)
            continue
        body, embedded_ms = _strip_ms_section(path.read_text(encoding="utf-8"))
        idx = index.get(slug) or index.get(path.name) or {}
        label, parent, part = _slug_to_question_label(slug, index)

        codes = [str(c) for c in (spec.get("syllabus_codes") or [])]
        los = [str(x) for x in (spec.get("learning_outcomes") or [])]
        if not los and kind != "practical":
            raise SystemExit(f"{draft_dir.name} q{slug}: empty learning_outcomes")
        if los:
            los = validate_learning_outcomes(los, syllabus=syllabus, allowed=set(lo_lookup))
        for lo_id in los:
            parent_code = parent_code_for_lo(lo_id)
            if parent_code not in codes and parent_code.split(".")[0] not in codes:
                if parent_code in allowed or parent_code in all_titles:
                    codes.append(parent_code)
        for c in codes:
            if c not in allowed and c not in all_titles:
                raise SystemExit(f"{draft_dir.name} q{slug}: unknown code {c}")

        skills = [s for s in (spec.get("skills") or []) if s in ALLOWED_SKILLS]
        qtype = spec.get("question_type") or kind
        if qtype not in ALLOWED_QUESTION_TYPES:
            qtype = kind if kind in ALLOWED_QUESTION_TYPES else "structured"

        ms_answer = spec.get("ms_answer") or ms_key.get(slug) or idx.get("ms_answer") or embedded_ms
        if isinstance(ms_answer, str) and not ms_answer.strip():
            ms_answer = None

        record = {
            "id": meta.question_id(slug if not slug.isdigit() else str(int(slug))),
            "exam_board": "CIE",
            "syllabus_code": "9701",
            "level": meta.level,
            "year": meta.year,
            "session": meta.session,
            "paper": meta.paper,
            "question": label if not slug.isdigit() else str(int(slug)),
            "marks": spec.get("marks", 1 if qtype == "mcq" else idx.get("marks")),
            "syllabus_codes": codes,
            "topic_titles": [all_titles[c] for c in codes if c in all_titles],
            "skills": skills,
            "question_type": qtype,
            "difficulty": int(spec.get("difficulty") or 3),
            "command_words": spec.get("command_words") or [],
            "misconceptions": [],
            "learning_outcomes": los,
            "learning_outcome_texts": [lo_lookup[i] for i in los],
            "learning_objectives": spec.get("learning_objectives") or [],
            "ms_answer": ms_answer,
            "source_qp": meta.source_qp,
            "source_ms": meta.source_ms,
            "page_qp": idx.get("page_hint"),
            "body": body,
            "mark_scheme": (
                f"Answer: **{ms_answer}**" if (ms_answer and qtype == "mcq") else (idx.get("mark_scheme") or "")
            ),
        }
        if parent:
            record["parent_question"] = parent
        if part:
            record["part"] = part
        if qtype == "practical":
            topic = spec.get("practical_topic")
            allowed_topics = {
                "Titrations",
                "Thermometric experiments",
                "Gravimetric experiments",
                "Gas volume experiments",
                "Rate experiments",
                "Qualitative analysis",
            }
            if topic not in allowed_topics:
                raise SystemExit(f"{draft_dir.name} q{slug}: bad practical_topic {topic!r}")
            record["practical_topic"] = topic

        (out_dir / f"q{slug}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        written += 1

    if missing:
        raise SystemExit(f"{draft_dir.name}: missing tags for {missing}")
    print(f"{draft_dir.name}: wrote {written} tagged JSON")
    return written


if __name__ == "__main__":
    print("import apply_tags from this module")
