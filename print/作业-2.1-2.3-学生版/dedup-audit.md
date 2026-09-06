# Dedup audit — IGCSE Chemistry homework · 2.1–2.3 (student)

Source: `vault-igcse/handouts/作业-2.1-2.3-学生版.md`

## Image hashes

All 29 `*-paper.png` paper clips have distinct SHA-256. No identical image was dropped.

Conservative whitespace trim did not change pixel size (already tight clips). Three leftover **full-page** structured scans were cropped to the question + marks only (footer / “Turn over” / barcode removed). Question numbers, tables, dotted answer lines, and mark allocations are intact:

| File | Why cropped | Kept content |
|---|---|---|
| img-022.png | leftover page after B1(b) table | table + [5] + [Total: 8] |
| img-026.png | leftover page after B2(d) Table 2.1 | table + [5] |
| img-029.png | leftover page after B2(e)(iii) | stem + dotted line + [1] + [Total: 14] |

Near-duplicate stems (same topic, different numbers or species) were **kept**:

- A18 neon \(A_r\) vs A19 europium % vs A20 copper isotopes
- A10 \(\mathrm{N}^{3-}\) configuration vs A9 particles with 2,8,8

## Dropped rows

| Dropped ID | Why | Kept ID |
|---|---|---|
| LO-DUMP | long 考纲 LO list not printed; replaced by one-line topic | H-TOPIC |

YAML frontmatter, `[[wikilinks]]`, and `→ [[题库首页]]` were never Manifest items (navigation / metadata, not exam blocks).

No `*-ms.png` and no 答案区 in the student Markdown.

kept 38 unique items; dropped 0 duplicates; student-no-answers 0

(LO-DUMP is the only `keep: false` row; it traces to H-TOPIC rather than a repeated question.)
