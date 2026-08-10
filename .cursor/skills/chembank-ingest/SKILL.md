---
name: chembank-ingest
description: >-
  Orchestrates ChemBank CIE 9701 past-paper ingest: PDF pipeline (extract/split/MS),
  controlled syllabus tagging, human spot-check, and Obsidian vault export. Use when
  the user asks to 导入真题, 切题, 打标, 导出 Obsidian, past paper, batch ingest,
  批量导入, 讲义, 组卷, 拼题, 试卷, handout, assemble, or chembank ingest.
---

# ChemBank ingest（批量友好）

One skill for the full ingest loop (MCQ / structured / practical). **Code** does extract/split/tag/export; **this skill** enforces order, wordlist bounds, the export checklist, and the spot-check gate.

批量加卷时优先走 `chembank ingest` / `chembank batch`，再按卷打标：

- Paper **1x** MCQ → [chembank-syllabus-tag](../chembank-syllabus-tag/SKILL.md) → `vault/`
- Paper **2/4/5x** 结构题 → [chembank-structured-tag](../chembank-structured-tag/SKILL.md) → `vault-structured/`
- Paper **3x** 实验题 → [chembank-practical-tag](../chembank-practical-tag/SKILL.md) → `vault-practical/`

## Paths

| Role | Path |
|------|------|
| Syllabus wordlist | `syllabus/cie-9701-as-a-level-chemistry.yaml` |
| Schema | `schema/question.schema.json` |
| Paper registry | `papers.yaml` (+ `draft/manifest.json`) |
| Local QP/MS (gitignored) | `raw/papers/9701_<season>_qp_<paper>.pdf` |
| Examiner reports (year-scoped) | `raw/reports/9701_<year>_<season>_er.pdf` |
| ER JSON | `draft/er/9701_<season>_er_<paper>.json` |
| Draft / tagged JSON | `draft/<paper_id>/`, `draft/<paper_id>/tagged/` |
| Canonical MD (MCQ) | `questions/` |
| Canonical MD (structured) | `questions-structured/` |
| Canonical MD (practical) | `questions-practical/` |
| Obsidian vault (MCQ) | `vault/` |
| Obsidian vault (structured) | `vault-structured/`（`syllabus/` → 链到 `vault/syllabus`） |
| Obsidian vault (practical) | `vault-practical/`（`syllabus/` → 链到 `vault/syllabus`） |
| Example frontmatter | `examples/cie-9701-2021-mj-p11-q1.md` |

## Handout / 组卷（select + assemble）

Given a rules YAML, pick questions from the corpus and render as one Obsidian handout note. This is **read-only** over the draft corpus — it does not re-tag or re-export.

```bash
source .venv/bin/activate
chembank select pick/5.2-demo.yaml -o build/pick52.json
# → build/pick52.json （rules + chosen questions）
chembank assemble build/pick52.json -o vault/handouts/5.2-demo.md --vault vault
# → vault/handouts/5.2-demo.md （stacked handout）
```

- Rules live in `pick/*.yaml`（see `pick/5.1-demo.yaml` for a full field reference：`title` required; optional `syllabus_codes`, `topic_title`, `year_min/max`, `difficulty_min/max`, `max_marks`, `question_type`, `count`, `sort` default `[year,question]`, `shuffle` with `seed`）。
- **Stacked layout**：one question per `---` block; large `<img src="file://…">` screenshot（abs path, ~820px）; caption `第N题 · <year> <session> · Q<orig> · <marks>分`; `[[questions/<id>]]` detail link. `select` dedupes by `id`; the `第N题` numbering is shared between the question grid and the answer section.
- **Answer section**：MCQ（has short `ms_answer`）→ letters；structured/practical（no `ms_answer`）→ inlined `*-ms.png` Mark Scheme screenshot via `resolve_asset_path`（searches sibling vaults）。
- Handouts write to `vault/handouts/<slug>.md`. User triggers：**讲义 / 组卷 / 拼题 / 试卷 / handout / assemble**。

## Hard rules

1. `syllabus_codes` **and** `learning_outcomes` **only** from the YAML wordlist. **Never invent codes/LO ids.**
2. Every tagged question needs **≥1 `learning_outcomes`**. Empty LO = tagging incomplete.
3. Paper 1/2 → AS-only (topics **1–22**) unless the user asks for A Level (`23–37` / `--all-codes`).
4. Prefer the **most specific** subtopic (e.g. `2.2` not bare `2`). Tag what the question **asks** (assessed skill), **not** decorative context. Enthalpy/Hess/ΔH → `5.x` never `4.2` from oxide lists. See structured/MCQ skill「考查点打标」。
5. After tagging: every question needs `ms_answer` (Paper 1) **and** ≥1 valid `syllabus_codes` + LO. `chembank tag --mock` / heuristic tags are **provisional** only.
5b. User trigger「**按考查点重标 LO**」→ re-tag by assessed skill (command word + MS), then `ingest --export`.
6. **Every** exported question needs `*-paper.png` (full paper clip). No wrong crops / atom-salad OCR under figures. Paper 1 MCQ clips must OCR-contain **A–D** (all four letters); Section B statement-combo clips must include the A–D combination key (never end at statement 3 alone). Audit also rejects tiny/stale PNGs and empty question bodies.
7. Examiner Report is **year-scoped**; merge when available; **never invent** facility %.
8. **Do not commit** past-paper / syllabus PDFs (`raw/` is gitignored).
9. Spot-check `draft/.../tagged/` (and vault samples) **before** treating `questions/` as canonical.

## End-to-end checklist（每次加卷必须对照）

```
ChemBank batch ingest:
- [ ] 1. QP + MS under raw/papers/ with clean names; optional ER under raw/reports/
- [ ] 2. chembank ingest <season> <paper>  → extract + split + MS bind
- [ ] 3. Tag: syllabus_codes + ≥1 learning_outcomes（skill / chembank tag）
- [ ] 4. ER: if PDF exists → er-extract + er-merge（ingest 会自动；无则跳过）
- [ ] 5. export-vault / ingest --export → questions/ + vault/ + *-paper.png + LO hubs
- [ ] 6. ★ chembank audit <refs> exit 0（F1–F13；见 chembank-syllabus-tag Pre-done）
- [ ] 7. Spot-check（见 chembank-syllabus-tag 验收清单）
- [ ] 8. papers.yaml status → exported；下一卷重复 1–7
```

## Batch ingest new paper

### Folder naming

| Kind | Path |
|------|------|
| QP | `raw/papers/9701_s21_qp_12.pdf` |
| MS | `raw/papers/9701_s21_ms_12.pdf` |
| ER (year) | `raw/reports/9701_2021_s21_er.pdf` |

Season tokens: `sYY`=MJ, `wYY`=ON, `mYY`=FM.

### One paper (example: s21 qp12 MCQ)

```bash
cd /Users/tsinglan-school/Desktop/题库
source .venv/bin/activate

# 1) Drop PDFs with the names above, then:
chembank ingest s21 12
# → draft/9701_s21_qp_12/q*.txt + ms_key.json；更新 papers.yaml

# 2) Tag (this skill hands off to chembank-syllabus-tag, or:)
#    「给 draft/9701_s21_qp_12 全卷打标并导出」
#    chembank tag draft/9701_s21_qp_12 …

# 3) After tagged/ exists — export + ER merge:
chembank ingest s21 12 --export
chembank audit s21:12   # must exit 0 before marking done
```

### Structured paper (example: s21 qp21)

```bash
# Drop:
#   raw/papers/9701_s21_qp_21.pdf
#   raw/papers/9701_s21_ms_21.pdf

chembank ingest s21 21
# → kind=structured；draft/.../q2a-i.txt 等最小小题 + ms_parts.json
# Tag with chembank-structured-tag（默认一最小小题一篇；QP clip + MS clip）
chembank ingest s21 21 --export   # → vault-structured/ + questions-structured/
chembank audit s21:21
```

### Practical paper (example: s21 qp31)

```bash
# Drop:
#   raw/papers/9701_s21_qp_31.pdf
#   raw/papers/9701_s21_ms_31.pdf

chembank ingest s21 31
# → kind=practical；vault=vault-practical
# Tag with chembank-practical-tag（按实验 topic / 主问题板块，非 part 级）
chembank ingest s21 31 --export   # → vault-practical/ + questions-practical/
chembank audit s21:31
```

### Next paper / many papers

```bash
chembank ingest s21 13                 # next variant same session
chembank batch s21:12 s21:13 w22:11    # mechanical loop
chembank papers                        # list registry
chembank batch --status pending,extracted
```

`ingest` / `batch` run: **extract → split → (er-extract/merge) → (export-vault if tagged)**.  
They do **not** invent syllabus tags; tagging stays in the syllabus-tag skill / `chembank tag`.

## Workflow (single paper detail)

```
进度:
- [ ] 1. pipeline — ingest / extract QP + split + bind MS
- [ ] 2. tag — controlled syllabus_codes + learning_outcomes
- [ ] 3. ER merge — when year report exists
- [ ] 4. export-vault — *-paper.png + dual-write + hubs
- [ ] 5. human spot-check
- [ ] 6. vault — Obsidian / Dataview usable
```

### 1. Pipeline

```bash
chembank ingest s21 11
# or legacy:
chembank pipeline \
  raw/papers/9701_s21_qp_11.pdf \
  -m raw/papers/9701_s21_ms_11.pdf \
  -d draft
```

Expect `draft/<paper_id>/q1.txt`… and `ms_key.json`.

### 2. Tag

Prefer Cursor skill [chembank-syllabus-tag](../chembank-syllabus-tag/SKILL.md) (no API key).  
CLI with key: `chembank tag draft/<paper_id> …`；`--mock` 仅冒烟。

### 3–4. ER + export

Handled by `chembank ingest <season> <paper>` when `tagged/` exists, or manually:

```bash
chembank er-extract raw/reports/9701_2021_s21_er.pdf --paper 11
chembank er-merge draft/er/9701_s21_er_11.json -t draft/9701_s21_qp_11/tagged
chembank export-vault raw/papers/9701_s21_qp_11.pdf \
  -d draft/9701_s21_qp_11 -m raw/papers/9701_s21_ms_11.pdf \
  --vault vault --export-md questions
```

### 5. Human spot-check (required)

At least **q1–q10** (more if mock/LLM looks noisy). Fix `tagged/qN.json`, then re-export.  
Recurring errors → [reference.md](reference.md).

## Acceptance

- Full Paper 1: 40 × (`ms_answer` + ≥1 `syllabus_codes` + ≥1 `learning_outcomes` + `*-paper.png`)
- ER merged when PDF available (bands OK; no invented %)
- Vault filterable by `syllabus_codes` / LO; `papers.yaml` lists the paper
- Agent never invents codes or commits PDFs

## Common mis-tag patterns

| Pattern | Wrong → right (examples) |
|---------|---------------------------|
| Stoichiometry over-breadth | Mole/Avogadro atom count as `2.4` → `2.2` |
| Bonding keyword over-tag | Shape Q tagged `3.2`/`3.4`/`3.5` → `3.5` only |
| Option-keyword steal | IE stem stolen by “orbital” → `1.4` not `1.3` |
| Mock fallback `1.1` | No keyword → almost always wrong |
| Haber / plant context | Heat-exchanger “speed up” as `7.x` → `8.1` |

More: [reference.md](reference.md), [spot-check-notes.md](spot-check-notes.md).
