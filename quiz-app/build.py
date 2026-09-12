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
STRUCTURED_DIR = REPO / "vault-structured" / "questions"
STRUCTURED_ASSETS = REPO / "vault-structured" / "assets"
IGCSE_QUESTIONS = REPO / "vault-igcse" / "questions"
IGCSE_ASSETS = REPO / "vault-igcse" / "assets"
IGCSE_STRUCTURED_DIR = REPO / "vault-igcse-structured" / "questions"
IGCSE_STRUCTURED_ASSETS = REPO / "vault-igcse-structured" / "assets"
IGCSE_PICKS = REPO / "pick"
UKCHO_QUESTIONS = REPO / "vault-ukcho" / "questions"
#: Committed mock records, used as a fallback when the (gitignored, copyrighted)
#: live vault has not been ingested yet — e.g. on a fresh clone or in CI.
UKCHO_FIXTURES = REPO / "fixtures" / "ukcho-mock" / "questions"
UKCHO_ASSETS = REPO / "vault-ukcho" / "assets"
UKCHO_FIXTURE_ASSETS = REPO / "fixtures" / "ukcho-mock" / "assets"
SITE_DIR = Path(__file__).resolve().parent / "site"
OUT_ASSETS = SITE_DIR / "assets"
OUT_STRUCTURED_ASSETS = SITE_DIR / "assets" / "structured"
OUT_UKCHO_ASSETS = SITE_DIR / "assets" / "ukcho"
OUT_DATA = SITE_DIR / "data.js"
OUT_STRUCTURED_DATA = SITE_DIR / "structured-data.js"
OUT_UKCHO_DATA = SITE_DIR / "ukcho-data.js"
INDEX_SRC = Path(__file__).resolve().parent / "index.html"
INDEX_DST = SITE_DIR / "index.html"

# The UKChO taxonomy lives in the chembank package (single source of truth).
SRC_DIR = REPO / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

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


def build_structured_data() -> tuple[list[dict], int, list[str]]:
    """Build structured-question data (Paper 2/4/5) for the homework/stat pages.

    Reads vault-structured/questions/*.md, copies the *-paper.png and *-ms.png
    images into site/assets/structured/, and returns a list of lightweight
    records (id + display fields + image URLs). Questions without both images
    are skipped so the student page never shows a broken question.
    """
    records: list[dict] = []
    copied = 0
    skips: list[str] = []

    if not STRUCTURED_DIR.is_dir():
        return records, copied, skips

    for md_path in sorted(STRUCTURED_DIR.glob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = parse_frontmatter(text)
        qid = fm.get("id") or md_path.stem
        figures = fm.get("figures") or []
        paper_name = None
        ms_name = None
        for fig_rel in figures:
            name = Path(fig_rel).name
            if name.endswith("-ms.png") and ms_name is None:
                ms_name = name
            elif name.endswith("-paper.png") and paper_name is None:
                paper_name = name

        if not (paper_name and ms_name):
            skips.append(f"{qid} (missing figure entries)")
            continue

        paper_src = STRUCTURED_ASSETS / paper_name
        ms_src = STRUCTURED_ASSETS / ms_name
        if not (paper_src.exists() and ms_src.exists()):
            skips.append(f"{qid} (missing image file)")
            continue

        OUT_STRUCTURED_ASSETS.mkdir(parents=True, exist_ok=True)
        for src in (paper_src, ms_src):
            dest = OUT_STRUCTURED_ASSETS / src.name
            if not dest.exists():
                shutil.copy2(src, dest)
                copied += 1

        records.append({
            "id": qid,
            "type": "structured",
            "year": fm.get("year"),
            "session": fm.get("session"),
            "paper": fm.get("paper"),
            "question": fm.get("question"),
            "marks": fm.get("marks"),
            "topics": fm.get("topic_titles") or [],
            "learning_outcome_texts": fm.get("learning_outcome_texts") or [],
            "paper_img": "assets/structured/" + paper_name,
            "ms_img": "assets/structured/" + ms_name,
        })
    return records, copied, skips


def _ukcho_label(rec: dict) -> str:
    """Human label for a sub-question, e.g. 'Q3(b)' or 'Q3(b)(i)'.

    Delegates to the chembank package so the site, the teacher workspace and the
    tagging prompt can never disagree about how a question is named.
    """
    from chembank import ukcho as U

    return U.question_label(rec)


def _ukcho_sort_key(rec: dict) -> tuple:
    def as_int(value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 999

    year = as_int(rec.get("year"))
    return (-year, as_int(rec.get("question_number")), str(rec.get("sub_question") or ""))


def build_ukcho_data() -> tuple[dict, tuple[int, int], list[str], dict]:
    """Build UKChO records + taxonomy for the tagging and filter pages.

    Reads ``vault-ukcho/questions/*.md`` — one parent record per main question and
    one record per sub-question — attaches sub-questions to their parents, copies
    any assets, and returns ``(payload, (new_assets, total_assets), problems,
    warnings)``. New and total are reported separately because a rebuild usually
    copies nothing, and "0 assets" would read as a failure.

    Sub-questions are kept as independent records: nothing here copies a parent's
    tags down to a sub-question.
    """
    from chembank import ukcho as U

    questions_dir = UKCHO_QUESTIONS
    if not any(questions_dir.glob("*.md")) and any(UKCHO_FIXTURES.glob("*.md")):
        questions_dir = UKCHO_FIXTURES  # fresh clone / CI: fall back to mocks

    records = U.load_ukcho_questions(questions_dir)
    problems: list[str] = []
    parents: list[dict] = []
    parent_by_id: dict[str, dict] = {}
    subs: list[dict] = []

    for rec in records:
        if rec.get("record_type") == "ukcho-parent":
            node = {
                "id": rec["id"],
                "year": rec.get("year"),
                "question_number": rec.get("question_number"),
                "title": rec.get("title") or "",
                "total_marks": rec.get("total_marks"),
                "overall_themes": rec.get("overall_themes") or [],
                "sub_question_ids": rec.get("sub_question_ids") or [],
                "mock": bool(rec.get("mock")),
            }
            parents.append(node)
            parent_by_id[node["id"]] = node
        else:
            sub = U.to_ordered_dict(rec)
            sub["label"] = _ukcho_label(rec)
            subs.append(sub)

    for sub in subs:
        parent = parent_by_id.get(sub.get("parent_question_id") or "")
        sub["parent_title"] = (parent or {}).get("title", "")
        # Page-clip PNGs (the question as it appears on the paper). UKChO parts are
        # answered by drawing structures, so the clip — not the extracted text — is
        # the authoritative rendering of the question.
        sub["figure_urls"] = [
            f"assets/ukcho/{Path(str(f)).name}" for f in (sub.get("figures") or [])
        ]
        if parent is None:
            problems.append(f"{sub.get('id')}: parent_question_id not found in vault")

    subs.sort(key=_ukcho_sort_key)
    parents.sort(key=lambda p: (-(p.get("year") or 0), p.get("question_number") or 0))

    for parent in parents:
        parent["sub_question_ids"] = [
            s["id"] for s in subs if s.get("parent_question_id") == parent["id"]
        ]

    copied = 0
    ukcho_asset_total = 0
    assets_dir = UKCHO_ASSETS if UKCHO_ASSETS.is_dir() and any(
        p for p in UKCHO_ASSETS.glob("*") if not p.name.startswith(".")
    ) else UKCHO_FIXTURE_ASSETS
    if assets_dir.is_dir():
        OUT_UKCHO_ASSETS.mkdir(parents=True, exist_ok=True)
        for src in sorted(assets_dir.glob("*")):
            if not src.is_file() or src.name.startswith("."):
                continue
            ukcho_asset_total += 1
            dest = OUT_UKCHO_ASSETS / src.name
            if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
                shutil.copy2(src, dest)
                copied += 1

    report = U.validate_all(records)
    for qid, errs in report["errors"].items():
        for err in errs:
            problems.append(f"{qid}: {err}")

    payload = {
        "generated": "chembank-ukcho",
        "builtAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stats": {
            "parents": len(parents),
            "subQuestions": len(subs),
            "needsReview": sum(1 for s in subs if s.get("review_required")),
            "suggested": sum(1 for s in subs if s.get("tag_status") == "suggested"),
            "validationErrors": len(report["errors"]),
            "validationWarnings": len(report["warnings"]),
        },
        "taxonomy": U.taxonomy(),
        "parents": parents,
        "questions": subs,
    }
    return payload, (copied, ukcho_asset_total), problems, report["warnings"]


def igcse_homework_ids() -> list[str]:
    """IDs from pick/igcse-*-hw.yaml so published IG homework images stay in site/."""
    ids: list[str] = []
    seen: set[str] = set()
    if not IGCSE_PICKS.is_dir():
        return ids
    for path in sorted(IGCSE_PICKS.glob("igcse-*-hw.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except OSError:
            continue
        for qid in data.get("include_ids") or []:
            qid = str(qid).strip()
            if qid and qid not in seen:
                seen.add(qid)
                ids.append(qid)
    return ids


def copy_igcse_homework_assets() -> tuple[int, list[str]]:
    """Copy paper/MS clips for curated IGCSE homework into site/assets."""
    copied = 0
    missing: list[str] = []
    OUT_ASSETS.mkdir(parents=True, exist_ok=True)
    OUT_STRUCTURED_ASSETS.mkdir(parents=True, exist_ok=True)
    for qid in igcse_homework_ids():
        mcq_paper = IGCSE_ASSETS / f"{qid}-paper.png"
        st_paper = IGCSE_STRUCTURED_ASSETS / f"{qid}-paper.png"
        st_ms = IGCSE_STRUCTURED_ASSETS / f"{qid}-ms.png"
        if mcq_paper.exists():
            dest = OUT_ASSETS / mcq_paper.name
            shutil.copy2(mcq_paper, dest)
            copied += 1
            continue
        if st_paper.exists():
            dest = OUT_STRUCTURED_ASSETS / st_paper.name
            shutil.copy2(st_paper, dest)
            copied += 1
            if st_ms.exists():
                shutil.copy2(st_ms, OUT_STRUCTURED_ASSETS / st_ms.name)
                copied += 1
            else:
                missing.append(f"{qid} (no MS clip)")
            continue
        missing.append(qid)
    return copied, missing


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

    # Build structured-question data (Paper 2/4/5) for mixed-type homework.
    s_records, s_copied, s_skips = build_structured_data()
    s_payload = {
        "generated": "chembank-structured",
        "builtAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stats": {"total": len(s_records)},
        "questions": s_records,
    }
    s_js = (
        "// Generated by quiz-app/build.py — do not edit by hand.\n"
        "window.STRUCTURED_DATA = "
        + json.dumps(s_payload, ensure_ascii=False)
        + ";\n"
    )
    OUT_STRUCTURED_DATA.write_text(s_js, encoding="utf-8")

    # Build UKChO tagging data + taxonomy (separate track; never touches AS/IG).
    ukcho_payload, (ukcho_copied, ukcho_asset_total), ukcho_problems, ukcho_warnings = build_ukcho_data()
    ukcho_js = (
        "// Generated by quiz-app/build.py — do not edit by hand.\n"
        "window.UKCHO_DATA = "
        + json.dumps(ukcho_payload, ensure_ascii=False)
        + ";\n"
        "window.UKCHO_TAXONOMY = window.UKCHO_DATA.taxonomy;\n"
    )
    OUT_UKCHO_DATA.write_text(ukcho_js, encoding="utf-8")

    # Copy front-end pages/assets into site/ (any quiz-app/*.{html,js}).
    FRONTEND_SOURCES = [INDEX_SRC, INDEX_SRC.parent / "assign.html",
                        INDEX_SRC.parent / "homework.html", INDEX_SRC.parent / "stats.html",
                        INDEX_SRC.parent / "home.html", INDEX_SRC.parent / "as.html",
                        INDEX_SRC.parent / "ig.html", INDEX_SRC.parent / "practice.html",
                        INDEX_SRC.parent / "as-shapes-of-molecules.html",
                        INDEX_SRC.parent / "ukcho.html",
                        INDEX_SRC.parent / "ukcho-tag.html",
                        INDEX_SRC.parent / "theme.css",
                        INDEX_SRC.parent / "config.js", INDEX_SRC.parent / "supabase-client.js",
                        INDEX_SRC.parent / "roster.js"]
    for src in FRONTEND_SOURCES:
        if src.exists():
            shutil.copy2(src, SITE_DIR / src.name)

    print(
        f"OK: {len(questions)} MCQ questions, {copied} MCQ assets, "
        f"{len(tree)} top-level syllabus nodes."
    )
    ig_copied, ig_missing = copy_igcse_homework_assets()
    print(f"OK: {ig_copied} IGCSE homework assets copied.")
    if ig_missing:
        print(f"WARN: {len(ig_missing)} IGCSE homework images missing:")
        for e in ig_missing[:20]:
            print("  -", e)

    print(f"OK: {len(s_records)} structured questions, {s_copied} structured assets.")
    if s_skips:
        print(f"WARN: {len(s_skips)} structured skipped:")
        for e in s_skips[:20]:
            print("  -", e)
    ukstats = ukcho_payload["stats"]
    print(
        f"OK: {ukstats['subQuestions']} UKChO sub-questions across "
        f"{ukstats['parents']} parents, {ukcho_asset_total} UKChO assets "
        f"({ukcho_copied} new; {ukstats['suggested']} suggested, "
        f"{ukstats['needsReview']} need review)."
    )
    if ukcho_problems:
        print(f"ERROR: {len(ukcho_problems)} UKChO validation problems:")
        for e in ukcho_problems[:20]:
            print("  -", e)
    if ukcho_warnings:
        print(f"WARN: {len(ukcho_warnings)} UKChO review prompts.")
    if errors:
        print(f"WARN: {len(errors)} asset problems:")
        for e in errors[:20]:
            print("  -", e)
    return 0 if not ukcho_problems else 1


if __name__ == "__main__":
    sys.exit(main())
