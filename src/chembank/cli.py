"""CLI for extract / split / tag / syllabus helpers / batch ingest."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
import webbrowser

from chembank.audit import audit_papers, format_audit_report
from chembank.examiner_report import (
    extract_examiner_report,
    merge_er_into_tagged_dir,
    suggested_pdf_name,
    write_examiner_report_json,
)
from chembank.extract import write_extracted_text
from chembank.export_md import export_all_lo_hubs
from chembank.export_vault import export_paper_to_vault
from chembank.ingest import ingest_many, ingest_paper
from chembank.registry import (
    DEFAULT_PAPERS_YAML,
    default_questions_dir_for_paper,
    default_vault_for_paper,
    list_registry_papers,
    paper_kind,
    parse_paper_ref,
    resolve_existing,
    resolve_registry_path,
    write_manifest,
)
from chembank.select import load_rules, select_questions, write_pick
from chembank.assemble import render_tiles
from chembank.split import parse_mcq_mark_scheme, write_split_output
from chembank.syllabus import (
    DEFAULT_SYLLABUS,
    as_only_codes,
    as_only_learning_outcomes,
    list_codes,
    list_learning_outcomes,
    load_syllabus,
)
from chembank.tag import infer_paper_meta_from_name, parse_paper_meta_string, tag_draft_dir
from chembank.ukcho import parse_frontmatter as parse_ukcho_frontmatter


def _cmd_extract(args: argparse.Namespace) -> int:
    out = write_extracted_text(Path(args.pdf), Path(args.output))
    print(f"Wrote {out}")
    return 0


def _cmd_split(args: argparse.Namespace) -> int:
    text = Path(args.text).read_text(encoding="utf-8")
    ms_text = None
    if args.mark_scheme:
        ms_path = Path(args.mark_scheme)
        if ms_path.suffix.lower() == ".pdf":
            from chembank.extract import extract_pdf_text

            ms_text = extract_pdf_text(ms_path)
        else:
            ms_text = ms_path.read_text(encoding="utf-8")
    chunks = write_split_output(
        text,
        Path(args.output),
        source_name=Path(args.text).name,
        mark_scheme_text=ms_text,
    )
    print(f"Split {len(chunks)} questions -> {args.output}")
    if chunks:
        style = chunks[0].paper_style
        nums = [c.question for c in chunks]
        print(f"style={style} questions={nums[0]}..{nums[-1]}")
    return 0


def _cmd_pipeline(args: argparse.Namespace) -> int:
    qp = Path(args.question_paper)
    stem = qp.stem
    draft = Path(args.draft_dir)
    text_path = draft / f"{stem}.txt"
    split_dir = draft / stem
    write_extracted_text(qp, text_path)
    print(f"Extracted {qp} -> {text_path}")

    ms_text = None
    if args.mark_scheme:
        ms = Path(args.mark_scheme)
        if ms.suffix.lower() == ".pdf":
            from chembank.extract import extract_pdf_text

            ms_text = extract_pdf_text(ms)
            (draft / f"{ms.stem}.txt").write_text(ms_text, encoding="utf-8")
        else:
            ms_text = ms.read_text(encoding="utf-8")

    text = text_path.read_text(encoding="utf-8")
    chunks = write_split_output(
        text,
        split_dir,
        source_name=stem,
        mark_scheme_text=ms_text,
    )
    print(f"Split {len(chunks)} questions -> {split_dir}")
    return 0


def _cmd_codes(args: argparse.Namespace) -> int:
    path = Path(args.syllabus) if args.syllabus else DEFAULT_SYLLABUS
    if getattr(args, "lo", False):
        return _print_learning_outcomes(args, path)
    rows = as_only_codes(path) if args.as_only else list_codes(path)
    if args.json:
        print(json.dumps([{"code": c, "title": t} for c, t in rows], ensure_ascii=False, indent=2))
    else:
        meta = load_syllabus(path).get("meta", {})
        print(f"# {meta.get('title', path.name)} ({len(rows)} codes)")
        for code, title in rows:
            print(f"{code}\t{title}")
    return 0


def _print_learning_outcomes(args: argparse.Namespace, path: Path) -> int:
    code = getattr(args, "code", None)
    if args.as_only and not code:
        rows = as_only_learning_outcomes(path)
    else:
        rows = list_learning_outcomes(path, code=code, as_only=args.as_only)
    if args.json:
        print(
            json.dumps(
                [{"id": i, "parent": p, "text": t} for i, p, t in rows],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        filt = f" code={code}" if code else ""
        print(f"# Learning outcomes ({len(rows)}{filt})")
        for lo_id, parent, text in rows:
            print(f"{lo_id}\t{parent}\t{text}")
    return 0


def _cmd_los(args: argparse.Namespace) -> int:
    path = Path(args.syllabus) if args.syllabus else DEFAULT_SYLLABUS
    return _print_learning_outcomes(args, path)


def _cmd_ms_key(args: argparse.Namespace) -> int:
    path = Path(args.mark_scheme)
    if path.suffix.lower() == ".pdf":
        from chembank.extract import extract_pdf_text

        text = extract_pdf_text(path)
    else:
        text = path.read_text(encoding="utf-8")
    key = parse_mcq_mark_scheme(text)
    print(json.dumps(key, ensure_ascii=False, indent=2))
    print(f"# {len(key)} answers", file=__import__("sys").stderr)
    return 0


def _resolve_vault_arg(
    args: argparse.Namespace, *, paper: int | str | None, syllabus_code: str = "9701"
) -> Path:
    """Use explicit --vault, else auto-detect from paper number + syllabus."""
    if getattr(args, "vault", None):
        return Path(args.vault)
    if paper is not None:
        return default_vault_for_paper(paper, syllabus_code)
    return Path("vault")


def _resolve_export_md_arg(
    args: argparse.Namespace,
    *,
    paper: int | str | None,
    syllabus_code: str = "9701",
) -> Path | None:
    if getattr(args, "export_md", None) is not None:
        raw = args.export_md
        if raw == "" or raw is False:
            return None
        return Path(raw)
    if paper is not None:
        return default_questions_dir_for_paper(paper, syllabus_code)
    return Path("questions")


def _ref_from_qp_or_draft(qp: Path | None, draft: Path | None):
    """Best-effort PaperRef from QP stem or draft folder name."""
    from chembank.registry import PaperRef

    for cand in (qp, draft):
        if cand is None:
            continue
        try:
            return parse_paper_ref(Path(cand).stem if Path(cand).suffix else Path(cand).name)
        except ValueError:
            continue
    return None


def _paper_from_qp_or_draft(qp: Path | None, draft: Path | None) -> int | str | None:
    ref = _ref_from_qp_or_draft(qp, draft)
    return None if ref is None else ref.paper


def _cmd_export_vault(args: argparse.Namespace) -> int:
    qp = Path(args.question_paper)
    draft = Path(args.draft)
    ref = _ref_from_qp_or_draft(qp, draft)
    paper = None if ref is None else ref.paper
    syl = "9701" if ref is None else ref.syllabus_code
    vault = _resolve_vault_arg(args, paper=paper, syllabus_code=syl)
    export_md = _resolve_export_md_arg(args, paper=paper, syllabus_code=syl)
    kind = paper_kind(paper, syl) if paper is not None else "unknown"
    result = export_paper_to_vault(
        qp_pdf=qp,
        draft_dir=draft,
        vault_dir=vault,
        questions_dir=export_md,
        refresh_extract=not args.no_refresh,
        ms_pdf=Path(args.mark_scheme) if args.mark_scheme else None,
    )
    print(f"Exported {result['questions']} questions [{kind}] -> {vault}")
    figs = result.get("figures") or {}
    print(f"Figures for {len(figs)} question(s) -> {result['assets_dir']}")
    from chembank.structured_parts import draft_stem_sort_key, parse_part_id

    def _fig_key(label: str) -> tuple:
        pid = parse_part_id(label)
        if pid:
            return pid.sort_key()
        if str(label).isdigit():
            return (int(label), "", 0)
        return draft_stem_sort_key(f"q{label}")

    for q, paths in sorted(figs.items(), key=lambda kv: _fig_key(kv[0])):
        print(f"  q{q}: {', '.join(paths)}")
    return 0


def _cmd_export_lo_hubs(args: argparse.Namespace) -> int:
    syllabus = Path(args.syllabus) if args.syllabus else None
    as_only = not args.all_levels
    if syllabus and "0620" in syllabus.name:
        as_only = False
    result = export_all_lo_hubs(
        Path(args.vault),
        as_only=as_only,
        code=args.code,
        syllabus_path=syllabus,
    )
    scope = f"code={args.code}" if args.code else ("AS" if not args.all_levels else "AS+A")
    print(f"Wrote {result['count']} LO hub(s) [{scope}] -> {result['lo_dir']}")
    return 0


def _cmd_er_extract(args: argparse.Namespace) -> int:
    pdf = Path(args.pdf)
    data = extract_examiner_report(pdf, paper=args.paper)
    year = int(data["year"])
    session = str(data["session"])

    # Copy PDF into year-scoped raw/reports/ (gitignored)
    if not args.no_copy:
        reports_dir = Path(args.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        dest_name = suggested_pdf_name(
            year, session, str(data.get("syllabus_code") or "9701")
        )
        dest = reports_dir / dest_name
        if pdf.resolve() != dest.resolve():
            shutil.copy2(pdf, dest)
            print(f"Copied PDF -> {dest}")
        data["source"] = str(dest)

    out = Path(args.output) if args.output else None
    written = write_examiner_report_json(data, out, paper=args.paper)
    print(f"Wrote ER JSON -> {written}")
    print(f"year={year} session={session} papers={sorted(data['papers'], key=int)}")
    for p, block in sorted(data["papers"].items(), key=lambda kv: int(kv[0])):
        st = block.get("stats") or {}
        print(
            f"  paper {p}: facility={st.get('questions_with_numeric_facility', 0)} "
            f"comments={st.get('questions_with_comments', 0)} "
            f"band_only={st.get('questions_with_band_only', 0)} "
            f"key={st.get('questions_total_in_key', 0)}"
        )
        print(
            f"    easy={block.get('easy_questions')} "
            f"difficult={block.get('difficult_questions')}"
        )
    return 0


def _cmd_er_merge(args: argparse.Namespace) -> int:
    er_path = Path(args.er_json)
    er_data = json.loads(er_path.read_text(encoding="utf-8"))
    tagged = Path(args.tagged)
    paper = args.paper
    if paper is None and len(er_data.get("papers") or {}) == 1:
        paper = next(iter(er_data["papers"]))
    source = args.source or er_data.get("source") or str(er_path)
    updated = merge_er_into_tagged_dir(
        tagged,
        er_data,
        paper=paper,
        source_path=source,
        update_difficulty=not args.no_difficulty,
    )
    print(f"Merged ER into {len(updated)} tagged question(s) under {tagged}")
    return 0


def _print_ingest_result(result) -> None:
    print(f"== {result.paper_id} [{result.status}] ==")
    print(f"  steps: {', '.join(result.steps) or '(none)'}")
    for msg in result.messages:
        print(f"  · {msg}")


def _cmd_ingest(args: argparse.Namespace) -> int:
    """Extract→split→(er)→(export) for one paper; update papers.yaml."""
    ref = parse_paper_ref(*args.paper_ref)
    if args.qp:
        ref.qp = args.qp
    if args.mark_scheme:
        ref.ms = args.mark_scheme
    if args.er_pdf:
        ref.er = args.er_pdf
    if args.draft:
        ref.draft = args.draft

    vault = Path(args.vault) if args.vault else None
    export_md = Path(args.export_md) if args.export_md is not None else None
    registry = resolve_registry_path(args.registry, ref.syllabus_code)

    result = ingest_paper(
        ref,
        export=bool(args.do_export),
        er=not args.no_er,
        force_er=args.force_er,
        vault=vault,
        export_md=export_md,
        refresh_on_export=not args.no_refresh,
        update_registry=not args.no_registry,
        registry_path=registry,
    )
    _print_ingest_result(result)
    return 0


def _cmd_batch(args: argparse.Namespace) -> int:
    """Ingest many papers from papers.yaml and/or CLI refs."""
    refs = []
    registry = Path(args.registry) if args.registry else DEFAULT_PAPERS_YAML

    if args.paper_ref:
        # Explicit list: chembank batch s21:11 s21:12
        for token in args.paper_ref:
            if ":" in token or "_" in token:
                refs.append(parse_paper_ref(token))
            else:
                raise SystemExit(
                    f"Batch ref {token!r} must look like s21:12 or 9701_s21_qp_12"
                )
        if refs:
            registry = resolve_registry_path(args.registry, refs[0].syllabus_code)
    else:
        registry = resolve_registry_path(args.registry, "9701")
        refs = list_registry_papers(registry)
        if args.status:
            want = {s.strip() for s in args.status.split(",") if s.strip()}
            refs = [r for r in refs if r.status in want]
        if args.limit:
            refs = refs[: args.limit]

    if not refs:
        print(
            "No papers to process. Add rows to papers.yaml or pass refs:\n"
            "  chembank batch s21:11 s21:12\n"
            "  chembank ingest s21 12   # registers one paper"
        )
        return 1

    # When --vault omitted, ingest each paper into its kind-specific vault.
    vault = Path(args.vault) if args.vault else None
    export_md = Path(args.export_md) if args.export_md is not None else None

    results = ingest_many(
        refs,
        export=bool(args.do_export),
        er=not args.no_er,
        force_er=args.force_er,
        vault=vault,
        export_md=export_md,
        refresh_on_export=not args.no_refresh,
        update_registry=not args.no_registry,
        registry_path=registry,
    )
    ok = 0
    for r in results:
        _print_ingest_result(r)
        if "pipeline" in r.steps:
            ok += 1
    print(f"Batch done: {ok}/{len(results)} papers pipelined")
    write_manifest(registry_path=registry)
    return 0 if ok == len(results) else 1


def _cmd_audit(args: argparse.Namespace) -> int:
    """Fail export quality gates (paper clips, LO, atom-salad, ER facility, …)."""
    from chembank.audit import AuditResult

    refs = list(args.paper_ref) if args.paper_ref else None
    check_pdf = not args.skip_pdf

    # Mixed P1/P2/P3 refs must hit their own vaults; a single --vault would miss most notes.
    if refs and args.vault is None:
        groups: dict[tuple[Path, Path | None], list[str]] = {}
        for token in refs:
            try:
                pref = parse_paper_ref(str(token))
            except ValueError:
                pref = None
            if pref is None:
                vault = Path("vault")
                qdir: Path | None = Path("questions")
            else:
                vault = default_vault_for_paper(pref.paper, pref.syllabus_code)
                qdir = (
                    Path(args.export_md)
                    if args.export_md is not None
                    else default_questions_dir_for_paper(pref.paper, pref.syllabus_code)
                )
            groups.setdefault((vault, qdir), []).append(str(token))
        result = AuditResult()
        looked = []
        for (vault, qdir), group_refs in groups.items():
            looked.append(str(vault / "questions"))
            part = audit_papers(
                vault_dir=vault,
                questions_dir=qdir,
                paper_refs=group_refs,
                check_pdf=check_pdf,
            )
            result.checked += part.checked
            result.passed += part.passed
            result.findings.extend(part.findings)
        print(format_audit_report(result))
        if result.checked == 0:
            print(
                "No vault questions matched. Export first, or pass refs like s21:11 / s21:21\n"
                f"(looked in {', '.join(looked)})"
            )
            return 2
        return 1 if result.failed else 0

    paper = None
    if refs:
        try:
            paper = parse_paper_ref(str(refs[0])).paper
        except ValueError:
            paper = None
    vault = _resolve_vault_arg(args, paper=paper)
    if args.export_md is not None:
        questions_dir: Path | None = Path(args.export_md)
    elif paper is not None:
        questions_dir = default_questions_dir_for_paper(paper)
    else:
        questions_dir = Path("questions")
    result = audit_papers(
        vault_dir=vault,
        questions_dir=questions_dir,
        paper_refs=refs,
        check_pdf=check_pdf,
    )
    print(format_audit_report(result))
    if result.checked == 0:
        print(
            "No vault questions matched. Export first, or pass refs like s21:11 / s21:21\n"
            f"(looked in {vault}/questions)"
        )
        return 2
    return 1 if result.failed else 0


def _cmd_papers(args: argparse.Namespace) -> int:
    """List or refresh the paper registry."""
    registry = Path(args.registry) if args.registry else DEFAULT_PAPERS_YAML
    refs = list_registry_papers(registry)
    if args.refresh_status:
        from chembank.registry import infer_status, upsert_paper

        for ref in refs:
            try:
                resolve_existing(ref, require_qp=False)
            except FileNotFoundError:
                pass
            ref.status = infer_status(Path(ref.draft), paper=ref)
            upsert_paper(ref, registry)
        refs = list_registry_papers(registry)
        write_manifest(registry_path=registry)
    if not refs:
        print(f"(empty) {registry} — run: chembank ingest s21 11")
        return 0
    for r in refs:
        er = "er" if r.er else "no-er"
        print(
            f"{r.id}\t{r.year}\t{r.session}\tp{r.paper}\t{r.status}\t{er}\t{r.qp}"
        )
    print(f"# {len(refs)} paper(s) in {registry}")
    return 0


def _cmd_tag(args: argparse.Namespace) -> int:
    draft = Path(args.draft)
    overrides = parse_paper_meta_string(args.paper_meta)
    meta = infer_paper_meta_from_name(draft.name)
    # Explicit --year / --session / --paper take precedence
    if args.year is not None:
        overrides["year"] = args.year
    if args.session:
        overrides["session"] = args.session
    if args.paper is not None:
        overrides["paper"] = args.paper
    if args.level:
        overrides["level"] = args.level

    only = [s.strip() for s in args.only.split(",") if s.strip()] if args.only else None
    md_dirs: list[Path] = []
    if args.export_md:
        md_dirs.append(Path(args.export_md))
    if args.vault:
        md_dirs.append(Path(args.vault))

    # Paper 1/2 default to AS-only vocabulary unless --all-codes
    as_only = not args.all_codes
    if args.as_only:
        as_only = True

    results = tag_draft_dir(
        draft,
        paper_meta=meta,
        paper_meta_overrides=overrides,
        as_only=as_only,
        syllabus_path=Path(args.syllabus) if args.syllabus else None,
        mock=args.mock,
        model=args.model,
        only=only,
        limit=args.limit,
        out_json_dir=Path(args.json_dir) if args.json_dir else None,
        out_md_dirs=md_dirs or None,
    )
    mode = "mock" if args.mock else "llm"
    print(f"Tagged {len(results)} question(s) [{mode}] from {draft}")
    for r in results:
        codes = ",".join(r["syllabus_codes"])
        print(f"  q{r['question']}: {codes}  answer={r.get('ms_answer')}")
    if md_dirs:
        print("Markdown -> " + ", ".join(str(p) for p in md_dirs))
    return 0


def _cmd_select(args: argparse.Namespace) -> int:
    """Select questions from draft corpus by a rules YAML → pick-list JSON."""
    rules = load_rules(Path(args.rules_yaml))
    docs_dir = Path(args.docs)
    picked = select_questions(rules, docs_dir=docs_dir)
    wrote = write_pick(rules, picked, Path(args.output), docs_dir=docs_dir)
    print(f"Selected {len(picked)} question(s) -> {wrote}")
    if rules.get("count") and len(picked) < rules["count"]:
        print(f"  (target was {rules['count']}; only {len(picked)} matched)")
    return 0


def _cmd_assemble(args: argparse.Namespace) -> int:
    """Render a pick-list JSON into an Obsidian tile-grid handout."""
    import json

    pick_path = Path(args.pick_json)
    pick = json.loads(pick_path.read_text(encoding="utf-8"))
    root = _resolve_vault_arg(args, paper=None)
    wrote = render_tiles(pick, vault_root=root, out_path=Path(args.output))
    print(f"Wrote tile handout ({len(pick.get('questions') or [])} tiles) -> {wrote}")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    """Serve the tile-selector page and JSON API until interrupted."""
    from chembank.serve import serve

    if args.open:
        url = f"http://{args.host}:{args.port}/"
        webbrowser.open(url, new=2)
    serve(
        pick=args.pick,
        port=args.port,
        vault=args.vault,
        host=args.host,
    )
    return 0


def _ukcho_questions_dir(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "dir", None) or "vault-ukcho/questions")


def _find_ukcho_md(questions_dir: Path, record_id: str) -> Path | None:
    for md_path in sorted(questions_dir.glob("*.md")):
        try:
            fm = parse_ukcho_frontmatter(md_path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if str(fm.get("id") or md_path.stem) == record_id:
            return md_path
    return None


def _cmd_ukcho(args: argparse.Namespace) -> int:
    """UKChO tagging foundation: taxonomy, validation, AI prompt/apply, ingest."""
    from chembank import ukcho as U

    questions_dir = _ukcho_questions_dir(args)
    cmd = args.ukcho_cmd

    if cmd == "extract":
        from chembank import ukcho_extract as X

        manifest = X.extract_paper(
            Path(args.pdf),
            Path(args.out),
            args.prefix,
            make_clips=not args.no_clips,
            zoom=args.zoom,
            ms_pdf=Path(args.ms) if args.ms else None,
        )
        n_parts = len(manifest["parts"])
        n_clips = sum(len(p.get("clips") or []) for p in manifest["parts"])
        n_ms = sum(len(p.get("ms_clips") or []) for p in manifest["parts"])
        print(f"Wrote {n_parts} parts, {n_clips} clips, {n_ms} MS clips -> {args.out}/parts.json")
        if args.ms and n_ms == 0:
            print("WARNING no mark-scheme bands were matched; check --ms")
        elif args.ms and n_ms < n_parts:
            print(
                f"NOTE {n_parts - n_ms} part(s) got no MS clip — "
                "their MS label may be missing or worded differently"
            )
        counts = {}
        for p in manifest["parts"]:
            counts[p["question"]] = counts.get(p["question"], 0) + 1
        print("Parts per question: " + ", ".join(f"Q{k}={v}" for k, v in sorted(counts.items())))
        return 0

    if cmd == "ingest":
        from chembank import ukcho_ingest as I

        summary = I.ingest_paper(
            manifest_dir=Path(args.manifest),
            tagging_path=Path(args.tagging),
            vault_dir=Path(args.vault),
            clip_source_dir=Path(args.clips) if args.clips else None,
            source_qp=args.source_qp,
            source_ms=args.source_ms,
        )
        print(
            f"Ingested {summary['parents']} parents + {summary['subquestions']} sub-questions "
            f"into {args.vault} ({summary['clips']} clips)"
        )
        if summary.get("preserved"):
            print(
                f"  kept teacher-reviewed tags on {summary['preserved']} sub-question(s) "
                "— re-ingest never overwrites a teacher's judgement"
            )
        if summary["needs_tags"]:
            print(
                f"  {len(summary['needs_tags'])} of {summary['subquestions']} sub-questions "
                "still need tags (empty skeleton slots) — fill the tagging sheet and re-ingest"
            )
            sample = ", ".join(summary["needs_tags"][:8])
            more = len(summary["needs_tags"]) - 8
            print(f"    {sample}{f' (+{more} more)' if more > 0 else ''}")
        for qid, errs in summary["other_errors"].items():
            print(f"  ERROR {qid}")
            for err in errs:
                print(f"    - {err}")
        for problem in summary["problems"]:
            print(f"  ERROR {problem}")
        for warn in summary["warnings"][:40]:
            print(f"  warn  {warn}")
        real_errors = sum(len(v) for v in summary["other_errors"].values()) + len(
            summary["problems"]
        )
        return 1 if real_errors else 0

    if cmd == "snapshot":
        from chembank import ukcho_ingest as I

        try:
            summary = I.write_snapshot(
                Path(args.vault), Path(args.out), prefix=args.prefix
            )
        except ValueError as exc:
            print(f"ERROR {exc}", file=__import__("sys").stderr)
            return 2
        for snap in summary["snapshots"]:
            print(
                f"{snap['prefix']}: {snap['parts']} parts "
                f"({snap['reviewed']} teacher-reviewed), "
                f"{snap['bytes'] // 1024} KB -> {snap['path']}"
            )
            for q in snap.get("quotes") or []:
                print(
                    f"  warn  {q['id']} quotes the paper in {q['field']}: "
                    f"\"{q['quote']}\""
                )
        print(
            "\nNo question or mark-scheme text is included, so this is safe to commit.\n"
            "Restore with the normal pipeline (same PDF -> same part keys):\n"
            "  chembank ukcho extract --pdf <qp.pdf> --out draft/ukcho/<year> --prefix <prefix>\n"
            "  chembank ukcho ingest --manifest draft/ukcho/<year> "
            "--tagging <prefix>-tags.json --vault vault-ukcho"
        )
        return 0

    if cmd == "import":
        from chembank import ukcho_ingest as I

        summary = I.import_edits(Path(args.edits), Path(args.vault))
        print(
            f"Imported teacher edits: {len(summary['updated'])} updated, "
            f"{len(summary['unchanged'])} unchanged, {len(summary['missing'])} not in the vault"
        )
        for rid in summary["missing"]:
            print(f"  ERROR no vault record for {rid}")
        for rid, errs in summary["errors"].items():
            print(f"  ERROR {rid}")
            for err in errs:
                print(f"    - {err}")
        if summary["ignored"]:
            print(f"  ignored {len(summary['ignored'])} entr(ies) with no id")
        if summary["updated"]:
            print("  Rebuild the site to publish them: python quiz-app/build.py")
            print(
                "  Back up the tags (the vault is gitignored): "
                "chembank ukcho snapshot"
            )
        return 1 if summary["missing"] or summary["errors"] else 0

    if cmd == "taxonomy":
        tax = U.taxonomy()
        if args.json:
            print(json.dumps(tax, ensure_ascii=False, indent=2))
        else:
            print(f"AS Anchors ({len(tax['asAnchors'])}):")
            for a in tax["asAnchors"]:
                print(f"  - {a}")
            print(f"\nUKChO Extension Topics ({len(tax['extensionTopics'])}):")
            for group, topics in tax["extensionTopicGroups"].items():
                print(f"  [{group}] {', '.join(topics)}")
            print(f"\nSkills: {', '.join(tax['skills'])}")
            print(f"Difficulty: {', '.join(tax['difficultyLevels'])}")
            print(f"Question Features: {', '.join(tax['questionFeatures'])}")
        return 0

    if cmd == "validate":
        records = U.load_ukcho_questions(questions_dir)
        if not records:
            print(f"No UKChO records found under {questions_dir}", file=__import__("sys").stderr)
            return 2
        report = U.validate_all(records)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"# UKChO validation — {report['ok']}/{report['count']} sub-questions clean")
            for qid, errs in report["errors"].items():
                print(f"ERROR {qid}")
                for e in errs:
                    print(f"  - {e}")
            for qid, warns in report["warnings"].items():
                print(f"warn  {qid}")
                for w in warns:
                    print(f"  - {w}")
        return 1 if report["errors"] else 0

    if cmd == "export":
        records = U.load_ukcho_questions(questions_dir)
        records = [U.to_ordered_dict(r) for r in records]
        payload = {"source": "UKChO", "count": len(records), "questions": records}
        out = Path(args.out) if args.out else None
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            print(f"Wrote {len(records)} records -> {out}")
        else:
            print(text)
        return 0

    # ---- whole-paper batch prompt (extract -> tagging sheet) ----------------
    if cmd == "prompt" and getattr(args, "manifest", None):
        from chembank import ukcho_ingest as I

        result = I.write_sheet(
            manifest_dir=Path(args.manifest),
            out_dir=Path(args.out) if args.out else None,
            prefix=args.prefix,
            year=args.year,
            source_ms=args.source_ms,
            force=args.force,
        )
        print(
            f"Prompt for {result['parts']} parts across {result['questions']} questions "
            f"-> {result['prompt_path']}"
        )
        print(f"Tagging sheet ({result['year'] or 'year ?'}) {result['sheet_status']}"
              f" -> {result['sheet_path']}")
        print(
            "\nNext: fill the tags in the sheet (or have a model answer prompt.json), "
            "then:\n"
            f"  chembank ukcho ingest --manifest {args.manifest} "
            f"--tagging {result['sheet_path']} --vault vault-ukcho"
        )
        if not result["sheet_written"]:
            print("\nNote: the existing sheet was left untouched so your tags survive.")
        return 0

    # ---- single-record commands need an id ---------------------------------
    record_id = args.id
    if not record_id:
        print(
            "This ukcho subcommand needs a record id, or --manifest for a whole paper.",
            file=__import__("sys").stderr,
        )
        return 2
    md_path = _find_ukcho_md(questions_dir, record_id)
    if md_path is None:
        print(f"Record {record_id!r} not found under {questions_dir}", file=__import__("sys").stderr)
        return 2
    text = md_path.read_text(encoding="utf-8")
    rec = U.normalize_record(U.parse_frontmatter(text), fallback_id=md_path.stem)

    if cmd == "prompt":
        bundle = U.build_tagging_request(rec)
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
        return 0

    if cmd == "apply":
        try:
            ai_payload = json.loads(Path(args.ai).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Could not read AI JSON: {exc}", file=__import__("sys").stderr)
            return 2
        if isinstance(ai_payload, dict) and "result" in ai_payload and isinstance(
            ai_payload["result"], dict
        ):
            ai_payload = ai_payload["result"]
        if not isinstance(ai_payload, dict):
            print("AI JSON must be an object.", file=__import__("sys").stderr)
            return 2
        merged = U.apply_ai_tags(rec, ai_payload)
        ordered = U.to_ordered_dict(merged)
        if args.write:
            body = U.split_body(text)
            md_path.write_text(U.to_frontmatter(ordered) + body, encoding="utf-8")
            print(f"Applied suggested tags -> {md_path} (tag_status=suggested)")
        else:
            draft_dir = Path("draft/ukcho")
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft = draft_dir / f"{record_id}.json"
            draft.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Wrote suggested tags -> {draft} (review, then --write to update the vault)")
        return 0

    print(f"Unknown ukcho subcommand: {cmd}", file=__import__("sys").stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="chembank",
        description="CIE 9701 chemistry past-paper bank (syllabus-first MVP)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("extract", help="Extract text from a PDF")
    e.add_argument("pdf")
    e.add_argument("-o", "--output", required=True)
    e.set_defaults(func=_cmd_extract)

    s = sub.add_parser("split", help="Split extracted text into question files")
    s.add_argument("text", help="Extracted .txt from extract")
    s.add_argument("-o", "--output", required=True, help="Output directory")
    s.add_argument("-m", "--mark-scheme", help="MS PDF or extracted text (MCQ key)")
    s.set_defaults(func=_cmd_split)

    pipe = sub.add_parser("pipeline", help="Extract + split QP (optional MS bind)")
    pipe.add_argument("question_paper")
    pipe.add_argument("-m", "--mark-scheme")
    pipe.add_argument("-d", "--draft-dir", default="draft")
    pipe.set_defaults(func=_cmd_pipeline)

    c = sub.add_parser("codes", help="List syllabus taxonomy codes")
    c.add_argument("--syllabus", help="Path to syllabus YAML")
    c.add_argument("--as-only", action="store_true", help="Only AS topics 1–22")
    c.add_argument(
        "--lo",
        action="store_true",
        help="List learning outcome ids instead of topic codes",
    )
    c.add_argument(
        "--code",
        help="With --lo: filter by topic/subtopic (e.g. 3 or 3.1)",
    )
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=_cmd_codes)

    lo = sub.add_parser(
        "los",
        help="List CIE 9701 learning outcome ids (controlled vocabulary)",
    )
    lo.add_argument("--syllabus", help="Path to syllabus YAML")
    lo.add_argument("--as-only", action="store_true", help="Only AS topics 1–22")
    lo.add_argument(
        "--code",
        help="Filter by topic or subtopic code (e.g. 3 or 3.1)",
    )
    lo.add_argument("--json", action="store_true")
    lo.set_defaults(func=_cmd_los)

    k = sub.add_parser("ms-key", help="Parse MCQ mark scheme answer key")
    k.add_argument("mark_scheme")
    k.set_defaults(func=_cmd_ms_key)

    t = sub.add_parser(
        "tag",
        help="AI-tag split drafts with controlled syllabus_codes (OpenAI-compatible or --mock)",
    )
    t.add_argument("draft", help="Draft directory with q*.txt (e.g. draft/9701_s21_qp_11)")
    t.add_argument(
        "--paper-meta",
        help="Overrides: year=2021,session=MJ,paper=11,level=AS (comma-separated)",
    )
    t.add_argument("--year", type=int, help="Exam year override")
    t.add_argument("--session", help="Session override: MJ / ON / FM")
    t.add_argument("--paper", help="Paper code override, e.g. 11")
    t.add_argument("--level", choices=["AS", "A", "AS/A"], help="Level override")
    t.add_argument("--syllabus", help="Path to syllabus YAML")
    t.add_argument(
        "--as-only",
        action="store_true",
        default=False,
        help="Restrict vocabulary to AS topics 1–22 (default for Paper 1/2)",
    )
    t.add_argument(
        "--all-codes",
        action="store_true",
        help="Allow full AS+A Level vocabulary (disables AS-only default)",
    )
    t.add_argument(
        "--mock",
        action="store_true",
        help="Dry-run heuristic tagging (no API key); still validates codes",
    )
    t.add_argument("--model", help="Chat model id (default: OPENAI_MODEL or gpt-4o-mini)")
    t.add_argument("--only", help="Comma-separated question numbers, e.g. 1,2,3")
    t.add_argument("--limit", type=int, help="Tag only the first N questions")
    t.add_argument(
        "--json-dir",
        help="JSON sidecar output dir (default: <draft>/tagged)",
    )
    t.add_argument(
        "--export-md",
        help="Write Obsidian Markdown into this directory (e.g. questions/)",
    )
    t.add_argument(
        "--vault",
        help="Also write Markdown into vault path (e.g. vault/questions/)",
    )
    t.set_defaults(func=_cmd_tag)

    v = sub.add_parser(
        "export-vault",
        help="Re-export tagged drafts to Obsidian (chemistry format + diagrams)",
    )
    v.add_argument("question_paper", help="QP PDF path")
    v.add_argument(
        "-d",
        "--draft",
        required=True,
        help="Draft dir with q*.txt + tagged/ (e.g. draft/9701_s21_qp_11)",
    )
    v.add_argument(
        "--vault",
        default=None,
        help="Obsidian vault root (default: vault/ 1x, vault-structured/ 2/4/5x, vault-practical/ 3x)",
    )
    v.add_argument(
        "--export-md",
        default=None,
        help="Also write Markdown copies here (default: questions/, questions-structured/, or questions-practical/)",
    )
    v.add_argument("-m", "--mark-scheme", help="MS PDF for re-split binding")
    v.add_argument(
        "--no-refresh",
        action="store_true",
        help="Skip re-extract/split; only re-render markdown + figures",
    )
    v.set_defaults(func=_cmd_export_vault)

    loh = sub.add_parser(
        "export-lo-hubs",
        help="Write Obsidian LO hub notes for all vocabulary LOs (searchable aliases)",
    )
    loh.add_argument("--vault", default="vault", help="Obsidian vault root")
    loh.add_argument("--syllabus", help="Path to syllabus YAML")
    loh.add_argument(
        "--code",
        help="Only LOs under this topic/subtopic (e.g. 1 or 1.1)",
    )
    loh.add_argument(
        "--all-levels",
        action="store_true",
        help="Include A Level LOs (default: AS topics 1–22 only)",
    )
    loh.set_defaults(func=_cmd_export_lo_hubs)

    sel = sub.add_parser(
        "select",
        help="Pick questions from draft corpus via a rules YAML → pick-list JSON",
    )
    sel.add_argument("rules_yaml", help="Selection rules YAML (e.g. pick/5.1-demo.yaml)")
    sel.add_argument(
        "-o", "--output", required=True, help="Pick-list JSON output (e.g. build/pick.json)"
    )
    sel.add_argument(
        "--docs", default="draft", help="Question corpus root (default: draft)"
    )
    sel.set_defaults(func=_cmd_select)

    asm = sub.add_parser(
        "assemble",
        help="Render a pick-list JSON into an Obsidian tile-grid handout",
    )
    asm.add_argument("pick_json", help="Pick-list JSON from `chembank select`")
    asm.add_argument(
        "-o", "--output", required=True, help="Handout Markdown output (e.g. vault/handouts/5.1-demo.md)"
    )
    asm.add_argument(
        "--vault", default="vault", help="Obsidian vault root for asset resolution (default: vault)"
    )
    asm.set_defaults(func=_cmd_assemble)

    srv = sub.add_parser(
        "serve",
        help="Open the interactive tile-selector page + JSON API in the browser",
    )
    srv.add_argument(
        "--pick",
        default="build/pick.json",
        help="Pick-list JSON (default: build/pick.json)",
    )
    srv.add_argument(
        "--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)"
    )
    srv.add_argument(
        "--port", type=int, default=8975, help="Bind port (default: 8975)"
    )
    srv.add_argument(
        "--vault",
        default="vault",
        help="Vault root for asset resolution (default: vault)",
    )
    srv.add_argument(
        "--open",
        action="store_true",
        help="Auto-open the browser on startup",
    )
    srv.set_defaults(func=_cmd_serve)

    er = sub.add_parser(
        "er-extract",
        help="Extract CIE Principal Examiner Report → year-scoped draft/er JSON",
    )
    er.add_argument("pdf", help="Examiner report PDF path")
    er.add_argument(
        "--paper",
        help="Only keep one paper variant (e.g. 11 for 9701/11)",
    )
    er.add_argument(
        "-o",
        "--output",
        help="Output JSON path (default: draft/er/9701_<season>_er[_<paper>].json)",
    )
    er.add_argument(
        "--reports-dir",
        default="raw/reports",
        help="Copy PDF here with clean year-scoped name (default: raw/reports)",
    )
    er.add_argument(
        "--no-copy",
        action="store_true",
        help="Do not copy PDF into raw/reports/",
    )
    er.set_defaults(func=_cmd_er_extract)

    erm = sub.add_parser(
        "er-merge",
        help="Merge draft/er JSON into draft/<paper_id>/tagged/qN.json",
    )
    erm.add_argument(
        "er_json",
        help="Structured ER JSON (e.g. draft/er/9701_s21_er_11.json)",
    )
    erm.add_argument(
        "-t",
        "--tagged",
        required=True,
        help="Tagged dir (e.g. draft/9701_s21_qp_11/tagged)",
    )
    erm.add_argument("--paper", help="Paper variant if ER JSON has multiple")
    erm.add_argument(
        "--source",
        help="Override examiner_report_source path stored on questions",
    )
    erm.add_argument(
        "--no-difficulty",
        action="store_true",
        help="Do not overwrite difficulty from ER qualitative bands",
    )
    erm.set_defaults(func=_cmd_er_merge)

    ing = sub.add_parser(
        "ingest",
        help="Batch-friendly one-paper pipeline: extract→split→(er)→(export-vault)",
    )
    ing.add_argument(
        "paper_ref",
        nargs="+",
        help="Paper ref: s21 12   or   9701_s21_qp_12   or   s21:12",
    )
    ing.add_argument("--qp", help="Override QP PDF path")
    ing.add_argument("-m", "--mark-scheme", help="Override MS PDF path")
    ing.add_argument("--er-pdf", help="Override Examiner Report PDF path")
    ing.add_argument("--draft", help="Override draft/<paper_id> directory")
    ing.add_argument(
        "--vault",
        default=None,
        help="Obsidian vault root (default: vault/ 1x, vault-structured/ 2/4/5x, vault-practical/ 3x)",
    )
    ing.add_argument(
        "--export-md",
        default=None,
        help="Also write Markdown here (default: questions/, questions-structured/, or questions-practical/)",
    )
    exp = ing.add_mutually_exclusive_group()
    exp.add_argument(
        "--export",
        dest="do_export",
        action="store_true",
        help="Export to vault when tagged/ exists (default)",
    )
    exp.add_argument(
        "--no-export",
        dest="do_export",
        action="store_false",
        help="Only extract+split (+ optional ER); skip vault export",
    )
    ing.set_defaults(do_export=True)
    ing.add_argument(
        "--no-er",
        action="store_true",
        help="Skip Examiner Report extract/merge even if PDF exists",
    )
    ing.add_argument(
        "--force-er",
        action="store_true",
        help="Re-extract ER JSON even if draft/er/… already exists",
    )
    ing.add_argument(
        "--no-refresh",
        action="store_true",
        help="On export: skip re-extract/split (pass-through to export-vault)",
    )
    ing.add_argument(
        "--registry",
        default=str(DEFAULT_PAPERS_YAML),
        help="papers.yaml path (default: papers.yaml)",
    )
    ing.add_argument(
        "--no-registry",
        action="store_true",
        help="Do not update papers.yaml / draft/manifest.json",
    )
    ing.set_defaults(func=_cmd_ingest)

    bat = sub.add_parser(
        "batch",
        help="Ingest many papers from papers.yaml or explicit refs (s21:11 s21:12)",
    )
    bat.add_argument(
        "paper_ref",
        nargs="*",
        help="Optional refs like s21:11 9701_s21_qp_12 (default: all in papers.yaml)",
    )
    bat.add_argument(
        "--status",
        help="Filter registry by status (comma): pending,extracted,tagged",
    )
    bat.add_argument("--limit", type=int, help="Process at most N papers")
    bat.add_argument(
        "--vault",
        default=None,
        help="Force one vault for all papers (default: auto per paper kind)",
    )
    bat.add_argument(
        "--export-md",
        default=None,
        help="Force dual-write dir (default: auto per paper kind)",
    )
    bat_exp = bat.add_mutually_exclusive_group()
    bat_exp.add_argument("--export", dest="do_export", action="store_true")
    bat_exp.add_argument("--no-export", dest="do_export", action="store_false")
    bat.set_defaults(do_export=True)
    bat.add_argument("--no-er", action="store_true")
    bat.add_argument("--force-er", action="store_true")
    bat.add_argument("--no-refresh", action="store_true")
    bat.add_argument("--registry", default=str(DEFAULT_PAPERS_YAML))
    bat.add_argument("--no-registry", action="store_true")
    bat.set_defaults(func=_cmd_batch)

    pap = sub.add_parser("papers", help="List papers.yaml registry")
    pap.add_argument("--registry", default=str(DEFAULT_PAPERS_YAML))
    pap.add_argument(
        "--refresh-status",
        action="store_true",
        help="Recompute status from draft/ + vault/ and rewrite registry",
    )
    pap.set_defaults(func=_cmd_papers)

    aud = sub.add_parser(
        "audit",
        help="Quality-gate exported vault questions (must pass before marking done)",
    )
    aud.add_argument(
        "paper_ref",
        nargs="*",
        help="Optional refs: s21:11 s21:21 (default: all questions in chosen vault)",
    )
    aud.add_argument(
        "--vault",
        default=None,
        help="Obsidian vault root (default: auto from first paper ref, else vault/)",
    )
    aud.add_argument(
        "--export-md",
        default=None,
        help="Dual-write Markdown dir to check (default: auto from paper kind)",
    )
    aud.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Skip QP paper-clip geometry / A–D / Section B key checks",
    )
    aud.set_defaults(func=_cmd_audit)

    uk = sub.add_parser(
        "ukcho",
        help="UKChO tagging foundation: taxonomy, validate, AI prompt/apply",
    )
    uk.add_argument(
        "--dir",
        default="vault-ukcho/questions",
        help="UKChO questions dir (default: vault-ukcho/questions)",
    )
    uksub = uk.add_subparsers(dest="ukcho_cmd", required=True)

    ukt = uksub.add_parser("taxonomy", help="Print the controlled UKChO tag taxonomy")
    ukt.add_argument("--json", action="store_true")
    ukt.set_defaults(func=_cmd_ukcho)

    ukv = uksub.add_parser("validate", help="Validate the UKChO vault against the taxonomy")
    ukv.add_argument("--json", action="store_true")
    ukv.set_defaults(func=_cmd_ukcho)

    uke = uksub.add_parser("export", help="Dump all UKChO records as JSON")
    uke.add_argument("-o", "--out", help="Write JSON here instead of stdout")
    uke.set_defaults(func=_cmd_ukcho)

    ukp = uksub.add_parser(
        "prompt",
        help=(
            "Print a ready-to-paste AI tagging request: for one sub-question by id, "
            "or a whole extracted paper with --manifest"
        ),
    )
    ukp.add_argument("id", nargs="?", help="Record id, e.g. ukcho-2025-q3b")
    ukp.add_argument(
        "--manifest",
        help=(
            "Dir containing parts.json from `ukcho extract`: writes prompt.json "
            "(for the tagger) and tagging.json (a fillable sheet) for the whole paper"
        ),
    )
    ukp.add_argument(
        "-o", "--out", help="Output dir for prompt.json/tagging.json (default: the manifest dir)"
    )
    ukp.add_argument("--prefix", default="", help="Override prefix, e.g. ukcho-2024")
    ukp.add_argument("--year", type=int, help="Override year (default: read from the prefix)")
    ukp.add_argument("--source-ms", default="", help="Mark scheme PDF path to record in the sheet")
    ukp.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing tagging.json (it holds the only copy of the tags)",
    )
    ukp.set_defaults(func=_cmd_ukcho)

    uka = uksub.add_parser(
        "apply", help="Merge an AI JSON response in as *suggested* tags (never locked)"
    )
    uka.add_argument("id", help="Record id, e.g. ukcho-2025-q3b")
    uka.add_argument("--ai", required=True, help="AI JSON response file")
    uka.add_argument(
        "--write",
        action="store_true",
        help="Write back to the vault markdown (default: draft only)",
    )
    uka.set_defaults(func=_cmd_ukcho)

    uks = uksub.add_parser(
        "snapshot",
        help=(
            "Write a content-free tag snapshot per paper (safe to commit) — the "
            "only backup of the tagging work, since the vault is gitignored"
        ),
    )
    uks.add_argument(
        "--vault", default="vault-ukcho", help="Vault dir (default: vault-ukcho)"
    )
    uks.add_argument(
        "-o",
        "--out",
        default="fixtures/ukcho-tags",
        help="Output dir (default: fixtures/ukcho-tags)",
    )
    uks.add_argument("--prefix", default="", help="Only this paper, e.g. ukcho-2025")
    uks.set_defaults(func=_cmd_ukcho)

    uki2 = uksub.add_parser(
        "import",
        help=(
            "Merge a teacher-edits download into the vault, stamping the records as "
            "reviewed so a later re-ingest cannot revert them"
        ),
    )
    uki2.add_argument(
        "--edits",
        required=True,
        help="ukcho-teacher-edits.json downloaded from the tagging workspace",
    )
    uki2.add_argument(
        "--vault", default="vault-ukcho", help="Vault dir (default: vault-ukcho)"
    )
    uki2.set_defaults(func=_cmd_ukcho)

    ukx = uksub.add_parser(
        "extract",
        help="Extract a UKChO paper PDF into parts + per-part page-clip PNGs",
    )
    ukx.add_argument("pdf", help="UKChO question paper PDF")
    ukx.add_argument(
        "-o", "--out", required=True, help="Output dir for parts.json, parts/ and clips/"
    )
    ukx.add_argument("--prefix", required=True, help="Filename prefix, e.g. ukcho-2025")
    ukx.add_argument("--no-clips", action="store_true", help="Skip PNG rendering")
    ukx.add_argument(
        "--ms",
        default="",
        help=(
            "Mark scheme PDF. Renders one <prefix>-<key>-ms.png per part, so the "
            "vault shows the marked answers like the AS/IGCSE banks do."
        ),
    )
    ukx.add_argument("--zoom", type=float, default=2.4, help="Clip render zoom (default 2.4)")
    ukx.set_defaults(func=_cmd_ukcho)

    uki = uksub.add_parser(
        "ingest",
        help="Materialise an extracted paper + tagging sheet into the vault",
    )
    uki.add_argument(
        "--manifest", required=True, help="Dir containing parts.json from `ukcho extract`"
    )
    uki.add_argument("--tagging", required=True, help="Tagging sheet JSON (parents + parts)")
    uki.add_argument("--vault", default="vault-ukcho", help="Vault dir (default: vault-ukcho)")
    uki.add_argument("--clips", help="Dir of clip PNGs (default: <manifest>/clips)")
    uki.add_argument("--source-qp", default="", help="Repo-relative QP path for provenance")
    uki.add_argument("--source-ms", default="", help="Repo-relative MS path for provenance")
    uki.set_defaults(func=_cmd_ukcho)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
