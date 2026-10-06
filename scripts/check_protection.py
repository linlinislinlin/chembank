#!/usr/bin/env python3
"""出卷保密自检 —— 一条命令确认「试卷选题不会上传 GitHub」。

用法：
    python3 scripts/check_protection.py            # 只查本地
    python3 scripts/check_protection.py --online   # 外加线上实测（需联网）

检查六项：
  1. .gitignore 是否覆盖本地专用目录
  2. 提交拦截防线是否就位（pre-commit hook / deploy.sh）
  3. 出卷内容是否已被 git 追踪（应为 0）
  4. 全库扫描：是否有选题清单冒充普通文件混进版本库
  5. 网站完整性（学生页内容不能被误删）
  6. [--online] 线上实测：网站 200、pick/print 404

退出码：0 = 全绿；1 = 有问题。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip() or "."
os.chdir(REPO)

GREEN, RED, YEL, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
results: list[bool] = []


def head(t: str) -> None:
    print(f"\n{'-'*64}\n{t}\n{'-'*64}")


def ok(t: str, detail: str = "") -> None:
    results.append(True)
    print(f"  {GREEN}✓{OFF} {t}" + (f"  {DIM}{detail}{OFF}" if detail else ""))


def bad(t: str, detail: str = "") -> None:
    results.append(False)
    print(f"  {RED}✗{OFF} {t}" + (f"  {DIM}{detail}{OFF}" if detail else ""))


def warn(t: str, detail: str = "") -> None:
    print(f"  {YEL}!{OFF} {t}" + (f"  {DIM}{detail}{OFF}" if detail else ""))


def git(*a: str) -> str:
    return subprocess.run(["git", "-c", "core.quotepath=false", *a],
                          capture_output=True, text=True).stdout


def tracked(prefix: str) -> int:
    return len([x for x in git("ls-files", prefix).split("\n") if x.strip()])


# ---------------------------------------------------------------- 1
head("1. 忽略规则 —— 出卷目录必须被 .gitignore 挡住")
gi = open(".gitignore", encoding="utf-8").read()
for d in ["pick/", "print/", "build/"]:
    if re.search(rf"^{re.escape(d)}\s*$", gi, re.M):
        ok(f".gitignore 含 {d}")
    else:
        bad(f".gitignore 缺 {d}", "新增文件会被 git add -A 收走")
for probe in ["pick/x.yaml", "print/x/paper-A.pdf"]:
    r = subprocess.run(["git", "check-ignore", "-q", probe])
    if r.returncode == 0:
        ok(f"实测忽略生效：{probe}")
    else:
        bad(f"实测忽略失效：{probe}")

# ---------------------------------------------------------------- 2
head("2. 提交拦截防线 —— 手滑也拦得住")
hp = git("config", "--get", "core.hooksPath").strip()
ok(f"core.hooksPath = {hp}") if hp == ".githooks" else bad(
    f"core.hooksPath = {hp or '(空)'}", "应为 .githooks；跑 git config core.hooksPath .githooks")
for f in [".githooks/pre-commit", "scripts/guard_local_only.py"]:
    if os.path.isfile(f) and os.access(f, os.X_OK):
        ok(f"{f} 存在且可执行")
    elif os.path.isfile(f):
        bad(f"{f} 不可执行", f"跑 chmod +x {f}")
    else:
        bad(f"{f} 缺失")
if "guard_local_only" in open("quiz-app/deploy.sh", encoding="utf-8").read():
    ok("deploy.sh 提交前会跑 guard")
else:
    bad("deploy.sh 未接 guard", "git add -A 可能把出卷内容抄上仓库")

# ---------------------------------------------------------------- 3
head("3. 出卷内容是否已进版本库 —— 期望全部为 0")
for d in ["pick/", "print/", "build/"]:
    n = tracked(d)
    ok(f"git ls-files {d:9} = 0") if n == 0 else bad(
        f"git ls-files {d:9} = {n}", "仍有出卷内容被追踪！")
for d in ["vault/handouts/", "vault/assets/"]:
    n = tracked(d)
    ok(f"git ls-files {d:16} = 0") if n == 0 else warn(
        f"git ls-files {d:16} = {n}", "可能含题面/答案，建议确认")

# ---------------------------------------------------------------- 4
head("4. 全库扫描 —— 有没有伪装成普通文件的选题清单")
ALLOW = ("src/", "tests/", "scripts/", "docs/", "fixtures/", ".github/",
         ".cursor/", "quiz-app/build.py", "syllabus/", "schema/")
# 只认「真的把 include_ids 当键用」（YAML 的 include_ids: / JSON 的 "include_ids":），
# 避免把注释、README 里提到这个词的散文误判成泄漏。
hits = git("grep", "-l", "-I", "-E", r"""include_ids["']?[[:space:]]*:""", "HEAD").split("\n")
leaks = []
for h in hits:
    h = h.strip().removeprefix("HEAD:")
    if not h or h.startswith(ALLOW):
        continue
    leaks.append(h)
if leaks:
    for l in leaks:
        bad(f"追踪文件含选题清单：{l}")
else:
    ok("没有任何选题清单混进版本库",
       f"扫描 {len([x for x in hits if x.strip()])} 处真·include_ids 键，全在合法源码/脚本里")

# ---------------------------------------------------------------- 5
head("5. 网站完整性 —— 学生页内容不能被误删")
site = tracked("quiz-app/site/")
if site > 5000:
    ok(f"quiz-app/site/ 追踪 {site:,} 个文件")
else:
    bad(f"quiz-app/site/ 只剩 {site:,} 个文件", "网站内容可能被误删")
st = git("status", "--short", "quiz-app/site/").strip()
ok("site/ 无未提交改动") if not st else warn("site/ 有未提交改动", st.split("\n")[0] + " …")

# ---------------------------------------------------------------- 6
if "--online" in sys.argv:
    head("6. 线上实测 —— 网站要开、选题要藏")

    def http(url: str) -> int:
        """用 curl 取状态码（Python 的 urllib 在 macOS 上常因缺根证书而 SSL 失败）。"""
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "25", url],
            capture_output=True, text=True,
        )
        try:
            return int((r.stdout or "0").strip())
        except ValueError:
            return -1

    SITE = "https://linlinislinlin.github.io/chembank"
    RAW = "https://raw.githubusercontent.com/linlinislinlin/chembank/main"
    c = http(f"{SITE}/as.html")
    ok("学生页 as.html 可访问 (200)") if c == 200 else bad(
        f"学生页 as.html 返回 {c}", "学生可能打不开网站！（-1 = 本机网络不通）")
    c = http(f"{SITE}/roster.js")
    ok("roster.js 可访问 (200)") if c == 200 else bad(f"roster.js 返回 {c}")
    for p in ["pick/1-atomic-structure-exam.yaml",
              "print/2-stoichiometry-homework-1/overleaf/main.pdf"]:
        c = http(f"{RAW}/{p}")
        ok(f"线上取不到 {os.path.basename(p)} (404)") if c == 404 else bad(
            f"线上仍能取到 {p}（HTTP {c}）", "选题/试卷仍公开！")

# ---------------------------------------------------------------- 结论
head("结论")
n_bad = results.count(False)
if n_bad == 0:
    print(f"  {GREEN}全部通过 —— 出卷内容只留本地，学生页正常。{OFF}")
    print(f"  {DIM}共 {len(results)} 项检查，0 失败。{OFF}")
    sys.exit(0)
else:
    print(f"  {RED}{n_bad} 项未通过（上面标 ✗）。{OFF}")
    print("  修好后重跑： python3 scripts/check_protection.py")
    sys.exit(1)
