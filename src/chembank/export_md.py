"""Export a tagged question to Obsidian-friendly Markdown."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from chembank.chem_format import format_chemistry_text
from chembank.syllabus import resolve_learning_outcomes, resolve_titles

# Late import avoided: strip helper lives here to keep export_vault→export_md acyclic.


def _strip_body_options_if_paper(body: str, *, has_paper: bool) -> str:
    """Delegate to export_vault helper without importing the package at module load."""
    if not has_paper:
        return body
    from chembank.export_vault import _strip_duplicate_mcq_options

    return _strip_duplicate_mcq_options(body, has_paper_clip=True)


def syllabus_note_path(code: str) -> str:
    """Vault-relative wiki path for a syllabus hub note."""
    return f"syllabus/{code}"


def lo_note_path(lo_id: str) -> str:
    """Vault-relative wiki path for a learning-outcome hub note."""
    return f"syllabus/lo/{lo_id}"


def syllabus_wikilink(code: str, title: str | None = None) -> str:
    label = f"{code} — {title}" if title else code
    return f"[[{syllabus_note_path(code)}|{label}]]"


def lo_wikilink(lo_id: str, text: str | None = None) -> str:
    label = f"{lo_id} — {text}" if text else lo_id
    # Keep labels readable in Obsidian lists
    if text and len(label) > 120:
        label = f"{lo_id} — {text[:100]}…"
    return f"[[{lo_note_path(lo_id)}|{label}]]"


def _split_figure_paths(figs: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Separate paper clips, MS clips, and focused diagram crops."""
    paper: list[str] = []
    ms: list[str] = []
    diagrams: list[str] = []
    for p in figs:
        if p.endswith("-ms.png") or "-ms." in Path(p).name:
            ms.append(p)
        elif p.endswith("-paper.png") or "-paper." in p:
            paper.append(p)
        else:
            diagrams.append(p)
    return paper, ms, diagrams


def question_to_markdown(
    data: dict[str, Any],
    *,
    related_ids: list[str] | None = None,
    figure_paths: list[str] | None = None,
) -> str:
    """Build Markdown with YAML frontmatter + wiki links for Obsidian graph."""
    codes = list(data.get("syllabus_codes") or [])
    qtype = str(data.get("question_type") or "").lower()
    is_practical = qtype == "practical"
    if not codes and not is_practical:
        raise ValueError("syllabus_codes is required (taxonomy-first tagging)")

    titles = list(data.get("topic_titles") or [])
    if codes and not titles:
        titles = resolve_titles(codes)
    lo_ids = [str(x) for x in (data.get("learning_outcomes") or []) if str(x).strip()]
    lo_texts = list(data.get("learning_outcome_texts") or [])
    if lo_ids and not lo_texts:
        try:
            lo_texts = resolve_learning_outcomes(lo_ids)
        except KeyError:
            lo_texts = []
    # Obsidian tags (show in graph when Tags is enabled).
    # Avoid bare numeric tags like "9701" — easy to mis-click exclude in Graph,
    # and some Obsidian builds treat them awkwardly.
    tags = ["chembank", "cie/9701", f"paper/{data.get('paper', 'x')}"]
    if is_practical:
        tags.append("practical")
    practical_topic = str(data.get("practical_topic") or "").strip() or None
    if practical_topic:
        tags.append(f"practical/{practical_topic.replace(' ', '_')}")
    for c in codes:
        tags.append(f"syllabus/{c.replace('.', '/')}")
    for lo_id in lo_ids:
        tags.append(f"lo/{lo_id.replace('.', '/')}")

    figs = list(figure_paths or data.get("figures") or [])
    paper_figs, ms_figs, diagram_figs = _split_figure_paths(figs)
    # Year-scoped ER identity (do not treat as universal LO difficulty)
    er_meta = data.get("examiner_report")
    if not isinstance(er_meta, dict):
        er_meta = None
        if any(data.get(k) for k in ("er_year", "er_session", "er_paper", "examiner_report_source")):
            er_meta = {
                "year": data.get("er_year"),
                "session": data.get("er_session"),
                "paper": data.get("er_paper"),
                "source": data.get("examiner_report_source"),
            }

    front = {
        "id": data["id"],
        "exam_board": data.get("exam_board", "CIE"),
        "syllabus_code": data.get("syllabus_code", "9701"),
        "level": data.get("level", "AS"),
        "year": data.get("year"),
        "session": data.get("session"),
        "paper": data.get("paper"),
        "question": data.get("question"),
        "parent_question": data.get("parent_question"),
        "part": data.get("part"),
        "marks": data.get("marks"),
        "syllabus_codes": codes or None,
        "topic_titles": titles or None,
        "learning_outcomes": lo_ids or None,
        "learning_outcome_texts": lo_texts or None,
        "skills": data.get("skills", []),
        "question_type": data.get("question_type", "mcq"),
        "practical_topic": practical_topic,
        "difficulty": data.get("difficulty"),
        "difficulty_source": data.get("difficulty_source"),
        "examiner_band": data.get("examiner_band"),
        "facility": data.get("facility"),
        "percent_correct": data.get("percent_correct"),
        "discrimination": data.get("discrimination"),
        "er_year": data.get("er_year"),
        "er_session": data.get("er_session"),
        "er_paper": data.get("er_paper"),
        "examiner_report_source": data.get("examiner_report_source"),
        "examiner_report": er_meta,
        "common_incorrect": data.get("common_incorrect"),
        "common_errors": data.get("common_errors") or None,
        "examiner_notes": data.get("examiner_notes"),
        "command_words": data.get("command_words", []),
        "misconceptions": data.get("misconceptions", []),
        "learning_objectives": data.get("learning_objectives") or None,
        "ms_answer": data.get("ms_answer"),
        "source_qp": data.get("source_qp"),
        "source_ms": data.get("source_ms"),
        "page_qp": data.get("page_qp"),
        "page_ms": data.get("page_ms"),
        "figures": figs or None,
        "tags": tags,
    }
    # Keep explicit nulls for numeric ER slots when ER was merged for this paper
    keep_null = set()
    if data.get("examiner_report_source") or data.get("er_year"):
        keep_null = {"facility", "percent_correct", "discrimination"}
    front = {
        k: v
        for k, v in front.items()
        if v is not None or k in keep_null
    }

    body = format_chemistry_text(data.get("body", "")).rstrip()
    # After chem format may split packed A–D into vertical lines — strip again
    body = _strip_body_options_if_paper(body, has_paper=bool(paper_figs)).rstrip()
    ms = format_chemistry_text(data.get("mark_scheme", "")).rstrip()
    fm = yaml.dump(front, allow_unicode=True, sort_keys=False).strip()

    from chembank.structured_parts import is_garbage_ms_text

    year = data.get("year")
    session = str(data.get("session", "")).lower()
    paper = data.get("paper")
    paper_note = f"papers/{data.get('syllabus_code', '9701')}-{year}-{session}-p{paper}"
    parent_q = data.get("parent_question")
    part_label = data.get("part")

    parts = [
        f"---\n{fm}\n---",
        "",
        f"试卷：[[{paper_note}|{year} {str(data.get('session', '')).upper()} Paper {paper}]]",
    ]
    if parent_q:
        parent_note = f"{data.get('id', '').rsplit('-q', 1)[0]}-q{parent_q}"
        # Thin index note (optional): link by parent question number
        parts.append(
            f"主问题：Q{parent_q}"
            + (f" · 小题 `{part_label}`" if part_label else "")
            + (f" · [[{parent_note}|Q{parent_q} 索引]]" if parent_q else "")
        )
    parts.extend(["", "## Question", ""])
    # Paper clip first — primary readable layout (options / tables / diagrams)
    for p in paper_figs:
        parts.append(f"![[{p}]]")
        parts.append("")
    parts.extend([body, ""])

    # Focused crops only when they add something beyond the paper clip
    if diagram_figs:
        parts.extend(["## Diagram", ""])
        for p in diagram_figs:
            parts.append(f"![[{p}]]")
            parts.append("")
    if ms_figs or (ms and not is_garbage_ms_text(ms)):
        parts.extend(["## Mark Scheme", ""])
        for p in ms_figs:
            parts.append(f"![[{p}]]")
            parts.append("")
        # Image is primary; only keep clean short MS text
        if ms and not is_garbage_ms_text(ms):
            parts.extend([ms, ""])
        elif ms_figs:
            parts.append("")

    er_notes = (data.get("examiner_notes") or "").strip()
    er_band = data.get("examiner_band")
    common_err = list(data.get("common_errors") or [])
    common_wrong = data.get("common_incorrect")
    if er_notes or er_band or common_err or common_wrong:
        parts.extend(["## Examiner report", ""])
        er_bits = []
        if data.get("er_year") or data.get("er_session") or data.get("er_paper"):
            er_bits.append(
                f"- Scope: {data.get('er_year')} {data.get('er_session')} "
                f"Paper {data.get('er_paper')} "
                f"(year-scoped; not universal LO difficulty)"
            )
        if er_band:
            er_bits.append(f"- Band: `{er_band}`")
        if data.get("facility") is not None:
            er_bits.append(f"- Facility: {data.get('facility')}")
        if data.get("percent_correct") is not None:
            er_bits.append(f"- Percent correct: {data.get('percent_correct')}")
        if common_wrong:
            er_bits.append(f"- Most common wrong option: **{common_wrong}**")
        if er_bits:
            parts.extend(er_bits)
            parts.append("")
        if common_err:
            parts.extend(["### Common errors", ""])
            parts.extend(f"- {e}" for e in common_err)
            parts.append("")
        if er_notes:
            parts.extend(["### Comments", "", er_notes, ""])

    if practical_topic:
        parts.extend(["## Practical topic", "", f"- `{practical_topic}`", ""])

    if codes:
        parts.extend(
            [
                "## Syllabus",
                "",
                *[f"- {syllabus_wikilink(c, t)}" for c, t in zip(codes, titles)],
                "",
            ]
        )

    if lo_ids:
        parts.extend(["## Learning outcomes", ""])
        for lo_id, lo_text in zip(lo_ids, lo_texts or [""] * len(lo_ids)):
            parts.append(f"- {lo_wikilink(lo_id, lo_text or None)}")
        parts.append("")

    if related_ids:
        parts.extend(
            [
                "## Related",
                "",
                *[f"- [[{rid}]]" for rid in related_ids],
                "",
            ]
        )

    return "\n".join(parts)


def write_question_markdown(
    data: dict[str, Any],
    out_path: Path,
    *,
    related_ids: list[str] | None = None,
    figure_paths: list[str] | None = None,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        question_to_markdown(
            data, related_ids=related_ids, figure_paths=figure_paths
        ),
        encoding="utf-8",
    )
    return out_path


def write_syllabus_hub(
    code: str,
    title: str,
    out_path: Path,
    *,
    question_ids: list[str] | None = None,
    parent_code: str | None = None,
) -> Path:
    """Create/update a syllabus topic note that questions link to."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tags = ["syllabus", f"syllabus/{code.replace('.', '/')}"]
    front = {
        "type": "syllabus-topic",
        "code": code,
        "title": title,
        "tags": tags,
    }
    lines = [
        "---",
        yaml.dump(front, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        f"# {code} — {title}",
        "",
    ]
    if parent_code:
        lines.append(f"上级：[[syllabus/{parent_code}]]")
        lines.append("")
    lines.extend(
        [
            "本页是考纲节点枢纽。图谱里与题目的连线来自各题 `## Syllabus` 中的双向链接。",
            "",
            "## 题目",
            "",
        ]
    )
    if question_ids:
        lines.extend(f"- [[{qid}]]" for qid in question_ids)
    else:
        lines.extend(
            [
                "```dataview",
                "TABLE ms_answer, year, paper, question, difficulty",
                'FROM "questions"',
                f'WHERE contains(syllabus_codes, "{code}")',
                "SORT year ASC, paper ASC, question ASC",
                "```",
            ]
        )
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def write_lo_hub(
    lo_id: str,
    text: str,
    out_path: Path,
    *,
    parent_code: str | None = None,
    question_ids: list[str] | None = None,
) -> Path:
    """Create/update a learning-outcome hub note (searchable id + Dataview)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    parent = parent_code or lo_id.rsplit("-", 1)[0]
    front = {
        "type": "learning-outcome",
        "id": lo_id,
        "aliases": [lo_id, f"LO {lo_id}"],
        "parent_code": parent,
        "text": text,
        "tags": ["learning-outcome", f"lo/{lo_id.replace('.', '/')}"],
    }
    lines = [
        "---",
        yaml.dump(front, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        f"# LO {lo_id}",
        "",
        f"**LO id:** `{lo_id}`",
        "",
        text,
        "",
        f"Parent topic: {syllabus_wikilink(parent)}",
        "",
        "## Questions",
        "",
    ]
    # Always include Dataview so hubs stay searchable/up-to-date even when
    # no questions are tagged yet (static export lists go stale).
    lines.extend(
        [
            "```dataview",
            "TABLE ms_answer, year, paper, question, syllabus_codes",
            'FROM "questions"',
            f'WHERE contains(learning_outcomes, "{lo_id}")',
            "SORT year ASC, paper ASC, question ASC",
            "```",
            "",
        ]
    )
    if question_ids:
        lines.append("### Linked from last export")
        lines.append("")
        lines.extend(f"- [[{qid}]]" for qid in question_ids)
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def export_all_lo_hubs(
    vault_dir: Path,
    *,
    as_only: bool = True,
    code: str | None = None,
    syllabus_path: Path | None = None,
) -> dict[str, Any]:
    """Write Obsidian LO hub notes for every LO in the controlled vocabulary."""
    from chembank.syllabus import list_learning_outcomes, parent_code_for_lo

    vault_dir = Path(vault_dir)
    lo_dir = vault_dir / "syllabus" / "lo"
    lo_dir.mkdir(parents=True, exist_ok=True)
    rows = list_learning_outcomes(syllabus_path, code=code, as_only=as_only)
    written: list[str] = []
    for lo_id, parent, text in rows:
        try:
            parent = parent_code_for_lo(lo_id)
        except ValueError:
            pass
        write_lo_hub(
            lo_id,
            text,
            lo_dir / f"{lo_id}.md",
            parent_code=parent,
        )
        written.append(lo_id)
    return {"count": len(written), "lo_dir": str(lo_dir), "ids": written}


def write_paper_hub(
    *,
    syllabus_code: str,
    year: int,
    session: str,
    paper: int | str,
    question_ids: list[str],
    out_path: Path,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sid = f"{syllabus_code}-{year}-{session.lower()}-p{paper}"
    front = {
        "type": "paper",
        "syllabus_code": syllabus_code,
        "year": year,
        "session": session.upper(),
        "paper": paper,
        "tags": ["paper", f"paper/{paper}", str(year)],
    }
    lines = [
        "---",
        yaml.dump(front, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        f"# {syllabus_code} {year} {session.upper()} Paper {paper}",
        "",
        f"共 {len(question_ids)} 题。",
        "",
        "## Questions",
        "",
        *[f"- [[{qid}]]" for qid in question_ids],
        "",
        "← [[题库首页]]",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
