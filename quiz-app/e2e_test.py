#!/usr/bin/env python3
"""End-to-end test of the ChemBank homework flow against real Supabase (seed).

IMPORTANT: This script WRITES to the user's Supabase tables, then CLEANS UP.
It simulates: teacher creates assignment -> fake students answer -> stats query.
Marked clearly for review: only ops against the user's own homework DB.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

CONFIG = Path(__file__).resolve().parent.parent / "quiz-app" / "config.js"
SITE_DATA = Path(__file__).resolve().parent.parent / "quiz-app" / "site" / "data.js"
BASE = "https://jrobrcaiqtfwuomzycui.supabase.co"
HDRS = ["-H", "Content-Type: application/json"]


def read_key() -> str:
    m = re.search(r'anonKey\s*:\s*"([^"]+)"', CONFIG.read_text(encoding="utf-8"))
    if not m:
        sys.exit("找不到 anonKey")
    return m.group(1)


def auth_hdrs(key: str):
    return ["-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}"]


def http(key: str, method: str, path: str, body=None, prefer=None) -> tuple[int, object]:
    cmd = ["curl", "-s", "-w", "\\n%{http_code}", "--max-time", "20", "-X", method]
    cmd += auth_hdrs(key) + HDRS
    if prefer:
        cmd += ["-H", f"Prefer: {prefer}"]
    if body is not None:
        cmd += ["-d", json.dumps(body, ensure_ascii=False)]
    cmd.append(BASE + path)
    r = subprocess.run(cmd, capture_output=True, text=True)
    parts = r.stdout.rsplit("\n", 1)
    raw = parts[0]
    code = int(parts[1].strip() or 0)
    try:
        parsed = json.loads(raw) if raw else None
    except Exception:
        parsed = raw
    return (code, parsed)


def get_real_question_ids() -> list[str]:
    m = re.search(r'window\.CHEMBANK_DATA\s*=\s*(\{.*\});', SITE_DATA.read_text(encoding="utf-8"), re.DOTALL)
    data = json.loads(m.group(1))
    return [q["id"] for q in data["questions"][:3]]


def run(key: str):
    print("== 1. 建测试作业 ==")
    qids = get_real_question_ids()
    code, ass = http(key, "POST", "/rest/v1/assignments?select=*",
                     {"title": "【测试作业】端到端验证", "question_ids": qids},
                     prefer="return=representation")
    print(f"   assignments POST -> {code}, id={ass[0].get('id') if isinstance(ass, list) else ass}")
    assert code in (200, 201) and isinstance(ass, list), f"建作业失败: {ass}"
    aid = ass[0]["id"]

    print("== 2. 建两个测试学生 ==")
    students = []
    for name, no in (("测试小明", "T001"), ("测试小红", "T002")):
        code, stu = http(key, "POST", "/rest/v1/students?select=*",
                         {"name": name, "student_no": no, "class_name": "测试班"},
                         prefer="return=representation")
        assert code in (200, 201) and isinstance(stu, list), f"建学生失败: {stu}"
        students.append(stu[0]["id"])
        print(f"   {name} -> id={stu[0]['id']}")

    print("== 3. 模拟作答（小明全对，小红部分错）==")
    answers = [
        (students[0], qids[0], "A", True),
        (students[0], qids[1], "B", True),
        (students[0], qids[2], "C", True),
        (students[1], qids[0], "D", False),
        (students[1], qids[1], "B", True),
        (students[1], qids[2], "C", True),
    ]
    for sid, qid, chosen, correct in answers:
        code, body = http(key, "POST", "/rest/v1/answers",
                          {"assignment_id": aid, "student_id": sid,
                           "question_id": qid, "chosen": chosen, "correct": correct})
        assert code in (200, 201), f"记答案失败: {body}"

    print("== 4. 按统计页逻辑查数（验证 stats.html 会渲染什么）==")
    code, rows = http(key, "GET", "/rest/v1/answers?select=*,students(name,student_no,class_name)&assignment_id=eq." + str(aid))
    print(f"   GET answers -> {code}, 条数={len(rows) if isinstance(rows, list) else rows}")
    assert code == 200 and isinstance(rows, list) and len(rows) == 6, f"作答查询异常: {rows}"
    by_stu = {}
    for r in rows:
        cn = r["students"]["name"]
        by_stu.setdefault(cn, []).append(r["correct"])
    for cn, vals in by_stu.items():
        ok = sum(vals)
        print(f"   {cn}: 正确 {ok}/{len(vals)}  ({round(ok/len(vals)*100)}%)")

    print("\n== 端到端流程通过 ✓ ==")

    print("\n== 5. 清理测试数据（torn down）==")
    # 依赖顺序：先删 answers，再 students、assignments
    http(key, "DELETE", "/rest/v1/answers?assignment_id=eq." + str(aid))
    for sid in students:
        http(key, "DELETE", "/rest/v1/students?id=eq." + str(sid))
    http(key, "DELETE", "/rest/v1/assignments?id=eq." + str(aid))
    code, leftover = http(key, "GET", "/rest/v1/assignments?select=id")
    n = len(leftover) if isinstance(leftover, list) else -1
    print(f"   清理后 assignments 条数 = {n}")
    assert n == 0, f"清理不彻底，残留 {n} 条"
    print("== 清理完成 ✓ ==")


if __name__ == "__main__":
    run(read_key())
