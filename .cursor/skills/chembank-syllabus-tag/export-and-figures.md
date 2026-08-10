# Obsidian 导出：化学格式 + 配图 + 排版

## 模块

| 模块 | 作用 |
|------|------|
| `src/chembank/symbols.py` | PDF 矢量 ΔH 恢复；Symbol PUA / `≡` → `→`；反应箭头插入 |
| `src/chembank/chem_format.py` | MathJax；`format_mcq_option_lines`；两列形状表 `format_mcq_options_table` |
| `src/chembank/split.py` | 切题；`strip_footer_noise`（页脚 / 题末页码） |
| `src/chembank/figures.py` | **每题**整题 paper clip + 焦点图（光谱 / A–D 结构块） |
| `src/chembank/export_md.py` | 写 Markdown：Question 顶嵌 `*-paper.png`；焦点图进 `## Diagram`；可选 `## Examiner report` |
| `src/chembank/export_vault.py` | 一键：刷新抽取 + 清噪音 + **全卷 paper clips** + 双写 |
| `src/chembank/examiner_report.py` | 按年抽取 Principal Examiner Report；定性 band→difficulty；merge 进 tagged |
| `src/chembank/syllabus.py` | 考纲 code + LO 词表 load / validate / resolve |

## Examiner Report（year-scoped）

CIE ER 通常只有定性「easy / particularly difficult」+ 逐题评论，**没有** facility / % correct。禁止编造数字。

| 路径 | 说明 |
|------|------|
| `raw/reports/9701_2021_s21_er.pdf` | 2021 June 全卷 ER（gitignored） |
| `draft/er/9701_s21_er_11.json` | Paper 11 结构化切片 |

```bash
chembank er-extract raw/reports/9701_2021_s21_er.pdf --paper 11
chembank er-merge draft/er/9701_s21_er_11.json -t draft/9701_s21_qp_11/tagged
# 然后 export-vault（可用 --no-refresh 只重写 MD）
```

难度映射（仅当 ER 写明 band）：`easy`→2，`particularly_difficult`→5，`difficulty_source=examiner_report_qualitative`。  
字段身份：`er_year` / `er_session` / `er_paper` / `examiner_report` — 未来 2022/2023 报告另存，不覆盖。

### Obsidian：查难问（本卷 ER）

```dataview
TABLE question, difficulty, examiner_band, common_incorrect, percent_correct
FROM "questions"
WHERE er_year = 2021 AND er_paper = 11 AND examiner_band = "particularly_difficult"
SORT difficulty DESC, question ASC
```

```dataview
TABLE question, difficulty, facility, percent_correct, examiner_band
FROM "questions"
WHERE er_year = 2021 AND difficulty >= 4
SORT difficulty DESC
```

无数字 facility 时用 `examiner_band` / `difficulty`；有未来年份报告时加 `er_year = 2022` 等条件，避免跨年混查。

## Batch ingest new paper

```bash
# 1. Drop PDFs:
#    raw/papers/9701_s21_qp_12.pdf
#    raw/papers/9701_s21_ms_12.pdf
#    raw/reports/9701_2021_s21_er.pdf   # optional, year-scoped

source .venv/bin/activate
chembank ingest s21 12                 # extract + split (+ er-extract)
# … tag draft/9701_s21_qp_12 (this skill) …
chembank ingest s21 12 --export        # er-merge + full-paper clips + dual-write

chembank batch s21:12 s21:13           # loop mechanical steps
chembank papers                        # registry
```

`ingest` 在尚无 `tagged/` 时不会 export；打标完成后再 `--export`。详见仓库 `README.md`。

## 一键命令（刷新全部整题截图）

```bash
source .venv/bin/activate

# 推荐（有 tagged/ 时）
chembank ingest s21 11 --export

# 等价分步
chembank export-vault raw/papers/9701_s21_qp_11.pdf \
  -d draft/9701_s21_qp_11 \
  -m raw/papers/9701_s21_ms_11.pdf \
  --vault vault \
  --export-md questions
```

仅重写 Markdown/配图、不重抽 PDF 文本：

```bash
chembank export-vault raw/papers/9701_s21_qp_11.pdf \
  -d draft/9701_s21_qp_11 \
  --vault vault --export-md questions --no-refresh
```

`export-vault` **始终**调用 `export_question_figures(..., include_paper_clips=True)`，为卷内 **每一题** 写出 `vault/assets/<id>-qN-paper.png`。

产出：

| 产物 | 路径 |
|------|------|
| 笔记（双写） | `vault/questions/<id>.md`、`questions/<id>.md` |
| **整题截图（必有）** | `vault/assets/<id>-qN-paper.png` |
| 焦点图（可选） | `vault/assets/<id>-qN.png`、`…-qN-2.png`… |

命名示例：`cie-9701-2021-mj-p11-q3-paper.png`

## 配图硬规则：每题完整试卷截图

**每道题都必须有**一张完整 paper clip，作为 `## Question` 的主阅读面：

1. **范围**：本题号基线 → 下一题号之前（含 stem、A–D 或陈述 1–3、题内 diagram/table）。
2. **嵌入**：`![[assets/<id>-qN-paper.png]]` 放在 `## Question` **第一行**。
3. **文本次要**：下方转录供搜索/打标；以截图为准阅读原卷排版。  
   - 已有 `*-paper.png` 且图含 A–D 时：**删除正文重复的 A–D 选项块**（`export_vault._strip_duplicate_mcq_options`）；body ≈ stem only。  
   - 禁止再挂只重复选项行 / 数据表的冗余 Diagram。
4. **身份校验**（`figures.question_paper_clips`）：
   - 题号几何：只认左缘题号（~x≤62）。缩进陈述号 `1`/`2`/`3`（~x≈71）不是题号。
   - 先到先得：同一题号以较早页为准，禁止后页陈述号覆盖前页真题。
   - OCR 须以本题号开头；短裁切无 A–D 且像他题陈述 → **丢弃重裁**。
   - 反例（禁止）：Q3 的 `*-paper.png` 出现 `Calcium is a stronger reducing agent than magnesium.`
   - **禁止下一题 bleed**：OCR 不得出现下一题号开场（`next_question_bleed`）。
   - **跨页续裁**：多页题可拼接 bands，但终页须硬停在下一题号之前；**禁止**用 min-height 垫高把下一题 opener 吞进本题（与结构题 Paper 21 bleed 同类失败）。结构题 part 级规则见 [chembank-structured-tag](../chembank-structured-tag/SKILL.md)。
   - **MCQ 必含 A 与 D**：paper-clip OCR 必须同时出现选项字母 A、D；否则拒绝。
   - **Statement-combo / Section B**：陈述 1–3 之后必须有 A–D 组合键（`1, 2 and 3` / `1 and 2 only` …）。裁到陈述列表结束、无选项表 → **硬拒**。键在下页重印或在 Section B 页眉时，拼接到 `*-paper.png` 底部（`PaperClip.bands`）。
5. **不完整则拒**：缺选项、切分子、串题、空条 → 不得写入 vault。

### 焦点图（额外，不能替代整题截图）

出现任一项则**额外**裁完整焦点 PNG：

- 题干含 `diagram` / `figure` / `shown below` / `infra-red` / `spectrum`
- MCQ 键线/结构式（横向 A–D，须有结构矢量墨迹；纯文字选项行不要单独裁）
- Boltzmann / 能量剖面等矢量图
- **不要**为数据表（protons/neutrons 表等）单独裁 Diagram——已在 paper clip 内
- 焦点裁切 **钳制在本题 y 带内**；OCR 含下一题号 → 丢弃

#### MCQ 结构选项（A–D）

1. 一图覆盖全部选项（含字母）；宽度须盖到 D  
2. 正文键线 OCR → **必须删除**（图已覆盖）  
3. **禁止失败态（Q22）**：paper clip 下仍出现 `C Br C Br…` 原子沙拉

#### 光谱

- 裁切须含坐标轴刻度、轴标题与曲线  
- 有图后删除正文中的轴标签残片

### 嵌入位置

```markdown
## Question

![[assets/cie-9701-2021-mj-p11-q3-paper.png]]

3 Phosphorus forms two chlorides. …

## Diagram

![[assets/cie-9701-2021-mj-p11-q21.png]]
```

（上例：paper 已含 A–D 时 body 不再重复选项表；仅结构/光谱等焦点图进 Diagram。）

## 化学格式硬规则

| 错误形态 | 正确处理 |
|----------|----------|
| `ΔH₁⦵` 裸文本 | `$\Delta H_{1}^{\ominus}$` |
| 孤儿 `ΔHc` 行 + 无箭头方程式 | 合并并插入 `→` / `\xrightarrow` |
| `` / `≡` / `U+F0AE` 当箭头 | 规范为 `→` |
| `A … B … C … D …` 同行 | 拆成四行 |
| 两列形状表（PCl₃ / [PCl₄]⁺） | markdown table（`format_mcq_options_table`） |

## 页脚噪音硬规则

`split.strip_footer_noise` 必须去掉：

- `© UCLES…`
- `9701/11/M/J/21`（及同类卷号行）
- `[Turn over]` / `Page N of N`
- **题末**孤立页码（`7`、`10`…）；保留题干中的轴数字（如光谱 `0`/`50`/`100`）

## Learning outcomes（考纲 LO）

**硬性要求**：每题 `learning_outcomes` 至少 1 个词表内 id；空列表 = 打标未完成，`validate_codes.py` 会 FAIL。

Frontmatter 示例：

```yaml
syllabus_codes:
- '3.1'
learning_outcomes:
- '3.1-1'
learning_outcome_texts:
- define electronegativity as the power of an atom to attract electrons to itself
```

正文会多一节 `## Learning outcomes`，链到 `vault/syllabus/lo/<id>.md`。

## Pre-done checklist（FORBIDDEN — `chembank audit` 硬拒）

导出完成后、宣称完成前 **必须**：

```bash
source .venv/bin/activate
chembank audit s21:11          # 单卷
chembank audit s21:11 s21:12 s21:13
chembank audit                 # 全部 vault/questions
```

| Code | FORBIDDEN 失败态 |
|------|------------------|
| `missing_paper_png` / `missing_paper_embed` | 无整题截图或未嵌入 `## Question` 顶 |
| `missing_A_or_D_in_clip` | MCQ paper clip OCR 缺选项字母 A 或 D |
| `missing_B_or_C_in_clip` | 有 A/D 但缺 B 或 C（横排/表格未裁全） |
| `section_b_missing_combo_key` | Section B / 陈述组合题裁切无 A–D 键（`1, 2 and 3` …） |
| `tiny_paper_png` | 导出 `*-paper.png` 过小/过矮（空白或截断） |
| `stale_or_wrong_paper_png` | 导出 PNG 与当前 QP 几何裁切重渲不一致 |
| `empty_question_body` | `## Question` 下除 embed 外无正文 |
| `foreign_or_wrong_stem` / `foreign_calcium_stmt` | 错题裁切 / 他题串图 |
| `atom_salad` | 有图仍留键线 OCR（`C Br C Br…`） |
| `options_run_together` | A–D 挤在同一行 |
| `bad_arrow` / `pua_chars` / `broken_ion_charge` | `≡`/Symbol PUA；`] +` 非 `]^{+}` |
| `glued_words` | `showboth` / `responsesA toD` 等粘连 |
| `footer_leak` / `trailing_page_num` | 页脚 / 题末页码泄漏 |
| `empty_LO` / `unknown_LO` | 空或词表外 learning_outcomes |
| `invented_facility` | 编造 `facility` / `percent_correct` |

实现：`src/chembank/audit.py`；CLI：`chembank audit`。非 exit 0 → **禁止**标完成；修后重跑 `export-vault` + `audit`。

## 用户侧

导出完成后提醒：**Obsidian → `Cmd+R` 刷新**，或关闭重开该笔记。
