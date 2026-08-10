"""Load and validate syllabus taxonomy codes and learning outcomes."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SYLLABUS = ROOT / "syllabus" / "cie-9701-as-a-level-chemistry.yaml"

# Subtopic code, then -N or -Na (lettered LO parts)
LO_ID_RE = re.compile(r"^(\d{1,2}\.\d{1,2})-(\d{1,2})([a-z])?$")


def load_syllabus(path: Path | None = None) -> dict[str, Any]:
    syllabus_path = path or DEFAULT_SYLLABUS
    with syllabus_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "topics" not in data:
        raise ValueError(f"Invalid syllabus file: {syllabus_path}")
    return data


def flatten_codes(syllabus: dict[str, Any]) -> dict[str, str]:
    """Return {code: title} for topics and subtopics."""
    codes: dict[str, str] = {}
    for topic in syllabus.get("topics", []):
        code = str(topic["code"])
        title = str(topic["title"])
        level = topic.get("level")
        if level:
            title = f"{title} [{level}]"
        codes[code] = title
        for sub in topic.get("subtopics", []) or []:
            codes[str(sub["code"])] = str(sub["title"])
    return codes


def flatten_learning_outcomes(syllabus: dict[str, Any]) -> dict[str, str]:
    """Return {lo_id: text} for all learning outcomes in the syllabus YAML."""
    out: dict[str, str] = {}
    for topic in syllabus.get("topics", []):
        for sub in topic.get("subtopics", []) or []:
            for lo in sub.get("learning_outcomes") or []:
                lo_id = str(lo["id"])
                out[lo_id] = str(lo["text"])
    return out


def parent_code_for_lo(lo_id: str) -> str:
    """Return parent subtopic code for an LO id (e.g. 3.1-1 → 3.1)."""
    m = LO_ID_RE.match(lo_id.strip())
    if not m:
        raise ValueError(f"Invalid learning outcome id: {lo_id}")
    return m.group(1)


def resolve_titles(codes: list[str], syllabus: dict[str, Any] | None = None) -> list[str]:
    lookup = flatten_codes(syllabus or load_syllabus())
    missing = [c for c in codes if c not in lookup]
    if missing:
        raise KeyError(f"Unknown syllabus code(s): {', '.join(missing)}")
    return [lookup[c] for c in codes]


def resolve_learning_outcomes(
    lo_ids: list[str], syllabus: dict[str, Any] | None = None
) -> list[str]:
    """Resolve LO ids to official syllabus wording. Raises KeyError if unknown."""
    lookup = flatten_learning_outcomes(syllabus or load_syllabus())
    missing = [x for x in lo_ids if x not in lookup]
    if missing:
        raise KeyError(f"Unknown learning outcome id(s): {', '.join(missing)}")
    return [lookup[x] for x in lo_ids]


def validate_learning_outcomes(
    lo_ids: list[str],
    *,
    syllabus: dict[str, Any] | None = None,
    allowed: set[str] | None = None,
) -> list[str]:
    """Validate LO ids against vocabulary; return de-duplicated list (order preserved)."""
    data = syllabus or load_syllabus()
    vocab = allowed if allowed is not None else set(flatten_learning_outcomes(data))
    out: list[str] = []
    for raw in lo_ids:
        lo_id = str(raw).strip()
        if lo_id not in vocab:
            raise ValueError(f"Unknown or disallowed learning outcome id: {lo_id}")
        if lo_id not in out:
            out.append(lo_id)
    return out


def list_codes(path: Path | None = None) -> list[tuple[str, str]]:
    lookup = flatten_codes(load_syllabus(path))
    return sorted(lookup.items(), key=lambda item: _code_sort_key(item[0]))


def list_learning_outcomes(
    path: Path | None = None,
    *,
    code: str | None = None,
    as_only: bool = False,
) -> list[tuple[str, str, str]]:
    """Return [(lo_id, parent_code, text), ...], optionally filtered by parent code."""
    syllabus = load_syllabus(path)
    rows: list[tuple[str, str, str]] = []
    as_majors: set[str] | None = None
    if as_only:
        as_majors = {
            str(t["code"]) for t in syllabus["topics"] if t.get("level") == "AS"
        }

    for topic in syllabus.get("topics", []):
        major = str(topic["code"])
        if as_majors is not None and major not in as_majors:
            continue
        for sub in topic.get("subtopics", []) or []:
            parent = str(sub["code"])
            if code is not None and parent != str(code) and major != str(code):
                # allow --code 3 to mean all 3.x, or --code 3.1 exact
                if "." in str(code):
                    continue
                if parent.split(".")[0] != str(code):
                    continue
            for lo in sub.get("learning_outcomes") or []:
                rows.append((str(lo["id"]), parent, str(lo["text"])))

    rows.sort(key=lambda item: _lo_sort_key(item[0]))
    return rows


def as_only_codes(path: Path | None = None) -> list[tuple[str, str]]:
    """Codes for AS topics 1–22 (and their subtopics)."""
    syllabus = load_syllabus(path)
    allowed_majors = {
        str(t["code"]) for t in syllabus["topics"] if t.get("level") == "AS"
    }
    out: list[tuple[str, str]] = []
    for code, title in list_codes(path):
        major = code.split(".")[0]
        if major in allowed_majors:
            out.append((code, title))
    return out


def as_only_learning_outcomes(path: Path | None = None) -> list[tuple[str, str, str]]:
    return list_learning_outcomes(path, as_only=True)


def _code_sort_key(code: str) -> tuple[int, ...]:
    parts = code.split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return (999,)


def _lo_sort_key(lo_id: str) -> tuple[Any, ...]:
    m = LO_ID_RE.match(lo_id)
    if not m:
        return (999, 0, 0, "")
    major, minor = m.group(1).split(".")
    num = int(m.group(2))
    letter = m.group(3) or ""
    return (int(major), int(minor), num, letter)
