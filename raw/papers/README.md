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
