"""End-to-end ingest for one past paper (batch-friendly)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chembank.examiner_report import (
    extract_examiner_report,
    merge_er_into_tagged_dir,
    write_examiner_report_json,
)
from chembank.export_vault import export_paper_to_vault
from chembank.extract import extract_pdf_text, write_extracted_text
from chembank.registry import (
    IngestResult,
    PaperRef,
    default_questions_dir_for_paper,
    default_vault_for_paper,
    infer_status,
    paper_kind,
    resolve_existing,
    upsert_paper,
    write_manifest,
)
from chembank.split import write_split_output


def run_pipeline(ref: PaperRef, *, draft_root: Path | None = None) -> Path:
    """Extract QP (+ MS) and split into draft/<paper_id>/qN.txt."""
    qp = Path(ref.qp)
    draft_root = Path(draft_root or Path(ref.draft).parent)
    stem = ref.id
    text_path = draft_root / f"{stem}.txt"
    split_dir = draft_root / stem

    write_extracted_text(qp, text_path)
    ms_text = None
    if ref.ms and Path(ref.ms).is_file():
        ms = Path(ref.ms)
        # Structured MS tables are scrambled by symbol recovery — prefer plain text
        # so part headers like ``2(a)(i)`` stay on their own lines.
        recover = paper_kind(ref.paper) == "mcq"
        ms_text = extract_pdf_text(ms, recover_symbols=recover)
        (draft_root / f"{ms.stem}.txt").write_text(ms_text, encoding="utf-8")

    chunks = write_split_output(
        text_path.read_text(encoding="utf-8"),
        split_dir,
        source_name=stem,
        mark_scheme_text=ms_text,
        # Paper 3 practical: topic / main-question grain (not fine parts)
        part_level=False if paper_kind(ref.paper) == "practical" else None,
    )
    if not chunks:
        raise RuntimeError(f"Split produced 0 questions for {stem}")
    return split_dir


def maybe_er_extract(ref: PaperRef, *, force: bool = False) -> Path | None:
    """Extract Examiner Report for this paper if PDF exists."""
    if not ref.er or not Path(ref.er).is_file():
        return None
    out = Path("draft") / "er" / f"{ref.syllabus_code}_{ref.season}_er_{ref.paper}.json"
    if out.is_file() and not force:
        return out
    data = extract_examiner_report(Path(ref.er), paper=str(ref.paper))
    # Keep PDF in place (already under raw/reports/); do not re-copy
    written = write_examiner_report_json(data, out, paper=str(ref.paper))
    return written


def maybe_er_merge(ref: PaperRef, er_json: Path | None) -> int:
    """Merge ER into tagged/ if both exist. Returns number of files updated."""
    tagged = Path(ref.draft) / "tagged"
    if er_json is None or not er_json.is_file() or not tagged.is_dir():
        return 0
    if not any(tagged.glob("q*.json")):
        return 0
    er_data = json.loads(er_json.read_text(encoding="utf-8"))
    updated = merge_er_into_tagged_dir(
        tagged,
        er_data,
        paper=str(ref.paper),
        source_path=ref.er or str(er_json),
    )
    return len(updated)


def maybe_export(
    ref: PaperRef,
    *,
    vault: Path | None = None,
    export_md: Path | None = None,
    refresh: bool = True,
) -> dict[str, Any] | None:
    """Export to vault if tagged JSON exists."""
    tagged = Path(ref.draft) / "tagged"
    if not tagged.is_dir() or not any(tagged.glob("q*.json")):
        return None
    vault_dir = Path(vault) if vault is not None else default_vault_for_paper(ref.paper)
    questions = (
        Path(export_md)
        if export_md is not None
        else default_questions_dir_for_paper(ref.paper)
    )
    return export_paper_to_vault(
        qp_pdf=Path(ref.qp),
        draft_dir=Path(ref.draft),
        vault_dir=vault_dir,
        questions_dir=questions,
        refresh_extract=refresh,
        ms_pdf=Path(ref.ms) if ref.ms else None,
    )


def ingest_paper(
    ref: PaperRef,
    *,
    export: bool = True,
    er: bool = True,
    force_er: bool = False,
    vault: Path | None = None,
    export_md: Path | None = None,
    refresh_on_export: bool = True,
    update_registry: bool = True,
    registry_path: Path | None = None,
) -> IngestResult:
    """
    Run extract → split → (optional er-extract/merge) → (optional export-vault).

    Tagging is intentionally separate (Cursor skill / `chembank tag`).
    Export runs only when `draft/<id>/tagged/` already has q*.json.
    Vault defaults: 1x → ``vault/``; 2/4/5x → ``vault-structured/``; 3x → ``vault-practical/``.
    """
    ref = resolve_existing(ref, require_qp=True)
    result = IngestResult(paper_id=ref.id, draft_dir=ref.draft)
    kind = paper_kind(ref.paper)
    vault_dir = Path(vault) if vault is not None else default_vault_for_paper(ref.paper)
    questions_dir = (
        Path(export_md)
        if export_md is not None
        else default_questions_dir_for_paper(ref.paper)
    )
    result.messages.append(
        f"kind={kind} vault={vault_dir} export_md={questions_dir}"
    )

    split_dir = run_pipeline(ref)
    result.steps.append("pipeline")
    result.messages.append(f"Extracted + split → {split_dir}")

    er_json = None
    if er:
        er_json = maybe_er_extract(ref, force=force_er)
        if er_json:
            result.steps.append("er-extract")
            result.er_json = str(er_json)
            result.messages.append(f"ER JSON → {er_json}")
        else:
            result.messages.append("No Examiner Report PDF for this year/session (skipped)")

    merged = maybe_er_merge(ref, er_json) if er else 0
    if merged:
        result.steps.append("er-merge")
        result.messages.append(f"Merged ER into {merged} tagged question(s)")

    if export:
        # Pipeline already refreshed extract/split in this call — avoid a second pass
        # unless the caller skipped pipeline somehow (not the case here).
        exported = maybe_export(
            ref,
            vault=vault_dir,
            export_md=questions_dir,
            refresh=False if "pipeline" in result.steps else refresh_on_export,
        )
        if exported:
            result.steps.append("export-vault")
            result.exported = int(exported.get("questions") or 0)
            result.messages.append(
                f"Exported {result.exported} questions → {vault_dir}/questions/"
            )
        else:
            if kind == "mcq":
                tag_skill = "chembank-syllabus-tag"
            elif kind == "practical":
                tag_skill = "chembank-practical-tag"
            else:
                tag_skill = "chembank-structured-tag"
            result.messages.append(
                "No tagged JSON yet — skip export. "
                f"Tag with {tag_skill} skill (or `chembank tag`), then re-run "
                f"`chembank ingest {ref.season} {ref.paper} --export`"
            )

    status = infer_status(Path(ref.draft), paper=ref)
    if result.exported:
        status = "exported"
    ref.status = status
    result.status = status

    if update_registry:
        upsert_paper(ref, registry_path)
        write_manifest(registry_path=registry_path)
        result.steps.append("registry")

    return result


def ingest_many(
    refs: list[PaperRef],
    **kwargs: Any,
) -> list[IngestResult]:
    """Ingest papers sequentially; collect per-paper results."""
    results: list[IngestResult] = []
    for ref in refs:
        results.append(ingest_paper(ref, **kwargs))
    return results
