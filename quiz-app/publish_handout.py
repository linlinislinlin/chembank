#!/usr/bin/env python3
"""把本地 Obsidian 讲义发布成一份在线作业（Supabase assignment Edge Function）。

用法：
    python3 quiz-app/publish_handout.py <讲义.md或slug> [--title 标题] [--due YYYY-MM-DD] [--programme ig|as]

从讲义提取题目引用（按出现顺序去重）：
  - [[questions/<id>]]
  - vault / vault-structured / vault-igcse / vault-igcse-structured 的 *-paper.png

再从 vault Markdown 组装题面快照，复制截图到 quiz-app/site/assets/，
调用 assignment Edge Function 创建作业（含 programme）。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SITE = Path(__file__).resolve().parent / "site"
CONFIG = Path(__file__).resolve().parent / "config.js"
HANDOUTS_DIRS = [
    REPO / "vault" / "handouts",
    REPO / "vault-structured" / "handouts",
    REPO / "vault-igcse" / "handouts",
    REPO / "vault-igcse-structured" / "handouts",
]
QUESTION_DIRS = [
    REPO / "vault-igcse" / "questions",
    REPO / "vault-igcse-structured" / "questions",
    REPO / "vault" / "questions",
    REPO / "vault-structured" / "questions",
    REPO / "questions",
    REPO / "questions-structured",
]
ASSET_DIRS = [
    REPO / "vault-igcse" / "assets",
    REPO / "vault-igcse-structured" / "assets",
    REPO / "vault" / "assets",
    REPO / "vault-structured" / "assets",
]

MCQ_LINK_RE = re.compile(r"\[\[questions/([A-Za-z0-9\-]+)\]\]", re.IGNORECASE)
PAPER_IMG_RE = re.compile(
    r"(?:vault(?:-structured|-igcse|-igcse-structured)?/assets/|alt=\")([A-Za-z0-9\-]+?)(?:-paper\.png|\")",
    re.IGNORECASE,
)
PAPER_FILE_RE = re.compile(r"([A-Za-z0-9\-]+)-paper\.png", re.IGNORECASE)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def load_config() -> dict:
    if not CONFIG.exists():
        sys.exit(f"找不到 {CONFIG}")
    src = CONFIG.read_text(encoding="utf-8")
    url = re.search(r'url\s*:\s*"([^"]+)"', src)
    key = re.search(r'anonKey\s*:\s*"([^"]+)"', src)
    token = re.search(r'statsToken\s*:\s*"([^"]+)"', src)
    edge = re.search(r'assignmentEdgeUrl\s*:\s*"([^"]+)"', src)
    if not url or not key:
        sys.exit("config.js 里 url / anonKey 未配置")
    if not edge:
        sys.exit("config.js 里 assignmentEdgeUrl 未配置")
    if not token:
        sys.exit("config.js 里 statsToken 未配置（发布作业需要教师口令）")
    return {
        "url": url.group(1),
        "key": key.group(1),
        "token": token.group(1),
        "edge": edge.group(1).rstrip("/"),
    }


def resolve_handout(arg: str) -> Path:
    p = Path(arg)
    if p.is_file():
        return p
    for d in HANDOUTS_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.stem == arg or arg in f.stem:
                return f
    sys.exit(f"找不到讲义：{arg}（传入完整 .md 路径或 slug）")


def parse_handout(text: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for line in text.splitlines():
        found: list[str] = []
        found.extend(m.group(1) for m in MCQ_LINK_RE.finditer(line))
        found.extend(m.group(1) for m in PAPER_FILE_RE.finditer(line))
        for qid in found:
            if qid.startswith("cie-") and qid not in seen:
                seen.add(qid)
                ordered.append(qid)
    return ordered


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def find_question_md(qid: str) -> Path | None:
    for d in QUESTION_DIRS:
        p = d / f"{qid}.md"
        if p.is_file():
            return p
    return None


def find_asset(name: str) -> Path | None:
    for d in ASSET_DIRS:
        p = d / name
        if p.is_file():
            return p
    return None


def is_structured(fm: dict, qid: str) -> bool:
    qtype = str(fm.get("question_type") or "").lower()
    if qtype.startswith("struct"):
        return True
    if qtype == "mcq":
        return False
    return bool(re.search(r"-p[3-6]\d-", qid))


def build_question(qid: str) -> dict:
    md = find_question_md(qid)
    if md is None:
        raise FileNotFoundError(f"找不到题目 Markdown：{qid}")
    fm = parse_frontmatter(md.read_text(encoding="utf-8"))
    structured = is_structured(fm, qid)
    paper_name = f"{qid}-paper.png"
    ms_name = f"{qid}-ms.png"
    paper_src = find_asset(paper_name)
    if paper_src is None:
        raise FileNotFoundError(f"找不到题干截图：{paper_name}")

    if structured:
        dest_dir = SITE / "assets" / "structured"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(paper_src, dest_dir / paper_name)
        paper_img = "assets/structured/" + paper_name
        ms_img = None
        ms_src = find_asset(ms_name)
        if ms_src is not None:
            shutil.copy2(ms_src, dest_dir / ms_name)
            ms_img = "assets/structured/" + ms_name
        return {
            "id": qid,
            "type": "structured",
            "marks": fm.get("marks") or 1,
            "year": fm.get("year"),
            "session": fm.get("session"),
            "paper": fm.get("paper"),
            "question": fm.get("question"),
            "topics": fm.get("topic_titles") or [],
            "figures": [paper_img],
            "paper_img": paper_img,
            "ms_img": ms_img,
            "body": "",
        }

    dest_dir = SITE / "assets"
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paper_src, dest_dir / paper_name)
    paper_img = "assets/" + paper_name
    return {
        "id": qid,
        "type": "mcq",
        "marks": fm.get("marks") or 1,
        "year": fm.get("year"),
        "session": fm.get("session"),
        "paper": fm.get("paper"),
        "question": fm.get("question"),
        "topics": fm.get("topic_titles") or [],
        "figures": [paper_img],
        "paper_img": paper_img,
        "ms_answer": str(fm.get("ms_answer") or "").strip().upper(),
        "body": "",
    }


def detect_programme(title: str, ids: list[str], explicit: str | None) -> str:
    if explicit in {"ig", "as"}:
        return explicit
    if re.search(r"^\s*(\[?igcse\]?|ig\b|0620)", title or "", re.I):
        return "ig"
    if any(qid.startswith("cie-0620-") for qid in ids):
        return "ig"
    return "as"


def list_assignments(cfg: dict) -> list[dict]:
    cmd = [
        "curl", "-s", "--max-time", "30",
        "-H", f"apikey: {cfg['key']}",
        "-H", f"Authorization: Bearer {cfg['key']}",
        cfg["url"] + "/rest/v1/assignments?select=id,title,programme,status&order=created_at.desc",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(r.stdout)
    except Exception:
        return []
    return data if isinstance(data, list) else []


def create_assignment(cfg: dict, payload: dict) -> dict:
    cmd = [
        "curl", "-s", "-w", "\n%{http_code}", "--max-time", "60",
        "-X", "POST",
        "-H", "content-type: text/plain",
        "-d", json.dumps(payload, ensure_ascii=False),
        cfg["edge"],
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    raw, _, code_str = r.stdout.rpartition("\n")
    code = int((code_str or "0").strip() or 0)
    try:
        parsed = json.loads(raw) if raw.strip() else None
    except Exception:
        parsed = raw
    if code != 200 or not isinstance(parsed, dict) or not parsed.get("assignment"):
        raise RuntimeError(f"创建作业失败 (HTTP {code})：{parsed}")
    return parsed["assignment"]


def main() -> int:
    ap = argparse.ArgumentParser(description="发布讲义为在线作业")
    ap.add_argument("handout", help="讲义 .md 路径或 slug")
    ap.add_argument("--title", help="作业标题（默认用讲义标题）")
    ap.add_argument("--due", help="截止日期 YYYY-MM-DD")
    ap.add_argument("--programme", choices=["ig", "as"], help="课程：ig 或 as（默认识别）")
    ap.add_argument("--force", action="store_true", help="标题已存在时仍新建一份")
    args = ap.parse_args()

    path = resolve_handout(args.handout)
    text = path.read_text(encoding="utf-8")
    ordered = parse_handout(text)
    if not ordered:
        print(f"⚠️  在讲义里没找到任何题目引用：{path.name}")
        return 1

    title = args.title
    if not title:
        m = re.search(r"^title\s*:\s*(.+)$", text, re.MULTILINE)
        title = m.group(1).strip().strip('"') if m else path.stem.replace("-", " ")
    programme = detect_programme(title, ordered, args.programme)
    if programme == "ig" and not re.search(r"^\s*(\[?igcse\]?|ig\b|0620)", title, re.I):
        title = "IGCSE " + title

    questions = []
    for qid in ordered:
        try:
            questions.append(build_question(qid))
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return 1

    cfg = load_config()
    if not args.force:
        for row in list_assignments(cfg):
            if (row.get("title") or "").strip() == title and row.get("status", "published") == "published":
                print(f"ℹ️  已有同名作业，未重复创建：{title}")
                print(f"   作业 ID：{row.get('id')}")
                print(f"   学生入口：ig.html" if programme == "ig" else "   学生入口：as.html")
                print(f"   作业直链：homework.html?id={row.get('id')}&track={programme}")
                return 0

    due_at = args.due + "T23:59:00Z" if args.due else None
    instructions = (
        "CIE 0620 IGCSE Chemistry (Extended) · 42 marks · 45 minutes. "
        "Section A: 20 MCQ (20 marks). Section B: structured questions (22 marks). "
        "A Periodic Table may be used. Show working in structured questions."
        if programme == "ig" and "2.1" in title
        else ""
    )
    ass = create_assignment(cfg, {
        "action": "create",
        "teacher_token": cfg["token"],
        "title": title,
        "instructions": instructions,
        "due_at": due_at,
        "show_answers_after_submit": True,
        "show_explanations_after_submit": True,
        "questions": questions,
        "programme": programme,
    })
    mcq_n = sum(1 for q in questions if q["type"] == "mcq")
    st_n = len(questions) - mcq_n
    print(f"\n✅ 已发布作业：{title}")
    print(f"   作业 ID：{ass.get('id')}")
    print(f"   课程：{programme}")
    print(f"   题目数：{len(questions)}（MCQ {mcq_n} · 结构题 {st_n}）")
    portal = "ig.html" if programme == "ig" else "as.html"
    print(f"   学生入口：{portal}")
    print(f"   作业直链：homework.html?id={ass.get('id')}&track={programme}")
    print(f"   统计：stats.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
