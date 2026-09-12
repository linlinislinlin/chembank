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

#: A question heading. The format changed over the years: 2022+ prefixes the
#: number with ``Q`` (``Q1 This question is about ...``), while 2003-2021 uses a
#: bare numbered heading (``1.  This question is about ...``), and in 2011 the
#: number sits alone on its line with the title on the next. All are accepted.
QUESTION_RE = re.compile(r"^(?:Q([1-9])|([1-9]\d?)\.)(?:\s+(.*))?$")
#: A part/sub-part label is usually alone on its line, but may share the line with
#: the start of the question text (e.g. "(ii) Determine the value of ..."), which
#: the trailing group captures.
PART_RE = re.compile(r"^\(([a-z])\)(?:\s+(.*))?$")
SUBPART_RE = re.compile(r"^\(([ivx]+)\)(?:\s+(.*))?$")

#: The first word of a sub-question instruction. A roman label followed by one of
#: these opens a real sub-question; a roman label followed by anything else is a
#: row of a table the candidate fills in (see :func:`_drop_table_rows`).
INSTRUCTION_RE = re.compile(
    r"^(?:Add|Balance|Calculate|Choose|Comment|Compare|Complete|Construct|Convert"
    r"|Deduce|Define|Describe|Determine|Discuss|Draw|Estimate|Explain|Give"
    r"|How|Identify|Include|Justify|Label|List|Name|Outline|Predict|Propose"
    r"|Select|Show|Sketch|State|Suggest|Tick|Use|What|When|Where|Which|Why"
    r"|Write)\b",
    re.IGNORECASE,
)

#: A table cell holds a name or a formula, so it is short. Text longer than this
#: is prose and therefore an instruction, however it starts.
TABLE_CELL_MAX_WORDS = 6

#: A table the candidate fills in is announced by its lead-in — "Complete the table
#: in the answer booklet with the number of peaks in the 13C NMR spectrum of:".
#: That wording is what separates such a table from a list of sub-questions that
#: merely share a stem: "Write the number of conjugated C=C bonds in: (i) α-carotene
#: (ii) β-carotene" grades the two items "one mark each", so each stays a
#: sub-question in its own right. The phrases are spelled out because a bare
#: ``table`` would also match "trends in electronegativity in the periodic table",
#: which introduces three separately marked sub-questions.
TABLE_LEAD_IN_RE = re.compile(
    r"answer booklet|complete the table|following table|table below",
    re.IGNORECASE,
)

#: The final page of a UKChO paper lists image credits as "Q1 The image is © ...",
#: which the 2022 and 2024 papers word as "Q4 The images are © ...". Those lines
#: look exactly like question labels, so they must be dropped.
CREDITS_RE = re.compile(r"^The images? (?:is|are) ©|^This work is published|^The image of ")

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

# --- mark scheme geometry -------------------------------------------------
#
# The mark scheme is a different layout from the question paper, so it needs its
# own geometry: MS labels hang further left and a part's own text sits directly
# to their right, rather than in a separate column.
#
# A roman label is the trap. ``(i)`` is *indented* when it is a sub-part of
# ``(a)`` — Q1(a)(i) — but sits at the left margin when it is a part in its own
# right, which is how Q3 and Q6 use it. Indentation alone cannot settle the
# question, so :func:`mark_scheme_bands` resolves it against the QP's known part
# list instead of guessing.

#: MS part labels start this far left (QP parts sit further right).
MS_LEFT_X_MAX = 70.0
#: MS sub-part labels are indented into this band.
MS_SUBPART_X_MIN = 70.0
MS_SUBPART_X_MAX = 100.0
#: An MS question heading sits at the very top of its page, so this doubles as a
#: page-furniture filter: it excludes the footer page number.
MS_HEADER_Y_MAX = 90.0

#: ``"6."`` bare on a line, or ``"1. This question is about ..."``. The mark
#: scheme spells a heading the same way the question paper does, so it reuses
#: :func:`question_heading` / :data:`QUESTION_RE` directly.



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


def question_heading(text: str) -> tuple[int, str] | None:
    """Return ``(question_number, trailing_text)`` for a question heading.

    Shared by the question paper and the mark scheme, because both use the same
    two historical spellings of a heading (see :data:`QUESTION_RE`).
    """
    m = QUESTION_RE.match(text)
    if not m:
        return None
    number = m.group(1) or m.group(2)
    return int(number), (m.group(3) or "").strip()


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


def _cell_text(rows, idx: int, label_x: float, label_y: float) -> str:
    """The text sitting to the right of a label on the same line.

    A table row is written as two cells at one ``y`` — ``(i)`` then ``Cubane`` —
    so the label's own line carries no text and the row's content is a separate
    entry. Joining the entries to the right recovers ``"Cubane"``.
    """
    chunks: list[str] = []
    for y, x, text in rows[idx + 1 :]:
        if y > label_y + 1.5:
            break
        if abs(y - label_y) <= 1.5 and x > label_x + 1.0:
            chunks.append(text)
    return " ".join(chunks).strip()


def _looks_like_table_cell(cell: str) -> bool:
    """Whether a label's right-hand text is a table cell rather than a question."""
    tokens = cell.split()
    if not tokens or len(tokens) > TABLE_CELL_MAX_WORDS:
        return False
    return not INSTRUCTION_RE.match(cell)


def _drop_table_rows(labels: list[Label], cells: list[str], leads: list[str]) -> list[Label]:
    """Drop roman labels that are rows of a table, not sub-questions.

    ``(b) Complete the table in the answer booklet with the number of peaks in
    the 13C NMR spectrum of: (i) Cubane (ii) Cubane-carboxylic acid ...`` labels
    the rows of one table, and the mark scheme grades that table as a single item
    ("3 marks for all five correct"), so the rows are not sub-questions and must
    not become records of their own. The same holds for a multi-column table such
    as ``(i) AlP / (iv) HgO / (ii) CsH ...``.

    Two things have to hold. A run of consecutive roman labels is a table when its
    *first* label carries a cell to its right — judging by the first entry keeps
    the run together even when a later row is long enough to read as prose, and
    leaves a run of genuine sub-questions alone because those open with an
    instruction. The run's lead-in must also announce a table, which keeps a list
    of items that merely share a stem ("Write the number of conjugated C=C bonds
    in: (i) ... (ii) ...", marked one mark each) as the separate sub-questions the
    mark scheme scores them as.
    """
    keep = [True] * len(labels)
    i = 0
    while i < len(labels):
        if labels[i].kind != "subpart":
            i += 1
            continue
        j = i
        while j + 1 < len(labels) and labels[j + 1].kind == "subpart":
            j += 1
        if (
            j > i
            and _looks_like_table_cell(cells[i])
            and TABLE_LEAD_IN_RE.search(leads[i])
        ):
            for k in range(i, j + 1):
                keep[k] = False
        i = j + 1
    return [label for label, kept in zip(labels, keep) if kept]


def find_labels(doc) -> list[Label]:
    """Detect every question / part / sub-part label, in document order."""
    labels: list[Label] = []
    cells: list[str] = []  # text sitting to the right of each label, if any
    leads: list[str] = []  # text between a sub-part label and its enclosing label
    for pno in range(doc.page_count):
        rows = _lines_in_order(doc[pno])
        anchor_ri = -1  # row index of the last question/part label on this page
        anchor_rest = ""  # text sharing that label's own line
        for idx, (y, x, text) in enumerate(rows):
            if x <= LEFT_X_MAX:
                head = question_heading(text)
                if head:
                    number, rest = head
                    if CREDITS_RE.match(rest):
                        continue  # image-credits page, not a real question
                    labels.append(
                        Label(
                            kind="question",
                            page=pno,
                            y=y,
                            x=x,
                            text=text,
                            question=number,
                            rest=rest,
                        )
                    )
                    cells.append("")
                    leads.append("")
                    anchor_ri = idx
                    anchor_rest = rest
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
                    cells.append("")
                    leads.append("")
                    anchor_ri = idx
                    anchor_rest = (p.group(2) or "").strip()
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
                    cells.append(_cell_text(rows, idx, x, y))
                    leads.append(
                        " ".join(
                            [anchor_rest]
                            + [t for _y, _x, t in rows[anchor_ri + 1 : idx]]
                        ).strip()
                        if anchor_ri >= 0
                        else ""
                    )
    return _drop_table_rows(labels, cells, leads)


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


# --- mark scheme splitting ------------------------------------------------


def find_ms_labels(doc) -> list[Label]:
    """Detect mark-scheme question / part / sub-part labels, in document order.

    Reuses :class:`Label`, but with MS geometry. A left-margin label is recorded
    as a ``part`` (even a roman one — see the module notes) and only an *indented*
    label is a ``subpart``. A sub-part carries its parent's letter in ``part``, so
    a label is self-describing without re-scanning the sequence.
    """
    labels: list[Label] = []
    current_part: str | None = None
    for pno in range(doc.page_count):
        for y, x, text in _lines_in_order(doc[pno]):
            if x > MS_SUBPART_X_MAX:
                continue  # MS answer columns and the right-hand mark column
            if y <= MS_HEADER_Y_MAX and x <= MS_LEFT_X_MAX:
                head = question_heading(text)
                if head:
                    number, rest = head
                    current_part = None
                    labels.append(
                        Label(
                            kind="question",
                            page=pno,
                            y=y,
                            x=x,
                            text=text,
                            question=number,
                            rest=rest,
                        )
                    )
                    continue
            if x <= MS_LEFT_X_MAX:
                p = PART_RE.match(text)
                if p:
                    current_part = p.group(1)
                    labels.append(
                        Label(kind="part", page=pno, y=y, x=x, text=text, part=p.group(1))
                    )
                    continue
                s = SUBPART_RE.match(text)
                if s:
                    # A multi-letter roman at the margin is a question-level part.
                    current_part = s.group(1)
                    labels.append(
                        Label(kind="part", page=pno, y=y, x=x, text=text, part=s.group(1))
                    )
                    continue
            elif x >= MS_SUBPART_X_MIN:
                s = SUBPART_RE.match(text)
                if s:
                    labels.append(
                        Label(
                            kind="subpart",
                            page=pno,
                            y=y,
                            x=x,
                            text=text,
                            part=current_part,
                            subpart=s.group(1),
                        )
                    )
    return labels


def mark_scheme_bands(
    doc, parts: list[Part]
) -> dict[str, tuple[int, float, int, float]]:
    """Map each QP part key to its MS band ``(page, y, end_page, end_y)``.

    The MS label stream cannot say whether ``(i)`` is a part or a sub-part, so the
    QP's known part list decides: each part is looked up by its own label.

    The MS is not always as finely divided as the question paper — it routinely
    answers ``(d)(i)`` and ``(d)(ii)`` under a single ``(d)``. A part with no MS
    label of its own therefore falls back to its parent part's *full* extent, which
    is the region the shared answer actually occupies. An earlier version advanced
    a cursor through the MS labels instead, which silently mis-aligned the whole
    question from there on: it consumed ``(f)``'s sub-part labels to satisfy
    ``(d)(i)`` and lost every later part.

    A part whose label is genuinely absent from the MS gets no band at all, so the
    gap stays visible instead of becoming a wrong clip.
    """
    labels = find_ms_labels(doc)

    heading: dict[int, tuple[int, float]] = {}
    for lb in labels:
        if lb.kind == "question" and lb.question is not None:
            heading.setdefault(lb.question, (lb.page, lb.y))
    ordered_q = sorted(heading.items(), key=lambda kv: kv[1])

    by_q: dict[int, list[Label]] = {}
    current: int | None = None
    for lb in labels:
        if lb.kind == "question":
            current = lb.question
            continue
        if current is not None:
            by_q.setdefault(current, []).append(lb)

    # A question's MS runs to the next question's heading. The final question has
    # no successor, so it runs to the last page that actually carries its labels —
    # using the heading's page would invert the band when (as here) the last part
    # sits on a later page than its own heading.
    q_end: dict[int, tuple[int, float]] = {}
    for i, (q, start) in enumerate(ordered_q):
        if i + 1 < len(ordered_q):
            q_end[q] = ordered_q[i + 1][1]
        else:
            last = max((lb.page for lb in by_q.get(q, [])), default=start[0])
            q_end[q] = (last, _page_height(doc, last))

    bands: dict[str, tuple[int, float, int, float]] = {}
    for part in parts:
        seq = by_q.get(part.question) or []
        if not seq:
            continue
        stop_page, stop_y = q_end.get(
            part.question, (seq[-1].page, _page_height(doc, seq[-1].page))
        )
        #: The (part, sub-part) pairs the question paper actually asks for. The MS
        #: sometimes labels rows of an answer table ("(i) I  (ii) E ...") that are
        #: not sub-questions, and a band must run past those rather than stop at
        #: them — otherwise Q2(d) would show only its first row.
        claimed = {
            (other.part, other.subpart) for other in parts if other.question == part.question
        }

        def band_from(
            i: int, end_page: int, end_y: float
        ) -> tuple[int, float, int, float]:
            """The band of label ``i``, ending at the given boundary.

            The boundary reuses the QP's page-break rule, so a band never becomes a
            sliver of the next page's header.
            """
            lb = seq[i]
            boundary = Label(kind="question", page=end_page, y=end_y, x=0.0, text="")
            ep, ey = _part_end(doc, lb, boundary)
            return (lb.page, lb.y, ep, ey)

        def next_boundary(i: int) -> tuple[int, float]:
            """The next label position strictly after label ``i``.

            Labels sharing a line must be skipped. The MS writes a compound label
            such as ``(a)(i)`` as two labels at the same ``y``, and ending a band at
            its own line would produce a zero-height (blank) clip.

            A sub-part label the question paper never asks for is skipped too: it
            labels a row of an answer table, and it belongs inside the band of the
            part it sits under.
            """
            pos = (seq[i].page, seq[i].y)
            for j in range(i + 1, len(seq)):
                lb = seq[j]
                if (lb.page, lb.y) <= pos:
                    continue
                if lb.subpart is None or (lb.part, lb.subpart) in claimed:
                    return lb.page, lb.y
            return stop_page, stop_y

        def tight(i: int) -> tuple[int, float, int, float]:
            ep, ey = next_boundary(i)
            return band_from(i, ep, ey)

        def whole_part(i: int) -> tuple[int, float, int, float]:
            """A part label's full extent, absorbing its sub-parts: it runs to the
            next part-level label, not to the next label of any kind."""
            pos = (seq[i].page, seq[i].y)
            for j in range(i + 1, len(seq)):
                if seq[j].subpart is None and (seq[j].page, seq[j].y) > pos:
                    return band_from(i, seq[j].page, seq[j].y)
            return band_from(i, stop_page, stop_y)

        i = next(
            (
                j
                for j, lb in enumerate(seq)
                if lb.part == part.part and lb.subpart == part.subpart
            ),
            None,
        )
        if i is not None:
            bands[part.key] = tight(i)
            continue

        if part.subpart is not None:
            # The MS answers this sub-part under its parent part, so pull the
            # parent's full extent rather than dropping the clip.
            j = next(
                (
                    j
                    for j, lb in enumerate(seq)
                    if lb.part == part.part and lb.subpart is None
                ),
                None,
            )
            if j is not None:
                bands[part.key] = whole_part(j)
    return bands


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
    ms_pdf: Path | None = None,
) -> dict[str, Any]:
    """Extract one UKChO paper: split parts, render clips, write a manifest JSON.

    Pass ``ms_pdf`` to also render one mark-scheme clip per part, named
    ``<prefix>-<key>-ms.png`` (``-ms-2.png`` when a band runs over a page break).
    The MS is a separate PDF with its own layout, so its bands are matched against
    the parts found in the QP — see :func:`mark_scheme_bands`.

    Output layout::

        out_dir/
          parts.json          # machine-readable split
          parts/<prefix>-<key>.txt
          clips/<prefix>-<key>-paper.png
          clips/<prefix>-<key>-ms.png

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

    ms_doc = None
    ms_bands: dict[str, tuple[int, float, int, float]] = {}
    if ms_pdf is not None and Path(ms_pdf).exists():
        ms_doc = fitz.open(Path(ms_pdf))
        ms_bands = mark_scheme_bands(ms_doc, parts)
        manifest["source_ms"] = str(ms_pdf)

    try:
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
            entry["ms_clips"] = []
            band = ms_bands.get(part.key)
            if make_clips and ms_doc is not None and band is not None:
                # A Part is just a page span, so the QP renderer does the MS too.
                ms_part = Part(
                    question=part.question,
                    part=part.part,
                    subpart=part.subpart,
                    page=band[0],
                    y=band[1],
                    text="",
                    end_page=band[2],
                    end_y=band[3],
                )
                ms_png = clip_dir / f"{clip_prefix}-{part.key}-ms.png"
                entry["ms_clips"] = render_part_clip(
                    ms_doc, ms_part, ms_png, zoom=zoom
                )
            manifest["parts"].append(entry)
    finally:
        doc.close()
        if ms_doc is not None:
            ms_doc.close()

    (out_dir / "parts.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def load_manifest(out_dir: Path) -> dict[str, Any]:
    return json.loads((Path(out_dir) / "parts.json").read_text(encoding="utf-8"))


def iter_part_dicts(manifest: dict[str, Any]) -> Iterable[dict[str, Any]]:
    return manifest.get("parts") or []
