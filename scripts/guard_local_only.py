#!/usr/bin/env python3
"""阻止「只应保存在本地」的出卷内容被提交到公开仓库（linlinislinlin/chembank）。

背景
----
本仓库是 **PUBLIC**。`print/`（试卷 PDF/TeX）与 `pick/`（选题单）一旦进 git，
任何人无需登录就能在 GitHub 上看到，并据此反推出某次考试选了哪些题。

这个脚本检查**已暂存（staged）**的文件，命中即中止提交。由两处调用：
  1. `.githooks/pre-commit` —— 拦截任何手动 `git commit`
  2. `quiz-app/deploy.sh`   —— 拦截一键部署

设计原则：宁可误拦，不可漏放。万一确实需要提交，用
`CHEMBANK_ALLOW_LOCAL_ONLY_COMMIT=1 git commit ...` 显式放行，并在提交信息里说明原因。

退出码：0 = 安全；1 = 命中受保护内容。
"""
from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys

# --------------------------------------------------------------------------
# 规则 1：这些目录属于“本地 only”，绝不进公开仓库
# --------------------------------------------------------------------------
PROTECTED_DIRS = (
    "pick/",            # 选题单：include_ids 就是“这次考了哪些题”
    "print/",           # 试卷排版产物：PDF / TeX / 答案
    "build/",           # chembank select 展开的选题 JSON
    "raw/papers/",      # 剑桥真题 PDF
    "raw/reports/",     # 考官报告
    "raw/ukcho/",
    "draft/",
)
PROTECTED_SUBSTRINGS = (
    "/handouts/",       # 讲义（含题面 + 答案区）
    "/assets/",         # 真题截图
    "/questions/",      # 题目正文
)

# --------------------------------------------------------------------------
# 规则 2：文件名像“出卷”的，一律拦
# --------------------------------------------------------------------------
NAME_PATTERNS = [
    (re.compile(r"\bexam\b", re.I), "文件名含 exam"),
    (re.compile(r"\bunit[-_ ]?test\b", re.I), "文件名含 unit test"),
    (re.compile(r"考试|试卷|答案卷|选题单|组卷", re.I), "文件名含中文出卷词"),
    (re.compile(r"paper[-_][ab]\d*\.", re.I), "文件名像 A/B 卷"),
    (re.compile(r"answers?[-_][ab]\d*\.", re.I), "文件名像 A/B 卷答案"),
]

# --------------------------------------------------------------------------
# 规则 3：内容签名 —— 即使换了无害文件名，也拦得住
# --------------------------------------------------------------------------
CONTENT_SIGNATURES = [
    (re.compile(rb"include_ids\s*:"), "含选题清单 include_ids"),
    (re.compile(rb"chembank\s+assemble\b"), "含组卷命令 chembank assemble"),
    (re.compile(rb"chembank\s+select\b"), "含选题命令 chembank select"),
]
# 只扫文本类后缀；.py 等代码文件会合法地提到这些词，故排除
SCAN_EXTS = {".yaml", ".yml", ".json", ".md", ".tex", ".txt", ".csv", ".jsonl"}
MAX_SCAN_BYTES = 2_000_000


def repo_root() -> str:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return (r.stdout or ".").strip() or "."


def staged_files() -> list[str]:
    """已暂存的新增/修改/改名文件（不含删除）。"""
    r = subprocess.run(
        ["git", "-c", "core.quotepath=false", "diff", "--cached",
         "--name-only", "--diff-filter=ACMR", "-z"],
        capture_output=True, text=True,
    )
    return [p for p in (r.stdout or "").split("\0") if p.strip()]


def check_path(path: str) -> list[str]:
    """按路径判断。"""
    hits: list[str] = []
    low = "/" + path  # 便于统一做 “/handouts/” 之类的子串匹配
    for d in PROTECTED_DIRS:
        if path.startswith(d):
            hits.append(f"位于本地专用目录 {d}")
            break
    else:
        for s in PROTECTED_SUBSTRINGS:
            if s in low:
                hits.append(f"位于本地专用位置 {s}")
                break
    for pat, why in NAME_PATTERNS:
        if pat.search(path):
            hits.append(why)
    return hits


def check_content(path: str) -> list[str]:
    """按内容判断（仅文本类后缀，且有大小上限）。"""
    if os.path.splitext(path)[1].lower() not in SCAN_EXTS:
        return []
    try:
        if os.path.getsize(path) > MAX_SCAN_BYTES:
            return []
        data = open(path, "rb").read()
    except OSError:
        return []
    return [why for pat, why in CONTENT_SIGNATURES if pat.search(data)]


def main() -> int:
    if os.environ.get("CHEMBANK_ALLOW_LOCAL_ONLY_COMMIT") == "1":
        print("⚠️  guard_local_only：已被 CHEMBANK_ALLOW_LOCAL_ONLY_COMMIT=1 显式放行。")
        return 0

    os.chdir(repo_root())
    files = staged_files()
    if not files:
        return 0

    flagged: list[tuple[str, list[str]]] = []
    for f in files:
        reasons = check_path(f) + check_content(f)
        if reasons:
            flagged.append((f, reasons))

    if not flagged:
        return 0

    print("\n" + "=" * 66)
    print("⛔ 提交被拦截：有出卷/选题内容正要进入【公开】仓库")
    print("=" * 66)
    for f, reasons in flagged:
        print(f"\n  {f}")
        for why in dict.fromkeys(reasons):
            print(f"      · {why}")
    print("\n" + "-" * 66)
    print("为什么危险：本仓库是 PUBLIC。`pick/*.yaml` 里的 include_ids、")
    print("`print/` 里的试卷与答案 PDF，公开后任何人都能看出这次考了哪些题。")
    print("\n怎么解决（三选一）：")
    print("  1) 让它留在本地（推荐）：")
    print("       git rm -r --cached <路径>      # 从索引移除，磁盘文件保留")
    print("     已加入 .gitignore 的目录会自动不再被 git add -A 收走。")
    print("  2) 把文件移到本地专用目录：pick/ 、print/ 或 build/")
    print("  3) 确实需要提交（例如修 guard 本身）：")
    print("       CHEMBANK_ALLOW_LOCAL_ONLY_COMMIT=1 git commit ...")
    print("-" * 66)
    return 1


if __name__ == "__main__":
    sys.exit(main())
