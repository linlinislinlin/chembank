# 结构题导出与 Part 裁切（vault-structured）

配合 [SKILL.md](SKILL.md)。实现主要在：

| 模块 | 职责 |
|------|------|
| `src/chembank/structured_parts.py` | 最小小题切分；共享 stem / letter preamble 前置；止于下一 part 标记 |
| `src/chembank/figures.py` | `structured_part_paper_clips`、`mark_scheme_part_clips`、`_structured_band_span` |
| `src/chembank/audit.py` | `_audit_structured_part_clips`（bleed + stem/preamble 门） |
| `src/chembank/export_vault.py` | 写入 `vault-structured/` + 渲染 `*-paper.png` / `*-ms.png` |

## Part QP clip 硬边界（MUST）

1. **终点**：下一 `(b)`/`(c)`/…、下一 `(ii)`/`(iii)`/…、或下一主问题 — **禁止**包含后续字母 preamble。
2. **共享 stem**：主问题 intro（首个 `(a)` 前）必须出现在该题每个 part 的 clip/正文。
3. **Letter preamble**：`(b)` 下、`(i)` 前的背景必须出现在该字母下每个 roman part。
4. **跨页**（`_structured_band_span`）：
   - 终页 **硬停** `end_y`，不得 pad 越过下一 part/题号。
   - **禁止**用旧版 ~76pt min-height 把下一 opener 垫进本 part（曾导致 letter/Q bleed）。
   - 下一页若只剩极短 sliver（仅下一标记），应跳过续页而非垫高吞入。
5. **MS clip**：`mark_scheme_part_clips` 按 **同一** part label 取行；与 QP part 一一对应。

## Audit 门（已接线 — 完成前必跑）

```bash
chembank audit s21:21   # 或当前卷 ref；须 exit 0
```

| 码 | 含义 |
|----|------|
| `next_question_bleed` | clip 含下一主问题 |
| `next_letter_bleed` | clip 含下一字母 part（如 `(b)` 进了 `1(a)(iii)`） |
| `next_roman_bleed` | clip 含下一罗马 part |
| `missing_shared_stem` | 缺主问题共享 stem |
| `missing_letter_preamble` | roman part 缺所属 letter preamble |
| `missing_ms_png` / `missing_ms_embed` | 缺同 part MS 图 |

无单独的 “wrong MS part OCR” 失败码：MS 正确性靠 part-label 几何绑定 + 缺图门 + 抽查。

## Paper 21 lessons（摘要）

- `1(a)(iii)` **不得**含 “(b) Solid ethanedioic…”。
- `1(b)(i)` **必须**含 Q1 stem + `(b)` preamble。
- 跨页末 part（`2(b)`、`5(c)(ii)` 等）**不得**因 min-height 吞入下一标记。

完整验收表与 MUST 列表见 SKILL.md → **Part QP / MS 裁切** / **Paper 21 lessons**。
