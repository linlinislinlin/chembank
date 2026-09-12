"""UKChO Round 1 PDF extraction, splitting and page-clip rendering.

UKChO papers are *not* shaped like CIE papers, so they do not use
``chembank.split`` / ``chembank.structured_parts``:

* a paper is 6 long questions, each with parts ``(a)``, ``(b)`` ... and some
  with sub-parts ``(i)``, ``(ii)``;
* almost every part is answered by *drawing structures*, so the text alone is
  useless to a student — a page-clip PNG of the part is the primary artefact.

This module therefore does three things:

1. reads the per-page text;
2. detects question / part / sub-part labels from their *coordinates* (the
   labels sit in a very stable left margin: x~77-81 for ``Q`` and ``(a)``,
   x~107-111 for ``(i)``), which is far more reliable than regex over the
   jumbled text stream;
3. renders one PNG per part, spanning page breaks when a part runs over.

Marks are deliberately **not** parsed here: the UKChO question paper does not
print per-part marks, and the mark scheme encodes them as tick boxes. Marks are
supplied by the tagging step (a human or a model reading the mark scheme), which
is why :class:`Part` exposes ``text`` but no ``marks``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# --- label geometry -------------------------------------------------------

#: Question and part labels both hang in the far-left margin.
LEFT_X_MAX = 95.0
#: Sub-part labels ``(i)`` / ``(ii)`` are indented one level.
SUBPART_X_MIN = 100.0
SUBPART_X_MAX = 128.0

QUESTION_RE = re.compile(r"^Q([1-9])\b\s*(.*)$")
#: A part/sub-part label is usually alone on its line, but may share the line with
#: the start of the question text (e.g. "(ii) Determine the value of ..."), which
#: the trailing group captures.
PART_RE = re.compile(r"^\(([a-z])\)(?:\s+(.*))?$")
SUBPART_RE = re.compile(r"^\(([ivx]+)\)(?:\s+(.*))?$")

#: The final page of a UKChO paper lists image credits as "Q1 The image is © ...".
#: Those lines look exactly like question labels, so they must be dropped.
CREDITS_RE = re.compile(r"^The image is ©|^This work is published|^The image of ")

#: A label this close to the top of a page is the first thing on the page, so the
#: *previous* part did not continue onto this page.
HEADER_Y = 90.0

#: Trim this much whitespace from the top/bottom of each clip.
CLIP_MARGIN = 4.0
#: Horizontal clip bounds as a fraction of page width.
CLIP_X0_FRAC = 0.045
CLIP_X1_FRAC = 0.955
#: Never emit a clip taller than this (safety net for a whole-page span).
MAX_CLIP_HEIGHT = 1400.0
#: Clips shorter than this are page furniture (a stray header, a page number).
MIN_CLIP_HEIGHT = 60.0


@dataclass
class Label:
    """A question / part / sub-part marker found in the PDF."""

    kind: str  # "question" | "part" | "subpart"
    page: int  # 0-based
    y: float
    x: float
    text: str
    question: int | None = None
    part: str | None = None
    subpart: str | None = None
    rest: str = ""  # text following a "Qn ..." label on the same line


@dataclass
class Part:
    """One sub-question, with the text and the pages it occupies."""

    question: int
    part: str
    subpart: str | None
    page: int
    y: float
    text: str
    end_page: int
    end_y: float
    labels: list[Label] = field(default_factory=list)

    @property
    def key(self) -> str:
        """Stable part key, e.g. ``3a`` or ``6b-i``."""
        base = f"{self.question}{self.part}"
        return f"{base}-{self.subpart}" if self.subpart else base

    @property
    def label(self) -> str:
        """Human label, e.g. ``(3a)`` or ``(6b)(i)``."""
        base = f"{self.question}{self.part}"
        return f"({base})({self.subpart})" if self.subpart else f"({base})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "part": self.part,
            "subpart": self.subpart,
            "key": self.key,
            "label": self.label,
            "page": self.page + 1,
            "end_page": self.end_page + 1,
            "text": self.text,
        }


# --- text extraction ------------------------------------------------------


def _lines_in_order(page) -> list[tuple[float, float, str]]:
    """Return ``(y, x, text)`` for every text line, in reading order."""
    out: list[tuple[float, float, str]] = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"]).strip()
            if not text:
                continue
            x0, y0, _x1, _y1 = line["bbox"]
            out.append((round(y0, 1), round(x0, 1), text))
    out.sort(key=lambda item: (item[0], item[1]))
    return out


def find_labels(doc) -> list[Label]:
    """Detect every question / part / sub-part label, in document order."""
    labels: list[Label] = []
    for pno in range(doc.page_count):
        for y, x, text in _lines_in_order(doc[pno]):
            if x <= LEFT_X_MAX:
                q = QUESTION_RE.match(text)
                if q:
                    rest = q.group(2).strip()
                    if CREDITS_RE.match(rest):
                        continue  # image-credits page, not a real question
                    labels.append(
                        Label(
                            kind="question",
                            page=pno,
                            y=y,
                            x=x,
                            text=text,
                            question=int(q.group(1)),
                            rest=rest,
                        )
                    )
                    continue
                p = PART_RE.match(text)
                if p:
                    labels.append(
                        Label(
                            kind="part",
                            page=pno,
                            y=y,
                            x=x,
                            text=text,
                            part=p.group(1),
                            rest=(p.group(2) or "").strip(),
                        )
                    )
                    continue
            elif SUBPART_X_MIN <= x <= SUBPART_X_MAX:
                s = SUBPART_RE.match(text)
                if s:
                    labels.append(
                        Label(
                            kind="subpart",
                            page=pno,
                            y=y,
                            x=x,
                            text=text,
                            subpart=s.group(1),
                            rest=(s.group(2) or "").strip(),
                        )
                    )
    return labels


def _text_between(doc, start: Label, end: Label | None) -> str:
    """Collect lines between two labels (page-aware, reading order).

    Note: UKChO parts that mix body text with equations or tables are laid out in
    columns, so this stream can interleave. The page clip is the authoritative
    rendering of a part; this text is a convenience copy for search/diffing.
    """
    chunks: list[str] = []
    last_page = end.page if end else start.page
    for pno in range(start.page, last_page + 1):
        for y, _x, text in _lines_in_order(doc[pno]):
            if pno == start.page and y < start.y - 1:
                continue
            if end is not None and pno == end.page and y >= end.y - 1:
                continue
            if pno == start.page and y == start.y and text == start.text:
                continue
            chunks.append(text)
    return "\n".join(chunks).strip()


def question_stems(doc, labels: list[Label]) -> dict[int, str]:
    """Map question number -> introductory stem (from ``Qn`` to the first part)."""
    stems: dict[int, str] = {}
    for idx, label in enumerate(labels):
        if label.kind != "question" or label.question is None:
            continue
        if label.question in stems:
            continue  # first occurrence wins; later ones are credits/noise
        nxt = next((lb for lb in labels[idx + 1 :] if lb.kind == "part"), None)
        stem = _text_between(doc, label, nxt)
        if label.rest:
            stem = (label.rest + "\n" + stem).strip()
        stems[label.question] = stem
    return stems


def _next_boundary(labels: list[Label], start_idx: int) -> tuple[Label | None, int]:
    """Return the next label that terminates the current part, plus its index."""
    for j in range(start_idx, len(labels)):
        return labels[j], j
    return None, len(labels)


def _part_end(doc, label: Label, end: Label | None) -> tuple[int, float]:
    """Resolve where a part ends, clamping a top-of-next-page boundary away.

    When the next label sits at the very top of a following page, the part
    finished on its own page — extending it would produce a sliver clip of the
    next page's header.
    """
    if end is None or (end.page > label.page and end.y < HEADER_Y):
        return label.page, _page_height(doc, label.page)
    return end.page, end.y


def split_parts(doc) -> tuple[list[Part], dict[int, str]]:
    """Split the paper into parts. Returns ``(parts, question_stems)``.

    A part runs from its own label to the next label of any kind. Sub-part labels
    start a new part, so ``Q6(b)(i)`` and ``Q6(b)(ii)`` become independent records
    — a UKChO sub-question is tagged on its own, never by inheriting ``Q6(b)``.

    A part letter immediately followed by a sub-part letter (``(a)`` then
    ``(a)(i)``) is a *container*: it is not emitted as a record of its own, and
    any text it carries is folded into the first sub-part.
    """
    labels = find_labels(doc)
    stems = question_stems(doc, labels)

    parts: list[Part] = []
    current_question: int | None = None
    pending_prefix = ""
    i = 0
    while i < len(labels):
        label = labels[i]
        if label.kind == "question":
            current_question = label.question
            pending_prefix = ""
            i += 1
            continue

        if label.kind == "part" and current_question is not None:
            nxt, _j = _next_boundary(labels, i + 1)
            if not label.rest and nxt is not None and nxt.kind == "subpart":
                pending_prefix = _text_between(doc, label, nxt)
                i += 1
                continue
            end, j = _next_boundary(labels, i + 1)
            end_page, end_y = _part_end(doc, label, end)
            text = _text_between(doc, label, end)
            if label.rest:
                text = (label.rest + "\n" + text).strip()
            parts.append(
                Part(
                    question=current_question,
                    part=label.part or "",
                    subpart=None,
                    page=label.page,
                    y=label.y,
                    text=text,
                    end_page=end_page,
                    end_y=end_y,
                    labels=[label],
                )
            )
            pending_prefix = ""
            i = j if j > i + 1 else i + 1
            continue

        if label.kind == "subpart" and current_question is not None:
            parent = next(
                (lb for lb in reversed(labels[:i]) if lb.kind == "part"), None
            )
            end, j = _next_boundary(labels, i + 1)
            end_page, end_y = _part_end(doc, label, end)
            text = _text_between(doc, label, end)
            if label.rest:
                text = (label.rest + "\n" + text).strip()
            if pending_prefix:
                text = (pending_prefix + "\n" + text).strip()
            parts.append(
                Part(
                    question=current_question,
                    part=parent.part if parent else "",
                    subpart=label.subpart,
                    page=label.page,
                    y=label.y,
                    text=text,
                    end_page=end_page,
                    end_y=end_y,
                    labels=[label],
                )
            )
            pending_prefix = ""
            i = j if j > i + 1 else i + 1
            continue

        i += 1

    return parts, stems


def _page_height(doc, pno: int) -> float:
    return float(doc[pno].rect.height)


# --- clip rendering -------------------------------------------------------


def render_part_clip(doc, part: Part, out_path: Path, zoom: float = 2.4) -> list[str]:
    """Render ``part`` (possibly across a page break) to one or more PNGs.

    Returns the list of files written. A part that fits on one page produces a
    single PNG; one that runs over a page break produces ``<stem>.png``,
    ``<stem>-2.png``, ... so nothing is silently cropped.
    """
    written: list[str] = []
    span = list(range(part.page, part.end_page + 1))
    import fitz

    for n, pno in enumerate(span):
        page = doc[pno]
        width, height = float(page.rect.width), float(page.rect.height)
        top = part.y - CLIP_MARGIN if pno == part.page else 0.0
        bottom = part.end_y - CLIP_MARGIN if pno == part.end_page else height
        top = max(0.0, top)
        bottom = min(height, bottom)
        # A short *first* clip is a genuinely short question and must be kept.
        # A short *continuation* clip is just the next page's header furniture.
        if n > 0 and bottom - top < MIN_CLIP_HEIGHT:
            continue
        if bottom - top < 12.0:
            continue
        if bottom - top > MAX_CLIP_HEIGHT:
            bottom = top + MAX_CLIP_HEIGHT
        clip = page.rect.__class__(
            width * CLIP_X0_FRAC,
            top,
            width * CLIP_X1_FRAC,
            bottom,
        )
        target = out_path if n == 0 else out_path.with_name(
            f"{out_path.stem}-{n + 1}{out_path.suffix}"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
        pix.save(str(target))
        written.append(str(target))
    return written


def extract_paper(
    pdf_path: Path,
    out_dir: Path,
    clip_prefix: str,
    make_clips: bool = True,
    zoom: float = 2.4,
) -> dict[str, Any]:
    """Extract one UKChO paper: split parts, render clips, write a manifest JSON.

    Output layout::

        out_dir/
          parts.json          # machine-readable split
          parts/<prefix>-<key>.txt
          clips/<prefix>-<key>.png

    Returns the manifest dict.
    """
    import fitz

    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)

    parts, stems = split_parts(doc)
    manifest: dict[str, Any] = {
        #: Carried in the manifest so the tagging step needs no extra flags.
        "prefix": clip_prefix,
        "source_pdf": str(pdf_path),
        "page_count": doc.page_count,
        "stems": {str(k): v for k, v in sorted(stems.items())},
        "parts": [],
    }

    text_dir = out_dir / "parts"
    text_dir.mkdir(parents=True, exist_ok=True)
    clip_dir = out_dir / "clips"

    for part in parts:
        entry = part.to_dict()
        txt_path = text_dir / f"{clip_prefix}-{part.key}.txt"
        txt_path.write_text(part.text + "\n", encoding="utf-8")
        entry["text_path"] = str(txt_path)
        if make_clips:
            png = clip_dir / f"{clip_prefix}-{part.key}-paper.png"
            entry["clips"] = render_part_clip(doc, part, png, zoom=zoom)
        else:
            entry["clips"] = []
        manifest["parts"].append(entry)

    doc.close()
    (out_dir / "parts.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def load_manifest(out_dir: Path) -> dict[str, Any]:
    return json.loads((Path(out_dir) / "parts.json").read_text(encoding="utf-8"))


def iter_part_dicts(manifest: dict[str, Any]) -> Iterable[dict[str, Any]]:
    return manifest.get("parts") or []
