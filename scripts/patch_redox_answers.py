#!/usr/bin/env python3
"""给 AS 6.1 Redox 作业（id=38）补标准答案。

背景：这份「电子转移配平」作业发布时只传了题面截图，没带上标准答案：
  · Section A（Q1–Q15，MCQ）缺 ms_answer；
  · Section B（Q16–Q19，简答）缺 ms_img（mark scheme 图）。
答案已从 print/redox-balancing-practice/answers/answers.tex 提取，
ms 图已部署到 assets/structured/as-redox-q{16..19}-ms.png 且 OCR 校验过内容对应。

做法：调用 assignment Edge Function 的 replaceQuestions，用「完整题面 + 答案」
重建 question_snapshot 与 assignment_answer_keys（题目 ID / 顺序不变，不影响学生）。
"""
from __future__ import annotations

import json
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / ".chembank-token"
EDGE_URL = "https://jrobrcaiqtfwuomzycui.supabase.co/functions/v1/assignment"
ASSIGNMENT_ID = 38

# Section A MCQ 答案（来自 answers.tex，已逐题核对题目内容）
MCQ_ANSWERS = ["D", "C", "D", "C", "D", "A", "A", "B", "D", "C", "C", "C", "D", "C", "B"]

TOPICS = ["Redox processes", "Oxidation numbers", "Balancing equations"]


def load_token() -> str:
    if not TOKEN_FILE.exists():
        sys.exit(f"缺少教师口令文件：{TOKEN_FILE}")
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        sys.exit(f"{TOKEN_FILE} 是空的，请填入教师口令。")
    return token


def build_questions() -> list[dict]:
    qs: list[dict] = []
    for i in range(1, 16):
        qs.append({
            "id": f"as-redox-balancing-q{i:02d}",
            "type": "mcq",
            "marks": 1,
            "year": None,
            "session": None,
            "paper": "custom",
            "question": i,
            "topics": TOPICS,
            "figures": [f"assets/as-redox-q{i:02d}.png"],
            "paper_img": f"assets/as-redox-q{i:02d}.png",
            "ms_answer": MCQ_ANSWERS[i - 1],
            "ms_img": None,
            "body": None,
        })
    struct_marks = [2, 2, 1, 1]
    for j, m in enumerate(struct_marks, start=16):
        qs.append({
            "id": f"as-redox-balancing-q{j:02d}",
            "type": "structured",
            "marks": m,
            "year": None,
            "session": None,
            "paper": "custom",
            "question": j,
            "topics": TOPICS,
            "figures": [f"assets/structured/as-redox-q{j:02d}.png"],
            "paper_img": f"assets/structured/as-redox-q{j:02d}.png",
            "ms_answer": None,
            "ms_img": f"assets/structured/as-redox-q{j:02d}-ms.png",
            "body": None,
        })
    return qs


def post(payload: dict) -> dict:
    import subprocess
    cmd = [
        "curl", "-s", "-w", "\n%{http_code}", "--max-time", "60",
        "-X", "POST",
        "-H", "content-type: text/plain",
        "-d", json.dumps(payload, ensure_ascii=False),
        EDGE_URL,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    raw, _, code_str = r.stdout.rpartition("\n")
    code = int((code_str or "0").strip() or 0)
    try:
        parsed = json.loads(raw) if raw.strip() else None
    except Exception:
        parsed = raw
    if code != 200:
        if isinstance(parsed, dict):
            return {"_http": code, **parsed}
        return {"_http": code, "error": str(parsed)}
    return parsed or {"error": "empty response"}


def main() -> int:
    questions = build_questions()
    token = load_token()
    payload = {
        "action": "replaceQuestions",
        "teacher_token": token,
        "assignment_id": ASSIGNMENT_ID,
        "questions": questions,
    }

    print(f"目标作业：id={ASSIGNMENT_ID}（AS 6.1 Redox）")
    print(f"题目数：{len(questions)}（15 MCQ + 4 简答）")
    print("答案预览：")
    for q in questions:
        if q["type"] == "mcq":
            print(f"  {q['question']:>2}. {q['id']}  → ms_answer={q['ms_answer']}")
        else:
            print(f"  {q['question']:>2}. {q['id']}  → ms_img={q['ms_img']}")

    result = post(payload)
    if result.get("_http") and result["_http"] not in (200,):
        print(f"\n✗ 失败（HTTP {result['_http']}）：{result.get('error')}")
        if result.get("student_submissions"):
            print(f"  已有 {result['student_submissions']} 名学生交卷。")
            print("  若确认只是补答案（题目 ID/顺序不变，不换题），可加 --force 重试。")
        return 1
    if result.get("assignment"):
        a = result["assignment"]
        print(f"\n✓ 已更新作业 id={a.get('id')}  title={a.get('title')}")
        print(f"  题面 {result.get('questions')} 道，标准答案 {result.get('answer_keys')} 条")
        print(f"学生入口：homework.html?id={a.get('id')}&track={a.get('programme')}")
        return 0
    print(f"\n✗ 失败：{result.get('error') or result}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
