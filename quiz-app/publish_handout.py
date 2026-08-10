#!/usr/bin/env python3
"""把本地 Obsidian 讲义发布成一份在线作业（Supabase）。

用法：
    python3 quiz-app/publish_handout.py <讲义.md或slug> [--title 标题] [--due YYYY-MM-DD]

它从讲义里提取题目引用：
  - [[questions/<id>]]          -> Paper 1 MCQ
  - <img …/vault-structured/assets/<id>-paper.png …>  -> 结构题 (Paper 2/4/5)
按讲义中的顺序去重，创建作业，并打印学生链接。

不会改动你的题库：只向 Supabase 的 assignments 表插入一条记录。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).resolve().parent / "config.js"
HANDOUTS_DIRS = [REPO / "vault" / "handouts",
                 REPO / "vault-structured" / "handouts"]

MCQ_LINK_RE = re.compile(r"\[\[questions/([A-Za-z0-9\-]+)\]\]", re.IGNORECASE)
STRUCT_IMG_RE = re.compile(r'<img\s+src="[^"]*vault-structured/assets/([A-Za-z0-9\-]+)-paper\.png"', re.IGNORECASE)


def load_config() -> dict:
    if not CONFIG.exists():
        sys.exit(f"找不到 {CONFIG}")
    src = CONFIG.read_text(encoding="utf-8")
    url = re.search(r'url\s*:\s*"([^"]+)"', src)
    key = re.search(r'anonKey\s*:\s*"([^"]+)"', src)
    if not url or not key:
        sys.exit("config.js 里 url / anonKey 未配置")
    return {"url": url.group(1), "key": key.group(1)}


def resolve_handout(arg: str) -> Path:
    p = Path(arg)
    if p.is_file():
        return p
    # 当作 slug 或文件名搜索
    for d in HANDOUTS_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.stem == arg:
                return f
    # 再退回全库搜索文件名
    for d in HANDOUTS_DIRS:
        if not d.is_dir():
            continue
        for f in d.glob("*.md"):
            if arg in f.stem:
                return f
    sys.exit(f"找不到讲义：{arg}（传入完整 .md 路径或 slug）")


def parse_handout(text: str) -> tuple[list[str], list[str], list[str]]:
    """Return (mcq_ids, struct_ids, ordered_ids).
    mcq/struct preserved in document order; ordered interleaves MCQ + structured
    back into the handout's original question order, deduped across both."""
    mcq: list[str] = []
    struct: list[str] = []
    seen_mcq: set[str] = set()
    seen_struct: set[str] = set()
    seen_all: set[str] = set()
    ordered_tmp: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines()):
        for m in MCQ_LINK_RE.finditer(line):
            qid = m.group(1)
            if qid not in seen_mcq:
                seen_mcq.add(qid)
                mcq.append(qid)
            if qid not in seen_all:
                seen_all.add(qid)
                ordered_tmp.append((line_no, qid))
        for m in STRUCT_IMG_RE.finditer(line):
            qid = m.group(1)
            if qid not in seen_struct:
                seen_struct.add(qid)
                struct.append(qid)
            if qid not in seen_all:
                seen_all.add(qid)
                ordered_tmp.append((line_no, qid))
    ordered_tmp.sort(key=lambda x: x[0])
    ordered = [qid for _, qid in ordered_tmp]
    return mcq, struct, ordered


def quick_check(ids: list[str]) -> tuple[dict[str, bool], list[str]]:
    """Whether each id is present in the built data files (data.js / structured-data.js).
    Returns (exists_map, missing). Only a warning for missing ids."""
    exists: dict[str, bool] = {}
    missing: list[str] = []
    for tag, path in (("data.js", REPO / "quiz-app" / "site" / "data.js"),
                      ("structured-data.js", REPO / "quiz-app" / "site" / "structured-data.js")):
        if not path.exists():
            continue
        src = path.read_text(encoding="utf-8")
        # 贪婪匹配 JSON 对象；id 都以 quote 形式出现
        for qid in ids:
            if qid in exists:
                continue
            if f'"id": "{qid}"' in src or f'"id":"{qid}"' in src:
                exists[qid] = True
    for qid in ids:
        exists.setdefault(qid, False)
        if not exists[qid]:
            missing.append(qid)
    return exists, missing


def post(key, url, path, body):
    cmd = ["curl", "-s", "-w", "\\n%{http_code}", "--max-time", "30", "-X", "POST"]
    cmd += ["-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}",
            "-H", "Content-Type: application/json",
            "-H", "Prefer: return=representation"]
    cmd += ["-d", json.dumps(body, ensure_ascii=False)]
    cmd.append(url + path)
    r = subprocess.run(cmd, capture_output=True, text=True)
    raw, _, code_str = r.stdout.rpartition("\n")
    code = int((code_str or "0").strip() or 0)
    try:
        parsed = json.loads(raw) if raw.strip() else None
    except Exception:
        parsed = raw
    return code, parsed


def main() -> int:
    ap = argparse.ArgumentParser(description="发布讲义为在线作业")
    ap.add_argument("handout", help="讲义 .md 路径或 slug")
    ap.add_argument("--title", help="作业标题（默认用讲义标题）")
    ap.add_argument("--due", help="截止日期 YYYY-MM-DD")
    args = ap.parse_args()

    path = resolve_handout(args.handout)
    text = path.read_text(encoding="utf-8")

    mcq, struct, ordered = parse_handout(text)
    if not mcq and not struct:
        print(f"⚠️  在讲义里没找到任何题目引用：{path.name}")
        return 1

    exists, missing = quick_check(ordered)
    if missing:
        print("⚠️  以下题目未在已构建的数据中找到（可能没跑过 build，或题型缺失）：")
        for qid in missing:
            print("   -", qid)
        print("   建议先运行：python3 quiz-app/build.py")
        return 1

    cfg = load_config()

    # 标题：讲义 frontmatter title 优先，否则文件名，否则 --title
    title = args.title
    if not title:
        m = re.search(r"^title\s*:\s*(.+)$", text, re.MULTILINE)
        title = m.group(1).strip() if m else (path.stem.replace("-", " "))
    due_at = args.due + "T23:59:00Z" if args.due else None

    code, ass = post(cfg["key"], cfg["url"],
                     "/rest/v1/assignments?select=*",
                     {"title": title, "question_ids": ordered, "due_at": due_at})
    if code not in (200, 201) or not isinstance(ass, list) or not ass:
        print(f"❌ 创建作业失败 (HTTP {code})：{ass}")
        return 1
    ass = ass[0]
    aid = ass["id"]

    mcq_n = len(mcq)
    struct_n = len(struct)
    print(f"\n✅ 已发布作业：{title}")
    print(f"   作业 ID：{aid}")
    print(f"   题目数：{len(ordered)}（MCQ {mcq_n} · 结构题 {struct_n}）")
    print(f"   学生链接：homework.html?id={aid}")
    print(f"   统计链接：stats.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
