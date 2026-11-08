#!/usr/bin/env python3
"""发布作业到线上（Supabase assignment Edge Function）。

把一份「发布清单」（题目 ID + 顺序，是最终 PDF 的精确镜像）发布成线上作业，
保证发到网页上的题 = 你确认过的那一版，绝不会发成旧版。

用法：
  # 新建作业
  python3 scripts/publish_assignment.py publish/7.1-equilibria-hw1.json

  # 替换已有作业的整套题面（作业 ID 不变，学生链接不变）
  python3 scripts/publish_assignment.py publish/7.1-equilibria-hw1.json --replace 34

  # 替换时若已有真实学生交卷，需显式 --force（强烈不推荐）
  python3 scripts/publish_assignment.py publish/7.1-equilibria-hw1.json --replace 34 --force

发布清单 JSON 格式（由出 PDF 的流程一并生成）：
  {
    "title": "7.1 Equilibrium homework 1 · dynamic equilibrium & Le Chatelier",
    "programme": "as",          // as | ig
    "instructions": "……",       // 可选
    "questions": ["cie-9701-...", "cie-9701-qls-eq-mcq-01", ...]
  }

教师口令从本地文件 .chembank-token 读取（已在 .gitignore 中，绝不进 git）。
题目题面数据从构建产物 site/data.js（MCQ）与 site/structured-data.js（结构化）读取，
保证与网页上学生看到的题面完全一致。
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / ".chembank-token"
EDGE_URL = "https://jrobrcaiqtfwuomzycui.supabase.co/functions/v1/assignment"
DATA_JS = ROOT / "quiz-app" / "site" / "data.js"
STRUCT_JS = ROOT / "quiz-app" / "site" / "structured-data.js"


def load_token() -> str:
    if not TOKEN_FILE.exists():
        sys.exit(f"缺少教师口令文件：{TOKEN_FILE}\n请把教师口令写入该文件（一行），再运行。")
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        sys.exit(f"{TOKEN_FILE} 是空的，请填入教师口令。")
    return token


def load_js_object(path: Path, marker: str) -> dict:
    """从 window.X = {...}; 形式读取一个 JSON 对象。"""
    raw = path.read_text(encoding="utf-8")
    i = raw.index(marker)
    i = raw.index("=", i) + 1
    j = raw.rindex("};")
    return json.loads(raw[i:j + 1])


def build_question_lookup() -> dict[str, dict]:
    """读取 site 构建产物，建立 id -> 题面数据 的映射（MCQ + structured）。"""
    mcq_obj = load_js_object(DATA_JS, "window.CHEMBANK_DATA")
    struct_obj = load_js_object(STRUCT_JS, "window.STRUCTURED_DATA")

    lookup: dict[str, dict] = {}
    for q in mcq_obj.get("questions", []):
        lookup[q["id"]] = q
    for q in struct_obj.get("questions", []):
        # structured-data.js 的字段名与 MCQ 略有差异，统一成 IncomingQ 需要的形态
        q2 = dict(q)
        q2["type"] = "structured"
        lookup[q["id"]] = q2
    return lookup


def to_incoming(q: dict) -> dict:
    """把一条题目数据转成 assignment Edge Function 的 IncomingQ。"""
    is_struct = q.get("type") == "structured"
    return {
        "id": q.get("id"),
        "type": "structured" if is_struct else "mcq",
        "marks": q.get("marks"),
        "year": q.get("year"),
        "session": q.get("session"),
        "paper": q.get("paper"),
        "question": q.get("question"),
        "topics": q.get("topics") or [],
        "figures": q.get("figures") or [],
        "paper_img": q.get("paper_img"),
        "body": q.get("body"),
        "ms_answer": q.get("ms_answer"),
        "ms_img": q.get("ms_img"),
    }


def post(payload: dict) -> dict:
    req = urllib.request.Request(
        EDGE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "text/plain"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            detail = json.loads(body)
        except Exception:
            detail = {"error": body}
        return {"_http": e.code, **detail}


def main() -> int:
    ap = argparse.ArgumentParser(description="发布作业到线上（ChemBank quiz）")
    ap.add_argument("manifest", help="发布清单 JSON 路径")
    ap.add_argument("--replace", type=int, help="替换该作业 ID 的整套题面（而非新建）")
    ap.add_argument("--force", action="store_true", help="已有真实学生交卷时仍强制替换")
    ap.add_argument("--dry-run", action="store_true", help="只打印将发布的题面，不真正发布")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    title = manifest.get("title") or ""
    programme = manifest.get("programme") or "as"
    questions_ids = manifest.get("questions") or []
    if not title:
        sys.exit("发布清单缺少 title")
    if not questions_ids:
        sys.exit("发布清单缺少 questions")

    lookup = build_question_lookup()
    missing = [qid for qid in questions_ids if qid not in lookup]
    if missing:
        sys.exit(f"以下题目不在线上题库中（请先补题库）：\n  " + "\n  ".join(missing))

    questions = [to_incoming(lookup[qid]) for qid in questions_ids]

    print(f"标题：{title}")
    print(f"轨道：{programme}")
    print(f"题目数：{len(questions)}")
    print("题目顺序：")
    for i, q in enumerate(questions, 1):
        print(f"  {i:2d}. {q['id']}  ({q['type']}, {q['marks']} 分)")

    if args.dry_run:
        print("\n[--dry-run] 未真正发布。")
        return 0

    token = load_token()
    payload = {
        "action": "replaceQuestions" if args.replace else "create",
        "teacher_token": token,
        "title": title,
        "programme": programme,
        "instructions": manifest.get("instructions") or "",
        "questions": questions,
    }
    if args.replace:
        payload["assignment_id"] = args.replace
        if args.force:
            payload["force"] = True

    result = post(payload)
    if result.get("_http") and result["_http"] not in (200,):
        print(f"\n✗ 发布失败（HTTP {result['_http']}）：{result.get('error')}")
        return 1
    if result.get("assignment"):
        a = result["assignment"]
        print(f"\n✓ 已发布作业 id={a.get('id')}  title={a.get('title')}")
        print(f"学生入口：homework.html?id={a.get('id')}&track={programme}")
        return 0
    print(f"\n✗ 发布失败：{result.get('error') or result}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
