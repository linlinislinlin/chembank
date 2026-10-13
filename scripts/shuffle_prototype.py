#!/usr/bin/env python3
"""Prototype: shuffle MCQ options in a local exam paper (demo).

Reads a pick YAML (e.g. pick/exam-stoich-gas-A.yaml), pulls each MCQ's raw
option text + answer letter from draft/<paper>/qN.txt, shuffles the four
options with a seed, and emits:

  - a console before/after report (so you can eyeball the effect)
  - build/shuffle-demo-<version>-student.md   (typeset, options shuffled)
  - build/shuffle-demo-<version>-answers.md   (teacher key, answer remapped)

This is a proof-of-concept: it only shuffles *text* options (single-line and
one-per-line). Table / picture options are flagged as "manual" and left alone.

Usage:
    python3 scripts/shuffle_prototype.py pick/exam-stoich-gas-A.yaml --seed 42
"""
from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DRAFT = REPO / "draft"

# CIE session -> season letter used in draft dirs (9701_<season><yy>_qp_<paper>)
SESSION_SEASON = {"fm": "m", "mj": "s", "on": "w"}

QID_RE = re.compile(r"cie-9701-(\d{4})-(\w+)-p(\d+)-q(\d+)", re.IGNORECASE)
ANS_RE = re.compile(r"Answer:\s*([A-Da-d])")

# Options all on one line: "A x B y C z D w"
SINGLE_LINE_RE = re.compile(r"(?<!\S)([ABCD])\s+", re.IGNORECASE)


def parse_qid(qid: str) -> dict | None:
    m = QID_RE.match(qid)
    if not m:
        return None
    year, session, paper, qnum = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
    season = SESSION_SEASON.get(session, session[0])
    return {
        "year": year,
        "session": session,
        "season": season,
        "yy": year[2:],
        "paper": paper,
        "qnum": qnum,
    }


def find_raw_txt(parts: dict) -> Path | None:
    """Return draft/9701_<season><yy>_qp_<paper>/q<num>.txt if it exists."""
    for suffix in (f"{parts['season']}{parts['yy']}",):
        d = DRAFT / f"9701_{suffix}_qp_{parts['paper']}"
        for name in (f"q{parts['qnum']}.txt", f"q{int(parts['qnum']):02d}.txt"):
            p = d / name
            if p.is_file():
                return p
    return None


def parse_raw(text: str) -> dict:
    """Split raw qN.txt into stem, options [(letter, content)], answer letter."""
    text = text.replace("\r\n", "\n")
    # Cut off the mark-scheme footer.
    body, _, _ = text.partition("--- MARK SCHEME ---")
    m = ANS_RE.search(text)
    answer = m.group(1).upper() if m else None

    lines = body.splitlines()

    # Detect single-line options: a line that contains >=2 option markers.
    single_line = None
    for i, ln in enumerate(lines):
        markers = [mm.start() for mm in SINGLE_LINE_RE.finditer(ln)]
        if len(markers) >= 4:
            single_line = i
            break

    if single_line is not None:
        stem = "\n".join(lines[:single_line]).strip()
        opt_line = lines[single_line]
        # Split on "A ".."D " boundaries.
        parts = re.split(r"\s+(?=[ABCD]\s)", opt_line.strip())
        options = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            options.append((p[0].upper(), p[1:].strip()))
        return {"stem": stem, "options": options, "answer": answer,
                "kind": "text"}

    # Otherwise: one option per line (may wrap). Find the A..D block.
    first_opt = None
    for i, ln in enumerate(lines):
        if re.match(r"^[ABCD]\s", ln.strip()):
            first_opt = i
            break
    if first_opt is None:
        return {"stem": body.strip(), "options": [], "answer": answer,
                "kind": "unknown"}

    stem_lines = lines[:first_opt]
    # Detect a table header: the line(s) right before options that aren't part
    # of the sentence stem (heuristic: short, no trailing punctuation).
    options = []
    i = first_opt
    while i < len(lines):
        ln = lines[i].strip()
        m = re.match(r"^([ABCD])\s+(.*)$", ln)
        if not m:
            # continuation of previous option
            if options:
                letter, content = options[-1]
                options[-1] = (letter, content + " " + ln)
            i += 1
            continue
        options.append((m.group(1).upper(), m.group(2).strip()))
        i += 1

    # Heuristic: if the last stem line is short and option rows look tabular
    # (the header sits just above "A/B/C/D"), treat it as a table header.
    kind = "text"
    if stem_lines and len(options) == 4:
        header = stem_lines[-1].strip()
        if header and not re.search(r"[.?!:]$", header) and len(header) < 60:
            kind = "table"

    return {"stem": "\n".join(stem_lines).strip(), "options": options,
            "answer": answer, "kind": kind}


def shuffle_options(options: list, answer: str | None, rng: random.Random):
    """Shuffle options; relabel A/B/C/D in new order + remap answer letter."""
    order = list(range(len(options)))
    rng.shuffle(order)
    new_opts: list[tuple[str, str]] = []
    new_answer = None
    for new_i, old_i in enumerate(order):
        letter, content = options[old_i]
        new_letter = "ABCD"[new_i]
        new_opts.append((new_letter, content))
        if letter == answer:
            new_answer = new_letter
    return new_opts, new_answer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pick", help="path to pick/<exam>.yaml")
    ap.add_argument("--seed", type=int, default=42, help="shuffle seed")
    ap.add_argument("--version", default="A", help="version label (A/B/C)")
    args = ap.parse_args()

    pick_path = Path(args.pick)
    if not pick_path.is_file():
        print(f"找不到 pick 文件：{pick_path}", file=sys.stderr)
        return 1
    data = yaml.safe_load(pick_path.read_text(encoding="utf-8")) or {}
    ids = data.get("include_ids") or []
    title = data.get("title") or pick_path.stem

    rng = random.Random(args.seed)

    student_lines: list[str] = [f"# {title} — shuffled (seed={args.seed})", ""]
    answer_lines: list[str] = [f"# {title} — 教师答案 (seed={args.seed})", ""]
    manual: list[str] = []

    mcq_total = sum(1 for qid in ids if re.search(r"-p1\d-q", qid))
    print("=" * 72)
    print(f"文件：{pick_path.name}    seed={args.seed}    MCQ={mcq_total}")
    print("=" * 72)

    q_no = 0
    for qid in ids:
        parts = parse_qid(qid)
        if not parts:
            continue
        # MCQ = paper number starting with '1' (Paper 1x).
        if not parts["paper"].startswith("1"):
            continue
        raw = find_raw_txt(parts)
        q_no += 1
        if raw is None:
            manual.append(f"{qid}: 找不到 draft 原文")
            student_lines.append(f"{q_no}. {qid}  [NO RAW — manual]")
            answer_lines.append(f"{q_no}. {qid}  [manual]")
            continue

        parsed = parse_raw(raw.read_text(encoding="utf-8"))
        opts = parsed["options"]
        answer = parsed["answer"]
        if not opts or len(opts) != 4:
            manual.append(f"{qid}: 选项解析失败 ({parsed['kind']})")
            student_lines.append(f"{q_no}. {qid}  [OPTIONS UNSHARED — manual]")
            answer_lines.append(f"{q_no}. {qid}  [manual]")
            continue
        if parsed["kind"] == "table":
            # Shuffle table rows (letter + content stay together).
            new_opts, new_answer = shuffle_options(opts, answer, rng)
        else:
            new_opts, new_answer = shuffle_options(opts, answer, rng)

        # ---- console before/after ----
        orig = " | ".join(f"{L} {c}" for L, c in opts)
        shuf = " | ".join(f"{L} {c}" for L, c in new_opts)
        print(f"\nQ{q_no}  {qid}")
        print(f"  答案 {answer}  →  {new_answer}")
        print(f"  原:  {orig}")
        print(f"  乱:  {shuf}")

        # ---- student markdown ----
        stem = parsed["stem"].strip()
        student_lines.append(f"## {q_no}. {qid}")
        student_lines.append("")
        student_lines.append(stem)
        student_lines.append("")
        for L, c in new_opts:
            student_lines.append(f"- **{L}** {c}")
        student_lines.append("")

        # ---- teacher answer key ----
        ans_content = next((c for L, c in new_opts if L == new_answer), "")
        answer_lines.append(f"## {q_no}. {qid}")
        answer_lines.append(f"- 正确答案：**{new_answer}**  ({ans_content})")
        answer_lines.append("")

    print("\n" + "=" * 72)
    if manual:
        print("需人工处理：")
        for m in manual:
            print("  -", m)
    else:
        print("全部 14 道 MCQ 均自动乱序成功。")

    # Write outputs.
    out_dir = REPO / "build"
    out_dir.mkdir(parents=True, exist_ok=True)
    student_path = out_dir / f"shuffle-demo-{args.version}-student.md"
    answer_path = out_dir / f"shuffle-demo-{args.version}-answers.md"
    student_path.write_text("\n".join(student_lines), encoding="utf-8")
    answer_path.write_text("\n".join(answer_lines), encoding="utf-8")
    print(f"\n学生卷：{student_path}")
    print(f"答案卷：{answer_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
