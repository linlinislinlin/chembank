#!/usr/bin/env python3
"""Build the ChemBank quiz web app from the Obsidian vault exports.

Reads:
  - questions/*.md            (Paper 1 MCQ; each question rendered as a -paper.png image)
  - vault/assets/              (the source PNG files)
  - vault/syllabus/*.md        (syllabus topic titles, for the nav tree)

Writes (into quiz-app/site/):
  - site/assets/*.png          (flattened copies, one per question image)
  - site/data.js               (QUESTIONS array + SYLLABUS tree + stats)
  - site/index.html            (copied from quiz-app/index.html if present)
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = REPO / "questions"
ASSETS_DIR = REPO / "vault" / "assets"
SYLLABUS_DIR = REPO / "vault" / "syllabus"
SITE_DIR = Path(__file__).resolve().parent / "site"
OUT_ASSETS = SITE_DIR / "assets"
OUT_DATA = SITE_DIR / "data.js"
INDEX_SRC = Path(__file__).resolve().parent / "index.html"
INDEX_DST = SITE_DIR / "index.html"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
EMBED_RE = re.compile(r"!\[\[([^\]]+?)\]\]")


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def extract_question_body(text: str) -> str:
    """Return the plain-text question body (between '## Question' and '## Mark Scheme')."""
    lines = text.splitlines()
    out: list[str] = []
    in_question = False
    for line in lines:
        if line.strip().startswith("## Question"):
            in_question = True
            continue
        if line.strip().startswith("## "):
            if in_question:
                break
            continue
        if in_question:
            # strip the Obsidian image embed -> keep the alt text summary only
            line = EMBED_RE.sub(lambda m: f"[图]{m.group(1)}", line)
            out.append(line)
    return "\n".join(out).strip()


def build_syllabus_index() -> dict[str, str]:
    """Map syllabus code -> title using vault/syllabus/<code>.md frontmatter."""
    index: dict[str, str] = {}
    for f in SYLLABUS_DIR.glob("*.md"):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        code = fm.get("code")
        if code is None:
            continue
        title = str(fm.get("title", ""))
        if not title:
            title = f.stem
        index[code] = title
    return index


def syllabus_tree(codes_with_titles: dict[str, str]) -> list[dict]:
    """Turn {code: title} (e.g. '1.1', '2') into a nested tree grouped by top level."""
    roots: dict[str, dict] = {}

    def ensure(code: str, title: str) -> dict:
        parts = code.split(".")
        top = parts[0]
        if top not in roots:
            node = {"code": top, "title": title, "children": []}
            roots[top] = node
            return node
        return roots[top]

    def find_child(node: dict, code: str) -> dict | None:
        for c in node["children"]:
            if c["code"] == code:
                return c
        return None

    # Sort numerically-aware so 2 < 10
    ordered = sorted(codes_with_titles.items(),
                     key=lambda kv: [int(p) for p in kv[0].split(".")])
    for code, title in ordered:
        parts = code.split(".")
        # top-level topic code "1" -> just the title row
        if len(parts) == 1:
            node = ensure(code, title)
            node.setdefault("count", 0)
            continue
        # sub-topic "1.1" belongs under root "1"
        root = ensure(parts[0], "")
        parent = find_child(root, parts[0])
        if parent is None:
            parent = {"code": parts[0], "title": "", "children": []}
            root["children"].append(parent)
        child = find_child(parent, code)
        if child is None:
            child = {"code": code, "title": title, "count": 0}
            parent["children"].append(child)
        child["count"] = 0  # placeholder; real count filled later
    return list(roots.values())


def content_hash(questions: list[dict], tree: list[dict]) -> str:
    """Content-addressed version: changes whenever the question set or syllabus tree does."""
    blob = json.dumps(
        {"q": questions, "t": tree},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def main() -> int:
    OUT_ASSETS.mkdir(parents=True, exist_ok=True)

    md_files = sorted(QUESTIONS_DIR.glob("*.md"))
    if not md_files:
        print("No questions found under", QUESTIONS_DIR, file=sys.stderr)
        return 1

    syllabus_index = build_syllabus_index()
    questions: list[dict] = []
    syllabus_counts: dict[str, int] = {}
    seen_assets: dict[str, str] = {}
    copied = failed = 0
    errors: list[str] = []

    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        qid = fm.get("id") or md_path.stem
        figures: list[str] = fm.get("figures") or []
        # Resolve each embedded image to a source file in vault/assets/
        local_figs: list[str] = []
        for fig_rel in figures:
            # figures are like "assets/<id>-paper.png"
            name = Path(fig_rel).name
            src = ASSETS_DIR / name
            if not src.exists():
                errors.append(f"missing asset {name} for {qid}")
                continue
            # flatten to a unique dest name
            if name not in seen_assets:
                dest = OUT_ASSETS / name
                shutil.copy2(src, dest)
                seen_assets[name] = name
                copied += 1
            local_figs.append("assets/" + name)

        codes = [str(c) for c in (fm.get("syllabus_codes") or [])]
        for c in codes:
            syllabus_counts[c] = syllabus_counts.get(c, 0) + 1

        topic_titles = fm.get("topic_titles") or []
        learning = fm.get("learning_outcomes") or []
        learning_texts = fm.get("learning_outcome_texts") or []

        questions.append(
            {
                "id": qid,
                "year": fm.get("year"),
                "session": fm.get("session"),
                "paper": fm.get("paper"),
                "question": fm.get("question"),
                "marks": fm.get("marks"),
                "difficulty": fm.get("difficulty"),
                "ms_answer": (fm.get("ms_answer") or "").strip(),
                "codes": codes,
                "topics": topic_titles,
                "learning_outcomes": learning,
                "learning_outcome_texts": learning_texts,
                "figures": local_figs,
                "body": extract_question_body(text)[:1200],
            }
        )

    # Build navigation tree with counts = unique questions per node.
    code_titles = {}
    for code in syllabus_counts:
        title = syllabus_index.get(code, syllabus_index.get(code.split(".")[0], code))
        code_titles[code] = title
    tree = syllabus_tree(code_titles)

    # Precompute, for each question, its set of codes.
    q_codes = [(q["id"], set(q["codes"])) for q in questions]

    def attach_counts(node: dict) -> int:
        # count unique questions whose codes intersect this node's subtree
        def all_codes(n):
            return [n["code"]] + [c for ch in (n.get("children") or []) for c in all_codes(ch)]
        n_codes = set(all_codes(node))
        unique = set()
        for qid, cs in q_codes:
            if cs & n_codes:
                unique.add(qid)
        count = len(unique)
        node["count"] = count
        if not node["title"]:
            node["title"] = syllabus_index.get(node["code"], node["code"])
        return count

    for root in tree:
        attach_counts(root)

    if not questions:
        print("No questions parsed.", file=sys.stderr)
        return 1

    payload = {
        "generated": "chembank-quiz",
        "version": content_hash(questions, tree),
        "builtAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stats": {"total": len(questions)},
        "questions": questions,
        "syllabus": tree,
    }

    js = (
        "// Generated by quiz-app/build.py — do not edit by hand.\n"
        "window.CHEMBANK_DATA = "
        + json.dumps(payload, ensure_ascii=False)
        + ";\n"
    )
    OUT_DATA.write_text(js, encoding="utf-8")

    # Copy front-end pages/assets into site/ (any quiz-app/*.{html,js}).
    FRONTEND_SOURCES = [INDEX_SRC, INDEX_SRC.parent / "assign.html",
                        INDEX_SRC.parent / "homework.html", INDEX_SRC.parent / "stats.html",
                        INDEX_SRC.parent / "config.js", INDEX_SRC.parent / "supabase-client.js"]
    for src in FRONTEND_SOURCES:
        if src.exists():
            shutil.copy2(src, SITE_DIR / src.name)

    print(
        f"OK: {len(questions)} questions, {copied} assets, "
        f"{len(tree)} top-level syllabus nodes."
    )
    if errors:
        print(f"WARN: {len(errors)} asset problems:")
        for e in errors[:20]:
            print("  -", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
