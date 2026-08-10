# Examiner reports (local only)

PDFs here are **gitignored**. Use **year-scoped** clean names:

```text
9701_<year>_<season>_er.pdf
```

Examples:

```text
9701_2021_s21_er.pdf    # June 2021 Principal Examiner Report (all papers)
9701_2022_s22_er.pdf    # future years — separate files, do not overwrite
9701_2022_w22_er.pdf
```

One ER PDF usually covers all paper variants for that session; `chembank ingest` / `er-extract --paper 11` slices the variant you need.

Structured extracts go to `draft/er/` (also gitignored):

```text
draft/er/9701_s21_er_11.json   # Paper 11 slice for MJ 2021
draft/er/9701_s21_er.json      # full multi-paper extract (optional)
```

ER difficulty / facility is **scoped to that year/session/paper**. Do not treat it as universal LO difficulty across years. Never invent `% correct`.

```bash
# Standalone
chembank er-extract raw/reports/9701_2021_s21_er.pdf --paper 11
chembank er-merge draft/er/9701_s21_er_11.json -t draft/9701_s21_qp_11/tagged

# Or via ingest (auto if ER PDF exists + tagged/ present)
chembank ingest s21 11
```
