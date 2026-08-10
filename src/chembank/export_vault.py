"""Re-export tagged drafts into Obsidian vault with chemistry format + figures."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from chembank.export_md import (
    write_lo_hub,
    write_paper_hub,
    write_question_markdown,
    write_syllabus_hub,
)
from chembank.extract import write_extracted_text
from chembank.figures import export_question_figures
from chembank.split import strip_footer_noise, write_split_output
from chembank.syllabus import (
    flatten_codes,
    flatten_learning_outcomes,
    load_syllabus,
    parent_code_for_lo,
    resolve_learning_outcomes,
    resolve_titles,
)


def _fresh_body(draft_dir: Path, n: str, *, draft_stem: str | None = None) -> str:
    name = draft_stem or f"q{n}"
    if not name.startswith("q"):
        name = f"q{name}"
    path = draft_dir / f"{name}.txt"
    if not path.exists():
        path = draft_dir / f"q{n}.txt"
    raw = path.read_text(encoding="utf-8")
    if "--- MARK SCHEME ---" in raw:
        raw = raw.split("--- MARK SCHEME ---", 1)[0]
    return strip_footer_noise(raw)


# Atom / group tokens that appear in failed skeletal-formula OCR (e.g. Q22).
# Optional charge / radical suffix covers mechanism OCR like C⁺ / H–.
_ATOM_OCR_TOKEN = re.compile(
    r"^(?:Br|Cl|I|F|OH|HO|NH|CN|CH|CO|Me|Et|Ph|H[₀0]?|N|C|[CHONSP]|[=|/−–—\\-]+)"
    r"[⁺⁻+−–—-]{0,2}$"
)

# PDF Symbol / ZapfDingbats often decode as C0 controls (ticks, δ+, etc.).
_PDF_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# Option letter + carbon-chain mechanism OCR (kept under A–D so old salad check missed it).
_MECHANISM_OPTION_RE = re.compile(
    r"^[A-D]\s+C(?:\s+(?:C|H|Br|Cl|I|F|N|O|C⁺|C\+|H⁺|H\+|Br⁺|Br\+|[^A-Za-z0-9\s])){2,}\s*$"
)
_HYDROGEN_GRID_RE = re.compile(r"^(?:H\s+){2,}H$")


def _strip_pdf_controls(text: str) -> str:
    """Remove C0 controls leaked from PDF symbol fonts (keep tab/newline)."""
    return _PDF_CONTROL_RE.sub("", text)


def _is_atom_salad_line(s: str) -> bool:
    """True for bond-line OCR garbage like 'C Br C Br C C Br C' or 'Cl H O Br'."""
    if not s:
        return False
    s = _strip_pdf_controls(s).strip()
    if not s:
        return True
    if s.startswith("|"):
        return False
    # Reject real prose / option text with words longer than atom symbols
    if re.search(r"[a-z]{3,}", s):
        return False
    # Legitimate short MCQ options: "A C", "B Cl–", "D Si"
    if re.fullmatch(
        r"[A-D]\s+(?:Br|Cl|I|F|OH|NH|CN|[A-Z][a-z]?)[⁺⁻+−–—-]{0,2}",
        s,
    ):
        return False
    if _MECHANISM_OPTION_RE.match(s):
        return True
    if _HYDROGEN_GRID_RE.match(s):
        return True
    # Charge-only crumbs (no option letter): ⁺ – / H– / Br⁺
    if re.fullmatch(r"[⁺⁻+−–—\s.•·*]+", s):
        return True
    if re.fullmatch(r"[HBrClINCO]+\s*[⁺⁻+−–—-]+|[⁺⁻+−–—-]+\s*[HBrClINCO]+", s):
        return True
    tokens = s.split()
    if len(tokens) < 2:
        # Single crumb left from skeletal OCR (Q26 trailing "O"; not bare A–D)
        return bool(
            re.fullmatch(
                r"(?:OH|HO|NH|CN|Br|Cl|I|F|[CHONSP]|[=|/−–—\\-]+)[⁺⁻+−–—-]{0,2}",
                s,
            )
        )
    # Require enough atom-like tokens so short legitimate options ("C P", "A C") survive.
    if len(tokens) == 2 and all(len(t) <= 2 for t in tokens):
        return False
    return all(_ATOM_OCR_TOKEN.fullmatch(t) for t in tokens)


_SECTION_B_KEY_START_RE = re.compile(
    r"^\s*(?:Section B\b|For each of the questions in this section\b|"
    r"The responses\s*A\s*to\s*D\b|"
    r"Decide whether each of the statements\b)",
    re.I,
)
_SECTION_B_KEY_LINE_RE = re.compile(
    r"^\s*(?:"
    r"A\s+B\s+C\s+D"
    r"|1,\s*2\s+and\s*3.*"
    r"|1\s+and\s*2.*"
    r"|2\s+and\s*3.*"
    r"|1\s+only.*"
    r"|are\s+only\s+are\s+only\s+are\s+is"
    r"|correct\s+correct\s+correct\s+correct"
    r"|No other combination of statements\b.*"
    r"|Use of the Data Booklet\b.*"
    r"|one or more of the three numbered statements\b.*"
    r"|be correct\.?"
    r"|the statements that you consider to be correct\)?\.?"
    r")\s*$",
    re.I,
)


def _strip_section_b_option_salad(body: str) -> str:
    """Drop garbled Section B A–D key OCR; options live in *-paper.png."""
    lines = body.splitlines()
    kept: list[str] = []
    skipping_key = False
    for line in lines:
        s = line.strip()
        if _SECTION_B_KEY_START_RE.match(s):
            skipping_key = True
            continue
        if skipping_key:
            if not s:
                continue
            if _SECTION_B_KEY_LINE_RE.match(s) or re.fullmatch(r"\d{1,2}", s):
                continue
            # Resumed real stem / statement
            skipping_key = False
        if _SECTION_B_KEY_LINE_RE.match(s):
            continue
        kept.append(line)
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


_MCQ_OPTION_LINE_RE = re.compile(r"^[A-D]\s+\S")
_MCQ_INLINE_ABCD_RE = re.compile(
    r"^\s*A\s+\S.+\s+B\s+\S.+\s+C\s+\S.+\s+D\s+\S",
)


def _strip_duplicate_mcq_options(body: str, *, has_paper_clip: bool) -> str:
    """When *-paper.png embeds A–D, drop duplicate option lists from the body.

    Policy: image is primary; body keeps the stem (for search/tagging) but must
    not repeat the A–D block already visible in the paper clip.
    """
    if not has_paper_clip or not body:
        return body
    lines = body.splitlines()
    packed_idxs = [
        i for i, ln in enumerate(lines) if _MCQ_INLINE_ABCD_RE.match(ln.strip())
    ]
    option_idxs = [
        i for i, ln in enumerate(lines) if _MCQ_OPTION_LINE_RE.match(ln.strip())
    ]
    letters = {
        lines[i].strip()[0]
        for i in option_idxs
        if lines[i].strip()[:1] in "ABCD"
    }
    has_packed = bool(packed_idxs)
    has_vertical = {"A", "D"} <= letters and len(option_idxs) >= 3
    if not has_packed and not has_vertical:
        return body

    drop = set(packed_idxs) | (set(option_idxs) if has_vertical or has_packed else set())
    # When a packed A–D row is present, also drop any vertical A–D lines
    if has_packed:
        drop |= set(option_idxs)
    kept: list[str] = []
    for i, ln in enumerate(lines):
        if i in drop:
            continue
        kept.append(ln)
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_diagram_label_noise(body: str, *, has_figure: bool) -> str:
    """Remove orphan axis / spectrum / structure OCR left when a PNG is embedded."""
    # Detect structure/mechanism markers on the raw body first — Section B salad
    # stripping also matches a lone "A B C D" line and would hide the signal.
    raw_lines = body.splitlines()
    has_structure_options = False
    mechanism_ocr = False
    for line in raw_lines:
        s = line.strip()
        if re.fullmatch(r"A\s+B\s+C\s+D", s):
            has_structure_options = True
        if _MECHANISM_OPTION_RE.match(s):
            mechanism_ocr = True
            has_structure_options = True
    letters = [ln.strip() for ln in raw_lines if ln.strip() in "ABCD"]
    if letters[:4] == ["A", "B", "C", "D"] or set(letters) >= set("ABCD"):
        if not any(re.match(r"^[A-D]\s+\S", ln.strip()) for ln in raw_lines):
            has_structure_options = True
    # Mechanism diagram debris without a clean A B C D row
    if any(
        re.search(r"(?:H[₃3]C\s+C\s+Br|N\s+C–|HO–••)", ln)
        for ln in raw_lines
    ):
        has_structure_options = True

    body = _strip_section_b_option_salad(body)
    body = _strip_pdf_controls(body)
    if not has_figure:
        return strip_footer_noise(body)
    lines = body.splitlines()
    kept: list[str] = []
    axis_only = re.compile(
        r"^(?:"
        r"[TtxXyY][₀₁₂₃₄₅₆₇₈₉0-9]?"
        r"|0|y|x|0\s*x|x\s*0|%"
        r"|transmittance(?:\s*/\s*%)?"
        r"|wavenumber(?:\s*/\s*cm[–\−-]¹?)?"
        r"|enthalpy|products?|reactants?"
        r"|progress of reaction"
        r"|heat exchanger|catalytic|converter|condenser"
        r")$",
        re.IGNORECASE,
    )
    spectrum_scale = re.compile(
        r"^(?:100|50|0|\d{3,4}(?:\s+\d{3,4})+)$"
    )

    # Tick/cross table rows that became empty after control-stripping: "A  ", "B  "
    tick_rows = [
        ln.strip()
        for ln in lines
        if re.fullmatch(r"[A-D]\s*", ln.strip())
        or re.fullmatch(r"[A-D](?:\s+[✓✗×xX✔✖])+", ln.strip())
    ]
    if len(tick_rows) >= 3:
        has_structure_options = True

    for line in lines:
        s = line.strip()
        if not s:
            kept.append(line)
            continue
        if axis_only.fullmatch(s):
            continue
        if re.fullmatch(r"[0yxYX]\s+[0yxYX]", s):
            continue
        if spectrum_scale.fullmatch(s):
            continue
        # Atom-letter / mechanism garbage from skeletal formulas
        if _is_atom_salad_line(s):
            continue
        # Charge-only / bullet crumbs after control strip
        if re.fullmatch(r"[⁺⁻+−–—\s.•·*]+", s):
            continue
        # Bare A/B/C/D with no option text — structures are in the image
        if has_structure_options and (
            s in "ABCD"
            or re.fullmatch(r"A\s+B\s+C\s+D", s)
            or re.fullmatch(r"[A-D]\s*", s)
        ):
            continue
        # Structure/mechanism clips: drop non-prose OCR; PNG is the reading surface
        if has_structure_options and not re.match(r"^\d+\b", s):
            if not re.search(r"[a-z]{3,}", s):
                continue
        kept.append(line)

    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return strip_footer_noise(text)


def export_paper_to_vault(
    *,
    qp_pdf: Path,
    draft_dir: Path,
    vault_dir: Path,
    questions_dir: Path | None = None,
    refresh_extract: bool = True,
    ms_pdf: Path | None = None,
) -> dict[str, Any]:
    """Refresh extract/split (optional), render figures, write Obsidian markdown."""
    qp_pdf = Path(qp_pdf)
    draft_dir = Path(draft_dir)
    vault_dir = Path(vault_dir)
    questions_dir = Path(questions_dir) if questions_dir else None
    assets_dir = vault_dir / "assets"

    from chembank.registry import paper_kind

    m_paper = re.search(r"qp_(\d+)$", draft_dir.name)
    paper_num = int(m_paper.group(1)) if m_paper else None
    kind = paper_kind(paper_num) if paper_num is not None else "unknown"

    if refresh_extract:
        text_path = draft_dir.parent / f"{draft_dir.name}.txt"
        write_extracted_text(qp_pdf, text_path)
        ms_text = None
        if ms_pdf and Path(ms_pdf).exists():
            from chembank.extract import extract_pdf_text

            # Infer paper number from draft name …_qp_21
            recover = kind == "mcq"
            ms_text = extract_pdf_text(Path(ms_pdf), recover_symbols=recover)
        write_split_output(
            text_path.read_text(encoding="utf-8"),
            draft_dir,
            source_name=draft_dir.name,
            mark_scheme_text=ms_text,
            # Paper 3: one draft per experiment block / main question
            part_level=False if kind == "practical" else None,
        )

    tagged_dir = draft_dir / "tagged"
    if not tagged_dir.exists():
        raise FileNotFoundError(f"No tagged JSON in {tagged_dir}")

    from chembank.figures import export_structured_part_figures
    from chembank.structured_parts import (
        draft_stem_sort_key,
        is_garbage_ms_text,
        parse_part_id,
        question_id_prefix,
    )

    # Infer id prefix from first tagged file
    sample = json.loads(next(tagged_dir.glob("q*.json")).read_text(encoding="utf-8"))
    prefix = question_id_prefix(sample["id"])

    tagged_paths = sorted(
        tagged_dir.glob("q*.json"),
        key=lambda p: draft_stem_sort_key(p.stem),
    )
    tagged_records = [
        json.loads(p.read_text(encoding="utf-8")) for p in tagged_paths
    ]
    part_mode = any(
        r.get("parent_question") or parse_part_id(str(r.get("question") or ""))
        for r in tagged_records
    )
    # Force topic grain for practical even if a stray part-tagged JSON appears
    if kind == "practical":
        part_mode = False

    if part_mode:
        part_labels = [str(r["question"]) for r in tagged_records]
        fig_map = export_structured_part_figures(
            qp_pdf,
            ms_pdf=ms_pdf,
            question_id_prefix=prefix,
            assets_dir=assets_dir,
            part_labels=part_labels,
        )
    else:
        tagged_qnums = [str(r["question"]) for r in tagged_records]
        fig_map = export_question_figures(
            qp_pdf,
            question_id_prefix=prefix,
            assets_dir=assets_dir,
            questions=tagged_qnums,
            include_paper_clips=True,
            ms_pdf=ms_pdf if kind == "practical" else None,
        )

    syllabus = load_syllabus()
    lookup = flatten_codes(syllabus)
    lo_lookup = flatten_learning_outcomes(syllabus)
    records: list[dict[str, Any]] = []
    for path, data in zip(tagged_paths, tagged_records):
        n = str(data["question"])
        pid = parse_part_id(n)
        figs = fig_map.get(n, [])
        if not any(p.endswith("-paper.png") or "-paper." in p for p in figs):
            raise RuntimeError(
                f"q{n}: export missing required paper clip "
                f"({prefix}-q{(pid.slug if pid else n)}-paper.png)"
            )
        require_ms = part_mode or kind == "practical"
        if require_ms and ms_pdf and Path(ms_pdf).exists():
            if not any(p.endswith("-ms.png") or "-ms." in p for p in figs):
                raise RuntimeError(
                    f"q{n}: export missing required MS clip "
                    f"({prefix}-q{(pid.slug if pid else n)}-ms.png)"
                )
        draft_stem = None
        if pid:
            draft_stem = pid.draft_stem
            data.setdefault("parent_question", pid.parent)
            data.setdefault("part", pid.part)
        body = _fresh_body(draft_dir, n, draft_stem=draft_stem)
        body = _strip_diagram_label_noise(body, has_figure=bool(figs))
        # Always strip Section B key salad (even if figure path list is empty)
        body = _strip_section_b_option_salad(body)
        has_paper = any(p.endswith("-paper.png") or "-paper." in p for p in figs)
        body = _strip_duplicate_mcq_options(body, has_paper_clip=has_paper)
        data["body"] = body
        data["figures"] = figs
        codes = list(data.get("syllabus_codes") or [])
        if codes:
            try:
                data["topic_titles"] = resolve_titles(codes, syllabus)
            except KeyError:
                pass
        lo_ids = [str(x) for x in (data.get("learning_outcomes") or []) if str(x).strip()]
        if lo_ids:
            try:
                data["learning_outcomes"] = lo_ids
                data["learning_outcome_texts"] = resolve_learning_outcomes(
                    lo_ids, syllabus
                )
            except KeyError:
                pass
        # refresh ms from draft if present; drop garbage OCR when MS image exists
        raw_path = draft_dir / f"{draft_stem or ('q' + n)}.txt"
        if raw_path.exists():
            raw = raw_path.read_text(encoding="utf-8")
            if "--- MARK SCHEME ---" in raw and not data.get("mark_scheme"):
                data["mark_scheme"] = raw.split("--- MARK SCHEME ---", 1)[1].strip()
        has_ms_img = any(p.endswith("-ms.png") or "-ms." in p for p in figs)
        if has_ms_img and is_garbage_ms_text(data.get("mark_scheme")):
            data["mark_scheme"] = ""
        records.append(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    by_code: dict[str, list[str]] = defaultdict(list)
    by_lo: dict[str, list[str]] = defaultdict(list)
    id_codes: dict[str, set[str]] = {}
    for data in records:
        qid = data["id"]
        codes = {str(c) for c in data.get("syllabus_codes") or []}
        id_codes[qid] = codes
        for c in codes:
            by_code[c].append(qid)
        for lo_id in data.get("learning_outcomes") or []:
            by_lo[str(lo_id)].append(qid)

    def related_for(qid: str) -> list[str]:
        scored: dict[str, int] = defaultdict(int)
        for c in id_codes[qid]:
            for other in by_code[c]:
                if other != qid:
                    scored[other] += 1
        return [oid for oid, _ in sorted(scored.items(), key=lambda x: (-x[1], x[0]))[:8]]

    vault_q = vault_dir / "questions"
    for data in records:
        rel = related_for(data["id"])
        figs = data.get("figures") or []
        write_question_markdown(
            data, vault_q / f"{data['id']}.md", related_ids=rel, figure_paths=figs
        )
        if questions_dir:
            write_question_markdown(
                data,
                questions_dir / f"{data['id']}.md",
                related_ids=rel,
                figure_paths=figs,
            )

    used = sorted(by_code.keys(), key=lambda c: [int(x) for x in c.split(".")])
    parents = {c.split(".")[0] for c in used if "." in c}
    for c in sorted(set(used) | parents, key=lambda x: [int(p) for p in x.split(".")]):
        write_syllabus_hub(
            c,
            lookup.get(c, c),
            vault_dir / "syllabus" / f"{c}.md",
            question_ids=by_code.get(c, []),
            parent_code=c.split(".")[0] if "." in c else None,
        )

    # Refresh LO hubs for outcomes used on this paper (aliases + Dataview).
    # For the full AS vocabulary (including unused LOs like 1.1-1), run:
    #   chembank export-lo-hubs --vault vault
    for lo_id in sorted(by_lo.keys()):
        text = lo_lookup.get(lo_id, lo_id)
        try:
            parent = parent_code_for_lo(lo_id)
        except ValueError:
            parent = lo_id.rsplit("-", 1)[0]
        write_lo_hub(
            lo_id,
            text,
            vault_dir / "syllabus" / "lo" / f"{lo_id}.md",
            parent_code=parent,
            question_ids=by_lo[lo_id],
        )

    qids = [d["id"] for d in records]
    year = sample.get("year", 2021)
    session = sample.get("session", "MJ")
    paper = sample.get("paper", 11)
    write_paper_hub(
        syllabus_code=str(sample.get("syllabus_code", "9701")),
        year=int(year),
        session=str(session),
        paper=paper,
        question_ids=qids,
        out_path=vault_dir
        / "papers"
        / f"{sample.get('syllabus_code', '9701')}-{year}-{str(session).lower()}-p{paper}.md",
    )

    # Thin parent-question index notes (q2.md) linking part children
    if part_mode:
        by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for data in records:
            pq = str(data.get("parent_question") or "")
            if pq:
                by_parent[pq].append(data)
        for pq, children in by_parent.items():
            children = sorted(
                children,
                key=lambda d: draft_stem_sort_key(
                    parse_part_id(str(d["question"])).draft_stem  # type: ignore[union-attr]
                    if parse_part_id(str(d["question"]))
                    else str(d["question"])
                ),
            )
            idx_id = f"{prefix}-q{pq}"
            lines = [
                "---",
                f"id: {idx_id}",
                "type: structured-parent-index",
                f"paper: {paper}",
                f"question: '{pq}'",
                "tags: [chembank, structured-index]",
                "---",
                "",
                f"# Question {pq}",
                "",
                f"试卷：[[papers/{sample.get('syllabus_code', '9701')}-{year}-{str(session).lower()}-p{paper}"
                f"|{year} {session} Paper {paper}]]",
                "",
                "## Parts",
                "",
            ]
            for ch in children:
                part = ch.get("part") or ""
                lines.append(f"- [[{ch['id']}|{ch.get('question')} {part}]]".replace("  ", " "))
            lines.append("")
            (vault_q / f"{idx_id}.md").write_text("\n".join(lines), encoding="utf-8")
            if questions_dir:
                Path(questions_dir).mkdir(parents=True, exist_ok=True)
                (Path(questions_dir) / f"{idx_id}.md").write_text(
                    "\n".join(lines), encoding="utf-8"
                )

    return {
        "questions": len(records),
        "figures": {k: v for k, v in fig_map.items()},
        "assets_dir": str(assets_dir),
    }
