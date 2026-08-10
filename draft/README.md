# Draft outputs

Intermediate extraction and splits land here for human review.

After `chembank ingest s21 11` (or the legacy `pipeline`) you should see:

```text
draft/manifest.json               # machine snapshot of papers.yaml
draft/9701_s21_qp_11.txt          # full QP text
draft/9701_s21_ms_11.txt          # full MS text
draft/9701_s21_qp_11/
  index.json                      # 40 question boundaries
  ms_key.json                     # { "1": "C", ... }
  q1.txt … q40.txt                # per-question chunks (+ MS answer)
  tagged/qN.json                  # after syllabus tagging
```

Review `index.json` before tagging `syllabus_codes` + `learning_outcomes`.

Year-scoped Examiner Report extracts:

```text
draft/er/9701_s21_er_11.json      # 2021 MJ Paper 11 slice
draft/er/9701_s21_er.json         # optional full multi-paper extract
```

Paper registry (human-edited + updated by ingest): repo-root `papers.yaml`.
