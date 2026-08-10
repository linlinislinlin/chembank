"""Paper registry + path conventions for batch ingest."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

DEFAULT_PAPERS_YAML = Path("papers.yaml")
DEFAULT_MANIFEST = Path("draft/manifest.json")
DEFAULT_VAULT_MCQ = Path("vault")
DEFAULT_VAULT_STRUCTURED = Path("vault-structured")
DEFAULT_VAULT_PRACTICAL = Path("vault-practical")
DEFAULT_QUESTIONS_MCQ = Path("questions")
DEFAULT_QUESTIONS_STRUCTURED = Path("questions-structured")
DEFAULT_QUESTIONS_PRACTICAL = Path("questions-practical")

# CIE season letter in filenames: s=June(MJ), w=Nov(ON), m=March(FM)
_SESSION_FROM_SEASON = {"s": "MJ", "w": "ON", "m": "FM"}
_SEASON_FROM_SESSION = {"MJ": "s", "ON": "w", "FM": "m"}

# Paper component (tens digit): 1=MCQ, 2/4/5=structured SAQ, 3=practical
_MCQ_COMPONENTS = {1}
_STRUCTURED_COMPONENTS = {2, 4, 5}
_PRACTICAL_COMPONENTS = {3}

_PAPER_STEM_RE = re.compile(
    r"^(?P<code>\d{4})_(?P<letter>[smw])(?P<yy>\d{2})_qp_(?P<paper>\d{1,2})$",
    re.I,
)
_SEASON_RE = re.compile(r"^(?P<letter>[smw])(?P<yy>\d{2})$", re.I)
_SHORT_REF_RE = re.compile(
    r"^(?:(?P<code>\d{4})[_-])?(?P<season>[smw]\d{2})[:_\s-](?P<paper>\d{1,2})$",
    re.I,
)


@dataclass
class PaperRef:
    """One past paper (QP + MS + optional ER)."""

    id: str
    year: int
    session: str  # MJ / ON / FM
    season: str  # s21 / w21 / m21
    paper: int | str
    board: str = "CIE"
    syllabus_code: str = "9701"
    qp: str = ""
    ms: str = ""
    er: str | None = None
    draft: str = ""
    status: str = "pending"  # pending | extracted | tagged | exported
    notes: str = ""
    updated_at: str = ""

    def paper_str(self) -> str:
        return str(self.paper)


def season_token(session: str, year: int) -> str:
    """MJ/ON/FM + year → s21 / w21 / m21."""
    yy = year % 100
    letter = _SEASON_FROM_SESSION.get(session.upper())
    if not letter:
        raise ValueError(f"Unknown session {session!r}; use MJ, ON, or FM")
    return f"{letter}{yy:02d}"


def parse_season(season: str) -> tuple[str, int, str]:
    """Parse `s21` → (letter, year, session)."""
    m = _SEASON_RE.fullmatch(season.strip())
    if not m:
        raise ValueError(f"Bad season token {season!r}; expected s21 / w21 / m21")
    letter = m.group("letter").lower()
    yy = int(m.group("yy"))
    year = 2000 + yy if yy < 80 else 1900 + yy
    session = _SESSION_FROM_SEASON[letter]
    return letter, year, session


def paper_id(syllabus_code: str, season: str, paper: int | str) -> str:
    return f"{syllabus_code}_{season.lower()}_qp_{paper}"


def paper_component(paper: int | str) -> int:
    """CIE component from paper code: 11→1, 21→2, 42→4."""
    n = int(paper)
    if n < 10:
        return n
    return n // 10


def paper_kind(paper: int | str) -> str:
    """Return ``mcq`` (1x), ``structured`` (2/4/5x), or ``practical`` (3x)."""
    comp = paper_component(paper)
    if comp in _MCQ_COMPONENTS:
        return "mcq"
    if comp in _PRACTICAL_COMPONENTS:
        return "practical"
    if comp in _STRUCTURED_COMPONENTS:
        return "structured"
    # Fallback: treat unknown as structured (safer than MCQ A–D gates)
    return "structured"


def default_vault_for_paper(paper: int | str) -> Path:
    """Obsidian vault root for this paper number."""
    kind = paper_kind(paper)
    if kind == "mcq":
        return DEFAULT_VAULT_MCQ
    if kind == "practical":
        return DEFAULT_VAULT_PRACTICAL
    return DEFAULT_VAULT_STRUCTURED


def default_questions_dir_for_paper(paper: int | str) -> Path:
    """Canonical Markdown dual-write dir for this paper number."""
    kind = paper_kind(paper)
    if kind == "mcq":
        return DEFAULT_QUESTIONS_MCQ
    if kind == "practical":
        return DEFAULT_QUESTIONS_PRACTICAL
    return DEFAULT_QUESTIONS_STRUCTURED


def default_paths(
    *,
    syllabus_code: str = "9701",
    season: str,
    paper: int | str,
    year: int | None = None,
    papers_dir: Path = Path("raw/papers"),
    reports_dir: Path = Path("raw/reports"),
    draft_root: Path = Path("draft"),
) -> PaperRef:
    """Build a PaperRef from naming convention (files may not exist yet)."""
    season = season.lower()
    _, inferred_year, session = parse_season(season)
    year = year or inferred_year
    pid = paper_id(syllabus_code, season, paper)
    er_name = f"{syllabus_code}_{year}_{season}_er.pdf"
    return PaperRef(
        id=pid,
        year=year,
        session=session,
        season=season,
        paper=int(paper) if str(paper).isdigit() else paper,
        syllabus_code=syllabus_code,
        qp=str(papers_dir / f"{pid}.pdf"),
        ms=str(papers_dir / f"{syllabus_code}_{season}_ms_{paper}.pdf"),
        er=str(reports_dir / er_name),
        draft=str(draft_root / pid),
        status="pending",
    )


def parse_paper_ref(
    *parts: str,
    syllabus_code: str = "9701",
) -> PaperRef:
    """Parse CLI refs: `9701_s21_qp_12`, `s21 12`, `s21:12`, `9701-s21-12`."""
    if not parts:
        raise ValueError("Need a paper reference (e.g. s21 12 or 9701_s21_qp_12)")
    joined = " ".join(p.strip() for p in parts if p.strip())
    # Full stem
    m = _PAPER_STEM_RE.fullmatch(joined.replace(" ", "_").replace("-", "_"))
    if m:
        return default_paths(
            syllabus_code=m.group("code"),
            season=f"{m.group('letter').lower()}{m.group('yy')}",
            paper=m.group("paper"),
        )
    # Compact: s21:12 / s21 12 / 9701_s21_12
    compact = joined.replace(" ", ":")
    m2 = _SHORT_REF_RE.fullmatch(compact.replace("_", ":").replace("-", ":"))
    if m2:
        code = m2.group("code") or syllabus_code
        return default_paths(
            syllabus_code=code,
            season=m2.group("season").lower(),
            paper=m2.group("paper"),
        )
    # Two tokens: season paper
    if len(parts) == 2:
        return default_paths(
            syllabus_code=syllabus_code,
            season=parts[0],
            paper=parts[1],
        )
    raise ValueError(
        f"Cannot parse paper ref {joined!r}. "
        "Use: chembank ingest s21 12   or   chembank ingest 9701_s21_qp_12"
    )


def resolve_existing(ref: PaperRef, *, require_qp: bool = True) -> PaperRef:
    """Fill er=None when ER PDF missing; optionally require QP/MS on disk."""
    qp = Path(ref.qp)
    ms = Path(ref.ms)
    er_path = Path(ref.er) if ref.er else None
    if require_qp and not qp.is_file():
        raise FileNotFoundError(
            f"QP not found: {qp}\n"
            f"Place it as: raw/papers/{ref.id}.pdf"
        )
    if require_qp and not ms.is_file():
        raise FileNotFoundError(
            f"MS not found: {ms}\n"
            f"Place it as: raw/papers/{ref.syllabus_code}_{ref.season}_ms_{ref.paper}.pdf"
        )
    if er_path is None or not er_path.is_file():
        # Try alternate discovery
        reports = Path("raw/reports")
        pattern = f"{ref.syllabus_code}_{ref.year}_{ref.season}_er.pdf"
        alt = reports / pattern
        ref.er = str(alt) if alt.is_file() else None
    else:
        ref.er = str(er_path)
    return ref


def load_papers_yaml(path: Path | None = None) -> dict[str, Any]:
    path = Path(path or DEFAULT_PAPERS_YAML)
    if not path.is_file():
        return {
            "board": "CIE",
            "syllabus": "9701",
            "papers": [],
        }
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("board", "CIE")
    data.setdefault("syllabus", "9701")
    data.setdefault("papers", [])
    return data


def save_papers_yaml(data: dict[str, Any], path: Path | None = None) -> Path:
    path = Path(path or DEFAULT_PAPERS_YAML)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# ChemBank paper registry — add a row when you drop new QP/MS PDFs.\n"
        "# Naming: raw/papers/9701_<season>_qp_<paper>.pdf\n"
        "#          raw/papers/9701_<season>_ms_<paper>.pdf\n"
        "#          raw/reports/9701_<year>_<season>_er.pdf\n"
        "# status: pending | extracted | tagged | exported\n"
        "#\n"
        "# Vaults (auto by paper number):\n"
        "#   Paper 1x (11/12/13) MCQ           → vault/\n"
        "#   Paper 2/4/5x structured SAQ      → vault-structured/\n"
        "#   Paper 3x (31/32/33…) practical   → vault-practical/\n"
        "#\n"
        "# MCQ example (s21 qp12):\n"
        "#   chembank ingest s21 12\n"
        "#   # tag via chembank-syllabus-tag skill\n"
        "#   chembank ingest s21 12 --export\n"
        "#\n"
        "# Structured example (s21 qp21):\n"
        "#   chembank ingest s21 21\n"
        "#   # tag via chembank-structured-tag skill\n"
        "#   chembank ingest s21 21 --export   # → vault-structured/\n"
        "#\n"
        "# Practical example (s21 qp31):\n"
        "#   chembank ingest s21 31\n"
        "#   # tag via chembank-practical-tag skill (topic grain)\n"
        "#   chembank ingest s21 31 --export   # → vault-practical/\n"
    )
    body = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    path.write_text(header + body, encoding="utf-8")
    return path


def upsert_paper(ref: PaperRef, path: Path | None = None) -> Path:
    """Insert or update a paper entry in papers.yaml."""
    data = load_papers_yaml(path)
    papers: list[dict[str, Any]] = list(data.get("papers") or [])
    ref.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {k: v for k, v in asdict(ref).items() if v is not None and v != ""}
    found = False
    for i, row in enumerate(papers):
        if row.get("id") == ref.id:
            papers[i] = {**row, **payload}
            found = True
            break
    if not found:
        papers.append(payload)
    # Stable sort: year, season, paper
    papers.sort(
        key=lambda r: (
            int(r.get("year") or 0),
            str(r.get("season") or ""),
            int(r.get("paper") or 0),
        )
    )
    data["papers"] = papers
    return save_papers_yaml(data, path)


def paper_from_row(row: dict[str, Any]) -> PaperRef:
    return PaperRef(
        id=str(row["id"]),
        year=int(row["year"]),
        session=str(row.get("session") or "MJ"),
        season=str(row["season"]),
        paper=row["paper"],
        board=str(row.get("board") or "CIE"),
        syllabus_code=str(row.get("syllabus_code") or row.get("syllabus") or "9701"),
        qp=str(row.get("qp") or ""),
        ms=str(row.get("ms") or ""),
        er=row.get("er"),
        draft=str(row.get("draft") or f"draft/{row['id']}"),
        status=str(row.get("status") or "pending"),
        notes=str(row.get("notes") or ""),
        updated_at=str(row.get("updated_at") or ""),
    )


def list_registry_papers(path: Path | None = None) -> list[PaperRef]:
    data = load_papers_yaml(path)
    return [paper_from_row(r) for r in data.get("papers") or []]


def write_manifest(
    refs: list[PaperRef] | None = None,
    path: Path | None = None,
    registry_path: Path | None = None,
) -> Path:
    """Machine-readable snapshot under draft/manifest.json."""
    import json

    path = Path(path or DEFAULT_MANIFEST)
    if refs is None:
        refs = list_registry_papers(registry_path)
    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "papers": [asdict(r) for r in refs],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def infer_status(draft_dir: Path, *, paper: PaperRef | None = None) -> str:
    """Best-effort status from filesystem."""
    draft_dir = Path(draft_dir)
    tagged = draft_dir / "tagged"
    if not draft_dir.is_dir() or not any(draft_dir.glob("q*.txt")):
        return "pending"
    if not tagged.is_dir() or not any(tagged.glob("q*.json")):
        return "extracted"
    # Prefer exported when vault notes already exist for this paper
    if paper is not None:
        sess = {"MJ": "mj", "ON": "on", "FM": "fm"}.get(paper.session.upper(), paper.session.lower())
        pattern = f"cie-9701-{paper.year}-{sess}-p{paper.paper}-q*.md"
        vault = default_vault_for_paper(paper.paper)
        if list((vault / "questions").glob(pattern)):
            return "exported"
        # Legacy: some early exports may still sit under vault/ only
        if vault != DEFAULT_VAULT_MCQ and list(Path("vault/questions").glob(pattern)):
            return "exported"
    return "tagged"


@dataclass
class IngestResult:
    paper_id: str
    steps: list[str] = field(default_factory=list)
    draft_dir: str = ""
    er_json: str | None = None
    exported: int = 0
    status: str = "pending"
    messages: list[str] = field(default_factory=list)
