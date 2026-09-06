#!/usr/bin/env python3
"""Tag remaining 2024 Paper 4 (FM P42, MJ P42, ON P41–43)."""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_9701_tags import apply_tags


def t(*los, skills=("recall",), d=3):
    return {
        "learning_outcomes": list(los),
        "skills": list(skills),
        "difficulty": d,
        "question_type": "structured",
    }


# --- 2024 FM P42 ---
M24_42 = {
    "1a-i": t("23.2-1"),
    "1a-ii": t("23.2-4", "23.4-2", skills=("explain",)),
    "1b-i": t("23.2-4", skills=("explain",)),
    "1b-ii": t("23.2-3", skills=("explain",)),
    "1b-iii": t("23.2-3", skills=("calculate",)),
    "1b-iv": t("25.1-9", skills=("calculate",)),
    "1b-v": t("25.1-10a", skills=("explain",)),
    "1c-i": t("23.3-2a", skills=("calculate",)),
    "1c-ii": t("23.4-2", "23.4-3", skills=("calculate",)),
    "1c-iii": t("23.4-4", skills=("explain",)),
    "1d-i": t("24.1-3a", "24.1-2"),
    "1d-ii": t("24.1-4", skills=("calculate",)),
    "1e-i": t("34.1-1a"),
    "1e-ii": t("34.1-1c"),
    "1e-iii": t("34.1-2"),
    "2a-i": t("25.1-1", "25.1-2"),
    "2a-ii": t("25.1-1", "7.2-3"),
    "2a-iii": t("25.1-1", "2.3-2a"),
    "2b-i": t("25.1-3"),
    "2b-ii": t("25.1-3", skills=("explain",)),
    "2b-iii": t("25.1-4b", skills=("calculate",)),
    "2c-i": t("23.3-1", skills=("explain",)),
    "2c-ii": t("23.3-1", skills=("explain",)),
    "2c-iii": t("23.4-3", skills=("calculate",)),
    "2d-i": t("24.2-4", skills=("calculate",)),
    "2d-ii": t("24.2-8", skills=("calculate",)),
    "3a-i": t("28.1-3a"),
    "3a-ii": t("28.1-3b"),
    "3b-i": t("28.2-1"),
    "3b-ii": t("28.3-3"),
    "3b-iii": t("28.3-5", skills=("explain",)),
    "3b-iv": t("28.2-3a"),
    "3b-v": t("28.2-5"),
    "3c-i": t("28.2-9a", "2.3-2a"),
    "3c-ii": t("28.2-10"),
    "3c-iii": t("28.2-10", skills=("calculate",)),
    "4a-i": t("28.2-3b"),
    "4a-ii": t("28.4-1a", skills=("draw",)),
    "4b-i": t("28.2-4"),
    "4b-ii": t("28.2-6b"),
    "4b-iii": t("37.3-1a"),
    "4b-iv": t("28.1-3c"),
    "4c-i": t("33.1-1a"),
    "4c-ii": t("33.3-3", skills=("draw",)),
    "5a-i": t("30.1-2a"),
    "5a-ii": t("30.1-3", skills=("draw",)),
    "5a-iii": t("30.1-1f", "2.3-2a"),
    "5a-iv": t("21.1-3"),
    "5a-v": t("13.2-1f"),
    "5a-vi": t("33.2-1a"),
    "5a-vii": t("13.4-4"),
    "5a-viii": t("37.4-1a"),
    "5b-i": t("37.2-1c"),
    "5b-ii": t("37.2-3"),
    "6a-i": t("32.2-1a"),
    "6a-ii": t("32.2-2a"),
    "6b-i": t("32.2-3"),
    "6b-ii": t("32.2-7"),
    "6b-iii": t("35.1-2a"),
    "6b-iv": t("35.1-2c", skills=("draw",)),
    "6c-i": t("33.1-4"),
    "6c-ii": t("33.3-1a"),
    "6d-i": t("37.2-1a"),
    "6d-ii": t("37.4-2"),
}

# --- 2024 MJ P42 ---
S24_42 = {
    "1a": t("23.2-1"),
    "1b": t("23.2-2"),
    "1c": t("23.2-3", skills=("calculate",)),
    "1d-i": t("23.2-2", skills=("draw",)),
    "2a-i": t("27.1-1", "2.3-2a"),
    "2a-ii": t("27.1-1", skills=("explain",)),
    "2b": t("24.2-4", skills=("calculate",)),
    "2c-i": t("24.2-7", "6.1-3"),
    "2c-ii": t("24.2-5a"),
    "3a": t("23.4-2", "23.3-2a", skills=("calculate",), d=4),
    "3b": t("23.4-4", skills=("explain",)),
    "4a-i": t("28.1-3a"),
    "4a-ii": t("28.1-2", skills=("draw",)),
    "4b": t("28.1-1"),
    "4c": t("28.3-4", skills=("explain",)),
    "4d": t("28.2-3a"),
    "4e-i": t("28.4-1a", skills=("draw",)),
    "4e-ii": t("28.4-1b"),
    "4e-iii": t("28.4-1a"),
    "5a-i": t("26.1-2e"),
    "5a-ii": t("26.1-4a", skills=("calculate",)),
    "5b": t("26.1-5a", "26.2-3a"),
    "5c": t("26.1-6"),
    "6a-i": t("25.1-2"),
    "6a-ii": t("25.1-1", "2.3-2a"),
    "6b-i": t("25.1-3"),
    "6b-ii": t("25.1-4c", skills=("calculate",)),
    "6c-i": t("25.1-5a"),
    "6c-ii": t("25.1-6", skills=("calculate",)),
    "6d-i": t("24.2-7"),
    "6d-ii": t("24.2-4", skills=("calculate",)),
    "7a-i": t("29.1-3"),
    "7a-ii": t("30.1-1c"),
    "7a-iii": t("30.1-4", skills=("explain",)),
    "7b-i": t("32.2-2b", skills=("draw",)),
    "7b-ii": t("32.2-3"),
    "8a": t("34.2-1"),
    "8b-i": t("34.2-3", skills=("draw",)),
    "8b-ii": t("34.2-3", skills=("explain",)),
    "8c": t("34.1-1a"),
    "8d": t("34.4-2"),
    "8e-i": t("35.1-2a"),
    "8e-ii": t("35.1-2c", skills=("draw",)),
    "8f": t("35.1-1a"),
    "9a": t("33.1-4", skills=("explain",)),
    "9b-i": t("33.3-1a"),
    "9b-ii": t("33.3-3", skills=("draw",)),
    "9b-iii": t("33.3-2a"),
    "9c-i": t("11.3-2a"),
    "9c-ii": t("37.4-2"),
    "9c-iii": t("37.4-1a"),
}

# --- 2024 ON P41 / P43 ---
W24_41 = {
    "1a-i": t("25.1-1"),
    "1a-ii": t("25.1-5a"),
    "1a-iii": t("25.1-5c"),
    "1a-iv": t("25.1-5d"),
    "1b-i": t("25.1-4b", skills=("calculate",)),
    "1b-ii": t("25.1-4b", skills=("explain",)),
    "1b-iii": t("27.1-2"),
    "1c": t("25.1-9", skills=("calculate",)),
    "1d": t("25.1-10a", skills=("explain",)),
    "2a": t("23.2-4", skills=("explain",)),
    "2b-i": t("23.2-2"),
    "2b-ii": t("23.2-4", skills=("explain",)),
    "2b-iii": t("23.2-1"),
    "2b-iv": t("23.2-3"),
    "2c": t("23.2-3", skills=("calculate",)),
    "2d": t("23.2-4", skills=("explain",)),
    "2e": t("23.4-3", skills=("calculate",)),
    "2f": t("23.4-2"),
    "3a-i": t("26.1-2e"),
    "3a-ii": t("26.1-4a", skills=("calculate",)),
    "3a-iii": t("26.1-2b"),
    "3b-i": t("26.2-2b"),
    "3b-ii": t("26.2-2a"),
    "3b-iii": t("26.2-3b"),
    "3b-iv": t("26.2-1"),
    "3c-i": t("28.1-3a"),
    "3c-ii": t("24.2-7", "6.1-2"),
    "4a": t("28.1-6"),
    "4b-i": t("28.2-3b"),
    "4b-ii": t("28.3-2a"),
    "4b-iii": t("28.3-5"),
    "4c-i": t("28.2-9a"),
    "4c-ii": t("28.2-10"),
    "4d-i": t("6.1-2", "24.2-7"),
    "4d-ii": t("2.4-1c", skills=("calculate",)),
    "5a": t("28.2-5"),
    "5b": t("28.2-3a"),
    "5c": t("28.4-1b"),
    "5d": t("28.4-1a"),
    "6a": t("30.1-2a"),
    "6b-i": t("30.1-1a", skills=("draw",)),
    "6b-ii": t("30.1-4"),
    "6c-i": t("30.1-1f"),
    "6c-ii": t("30.1-1f", "2.3-2a"),
    "6c-iii": t("37.3-1a"),
    "6d-i": t("37.4-1c"),
    "6d-ii": t("37.4-2"),
    "6d-iii": t("37.4-2"),
    "6d-iv": t("37.4-2", skills=("explain",)),
    "6e": t("37.3-1a"),
    "7a": t("34.1-1a"),
    "7b": t("34.1-1b"),
    "7c": t("34.1-1c"),
    "7d": t("33.3-1a"),
    "7e": t("34.1-2"),
    "7f": t("34.4-2"),
    "7g": t("34.4-3"),
    "7h": t("34.1-3"),
    "7i": t("21.1-3"),
    "8a": t("34.4-1"),
    "8b-i": t("37.2-1c"),
    "8b-ii": t("37.2-3"),
    "8b-iii": t("37.4-1a"),
    "8c": t("35.1-1a"),
}

# --- 2024 ON P42 ---
W24_42 = {
    "1a-i": t("25.1-3"),
    "1a-ii": t("25.1-4c", skills=("calculate",)),
    "1a-iii": t("25.1-5a"),
    "1a-iv": t("25.1-6", skills=("calculate",)),
    "1b-i": t("25.1-7"),
    "1b-ii": t("25.1-8"),
    "1b-iii": t("25.1-9", skills=("calculate",)),
    "1b-iv": t("25.1-10a"),
    "1c": t("25.1-4b", skills=("calculate",)),
    "2a": t("23.2-1"),
    "2b-i": t("23.2-2"),
    "2b-ii": t("23.2-4", skills=("explain",)),
    "2b-iii": t("23.2-3", skills=("calculate",)),
    "2c": t("23.2-3", skills=("calculate",)),
    "2d": t("23.3-2a", skills=("calculate",)),
    "2e-i": t("23.4-2", skills=("calculate",)),
    "2e-ii": t("23.4-4", skills=("explain",)),
    "3a-i": t("26.1-2c"),
    "3a-ii": t("26.1-2b"),
    "3a-iii": t("26.1-2e"),
    "3a-iv": t("26.1-4a", skills=("calculate",)),
    "3b-i": t("26.2-1"),
    "3b-ii": t("26.2-2a"),
    "3b-iii": t("26.2-3b"),
    "3b-iv": t("26.1-6"),
    "3b-v": t("26.1-5d"),
    "4a-i": t("28.1-1"),
    "4a-ii": t("28.1-6"),
    "4a-iii": t("28.1-3b"),
    "4b-i": t("28.2-1"),
    "4b-ii": t("28.2-3a"),
    "4b-iii": t("28.2-5"),
    "4b-iv": t("28.3-3"),
    "4c-i": t("28.2-10"),
    "4c-ii": t("28.2-9a"),
    "4c-iii": t("24.2-4", skills=("calculate",)),
    "5a": t("28.4-1a"),
    "5b-i": t("28.4-1b"),
    "5b-ii": t("28.2-4"),
    "5c": t("28.3-5"),
    "6a-i": t("30.1-1a"),
    "6a-ii": t("30.1-2a"),
    "6b": t("30.1-3", skills=("draw",)),
    "6c": t("30.1-1f"),
    "6d-i": t("37.4-1c"),
    "6d-ii": t("37.4-2"),
    "6d-iii": t("37.3-1a"),
    "6d-iv": t("37.4-2"),
    "7a": t("13.4-4"),
    "7b-i": t("30.1-3"),
    "7b-ii": t("30.1-3"),
    "7c": t("13.3-2"),
    "7d": t("30.1-2a"),
    "7e": t("30.1-3"),
    "7f-i": t("15.1-5"),
    "7f-ii": t("15.1-3a"),
    "8a": t("13.4-4"),
    "8b": t("13.4-4"),
    "8c": t("13.4-2"),
    "8d": t("13.4-4"),
    "8e": t("35.1-1a"),
    "8f": t("37.4-2"),
    "8g": t("37.3-1a"),
    "8h": t("37.4-1a"),
}


def _drop(draft: Path, *names: str) -> None:
    for n in names:
        p = draft / f"q{n}.txt"
        if p.exists():
            p.unlink()
        tagged = draft / "tagged" / f"q{n}.json"
        if tagged.exists():
            tagged.unlink()


def _promote_s_to_b(draft: Path, romans: tuple[str, ...]) -> None:
    """OCR treated CaF2(s) as letter (s); those romans belong to 2(b)."""
    _drop(draft, "2b", "2g")
    for rom in romans:
        src = draft / f"q2s-{rom}.txt"
        dst = draft / f"q2b-{rom}.txt"
        if src.exists():
            text = src.read_text(encoding="utf-8")
            text = text.replace("\n(s)\n", "\n(b)\n", 1)
            dst.write_text(text, encoding="utf-8")
            src.unlink()
        old_j = draft / "tagged" / f"q2s-{rom}.json"
        if old_j.exists():
            old_j.unlink()
    idx_path = draft / "index.json"
    if idx_path.exists():
        rows = json.loads(idx_path.read_text(encoding="utf-8"))
        out = []
        for r in rows:
            slug = str(r.get("part_slug") or "")
            fname = str(r.get("file") or "")
            if slug in {"2b", "2g"} or fname in {"q2b.txt", "q2g.txt"}:
                continue
            if slug.startswith("2s-") or fname.startswith("q2s-"):
                rom = slug.split("-", 1)[-1] if "-" in slug else fname.replace("q2s-", "").replace(".txt", "")
                r = dict(r)
                r["question"] = f"2(b)({rom})"
                r["part"] = f"(b)({rom})"
                r["part_slug"] = f"2b-{rom}"
                r["file"] = f"q2b-{rom}.txt"
                r["parts"] = [r["part"]]
            out.append(r)
        idx_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    _drop(ROOT / "draft/9701_m24_qp_42", "7")
    _drop(ROOT / "draft/9701_s24_qp_42", "10", "1s-ii")
    _drop(ROOT / "draft/9701_w24_qp_41", "9")
    _drop(ROOT / "draft/9701_w24_qp_42", "9")
    _drop(ROOT / "draft/9701_w24_qp_43", "9")
    _promote_s_to_b(ROOT / "draft/9701_w24_qp_41", ("i", "ii", "iii", "iv"))
    _promote_s_to_b(ROOT / "draft/9701_w24_qp_42", ("i", "ii", "iii"))
    _promote_s_to_b(ROOT / "draft/9701_w24_qp_43", ("i", "ii", "iii", "iv"))
    apply_tags(ROOT / "draft/9701_m24_qp_42", M24_42, as_only=False)
    apply_tags(ROOT / "draft/9701_s24_qp_42", S24_42, as_only=False)
    apply_tags(ROOT / "draft/9701_w24_qp_41", W24_41, as_only=False)
    apply_tags(ROOT / "draft/9701_w24_qp_42", W24_42, as_only=False)
    apply_tags(ROOT / "draft/9701_w24_qp_43", W24_41, as_only=False)


if __name__ == "__main__":
    main()
