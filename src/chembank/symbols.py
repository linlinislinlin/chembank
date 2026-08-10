"""Recover chemistry symbols that CIE PDFs draw as vectors (not text).

Cambridge papers often paint ΔH⦵ and similar as filled path drawings. Plain
`page.get_text()` then leaves blank gaps. This module:

1. Merges real text spans with unicode sub/superscripts from font size
2. Detects vector ΔH clusters and decodes subscripts from ink
3. Interleaves both by page coordinates into reading order
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CHAR_FIXES = str.maketrans(
    {
        "\uf0b4": "×",
        "\uf0b7": "·",
        "\uf0ae": "→",  # Symbol font arrowright (often renders as ≡)
        "\uf0d7": "→",
        "\uf02d": "−",  # Symbol font minus (often renders as a horizontal bar)
        "\uf02b": "+",  # Symbol font plus
        "\uf0b0": "°",  # Symbol font degree
        "\uf044": "Δ",  # Symbol font Delta (ΔH)
        "\uf070": "π",  # Symbol font pi
        "\uf073": "σ",  # Symbol font sigma
        "\u00a0": " ",
        "\u2212": "−",
        "\u2261": "→",  # ≡ mis-extracted reaction arrow
        # CIE Identity-H custom fonts (2023+ Paper 1): space encoded as C0 controls
        "\x01": " ",
        "\x03": " ",
    }
)

_SUB = str.maketrans("0123456789+-=()aeox", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓ")
_SUP = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")

PLIMSOLL = "⦵"
DELTA_H = "ΔH"


@dataclass
class Token:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    kind: str  # text | symbol

    @property
    def y_mid(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def x_mid(self) -> float:
        return (self.x0 + self.x1) / 2


def normalize_chars(text: str) -> str:
    return text.translate(CHAR_FIXES)


def _to_sub(s: str) -> str:
    return s.translate(_SUB)


def _to_sup(s: str) -> str:
    return s.translate(_SUP)


def _script_role(size: float, body_size: float) -> str:
    if body_size <= 0:
        return "body"
    return "script" if size / body_size < 0.78 else "body"


def text_tokens_from_page(page: Any) -> list[Token]:
    """Build tokens from text dict; fold small spans into sub/superscripts."""
    data = page.get_text("dict")
    raw: list[tuple[float, float, float, float, str, float]] = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = normalize_chars(span.get("text") or "")
                if text == "":
                    continue
                x0, y0, x1, y1 = span["bbox"]
                size = float(span.get("size") or 0)
                # Leading spaces mark a hole where vector symbols sit — shift x0
                # to the first non-space so symbols can sort into the hole.
                stripped_l = text.lstrip(" ")
                lead = len(text) - len(stripped_l)
                if lead and size > 0:
                    x0 = x0 + lead * size * 0.33
                    text = stripped_l
                text = text.rstrip()
                if not text:
                    continue
                raw.append((x0, y0, x1, y1, text, size))

    if not raw:
        return []

    sizes = sorted(s for *_, s in raw if s > 0)
    body_size = sizes[len(sizes) // 2] if sizes else 11.0
    large = [s for s in sizes if s >= body_size * 0.9]
    if large:
        body_size = large[len(large) // 2]

    tokens: list[Token] = []
    i = 0
    while i < len(raw):
        x0, y0, x1, y1, text, size = raw[i]
        role = _script_role(size, body_size)
        if role == "script" and tokens:
            prev = tokens[-1]
            if abs(prev.y_mid - (y0 + y1) / 2) < body_size * 1.2 and x0 - prev.x1 < body_size:
                if (y0 + y1) / 2 < prev.y_mid - body_size * 0.05:
                    prev.text += _to_sup(text.strip())
                else:
                    prev.text += _to_sub(text.strip())
                prev.x1 = max(prev.x1, x1)
                prev.y0 = min(prev.y0, y0)
                prev.y1 = max(prev.y1, y1)
                i += 1
                continue
        tokens.append(Token(x0, y0, x1, y1, text, "text"))
        i += 1
    return tokens


def _drawing_rects(page: Any) -> list[tuple[float, float, float, float]]:
    rects: list[tuple[float, float, float, float]] = []
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None:
            continue
        w, h = r.width, r.height
        if w <= 0 or h <= 0 or w > 80 or h > 30:
            continue
        if w < 0.4 and h < 0.4:
            continue
        rects.append((r.x0, r.y0, r.x1, r.y1))
    return rects


def _cluster_rects(
    rects: list[tuple[float, float, float, float]],
    *,
    y_tol: float = 8.0,
    x_gap: float = 5.0,
) -> list[list[tuple[float, float, float, float]]]:
    """Cluster by horizontal reading bands, then split on large x-gaps."""
    if not rects:
        return []

    # Bucket into y-bands
    by_y = sorted(rects, key=lambda r: (r[1] + r[3]) / 2)
    bands: list[list[tuple[float, float, float, float]]] = []
    band: list[tuple[float, float, float, float]] = [by_y[0]]
    band_y = (by_y[0][1] + by_y[0][3]) / 2
    for r in by_y[1:]:
        cy = (r[1] + r[3]) / 2
        if abs(cy - band_y) <= y_tol:
            band.append(r)
            band_y = (band_y * (len(band) - 1) + cy) / len(band)
        else:
            bands.append(band)
            band = [r]
            band_y = cy
    bands.append(band)

    clusters: list[list[tuple[float, float, float, float]]] = []
    for band_rects in bands:
        ordered = sorted(band_rects, key=lambda r: r[0])
        cur = [ordered[0]]
        for r in ordered[1:]:
            cluster_x1 = max(c[2] for c in cur)
            if r[0] - cluster_x1 <= x_gap:
                cur.append(r)
            else:
                clusters.append(cur)
                cur = [r]
        clusters.append(cur)
    return clusters


def _classify_subscript_ink(page: Any, bbox: tuple[float, float, float, float]) -> str:
    """Classify a subscript glyph from rendered ink. Returns '1'|'2'|'3'|'c'|'?'."""
    import fitz

    x0, y0, x1, y1 = bbox
    clip = fitz.Rect(x0 - 0.3, y0 - 0.3, x1 + 0.3, y1 + 0.3)
    pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(10, 10), alpha=False)
    w, h, n = pix.width, pix.height, pix.n
    samples = pix.samples
    dark = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if samples[(y * w + x) * n] < 170:
                dark[y][x] = 1
    xs = [x for y in range(h) for x in range(w) if dark[y][x]]
    ys = [y for y in range(h) for x in range(w) if dark[y][x]]
    if not xs:
        return "?"
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    bw, bh = maxx - minx + 1, maxy - miny + 1
    if bw <= 0 or bh <= 0:
        return "?"

    def row_dens(y: int) -> float:
        return sum(dark[y][x] for x in range(minx, maxx + 1)) / bw

    bottom = sum(row_dens(y) for y in range(maxy - max(1, bh // 5), maxy + 1)) / max(
        1, bh // 5
    )
    mid = row_dens(miny + bh // 2)
    right_open = 1.0 - (
        sum(dark[miny + bh // 2][x] for x in range(minx + 2 * bw // 3, maxx + 1))
        / max(1, bw // 3)
    )
    aspect = bw / bh

    # 1: narrow stem
    if aspect < 0.5 and right_open < 0.35:
        return "1"
    # c: strongly open on the right through the body
    if right_open > 0.75 and bottom < 0.7:
        return "c"
    # 2: heavy bottom bar, weaker mid band
    if bottom >= 0.62 and mid <= 0.4:
        return "2"
    # 3: curved, moderate right openness
    if right_open > 0.25:
        return "3"
    return "2" if bottom > mid else "3"


def decode_delta_h_tokens(page: Any) -> list[Token]:
    """Find vector-drawn ΔH⦵ₙ clusters and return symbol tokens."""
    rects = _drawing_rects(page)
    clusters = _cluster_rects(rects)
    tokens: list[Token] = []

    for cluster in clusters:
        if len(cluster) < 4:
            continue
        x0 = min(r[0] for r in cluster)
        y0 = min(r[1] for r in cluster)
        x1 = max(r[2] for r in cluster)
        y1 = max(r[3] for r in cluster)
        width = x1 - x0
        height = y1 - y0
        if width < 14 or width > 36 or height < 6 or height > 18:
            continue

        # Plimsoll ≈ thin horizontal bar + small circle
        has_bar = any((r[3] - r[1]) <= 1.2 and (r[2] - r[0]) >= 2.0 for r in cluster)
        large = [r for r in cluster if (r[2] - r[0]) >= 4.5 and (r[3] - r[1]) >= 5.5]
        if not has_bar or len(large) < 2:
            continue

        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        tall = [
            r
            for r in cluster
            if r[0] >= cx - 2
            and (r[3] - r[1]) >= 3.2
            and (r[3] - r[1]) >= (r[2] - r[0]) * 0.85
            and (r[1] + r[3]) / 2 >= cy - 1
        ]
        if tall:
            sub = max(tall, key=lambda r: (r[1] + r[3]) / 2)
            sub_char = _classify_subscript_ink(page, sub)
        else:
            sub_char = ""

        if sub_char and sub_char != "?":
            text = f"{DELTA_H}{_to_sub(sub_char)}{PLIMSOLL}"
        else:
            text = f"{DELTA_H}{PLIMSOLL}"
        tokens.append(Token(x0, y0, x1, y1, text, "symbol"))

    return tokens


def _same_line(a: Token, b: Token, *, tol: float) -> bool:
    return abs(a.y_mid - b.y_mid) <= tol


def tokens_to_text(tokens: list[Token], *, line_tol: float = 5.5) -> str:
    if not tokens:
        return ""
    # symbols before text at the same x so ΔH fills leading holes
    ordered = sorted(
        tokens,
        key=lambda t: (round(t.y_mid / line_tol), t.x0, 0 if t.kind == "symbol" else 1),
    )
    lines: list[list[Token]] = []
    for tok in ordered:
        if not lines or not _same_line(lines[-1][0], tok, tol=line_tol):
            lines.append([tok])
        else:
            lines[-1].append(tok)

    out_lines: list[str] = []
    for line in lines:
        line = sorted(line, key=lambda t: (t.x0, 0 if t.kind == "symbol" else 1))
        parts: list[str] = []
        prev: Token | None = None
        for tok in line:
            if prev is not None:
                gap = tok.x0 - prev.x1
                need_space = gap > 2.8
                # Keep a space around recovered symbols next to words
                if tok.kind == "symbol" and prev.text[-1:].isalnum():
                    need_space = True
                if prev.kind == "symbol" and tok.text[:1].isalnum():
                    need_space = True
                # Preserve spaces after punctuation when spans are close
                if prev.text[-1:] in ",;:" and tok.text[:1].isalnum():
                    need_space = True
                if need_space and not (parts and parts[-1].endswith(" ")):
                    parts.append(" ")
            parts.append(tok.text)
            prev = tok
        text = "".join(parts)
        while "  " in text:
            text = text.replace("  ", " ")
        out_lines.append(text.strip())
    return "\n".join(out_lines)


def _inject_reaction_arrows(tokens: list[Token]) -> list[Token]:
    """If a ΔH label sits in the x-gap between two formula fragments, insert →."""
    texts = [t for t in tokens if t.kind == "text"]
    symbols = [t for t in tokens if t.kind == "symbol"]
    extras: list[Token] = []

    for sym in symbols:
        # Find text tokens on a line slightly below the symbol (thermochemical eq.)
        below = [
            t
            for t in texts
            if 0 <= (t.y_mid - sym.y_mid) <= 22
        ]
        # Prefer same-line neighbors around the symbol x
        left_cands = [
            t
            for t in texts
            if abs(t.y_mid - sym.y_mid) <= 18
            and t.x1 <= sym.x_mid + 2
            and "(" in t.text
        ]
        right_cands = [
            t
            for t in texts
            if abs(t.y_mid - sym.y_mid) <= 18
            and t.x0 >= sym.x_mid - 2
            and "(" in t.text
        ]
        # Also allow formula line below orphan ΔHc
        if (not left_cands or not right_cands) and below:
            line_y = min(below, key=lambda t: abs(t.y_mid - (sym.y_mid + 12))).y_mid
            left_cands = [
                t for t in texts if abs(t.y_mid - line_y) <= 6 and t.x1 < sym.x0 and "(" in t.text
            ]
            right_cands = [
                t for t in texts if abs(t.y_mid - line_y) <= 6 and t.x0 > sym.x1 and "(" in t.text
            ]

        if not left_cands or not right_cands:
            continue
        left = max(left_cands, key=lambda t: t.x1)
        right = min(right_cands, key=lambda t: t.x0)
        gap = right.x0 - left.x1
        if gap < 8:
            continue
        # Place arrow in the gap; keep ΔH on its own or fold into "→"
        arrow_y0 = min(left.y0, right.y0)
        arrow_y1 = max(left.y1, right.y1)
        extras.append(
            Token(
                x0=(left.x1 + right.x0) / 2 - 4,
                y0=arrow_y0,
                x1=(left.x1 + right.x0) / 2 + 4,
                y1=arrow_y1,
                text="→",
                kind="text",
            )
        )
        # Pull orphan enthalpy label down onto the equation line for reading order
        sym.y0 = arrow_y0 - 2
        sym.y1 = arrow_y1
        # Put label just above arrow x
        sym.x0 = (left.x1 + right.x0) / 2 - (sym.x1 - sym.x0) / 2
        sym.x1 = sym.x0 + 18

    return tokens + extras


def extract_page_with_symbols(page: Any) -> str:
    """Full page text with vector ΔH symbols restored."""
    text_toks = text_tokens_from_page(page)
    sym_toks = decode_delta_h_tokens(page)
    merged = _inject_reaction_arrows(text_toks + sym_toks)
    return tokens_to_text(merged)
