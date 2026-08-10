#!/usr/bin/env python3
"""Validate syllabus_codes / learning_outcomes against the 9701 taxonomy."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from chembank.syllabus import (  # noqa: E402
    flatten_codes,
    flatten_learning_outcomes,
    load_syllabus,
)

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _front_from_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
        return data if isinstance(data, dict) else {}

    m = FM_RE.match(text)
    if not m:
        raise ValueError(f"No YAML frontmatter: {path}")
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("PyYAML required: pip install PyYAML") from exc
    front = yaml.safe_load(m.group(1)) or {}
    return front


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "Usage: validate_codes.py <question.md|tagged.json>...",
            file=sys.stderr,
        )
        return 2

    syllabus = load_syllabus()
    allowed_codes = flatten_codes(syllabus)
    allowed_los = flatten_learning_outcomes(syllabus)
    errors = 0
    for raw in argv[1:]:
        path = Path(raw)
        try:
            front = _front_from_file(path)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {path}: {exc}")
            errors += 1
            continue
        codes = [str(c) for c in front.get("syllabus_codes") or []]
        lo_ids = [str(c) for c in front.get("learning_outcomes") or []]
        if not codes:
            print(f"FAIL {path}: empty syllabus_codes")
            errors += 1
            continue
        if not lo_ids:
            print(f"FAIL {path}: empty learning_outcomes (every question needs ≥1 LO id)")
            errors += 1
            continue
        bad = [c for c in codes if c not in allowed_codes]
        bad_lo = [c for c in lo_ids if c not in allowed_los]
        if bad or bad_lo:
            msg = []
            if bad:
                msg.append(f"unknown codes {bad}")
            if bad_lo:
                msg.append(f"unknown learning_outcomes {bad_lo}")
            print(f"FAIL {path}: {'; '.join(msg)}")
            errors += 1
        else:
            titles = [allowed_codes[c] for c in codes]
            print(f"OK   {path}: {list(zip(codes, titles))} los={lo_ids}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
