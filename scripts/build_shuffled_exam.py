#!/usr/bin/env python3
"""Build a shuffled, printable exam paper (student + teacher key) from a pick YAML.

Rules (teacher-confirmed):
  - text MCQ options  -> shuffle A/B/C/D, remap the answer letter
  - combo MCQ options -> shuffle A/B/C/D *and* the 1/2/3 statements, remap
  - table / figure / structure options -> keep exactly as the original clip
  - structured questions -> keep as original clip (no options to shuffle)

Outputs (into print/<slug>-shuffled/):
  overleaf/main.tex      student paper (typeset MCQ + kept clips)
  overleaf/answers.tex   teacher answer key (remapped letters + content)
  overleaf/main.pdf      compiled student PDF
  overleaf/answers.pdf   compiled answer-key PDF
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
DRAFT = REPO / "draft"
PRINT = REPO / "print"

XELATEX = "/Users/tsinglan-school/Library/TinyTeX/bin/universal-darwin/xelatex"

QID_RE = re.compile(r"cie-9701-(\d{4})-(\w+)-p(\d+)-q(\d+)", re.IGNORECASE)
ANS_RE = re.compile(r"Answer:\s*([A-Da-d])")
SESSION_SEASON = {"fm": "m", "mj": "s", "on": "w"}

# ---------------------------------------------------------------- LaTeX text

# Longest-first so e.g. C4H8O2 wins over C4 / O2.
FORMULAS = [
    ("Na₂SO₄•xH₂O", r"\ce{Na2SO4.xH2O}"),
    ("CH₃SH", r"\ce{CH3SH}"),
    ("C₄H₈O₂", r"\ce{C4H8O2}"),
    ("C₃H₆O₃", r"\ce{C3H6O3}"),
    ("C₂H₄O", r"\ce{C2H4O}"),
    ("C₂H₄", r"\ce{C2H4}"),
    ("C₃H₆", r"\ce{C3H6}"),
    ("AlCl₃", r"\ce{AlCl3}"),
    ("Na₂SO₄", r"\ce{Na2SO4}"),
    ("CO₂", r"\ce{CO2}"),
    ("SO₂", r"\ce{SO2}"),
    ("H₂O", r"\ce{H2O}"),
    ("O₂", r"\ce{O2}"),
    ("BF₃", r"\ce{BF3}"),
    ("PH₃", r"\ce{PH3}"),
    ("NH₃", r"\ce{NH3}"),
    ("CH₂O", r"\ce{CH2O}"),
    ("NaN₃", r"\ce{NaN3}"),
    ("Na⁺", r"\ce{Na+}"),
    ("Mg⁺", r"\ce{Mg+}"),
    ("COOH", r"\ce{COOH}"),
]


def _replace_all(s: str, pairs):
    for a, b in pairs:
        s = s.replace(a, b)
    return s


_OCR_FIXES = [
    ("behaveleast", "behave least"),
    ("cm³of", "cm³ of"),
    ("dm³of", "dm³ of"),
    ("m³of", "m³ of"),
    ("gof", "g of"),
    ("°Cand", "°C and"),
    ("kPa.", "kPa."),
]


def to_latex(text: str) -> str:
    """Convert raw extracted prose into LaTeX (mhchem for formulae)."""
    s = text.strip()
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in _OCR_FIXES:
        s = s.replace(a, b)
    # Chemical formulae, longest-first so CH2O beats H2O, C2H4O beats O2, etc.
    formulas = sorted(FORMULAS, key=lambda p: -len(p[0]))
    s = _replace_all(s, formulas)
    # Units / exponents.
    s = s.replace("mol dm–³", r"mol\,dm$^{-3}$")
    s = s.replace("mol dm⁻³", r"mol\,dm$^{-3}$")
    s = s.replace("moldm–³", r"mol\,dm$^{-3}$")
    s = s.replace("moldm⁻³", r"mol\,dm$^{-3}$")
    s = s.replace("dm–³", r"dm$^{-3}$")
    s = s.replace("dm⁻³", r"dm$^{-3}$")
    s = s.replace("dm³", r"dm$^3$")
    s = s.replace("cm³", r"cm$^3$")
    s = s.replace("m³", r"m$^3$")
    s = s.replace("10–⁶", r"$10^{-6}$")
    s = s.replace("10–³", r"$10^{-3}$")
    s = s.replace("10–²", r"$10^{-2}$")
    s = s.replace("°C", r"$^\circ$C")
    s = s.replace("×", r"$\times$")
    s = s.replace("→", r"$\to$")
    s = s.replace("•", r"$\cdot$")
    # Straighten stray unicode sub/superscripts that remain.
    s = s.replace("⁶", r"$^6$").replace("⁻", r"$^-$")
    s = s.replace("⁺", r"$^+$").replace("₂", r"$_2$").replace("₃", r"$_3$")
    s = s.replace("₄", r"$_4$").replace("₈", r"$_8$")
    s = re.sub(r"\s+", " ", s)
    return s


# ---------------------------------------------------------------- parse raw

def parse_qid(qid: str) -> dict | None:
    m = QID_RE.match(qid)
    if not m:
        return None
    year, session, paper, qnum = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
    return {"year": year, "yy": year[2:], "session": session,
            "season": SESSION_SEASON.get(session, session[0]),
            "paper": paper, "qnum": qnum}


def find_raw_txt(parts: dict) -> Path | None:
    d = DRAFT / f"9701_{parts['season']}{parts['yy']}_qp_{parts['paper']}"
    for name in (f"q{parts['qnum']}.txt", f"q{int(parts['qnum']):02d}.txt"):
        p = d / name
        if p.is_file():
            return p
    return None


def parse_raw(text: str) -> dict:
    """Return {stem, options[(letter, content)], answer, kind}."""
    text = text.replace("\r\n", "\n")
    body, _, _ = text.partition("--- MARK SCHEME ---")
    m = ANS_RE.search(text)
    answer = m.group(1).upper() if m else None
    lines = body.splitlines()

    # One option per line block.
    first_opt = None
    for i, ln in enumerate(lines):
        if re.match(r"^[ABCD]\s", ln.strip()):
            first_opt = i
            break
    if first_opt is None:
        return {"stem": body.strip(), "options": [], "answer": answer, "kind": "unknown"}

    # Single-line options: "A x B y C z D w" all on one line.
    single_line = None
    for i, ln in enumerate(lines):
        if len(re.findall(r"(?<!\S)[ABCD]\s+", ln)) >= 4:
            single_line = i
            break

    if single_line is not None:
        stem_lines = lines[:single_line]
        parts = re.split(r"\s+(?=[ABCD]\s)", lines[single_line].strip())
        options = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            options.append((p[0].upper(), p[1:].strip()))
    else:
        stem_lines = lines[:first_opt]
        options = []
        i = first_opt
        while i < len(lines):
            ln = lines[i].strip()
            mm = re.match(r"^([ABCD])\s+(.*)$", ln)
            if not mm:
                if options:
                    letter, content = options[-1]
                    options[-1] = (letter, content + " " + ln)
                i += 1
                continue
            options.append((mm.group(1).upper(), mm.group(2).strip()))
            i += 1

    kind = "text"
    # Table heuristic: all four option contents are purely numeric with >=1 space.
    if len(options) == 4 and all(re.fullmatch(r"[\d\s.]+", c) and " " in c for _l, c in options):
        kind = "table"
    # Combo heuristic: statements "1 ... 2 ... 3 ..." present in the stem.
    if re.search(r"^\s*1\s", body, re.M) and re.search(r"^\s*[23]\s", body, re.M):
        kind = "combo"

    return {"stem": "\n".join(stem_lines).strip(), "options": options,
            "answer": answer, "kind": kind}


# ---------------------------------------------------------------- shuffle

def shuffle_options(options, answer, kind, rng):
    """Return (new_options, new_answer, note). new_options = [(letter, content)]."""
    order = list(range(len(options)))
    rng.shuffle(order)
    new = []
    new_answer = None
    for ni, oi in enumerate(order):
        letter, content = options[oi]
        new.append(("ABCD"[ni], content))
        if letter == answer:
            new_answer = "ABCD"[ni]
    note = "shuffled" if kind == "combo" else "shuffled"
    return new, new_answer, note


def _marks_only(subtitle: str) -> str:
    """Return just the numeric mark total out of a 'Time allowed… Total marks…' line."""
    m = re.search(r"Total marks:\s*(\d+)", subtitle)
    return m.group(1) if m else ""


# ---------------------------------------------------------------- structured marks

STRUCTURED_DIR = REPO / "vault-structured" / "questions"
STRUCTURED_ASSETS = REPO / "vault-structured" / "assets"


def _structured_marks(qid: str) -> int:
    """Read the real marks for a structured part from its vault markdown."""
    try:
        text = (STRUCTURED_DIR / f"{qid}.md").read_text(encoding="utf-8")
    except OSError:
        return 1
    m = re.search(r"^marks:\s*(\d+)", text, re.M)
    return int(m.group(1)) if m else 1


# ---------------------------------------------------------------- LaTeX emit

PREAMBLE = r"""\documentclass[10pt,a4paper]{article}
\usepackage[margin=16mm,headheight=13pt,headsep=5pt,footskip=9mm]{geometry}
\usepackage{fontspec}
\usepackage[version=4]{mhchem}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{array}
\usepackage{enumitem}
\usepackage{needspace}
\usepackage{setspace}
\usepackage{fancyhdr}
\usepackage{amsmath,amssymb}
\usepackage{pgffor}

\raggedbottom
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.12em}
\setlist[enumerate]{leftmargin=1.6em,itemsep=0.25em,topsep=0.25em}

\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small \doctitle}
\fancyhead[R]{\small \docmarks}
\fancyfoot[C]{\small Page \thepage}
\renewcommand{\headrulewidth}{0.3pt}
\newcommand{\doctitle}{}\newcommand{\docmarks}{}

\graphicspath{{images/}}
\DeclareGraphicsExtensions{.png,.jpg,.jpeg,.pdf}

\newcommand{\clipq}[3]{%
  \par\sbox0{\includegraphics[width=0.94\linewidth,keepaspectratio]{#3}}%
  \Needspace{\dimexpr\ht0+1.5em+2pt\relax}%
  \noindent{\small\textbf{#1}}\hfill{\small[#2]}\par\vspace{0.08em}%
  \noindent\usebox0\par\vspace{0.28em}%
}
"""


def mcq_block(num: int, stem: str, options: list, marks: int = 1) -> str:
    """Render one MCQ as a 2×2 option grid: A/B on row 1, C/D on row 2."""
    lines = [r"\Needspace{5em}", f"\\textbf{{{num}.}}\\hfill[1 mark]\\par",
             stem, r"\par\vspace{0.15em}"]
    cells = [f"\\textbf{{{L}}}\\quad {c}" for L, c in options]
    lines.append(r"\begin{tabular}{@{} p{0.48\linewidth} p{0.48\linewidth} @{}}")
    lines.append(f"{cells[0]} & {cells[1]} \\\\[0.35em]")
    lines.append(f"{cells[2]} & {cells[3]} \\\\")
    lines.append(r"\end{tabular}")
    lines.append(r"\par\vspace{0.3em}")
    return "\n".join(lines)


def build_latex(title, subtitle, mcqs, clips, *, is_answers):
    doc = PREAMBLE
    doc += r"\renewcommand{\doctitle}{" + title + r"}"
    doc += "\n" + r"\renewcommand{\docmarks}{" + ("" if is_answers else "Total marks: " + _marks_only(subtitle)) + r"}"
    doc += "\n\\begin{document}\n"
    doc += "{\\Large\\bfseries " + title + "}\\par\\vspace{0.3em}\n"
    if not is_answers:
        doc += "{\\normalsize " + subtitle + "}\\par\\vspace{0.3em}\n"
        doc += "\\noindent\\rule{\\linewidth}{0.5pt}\\par\\vspace{0.4em}\n"
        doc += "\\noindent\\textbf{Instructions:} Answer \\textbf{all} questions. "
        doc += "Section A contains multiple-choice questions; choose one answer (A--D) for each. "
        doc += "Section B contains structured questions; show all working.\\par\\vspace{0.5em}\n"
    else:
        doc += "\\noindent\\rule{\\linewidth}{0.5pt}\\par\\vspace{0.4em}\n"

    if mcqs:
        doc += "\\section*{Section A --- Multiple Choice (1 mark each)}\\par\n"
        for m in mcqs:
            doc += m + "\n"
        doc += "\\newpage\n"

    if clips:
        doc += "\\section*{Section B --- Structured Questions}\\par\n"
        for i, item in enumerate(clips, start=1):
            label, marks, fname = item[0], item[1], item[2]
            mlabel = "1 mark" if marks == 1 else f"{marks} marks"
            doc += f"\\clipq{{{i}.}}{{{mlabel}}}{{{fname}}}\n"

    doc += "\\end{document}\n"
    return doc


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pick", help="pick/<exam>.yaml")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--version", default="A")
    args = ap.parse_args()

    pick_path = Path(args.pick)
    if not pick_path.is_file():
        print(f"missing pick: {pick_path}", file=sys.stderr)
        return 1
    data = yaml.safe_load(pick_path.read_text(encoding="utf-8")) or {}
    ids = data.get("include_ids") or []
    title = data.get("title") or pick_path.stem
    rng = __import__("random").Random(args.seed)

    section_a = []      # rendered LaTeX items, in original question order
    struct_clips = []   # (label, marks, filename, qid) structured questions
    answer_rows = []    # (label, answer letter, content latex)
    skip = []

    # Existing clip images (structured) live under print/<slug>/images/.
    src_slug = pick_path.stem
    src_img = PRINT / src_slug / "images"

    out_dir = PRINT / f"{src_slug}-shuffled-{args.version}"
    overleaf = out_dir / "overleaf"
    img_out = overleaf / "images"
    img_out.mkdir(parents=True, exist_ok=True)

    mcq_n = 0
    str_n = 0
    for qid in ids:
        parts = parse_qid(qid)
        if not parts:
            continue
        if parts["paper"].startswith("1"):
            mcq_n += 1
            raw = find_raw_txt(parts)
            if raw is None:
                skip.append(f"{qid}: no raw text")
                continue
            parsed = parse_raw(raw.read_text(encoding="utf-8"))
            opts = parsed["options"]
            ans = parsed["answer"]
            kind = parsed["kind"]
            stem = to_latex(parsed["stem"])

            if kind == "table" or not opts or len(opts) != 4:
                # Keep original clip (table / figure / unparseable) — in Section A.
                clip_name = f"mcq{mcq_n:02d}.png"
                src = src_img / clip_name
                if src.is_file():
                    shutil.copy2(src, img_out / clip_name)
                    section_a.append(f"\\clipq{{A{mcq_n}.}}{{1 mark}}{{{clip_name}}}")
                    answer_rows.append((f"A{mcq_n}", ans, "— kept unchanged (table/figure)"))
                else:
                    skip.append(f"{qid}: clip {clip_name} missing")
                continue

            new_opts, new_ans, _ = shuffle_options(opts, ans, kind, rng)
            opt_latex = [(L, to_latex(c)) for L, c in new_opts]
            section_a.append(mcq_block(mcq_n, stem, opt_latex))
            ans_content = next((c for L, c in opt_latex if L == new_ans), "")
            answer_rows.append((f"A{mcq_n}", new_ans, ans_content))
        else:
            # structured -> keep clip (unchanged), read real marks from vault.
            str_n += 1
            clip_name = f"str{str_n:02d}.png"
            src = src_img / clip_name
            marks = _structured_marks(qid)
            if src.is_file():
                shutil.copy2(src, img_out / clip_name)
                struct_clips.append((str(str_n), marks, clip_name, qid))
            else:
                skip.append(f"{qid}: clip {clip_name} missing")

    # ---- student paper ----
    total_marks = len(section_a) + sum(item[1] for item in struct_clips)
    subtitle = f"Time allowed: 45 minutes \\quad Total marks: {total_marks}"
    student_tex = build_latex(title, subtitle, section_a, struct_clips, is_answers=False)
    (overleaf / "main.tex").write_text(student_tex, encoding="utf-8")

    # ---- answer key (standalone document) ----
    ans_doc = PREAMBLE
    ans_doc += "\\renewcommand{\\doctitle}{" + title + " — Answer Key}\n"
    ans_doc += "\\renewcommand{\\docmarks}{shuffled · seed " + str(args.seed) + "}\n"
    ans_doc += "\\begin{document}\n"
    ans_doc += "{\\Large\\bfseries " + title + " — Answer Key}\\par\\vspace{0.3em}\n"
    ans_doc += "{\\normalsize Section A (letters) + Section B (Mark Scheme clips).}\\par\\vspace{0.4em}\n"
    ans_doc += "\\noindent\\rule{\\linewidth}{0.5pt}\\par\\vspace{0.6em}\n"
    ans_doc += "\\section*{Section A --- Multiple Choice}\\par\n"
    ans_doc += "\\begin{tabular}{@{} p{0.12\\linewidth} p{0.14\\linewidth} p{0.7\\linewidth} @{}}\n"
    ans_doc += "\\toprule\\textbf{Q} & \\textbf{Answer} & \\textbf{Content} \\\\\\midrule\n"
    for label, letter, content in answer_rows:
        ans_doc += f"{label} & {letter} & {content} \\\\\n"
    ans_doc += "\\bottomrule\\end{tabular}\n"

    # Section B: Mark Scheme clips for structured questions.
    if struct_clips:
        ans_doc += "\\newpage\n"
        ans_doc += "\\section*{Section B --- Structured (Mark Scheme)}\\par\n"
        for i, item in enumerate(struct_clips, start=1):
            label, marks, fname, qid = item[0], item[1], item[2], item[3]
            # Copy the MS clip into images/ for the answer key.
            ms_src = STRUCTURED_ASSETS / f"{qid}-ms.png"
            ms_name = f"ans-ms-{i:02d}.png"
            if ms_src.is_file():
                shutil.copy2(ms_src, img_out / ms_name)
                mlabel = "1 mark" if marks == 1 else f"{marks} marks"
                ans_doc += f"\\clipq{{B{i}.}}{{{mlabel}}}{{{ms_name}}}\n"
            else:
                ans_doc += f"\\textbf{{B{i}.}}\\quad (no Mark Scheme clip found)\\par\\vspace{{0.5em}}\n"

    ans_doc += "\\end{document}\n"
    (overleaf / "answers.tex").write_text(ans_doc, encoding="utf-8")

    # ---- compile ----
    for tex_name, pdf_name in (("main.tex", "main.pdf"), ("answers.tex", "answers.pdf")):
        r = subprocess.run(
            [XELATEX, "-interaction=nonstopmode", tex_name],
            cwd=overleaf, capture_output=True, text=True,
        )
        r2 = subprocess.run(
            [XELATEX, "-interaction=nonstopmode", tex_name],
            cwd=overleaf, capture_output=True, text=True,
        )
        ok = (overleaf / pdf_name).is_file()
        print(f"{tex_name}: {'OK -> ' + pdf_name if ok else 'FAILED'}")
        if not ok:
            tail = (r2.stdout + r2.stderr).splitlines()[-20:]
            print("\n".join(tail))

    n_table = sum(1 for it in section_a if "\\clipq{A" in it)
    n_shuffled = len(section_a) - n_table
    print(f"\n学生卷 PDF: {overleaf / 'main.pdf'}")
    print(f"答案卷 PDF: {overleaf / 'answers.pdf'}")
    print(f"乱序题目: {n_shuffled} MCQ · 保留原样: {n_table} 表格/图题 · {len(struct_clips)} 结构题")
    if skip:
        print("跳过/需注意：")
        for s in skip:
            print("  -", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
