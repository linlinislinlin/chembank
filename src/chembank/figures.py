"""Detect and render question diagrams from CIE past-paper PDFs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FigureRegion:
    page: int  # 1-based
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class PaperClip:
    """Full-question screenshot: one or more page bands stitched top→bottom.

    Section B statement-combo questions often need a second band for the
    A–D key (``1, 2 and 3`` / ``1 and 2 only`` …), especially across a
    page break after statement 3.
    """

    bands: list[FigureRegion]

    def __post_init__(self) -> None:
        if not self.bands:
            raise ValueError("PaperClip requires at least one band")

    @property
    def primary(self) -> FigureRegion:
        return self.bands[0]

    # Compat: treat as the primary band for geometry checks / old callers.
    @property
    def page(self) -> int:
        return self.primary.page

    @property
    def x0(self) -> float:
        return self.primary.x0

    @property
    def y0(self) -> float:
        return self.primary.y0

    @property
    def x1(self) -> float:
        return self.primary.x1

    @property
    def y1(self) -> float:
        return self.primary.y1

    @property
    def width(self) -> float:
        return self.primary.width

    @property
    def height(self) -> float:
        return sum(b.height for b in self.bands)


def _is_delta_h_sized(w: float, h: float) -> bool:
    return w < 40 and h < 20


_AXIS_LABEL_RE = re.compile(
    r"^(?:[TxXyY][₀₁₂₃₄₅₆₇₈₉0-9]?|0|%|"
    r"transmittance.*|wavenumber.*|enthalpy|progress.*|"
    r"products?|reactants?|"
    r"\d{2,4}|100|50)$",
    re.IGNORECASE,
)

_ATOM_LABEL_RE = re.compile(
    r"^(?:[A-Z][a-z]?|OH|HO|NH|CN|CO|Br|Cl|I|F|H|O|N|C|S|P|"
    r"[₀₁₂₃₄₅₆₇₈₉0-9]+|[+=−–—-]+)$"
)


def find_figure_regions(page: Any, *, page_no: int) -> list[FigureRegion]:
    """Cluster non-trivial vector drawings into candidate figure bboxes."""
    import fitz

    strokes: list[Any] = []
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None:
            continue
        w, h = r.width, r.height
        if w <= 0 or h <= 0:
            continue
        if _is_delta_h_sized(w, h):
            continue
        area = w * h
        # Keep axis ticks / curve segments that are part of larger figures
        if area < 80 and w < 25 and h < 25:
            continue
        strokes.append(fitz.Rect(r))

    if not strokes:
        # Embedded images count as figures too
        for img in page.get_images(full=True):
            try:
                rects = page.get_image_rects(img[0])
            except Exception:  # noqa: BLE001
                continue
            for r in rects:
                if r.width >= 60 and r.height >= 40:
                    strokes.append(fitz.Rect(r))

    if not strokes:
        return []

    strokes = sorted(strokes, key=lambda r: (r.y0, r.x0))
    clusters: list[dict[str, Any]] = []
    pad = 36.0
    for r in strokes:
        placed = False
        for c in clusters:
            balloon = fitz.Rect(
                c["bbox"].x0 - pad,
                c["bbox"].y0 - pad,
                c["bbox"].x1 + pad,
                c["bbox"].y1 + pad,
            )
            if balloon.intersects(r):
                c["bbox"] |= r
                c["n"] += 1
                placed = True
                break
        if not placed:
            clusters.append({"bbox": fitz.Rect(r), "n": 1})

    # Merge same-row clusters separated by option gaps (A–B vs C–D structures)
    clusters = _merge_horizontal_row_clusters(clusters, y_tol=28.0, max_gap=90.0)

    try:
        words = page.get_text("words")  # x0,y0,x1,y1,word,...
    except Exception:  # noqa: BLE001
        words = []

    regions: list[FigureRegion] = []
    for c in clusters:
        b = fitz.Rect(c["bbox"])
        # Structure option rows can be shallow (~40pt) but wide
        if b.width < 70 or b.height < 32:
            continue
        # Ignore full-width header/footer bars (but keep wide spectra)
        if b.width > page.rect.width * 0.85 and b.height < 80:
            continue

        drawing_bbox = fitz.Rect(b)
        probe = FigureRegion(
            page=page_no, x0=b.x0, y0=b.y0, x1=b.x1, y1=b.y1
        )
        table_like = _is_data_table_region(page, probe)

        for w in words:
            x0, y0, x1, y1, word = w[0], w[1], w[2], w[3], str(w[4])
            label = word.strip()
            if not label or len(label) > 28:
                continue
            wr = fitz.Rect(x0, y0, x1, y1)
            near = (
                wr.x0 < b.x1 + 50
                and wr.x1 > b.x0 - 50
                and wr.y0 < b.y1 + 50
                and wr.y1 > b.y0 - 50
            )
            if not near:
                continue
            # Data tables: keep grid tight — do not absorb A–D option prose
            # below the ruled area (W/X/Y/Z particle labels match atom regex).
            if table_like and wr.y0 > drawing_bbox.y1 + 10:
                continue
            # Axis / spectrum / energy-profile labels
            if _AXIS_LABEL_RE.fullmatch(label) or re.fullmatch(
                r"[TxXyY0-9₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹%./−–-]+", label
            ):
                b |= wr
                continue
            # Atom / group labels on skeletal structures
            if _ATOM_LABEL_RE.fullmatch(label):
                b |= wr

        # padding for anti-alias crop
        b += (-8, -8, 8, 8)
        b &= page.rect
        regions.append(
            FigureRegion(page=page_no, x0=b.x0, y0=b.y0, x1=b.x1, y1=b.y1)
        )

    # Dedup heavy overlaps
    regions.sort(key=lambda r: -r.area)
    kept: list[FigureRegion] = []
    for r in regions:
        rr = (r.x0, r.y0, r.x1, r.y1)
        overlap = False
        for k in kept:
            ix0, iy0 = max(rr[0], k.x0), max(rr[1], k.y0)
            ix1, iy1 = min(rr[2], k.x1), min(rr[3], k.y1)
            if ix1 > ix0 and iy1 > iy0:
                inter = (ix1 - ix0) * (iy1 - iy0)
                if inter / min(r.area, k.area) > 0.55:
                    overlap = True
                    break
        if not overlap:
            kept.append(r)
    return sorted(kept, key=lambda r: (r.page, r.y0, r.x0))


def _merge_horizontal_row_clusters(
    clusters: list[dict[str, Any]],
    *,
    y_tol: float,
    max_gap: float,
) -> list[dict[str, Any]]:
    """Merge drawing clusters that sit on one horizontal options row."""
    if len(clusters) < 2:
        return clusters
    items = sorted(clusters, key=lambda c: (c["bbox"].y0, c["bbox"].x0))
    merged: list[dict[str, Any]] = []
    for c in items:
        if not merged:
            merged.append(c)
            continue
        prev = merged[-1]
        pb, cb = prev["bbox"], c["bbox"]
        y_overlap = min(pb.y1, cb.y1) - max(pb.y0, cb.y0)
        same_row = y_overlap > min(pb.height, cb.height) * 0.35 or abs(
            pb.y0 - cb.y0
        ) <= y_tol
        gap = cb.x0 - pb.x1
        if same_row and 0 <= gap <= max_gap:
            prev["bbox"] = pb | cb
            prev["n"] += c["n"]
        else:
            merged.append(c)
    return merged


# CIE Paper 1: real question numbers sit ~x=50; Section B statement
# numbers (1)/(2)/(3) sit indented ~x=71. Keep the cut between them.
_QUESTION_NUMBER_X_MAX = 62.0


def question_y_ranges_on_page(page: Any) -> dict[str, tuple[float, float]]:
    """Map question number -> (y0, y1) on a single page using leading question digits.

    Ignores indented Section B statement numbers (1/2/3) so they cannot
    truncate a question band or impersonate MCQ question numbers.
    """
    words = page.get_text("words")
    starts: list[tuple[str, float]] = []
    for w in words:
        x0, y0, x1, y1, word = w[0], w[1], w[2], w[3], str(w[4])
        if not re.fullmatch(r"\d{1,2}", word):
            continue
        # Question numbers sit at the far left margin (~50pt), not at the
        # indented statement column (~71pt) used in Q31–40.
        if x0 > _QUESTION_NUMBER_X_MAX:
            continue
        n = int(word)
        if 1 <= n <= 40:
            starts.append((word, y0))

    # Unique by number keeping topmost
    by_num: dict[str, float] = {}
    for num, y in sorted(starts, key=lambda t: t[1]):
        if num not in by_num:
            by_num[num] = y

    ordered = sorted(by_num.items(), key=lambda t: t[1])
    ranges: dict[str, tuple[float, float]] = {}
    for i, (num, y0) in enumerate(ordered):
        y1 = ordered[i + 1][1] if i + 1 < len(ordered) else page.rect.y1 - 40
        ranges[num] = (y0 - 2, y1 - 2)
    return ranges


_FOOTER_WORD_RE = re.compile(
    r"UCLES|Turn\s*over|9701/\d+|Permission|copyright|Acknowledgements|"
    r"BLANK|www\.cambridge",
    re.I,
)

# Start of the long copyright / blank-page trailer on the last QP page.
_COPYRIGHT_START_RE = re.compile(
    r"^(?:Permission|BLANK)$",
    re.I,
)


def _clip_text(page: Any, region: FigureRegion) -> str:
    """OCR-ish plain text inside a figure region (for validation)."""
    import fitz
    from chembank.symbols import normalize_chars

    clip = fitz.Rect(region.x0, region.y0, region.x1, region.y1) & page.rect
    plain = normalize_chars(page.get_text("text", clip=clip) or "")
    # CIE 2023+ Paper 1: left-margin bold qnums are often missing from
    # get_text("text"/"words") clips even though dict still has the span.
    # Prepend the leftmost digit-only span near the top of the band when needed.
    # Require a real qnum token ("40 What…"), not organic "2-methyl…".
    if re.match(r"^\s*\d{1,2}(?:\s|[A-Z]|$)", plain):
        return plain
    # Prefer a left-margin digit near the top; some 2023 layouts put the
    # qnum mid-band (after the stem), so fall back to any left-margin digit
    # inside the band.
    best: tuple[float, float, str] | None = None  # (y0, x0, text)
    fallback: tuple[float, float, str] | None = None
    top_y = region.y0 + 36
    for w in page.get_text("words"):
        x0, y0, _x1, _y1, word = w[0], w[1], w[2], w[3], str(w[4])
        if not re.fullmatch(r"\d{1,2}", word):
            continue
        if x0 > _QUESTION_NUMBER_X_MAX:
            continue
        if y0 < region.y0 - 2 or y0 > region.y1 + 2:
            continue
        cand = (y0, x0, word)
        if y0 <= top_y and (
            best is None or y0 < best[0] or (y0 == best[0] and x0 < best[1])
        ):
            best = cand
        if fallback is None or y0 < fallback[0] or (
            y0 == fallback[0] and x0 < fallback[1]
        ):
            fallback = cand
    if best is None:
        best = fallback
    if best is None:
        data = page.get_text("dict", clip=clip) or {}
        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = (span.get("text") or "").strip()
                    if not re.fullmatch(r"\d{1,2}", text):
                        continue
                    x0, y0 = float(span["bbox"][0]), float(span["bbox"][1])
                    if x0 > _QUESTION_NUMBER_X_MAX:
                        continue
                    if y0 < region.y0 - 2 or y0 > region.y1 + 2:
                        continue
                    if best is None or y0 < best[0] or (y0 == best[0] and x0 < best[1]):
                        best = (y0, x0, text)
    if best is None:
        return plain
    return f"{best[2]} {plain.lstrip()}"


def _paper_clip_text(doc: Any, clip: PaperClip) -> str:
    """Concatenated text from all bands (primary stem first)."""
    parts: list[str] = []
    for band in clip.bands:
        page = doc[band.page - 1]
        parts.append(_clip_text(page, band))
    return "\n".join(parts)


_STATEMENT_COMBO_RE = re.compile(
    r"(?:Which statements|which of the following statements|"
    r"In which (?:ions|molecules|compounds)|"
    # Note: do NOT match bare "Which reagents…" / "Which statement is correct?"
    # (ordinary MCQ). Statement-combo keys use "Which statements are correct".
    r"Which (?:oxides|reactions|changes|pairs|mixtures|alcohols)\b|"
    r"Which statements?\s+are\s+correct\b)",
    re.I,
)
# Prose statements: "1 The …" / "2 Calcium …"
_NUMBERED_STATEMENTS_RE = re.compile(
    r"(?:^|\n)\s*1\s+[A-Za-z][\s\S]*?(?:^|\n)\s*2\s+[A-Za-z][\s\S]*?"
    r"(?:^|\n)\s*3\s+[A-Za-z]",
    re.M,
)
# Bare 1/2/3 markers (structure / nuclide statements under Section B)
_BARE_STATEMENT_MARKERS_RE = re.compile(
    r"(?:^|\n)\s*1\s*(?:\n|$)[\s\S]*?(?:^|\n)\s*2\s*(?:\n|$)[\s\S]*?"
    r"(?:^|\n)\s*3\s*(?:\n|$)",
    re.M,
)
_ABCD_COMBO_KEY_RE = re.compile(
    r"(?:responses\s*A\s*to\s*D|"
    r"1[, ]\s*2\s+and\s*3|"
    r"2\s+and\s*3|"
    r"1\s+and\s*2\s+only|"
    r"1\s+and\s*3|"
    r"1\s+only|"
    r"2\s+only|"
    r"only\s+are\s+correct|"
    r"No other combination of statements)",
    re.I,
)
# Ordinary MCQ prose options (Section A) — not statement-combo
_PROSE_ABCD_OPTIONS_RE = re.compile(
    r"(?:^|\n)\s*A\s+\S[\s\S]*?(?:^|\n)\s*B\s+\S[\s\S]*?"
    r"(?:^|\n)\s*C\s+\S[\s\S]*?(?:^|\n)\s*D\s+\S",
    re.M,
)


def _is_statement_combo_question(text: str, *, qnum: str | None = None) -> bool:
    """True for Section B style MCQs with numbered statements 1–3."""
    if not text or not text.strip():
        return False
    # Ordinary A–D prose options ⇒ Section A
    if _PROSE_ABCD_OPTIONS_RE.search(text) and not _ABCD_COMBO_KEY_RE.search(text):
        return False

    n = int(qnum) if qnum and str(qnum).isdigit() else None
    has_prose_stmts = bool(_NUMBERED_STATEMENTS_RE.search(text))
    has_bare_stmts = bool(_BARE_STATEMENT_MARKERS_RE.search(text))
    has_stem = bool(_STATEMENT_COMBO_RE.search(text))

    # CIE Paper 1 Section B is Q31–40
    if n is not None and 31 <= n <= 40:
        return has_prose_stmts or has_bare_stmts or has_stem

    # Earlier questions: only when stem + prose statements 1–3 (not rate tables)
    if has_stem and has_prose_stmts:
        return True
    return False


def _has_abcd_combo_options(text: str) -> bool:
    """True when clip text includes the Section B A–D combination key."""
    return bool(text and _ABCD_COMBO_KEY_RE.search(text))


def _find_abcd_combo_key_region(
    page: Any,
    *,
    page_no: int,
    y_min: float = 0.0,
    y_max: float | None = None,
) -> FigureRegion | None:
    """Locate the Section B A–D combination key block on a page.

    Built from word geometry (``responses`` / ``1,``+``and`` / ``No other
    combination``), not ``_horizontal_abcd_labels`` — that helper rejects the
    key because the intro line also contains lone ``A``/``D`` glyphs.
    """
    if y_max is None:
        y_max = page.rect.y1

    words = page.get_text("words")
    # Clusters of "responses" intro lines in the window
    response_ys: list[float] = []
    combo_row_ys: list[float] = []
    for w in words:
        wx0, wy0, wx1, wy1, word = w[0], w[1], w[2], w[3], str(w[4])
        if wy1 < y_min - 2 or wy0 > y_max + 2:
            continue
        if re.fullmatch(r"responses?", word, re.I):
            response_ys.append(wy0)
        elif word in {"1,", "1"}:
            nearby = [
                str(o[4]).lower()
                for o in words
                if abs(o[1] - wy0) < 8 and 0 <= (o[0] - wx0) < 80
            ]
            # "1, 2 and 3" starts the combination row
            if "2" in nearby and "and" in nearby:
                combo_row_ys.append(wy0)

    if not response_ys and not combo_row_ys:
        return None

    # Prefer a responses-line that has a combo row shortly below it
    top: float | None = None
    if response_ys:
        for ry in sorted(response_ys):
            if any(ry < cy <= ry + 70 for cy in combo_row_ys) or not combo_row_ys:
                top = ry - 2.0
                break
    if top is None and combo_row_ys:
        top = min(combo_row_ys) - 36.0

    assert top is not None
    # Bottom: through "No other combination of statements…"
    bottom = top + 50.0
    for w in words:
        wx0, wy0, wx1, wy1, word = w[0], w[1], w[2], w[3], str(w[4])
        if wy0 < top - 2 or wy0 > min(y_max, top + 160):
            continue
        low = word.lower().rstrip(".")
        if low in {
            "correct",
            "response",
            "combination",
            "statements",
            "used",
            "as",
            "a",
            "other",
            "no",
            "of",
            "is",
        }:
            # Keep extending while we're in the key / trailer sentence
            if wy0 <= top + 140:
                bottom = max(bottom, wy1)

    x0 = 40.0
    x1 = page.rect.x1 - 32.0
    region = FigureRegion(
        page=page_no,
        x0=x0,
        y0=max(float(y_min), max(0.0, top)),
        x1=x1,
        y1=min(float(y_max), bottom + 8.0),
    )
    if region.height < 40:
        return None
    text = _clip_text(page, region)
    if not _has_abcd_combo_options(text):
        return None
    # Must include option letters A and D (the combination grid)
    if not re.search(r"(?:^|\s)A(?:\s|$)", text) or not re.search(
        r"(?:^|\s)D(?:\s|$)", text
    ):
        return None
    return region


def _paper_clip_matches_question(qnum: str, text: str) -> bool:
    """Reject crops whose leading stem is a different question / statement.

    Paper clips must start with this question number. Also reject when the
    crop is clearly a Section B statement line (e.g. bare ``3 Calcium…``)
    that slipped past geometry filters.
    """
    if not text or not text.strip():
        return False
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    # Skip copyright / ornament prefixes; prefer the line that opens with qnum.
    stem_i: int | None = None
    for i, ln in enumerate(lines):
        first = ln.split()[0] if ln.split() else ""
        if _COPYRIGHT_START_RE.match(first):
            continue
        if re.match(r"^(?:Permission|To avoid|Cambridge Assessment)\b", ln, re.I):
            continue
        if re.match(rf"^{re.escape(qnum)}(?:\s|[A-Z]|\b)", ln):
            stem_i = i
            break
        # Symbol-only / charge junk before the stem (–, x+y+, (II)(II), …)
        if not re.search(r"[A-Za-z]{3,}", ln):
            continue
        if stem_i is None:
            stem_i = i  # first prose line; may still fail qnum check below
        break
    if stem_i is None:
        return False
    stripped = "\n".join(lines[stem_i:])
    # Must begin with this question number as a token
    if not re.match(rf"^{re.escape(qnum)}(?:\s|[A-Z]|\b)", stripped):
        return False
    # Single-digit qnums: reject if this looks like an indented statement
    # crop that only contains "N <statement>" without MCQ options / stem ask.
    # Real Q1–Q9 always have A–D options or a multi-line stem; a lone short
    # statement line from Q36 is foreign content for early questions.
    first_line = stripped.splitlines()[0].strip()
    if re.fullmatch(
        rf"{re.escape(qnum)}\s+.{{10,120}}",
        first_line,
    ) and not re.search(r"\b[A-D]\b", stripped):
        # Allow multi-line stems that introduce options later, or Section B
        # questions (31–40) whose body is numbered statements 1/2/3.
        if int(qnum) <= 30 and len(stripped.splitlines()) <= 2:
            # Heuristic: foreign statement crops are short (1–2 lines) and
            # lack A–D; real early MCQs always include A–D in the band.
            return False
    return True


def _content_bottom_y(
    page: Any, *, y0: float, y1: float, x0: float, x1: float
) -> float:
    """Lowest text/drawing y within the question band (trim trailing whitespace)."""
    import fitz

    bottom = y0 + 36.0
    # Cap above copyright / blank-page trailers when present in this band.
    trailer_y: float | None = None
    for w in page.get_text("words"):
        wx0, wy0, wx1, wy1, word = w[0], w[1], w[2], w[3], str(w[4])
        if wy1 < y0 - 2 or wy0 > y1 + 2:
            continue
        if wx1 < x0 or wx0 > x1:
            continue
        if _COPYRIGHT_START_RE.match(word):
            trailer_y = wy0 if trailer_y is None else min(trailer_y, wy0)
    hard_cap = trailer_y - 4.0 if trailer_y is not None else y1

    for w in page.get_text("words"):
        wx0, wy0, wx1, wy1, word = w[0], w[1], w[2], w[3], str(w[4])
        if wy1 < y0 - 2 or wy0 > hard_cap:
            continue
        if wx1 < x0 or wx0 > x1:
            continue
        # Skip page footers / running headers
        if _FOOTER_WORD_RE.search(word):
            continue
        if wy0 > page.rect.y1 - 50:
            continue
        bottom = max(bottom, wy1)
    # Thin full-width rules often separate the last question from copyright.
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None or r.width <= 0 or r.height <= 0:
            continue
        if r.y1 < y0 - 2 or r.y0 > hard_cap:
            continue
        if r.x1 < x0 or r.x0 > x1:
            continue
        if r.y0 > page.rect.y1 - 50:
            continue
        # Ignore full-page rules / underlines spanning the margin.
        # Only treat a near-bottom separator as a copyright trailer cut
        # (table gridlines mid-question must not truncate the clip).
        if r.height < 1.5 and r.width > 200:
            if trailer_y is not None and r.y0 <= trailer_y and r.y0 > y0 + 40:
                hard_cap = min(hard_cap, r.y0 - 2.0)
            continue
        bottom = max(bottom, r.y1)
    return min(hard_cap, bottom + 10.0)


def _horizontal_abcd_labels(
    page: Any, y0: float, y1: float
) -> dict[str, tuple[float, float, float, float]] | None:
    """Return A–D label bboxes if they form a horizontal options row."""
    words = page.get_text("words")
    cands: dict[str, list[tuple[float, float, float, float]]] = {
        "A": [],
        "B": [],
        "C": [],
        "D": [],
    }
    for w in words:
        label = str(w[4]).strip()
        if label not in cands:
            continue
        if not (y0 - 5 <= w[1] <= y1 + 5):
            continue
        # Option letters are short glyphs near structures / option text
        if w[2] - w[0] > 20:
            continue
        cands[label].append((w[0], w[1], w[2], w[3]))

    picked: dict[str, tuple[float, float, float, float]] = {}
    for letter in "ABCD":
        if not cands[letter]:
            return None
        # Prefer the topmost row of option letters
        picked[letter] = min(cands[letter], key=lambda t: (t[1], t[0]))

    ys = [picked[L][1] for L in "ABCD"]
    xs = [picked[L][0] for L in "ABCD"]
    if max(ys) - min(ys) > 18:
        return None  # vertical option list, not a structure row
    if xs != sorted(xs):
        return None
    # Must span a meaningful width (crowded horizontal options / structures)
    if picked["D"][2] - picked["A"][0] < 180:
        return None
    return picked


def _mcq_options_block(
    page: Any,
    *,
    page_no: int,
    y0: float,
    y1: float,
    labels: dict[str, tuple[float, float, float, float]],
) -> FigureRegion | None:
    """Build a bbox covering A–D labels + structures/drawings under them.

    Prose-only horizontal option rows (``A W and Y  B W and Z …``) return
    ``None`` — those belong in the paper clip, not a redundant Diagram crop.
    The block is always clamped to the question band ``y1`` so it cannot
    bleed into the next question.
    """
    import fitz

    lab_y0 = min(v[1] for v in labels.values())
    lab_y1 = max(v[3] for v in labels.values())
    x0 = min(v[0] for v in labels.values()) - 12
    x1 = max(v[2] for v in labels.values()) + 12

    # Structures usually sit just below the letters — never past next question
    band_top = max(y0, lab_y0 - 6)
    band_bot = min(y1 - 2.0, lab_y1 + 120)

    union = fitz.Rect(x0, lab_y0, x1, lab_y1)
    structure_area = 0.0
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None or r.width <= 0 or r.height <= 0:
            continue
        if r.y1 < band_top - 5 or r.y0 > band_bot + 5:
            continue
        # Ignore tiny noise / hairline table rules far from structures
        if r.width * r.height < 40 and r.height < 8:
            continue
        if r.height < 1.5 or r.width < 1.5:
            continue
        union |= fitz.Rect(r)
        structure_area += float(r.width * r.height)

    # Prose MCQ options have letters + text only — no skeletal drawings.
    # Skip those; paper clip already shows A–D.
    if structure_area < 600:
        return None

    # Include atom-label words inside the options band
    for w in page.get_text("words"):
        label = str(w[4]).strip()
        if not label or label in "ABCD":
            continue
        wr = fitz.Rect(w[0], w[1], w[2], w[3])
        if wr.y1 < band_top - 5 or wr.y0 > band_bot + 5:
            continue
        if wr.x1 < union.x0 - 40 or wr.x0 > union.x1 + 40:
            continue
        if _ATOM_LABEL_RE.fullmatch(label) or len(label) <= 3:
            union |= wr

    # Expand to full A–D span even if rightmost drawings were sparse
    union.x0 = min(union.x0, labels["A"][0] - 16)
    union.x1 = max(union.x1, labels["D"][2] + 40)
    union.y0 = min(union.y0, lab_y0 - 4)
    union += (-6, -4, 10, 8)
    union &= page.rect
    # Hard clamp: never enter the next question's y-band
    union.y1 = min(union.y1, y1 - 2.0)
    union.y0 = max(union.y0, y0 - 2.0)

    # Reject if we clearly clipped an option letter or the block is too narrow
    if union.x0 > labels["A"][0] - 2:
        union.x0 = max(page.rect.x0 + 35, labels["A"][0] - 16)
    if union.x1 < labels["D"][2] + 8:
        union.x1 = min(page.rect.x1 - 30, labels["D"][2] + 48)
    if union.width < 200 or union.height < 28:
        return None
    return FigureRegion(
        page=page_no, x0=union.x0, y0=union.y0, x1=union.x1, y1=union.y1
    )


def _is_data_table_region(page: Any, region: FigureRegion) -> bool:
    """True when a figure region is mostly a ruled data table (not a spectrum/structure)."""
    h_rules = 0
    v_rules = 0
    other_area = 0.0
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None or r.width <= 0 or r.height <= 0:
            continue
        if r.y1 < region.y0 - 2 or r.y0 > region.y1 + 2:
            continue
        if r.x1 < region.x0 - 2 or r.x0 > region.x1 + 2:
            continue
        if r.height < 1.8 and r.width > 40:
            h_rules += 1
        elif r.width < 1.8 and r.height > 18:
            v_rules += 1
        else:
            other_area += float(r.width * r.height)
    # Tables: several H+V rules and little non-rule ink (unlike spectra/structures)
    return h_rules >= 3 and v_rules >= 2 and other_area < 2500


def _clip_contains_next_question(text: str, qnum: str) -> bool:
    """True if OCR text includes a later question opener (bleed into next item).

    Requires a real stem word after the number (``2 Where…`` / ``3 Calcium…``),
    not a bare option letter or table cell (``3`` then ``B`` in a Group/Period
    options grid). PDF extracts often insert C0 controls between the number
    and the stem (``2\\t\\x07Carbon``), so those are skipped.
    """
    if not text or not qnum.isdigit():
        return False
    n = int(qnum)
    nxt = n + 1
    if nxt > 40:
        return False
    # Next-question opener: "<n> <CapitalizedWord…>" — at least 3 letters so
    # single option letters (A–D) and short table cells do not false-trigger.
    return bool(
        re.search(
            rf"(?:^|\n)\s*{nxt}(?:\s|[\x00-\x1f\ufeff])+[A-Z][A-Za-z]{{2,}}\b",
            text,
        )
    )


def _attach_abcd_combo_for_statements(
    doc: Any,
    *,
    primary: FigureRegion,
    primary_text: str,
    page_index: int,
    qnum: str,
    page_qranges: dict[str, tuple[float, float]] | None = None,
) -> list[FigureRegion]:
    """Ensure statement-combo clips include the A–D combination key.

    Bands are always ``[stem+statements, A–D key]`` so the options grid sits
    at the bottom of the stitched ``*-paper.png`` (CIE often prints the key
    once above Q31–40; we still stitch it under the question).

    Lookup order for the key band:
    1. Already inside the primary band → nothing to add
    2. Same page after statements
    3. Same page above the stem (Section B header)
    4. Next page before the first question (page-break reprint — e.g. Q35)
    5. Previous pages (walk back up to 3)
    """
    bands = [primary]
    if not _is_statement_combo_question(primary_text, qnum=qnum):
        return bands
    if _has_abcd_combo_options(primary_text):
        return bands

    page = doc[page_index]
    page_no = page_index + 1
    key: FigureRegion | None = None
    # Last question on the page (even with trailing whitespace) may continue
    # with a reprinted A–D key on the next page.
    last_on_page = False
    if page_qranges:
        later = [
            qy0
            for q, (qy0, _) in page_qranges.items()
            if q != qnum and qy0 > primary.y0 + 2
        ]
        last_on_page = not later
    near_page_end = primary.y1 >= page.rect.y1 - 90 or last_on_page

    # 2) Same page below the stem band
    key = _find_abcd_combo_key_region(
        page,
        page_no=page_no,
        y_min=primary.y1 - 4,
        y_max=page.rect.y1 - 40,
    )
    if key is not None and key.y0 < primary.y1 - 20:
        key = None

    # 3) Same page above stem (Section B header) — preferred over a later page
    if key is None:
        key = _find_abcd_combo_key_region(
            page,
            page_no=page_no,
            y_min=0.0,
            y_max=primary.y0 - 2,
        )

    # 4) Next-page continuation only when this question runs to the page end
    #    (e.g. Q35 statements on p13, key reprinted atop p14).
    if key is None and near_page_end and page_index + 1 < len(doc):
        nxt = doc[page_index + 1]
        nxt_ranges = question_y_ranges_on_page(nxt)
        first_q_y = (
            min(y0 for y0, _ in nxt_ranges.values()) if nxt_ranges else nxt.rect.y1
        )
        key = _find_abcd_combo_key_region(
            nxt,
            page_no=page_index + 2,
            y_min=0.0,
            y_max=first_q_y - 2,
        )

    # 5) Walk back previous pages
    if key is None:
        for back in range(page_index - 1, max(-1, page_index - 3), -1):
            if back < 0:
                break
            prev = doc[back]
            key = _find_abcd_combo_key_region(
                prev,
                page_no=back + 1,
                y_min=0.0,
                y_max=prev.rect.y1,
            )
            if key is not None:
                break

    if key is not None:
        bands.append(key)
    return bands


def _clip_has_option_letters_ad(text: str) -> bool:
    """MCQ paper clips must expose option letters A and D."""
    if not text:
        return False
    # Allow "A →" / "A→" / lone "A" (2023 papers often put a reaction arrow
    # in the next span after the option letter).
    has_a = bool(re.search(r"(?:^|\s)A(?:\s|$|[→\-=])", text, re.M))
    has_d = bool(re.search(r"(?:^|\s)D(?:\s|$|[→\-=])", text, re.M))
    return has_a and has_d


def _clip_option_letters_found(text: str) -> set[str]:
    """Collect standalone MCQ option letters A–D from clip OCR/PDF text."""
    found: set[str] = set()
    if not text:
        return found
    # Vertical / table rows: "A pyramidal", "B 1 and 2 only", bare "A"
    for m in re.finditer(r"(?m)^\s*([A-D])(?:\s|$|[.)]|→)", text):
        found.add(m.group(1))
    # Horizontal row: "A  Ar+   B  B   C  F   D  Se-" (D may be last token)
    for m in re.finditer(
        r"(?:^|\s)([A-D])(?:\s+)(?=[A-Za-z0-9\[\(\d]|1,|2\s|3\s)|"
        r"(?:^|\s)([A-D])(?:\s*$)",
        text,
        re.M,
    ):
        found.add(m.group(1) or m.group(2))
    # Compact structure grids: "A B C D" on one line
    if re.search(r"(?:^|\s)A\s+B\s+C\s+D(?:\s|$)", text, re.M):
        found.update("ABCD")
    # Section B intro / key: "responses A to D" plus lettered columns
    if re.search(r"responses\s+A\s+to\s+D", text, re.I):
        found.update("ABCD")
    return found


def _clip_has_option_letters_abcd(text: str) -> bool:
    """MCQ paper clips must expose all four option letters A–D."""
    if not _clip_has_option_letters_ad(text):
        return False
    return {"A", "B", "C", "D"} <= _clip_option_letters_found(text)


def _pdf_requires_mcq_options(pdf_path: Path) -> bool:
    """True for Paper 1x MCQ; False for Paper 2/3/4/5x (structured/practical)."""
    m = re.search(r"qp_(\d+)", Path(pdf_path).name, re.I)
    if m:
        from chembank.registry import paper_kind

        return paper_kind(int(m.group(1))) == "mcq"
    return True


# Right inset (pt) from page edge for paper-clip x1.
# Paper 3 examiner mark grids (I–IV boxes) sit ~30pt from the page edge;
# the default 32pt inset clips their right border.
_PAPER_CLIP_RIGHT_INSET_DEFAULT = 32.0
_PAPER_CLIP_RIGHT_INSET_PRACTICAL = 8.0
_PAPER_CLIP_LEFT_X0 = 40.0


def _pdf_paper_kind(pdf_path: Path) -> str | None:
    m = re.search(r"qp_(\d+)", Path(pdf_path).name, re.I)
    if not m:
        return None
    from chembank.registry import paper_kind

    return paper_kind(int(m.group(1)))


def _paper_clip_x_bounds(page: Any, pdf_path: Path) -> tuple[float, float]:
    """Horizontal crop bounds for a full-question paper clip.

    Practical papers keep nearly full page width so CIE right-edge mark
    grids (Roman I–IV boxes + ``[n]``) are not clipped.
    """
    right_inset = _PAPER_CLIP_RIGHT_INSET_DEFAULT
    if _pdf_paper_kind(pdf_path) == "practical":
        right_inset = _PAPER_CLIP_RIGHT_INSET_PRACTICAL
    x0 = _PAPER_CLIP_LEFT_X0
    x1 = float(page.rect.x1) - right_inset
    return x0, x1


def _qualitative_section_y(page: Any) -> float | None:
    """Y0 of Paper 3 left-margin 'Qualitative analysis' section header."""
    try:
        hits = page.search_for("Qualitative analysis")
    except Exception:
        hits = []
    # Left-margin section title only (ignore mid-sentence "Qualitative Analysis Notes")
    hits = [r for r in hits if r.x0 < 80 and r.y0 < 200]
    if not hits:
        return None
    return float(min(r.y0 for r in hits))


def _extend_structured_paper_bands(
    doc: Any,
    *,
    primary: FigureRegion,
    qnum: str,
    page_index: int,
) -> list[FigureRegion]:
    """Append continuation-page bands until the next main question starts."""
    bands: list[FigureRegion] = [primary]
    q_i = int(qnum)
    x0 = primary.x0
    x1 = primary.x1
    for j in range(page_index + 1, len(doc)):
        page = doc[j]
        qranges = question_y_ranges_on_page(page)
        later = sorted(
            ((q, y0) for q, (y0, _y1) in qranges.items() if int(q) > q_i),
            key=lambda t: t[1],
        )
        # Continuation starts below running header / printed page number
        y0 = 48.0
        # Paper 3: Qual section preamble is the start of the next block (usually Q3)
        qa_y = _qualitative_section_y(page)
        if qa_y is not None and (not later or qa_y < later[0][1]):
            # Previous question already finished on an earlier page — do not
            # swallow the Qual preamble into Q1/Q2.
            if qa_y <= y0 + 24:
                break
            end_y = qa_y - 2.0
            if end_y > y0 + 30:
                content_y1 = _content_bottom_y(
                    page, y0=y0, y1=end_y, x0=x0, x1=x1
                )
                clip_y1 = min(end_y, max(y0 + 36, content_y1))
                if clip_y1 > y0 + 30:
                    bands.append(
                        FigureRegion(
                            page=j + 1, x0=x0, y0=y0, x1=x1, y1=clip_y1
                        )
                    )
            break
        if later:
            end_y = later[0][1] - 2.0
            if end_y <= y0 + 40:
                break
            content_y1 = _content_bottom_y(
                page, y0=y0, y1=end_y, x0=x0, x1=x1
            )
            clip_y1 = min(end_y, max(y0 + 36, content_y1))
            if clip_y1 > y0 + 30:
                bands.append(
                    FigureRegion(
                        page=j + 1, x0=x0, y0=y0, x1=x1, y1=clip_y1
                    )
                )
            break
        # Whole page is still this question
        if any(int(q) == q_i for q in qranges):
            # Fresh start of same number should not happen; stop to be safe
            break
        # Stop on blank / copyright-only trailing pages
        page_text = (page.get_text("text") or "").strip()
        if re.search(r"^\s*BLANK PAGE\s*$", page_text, re.I | re.M) and not re.search(
            r"^\s*\([a-z]\)", page_text, re.I | re.M
        ):
            break
        content_y1 = _content_bottom_y(
            page, y0=y0, y1=page.rect.y1 - 40, x0=x0, x1=x1
        )
        clip_y1 = max(y0 + 36, content_y1)
        if clip_y1 <= y0 + 30:
            break
        bands.append(
            FigureRegion(page=j + 1, x0=x0, y0=y0, x1=x1, y1=clip_y1)
        )
    return bands


def question_paper_clips(pdf_path: Path) -> dict[str, PaperClip]:
    """Full question-band clips (stem + options + diagrams) keyed by question number.

    First valid occurrence wins: later pages must not overwrite Q1–Q9 with
    Section B statement digits that share the same numeral.

    Statement-combination (Section B) clips **must** include the A–D key
    (``1, 2 and 3`` / ``1 and 2 only`` …). Crops that end at the statement
    list without options are rejected or extended across the page break.

    Structured papers (Paper 2/3/4/5x) skip the A–D option-letter gate and
    stitch continuation pages until the next main question.
    """
    import fitz

    pdf_path = Path(pdf_path)
    require_mcq = _pdf_requires_mcq_options(pdf_path)
    doc = fitz.open(pdf_path)
    out: dict[str, PaperClip] = {}
    try:
        for i, page in enumerate(doc):
            qranges = question_y_ranges_on_page(page)
            for q, (y0, y1) in qranges.items():
                if q in out:
                    continue  # keep first (earlier-page) match
                # Side margins: keep question number + full option / mark-grid width
                x0, x1 = _paper_clip_x_bounds(page, pdf_path)
                content_y1 = _content_bottom_y(
                    page, y0=y0, y1=y1 - 4, x0=x0, x1=x1
                )
                clip_y1 = max(y0 + 36, content_y1)
                region = FigureRegion(
                    page=i + 1, x0=x0, y0=max(0, y0 - 2), x1=x1, y1=clip_y1
                )
                text = _clip_text(page, region)
                if not _paper_clip_matches_question(q, text):
                    continue
                # Reject bands that already include the next question opener
                if _clip_contains_next_question(text, q):
                    continue

                if require_mcq:
                    bands = _attach_abcd_combo_for_statements(
                        doc,
                        primary=region,
                        primary_text=text,
                        page_index=i,
                        qnum=q,
                        page_qranges=qranges,
                    )
                else:
                    bands = _extend_structured_paper_bands(
                        doc, primary=region, qnum=q, page_index=i
                    )
                clip = PaperClip(bands=bands)
                combined = _paper_clip_text(doc, clip)
                if require_mcq:
                    # Hard reject: statement-combo must include A–D combination key
                    if _is_statement_combo_question(text, qnum=q) and not (
                        _has_abcd_combo_options(combined)
                        and _clip_has_option_letters_ad(combined)
                    ):
                        continue
                    # Paper 1 MCQ: every clip must expose option letters A–D
                    if not _clip_has_option_letters_abcd(combined):
                        continue
                out[q] = clip
    finally:
        doc.close()
    return out


def assign_figures_to_questions(
    pdf_path: Path,
) -> dict[str, list[FigureRegion]]:
    """Return {question_number: [figures]} for a full QP PDF."""
    import fitz

    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    assigned: dict[str, list[FigureRegion]] = {}
    try:
        for i, page in enumerate(doc, start=1):
            figs = find_figure_regions(page, page_no=i)
            qranges = question_y_ranges_on_page(page)
            if not qranges:
                continue

            # Prefer dedicated A–D structure/options blocks when present
            option_blocks: dict[str, FigureRegion] = {}
            for q, (y0, y1) in qranges.items():
                labels = _horizontal_abcd_labels(page, y0, y1)
                if not labels:
                    continue
                block = _mcq_options_block(
                    page, page_no=i, y0=y0, y1=y1, labels=labels
                )
                if block is not None:
                    option_blocks[q] = block

            for fig in figs:
                fmid = (fig.y0 + fig.y1) / 2
                best_q = None
                best_score = -1.0
                for q, (y0, y1) in qranges.items():
                    if fig.y1 < y0 - 10 or fig.y0 > y1 + 10:
                        continue
                    if y0 <= fmid <= y1:
                        score = 2.0 + min(fig.y1, y1) - max(fig.y0, y0)
                    else:
                        score = min(fig.y1, y1) - max(fig.y0, y0)
                    if score > best_score:
                        best_score = score
                        best_q = q
                if best_q and best_score > 0:
                    # Drop fragments swallowed by a fuller options block
                    block = option_blocks.get(best_q)
                    if block is not None:
                        ix0 = max(fig.x0, block.x0)
                        iy0 = max(fig.y0, block.y0)
                        ix1 = min(fig.x1, block.x1)
                        iy1 = min(fig.y1, block.y1)
                        if ix1 > ix0 and iy1 > iy0:
                            inter = (ix1 - ix0) * (iy1 - iy0)
                            if inter / max(fig.area, 1) > 0.45:
                                continue
                    # Data tables live inside the paper clip — skip focus crop
                    if _is_data_table_region(page, fig):
                        continue
                    # Clamp to question band (no next-question bleed)
                    qy0, qy1 = qranges[best_q]
                    clamped = FigureRegion(
                        page=fig.page,
                        x0=fig.x0,
                        y0=max(fig.y0, qy0 - 2),
                        x1=fig.x1,
                        y1=min(fig.y1, qy1 - 2),
                    )
                    if clamped.height < 28 or clamped.width < 60:
                        continue
                    assigned.setdefault(best_q, []).append(clamped)

            for q, block in option_blocks.items():
                assigned.setdefault(q, []).append(block)
                # Sort: spectrum/diagram above options
                assigned[q].sort(key=lambda r: (r.y0, r.x0))
    finally:
        doc.close()
    return assigned


def render_figure(
    pdf_path: Path,
    fig: FigureRegion | PaperClip,
    out_path: Path,
    *,
    zoom: float = 2.5,
) -> Path:
    """Render a single region, or stitch PaperClip bands top→bottom."""
    import fitz

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(fig, PaperClip):
        return render_paper_clip(pdf_path, fig, out_path, zoom=zoom)

    doc = fitz.open(pdf_path)
    try:
        page = doc[fig.page - 1]
        clip = fitz.Rect(fig.x0, fig.y0, fig.x1, fig.y1) & page.rect
        pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pix.save(out_path)
    finally:
        doc.close()
    return out_path


def render_paper_clip(
    pdf_path: Path,
    clip: PaperClip,
    out_path: Path,
    *,
    zoom: float = 2.5,
) -> Path:
    """Render one or more bands and stitch them into a single PNG."""
    import fitz
    from PIL import Image

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    try:
        images: list[Image.Image] = []
        for band in clip.bands:
            page = doc[band.page - 1]
            rect = fitz.Rect(band.x0, band.y0, band.x1, band.y1) & page.rect
            pix = page.get_pixmap(
                clip=rect, matrix=fitz.Matrix(zoom, zoom), alpha=False
            )
            images.append(pix.pil_image().convert("RGB"))
        if len(images) == 1:
            images[0].save(out_path)
            return out_path

        gap = 8
        width = max(im.width for im in images)
        height = sum(im.height for im in images) + gap * (len(images) - 1)
        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        y = 0
        for i, im in enumerate(images):
            x = max(0, (width - im.width) // 2)
            canvas.paste(im, (x, y))
            y += im.height + (gap if i < len(images) - 1 else 0)
        canvas.save(out_path)
    finally:
        doc.close()
    return out_path


def mark_scheme_main_clips(ms_pdf: Path) -> dict[str, PaperClip]:
    """Roll part-level MS clips up to main-question PaperClips (Paper 3 grain)."""
    from chembank.structured_parts import parse_part_id

    part_clips = mark_scheme_part_clips(ms_pdf)
    by_parent: dict[str, list[FigureRegion]] = {}
    for label, clip in part_clips.items():
        pid = parse_part_id(label)
        if not pid:
            continue
        by_parent.setdefault(pid.parent, []).extend(clip.bands)
    out: dict[str, PaperClip] = {}
    for parent, bands in by_parent.items():
        bands = sorted(bands, key=lambda b: (b.page, b.y0, b.x0))
        if bands:
            out[parent] = PaperClip(bands=bands)
    return out


def export_question_figures(
    pdf_path: Path,
    *,
    question_id_prefix: str,
    assets_dir: Path,
    questions: list[str] | None = None,
    include_paper_clips: bool = True,
    ms_pdf: Path | None = None,
) -> dict[str, list[str]]:
    """Render figures; return {question_num: [vault-relative asset paths]}.

    Paths are ordered: ``*-paper.png`` full-question clip first (when enabled),
    then focused diagram/options crops, then ``*-ms.png`` when ``ms_pdf`` is set.
    When ``include_paper_clips`` is True, every requested question must receive
    a paper clip.
    """
    pdf_path = Path(pdf_path)
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    assigned = assign_figures_to_questions(pdf_path)
    paper_clips = question_paper_clips(pdf_path) if include_paper_clips else {}
    ms_clips = (
        mark_scheme_main_clips(ms_pdf)
        if ms_pdf is not None and Path(ms_pdf).exists()
        else {}
    )

    if questions is not None:
        qnums = set(questions)
    else:
        qnums = set(assigned) | set(paper_clips)

    if include_paper_clips:
        missing = sorted(
            (q for q in qnums if q not in paper_clips),
            key=lambda x: int(x),
        )
        if missing:
            raise RuntimeError(
                "Missing full-question paper clips for: "
                + ", ".join(f"q{q}" for q in missing)
                + ". Check question-number detection / stem validation."
            )

    import fitz

    out: dict[str, list[str]] = {}
    doc = fitz.open(pdf_path)
    try:
        for qnum in sorted(qnums, key=lambda x: int(x)):
            paths: list[str] = []

            if qnum in paper_clips:
                name = f"{question_id_prefix}-q{qnum}-paper.png"
                render_figure(pdf_path, paper_clips[qnum], assets_dir / name)
                paths.append(f"assets/{name}")

            focus_i = 0
            for fig in assigned.get(qnum, []):
                # Skip focused crops almost identical to the paper clip
                paper = paper_clips.get(qnum)
                if paper is not None:
                    # If focused crop covers >85% of paper height, skip (redundant)
                    if (
                        fig.height >= paper.height * 0.85
                        and fig.width >= paper.width * 0.75
                    ):
                        continue
                # Reject focus crops that OCR into the next question
                focus_text = _clip_text(doc[fig.page - 1], fig)
                if _clip_contains_next_question(focus_text, qnum):
                    continue
                focus_i += 1
                suffix = "" if focus_i == 1 else f"-{focus_i}"
                name = f"{question_id_prefix}-q{qnum}{suffix}.png"
                render_figure(pdf_path, fig, assets_dir / name)
                paths.append(f"assets/{name}")

            ms_clip = ms_clips.get(qnum)
            if ms_clip is not None and ms_pdf is not None:
                ms_name = f"{question_id_prefix}-q{qnum}-ms.png"
                render_figure(Path(ms_pdf), ms_clip, assets_dir / ms_name)
                paths.append(f"assets/{ms_name}")

            if paths:
                out[qnum] = paths
    finally:
        doc.close()
    return out


_MS_PART_LABEL_RE = re.compile(
    r"^\d{1,2}\([a-z]\)(?:\([ivx]+\))?$",
    re.IGNORECASE,
)
_QP_PART_TOKEN_RE = re.compile(r"^\(([a-z]|[ivx]+)\)$", re.IGNORECASE)


def _page_space_words(page: Any) -> list[tuple[str, float, float, float, float]]:
    """Words as (text, x0, y0, x1, y1) in the visible (rotated) page space."""
    import fitz

    m = page.rotation_matrix
    out: list[tuple[str, float, float, float, float]] = []
    for w in page.get_text("words"):
        p0 = fitz.Point(w[0], w[1]) * m
        p1 = fitz.Point(w[2], w[3]) * m
        x0, x1 = sorted((p0.x, p1.x))
        y0, y1 = sorted((p0.y, p1.y))
        out.append((str(w[4]), x0, y0, x1, y1))
    return out


def mark_scheme_part_clips(ms_pdf: Path) -> dict[str, PaperClip]:
    """Horizontal row crops per MS part label (``2(a)(i)`` → PaperClip).

    CIE Paper 2/4 mark schemes are landscape tables: each part is a row with
    Question | Answer | Marks. Labels are located via word geometry (rotation
    aware) and bands run from one label to the next.
    """
    import fitz

    from chembank.structured_parts import parse_part_id

    ms_pdf = Path(ms_pdf)
    doc = fitz.open(ms_pdf)
    out: dict[str, PaperClip] = {}
    try:
        for i, page in enumerate(doc):
            labs: list[tuple[str, float]] = []
            for text, x0, y0, x1, y1 in _page_space_words(page):
                t = text.strip()
                if not _MS_PART_LABEL_RE.match(t):
                    continue
                pid = parse_part_id(t)
                if not pid:
                    continue
                labs.append((pid.label, y0))
            if not labs:
                continue
            labs.sort(key=lambda t: t[1])
            # Dedupe identical labels keeping topmost
            seen: set[str] = set()
            uniq: list[tuple[str, float]] = []
            for label, y0 in labs:
                if label in seen:
                    continue
                seen.add(label)
                uniq.append((label, y0))
            header_y = 52.0
            for j, (label, y0) in enumerate(uniq):
                top = header_y if j == 0 else y0
                bot = (
                    uniq[j + 1][1]
                    if j + 1 < len(uniq)
                    else float(page.rect.y1) - 28.0
                )
                if bot <= top + 12:
                    bot = min(float(page.rect.y1) - 20.0, top + 36.0)
                region = FigureRegion(
                    page=i + 1,
                    x0=36.0,
                    y0=max(0.0, top),
                    x1=float(page.rect.x1) - 32.0,
                    y1=min(float(page.rect.y1), bot),
                )
                out[label] = PaperClip(bands=[region])
    finally:
        doc.close()
    return out


# Top content margin used for multi-page structured part continuations.
_STRUCTURED_PAGE_TOP = 48.0
# Skip a next-page sliver shorter than this — it only catches the following
# part/question opener (forced min-height used to cause letter/Q bleed).
_STRUCTURED_MIN_CONT_H = 10.0


def _structured_band_span(
    doc: Any,
    *,
    start_page: int,
    start_y: float,
    end_page: int,
    end_y: float,
) -> list[FigureRegion]:
    """Build page bands covering ``[start, end)`` in page-index / y space.

    End boundaries are hard: never pad past ``end_y`` on the final page (a
    previous min-height of 76pt swallowed the next ``(b)`` / ``(ii)`` / Qn).
    """
    if end_page < start_page:
        return []
    if end_page == start_page and end_y <= start_y + 6.0:
        return []

    bands: list[FigureRegion] = []
    if start_page == end_page:
        page = doc[start_page]
        x0, x1 = 40.0, float(page.rect.x1) - 32.0
        # Prefer the hard stop; only pad tiny same-page spans that have no
        # later marker (end_y already past useful content).
        y1 = end_y if end_y > start_y + 6.0 else start_y + 28.0
        bands.append(
            FigureRegion(
                page=start_page + 1,
                x0=x0,
                y0=max(0.0, start_y),
                x1=x1,
                y1=min(float(page.rect.y1) - 20.0, y1),
            )
        )
        return bands

    page = doc[start_page]
    bands.append(
        FigureRegion(
            page=start_page + 1,
            x0=40.0,
            y0=max(0.0, start_y),
            x1=float(page.rect.x1) - 32.0,
            y1=float(page.rect.y1) - 36.0,
        )
    )
    for j in range(start_page + 1, end_page):
        mid = doc[j]
        bands.append(
            FigureRegion(
                page=j + 1,
                x0=40.0,
                y0=_STRUCTURED_PAGE_TOP,
                x1=float(mid.rect.x1) - 32.0,
                y1=float(mid.rect.y1) - 36.0,
            )
        )
    # Last page: honour end_y exactly; omit near-empty top bands that would
    # only capture the next part letter or main-question opener.
    if end_y > _STRUCTURED_PAGE_TOP + _STRUCTURED_MIN_CONT_H:
        last = doc[end_page]
        bands.append(
            FigureRegion(
                page=end_page + 1,
                x0=40.0,
                y0=_STRUCTURED_PAGE_TOP,
                x1=float(last.rect.x1) - 32.0,
                y1=min(float(last.rect.y1) - 20.0, end_y),
            )
        )
    return bands


def _merge_adjacent_part_bands(bands: list[FigureRegion]) -> list[FigureRegion]:
    """Merge same-page bands that abut or overlap (stem+body continuity)."""
    if not bands:
        return bands
    ordered = sorted(bands, key=lambda b: (b.page, b.y0, b.y1))
    out = [ordered[0]]
    for band in ordered[1:]:
        prev = out[-1]
        if band.page == prev.page and band.y0 <= prev.y1 + 12.0:
            out[-1] = FigureRegion(
                page=prev.page,
                x0=min(prev.x0, band.x0),
                y0=min(prev.y0, band.y0),
                x1=max(prev.x1, band.x1),
                y1=max(prev.y1, band.y1),
            )
        else:
            out.append(band)
    return out


def structured_part_paper_clips(qp_pdf: Path) -> dict[str, PaperClip]:
    """Per-part QP crops keyed by label ``2(a)(i)``.

    Uses left-margin ``(a)`` / ``(i)`` markers inside each main-question band.
    Each leaf clip:
    - ends at the next part marker (next roman, next letter stem, or next main Q)
      so ``(a)(iii)`` never bleeds into ``(b)`` preamble;
    - prepends the shared question stem and, for roman leaves, the letter
      preamble under ``(b)`` / ``(c)`` when that text sits above ``(i)``.
    """
    import fitz

    from chembank.structured_parts import PartId

    qp_pdf = Path(qp_pdf)
    doc = fitz.open(qp_pdf)
    # All markers (letter + roman); letter stems stay as hard boundaries.
    events: list[tuple[PartId, int, float]] = []
    try:
        current_q: str | None = None
        current_letter: str | None = None
        for i, page in enumerate(doc):
            qranges = question_y_ranges_on_page(page)
            # Update current_q when a main number appears
            if qranges:
                # leftmost / topmost new question on page
                ordered = sorted(qranges.items(), key=lambda kv: kv[1][0])
                current_q = ordered[0][0]
            if current_q is None:
                continue
            # Part tokens in this question's y window (or whole page if continuation)
            if current_q in qranges:
                y_lo, y_hi = qranges[current_q]
            else:
                y_lo, y_hi = 40.0, float(page.rect.y1) - 36.0
            tokens: list[tuple[str, float]] = []
            for w in page.get_text("words"):
                text = str(w[4])
                if not _QP_PART_TOKEN_RE.match(text):
                    continue
                if w[0] > 120:
                    continue
                mid_y = (w[1] + w[3]) / 2
                if mid_y < y_lo - 4 or mid_y > y_hi + 4:
                    continue
                tokens.append((text.lower(), float(w[1])))
            tokens.sort(key=lambda t: t[1])
            for tok, y0 in tokens:
                inner = tok.strip("()").lower()
                # Romans before letters: "(i)" must not become letter "i"
                if re.fullmatch(r"(?:iv|ix|vi{0,3}|iii|ii|i|v|x)", inner):
                    if current_letter:
                        events.append(
                            (
                                PartId(
                                    parent=str(current_q),
                                    letter=current_letter,
                                    roman=inner,
                                ),
                                i,
                                y0,
                            )
                        )
                elif re.fullmatch(r"[a-z]", inner):
                    current_letter = inner
                    events.append(
                        (
                            PartId(
                                parent=str(current_q),
                                letter=current_letter,
                                roman=None,
                            ),
                            i,
                            y0,
                        )
                    )

        if not events:
            return {}

        letters_with_romans: set[tuple[str, str]] = set()
        for pid, _, _ in events:
            if pid.roman:
                letters_with_romans.add((pid.parent, pid.letter))
        leaves = [
            e
            for e in events
            if e[0].roman is not None
            or (e[0].parent, e[0].letter) not in letters_with_romans
        ]

        # Letter-stem positions (even when romans exist) — hard end boundaries.
        letter_pos: dict[tuple[str, str], tuple[int, float]] = {}
        first_roman_pos: dict[tuple[str, str], tuple[int, float]] = {}
        first_marker_pos: dict[str, tuple[int, float]] = {}
        for pid, page_i, y0 in events:
            key = (pid.parent, pid.letter)
            if pid.roman is None and key not in letter_pos:
                letter_pos[key] = (page_i, y0)
            if pid.roman is not None and key not in first_roman_pos:
                first_roman_pos[key] = (page_i, y0)
            if pid.parent not in first_marker_pos:
                first_marker_pos[pid.parent] = (page_i, y0)

        main_clips = question_paper_clips(qp_pdf)

        # Boundary list: every marker (letter stems + leaf markers) in order.
        # Letter-only events that have roman children are boundaries but not leaves.
        # Main-question openers are hard stops so the last part of Qn cannot
        # swallow Q(n+1)'s stem (e.g. 3(d) must end before "4 Aqueous…").
        boundary_keys: list[tuple[str, int, float]] = []
        seen_bound: set[tuple[str, int, int]] = set()
        for pid, page_i, y0 in events:
            # Deduplicate identical (label, page, rounded-y) markers
            sig = (pid.label, page_i, int(y0))
            if sig in seen_bound:
                continue
            seen_bound.add(sig)
            boundary_keys.append((pid.label, page_i, y0))
        # Also ensure letter stems appear even if somehow skipped
        for (parent, letter), (page_i, y0) in letter_pos.items():
            lab = f"{parent}({letter})"
            sig = (lab, page_i, int(y0))
            if sig not in seen_bound:
                seen_bound.add(sig)
                boundary_keys.append((lab, page_i, y0))
        for qnum, clip in main_clips.items():
            if not clip.bands:
                continue
            b0 = clip.bands[0]
            lab = f"Q{qnum}"
            page_i = b0.page - 1
            sig = (lab, page_i, int(b0.y0))
            if sig not in seen_bound:
                seen_bound.add(sig)
                boundary_keys.append((lab, page_i, float(b0.y0)))
        boundary_keys.sort(key=lambda t: (t[1], t[2]))

        def _end_before_next(
            page_i: int, y0: float, parent: str
        ) -> tuple[int, float]:
            for lab, n_page, n_y0 in boundary_keys:
                # Skip markers that belong to this part's own start / earlier
                if n_page < page_i or (n_page == page_i and n_y0 <= y0 + 0.5):
                    continue
                # Do not treat this question's own main opener as an end
                if lab == f"Q{parent}":
                    continue
                return n_page, n_y0 - 2.0
            parent_clip = main_clips.get(parent)
            if parent_clip is not None:
                last = parent_clip.bands[-1]
                return last.page - 1, last.y1
            return len(doc) - 1, float(doc[-1].rect.y1) - 40.0

        out: dict[str, PaperClip] = {}
        for pid, page_i, y0 in leaves:
            end_page, end_y = _end_before_next(page_i, y0, pid.parent)
            body_bands = _structured_band_span(
                doc,
                start_page=page_i,
                start_y=max(0.0, y0 - 2.0),
                end_page=end_page,
                end_y=end_y,
            )

            shared: list[FigureRegion] = []
            # Question-level intro: main Q start → first part marker
            parent_clip = main_clips.get(pid.parent)
            first_m = first_marker_pos.get(pid.parent)
            if parent_clip is not None and first_m is not None:
                q_page = parent_clip.bands[0].page - 1
                q_y0 = parent_clip.bands[0].y0
                m_page, m_y0 = first_m
                stem_bands = _structured_band_span(
                    doc,
                    start_page=q_page,
                    start_y=q_y0,
                    end_page=m_page,
                    end_y=m_y0 - 2.0,
                )
                shared.extend(stem_bands)

            # Letter preamble under (b)/(c)/… before first roman child
            key = (pid.parent, pid.letter)
            if pid.roman and key in letter_pos and key in first_roman_pos:
                lp, ly = letter_pos[key]
                rp, ry = first_roman_pos[key]
                if rp > lp or ry > ly + 8.0:
                    pre_bands = _structured_band_span(
                        doc,
                        start_page=lp,
                        start_y=max(0.0, ly - 2.0),
                        end_page=rp,
                        end_y=ry - 2.0,
                    )
                    shared.extend(pre_bands)

            bands = _merge_adjacent_part_bands(shared + body_bands)
            if not bands:
                continue
            out[pid.label] = PaperClip(bands=bands)
        return out
    finally:
        doc.close()


def export_structured_part_figures(
    qp_pdf: Path,
    *,
    ms_pdf: Path | None,
    question_id_prefix: str,
    assets_dir: Path,
    part_labels: list[str],
) -> dict[str, list[str]]:
    """Render QP part clips + MS part clips. Keys are part labels ``2(a)(i)``.

    Asset names use slugs: ``{prefix}-q2a-i-paper.png``, ``{prefix}-q2a-i-ms.png``.
    Falls back to the parent main-question QP clip when a part band is missing.
    """
    from chembank.structured_parts import parse_part_id

    qp_pdf = Path(qp_pdf)
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    part_clips = structured_part_paper_clips(qp_pdf)
    main_clips = question_paper_clips(qp_pdf)
    ms_clips = mark_scheme_part_clips(ms_pdf) if ms_pdf and Path(ms_pdf).exists() else {}

    out: dict[str, list[str]] = {}
    for label in part_labels:
        pid = parse_part_id(label)
        if not pid:
            continue
        paths: list[str] = []
        clip = part_clips.get(pid.label) or main_clips.get(pid.parent)
        if clip is None:
            raise RuntimeError(f"Missing QP paper clip for structured part {pid.label}")
        paper_name = f"{question_id_prefix}-q{pid.slug}-paper.png"
        render_figure(qp_pdf, clip, assets_dir / paper_name)
        paths.append(f"assets/{paper_name}")

        ms_clip = ms_clips.get(pid.label)
        # Fallback: MS sometimes marks 3(a) as one block while QP splits 3(a)(i)/(ii).
        if ms_clip is None and pid.letter:
            parent_label = f"{pid.parent}({pid.letter})"
            ms_clip = ms_clips.get(parent_label)
        if ms_clip is None and pid.parent:
            # Last resort: any MS clip sharing the same main question number.
            for key, clip in ms_clips.items():
                if str(key).startswith(f"{pid.parent}(") or str(key) == pid.parent:
                    ms_clip = clip
                    break
        if ms_clip is not None and ms_pdf is not None:
            ms_name = f"{question_id_prefix}-q{pid.slug}-ms.png"
            render_figure(Path(ms_pdf), ms_clip, assets_dir / ms_name)
            paths.append(f"assets/{ms_name}")
        out[pid.label] = paths
    return out

