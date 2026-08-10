---
name: chembank-structured-tag
description: >-
  Tags CIE 9701 Chemistry structured past-paper questions (Paper 2 AS / Paper 4
  A Level, also Paper 5) with controlled syllabus codes, Obsidian MathJax
  chemistry formatting, per-part QP paper clips, and Mark Scheme screenshots.
  Exports only to vault-structured/. Use when the user asks to 打标签结构题、
  简答题打标、Paper 2、Paper 4、structured tag、导出结构题 Obsidian、vault-structured、
  chembank structured, or map qp21/qp22/qp41 questions to 9701 LO codes.
  For Paper 3 practical use chembank-practical-tag → vault-practical/.
---

# ChemBank 结构题打标签 + Obsidian 导出（vault-structured）

在本对话里：读 **每个最小小题** → 受控词表选 `syllabus_codes` + 最具体 `learning_outcomes` → **化学格式化** → **QP 截图 + MS 截图** → 写入 **`vault-structured/`**（**禁止**写入 MCQ 的 `vault/` 或实验库 `vault-practical/`）。

**禁止**调用外部 LLM API；**禁止**发明词表外的 `syllabus_codes` / `learning_outcomes` ids。

MCQ（Paper 1）请用 [chembank-syllabus-tag](../chembank-syllabus-tag/SKILL.md)。  
Paper 3 实验题请用 [chembank-practical-tag](../chembank-practical-tag/SKILL.md) → `vault-practical/`。  
批量编排见 [chembank-ingest](../chembank-ingest/SKILL.md)。

Part 裁切几何细节见 [export-and-figures.md](export-and-figures.md)（含 Paper 21 bleed 教训）。

## 默认笔记粒度（part-level）

| 选择 | 说明 |
|------|------|
| **默认：一最小小题一篇** | 如 `2(a)(i)` → `cie-9701-2021-mj-p21-q2a-i.md`；含该小题 QP 裁切 + **MS 裁切** |
| 可选索引 | 薄 `…-q2.md` 链到各子小题（export 自动生成） |

Frontmatter 必填：

- `question: "2(a)(i)"`
- `parent_question: "2"`
- `part: "(a)(i)"`
- `syllabus_codes` + ≥1 `learning_outcomes`
- `question_type: structured`

Assets：

- `assets/<id>-paper.png` — 该小题（或所属 band）QP 裁切
- `assets/<id>-ms.png` — **对应 MS 行/格截图（主答案面；勿依赖乱码 MS 文本）**

## Pre-done checklist（FORBIDDEN — 未清零不得标完成）

导出结束前 **必须** `chembank audit <ref>`（exit 0）。结构题门禁（均已接线于 `src/chembank/audit.py` → `_audit_structured_part_clips`）：

| # | FORBIDDEN | 检测 |
|---|-----------|------|
| F1 | 缺 `*-paper.png` / embed | `missing_paper_png` / `missing_paper_embed` |
| F1b | 缺 `*-ms.png` / embed | `missing_ms_png` / `missing_ms_embed` |
| F2 | 错题裁切 / 串题 | `foreign_or_wrong_stem` |
| F3 | 原子沙拉 OCR（有结构图时） | `atom_salad` |
| F4 | 页脚 / 页码泄漏 | `footer_leak` / `trailing_page_num` |
| F5 | 空 `learning_outcomes` | `empty_LO` |
| F6 | 反应箭头 / PUA / 离子电荷坏格式 | `bad_arrow` / `pua_chars` / `broken_ion_charge` |
| F7 | 空题干（仅图） | `empty_question_body` |
| F8 | 陈旧 / 过小 PNG | `tiny_paper_png` / `stale_or_wrong_paper_png` |
| F9 | 裁进下一主问题 | `next_question_bleed`（含 PDF 控制符夹在题号与词干之间） |
| F9b | 裁进下一字母 / 罗马 part | `next_letter_bleed` / `next_roman_bleed`（如 `2(b)` 含 `(c)`；`6(d)(i)` 含 `(ii)`） |
| F10 | 正文塞满 MS 乱码（`11111` / Marks 重复） | 应清空 `mark_scheme` 文本，只留 MS 图 |
| F11 | part 缺共享题干（Q stem / letter preamble） | `missing_shared_stem` / `missing_letter_preamble` |
| — | ~~缺 A–D~~ | **不适用**结构题（audit 会跳过 MCQ 选项门） |

```bash
source .venv/bin/activate
chembank audit s21:21          # auto → vault-structured/
# 或：chembank audit s21:21 --vault vault-structured
```

**完成前硬门**：对当前卷跑 `chembank audit <ref>`（例 `s21:21`）。exit ≠ 0 或仍有 `next_letter_bleed` / `next_roman_bleed` / `missing_shared_stem` / `missing_letter_preamble` → **禁止**标完成。

## Part QP / MS 裁切（FORBIDDEN / MUST）

下列规则对每个最小小题的 `*-paper.png`、draft 正文、`*-ms.png` **硬性强制**。违反即失败；修图/重切后重跑 audit。

| # | 规则 | 说明 |
|---|------|------|
| **C1** | **MUST 止于下一 part 边界** | Part QP clip **必须以**下一 `(b)`/`(c)`/…、下一 `(ii)`/`(iii)`/…、或下一主问题号为终点。**FORBIDDEN** 把后续字母 part 的 preamble（`(b)` 下、`(i)` 前的背景句）裁进上一小题。 |
| **C2** | **MUST 含共享主问题 stem** | 主问题号后、第一个 `(a)` 前的总述（如 “1 Ethanedioic acid… Mr = 90”）→ 该主问题下**每一个** part 的笔记/QP 裁切都要包含。Audit：`missing_shared_stem`。 |
| **C3** | **MUST 含 letter preamble** | `(b)`/`(c)` 标记下、第一个 `(i)` 前的共用背景 → 该字母下所有 roman part（`…b-i` / `…b-ii` …）都要包含。Audit：`missing_letter_preamble`。 |
| **C4** | **FORBIDDEN 跨页 min-height 吞下一题** | 跨页续裁**硬停**在本 part 的 `end_y` / 下一标记处。**禁止**用最小高度垫高把下一页顶部的下一 part / 下一题 opener 垫进来（`figures._structured_band_span`）。 |
| **C5** | **MUST MS = 同一 part** | `*-ms.png` 必须来自 `mark_scheme_part_clips` 对**同一** part label 的行/格；禁止邻行 / 邻 part MS。缺图 → `missing_ms_png`（无单独 wrong-MS OCR 码；靠 label 绑定 + 目视）。 |
| **C6** | **MUST audit 清零** | 完成前跑 `chembank audit <ref>`；`next_letter_bleed` / `next_roman_bleed` / `missing_shared_stem` / `missing_letter_preamble` / `next_question_bleed` 任一非零 → 未完成。 |
| **C7** | **FORBIDDEN 串主问题** | 末 part 不得含下一题号开场（例 `3(d)` 不得含 `4 Aqueous…`）。Audit：`next_question_bleed`。 |

实现锚点：`structured_parts.split_main_question_into_parts`（stem/preamble 前置 + 止于下一标记）、`figures.structured_part_paper_clips` / `_structured_band_span`（硬边界、无吞页）、`audit._audit_structured_part_clips`。

## Paper 21 lessons（失败反例 — 勿再犯）

来自 `9701_s21_qp_21` / vault-structured 的真实 bleed 教训：

| 失败 | 反例 | 正确 |
|------|------|------|
| **next_letter_bleed** | `q1a-iii`（`1(a)(iii)`）的 paper/OCR 含 **“(b) Solid ethanedioic…”** | `1(a)(iii)` 止于 `(b)` 之前；`(b)` preamble 只属于 `1(b)(i)`/`1(b)(ii)`… |
| **next_roman_bleed** | `6(d)(i)` 裁进 `(ii)` 正文 | 止于下一罗马标记 |
| **missing_shared_stem** | `1(b)(i)` 只有 `(b)` 段、缺 Q1 开场 “Ethanedioic acid… Mr = 90” | 每个 part 都带主问题 stem |
| **missing_letter_preamble** | `1(b)(ii)` 只有 `(ii)` 句、缺 `(b)` 下共用背景 | roman part 必须含所属 letter preamble |
| **跨页 min-height 吞页** | 跨页末 part（如 `2(b)`、`5(c)(ii)`）被垫高，吞入下一页 `(c)` / `(iii)` / 下一题号 | 硬停 `end_y`；短续页 sliver（仅下一 opener）应跳过，不垫 76pt 级 min-height |

抽查清单（每卷至少看一眼）：`q1a-iii` 无 `(b)`；`q1b-i` 有 Q1 stem + `(b)` preamble；跨页末 part 无下一字母/题号。

## 硬性规则（MUST）

0. **每小题 ≥1 个词表内 `learning_outcomes`**；父级 `syllabus_codes` 同步保留。
1. **`question_type`: `structured`**（或 `extended` / `practical` / `data`）；**不要**标成 `mcq`。
2. **每小题必有 QP 截图**：`## Question` 顶部 `![[assets/<id>-paper.png]]`。
3. **每小题必有 MS 截图**：`## Mark Scheme` 下 `![[assets/<id>-ms.png]]`（**图像优先**）。乱码 OCR（`1 1 1 1 1`、重复 Marks/Answer）**禁止**写入正文；`mark_scheme` 文本可空。
4. **化学格式**：与 MCQ skill 相同（ΔH^ominus、箭头、`\mathrm{[…]^{+}}`、去页脚）。
5. **有图时去掉原子沙拉 / 轴标签碎片**。
6. **双写**：`questions-structured/` **和** `vault-structured/questions/`；图在 `vault-structured/assets/`。考纲 hub 经 `vault-structured/syllabus` → `vault/syllabus` 符号链接共享。
7. **Paper 2 → AS-only（1–22）**；Paper 4 → 可用 A Level（`--all-codes` / topics 23–37）除非用户只要 AS。
8. **ER**：有则 merge 到 `parent_question`；禁止编造 facility %。
9. **`chembank audit` exit 0** 才算完成（含上方 C1–C7 / F9 / F9b / F11）。
10. 提醒用户 Obsidian **Cmd+R**（打开的是 `vault-structured`）。
11. **Part 裁切**：遵守上方 **Part QP / MS 裁切（C1–C7）** 与 **Paper 21 lessons**；细节见 [export-and-figures.md](export-and-figures.md)。

## 进度清单（每个 part）

```
ChemBank 结构题导出验收:
- [ ] 1. QP+MS 已命名放入 raw/papers/（如 9701_s21_qp_21.pdf）
- [ ] 2. chembank ingest <season> <paper> → draft/ 切最小小题 + ms_parts.json
- [ ] 3. 对每个 part 打标：syllabus_codes + ≥1 LO；parent_question + part；★按考查点（非装饰背景；焓变→5.x）
- [ ] 4. 化学格式 + 去页脚；有图无原子沙拉；MS 文本无乱码
- [ ] 5. ingest --export → vault-structured/：每 part 有 *-paper.png + *-ms.png（MS=同 part）
- [ ] 6. ★ chembank audit <ref> exit 0（含 missing_ms_*）
- [ ] 7. ★ audit 清零：next_letter_bleed / next_roman_bleed / missing_shared_stem / missing_letter_preamble / next_question_bleed；抽查跨页末 part 与 q1a-iii 无 “(b) Solid ethanedioic…”
- [ ] 8. ★ 随机抽 5 篇核对 LO 贴合考查点；若用过 --mock 则声明 provisional 并「按考查点重标 LO」
- [ ] 9. 提醒用户打开 vault-structured 并 Cmd+R
```

## 路径

| 用途 | 路径 |
|------|------|
| 考纲词表 | `syllabus/cie-9701-as-a-level-chemistry.yaml` |
| 切题草稿 | `draft/<paper_id>/q2a-i.txt`（一最小小题一文件） |
| MS 分块 | `draft/<paper_id>/ms_parts.json` + `ms_structured.json` |
| 打标 JSON | `draft/<paper_id>/tagged/q2a-i.json` |
| **QP 截图** | `vault-structured/assets/<id>-paper.png` |
| **MS 截图** | `vault-structured/assets/<id>-ms.png` |
| 输出 | `questions-structured/<id>.md` + `vault-structured/questions/<id>.md` |
| MCQ / 实验库（勿写入） | `vault/` · `vault-practical/` |

## 批量导入

```bash
source .venv/bin/activate

# 1) 放入：
#    raw/papers/9701_s21_qp_21.pdf
#    raw/papers/9701_s21_ms_21.pdf

chembank ingest s21 21
# → kind=structured vault=vault-structured
# → draft/9701_s21_qp_21/q1a-i.txt … + ms_parts.json

# 2) 本对话按 part 打标（每文件 ≥1 LO）
# 写 draft/.../tagged/q2a-i.json 后：

chembank ingest s21 21 --export
chembank audit s21:21   # MUST exit 0；须抓住 letter/roman bleed + shared stem/preamble
```

## 打标签规则（词表）

1. 只选 YAML 已有 `syllabus_codes`（优先最具体子主题）。
2. **必须**选最具体 `learning_outcomes`（**每 part ≥1**）。跨小问不要把整道主问题的 LO 全堆进一个 part。
3. `skills` / `command_words` / `difficulty` 照常；`marks` = 该小题卷面分（若可知）。
4. **不要**把考纲 LO 写进 `learning_objectives`。
5. 校验：`chembank codes --lo --code 3.1`；`python .cursor/skills/chembank-syllabus-tag/scripts/validate_codes.py <md>`

允许的 `question_type`：`structured` | `extended` | `practical` | `data`。

## 考查点打标（MUST — 防装饰性误标）

标的是**该 part 正在考查的技能**（command word + 计算/作图/解释），**不是**题干装饰性化学背景。

| # | 规则 | 说明 / 反例 |
|---|------|-------------|
| **T1** | **Tag the assessed skill** | 读 command word + 本 part 要求；勿把整题主题 LO 堆进每个 part |
| **T2** | **Enthalpy / Hess / ΔH → 5.x** | `Calculate ΔHf`、Hess cycle、reaction pathway + ΔH/Ea → `5.1` / `5.2`（用 `chembank los --code 5.1` / `5.2` 选最具体 LO）。**禁止**因 Period 3 氧化物列表标成 `4.2` |
| **T3** | **Prefer MS / asked calculation** | 上下文跨多主题时，选与 mark scheme / 所问计算一致的 LO |
| **T4** | **FORBIDDEN: intro compound list alone** | 开场 `Na₂O Al₂O₃ P₄O₆…` 或氯化物列表**不能**单独决定 LO |
| **T5** | **批末抽查** | 完成前随机抽 **5** 篇笔记核对 LO 是否贴合考查点；若用过 `chembank tag --mock` / 启发式 → **必须声明 provisional**，并要求人工或仔细 agent「按考查点重标 LO」 |

**失败反例（已修）：** `cie-9701-2022-fm-p22-q2c-iii`（P₄O₆ ΔHf from ΔHr + ΔHf(P₄O₁₀)）曾被标 `4.2` / `4.2-2`；正确为 `5.1`+`5.2` / `5.1-3b`+`5.2-2a`。

触发重标：用户说「**按考查点重标 LO**」→ 按上表重读 part + MS，改 `draft/.../tagged/*.json`，再 `chembank ingest <ref> --export`。

## 示例 id

| 小题 | id | draft |
|------|-----|-------|
| 2(a)(i) | `cie-9701-2021-mj-p21-q2a-i` | `tagged/q2a-i.json` |
| 2(b) | `cie-9701-2021-mj-p21-q2b` | `tagged/q2b.json` |

## 与 CLI / MCQ skill 的关系

| 方式 | 何时用 |
|------|--------|
| `chembank ingest s21 21` | 结构卷机械步骤；自动 `vault-structured/` |
| **本 Skill** | 无 API key；按 part 打标 + 验收 |
| `chembank-syllabus-tag` | **仅** Paper 1 MCQ → `vault/` |
| `chembank-practical-tag` | Paper 3 实验（topic 粒度）→ `vault-practical/` |
| `chembank audit s21:21` | 结构题质量门（无 A–D；要 MS 图 + part bleed/stem 门） |
