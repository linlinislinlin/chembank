# ChemBank ingest — reference

## Handout / 组卷 (select + assemble)

```bash
source .venv/bin/activate
chembank select pick/<rules>.yaml -o build/pick.json          # → pick-list JSON
chembank assemble build/pick.json -o vault/handouts/<slug>.md --vault vault
```

- Rules YAML field reference：`pick/5.1-demo.yaml`（also `pick/5.2-demo.yaml`）。
- Output：pick-list JSON（`build/pick.json`）→ stacked handout（`vault/handouts/<slug>.md`）。
- Answer section behavior：MCQ → `ms_answer` letter；structured/practical → inlined `*-ms.png` Mark Scheme screenshot。

## Obsidian Dataview

Vault root should include `questions/` (this repo uses `vault/questions/`). Example query:

```dataview
TABLE ms_answer, syllabus_codes, topic_titles
FROM "questions"
WHERE contains(syllabus_codes, "2.2")
SORT question ASC
```

Other useful filters: `WHERE contains(syllabus_codes, "14.2")`, `WHERE ms_answer = "C"`.

## Verification log — `9701_s21_qp_11` (2026-08-01)

Checked **without** Obsidian GUI (YAML frontmatter parse + code membership + filter simulation).

| Check | Result |
|-------|--------|
| `vault/questions/cie-9701-2021-mj-p11-q*.md` count | **40** |
| Required frontmatter | `id`, `syllabus_codes`, `ms_answer`, sources, etc. — OK |
| Codes ∈ AS wordlist | OK |
| `contains(syllabus_codes, "2.2")` | q1, q27, q31 |
| `contains(syllabus_codes, "1.4")` | q7 |
| `contains(syllabus_codes, "8.2")` | q5 |
| `contains(syllabus_codes, "14.2")` | q21, q23, q29, q39 |
| Unique codes used | 34 |

Tagging run: CLI `--mock` (no `OPENAI_API_KEY` / `CHEMBANK_API_KEY`), then **human correction** of all 40 codes against the stem ask. Mock alone is not vault-quality.

## Mis-tag examples (q1–q10)

| Q | Ask (short) | Bad | Good | Why |
|---|-------------|-----|------|-----|
| 1 | Largest number of H atoms | `2.4`,`2.2` | `2.2` | Mole/Avogadro count, not reacting masses |
| 3 | Shape of PCl₃ / [PCl₄]⁺ | `3.2`,`3.4`,`3.5` | `3.5` | Ask is shape only |
| 5 | Boltzmann y-axis / higher T | `1.1` | `8.2` | Kinetics / activation energy context |
| 6 | Min mass O₂ for propane | `1.1` | `2.4` | Gas volume + reacting mass |
| 7 | First IE O vs N | `1.3` | `1.4` | Option “p orbital” stole the tag |
| 8 | Most ideal gas | `12.1` | `4.1` | Distractor “ammonia” stole the tag |
| 10 | Haber heat exchanger purpose | `7.1`,`7.2` | `8.1`,`12.1` | Answer about speeding reaction; N chemistry |

Full table: [spot-check-notes.md](spot-check-notes.md).

## Re-export after fixing JSON

```bash
source .venv/bin/activate
python - <<'PY'
import json
from pathlib import Path
from chembank.export_md import write_question_markdown
from chembank.syllabus import resolve_titles, load_syllabus

syllabus = load_syllabus()
tagged = Path("draft/9701_s21_qp_11/tagged")
for p in tagged.glob("q*.json"):
    data = json.loads(p.read_text())
    data["topic_titles"] = resolve_titles(data["syllabus_codes"], syllabus)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    for d in (Path("questions"), Path("vault/questions")):
        write_question_markdown(data, d / f"{data['id']}.md")
PY
```
