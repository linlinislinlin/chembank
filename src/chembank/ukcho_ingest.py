"""Materialise an extracted UKChO paper + tagging sheet into the Obsidian vault.

This is the bridge between the mechanical step (:mod:`chembank.ukcho_extract`,
which knows the *structure* of a paper) and the tagging step (a human or a model
reading the actual chemistry, captured in a *tagging sheet*).

Why a sheet instead of tagging one record at a time
---------------------------------------------------
A UKChO paper is ~45 sub-questions. Driving ``ukcho prompt`` / ``ukcho apply`` 45
times is unusable, and the parent records carry structure the model cannot infer
per sub-question. So the tagging sheet holds:

* ``parents`` — one entry per main question (title, total marks, themes);
* ``parts``   — one entry per sub-question, keyed by the extract's part key
  (``"3b-i"``), holding only the *tags* plus marks and answer/mark-scheme text.

Everything mechanical (ids, parent links, page clips, provenance) is derived from
the extract, so the sheet never has to repeat it. Records land with
``tag_status: suggested`` / ``tag_source: ai``: a model proposed them and a
teacher must still accept or edit them. Nothing is locked.

The sheet is intentionally *not* committed — it embeds question and mark-scheme
text, which is copyrighted past-paper content.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from chembank import ukcho as U

#: Tag fields a tagging sheet may set on a sub-question (everything else is derived).
TAGGABLE_FIELDS: tuple[str, ...] = (
    "primary_as_anchor",
    "secondary_as_anchors",
    "extension_topics",
    "primary_skill",
    "secondary_skills",
    "difficulty_level",
    "difficulty_reason",
    "question_features",
    "prerequisites",
    "requires_extension_knowledge",
)

#: The tag fields that must be filled before a part counts as tagged at all.
#: A sheet skeleton pre-creates every key so the tagger has slots to fill, which
#: means "is this part tagged?" can no longer be answered by "is the dict empty?".
CORE_TAG_FIELDS: tuple[str, ...] = (
    "primary_as_anchor",
    "primary_skill",
    "difficulty_level",
)

#: Empty-value shape for a skeleton slot, so a half-filled sheet validates the
#: same way a hand-written one does.
_LIST_TAG_FIELDS = frozenset(
    {"secondary_as_anchors", "extension_topics", "secondary_skills",
     "question_features", "prerequisites"}
)
_BOOL_TAG_FIELDS = frozenset({"requires_extension_knowledge"})

#: Part keys as they appear in the extract manifest: "3a", "6b-ii".
_PART_KEY_RE = r"(\d+)([a-z])(?:-([ivx]+))?"


#: Parent fields that are authored rather than purely mechanical, so a re-ingest
#: does not revert a teacher's title or corrected mark total.
PRESERVED_PARENT_FIELDS: tuple[str, ...] = ("title", "total_marks", "overall_themes")


def _empty_slot(field: str) -> Any:
    if field in _LIST_TAG_FIELDS:
        return []
    if field in _BOOL_TAG_FIELDS:
        return False
    return None


#: Non-tag metadata a sheet may also set. ``question_text`` overrides the raw PDF
#: text layer, which interleaves columns on layout-heavy UKChO parts.
EXTRA_FIELDS: tuple[str, ...] = (
    "answer",
    "mark_scheme",
    "teacher_notes",
    "review_required",
    "question_text",
)

#: Extras the sheet skeleton offers empty slots for. These come from the mark
#: scheme rather than the question paper, so a tagger reading both needs somewhere
#: to put them. ``question_text`` is deliberately absent: the extract already
#: supplies it, and echoing ~45 blocks of paper text into the hand-off file would
#: make it enormous and invite silent transcription drift.
EXTRA_SLOT_FIELDS: tuple[str, ...] = (
    "answer",
    "mark_scheme",
    "teacher_notes",
)


#: Everything a human (or the tagging pass) authors on a sub-question. When a
#: record has already been reviewed by a teacher, these values are carried over on
#: re-ingest; every other field is derived from the extract and always refreshed.
#: This is what makes ``ingest`` safe to re-run.
PRESERVED_FIELDS: tuple[str, ...] = (
    TAGGABLE_FIELDS + EXTRA_FIELDS + ("marks", "tag_status", "tag_source", "year_tags")
)


def load_tagging(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sub_id(prefix: str, key: str) -> str:
    """``("ukcho-2025", "3b-i") -> "ukcho-2025-q3b-i"``."""
    m = re.fullmatch(_PART_KEY_RE, key)
    if not m:
        return f"{prefix}-q{key}"
    q, part, sub = m.group(1), m.group(2), m.group(3)
    return f"{prefix}-q{q}{part}" + (f"-{sub}" if sub else "")


def parent_id(prefix: str, question: int | str) -> str:
    return f"{prefix}-q{question}"


def _part_sort_key(key: str) -> tuple[int, str, int]:
    m = re.fullmatch(_PART_KEY_RE, key)
    if not m:
        return (999, key, 0)
    roman = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}
    return (int(m.group(1)), m.group(2), roman.get(m.group(3) or "", 0))


def year_from_prefix(prefix: str) -> int | None:
    """``"ukcho-2025" -> 2025``. Returns ``None`` when no year is present."""
    m = re.search(r"(?:^|[-_])((?:19|20)\d{2})(?:$|[-_])", prefix or "")
    return int(m.group(1)) if m else None


def prefix_from_manifest(manifest: dict[str, Any]) -> str:
    """Recover the paper prefix, e.g. ``"ukcho-2025"``.

    New extracts record it directly. Extracts made before that field existed are
    recovered from an asset name (``parts/ukcho-2025-3a.txt`` -> ``ukcho-2025``),
    so a paper extracted earlier can still be tagged without re-extracting.
    """
    declared = str(manifest.get("prefix") or "")
    if declared:
        return declared
    for part in manifest.get("parts") or []:
        key = str(part.get("key") or "")
        if not key:
            continue
        for candidate in [part.get("text_path")] + list(part.get("clips") or []):
            name = Path(str(candidate or "")).name
            head, sep, _tail = name.partition(key)
            if sep and head:
                return head.rstrip("-_")
    return ""


def resolve_prefix(manifest: dict[str, Any], prefix: str = "") -> str:
    """Explicit flag > manifest field > recovered from an asset name > "ukcho"."""
    return prefix or prefix_from_manifest(manifest) or "ukcho"



def build_records(
    manifest: dict[str, Any],
    tagging: dict[str, Any],
    prefix: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Return ``(parents, subquestions, problems)``.

    Raises nothing: a part missing from the tagging sheet becomes a record with
    empty tags and ``review_required: true``, so an incomplete sheet is visible in
    the teacher UI rather than silently dropping questions.
    """
    prefix = prefix or tagging.get("prefix") or "ukcho"
    year = tagging.get("year")
    source_qp = tagging.get("source_qp", "")
    source_ms = tagging.get("source_ms", "")
    sheet_parents = {int(p["question_number"]): p for p in tagging.get("parents") or []}
    sheet_parts: dict[str, Any] = tagging.get("parts") or {}

    problems: list[str] = []
    parts = manifest.get("parts") or []

    by_question: dict[int, list[dict[str, Any]]] = {}
    for part in parts:
        by_question.setdefault(int(part["question"]), []).append(part)

    def _sheet_marks(kids: list[dict[str, Any]]) -> int:
        """Sum a question's part marks from the sheet.

        Marks live in the tagging sheet, not in the extract, so the fallback has
        to read ``sheet_parts`` — summing the manifest parts would always be 0.
        """
        total = 0
        for kid in kids:
            marks = (sheet_parts.get(kid["key"]) or {}).get("marks")
            if isinstance(marks, (int, float)):
                total += marks
        return total

    parents: list[dict[str, Any]] = []
    for q in sorted(by_question):
        meta = sheet_parents.get(q, {})
        kids = by_question[q]
        pid = parent_id(prefix, q)
        parents.append(
            U.normalize_record(
                {
                    "id": pid,
                    "record_type": "ukcho-parent",
                    "source": "UKChO",
                    "year": year,
                    "question_number": q,
                    "title": meta.get("title") or "",
                    "total_marks": meta.get("total_marks") or _sheet_marks(kids),
                    "overall_themes": meta.get("overall_themes") or [],
                    "sub_question_ids": [sub_id(prefix, p["key"]) for p in kids],
                    "stems": manifest.get("stems", {}).get(str(q), ""),
                    "source_qp": source_qp,
                    "source_ms": source_ms,
                },
                fallback_id=pid,
            )
        )

    manifest_by_key = {p["key"]: p for p in parts}
    for key in sorted(sheet_parts, key=_part_sort_key):
        if key not in manifest_by_key:
            problems.append(f"tagging sheet has part {key!r} that is not in the extract")
    for key, part in manifest_by_key.items():
        if key not in sheet_parts:
            problems.append(f"part {key!r} is in the extract but has no tags (review_required set)")

    subs: list[dict[str, Any]] = []
    for key in sorted(manifest_by_key, key=_part_sort_key):
        part = manifest_by_key[key]
        tags = dict(sheet_parts.get(key) or {})
        raw: dict[str, Any] = {
            "id": sub_id(prefix, key),
            "record_type": "ukcho-subquestion",
            "source": "UKChO",
            "year": year,
            "question_number": int(part["question"]),
            "sub_question": _sub_of(part),
            "parent_question_id": parent_id(prefix, part["question"]),
            "marks": tags.get("marks"),
            "question_text": part.get("text") or "",
            "source_qp": source_qp,
            "source_ms": source_ms,
            # A sheet may carry provenance (a snapshot of an already-reviewed
            # record must restore as reviewed, not regress to "ai suggested").
            "tag_status": tags.get("tag_status") or "suggested",
            "tag_source": tags.get("tag_source") or "ai",
        }
        for field in TAGGABLE_FIELDS:
            if field in tags:
                raw[field] = tags[field]
        for field in EXTRA_FIELDS:
            if field in tags:
                raw[field] = tags[field]
        # Clips are derived from the extract, never from the sheet. MS clips go in
        # the same `figures` list as the AS/IGCSE banks; `-ms` in the name is what
        # tells the body builder (and the site) which is which.
        raw["figures"] = [
            f"assets/{Path(str(c)).name}"
            for c in (part.get("clips") or []) + (part.get("ms_clips") or [])
        ]
        rec = U.normalize_record(raw, fallback_id=raw["id"])
        # A part is "untagged" if any core tag is missing — not merely if the
        # sheet entry is absent, because a skeleton pre-creates every key.
        untagged = [f for f in CORE_TAG_FIELDS if not rec.get(f)]
        if untagged and "review_required" not in tags:
            rec["review_required"] = True
        subs.append(rec)

    return parents, subs, problems


# ---------------------------------------------------------------------------
# Tagging sheet skeleton (the extract -> tagging hand-off)
# ---------------------------------------------------------------------------

def build_sheet_skeleton(
    manifest: dict[str, Any],
    prefix: str = "",
    year: int | None = None,
    source_qp: str = "",
    source_ms: str = "",
) -> dict[str, Any]:
    """A fillable tagging sheet with every part key already present.

    Hand-writing a sheet for a ~45-part paper is where a new year gets stuck: the
    part keys must match the extract exactly or every part is misfiled, and the
    parents/questions scaffolding is pure mechanical work. This pre-creates all of
    it with empty tag slots, so tagging becomes "fill in the chemistry".

    Slots are empty rather than absent so a half-filled sheet is obvious. Marks
    cannot be derived from the question paper, so they are left as ``None``.
    """
    prefix = resolve_prefix(manifest, prefix)
    if year is None:
        year = year_from_prefix(prefix)
    parts = manifest.get("parts") or []

    by_question: dict[int, list[dict[str, Any]]] = {}
    for part in parts:
        by_question.setdefault(int(part["question"]), []).append(part)

    return {
        "source": "UKChO",
        "prefix": prefix,
        "year": year,
        "source_qp": source_qp or str(manifest.get("source_pdf") or ""),
        "source_ms": source_ms,
        "parents": [
            {
                "question_number": q,
                "title": "",
                "total_marks": None,
                "overall_themes": [],
            }
            for q in sorted(by_question)
        ],
        "parts": {
            key: {
                "marks": None,
                **{field: _empty_slot(field) for field in TAGGABLE_FIELDS},
                **{field: None for field in EXTRA_SLOT_FIELDS},
            }
            for key in sorted((p["key"] for p in parts), key=_part_sort_key)
        },
    }


def build_paper_prompt(
    manifest: dict[str, Any],
    prefix: str = "",
    year: int | None = None,
) -> dict[str, Any]:
    """A single self-contained request covering every part of one paper.

    The per-record ``ukcho prompt`` forces one model call per part and hides the
    parent stem, which matters because later parts of a UKChO question depend on
    earlier deductions. This bundles the whole paper so a tagger sees the same
    context a teacher would.
    """
    prefix = resolve_prefix(manifest, prefix)
    if year is None:
        year = year_from_prefix(prefix)
    parts = manifest.get("parts") or []
    stems = manifest.get("stems") or {}

    tax = U.taxonomy()
    system = U.TAGGING_INSTRUCTIONS + json.dumps(
        {
            "asAnchors": tax["asAnchors"],
            "extensionTopics": tax["extensionTopics"],
            "skills": tax["skills"],
            "difficultyLevels": tax["difficultyLevels"],
            "questionFeatures": tax["questionFeatures"],
        },
        ensure_ascii=False,
        indent=2,
    )

    by_question: dict[int, list[dict[str, Any]]] = {}
    for part in parts:
        by_question.setdefault(int(part["question"]), []).append(part)

    questions = [
        {
            "question_number": q,
            "stem": stems.get(str(q), ""),
            "part_keys": [p["key"] for p in sorted(by_question[q], key=lambda p: _part_sort_key(p["key"]))],
        }
        for q in sorted(by_question)
    ]

    return {
        "system": system,
        "paper": {
            "prefix": prefix,
            "year": year,
            "source_pdf": str(manifest.get("source_pdf") or ""),
            "questions": len(by_question),
            "parts": len(parts),
        },
        "questions": questions,
        "parts": [
            {
                "key": part["key"],
                "label": U.question_label({"question_number": part["question"],
                                           "sub_question": _sub_of(part)}),
                "question": part["question"],
                "marks": None,  # not derivable from the question paper
                "text": part.get("text") or "",
                "clips": [Path(str(c)).name for c in (part.get("clips") or [])],
            }
            for part in sorted(parts, key=lambda p: _part_sort_key(p["key"]))
        ],
        "taxonomy": tax,
        "response_schema": {
            "parts": {
                "<key>": {field: _empty_slot(field) for field in TAGGABLE_FIELDS}
                | {field: None for field in EXTRA_SLOT_FIELDS}
                | {"marks": None}
            }
        },
    }


def _sub_of(part: dict[str, Any]) -> str:
    """``{"question": 6, "part": "b", "subpart": "ii"} -> "b-ii"``."""
    base = str(part.get("part") or "")
    return f"{base}-{part['subpart']}" if part.get("subpart") else base


def write_sheet(
    manifest_dir: Path,
    out_dir: Path | None = None,
    prefix: str = "",
    year: int | None = None,
    source_qp: str = "",
    source_ms: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """Write ``prompt.json`` + ``tagging.json`` for one extracted paper.

    ``tagging.json`` is never overwritten unless ``force`` is set: it holds the
    only copy of the tagging work for a paper, and re-running the command to get a
    fresh prompt must not destroy it.
    """
    manifest_dir = Path(manifest_dir)
    manifest = json.loads((manifest_dir / "parts.json").read_text(encoding="utf-8"))
    out = Path(out_dir) if out_dir else manifest_dir
    out.mkdir(parents=True, exist_ok=True)

    prompt_path = out / "prompt.json"
    sheet_path = out / "tagging.json"

    resolved_prefix = resolve_prefix(manifest, prefix)
    prompt_path.write_text(
        json.dumps(
            build_paper_prompt(manifest, prefix=resolved_prefix, year=year),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    written_sheet = False
    if sheet_path.exists() and not force:
        sheet_status = "kept (already exists — use --force to reset)"
    else:
        sheet_path.write_text(
            json.dumps(
                build_sheet_skeleton(
                    manifest,
                    prefix=resolved_prefix,
                    year=year,
                    source_qp=source_qp,
                    source_ms=source_ms,
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        written_sheet = True
        sheet_status = "written"

    return {
        "prefix": resolved_prefix,
        "year": year if year is not None else year_from_prefix(resolved_prefix),
        "parts": len(manifest.get("parts") or []),
        "questions": len({int(p["question"]) for p in manifest.get("parts") or []}),
        "prompt_path": prompt_path,
        "sheet_path": sheet_path,
        "sheet_status": sheet_status,
        "sheet_written": written_sheet,
    }


def _body(rec: dict[str, Any], parent: dict[str, Any]) -> str:
    label = f"{rec.get('year')} {U.question_label(rec)}"
    lines = [f"# UKChO {label} — {parent.get('title', '')}", ""]
    # Paper clips head the note; mark-scheme clips belong with the mark scheme, so
    # the two are split on the `-ms` marker rather than dumped together.
    paper_figs = [f for f in (rec.get("figures") or []) if "-ms" not in f]
    ms_figs = [f for f in (rec.get("figures") or []) if "-ms" in f]
    for fig in paper_figs:
        lines.append(f"![[{fig}]]")
        lines.append("")
    if rec.get("marks"):
        lines.append(f"**Marks:** {rec['marks']}")
        lines.append("")
    if rec.get("question_text"):
        lines += ["## Question", "", rec["question_text"], ""]
    if ms_figs or rec.get("mark_scheme"):
        # One section: the marked-answer image first, then the extracted text.
        lines += ["## Mark scheme", ""]
        for fig in ms_figs:
            lines.append(f"![[{fig}]]")
            lines.append("")
        if rec.get("mark_scheme"):
            lines += [rec["mark_scheme"], ""]
    if rec.get("answer"):
        lines += ["## Answer", "", rec["answer"], ""]
    lines += [
        "## Tags",
        "",
        f"- AS anchor: {rec.get('primary_as_anchor') or '—'}"
        + (
            f" (+ {', '.join(rec['secondary_as_anchors'])})"
            if rec.get("secondary_as_anchors")
            else ""
        ),
        f"- Extension: {', '.join(rec.get('extension_topics') or []) or '—'}",
        f"- Skill: {rec.get('primary_skill') or '—'}"
        + (f" (+ {', '.join(rec['secondary_skills'])})" if rec.get("secondary_skills") else ""),
        f"- Difficulty: {rec.get('difficulty_level') or '—'}",
        f"- Parent: [[{parent.get('id')}]]",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _parent_body(parent: dict[str, Any], kids: list[dict[str, Any]]) -> str:
    # An untitled question shows a neutral fallback; the record itself stays empty
    # so a teacher-supplied title can be restored on a later re-ingest.
    title = parent.get("title") or f"Question {parent.get('question_number')}"
    lines = [f"# UKChO {parent.get('year')} Q{parent.get('question_number')} — {title}", ""]
    if parent.get("stems"):
        lines += ["## Context", "", parent["stems"], ""]
    lines += [f"**Total marks:** {parent.get('total_marks')}", "", "## Sub-questions", ""]
    for kid in kids:
        lines.append(
            f"- [[{kid['id']}|{U.question_label(kid)}]] "
            f"({kid.get('marks')} marks · {kid.get('difficulty_level') or 'untagged'})"
        )
    return "\n".join(lines).rstrip() + "\n"


def _load_reviewed_records(questions_dir: Path) -> dict[str, dict[str, Any]]:
    """Existing vault records by id, so teacher edits can be carried over.

    Only reviewed records are returned: for anything the AI produced there is no
    reason to prefer the old copy over the tagging sheet.
    """
    reviewed: dict[str, dict[str, Any]] = {}
    for rec in U.load_ukcho_questions(questions_dir):
        rid = str(rec.get("id") or "")
        if rid and U.is_teacher_authored(rec):
            reviewed[rid] = rec
    return reviewed


def _carry_over_parent(parent: dict[str, Any], old: dict[str, Any] | None) -> None:
    """Keep a teacher's parent title / corrected totals when the sheet is silent.

    Parents carry no tag fields, so only the authored metadata is restored, and
    only where the tagging sheet left it blank — an explicit sheet value still wins.
    """
    if old is None:
        return
    for field in PRESERVED_PARENT_FIELDS:
        current = parent.get(field)
        blank = current is None or current == "" or current == []
        if blank and old.get(field):
            parent[field] = old[field]


def ingest_paper(
    manifest_dir: Path,
    tagging_path: Path,
    vault_dir: Path,
    clip_source_dir: Path | None = None,
    source_qp: str = "",
    source_ms: str = "",
) -> dict[str, Any]:
    """Write parents + sub-questions + page clips into ``vault_dir``.

    Safe to re-run: records a teacher has already reviewed keep their authored
    fields (see :data:`PRESERVED_FIELDS`), and only untagged/AI-sourced records are
    refreshed from the tagging sheet. Other papers in the vault are left alone.
    """
    manifest = json.loads(
        (Path(manifest_dir) / "parts.json").read_text(encoding="utf-8")
    )
    tagging = load_tagging(tagging_path)
    if source_qp:
        tagging["source_qp"] = source_qp
    if source_ms:
        tagging["source_ms"] = source_ms

    prefix = tagging.get("prefix") or "ukcho"
    parents, subs, problems = build_records(manifest, tagging, prefix=prefix)

    questions_dir = Path(vault_dir) / "questions"
    assets_dir = Path(vault_dir) / "assets"
    questions_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    # --- clips ------------------------------------------------------------
    clips_dir = Path(clip_source_dir) if clip_source_dir else Path(manifest_dir) / "clips"
    copied = 0
    ms_copied = 0
    for part in manifest.get("parts") or []:
        for clip in (part.get("clips") or []) + (part.get("ms_clips") or []):
            is_ms = "-ms" in Path(str(clip)).name
            src = Path(clip)
            if not src.is_absolute() and not src.exists():
                src = clips_dir / Path(clip).name
            if not src.exists():
                problems.append(f"missing clip for part {part['key']}: {clip}")
                continue
            dest = assets_dir / src.name
            shutil.copy2(src, dest)
            copied += 1
            if is_ms:
                ms_copied += 1

    # --- records ----------------------------------------------------------
    # A teacher's work outranks the tagging sheet: carry it over before writing.
    reviewed = _load_reviewed_records(questions_dir)
    preserved = 0
    for sub in subs:
        old = reviewed.get(str(sub["id"]))
        if old is not None:
            for field in PRESERVED_FIELDS:
                if field in old:
                    sub[field] = old[field]
            preserved += 1

    by_q: dict[int, list[dict[str, Any]]] = {}
    for sub in subs:
        by_q.setdefault(int(sub["question_number"]), []).append(sub)

    written = 0
    for parent in parents:
        _carry_over_parent(parent, reviewed.get(str(parent["id"])))
        kids = sorted(
            by_q.get(int(parent["question_number"]), []),
            key=lambda r: _part_sort_key(f"{r['question_number']}{r['sub_question']}"),
        )
        path = questions_dir / f"{parent['id']}.md"
        path.write_text(
            U.to_frontmatter(U.to_ordered_dict(parent)) + "\n" + _parent_body(parent, kids),
            encoding="utf-8",
        )
        written += 1

    for sub in subs:
        parent = next(
            p for p in parents if p["id"] == sub["parent_question_id"]
        )
        path = questions_dir / f"{sub['id']}.md"
        path.write_text(
            U.to_frontmatter(U.to_ordered_dict(sub)) + "\n" + _body(sub, parent),
            encoding="utf-8",
        )
        written += 1

    report = U.validate_all(parents + subs)
    validation_errors = sum(len(v) for v in report["errors"].values())
    warnings = [f"{qid}: {w}" for qid, ws in report["warnings"].items() for w in ws]

    # Separate "not tagged yet" from "tagged wrongly". Both surface as validation
    # errors, but only the second is a mistake — a partly-filled skeleton is simply
    # unfinished work, and reporting 3 errors x 40 blank parts drowns the real ones.
    needs_tags = [
        s["id"] for s in subs if any(not s.get(f) for f in CORE_TAG_FIELDS)
    ]
    unfinished = set(needs_tags)
    other_errors = {
        qid: errs for qid, errs in report["errors"].items() if qid not in unfinished
    }

    return {
        "parents": len(parents),
        "subquestions": len(subs),
        "clips": copied,
        "ms_clips": ms_copied,
        "written": written,
        "preserved": preserved,
        "problems": problems,
        "errors": validation_errors + len(problems),
        "needs_tags": needs_tags,
        "other_errors": other_errors,
        "warnings": warnings,
        "report": report,
    }


# ---------------------------------------------------------------------------
# Tag snapshots (committed, content-free backup of the tagging work)
# ---------------------------------------------------------------------------

#: Past-paper *content* that must never be committed. The vault and the tagging
#: sheet both embed question and mark-scheme text, so they are gitignored and a
#: crash would lose every tagging decision. A snapshot keeps the decisions and
#: drops this text, so it can live in git without redistributing RSC material.
#:
#: ``teacher_notes`` is deliberately NOT excluded: it is the teacher's own
#: annotation rather than paper text, and losing it would lose original work.
SNAPSHOT_EXCLUDED_FIELDS: tuple[str, ...] = ("question_text", "answer", "mark_scheme")

#: Everything a snapshot carries for one part: the tags, the marks, and the
#: provenance needed to restore the record exactly as it was reviewed.
SNAPSHOT_PART_FIELDS: tuple[str, ...] = (
    TAGGABLE_FIELDS
    + tuple(f for f in EXTRA_FIELDS if f not in SNAPSHOT_EXCLUDED_FIELDS)
    + ("marks", "tag_status", "tag_source")
)


def snapshot_prefix(record_id: str) -> str:
    """``"ukcho-2025-q3b-i" -> "ukcho-2025"`` — the paper a record belongs to."""
    head, sep, _tail = str(record_id or "").partition("-q")
    return head if sep else str(record_id or "")


def part_key(rec: dict[str, Any]) -> str:
    """Vault record -> tagging-sheet key. ``Q3(b)(i)`` -> ``"3b-i"``.

    Inverse of :func:`_sub_of`; this is what lets a snapshot drop straight back
    into ``ingest --tagging``.
    """
    return f"{rec.get('question_number')}{rec.get('sub_question') or ''}"


def build_snapshot(vault_dir: Path, prefix: str) -> dict[str, Any]:
    """A content-free tagging sheet for one paper, read from the vault.

    The vault is the authority (a teacher may have corrected a tag there), so the
    snapshot is generated from it rather than from the original tagging sheet.
    """
    records = U.load_ukcho_questions(Path(vault_dir) / "questions")
    subs = [
        r for r in records
        if r.get("record_type") == "ukcho-subquestion"
        and snapshot_prefix(str(r.get("id") or "")) == prefix
    ]
    parents = [
        r for r in records
        if r.get("record_type") == "ukcho-parent"
        and snapshot_prefix(str(r.get("id") or "")) == prefix
    ]
    if not subs and not parents:
        raise ValueError(f"no vault records for prefix {prefix!r}")

    parts: dict[str, Any] = {}
    for rec in sorted(subs, key=lambda r: _part_sort_key(part_key(r))):
        parts[part_key(rec)] = {
            field: rec.get(field, _empty_slot(field) if field in TAGGABLE_FIELDS else None)
            for field in SNAPSHOT_PART_FIELDS
        }

    return {
        "generated": "chembank-ukcho-tag-snapshot",
        "source": "UKChO",
        "prefix": prefix,
        "year": year_from_prefix(prefix) or (subs[0].get("year") if subs else None),
        "source_qp": (parents[0].get("source_qp") if parents else "") or "",
        "source_ms": (parents[0].get("source_ms") if parents else "") or "",
        "parents": [
            {
                "question_number": p.get("question_number"),
                "title": p.get("title") or "",
                "total_marks": p.get("total_marks"),
                "overall_themes": p.get("overall_themes") or [],
            }
            for p in sorted(parents, key=lambda p: p.get("question_number") or 0)
        ],
        "parts": parts,
    }


def find_content_leaks(snapshot: dict[str, Any]) -> list[str]:
    """Any excluded field that still carries text. Must always be empty.

    A hard guard rather than a convention: this file is meant to be committed, so
    a mistake here would publish copyrighted past-paper text.
    """
    leaks: list[str] = []
    for key, entry in (snapshot.get("parts") or {}).items():
        for field in SNAPSHOT_EXCLUDED_FIELDS:
            if str(entry.get(field) or "").strip():
                leaks.append(f"part {key}: {field}")
    return leaks


#: A run of this many consecutive words shared between a tag field and the paper is
#: worth flagging. Tag fields legitimately *describe* a question, so this is a
#: warning rather than a failure — the point is that a quotation is a visible,
#: reviewable decision instead of an invisible one.
VERBATIM_QUOTE_WORDS = 8

#: Tag fields that are free text, so a quotation can hide in them.
_FREE_TEXT_SNAPSHOT_FIELDS: tuple[str, ...] = (
    "difficulty_reason",
    "teacher_notes",
)


def _normalized_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text or "").lower())


def find_verbatim_quotes_from(
    records: list[dict[str, Any]],
    min_words: int = VERBATIM_QUOTE_WORDS,
) -> list[dict[str, str]]:
    """The detector itself, over records already in memory (so it is testable)."""
    findings: list[dict[str, str]] = []
    for rec in records:
        if rec.get("record_type") != "ukcho-subquestion":
            continue
        protected = " ".join(
            " ".join(_normalized_words(rec.get(f)))
            for f in ("question_text", "answer", "mark_scheme")
        )
        if not protected:
            continue
        protected = f" {protected} "
        for field in _FREE_TEXT_SNAPSHOT_FIELDS:
            words = _normalized_words(rec.get(field))
            for i in range(0, max(0, len(words) - min_words + 1)):
                window = " ".join(words[i : i + min_words])
                if f" {window} " in protected:
                    findings.append(
                        {"id": str(rec.get("id")), "field": field, "quote": window}
                    )
                    break  # one report per field is enough to review
    return findings


def find_verbatim_quotes(
    vault_dir: Path,
    min_words: int = VERBATIM_QUOTE_WORDS,
) -> list[dict[str, str]]:
    """Tag text that quotes the paper verbatim, so it can be reviewed before commit.

    A snapshot is meant to be committable, but a tag *field* being safe does not
    make its *value* safe: ``difficulty_reason`` explains the question and may
    quote it. This surfaces those runs instead of silently shipping them.
    """
    records = U.load_ukcho_questions(Path(vault_dir) / "questions")
    return find_verbatim_quotes_from(records, min_words)


def write_snapshot(
    vault_dir: Path,
    out_dir: Path,
    prefix: str = "",
) -> dict[str, Any]:
    """Write one content-free snapshot per paper into ``out_dir``.

    Restore is the existing pipeline, so no special command is needed::

        chembank ukcho extract ...           # same PDF -> same part keys
        chembank ukcho ingest --tagging <prefix>-tags.json --vault vault-ukcho
    """
    vault_dir = Path(vault_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = U.load_ukcho_questions(vault_dir / "questions")
    prefixes = sorted({snapshot_prefix(str(r.get("id") or "")) for r in records} - {""})
    if prefix:
        prefixes = [p for p in prefixes if p == prefix]
    if not prefixes:
        raise ValueError(
            f"no UKChO records under {vault_dir / 'questions'}"
            + (f" for prefix {prefix!r}" if prefix else "")
        )

    written: list[Path] = []
    report: list[dict[str, Any]] = []
    quotes = find_verbatim_quotes(vault_dir)
    for pfx in prefixes:
        snapshot = build_snapshot(vault_dir, pfx)
        leaks = find_content_leaks(snapshot)
        if leaks:
            raise ValueError(
                "refusing to write a snapshot containing past-paper content: "
                + ", ".join(leaks[:5])
            )
        path = out_dir / f"{pfx}-tags.json"
        path.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        written.append(path)
        reviewed = sum(
            1 for e in snapshot["parts"].values()
            if U.is_teacher_authored(e)
        )
        report.append(
            {
                "prefix": pfx,
                "path": path,
                "year": snapshot["year"],
                "parts": len(snapshot["parts"]),
                "reviewed": reviewed,
                "bytes": path.stat().st_size,
                # A tag value may quote the paper even though the field is safe.
                "quotes": [q for q in quotes if snapshot_prefix(q["id"]) == pfx],
            }
        )
    return {"snapshots": report, "written": written}


# ---------------------------------------------------------------------------
# Teacher write-back (workspace edits -> vault)
# ---------------------------------------------------------------------------

def load_edits(path: Path) -> list[dict[str, Any]]:
    """Read a teacher-edits file from the tagging workspace.

    Accepts the ``{"records": [...]}`` envelope the workspace downloads, or a bare
    list. A single record object is also accepted so `ukcho apply`-style hand
    written files keep working.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        records = payload.get("records", payload)
        if isinstance(records, dict) and "id" in records:
            return [records]
        if isinstance(records, list):
            return [r for r in records if isinstance(r, dict)]
        return []
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    return []


def import_edits(
    edits_path: Path,
    vault_dir: Path,
    stamp_source: str = "teacher",
) -> dict[str, Any]:
    """Merge a teacher-edits file into the vault, marking records as reviewed.

    The workspace writes edits to a download rather than to the vault (a static
    page cannot write files), so this is the other half of the loop: edits land on
    disk, get stamped ``tag_source: teacher``, and survive any later re-ingest.

    Only authored fields are merged. Derived fields (ids, parent links, figure
    paths) and question text stay owned by the extract, so a UI payload can never
    corrupt the structure of a record.
    """
    vault_dir = Path(vault_dir)
    questions_dir = vault_dir / "questions"
    edits = load_edits(edits_path)

    updated: list[str] = []
    unchanged: list[str] = []
    missing: list[str] = []
    ignored: list[dict[str, Any]] = []

    for incoming in edits:
        rid = str(incoming.get("id") or "").strip()
        if not rid:
            ignored.append({"reason": "record has no id"})
            continue
        path = questions_dir / f"{rid}.md"
        if not path.exists():
            missing.append(rid)
            continue

        text = path.read_text(encoding="utf-8")
        current = U.normalize_record(
            U.parse_frontmatter(text), fallback_id=str(rid)
        )
        merged = dict(current)
        for field in PRESERVED_FIELDS:
            if field in incoming:
                merged[field] = incoming[field]

        # The file *is* the teacher's decision, so stamp provenance explicitly
        # rather than trusting the payload to carry it.
        merged["tag_source"] = str(incoming.get("tag_source") or stamp_source)
        if not incoming.get("tag_status"):
            merged["tag_status"] = "edited"

        if merged == current:
            unchanged.append(rid)
            continue

        if text.startswith("---"):
            body = U.split_body(text)
        else:
            body = "\n" + text
        path.write_text(
            U.to_frontmatter(U.to_ordered_dict(merged)) + body, encoding="utf-8"
        )
        updated.append(rid)

    errors: dict[str, list[str]] = {}
    if updated:
        report = U.validate_all(
            [U.normalize_record(U.parse_frontmatter(
                (questions_dir / f"{rid}.md").read_text(encoding="utf-8")),
                fallback_id=rid)
             for rid in updated]
        )
        errors = report["errors"]

    return {
        "considered": len(edits),
        "updated": updated,
        "unchanged": unchanged,
        "missing": missing,
        "ignored": ignored,
        "errors": errors,
    }
