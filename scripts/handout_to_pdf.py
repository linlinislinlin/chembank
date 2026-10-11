#!/usr/bin/env python3
"""把 ChemBank 讲义 (.md) 渲染成打印用 PDF。

用法：
    python3 scripts/handout_to_pdf.py <handout.md> [--out-dir handouts-pdf]

产出两份 PDF：
  <slug>-student.pdf   学生版：只有题目（不含答案）
  <slug>-teacher.pdf   教师版：题目 + 标准答案（MCQ 选项字母 + 结构题 mark scheme 图）

依赖本机 Google Chrome 无头模式渲染（无需 LaTeX）。
"""
from __future__ import annotations

import argparse
import html
import os
import re
import signal
import subprocess
import sys
import time
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 14mm 12mm; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", "Helvetica Neue", Arial, sans-serif;
       color: #111; font-size: 12px; line-height: 1.5; }
h1 { font-size: 19px; margin: 0 0 2px; }
.meta { color: #555; font-size: 12px; margin-bottom: 4px; }
h2 { font-size: 14px; margin: 18px 0 8px; padding-top: 6px; border-top: 2px solid #333; }
.q { break-inside: avoid; page-break-inside: avoid; margin: 0 0 8px; }
.q img { max-width: 100%; height: auto; display: block; }
.cap { font-size: 11px; color: #444; margin: 1px 0 10px; }
hr.sep { border: 0; border-top: 1px dashed #bbb; margin: 6px 0 10px; }
.ans { margin: 2px 0 4px; font-weight: 600; }
.mswrap { break-inside: avoid; page-break-inside: avoid; margin-bottom: 8px; }
.mswrap img { max-width: 78%; height: auto; display: block; }
.pagebreak { break-before: page; page-break-before: always; }
"""


def read_frontmatter_title(md: str) -> str:
    m = re.search(r"^title:\s*(.+)$", md, re.MULTILINE)
    return m.group(1).strip().strip('"').strip("'") if m else "Homework"


def meta_line(md: str) -> str:
    m = re.search(r"\*\*CIE 9701\*\*\s*·\s*(\d+)\s*题\s*·\s*共\s*(\d+)\s*分", md)
    return f"CIE 9701 · {m.group(1)} 题 · 共 {m.group(2)} 分" if m else "CIE 9701"


def strip_obsidian_links(line: str) -> str:
    return re.sub(r"\[\[[^\]]*\]\]", "", line)


def questions_html(chunk: str) -> str:
    out: list[str] = []
    img: str | None = None
    cap: str | None = None

    def flush() -> None:
        nonlocal img, cap
        if img or cap:
            out.append('<div class="q">')
            if img:
                out.append(img)
            if cap:
                out.append(f'<div class="cap">{html.escape(cap)}</div>')
            out.append("</div>")
        img, cap = None, None

    for raw in chunk.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("<img"):
            flush()
            img = line
        elif line == "---":
            flush()
            out.append('<hr class="sep">')
        elif line.startswith("**第") and "题" in line:
            cap = strip_obsidian_links(line).replace("**", "").strip()
        else:
            # 其他零散文本/边框，跳过
            continue
    flush()
    return "\n".join(out)


def answers_html(chunk: str) -> str:
    out: list[str] = []
    for raw in chunk.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"-\s*\*\*第(\d+)题\*\*[:：]\s*([A-D])\b", line)
        if m:
            out.append(f'<div class="ans">第 {m.group(1)} 题：{m.group(2)}</div>')
            continue
        m = re.match(r"\*\*第(\d+)题\*\*[:：]?\s*$", line)
        if m:
            out.append(f'<div class="ans">第 {m.group(1)} 题：</div>')
            continue
        if line.startswith("<img"):
            out.append(f'<div class="mswrap">{line}</div>')
            continue
    return "\n".join(out)


def build_html(title: str, meta: str, questions: str, answers: str | None) -> str:
    ans_block = ""
    if answers is not None:
        ans_block = (
            '<h2 class="pagebreak">标准答案</h2>\n' + answers
        )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        f"<h1>{html.escape(title)}</h1><div class='meta'>{html.escape(meta)}</div>"
        "<h2>试题</h2>"
        f"{questions}"
        f"{ans_block}"
        "</body></html>"
    )


def render_pdf(html_path: Path, out_pdf: Path) -> None:
    """把已写好的 HTML 文件用 Chrome 无头渲染成 PDF。"""
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    tmp_root = out_pdf.parent / ".tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    td = tempfile.mkdtemp(dir=tmp_root)
    cmd = [
        CHROME, "--headless=old", "--disable-gpu", "--no-sandbox",
        "--disable-dev-shm-usage", "--hide-scrollbars",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        f"--user-data-dir={td}/chrome",
        f"--print-to-pdf={out_pdf}",
        html_path.as_uri(),
    ]
    # 不接管 stdout/stderr：Chrome 子进程会继承管道，导致父进程读不到 EOF 而假死。
    proc = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # 轮询产物：只要 PDF 写完且大小稳定，就认为渲染完成（Chrome 常写完不退出）。
    deadline = time.time() + 45
    ok = False
    while time.time() < deadline:
        if out_pdf.exists() and out_pdf.stat().st_size > 1024:
            s1 = out_pdf.stat().st_size
            time.sleep(0.8)
            if out_pdf.exists() and out_pdf.stat().st_size == s1:
                ok = True
                break
        time.sleep(0.4)
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        proc.kill()
    if not ok:
        sys.exit(f"❌ 生成失败：{out_pdf}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("handout", help="讲义 .md 路径")
    ap.add_argument("--out-dir", default=str(REPO / "handouts-pdf"))
    args = ap.parse_args()

    src = Path(args.handout).resolve()
    md = src.read_text(encoding="utf-8")
    title = read_frontmatter_title(md)
    meta = meta_line(md)

    i_img = md.find("<img")
    i_ans = md.find("## 答案区")
    if i_img == -1:
        sys.exit(f"❌ 讲义里没有题目图片：{src}")
    q_chunk = md[i_img: i_ans if i_ans != -1 else len(md)]
    a_chunk = md[i_ans + len("## 答案区"):].split("→ [[")[0] if i_ans != -1 else ""

    slug = src.stem
    out_dir = Path(args.out_dir).resolve()
    html_dir = out_dir / "html"
    html_dir.mkdir(parents=True, exist_ok=True)
    q_html = questions_html(q_chunk)
    a_html = answers_html(a_chunk)

    s_html = html_dir / f"{slug}-student.html"
    t_html = html_dir / f"{slug}-teacher.html"
    s_html.write_text(build_html(title, meta, q_html, None), encoding="utf-8")
    t_html.write_text(build_html(title, meta, q_html, a_html), encoding="utf-8")

    s_pdf = out_dir / f"{slug}-student.pdf"
    t_pdf = out_dir / f"{slug}-teacher.pdf"
    render_pdf(s_html, s_pdf)
    render_pdf(t_html, t_pdf)
    print(f"✅ {title}")
    print(f"   学生版: {s_pdf}")
    print(f"   教师版: {t_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
