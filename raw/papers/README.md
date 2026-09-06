# Past papers (local only)

PDFs here are **gitignored**. Use CIE-style clean names so `chembank ingest` can find them:

```text
9701_<season>_qp_<paper>.pdf
9701_<season>_ms_<paper>.pdf
```

| Token | Meaning |
|-------|---------|
| `s21` | June (MJ) 2021 |
| `w21` | November (ON) 2021 |
| `m22` | March (FM) 2022 |
| `11` / `12` / `13` | Paper 1 MCQ → `vault/` |
| `21` / `22` / `23` | Paper 2 structured → `vault-structured/` |
| `41` / `42` / `43` | Paper 4 structured → `vault-structured/` |

Examples:

```text
9701_s21_qp_11.pdf
9701_s21_ms_11.pdf
9701_s21_qp_12.pdf          # MCQ variant
9701_s21_ms_12.pdf
9701_s21_qp_21.pdf          # Paper 2 structured
9701_s21_ms_21.pdf
9701_w22_qp_11.pdf
9701_w22_ms_11.pdf
9701_syllabus_2025-2027.pdf # optional reference (not ingested)
```

Examiner Reports live under [`../reports/`](../reports/) as `9701_<year>_<season>_er.pdf`.

After dropping QP + MS:

```bash
chembank ingest s21 12    # MCQ → vault/
chembank ingest s21 21    # structured → vault-structured/
```

## IGCSE 0620 (isolated from 9701)

```text
0620_<season>_qp_<paper>.pdf
0620_<season>_ms_<paper>.pdf
```

| Token | 0620 Extended |
|-------|----------------|
| `21` / `22` / `23` | Paper 2 MCQ → `vault-igcse/` |
| `41` / `42` / `43` | Paper 4 theory → `vault-igcse-structured/` |
| `61` / `62` / `63` | Paper 6 ATP → `vault-igcse-practical/` |

Always use the full stem so ingest does not treat these as 9701 Paper 2 structured:

```bash
chembank ingest 0620_s25_qp_21
chembank ingest 0620_s25_qp_21 --export
chembank audit 0620_s25_qp_21
```

Examiner reports: `raw/reports/0620_<year>_<season>_er.pdf`. Registry: `papers-igcse.yaml`.
