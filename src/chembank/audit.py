"""Quality audit for exported ChemBank vault questions.

Hard-fails known failure modes so export cannot be marked done until clean.
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from chembank.export_vault import _is_atom_salad_line, _strip_duplicate_mcq_options
from chembank.syllabus import flatten_codes, flatten_learning_outcomes, load_syllabus

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FOOTER_RE = re.compile(
    r"(?:©\s*UCLES|9701/\d+/[MWCOPJ]/\d+|\[Turn over\]|Page\s+\d+\s+of\s+\d+)",
    re.I,
)
PUA_RE = re.compile(r"[\uf000-\uf0ff]")
# PDF symbol fonts often leak as C0 controls (not in PUA range).
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
GLUE_RE = re.compile(
    r"showboth|ofeach|andare|thestatements|responsesA\s*toD|1,\s*2\s+and3\b",
    re.I,
)
OPTIONS_RUN_RE = re.compile(r"A\s+\S.+\s+B\s+\S.+\s+C\s+\S")
BAD_ARROW_RE = re.compile(r"[≡\uf0ae\uf0d7]")
BRACKET_CHARGE_RE = re.compile(r"\\mathrm\{[^}]*\][+-]\}|\][+-](?!\^)")
QUESTION_SECTION_RE = re.compile(r"## Question\n(.*?)(?=\n## |\Z)", re.S)
MCQ_OPTION_LINE_RE = re.compile(r"^[A-D]\s+\S")

# Forbidden failure-mode codes (skill Pre-done checklist)
FAIL_CODES = (
    "missing_paper_png",
    "missing_paper_embed",
    "missing_md",
    "empty_LO",
    "unknown_LO",
    "unknown_code",
    "missing_A_or_D_in_clip",
    "missing_B_or_C_in_clip",
    "section_b_missing_combo_key",
    "foreign_or_wrong_stem",
    "foreign_calcium_stmt",
    "atom_salad",
    "options_run_together",
    "footer_leak",
    "trailing_page_num",
    "bad_arrow",
    "pua_chars",
    "control_chars",
    "glued_words",
    "broken_ion_charge",
    "invented_facility",
    "no_paper_clip_geometry",
    "missing_dual_write",
    "duplicate_options_under_paper",
    "next_question_bleed",
    "next_letter_bleed",
    "next_roman_bleed",
    "missing_shared_stem",
    "missing_letter_preamble",
    "tiny_paper_png",
    "stale_or_wrong_paper_png",
    "empty_question_body",
    "clipped_right_mark_grid",
)

# Practical paper clips must keep the CIE right-edge mark grid (I–IV boxes).
# Historical bug: x1 = page.width - 32 clipped those boxes (~30pt from edge).
_PRACTICAL_MAX_RIGHT_INSET_PT = 16.0

_ROMAN_ORDER = ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x")
_STEM_STOP = {
    "with",
    "from",
    "that",
    "this",
    "when",
    "have",
    "each",
    "into",
    "used",
    "give",
    "state",
    "question",
}
_PREAMBLE_STOP = {
    "which",
    "about",
    "using",
    "under",
    "after",
    "before",
    "given",
    "state",
    "write",
    "their",
    "there",
    "these",
    "those",
    "other",
    "would",
    "could",
}

# Exported paper PNGs below this are almost certainly blank / truncated crops.
_MIN_PAPER_PNG_BYTES = 3000
_MIN_PAPER_PNG_HEIGHT = 80


@dataclass
class Finding:
    question_id: str
    code: str
    detail: str = ""

    def __str__(self) -> str:
        if self.detail:
            return f"{self.question_id}: {self.code} ({self.detail})"
        return f"{self.question_id}: {self.code}"


@dataclass
class AuditResult:
    checked: int = 0
    passed: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def failed(self) -> int:
        return self.checked - self.passed

    def by_code(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in self.findings:
            counts[f.code] = counts.get(f.code, 0) + 1
        return counts


def _front_and_body(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return {}, text
    front = yaml.safe_load(m.group(1)) or {}
    return front if isinstance(front, dict) else {}, text[m.end() :]


def _question_body(body: str) -> str:
    m = QUESTION_SECTION_RE.search(body)
    return m.group(1) if m else body


def _audit_markdown(
    md_path: Path,
    *,
    vault_dir: Path,
    questions_dir: Path | None,
    allowed_codes: dict[str, str],
    allowed_los: dict[str, str],
) -> list[Finding]:
    findings: list[Finding] = []
    front, body = _front_and_body(md_path)
    qid = str(front.get("id") or md_path.stem)
    qbody = _question_body(body)
    qnum = str(front.get("question") or "")

    paper_png = vault_dir / "assets" / f"{qid}-paper.png"
    if not paper_png.exists():
        findings.append(Finding(qid, "missing_paper_png"))
    else:
        try:
            size = paper_png.stat().st_size
        except OSError:
            size = 0
        if size < _MIN_PAPER_PNG_BYTES:
            findings.append(Finding(qid, "tiny_paper_png", f"{size} bytes"))
        else:
            try:
                # PNG IHDR width/height at bytes 16–24
                data = paper_png.read_bytes()
                if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
                    import struct

                    _w, h = struct.unpack(">II", data[16:24])
                    if h < _MIN_PAPER_PNG_HEIGHT:
                        findings.append(
                            Finding(qid, "tiny_paper_png", f"height={h}px")
                        )
            except OSError:
                pass
    if f"![[assets/{qid}-paper.png]]" not in (body if body else md_path.read_text()):
        # re-check full file for embed
        full = md_path.read_text(encoding="utf-8")
        if f"![[assets/{qid}-paper.png]]" not in full:
            findings.append(Finding(qid, "missing_paper_embed"))

    # Structured parts: require MS screenshot embed (image-primary mark scheme)
    qtype = str(front.get("question_type") or "").lower()
    is_structured = qtype in {"structured", "extended", "practical", "data"} or bool(
        front.get("parent_question") or front.get("part")
    )
    if is_structured and front.get("type") != "structured-parent-index":
        ms_png = vault_dir / "assets" / f"{qid}-ms.png"
        full_ms = body if body else md_path.read_text(encoding="utf-8")
        if not ms_png.exists():
            findings.append(Finding(qid, "missing_ms_png"))
        elif f"![[assets/{qid}-ms.png]]" not in full_ms:
            full_ms = md_path.read_text(encoding="utf-8")
            if f"![[assets/{qid}-ms.png]]" not in full_ms:
                findings.append(Finding(qid, "missing_ms_embed"))

    # Stem / searchable body must exist under the paper embed (not clip-only empty)
    body_lines = [
        ln.strip()
        for ln in qbody.splitlines()
        if ln.strip() and not ln.strip().startswith("![[")
    ]
    if not body_lines:
        findings.append(Finding(qid, "empty_question_body"))

    qtype = str(front.get("question_type") or "").lower()
    paper_val = front.get("paper")
    is_practical = qtype == "practical"
    if not is_practical and paper_val is not None:
        from chembank.registry import paper_kind

        is_practical = paper_kind(paper_val) == "practical"

    lo_ids = [str(x) for x in (front.get("learning_outcomes") or []) if str(x).strip()]
    # Paper 3: LO optional; practical_topic is the primary taxonomy
    if not lo_ids and not is_practical:
        findings.append(Finding(qid, "empty_LO"))
    for lo in lo_ids:
        if lo not in allowed_los:
            findings.append(Finding(qid, "unknown_LO", lo))
    for code in front.get("syllabus_codes") or []:
        if str(code) not in allowed_codes:
            findings.append(Finding(qid, "unknown_code", str(code)))

    _PRACTICAL_TOPICS = {
        "Titrations",
        "Thermometric experiments",
        "Gravimetric experiments",
        "Gas volume experiments",
        "Rate experiments",
        "Qualitative analysis",
    }
    if is_practical:
        topic = str(front.get("practical_topic") or "").strip()
        if not topic:
            findings.append(Finding(qid, "empty_practical_topic"))
        elif topic not in _PRACTICAL_TOPICS:
            findings.append(Finding(qid, "unknown_practical_topic", topic))

    if FOOTER_RE.search(qbody):
        findings.append(Finding(qid, "footer_leak"))

    has_paper_embed = f"![[assets/{qid}-paper.png]]" in (body or "")
    if not has_paper_embed:
        full = md_path.read_text(encoding="utf-8")
        has_paper_embed = f"![[assets/{qid}-paper.png]]" in full

    # Body must not repeat A–D when the paper clip already shows them
    if has_paper_embed:
        stripped = _strip_duplicate_mcq_options(qbody, has_paper_clip=True)
        if stripped != qbody.strip():
            # qbody may include embed lines; compare option presence directly
            opt_lines = [
                ln.strip()
                for ln in qbody.splitlines()
                if MCQ_OPTION_LINE_RE.match(ln.strip())
                or OPTIONS_RUN_RE.search(ln.strip())
            ]
            letters = {ln[0] for ln in opt_lines if ln[:1] in "ABCD"}
            if {"A", "D"} <= letters and len(opt_lines) >= 3:
                findings.append(
                    Finding(
                        qid,
                        "duplicate_options_under_paper",
                        f"{len(opt_lines)} option lines under paper embed",
                    )
                )

    lines = [
        ln.strip()
        for ln in qbody.splitlines()
        if ln.strip() and not ln.strip().startswith("![[")
    ]
    for ln in lines:
        if ln.startswith("|") or "---" in ln:
            continue
        # Short element options ("A C" / "C P") are excluded inside _is_atom_salad_line;
        # mechanism OCR under A–D (e.g. "A C C H C C⁺ …") is still flagged.
        if _is_atom_salad_line(ln):
            findings.append(Finding(qid, "atom_salad", ln[:60]))
            break

    for ln in lines:
        if "|" in ln:
            continue
        if OPTIONS_RUN_RE.search(ln) and len(ln) > 40:
            findings.append(Finding(qid, "options_run_together", ln[:60]))
            break

    if lines and re.fullmatch(r"\d{1,2}", lines[-1]):
        # Trailing lone page number (not the question number alone as stem)
        if lines[-1] != qnum or len(lines) > 1:
            # Only flag when last line is a bare number and stem already present
            if any(re.match(rf"^{re.escape(qnum)}\b", ln) for ln in lines[:-1]) or (
                lines and re.match(rf"^{re.escape(qnum)}\b", lines[0] or "")
            ):
                findings.append(Finding(qid, "trailing_page_num", lines[-1]))

    if BAD_ARROW_RE.search(qbody):
        findings.append(Finding(qid, "bad_arrow"))
    if PUA_RE.search(qbody):
        chars = sorted({f"U+{ord(c):04X}" for c in PUA_RE.findall(qbody)})
        findings.append(Finding(qid, "pua_chars", ",".join(chars)))
    if CONTROL_RE.search(qbody):
        chars = sorted({f"U+{ord(c):04X}" for c in CONTROL_RE.findall(qbody)})
        findings.append(Finding(qid, "control_chars", ",".join(chars)))
    if GLUE_RE.search(qbody):
        findings.append(Finding(qid, "glued_words", GLUE_RE.search(qbody).group(0)))
    if BRACKET_CHARGE_RE.search(qbody):
        findings.append(
            Finding(qid, "broken_ion_charge", BRACKET_CHARGE_RE.search(qbody).group(0)[:40])
        )

    # Invented facility / % correct: non-null when ER merge left no numeric source
    fac = front.get("facility")
    pct = front.get("percent_correct")
    if fac is not None or pct is not None:
        # CIE qualitative ERs (e.g. 2021) have no facility numbers — any value is invented
        findings.append(
            Finding(qid, "invented_facility", f"facility={fac} percent_correct={pct}")
        )

    if questions_dir is not None:
        dual = Path(questions_dir) / f"{qid}.md"
        if not dual.exists():
            findings.append(Finding(qid, "missing_dual_write"))

    return findings


def _ascii_fold(text: str) -> str:
    """Fold common Latin/chemistry glyphs so preamble tokens match PDF text.

    CIE papers use Brønsted / en-dashes; ASCII-only tokenisation otherwise
    splits ``Brønsted`` into the non-matching fragment ``nsted``.
    """
    if not text:
        return ""
    repl = {
        "ø": "o",
        "Ø": "O",
        "æ": "ae",
        "Æ": "AE",
        "å": "a",
        "Å": "A",
        "–": "-",
        "—": "-",
        "′": "'",
        "’": "'",
    }
    out = text
    for a, b in repl.items():
        out = out.replace(a, b)
    return out


def _distinctive_words(text: str, *, stop: set[str], min_len: int = 4, limit: int = 6) -> list[str]:
    words = re.findall(rf"[A-Za-z]{{{min_len},}}", _ascii_fold(text or ""))
    out: list[str] = []
    seen: set[str] = set()
    for w in words:
        key = w.lower()
        if key in stop or key in seen:
            continue
        seen.add(key)
        out.append(w)
        if len(out) >= limit:
            break
    return out


def _word_hits(haystack: str, words: list[str]) -> int:
    folded = _ascii_fold(haystack or "")
    return sum(1 for w in words if re.search(rf"\b{re.escape(w)}\b", folded, re.I))


def _audit_structured_part_clips(
    qp_pdf: Path,
    part_notes: list[tuple[str, str]],
) -> list[Finding]:
    """Part-level QP clip gates: letter/roman/Q bleed + shared stem/preamble.

    ``part_notes`` is ``(qid, part_label)`` e.g. ``(..., "1(a)(iii)")``.
    """
    from chembank.figures import (
        _clip_contains_next_question,
        _paper_clip_text,
        question_paper_clips,
        structured_part_paper_clips,
    )
    from chembank.structured_parts import parse_part_id, split_main_question_into_parts

    import fitz

    findings: list[Finding] = []
    if not qp_pdf.exists() or not part_notes:
        return findings

    clips = structured_part_paper_clips(qp_pdf)
    main_clips = question_paper_clips(qp_pdf)
    doc = fitz.open(qp_pdf)
    try:
        parent_text = {
            qnum: _paper_clip_text(doc, clip) for qnum, clip in main_clips.items()
        }
        split_by_parent: dict[str, dict[str, str]] = {}
        for qnum, ptext in parent_text.items():
            split_by_parent[qnum] = {
                pid.label: body
                for pid, body in split_main_question_into_parts(qnum, ptext)
            }

        parsed: list[tuple[str, Any]] = []
        for qid, label in part_notes:
            pid = parse_part_id(label)
            if pid:
                parsed.append((qid, pid))

        by_parent: dict[str, list[Any]] = {}
        for _, pid in parsed:
            by_parent.setdefault(pid.parent, []).append(pid)

        for qid, pid in parsed:
            clip = clips.get(pid.label)
            if clip is None:
                findings.append(Finding(qid, "no_paper_clip_geometry", pid.label))
                continue
            text = _paper_clip_text(doc, clip)
            siblings = by_parent.get(pid.parent, [])

            if _clip_contains_next_question(text, pid.parent):
                findings.append(
                    Finding(
                        qid,
                        "next_question_bleed",
                        f"part clip includes q{int(pid.parent) + 1}",
                    )
                )

            letters = sorted({p.letter for p in siblings})
            if pid.letter in letters:
                for nl in letters[letters.index(pid.letter) + 1 :]:
                    if re.search(rf"(?:^|\n)\s*\({nl}\)(?:\s|\n|\(|$)", text):
                        findings.append(
                            Finding(
                                qid,
                                "next_letter_bleed",
                                f"part clip includes ({nl})",
                            )
                        )
                        break

            if pid.roman:
                same = sorted(
                    [p.roman for p in siblings if p.letter == pid.letter and p.roman],
                    key=lambda r: _ROMAN_ORDER.index(r)
                    if r in _ROMAN_ORDER
                    else 99,
                )
                if pid.roman in same:
                    for nr in same[same.index(pid.roman) + 1 :]:
                        if re.search(rf"(?:^|\n)\s*\({nr}\)(?:\s|\n|$)", text):
                            findings.append(
                                Finding(
                                    qid,
                                    "next_roman_bleed",
                                    f"part clip includes ({nr})",
                                )
                            )
                            break

            ptext = parent_text.get(pid.parent, "")
            stem_m = re.search(r"(?m)^\s*\(a\)", ptext)
            if stem_m:
                stem = ptext[: stem_m.start()].strip()
                words = _distinctive_words(stem, stop=_STEM_STOP, min_len=4, limit=6)
                if words:
                    need = 2 if len(words) >= 2 else 1
                    if _word_hits(text, words) < need:
                        findings.append(
                            Finding(
                                qid,
                                "missing_shared_stem",
                                f"need {need} of {words}",
                            )
                        )

            if pid.roman:
                split_parts = split_by_parent.get(pid.parent, {})
                bi_body = split_parts.get(f"{pid.parent}({pid.letter})(i)", "")
                pre_m = re.search(
                    rf"\({pid.letter}\)(.*?)(?=\(i\))", bi_body, re.S
                )
                if pre_m:
                    pre = pre_m.group(0)
                    pwords = _distinctive_words(
                        pre, stop=_PREAMBLE_STOP, min_len=5, limit=5
                    )
                    if len(pwords) >= 2 and _word_hits(text, pwords) < 2:
                        findings.append(
                            Finding(
                                qid,
                                "missing_letter_preamble",
                                f"need 2 of {pwords}",
                            )
                        )
    finally:
        doc.close()
    return findings


def _right_edge_drawings_clipped(page: Any, band: Any) -> float | None:
    """Return rightmost drawing x1 past ``band.x1``, else None.

    Detects CIE Paper 3 examiner mark grids / box strokes near the right edge
    that the crop truncates.
    """
    threshold = float(page.rect.x1) - 80.0
    overflow: float | None = None
    try:
        drawings = page.get_drawings()
    except Exception:
        return None
    for d in drawings:
        r = d.get("rect")
        if r is None:
            continue
        if r.y1 < band.y0 - 2 or r.y0 > band.y1 + 2:
            continue
        if float(r.x1) <= threshold:
            continue
        if float(r.x1) > float(band.x1) + 0.5:
            overflow = float(r.x1) if overflow is None else max(overflow, float(r.x1))
    return overflow


def _audit_paper_clips(
    qp_pdf: Path,
    question_ids: list[tuple[str, str]],
    *,
    require_mcq_options: bool = True,
) -> list[Finding]:
    """Validate paper-clip geometry/text from the QP PDF.

    ``question_ids`` is a list of ``(qid, qnum)``.
    Structured papers skip A–D / Section B combo-key gates.
    Practical papers must keep near-full width (right-edge mark grids).
    """
    from chembank.figures import (
        _clip_contains_next_question,
        _clip_has_option_letters_ad,
        _clip_has_option_letters_abcd,
        _clip_option_letters_found,
        _has_abcd_combo_options,
        _is_statement_combo_question,
        _paper_clip_matches_question,
        _paper_clip_text,
        _pdf_paper_kind,
        question_paper_clips,
    )

    import fitz

    findings: list[Finding] = []
    if not qp_pdf.exists():
        for qid, _ in question_ids:
            findings.append(Finding(qid, "no_paper_clip_geometry", f"missing pdf {qp_pdf}"))
        return findings

    is_practical = _pdf_paper_kind(qp_pdf) == "practical"
    clips = question_paper_clips(qp_pdf)
    doc = fitz.open(qp_pdf)
    try:
        for qid, qnum in question_ids:
            if qnum not in clips:
                findings.append(Finding(qid, "no_paper_clip_geometry"))
                continue
            text = _paper_clip_text(doc, clips[qnum])
            if not _paper_clip_matches_question(qnum, text):
                preview = " ".join(text.strip().splitlines()[:2])[:80]
                findings.append(Finding(qid, "foreign_or_wrong_stem", preview))
            if require_mcq_options:
                if not _clip_has_option_letters_ad(text):
                    findings.append(Finding(qid, "missing_A_or_D_in_clip"))
                elif not _clip_has_option_letters_abcd(text):
                    missing = sorted(
                        {"A", "B", "C", "D"} - _clip_option_letters_found(text)
                    )
                    findings.append(
                        Finding(
                            qid,
                            "missing_B_or_C_in_clip",
                            f"missing {','.join(missing)}",
                        )
                    )
                if _is_statement_combo_question(
                    text, qnum=qnum
                ) and not _has_abcd_combo_options(text):
                    findings.append(Finding(qid, "section_b_missing_combo_key"))
            if is_practical:
                for band in clips[qnum].bands:
                    page = doc[band.page - 1]
                    right_inset = float(page.rect.x1) - float(band.x1)
                    if right_inset > _PRACTICAL_MAX_RIGHT_INSET_PT:
                        findings.append(
                            Finding(
                                qid,
                                "clipped_right_mark_grid",
                                f"right_inset={right_inset:.1f}pt (max {_PRACTICAL_MAX_RIGHT_INSET_PT:.0f})",
                            )
                        )
                        break
                    overflow_x1 = _right_edge_drawings_clipped(page, band)
                    if overflow_x1 is not None:
                        findings.append(
                            Finding(
                                qid,
                                "clipped_right_mark_grid",
                                f"drawing x1={overflow_x1:.1f} beyond clip x1={band.x1:.1f}",
                            )
                        )
                        break
            if _clip_contains_next_question(text, qnum):
                findings.append(
                    Finding(qid, "next_question_bleed", f"paper clip OCR includes q{int(qnum)+1}")
                )
            try:
                n = int(qnum)
            except ValueError:
                n = 0
            if require_mcq_options and n <= 30 and re.search(
                r"Calcium is a stronger reducing", text
            ):
                findings.append(Finding(qid, "foreign_calcium_stmt"))
    finally:
        doc.close()
    return findings


def _thumb_hash(im: Any) -> str:
    t = im.convert("L").resize((48, 48))
    # Pillow 10+: get_flattened_data; older: getdata
    getter = getattr(t, "get_flattened_data", None)
    px = list(getter() if getter else t.getdata())
    avg = sum(px) / len(px) if px else 0
    return "".join("1" if p > avg else "0" for p in px)


def _compare_exported_paper_png(
    qp_pdf: Path,
    clip: Any,
    exported: Path,
    *,
    qid: str,
    tmp: Path,
) -> Finding | None:
    from chembank.figures import render_paper_clip

    if not exported.exists():
        return None
    fresh_path = tmp / f"{qid}.png"
    try:
        render_paper_clip(qp_pdf, clip, fresh_path)
        img_exp = Image.open(exported)
        img_fresh = Image.open(fresh_path)
    except Exception as exc:  # noqa: BLE001 — surface as audit finding
        return Finding(qid, "stale_or_wrong_paper_png", f"render/compare error: {exc}")
    dw = abs(img_fresh.size[0] - img_exp.size[0])
    dh = abs(img_fresh.size[1] - img_exp.size[1])
    dist = sum(a != b for a, b in zip(_thumb_hash(img_fresh), _thumb_hash(img_exp)))
    if dist > 100 or dh > 60 or dw > 60:
        return Finding(
            qid,
            "stale_or_wrong_paper_png",
            f"exported={img_exp.size} fresh={img_fresh.size} "
            f"hash_dist={dist} dwh=({dw},{dh})",
        )
    return None


def _audit_exported_pngs_match_clips(
    qp_pdf: Path,
    question_ids: list[tuple[str, str]],
    *,
    vault_dir: Path,
) -> list[Finding]:
    """Flag exported *-paper.png that diverge from a fresh render of current clips."""
    from chembank.figures import question_paper_clips

    findings: list[Finding] = []
    if not qp_pdf.exists():
        return findings
    clips = question_paper_clips(qp_pdf)
    assets = Path(vault_dir) / "assets"
    with tempfile.TemporaryDirectory(prefix="chembank-audit-") as td:
        tmp = Path(td)
        for qid, qnum in question_ids:
            clip = clips.get(qnum)
            if clip is None:
                continue
            finding = _compare_exported_paper_png(
                qp_pdf, clip, assets / f"{qid}-paper.png", qid=qid, tmp=tmp
            )
            if finding:
                findings.append(finding)
    return findings


def _audit_exported_structured_pngs(
    qp_pdf: Path,
    part_notes: list[tuple[str, str]],
    *,
    vault_dir: Path,
) -> list[Finding]:
    """Flag structured part *-paper.png that diverge from current part clips."""
    from chembank.figures import structured_part_paper_clips

    findings: list[Finding] = []
    if not qp_pdf.exists():
        return findings
    clips = structured_part_paper_clips(qp_pdf)
    assets = Path(vault_dir) / "assets"
    with tempfile.TemporaryDirectory(prefix="chembank-audit-part-") as td:
        tmp = Path(td)
        for qid, label in part_notes:
            clip = clips.get(label)
            if clip is None:
                continue
            finding = _compare_exported_paper_png(
                qp_pdf, clip, assets / f"{qid}-paper.png", qid=qid, tmp=tmp
            )
            if finding:
                findings.append(finding)
    return findings


def _is_mcq_export(front: dict[str, Any]) -> bool:
    """True when vault note should enforce Paper 1 A–D clip gates."""
    qtype = str(front.get("question_type") or "").lower()
    if qtype in {"structured", "extended", "practical", "data"}:
        return False
    if qtype == "mcq":
        return True
    paper = front.get("paper")
    if paper is not None:
        from chembank.registry import paper_kind

        return paper_kind(paper) == "mcq"
    return True


def audit_vault_questions(
    *,
    vault_dir: Path,
    md_paths: list[Path],
    questions_dir: Path | None = None,
    qp_by_prefix: dict[str, Path] | None = None,
    check_pdf: bool = True,
) -> AuditResult:
    """Audit exported question markdown (+ optional QP paper-clip checks)."""
    vault_dir = Path(vault_dir)
    questions_dir = Path(questions_dir) if questions_dir else None
    qp_by_prefix = qp_by_prefix or {}

    syllabus = load_syllabus()
    allowed_codes = flatten_codes(syllabus)
    allowed_los = flatten_learning_outcomes(syllabus)

    result = AuditResult()
    by_prefix: dict[str, list[tuple[str, str]]] = {}
    mcq_by_prefix: dict[str, bool] = {}
    structured_parts_by_prefix: dict[str, list[tuple[str, str]]] = {}

    for md_path in md_paths:
        front, _ = _front_and_body(md_path)
        # Thin parent indexes (q2.md linking parts) are not full question notes
        if front.get("type") == "structured-parent-index":
            continue
        result.checked += 1
        findings = _audit_markdown(
            md_path,
            vault_dir=vault_dir,
            questions_dir=questions_dir,
            allowed_codes=allowed_codes,
            allowed_los=allowed_los,
        )
        result.findings.extend(findings)
        qid = str(front.get("id") or md_path.stem)
        qnum = str(front.get("parent_question") or front.get("question") or "")
        # For part notes, geometry checks use the parent main-question number
        if front.get("part") and front.get("parent_question"):
            qnum = str(front.get("parent_question"))
        from chembank.structured_parts import question_id_prefix

        prefix = question_id_prefix(qid)
        if qnum and str(qnum).isdigit():
            by_prefix.setdefault(prefix, []).append((qid, str(qnum)))
            # Prefix is MCQ only if every note under it is MCQ
            is_mcq = _is_mcq_export(front)
            mcq_by_prefix[prefix] = mcq_by_prefix.get(prefix, True) and is_mcq
        # Collect part labels for structured bleed / shared-stem gates
        part_label = str(front.get("question") or "")
        if (
            not _is_mcq_export(front)
            and front.get("part")
            and re.match(r"^\d{1,2}\([a-z]\)", part_label, re.I)
        ):
            structured_parts_by_prefix.setdefault(prefix, []).append(
                (qid, part_label)
            )

    if check_pdf:
        for prefix, pairs in by_prefix.items():
            qp = qp_by_prefix.get(prefix)
            if qp is None:
                continue
            # Deduplicate parent qnums for structured part notes
            uniq_pairs: list[tuple[str, str]] = []
            seen_q: set[str] = set()
            for qid, qnum in pairs:
                key = qnum
                if key in seen_q and not mcq_by_prefix.get(prefix, True):
                    continue
                seen_q.add(key)
                uniq_pairs.append((qid, qnum))
            result.findings.extend(
                _audit_paper_clips(
                    Path(qp),
                    uniq_pairs if not mcq_by_prefix.get(prefix, True) else pairs,
                    require_mcq_options=mcq_by_prefix.get(prefix, True),
                )
            )
            # Stale-PNG check is MCQ-oriented (main-Q clips); skip for structured parts
            if mcq_by_prefix.get(prefix, True):
                result.findings.extend(
                    _audit_exported_pngs_match_clips(
                        Path(qp), pairs, vault_dir=vault_dir
                    )
                )
            else:
                part_notes = structured_parts_by_prefix.get(prefix, [])
                if part_notes:
                    result.findings.extend(
                        _audit_structured_part_clips(Path(qp), part_notes)
                    )
                    result.findings.extend(
                        _audit_exported_structured_pngs(
                            Path(qp), part_notes, vault_dir=vault_dir
                        )
                    )

    failed_ids = {f.question_id for f in result.findings}
    result.passed = result.checked - len(failed_ids)
    return result


def resolve_md_paths(
    vault_dir: Path,
    *,
    prefixes: list[str] | None = None,
    glob_pattern: str = "cie-9701-*.md",
) -> list[Path]:
    qdir = Path(vault_dir) / "questions"
    paths = sorted(qdir.glob(glob_pattern))
    if prefixes:
        paths = [
            p
            for p in paths
            if any(p.stem.startswith(pref) or pref in p.stem for pref in prefixes)
        ]
    return paths


def prefix_from_paper_meta(year: int, session: str, paper: int | str) -> str:
    """Build vault id prefix like cie-9701-2021-mj-p11."""
    sess = str(session).lower()
    return f"cie-9701-{year}-{sess}-p{paper}"


def audit_papers(
    *,
    vault_dir: Path = Path("vault"),
    questions_dir: Path | None = Path("questions"),
    paper_refs: list[Any] | None = None,
    check_pdf: bool = True,
) -> AuditResult:
    """Audit one or more papers (registry refs) or all vault exports."""
    from chembank.registry import list_registry_papers, parse_paper_ref, resolve_existing

    vault_dir = Path(vault_dir)
    qp_by_prefix: dict[str, Path] = {}
    prefixes: list[str] | None = None

    if paper_refs:
        prefixes = []
        refs = []
        for token in paper_refs:
            if hasattr(token, "qp"):
                refs.append(token)
            else:
                refs.append(parse_paper_ref(str(token)))
        for ref in refs:
            try:
                resolve_existing(ref, require_qp=False)
            except FileNotFoundError:
                pass
            pref = prefix_from_paper_meta(int(ref.year), str(ref.session), ref.paper)
            prefixes.append(pref)
            qp = Path(ref.qp) if ref.qp else None
            if qp and qp.exists():
                qp_by_prefix[pref] = qp
    else:
        # All exported notes; attach QP paths from registry when possible
        for ref in list_registry_papers():
            try:
                resolve_existing(ref, require_qp=False)
            except FileNotFoundError:
                pass
            pref = prefix_from_paper_meta(int(ref.year), str(ref.session), ref.paper)
            qp = Path(ref.qp) if ref.qp else None
            if qp and qp.exists():
                qp_by_prefix[pref] = qp

    md_paths = resolve_md_paths(vault_dir, prefixes=prefixes)
    if not md_paths:
        result = AuditResult()
        return result

    return audit_vault_questions(
        vault_dir=vault_dir,
        md_paths=md_paths,
        questions_dir=questions_dir,
        qp_by_prefix=qp_by_prefix,
        check_pdf=check_pdf,
    )


def format_audit_report(result: AuditResult) -> str:
    lines = [
        f"ChemBank audit: {result.passed} pass / {result.failed} fail "
        f"(checked {result.checked})",
    ]
    if result.findings:
        lines.append("Failures:")
        for f in sorted(result.findings, key=lambda x: (x.question_id, x.code)):
            lines.append(f"  FAIL {f}")
        lines.append("By code:")
        for code, n in sorted(result.by_code().items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  {code}: {n}")
    else:
        lines.append("All checks passed.")
    return "\n".join(lines)
