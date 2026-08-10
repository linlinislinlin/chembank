"""Select questions from the ChemBank draft corpus using a rules YAML.

Kept dependency-light on purpose: stdlib only (pathlib, json, re, random).
The canonical question data lives in ``draft/<paper_id>/tagged/q*.json``
(see ``schema/question.schema.json``). ``select`` reads every valid question
there, applies the rule filters, dedupes by question id, sorts, and writes a
pick-list JSON that ``assemble`` turns into an Obsidian tile-grid handout.
"""

from __future__ import annotations

import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Question JSON sidecar location: draft/<paper_id>/tagged/q*.json
TAGGED_GLOB = "tagged/q*.json"

# Field names used to coordinate between select.py and assemble.py. Keep the
# pick JSON small: the full tagged record would bloat it and duplicate the
# source-of-truth draft JSON. We only persist what the tile renderer needs.
PICK_FIELDS = [
    "id",
    "exam_board",
    "syllabus_code",
    "level",
    "year",
    "session",
    "paper",
    "question",
    "parent_question",
    "part",
    "marks",
    "syllabus_codes",
    "learning_outcomes",
    "learning_outcome_texts",
    "topic_titles",
    "question_type",
    "practical_topic",
    "difficulty",
    "ms_answer",
    "figures",
    "body",
    "source_qp",
    "source_ms",
    "page_qp",
    "page_ms",
]


class RuleError(ValueError):
    """Raised when a selection rules YAML is malformed."""


def _slugify(text: str) -> str:
    """Lowercase, keep ASCII alnum + `-`/`_`, else underscore."""
    text = text.strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9_\-]", "_", text)
    text = re.sub(r"_+", "-", text).strip("-")
    return text


def _pick_field(data: dict[str, Any], field: str):
    """Read a field from a question record with tolerant defaults."""
    value = data.get(field)
    if value is None and field == "marks":
        return None
    return value


def load_rules(path: str | Path) -> dict[str, Any]:
    """Load and validate a selection rules YAML."""
    path = Path(path)
    if not path.is_file():
        raise RuleError(f"Rules file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuleError(f"Rules file {path} must map to a top-level mapping")
    rules: dict[str, Any] = dict(raw)

    title = rules.get("title")
    if not title or not str(title).strip():
        raise RuleError(f"Rules file {path}: `title` is required")
    rules["title"] = str(title).strip()

    codes = rules.get("syllabus_codes")
    if codes is not None:
        if not isinstance(codes, list) or not codes:
            raise RuleError(f"Rules file {path}: `syllabus_codes` must be a non-empty list")
        rules["syllabus_codes"] = [str(c).strip() for c in codes if str(c).strip()]

    for key in ("year_min", "year_max", "max_marks", "difficulty_min", "difficulty_max", "count"):
        value = rules.get(key)
        if value is None:
            continue
        if not isinstance(value, int) or isinstance(value, bool):
            raise RuleError(f"Rules file {path}: `{key}` must be an integer")
        rules[key] = value

    exclude_after = rules.get("exclude_after")
    if exclude_after is not None:
        # Optional cutoff code (e.g. "5.2"): keep only questions whose codes
        # are ALL strictly before this code. Tolerant of formatting; the key
        # helper handles weird / non-numeric values gracefully at match time.
        if not isinstance(exclude_after, str) or not str(exclude_after).strip():
            raise RuleError(f"Rules file {path}: `exclude_after` must be a non-empty string")
        rules["exclude_after"] = str(exclude_after).strip()

    sort = rules.get("sort", "year,question")
    if not isinstance(sort, (str, list)) or (isinstance(sort, list) and not sort):
        raise RuleError(f"Rules file {path}: `sort` must be a string or non-empty list")
    if isinstance(sort, str):
        rules["sort"] = [s.strip() for s in sort.split(",") if s.strip()]

    if "shuffle" in rules:
        if not isinstance(rules["shuffle"], bool):
            raise RuleError(f"Rules file {path}: `shuffle` must be a boolean")

    rules.setdefault("sort", ["year", "question"])
    rules.setdefault("shuffle", False)
    rules.setdefault("topic_title", None)
    rules.setdefault("question_type", None)
    rules.setdefault("count", None)
    return rules


def load_all_questions(docs_dir: str | Path = "draft") -> list[dict[str, Any]]:
    """Glob every tagged question JSON under ``docs_dir`` and return valid dicts.

    Invalid / non-JSON files are skipped instead of crashing, so a corrupt
    sidecar does not take down the whole selection.
    """
    docs_dir = Path(docs_dir)
    questions: list[dict[str, Any]] = []
    if not docs_dir.is_dir():
        return questions
    for path in sorted(docs_dir.rglob(TAGGED_GLOB)):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        if not isinstance(data, dict) or not data.get("id"):
            continue
        # Some older sidecars may not carry syllabus_codes; give them an empty
        # list so the caller can still sort/filter without crashing.
        data.setdefault("syllabus_codes", [])
        questions.append(data)
    return questions


def _code_key(code: str) -> tuple[int, int]:
    """Map a syllabus code like ``"5.1"``/``"23.1"`` to a numeric (topic, subtopic) key.

    ``"5"`` → (5, 0). Non-numeric payloads (e.g. ``"5.1b"`` suffixes or garbage)
    map subtopic to a very large sentinel so ordering stays deterministic and
    such codes rank at-or-after any real cutoff (they get rejected by
    ``exclude_after`` unless that behaviour is explicitly tolerated elsewhere).
    """
    text = str(code).strip()
    topic, sep, sub = text.partition(".")
    try:
        t = int(topic)
    except ValueError:
        t = 10**9
    if sep:
        # Take the leading-digit subtopic and ignore any part suffix
        # (e.g. "5.1b" -> subtopic 1), so part variants rank with their topic.
        head = re.match(r"\d+", sub)
        s = int(head.group(0)) if head else 10**9
    else:
        s = 0
    return (t, s)


def _matches_rules(data: dict[str, Any], rules: dict[str, Any]) -> bool:
    codes = [str(c) for c in (data.get("syllabus_codes") or [])]
    wanted = rules.get("syllabus_codes")
    if wanted and not any(c in wanted for c in codes):
        return False

    exclude_after = rules.get("exclude_after")
    if exclude_after and codes:
        cutoff = _code_key(exclude_after)
        # Reject if ANY code hits a topic at-or-after the cutoff, so earlier /
        # shallower companion codes (e.g. 2.3 alongside 5.1) remain allowed.
        if any(_code_key(c) >= cutoff for c in codes):
            return False

    topic_title = rules.get("topic_title")
    if topic_title:
        titles = [str(t) for t in (data.get("topic_titles") or [])]
        if not any(topic_title.lower() in t.lower() for t in titles):
            return False

    qtype = rules.get("question_type")
    if qtype and str(data.get("question_type") or "").lower() != str(qtype).lower():
        return False

    year = data.get("year")
    if rules.get("year_min") is not None and (year is None or year < rules["year_min"]):
        return False
    if rules.get("year_max") is not None and (year is None or year > rules["year_max"]):
        return False

    difficulty = data.get("difficulty")
    if rules.get("difficulty_min") is not None:
        if difficulty is None or difficulty < rules["difficulty_min"]:
            return False
    if rules.get("difficulty_max") is not None:
        if difficulty is None or difficulty > rules["difficulty_max"]:
            return False

    marks = data.get("marks")
    if rules.get("max_marks") is not None:
        if marks is None or marks > rules["max_marks"]:
            return False
    return True


def select_questions(
    rules: dict[str, Any],
    docs_dir: str | Path = "draft",
    category: str = "all",
) -> list[dict[str, Any]]:
    """Filter the corpus by ``rules`` and return a deduped, limited question list.

    ``category`` is informational (e.g. which vault a question exports to) and
    recorded on each pick entry; it does not affect filtering.
    """
    from chembank.registry import default_vault_for_paper, paper_kind

    docs = [d for d in load_all_questions(docs_dir) if _matches_rules(d, rules)]

    # Dedupe by stable question id, keeping the first occurrence.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for d in docs:
        qid = str(d["id"])
        if qid in seen:
            continue
        seen.add(qid)
        unique.append(d)

    sort_spec: list[str] = [s for s in rules.get("sort", ["year", "question"])]

    def _sort_key(d: dict[str, Any]) -> tuple[Any, ...]:
        out: list[Any] = []
        for field in sort_spec:
            if field == "question":
                # Numerical questions first, then string part labels.
                out.append(_question_sort_key(str(d.get("question") or "")))
            elif field in ("year", "marks"):
                out.append(d.get(field) if d.get(field) is not None else -1)
            else:
                out.append(str(d.get(field) or ""))
        return tuple(out)

    if rules.get("no_sort"):
        result = unique
    else:
        result = sorted(unique, key=_sort_key)

    if rules.get("shuffle"):
        rng = random.Random(rules.get("seed"))
        rng.shuffle(result)

    count = rules.get("count")
    result = result[:count] if count else result

    # Attach pick metadata (vault hint + category) to each entry.
    for d in result:
        paper = d.get("paper")
        try:
            vault = default_vault_for_paper(paper).name if paper is not None else None
        except (TypeError, ValueError):
            vault = None
        d["_vault"] = vault
        d["_category"] = category
    return result


def _question_sort_key(label: str) -> tuple[Any, ...]:
    """`7` before `10`, `2(a)` grouped after the shared integer part."""
    head = re.match(r"\d+", label)
    num = int(head.group(0)) if head else 10**9
    rest = label[head.end() :] if head else label
    return (num, rest)


def to_pick_entry(data: dict[str, Any], *, source: str) -> dict[str, Any]:
    """Slice a question record down to the fields assemble needs."""
    entry: dict[str, Any] = {}
    for field in PICK_FIELDS:
        entry[field] = data.get(field)
    entry["vault"] = data.get("_vault")
    entry["category"] = data.get("_category", "all")
    entry["source"] = source
    return entry


def write_pick(
    rules: dict[str, Any],
    questions: list[dict[str, Any]],
    path: str | Path,
    *,
    docs_dir: str | Path = "draft",
) -> Path:
    """Write the pick-list JSON (rules + chosen questions) to ``path``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    total = len(load_all_questions(docs_dir))
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_corpus_dir": str(docs_dir),
        "corpus_question_count": total,
        "rules": {k: v for k, v in rules.items() if k != "no_sort"},
        "slug": _slugify(str(rules.get("title") or "handout")),
        "title": rules.get("title"),
        "question_count": len(questions),
        "questions": [
            to_pick_entry(q, source="draft") for q in questions
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_pick(path: str | Path) -> dict[str, Any]:
    """Read a pick-list JSON written by :func:`write_pick`."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
