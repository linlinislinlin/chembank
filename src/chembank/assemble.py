"""Render a pick list into an Obsidian tile-grid handout (Markdown).

Takes the pick-list JSON produced by ``chembank select`` and emits a single
Obsidian note consisting of a header plus a grid of thumbnail tiles, one per
question. Each tile shows the question's paper-clip screenshot (the PNG under
``<vault>/assets/<id>-paper.png``) with a small caption under it.

Image resolution
----------------
Figuring out where a question's screenshot lives is the fiddly part. The pick
JSON stores figure entries as vault-relative lists like
``["assets/cie-9701-2021-mj-p11-q1-paper.png"]`` but the actual file sits in
one of several sibling vault roots depending on paper kind (MCQ → ``vault/``,
structured → ``vault-structured/``, practical → ``vault-practical/``). We search
the target vault root *and* its known sibling vaults for the asset, then emit
a *top-level* Obsidian embed (never wrapped inside inline HTML, which Obsidian
does not render):

The user opens the *whole repository root* as the Obsidian vault (not the
sub-vault ``vault/``), so wiki-links like ``![[assets/x.png]]`` never resolve
(the assets actually live under ``vault/assets/`` etc.). Instead we emit every
image as a top-level markdown image whose path is relative to the repository
root (= ``vault_root.parent``), which is exactly the Obsidian vault root:

- asset under the repo root  → ``![](<repo-rel>/<file>.png|240)``
                               (markdown image, repo-root-relative, sized via
                                Obsidian's ``|width`` pipe syntax)
- asset outside the repo     → ``![](file://<abs>)``  (fallback, unlikely)
- asset not found / no fig   → text placeholder tile, never a crash

Each tile also carries a handout-internal sequential number (第1题, 第2题, …)
plus the original year/session/question, and the answer section reuses the same
sequential number so every question can be paired with its Mark Scheme answer.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Any

import yaml

# Vault roots (repo-relative) to search for assets, regardless of ``--vault``.
KNOWN_VAULTS = ("vault", "vault-structured", "vault-practical")

TEMPLATE = "tiles"

# Paper number → sibling vault root, used as a strong hint when a figure entry
# is ambiguous (helps pick the right vault before falling back to search).
_PAPER_KIND_VAULT = {
    "1": "vault",
    "2": "vault-structured",
    "4": "vault-structured",
    "5": "vault-structured",
    "3": "vault-practical",
}


def _slugify(text: str) -> str:
    """Reuse the slug logic from select.py without importing it (keeps this
    module usable even if select's imports change)."""
    text = re.sub(r"\s+", "-", text.strip().lower())
    text = re.sub(r"[^a-z0-9_\-]", "_", text)
    return re.sub(r"_+", "-", text).strip("-")


def _know_vaults() -> tuple[Path, ...]:
    """Sibling vault roots relative to the repo (may not exist in tests)."""
    return tuple(Path(v) for v in KNOWN_VAULTS)


def resolve_asset_path(
    figure_entry: str,
    *,
    vault_root: Path,
    search_roots: list[Path] | None = None,
) -> Path | None:
    """Return the real on-disk path of a figure entry, or ``None``.

    Handles vault-relative entries (``assets/x.png``), plus a bare filename or
    a path that is already relative/absolute. ``search_roots`` defaults to the
    target vault root plus its known sibling vaults under the same parent.
    """
    if not figure_entry:
        return None
    figure_entry = figure_entry.strip()
    # Strip Obsidian embed / markdown wrappers if stored inline.
    inner = figure_entry
    if inner.startswith("![[") and inner.endswith("]]"):
        inner = inner[3:-2]
    elif inner.startswith("![") and "]" in inner:
        inner = inner.split("]")[1].lstrip("(").rstrip(")").strip()
    if not inner:
        return None
    inner = inner.replace("\\", "/")

    candidates: list[Path] = []
    p = Path(inner)
    if p.is_absolute():
        candidates.append(p)
    else:
        roots = list(search_roots) if search_roots is not None else []
        roots.append(vault_root)
        # Sibling vaults of the target vault, e.g. fixtures/vault-structured.
        parent = vault_root.parent
        for name in KNOWN_VAULTS:
            roots.append(parent / name if parent else Path(name))
        # Also search repo-relative known vaults (helps when cwd = repo root).
        roots.extend(_know_vaults())
        # If the entry already points at a specific vault dir, try that too.
        for root in roots:
            candidates.append(root / inner)
        # Bare filename inside assets/.
        if "/" not in inner:
            for root in roots:
                candidates.append(root / "assets" / inner)

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _asset_relpath(asset_path: Path, base: Path) -> str | None:
    """Return ``asset_path`` relative to ``base`` (may contain ``..``), or None.

    Used for both vault-relative wikilinks (``base`` = the target vault root,
    an ancestor, so the result is a clean ``assets/<file>``) and cross-vault
    markdown images (``base`` = the output note's directory, which is *sibling*
    to the asset's vault, so ``..`` segments appear). ``os.path.relpath`` is
    used because ``Path.relative_to`` raises when ``base`` is not an ancestor.
    """
    try:
        rel = os.path.relpath(asset_path.resolve(), base.resolve())
    except (ValueError, OSError):
        return None
    return Path(rel).as_posix()


def _paper_vault_hint(paper: Any) -> str | None:
    return _PAPER_KIND_VAULT.get(str(paper)[:1])


def _detail_note_path(question: dict[str, Any], vault_root: Path) -> str | None:
    """Return a vault-relative path (no suffix) for the question's detail note,
    or None. Obsidian wikilinks are vault-scoped, so we only link to notes that
    live in the target vault root; sibling-vault notes yield a plain caption."""
    qid = question.get("id")
    if not qid:
        return None
    guess = vault_root / "questions" / f"{qid}.md"
    if guess.is_file():
        return f"questions/{qid}"
    return None


def render_tiles(
    pick: dict[str, Any],
    vault_root: str | Path,
    out_path: str | Path,
) -> Path:
    """Build the tile-grid Markdown note and write it to ``out_path``."""
    vault_root = Path(vault_root)
    out_path = Path(out_path)
    questions = list(pick.get("questions") or [])
    rules = pick.get("rules") or {}
    title = str(pick.get("title") or rules.get("title") or "Handout")
    slug = str(pick.get("slug") or _slugify(title))
    topic_titles = _collect_topic_titles(questions)
    syllabus_codes = _collect_syllabus_codes(questions)
    total_marks = _total_marks(questions)

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    front = {
        "id": slug,
        "aliases": [title],
        "type": "handout",
        "template": TEMPLATE,
        "title": title,
        "topic_titles": topic_titles or None,
        "syllabus_codes": syllabus_codes or None,
        "question_count": len(questions),
        "total_marks": total_marks,
        "generated_from": str(out_path.name),
        "generated_at": generated,
        "tags": ["handout", "chembank"],
    }

    lines: list[str] = [
        "---",
        yaml.dump(front, allow_unicode=True, sort_keys=False).strip(),
        "---",
        "",
        f"# {title}",
        "",
        _meta_line(questions, total_marks),
        "",
        "---",
        "",
    ]

    if not questions:
        lines.extend(["（无题目）", ""])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    lines.extend(_syllabus_section(syllabus_codes, rules))
    lines.append("")

    # Group questions by primary learning outcome. The flat, re-ordered list is
    # shared by both the grid and the answer section so the sequential numbers
    # (第1题, 第2题, …) stay global and continuous across every LO group.
    groups = _group_questions(questions)
    ordered = [q for _lo, _text, group in groups for q in group]

    # If a prior "---" was emitted by the syllabus section, no extra divider needed.
    lines.extend(_render_grid(groups, vault_root, out_path))
    lines.append("")
    lines.extend(_answer_section(ordered, vault_root))
    lines.append("→ [[题库首页]]")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def _meta_line(questions: list[dict[str, Any]], total_marks: int) -> str:
    subjects = {str(q.get("subject") or "CIE 9701") for q in questions}
    subject = ", ".join(sorted(subjects)) if subjects else "CIE 9701"
    return (
        f"**{subject}** · {len(questions)} 题 · "
        f"共 {total_marks} 分 · 生成于 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    )


def _collect_topic_titles(questions: list[dict[str, Any]]) -> list[str]:
    titles: list[str] = []
    for q in questions:
        for t in q.get("topic_titles") or []:
            if str(t) not in titles:
                titles.append(str(t))
    return titles


def _collect_syllabus_codes(questions: list[dict[str, Any]]) -> list[str]:
    codes: list[str] = []
    for q in questions:
        for c in q.get("syllabus_codes") or []:
            if str(c) not in codes:
                codes.append(str(c))
    return codes


def _total_marks(questions: list[dict[str, Any]]) -> int:
    total = 0
    for q in questions:
        m = q.get("marks")
        if isinstance(m, int):
            total += m
    return total


def _paper_figure(question: dict[str, Any]) -> str | None:
    """First paper-clip figure entry, or None."""
    for p in question.get("figures") or []:
        sp = str(p)
        if "-paper" in sp or "-paper." in sp or "-paper]" in sp:
            return sp
    # Fall back to the first figure if none is explicitly a paper clip.
    for p in question.get("figures") or []:
        if str(p):
            return str(p)
    return None


def _session_label(question: dict[str, Any]) -> str | None:
    """Session label such as ``MJ``/``ON``/``FM``, or None when absent."""
    session = question.get("session")
    if session is None:
        return None
    text = str(session).strip()
    return text.upper() if text else None


def _tile_caption(seq: int, question: dict[str, Any]) -> str:
    """Tile caption ``第N题 · <year> <session> · Q<orig> · <marks>分``.

    ``seq`` is the handout-internal sequential number (1,2,3…) that both the
    tile grid and the answer section share, so users can pair a question with
    its Mark Scheme answer by counting. The label also keeps the *original*
    exam year/session/question so the source is never lost.
    """
    bits = [f"第{seq}题"]
    year = question.get("year")
    session = _session_label(question)
    if year is not None and session:
        bits.append(f"{year} {session}")
    elif year is not None:
        bits.append(str(year))
    original = question.get("question")
    if original is not None and str(original).strip():
        bits.append(f"Q{original}")
    marks = question.get("marks")
    if isinstance(marks, int):
        bits.append(f"{marks} 分")
    return " · ".join(bits)


_SYLLABUS_PATH = "syllabus/cie-9701-as-a-level-chemistry.yaml"


def _syllabus_section(
    syllabus_codes: list[str], rules: dict[str, Any]
) -> list[str]:
    """Render a '考纲范围' (syllabus scope) block for the handout's codes.

    Reads the controlled syllabus YAML and, for every subtopic whose ``code`` is
    in the handout's ``syllabus_codes``, prints the topic group + subtopic title
    and each learning outcome (``id`` + text). Useful for quick human checks of
    whether a question matches the intended topic. Falls back gracefully when the
    YAML is missing or no subtopics are found.
    """
    path = Path(_SYLLABUS_PATH)
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    topics = data.get("topics") if isinstance(data, dict) else None
    if not isinstance(topics, list):
        return []

    wanted = {str(c) for c in syllabus_codes}
    out: list[str] = ["## 考纲范围", ""]
    found = False
    for topic in topics:
        for st in topic.get("subtopics") or []:
            code = str(st.get("code") or "")
            if code not in wanted:
                continue
            found = True
            title = st.get("title") or ""
            group = topic.get("group") or "Chemistry"
            out.append(f"**{code} — {title}**（{group}）")
            out.append("")
            for lo in st.get("learning_outcomes") or []:
                lid = lo.get("id") or ""
                text = lo.get("text") or ""
                out.append(f"- `{lid}` {text}")
            out.append("")
    if not found:
        return []
    # Close the section with a divider so it separates from the questions grid.
    out.append("---")
    out.append("")
    return out


def _lo_numeric_key(lo: str) -> tuple:
    """Return a sortable key for a learning-outcome id like ``"5.1-2"``.

    Compares the whole LO id numerically component-by-component, ignoring
    case and any trailing part-letter suffix. E.g. (topic, subtopic, item):
    ``5.1-1`` < ``5.1-2`` < ``5.1-3b`` < ``5.1-10`` < ``5.2-1`` < ``5.2-2a``.
    Values with no leading digits sort last.
    """
    text = str(lo).strip().lower()
    nums = [int(n) for n in re.findall(r"\d+", text)]
    if not nums:
        return (10**9,)
    rest = re.sub(r"\d+", "", text).strip("-.")
    return tuple(nums) + (rest,)


def _primary_lo(question: dict[str, Any]) -> str:
    """Return the primary LO id for a question's group, or ``""`` if none.

    The primary LO is the numerically smallest id among ``learning_outcomes``
    (e.g. ``["5.1-2","5.1-3b"]`` → ``"5.1-2"``), so each multi-LO question
    renders exactly once under its smallest LO. Missing/empty LOs → ``""``,
    which cleanly falls into the fallback group instead of crashing.
    """
    los = [str(x) for x in (question.get("learning_outcomes") or []) if str(x).strip()]
    if not los:
        return ""
    return min(los, key=_lo_numeric_key)


def _lo_text(question: dict[str, Any], lo: str) -> str:
    """Return the matching learning-outcome text snippet, or ``""``."""
    texts = question.get("learning_outcome_texts") or []
    for i, lid in enumerate(question.get("learning_outcomes") or []):
        if str(lid) == str(lo):
            if i < len(texts) and texts[i]:
                return str(texts[i]).strip()
            return ""
    return ""


def _group_questions(questions: list[dict[str, Any]]) -> list[tuple[str, str, list[dict]]]:
    """Group questions by primary learning outcome, in ascending LO order.

    Returns ``[(lo_id, header_text, [questions]), …]``. Each question appears
    exactly once, under its smallest LO. The fallback group uses an empty
    ``lo_id`` ("（未标 LO）" header) and sorts last. Within each group, questions
    are ordered by (year, paper, question). The flat concatenation of the group
    lists is what both the grid and the answer section iterate, guaranteeing the
    sequential numbering stays global.
    """
    buckets: dict[str, list[dict[str, Any]]] = {}
    for q in questions:
        lo = _primary_lo(q)
        buckets.setdefault(lo, []).append(q)

    def _q_key(q: dict[str, Any]) -> tuple:
        year = q.get("year")
        paper = str(q.get("paper") or "")
        return (year if year is not None else 0, paper, str(q.get("question") or ""))

    groups: list[tuple[str, str, list[dict]]] = []
    for lo in sorted(buckets, key=lambda x: _lo_numeric_key(x) if x else (10**9, "~")):
        group = sorted(buckets[lo], key=_q_key)
        groups.append((lo, _lo_text(group[0], lo) if lo else "", group))
    return groups


def _render_grid(
    groups: list[tuple[str, str, list[dict]]], vault_root: Path, note_path: Path
) -> list[str]:
    """Render each LO group as a header plus full-width stacked blocks.

    The user chose a stacked, exam-paper-like layout (as opposed to a 3-column
    thumbnail grid): each question gets its own row with a large screenshot,
    the shared sequential＋source caption, and a link to the detail note.
    Images use an HTML ``<img src="file://…">`` so they always render in
    Obsidian regardless of vault root or table-cell pipe splitting.

    ``groups`` is the ordered ``(lo_id, header_text, questions)`` list from
    :func:`_group_questions`; a numbered LO header sits above the questions in
    that group. Sequential numbering (第1题, …) runs continuously across all
    groups, so it stays in sync with the answer section.
    """
    import html

    out: list[str] = []
    seq = 0
    for lo, lo_text, group in groups:
        if lo:
            header = f"### {lo}"
            if lo_text:
                header += f" — {html.escape(lo_text)}"
            out.append(header)
            out.append("")
        elif group:
            out.append("### （未标 LO）")
            out.append("")
        for q in group:
            seq += 1
            out.append("---")
            out.append("")
            tile = _render_tile(q, vault_root, html, seq, note_path)
            for line in tile:
                out.append(line)
            out.append("")
    return out


def _render_tile(
    question: dict[str, Any],
    vault_root: Path,
    html: Any,
    seq: int,
    note_path: Path,
) -> list[str]:
    caption = _tile_caption(seq, question)
    qid = question.get("id") or ""
    detail = _detail_note_path(question, vault_root)

    lines: list[str] = []
    paper_fig = _paper_figure(question)
    asset_path = paper_fig and resolve_asset_path(paper_fig, vault_root=vault_root)
    if asset_path is not None:
        # A full-width image (max ~820px) so it reads like a real exam item.
        src = asset_path.resolve().as_uri()
        lines.append(f'<img src="{src}" alt="{html.escape(qid or "img")}" style="max-width:820px;width:100%;height:auto;"/>')
    else:
        snippet = _question_snippet(question, limit=60)
        lines.append(f"**（无图）**{html.escape(snippet)}")
    lines.append(f"**{html.escape(caption)}**")
    if detail:
        lines.append(f"[[{detail}]]")
    return lines


def _question_snippet(question: dict[str, Any], limit: int = 40) -> str:
    body = str(question.get("body") or question.get("question") or "")
    return body.strip().replace("\n", " ")[:limit]


def _answer_section(
    questions: list[dict[str, Any]], vault_root: Path
) -> list[str]:
    """Footer listing MS content, labelled with the *sequential* number that
    also appears on each question so users pair question ↔ answer by counting.

    - MCQ questions carry a short ``ms_answer`` (e.g. ``C``) → shown as text.
    - Structured/practical questions have no ``ms_answer`` but usually ship an
      ``…-ms.png`` screenshot → embedded as a thumbnail so the user can read
      the actual mark scheme without leaving the handout.
    """
    import html as _html

    entries = [q for q in questions if q.get("ms_answer") or _ms_figure(q, vault_root)]
    if not entries:
        return []
    out = ["## 答案区", ""]
    for seq, q in enumerate(questions, start=1):
        ms = q.get("ms_answer")
        detail = _detail_note_path(q, vault_root)
        if ms:
            line = f"- **第{seq}题**: {ms}"
            if detail:
                line += f" · [[{detail}]]"
            out.append(line)
            continue
        # No ms_answer: embed the Mark Scheme screenshot, if available.
        ms_path = _ms_figure(q, vault_root)
        if ms_path:
            src = ms_path.resolve().as_uri()
            link = f"[[{detail}]]" if detail else ""
            out.append(f"**第{seq}题**:")
            out.append(
                f'<img src="{src}" alt="ms" style="max-width:520px;width:100%;height:auto;"/>'
            )
            if link:
                out.append(link)
            out.append("")
    out.append("")
    return out


def _ms_figure(question: dict[str, Any], vault_root: Path) -> Any:
    """Return the resolved Mark-Scheme screenshot path for a question, or None.

    Looks for a ``figures`` entry whose filename contains ``-ms`` (the mark
    scheme clip). Uses ``resolve_asset_path`` so in-vault and sibling-vault
    assets are both found.
    """
    figures = question.get("figures") or []
    for f in figures:
        sf = str(f)
        if "-ms" in sf and ("." in sf):
            resolved = resolve_asset_path(sf, vault_root=vault_root)
            if resolved is not None:
                return resolved
    return None
