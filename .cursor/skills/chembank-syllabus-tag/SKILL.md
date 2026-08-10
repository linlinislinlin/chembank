---
name: chembank-syllabus-tag
description: >-
  Tags CIE 9701 Chemistry past-paper questions with controlled syllabus codes,
  Obsidian MathJax chemistry formatting, and diagram PNG embeds (no external
  LLM API). Use when the user asks to 打标签、按考纲标題、syllabus tag、导出
  Obsidian、export vault、配图、diagram、化学格式、auto-tag ChemBank drafts、
  or map questions to 9701 topic codes for Obsidian export.
---

# ChemBank 考纲打标签 + Obsidian 导出（无需 API key）

在本对话里：读题 → 受控词表选 `syllabus_codes` + 最具体 `learning_outcomes` → **化学格式化** → **整题截图 + 配图** → 写入 **`vault/`（Paper 1 MCQ）**。  
**禁止**调用外部 LLM API；**禁止**发明词表外的 `syllabus_codes` / `learning_outcomes` ids 或 LO 原文。

Paper 2/4 结构题请用 [chembank-structured-tag](../chembank-structured-tag/SKILL.md) → `vault-structured/`。  
Paper 3 实验题请用 [chembank-practical-tag](../chembank-practical-tag/SKILL.md) → `vault-practical/`。

细节与命令见 [export-and-figures.md](export-and-figures.md)。

## Pre-done checklist（FORBIDDEN 失败态 — 未清零不得标完成）

导出/打标结束前 **必须**跑 `chembank audit`（exit 0）。下列失败态在 audit 中硬拒；**禁止**口头宣称完成：

| # | FORBIDDEN 失败态 | 检测 |
|---|------------------|------|
| F1 | Paper clip 残缺 / 缺 A–D（尤指 Section B q31–40 裁到陈述 3、无组合键） | `missing_A_or_D_in_clip` / `missing_B_or_C_in_clip` / `section_b_missing_combo_key` / `missing_paper_png` |
| F2 | 错题裁切（他题 stem 串进本图，如 Q3 出现 Calcium reducing…） | `foreign_or_wrong_stem` / `foreign_calcium_stmt` |
| F3 | 原子沙拉 / 键线 OCR 留在有图正文下（`C Br C Br…`） | `atom_salad` |
| F4 | 选项挤在一行；两列表被截断成乱码 | `options_run_together` |
| F5 | 缺反应箭头 / 残留 `≡` / Symbol PUA；离子电荷写成 `]+` 而非 `]^{+}` | `bad_arrow` / `pua_chars` / `broken_ion_charge` |
| F6 | 页脚/页码泄漏（`© UCLES`、`9701/…`、`[Turn over]`、题末孤立页码） | `footer_leak` / `trailing_page_num` |
| F7 | 空 `learning_outcomes` | `empty_LO` |
| F8 | ER 编造 facility / `% correct`（定性报告无数字时非 null） | `invented_facility` |
| F9 | Paper embed 下正文再重复 A–D 选项块 | `duplicate_options_under_paper` |
| F10 | Paper / focus PNG 裁进下一题（OCR 出现下一题号；跨页亦禁止 min-height 吞下一题） | `next_question_bleed` |
| F11 | 导出 `*-paper.png` 过小 / 过矮（空白或截断） | `tiny_paper_png` |
| F12 | 导出 PNG 与当前几何裁切不一致（陈旧截图） | `stale_or_wrong_paper_png` |
| F13 | `## Question` 下无任何正文（仅图或空） | `empty_question_body` |

```bash
# 每批导出后必跑（非 0 = 未完成）
source .venv/bin/activate
chembank audit s21:11 s21:12 s21:13
# 或：chembank audit          # 全部 vault/questions
```

## 硬性规则（MUST）— 每次导出前对照

0. **每题必须有 ≥1 个 `learning_outcomes` id**（词表内最具体 LO；父级 `syllabus_codes` 同步保留）。空 LO = 打标未完成。
1. **每题必须有完整试卷截图（主阅读面）**：  
   - 每道导出题在 `## Question` **顶部**嵌入整题 paper clip：`![[assets/<id>-qN-paper.png]]`  
   - 裁切 = **本题号 → 下一题号之前**（含 stem + 全部选项/陈述 1–3 + 题内 diagram/table）  
   - 截图是**主阅读面**；下方转录文本仅供搜索 / 打标 / LO  
   - **身份校验**：OCR 须以本题号开头且含本题 stem 关键词；残缺、切边、他题串图 → 拒绝并重裁  
   - **禁止串题**（反例）：Q3（PCl₃ 形状）出现 Q36 陈述 `3 Calcium is a stronger reducing…`  
   - **禁止裁进下一题**：paper / focus PNG 的 OCR **不得**出现下一题号开场（如本题 Q1 图底出现 `2 Where in the Periodic…`）  
   - 几何：题号在左缘 ~x≤62；Section B 缩进的 `1`/`2`/`3`（~x≈71）**不是**题号  
   - `chembank export-vault` **必须**为卷内每一题生成 `*-paper.png`（`include_paper_clips=True`）  
   - **Paper 1 MCQ 硬拒**：`*-paper.png` OCR **必须**含选项字母 **A、B、C、D**（不仅是 A 与 D）；缺任一则拒绝并重裁。横排选项（`A … B … C … D …`）与竖排/表格均适用  
   - **Section B / statement-combo 硬拒**：凡「Which statements…」/ 陈述 1–3 / Q31–40 组合题，裁切 **必须**含 A–D 组合键（`1, 2 and 3` / `1 and 2 only` / `2 and 3 only` / `1 only`）。**禁止**裁到陈述 3 就结束、下方无 A–D 表。跨页时把下页重印的 A–D 键拼进同一张 `*-paper.png`（键在图底部）；正文若出现 `responsesA toD` / `1, 2 and3…` 乱码则删除，以图为准  
   - **导出 PNG 一致性**：`chembank audit` 会把 vault 里的 `*-paper.png` 与当前 QP 几何裁切重渲对比；尺寸/哈希偏离 → `stale_or_wrong_paper_png`，须重跑 `export-vault`  
   - **禁止空题**：`## Question` 下除 paper embed 外须有可搜索正文（stem）；禁止只有图或空白  
   - **正文不重复 A–D**：已有 `*-paper.png` 且图内含选项时，body **只保留 stem**（可含表内数据 OCR 供搜索），**删除**重复的 `A …`/`B …`/`C …`/`D …` 选项块；禁止再挂只重复选项/数据表的冗余 Diagram  
2. **导出前刷新正文**：用带符号恢复的最新 `draft/.../qN.txt`（`chembank extract` / `export-vault`），不要沿用旧的丢符号正文。
3. **化学格式**（`chem_format` / `symbols`）：  
   - `ΔH₁⦵` → `$\Delta H_{1}^{\ominus}$`（标准态为 **上标** `\ominus`）  
   - 反应式必须有箭头 `→` 或 `\xrightarrow{...}`  
   - 禁止残留：空白箭头、`≡`、Symbol PUA（`U+F0AE` / `U+F0B0`° / `U+F044`Δ / `U+F070`π / `U+F073`σ 等）、孤儿「单独一行 ΔHc + 无箭头方程式」  
   - PDF 伪影 `≡` / `=`（夹在反应物与产物之间）→ 规范为 `→`  
   - 离子电荷：`[PCl₄]+` → `$\mathrm{[PCl_{4}]^{+}}$`（**禁止** `]+` 裸挂）  
   - 粘连词：`showboth` → `show both`（及 ofeach / responsesA toD 等）
4. **焦点配图**（额外 `*-qN.png`，不能替代整题截图）：  
   - diagram / Boltzmann / IR 光谱 / 结构选项题另裁完整焦点图  
   - **MCQ 结构选项**：一图覆盖 **A–D 全部**（含选项字母）；禁止分子从边缘切断、缺 C/D  
   - 光谱：整幅坐标轴 + 曲线；禁止只剩 `transmittance` / `wavenumber` 文本
5. **去掉乱码结构文本**（禁止失败态，见 Q22）：已有结构图 / `*-paper.png` / 光谱图时，正文**不得**残留键线 OCR「原子沙拉」，例如：  
   `C Br C Br C C Br C`、`C C Br C C Br C C Cl C C I`、`Cl H O Br`、`OH O`、`O O|`。  
   同时删除无实际选项文字的裸 `A`/`B`/`C`/`D` 行（结构已在图里）。  
   轴标签碎片（`T1`/`y`/`0`/`transmittance`/`4000 3000…`）一并删除。
6. **选项排版**：文本选项 A/B/C/D **各占一行**（`format_mcq_option_lines`）；两列表格式选项（如 PCl₃ / [PCl₄]⁺）用 markdown table。结构题以图为准，不要在图下再堆 OCR 碎片。
7. **页脚噪音**：剔除 `9701/11/M/J/21`、`© UCLES`、`[Turn over]`、`Page N of N`、题末孤立页码（如 Q15 末尾的 `7`）。用 `split.strip_footer_noise`。
8. **双写 + 资源**：同一内容写入 `questions/` **和** `vault/questions/`；图在 `vault/assets/`。
9. **结束后提醒用户**：Obsidian `Cmd+R` 刷新（或重开笔记）。
10. **Examiner Report（有则必挂，按年）**：该 year/session/paper 若有 ER，导出前必须 merge；无则 facility/notes 留空。禁止跨年套用难度，禁止编造 % correct。
11. **`chembank audit` 必须 exit 0**：见上方 Pre-done checklist；失败则修图/修正文/重导出后再 audit。

## 进度清单（每次打标/导出请复制勾选）

```
ChemBank 导出验收:
- [ ] 1. 确认 draft/tagged 范围（题号）
- [ ] 2. 加载考纲词表（AS-only 默认）；syllabus_codes ∈ 词表；learning_outcomes ∈ LO 词表
- [ ] 2b. ★每题必须有 ≥1 个 learning_outcomes id（词表内）；空 LO = 打标未完成，禁止导出当完成
- [ ] 2b2. ★按考查点打标（非装饰背景；焓变/Hess/bond energy→5.x；禁仅凭化合物列表）；批末抽 5 题；--mock = provisional
- [ ] 2c. ★若该年该卷有 Examiner Report：已 er-extract + er-merge；frontmatter 含 er_year/er_session/er_paper；有评论题含 examiner_notes；无数字则 facility/percent_correct 为 null（不编造）
- [ ] 3. 刷新 draft（extract + 符号恢复）
- [ ] 4. 化学格式：ΔH^ominus 上标；反应箭头为 →（无 ≡/空白/PUA）；离子 ]^{+}；无孤儿 ΔHc；无 showboth 粘连
- [ ] 5. MCQ 选项：A/B/C/D 各一行；两列表格式选项用 markdown table
- [ ] 6. 页脚：无 © UCLES / 9701/…/… / [Turn over] / 题末孤立页码
- [ ] 7. ★每题必有 *-paper.png 整题截图（## Question 顶部）；OCR=本题号+stem+选项字母A–D；Section B 必含 A–D 组合键；无他题串图；PNG 非空/非陈旧
- [ ] 8. 焦点图：diagram/光谱/结构选项完整；A–D 结构全可见、不切分子
- [ ] 9. 有图时去掉键线 OCR / 轴标签碎片（禁：Q22 式 `C Br C Br…` 留在图下）
- [ ] 10. 双写 questions/ + vault/questions/；assets 在 vault/assets/；LO hub 在 vault/syllabus/lo/
- [ ] 11. ★chembank audit <refs>  exit 0（F1–F13 全清零；否则禁止标完成）
- [ ] 12. 抽查：q1 数据表/同位素、q3 形状表、焓变(q4)、结构 MCQ(q21)、光谱(q26)、Section B(q36)、页码(q15)、ER 难问(q14)；确认无下一题 bleed、paper 下无重复 A–D
- [ ] 13. 提醒用户 Obsidian Cmd+R
```

## 路径

| 用途 | 路径 |
|------|------|
| 考纲词表 | `syllabus/cie-9701-as-a-level-chemistry.yaml` |
| 切题草稿 | `draft/<paper_id>/q*.txt` |
| 打标 JSON | `draft/<paper_id>/tagged/qN.json` |
| Examiner Report PDF（按年） | `raw/reports/9701_<year>_<season>_er.pdf`（gitignored） |
| ER 结构化 JSON | `draft/er/9701_<season>_er_<paper>.json` |
| **整题截图（必有）** | `vault/assets/<id>-qN-paper.png` |
| 焦点配图 | `vault/assets/<id>-qN.png` |
| 输出 | `questions/<id>.md` 与 `vault/questions/<id>.md` |
| 核心模块 | `src/chembank/{chem_format,figures,export_md,export_vault,examiner_report,symbols,split}.py` |

## Batch ingest new paper（与 CLI 对齐）

加新卷时先走机械流水线，再在本 skill 打标/验收。命名与命令见仓库根 `README.md` / `papers.yaml`。

| 文件 | 约定 |
|------|------|
| QP | `raw/papers/9701_<season>_qp_<paper>.pdf` |
| MS | `raw/papers/9701_<season>_ms_<paper>.pdf` |
| ER（按年，可选） | `raw/reports/9701_<year>_<season>_er.pdf` |

```bash
source .venv/bin/activate

# 例：June 2021 Paper 12 — 放入 PDF 后
chembank ingest s21 12
# → extract + split + MS；有 ER 则 er-extract；更新 papers.yaml
# → 尚无 tagged/ 时跳过 export（正常）

# 本对话：给 draft/9701_s21_qp_12 打标（syllabus_codes + ≥1 LO）
# 写 draft/.../tagged/qN.json 后：

chembank ingest s21 12 --export
# = er-merge（若可）+ export-vault（每题 *-paper.png + 双写 + LO hubs）

# ★ 质量门：必须 exit 0 才算完成
chembank audit s21:12

# 下一卷 / 多卷机械步骤
chembank ingest w22 11
chembank batch s21:12 s21:13
chembank audit s21:12 s21:13
chembank papers
```

**本 skill 在批量场景强制：** 上方「Pre-done checklist」+「硬性规则」+「进度清单」每一项；`chembank audit` 非 0、缺 LO、缺 `*-paper.png`、错裁、原子沙拉、未 merge 已有 ER、编造 facility % → **不得声称完成**。

编排入口也可触发 [chembank-ingest](../chembank-ingest/SKILL.md)。

## 推荐工作流（优先 CLI 一键导出）

打完标签（或已有 `tagged/*.json`）后，**优先**（会为**每一题**生成完整 `*-paper.png`）：

```bash
source .venv/bin/activate

# 一键（推荐）：ingest 会在 tagged/ 存在时 er-merge + export-vault
chembank ingest s21 11 --export

# 或分步：
chembank er-extract raw/reports/9701_2021_s21_er.pdf --paper 11
chembank er-merge draft/er/9701_s21_er_11.json -t draft/9701_s21_qp_11/tagged
chembank export-vault raw/papers/<qp>.pdf \
  -d draft/<paper_id> \
  -m raw/papers/<ms>.pdf \
  --vault vault \
  --export-md questions
```

仅重写 Markdown/配图、不重抽 PDF：

```bash
chembank export-vault raw/papers/<qp>.pdf \
  -d draft/<paper_id> \
  --vault vault --export-md questions --no-refresh
```

## 打标签规则（词表）

1. 只选 YAML 已有 `syllabus_codes`（优先最具体子主题，如 `2.4`）。
2. **必须同时**选最具体的 `learning_outcomes` ids（如 `3.1-1`、`2.4-1a`）— **每题 ≥1 个**：
   - 来源：`syllabus/cie-9701-as-a-level-chemistry.yaml` 各 subtopic 下的 `learning_outcomes`
   - **禁止**自造 LO id 或改写官方 LO 原文；导出时用词表 resolve 文本
   - 有 LO 时 **必须**保留对应父级 `syllabus_codes`（如 `3.1-1` → 至少含 `3.1`）
   - **禁止**以「不确定」为由留下 `learning_outcomes: []`；拿不准时选最接近的 1–2 个 LO，并在备注/验收里标 uncertain
   - 无 LO 的 tagged JSON / 导出笔记视为**打标未完成**，不得当作完成验收
3. 1–3 个 code；`topic_titles` 与词表 title 一致。
4. 填 `skills` / `question_type` / `difficulty` / `command_words`；MCQ：`marks: 1`，`ms_answer` 来自 MS。
5. **不要**把考纲 LO 写进 `learning_objectives`（该字段仅自由文本教学备注）；考纲 LO 只用 `learning_outcomes`。
6. **Examiner Report（按年/卷，有则必挂）**：
   - 若该 **year + session + paper** 已有 ER（`raw/reports/9701_<year>_<season>_er.pdf` 或 `draft/er/9701_<season>_er_<paper>.json`），打标/导出前 **必须** `er-merge`，把 facility / band / notes / common_errors 写入 tagged JSON。
   - ER 数据 **只作用于该年该卷**；禁止当成同一 LO 的跨年「通用难度」。字段保留身份：`er_year` / `er_session` / `er_paper` / `examiner_report` / `examiner_report_source`。
   - **禁止发明** `% correct` / facility / discrimination；PDF 只有定性描述时：存 `examiner_band` + `examiner_notes`，并用文档化映射更新 `difficulty`（easy→2，particularly_difficult→5，`difficulty_source: examiner_report_qualitative`）。
   - **无 ER** 时：`facility` / `percent_correct` / `examiner_notes` 留空，不编造。
   - CLI：`chembank er-extract <pdf> --paper 11` → `chembank er-merge draft/er/9701_s21_er_11.json -t draft/.../tagged`
7. 校验 / 浏览词表：

```bash
chembank codes --lo --code 3.1          # 或 chembank los --code 3.1
chembank los --as-only | head
python .cursor/skills/chembank-syllabus-tag/scripts/validate_codes.py path/to/file.md
```

允许的 `skills`：`recall` | `explain` | `calculate` | `data-analysis` | `practical` | `compare` | `evaluate` | `draw`  
允许的 `question_type`：`mcq` | `structured` | `extended` | `practical` | `data`

## 考查点打标（MUST — 防装饰性误标）

标的是**该题正在考查的技能**（command word + 计算/推理），**不是**装饰性化学背景。

| # | 规则 | 说明 / 反例 |
|---|------|-------------|
| **T1** | **Tag the assessed skill** | 读 stem 所问；勿因试剂/化合物名堆无关 LO |
| **T2** | **Enthalpy / Hess / ΔH / bond energy → 5.x** | 焓变计算、Hess、bond energy 表 → `5.1` / `5.2`。**禁止**因同位素/周期表背景抢成 `1.2` / `4.2` / `9.x`（除非题干明确考那些） |
| **T3** | **Prefer MS / asked calculation** | 多主题时选与答案键/所问一致的 LO；ΔH 仅作平衡条件时可为 `7.1`（非强制 `5.x`） |
| **T4** | **FORBIDDEN: intro compound list alone** | 开场化合物/氧化物列表不能单独决定 LO |
| **T5** | **批末抽查** | 完成前随机抽 **5** 题核对 LO；若用过 `chembank tag --mock` → **声明 provisional**，要求「按考查点重标 LO」后再当正式标签 |

触发重标：用户说「**按考查点重标 LO**」→ 重读题干 + MS，改 `draft/.../tagged/*.json`，再 `chembank ingest <ref> --export`。

## 手工导出时（无 CLI 时）

1. `chembank extract` → `chembank split`（符号恢复 + `strip_footer_noise`）  
2. 更新 `tagged/qN.json` 的 `body` 为最新 draft  
3. `chembank.figures.export_question_figures`（**必须**含每题 `*-paper.png` + 可选焦点图）  
4. `chembank.export_md.write_question_markdown(..., figure_paths=[...])`  
5. 同步到 `questions/` 与 `vault/questions/`

**不要**手写未格式化的 `ΔH₁⦵` 明文进 vault（应使用 MathJax）。

## 验收抽查（已知易错题型）

| 题型 | 通过标准 |
|------|----------|
| **每题截图** | `*-paper.png` 存在；`## Question` 顶嵌；OCR=本题 stem |
| 形状表（如 q3） | 截图含 PCl₃/[PCl₄]⁺ 两列表；无 Calcium 串题 |
| 焓变 / Hess（如 q4） | `$\Delta H_{n}^{\ominus}$`；`\xrightarrow` 或 `→`；无孤儿 `ΔHc` |
| 反应箭头伪影（如 q9） | 方程式为 `→`，不是 `≡` / `` / 空白 |
| 选项挤排（如 q2） | 文本 A–D 各一行；截图保留试卷横排 |
| 结构 MCQ（如 q21/q22） | 图含 A–D 全部结构；正文无 `C Br C…` 原子沙拉 |
| 光谱+结构（如 q26） | IR 全图 + A–D 结构；无轴标签残片 |
| Section B（如 q31/q35/q36） | 截图含陈述 1–3 **且**底部含 A–D 组合键；禁裁到陈述 3 为止；正文无 `responsesA toD` 乱码 |
| 页脚泄漏（如 q15） | 题末无孤立页码数字 |

## 触发示例

- 「用考纲给 draft/9701_s21_qp_11 的 q1–q5 打标签并导出 Obsidian」
- 「导入 s21 qp12 / 批量加一卷新题」
- 「导出 vault / 刷新配图和化学格式」
- 「每个题目都配完整截图」
- 「chembank syllabus tag 全卷（分批）」
- 「根据导出错误改 skill」

## 与 CLI 的关系

| 方式 | 何时用 |
|------|--------|
| `chembank ingest` / `batch` | 新卷机械步骤：extract→split→(er)→(export)；更新 `papers.yaml` |
| **本 Skill + `export-vault` / `ingest --export`** | 无 API key；打标+导出默认路径（含全卷整题截图） |
| **`chembank audit`** | 导出后质量门；**exit 0 前不得标完成**（见 Pre-done F1–F13） |
| `chembank tag` + API | 用户自备 key 批量打标 |
| `chembank tag --mock` | **仅冒烟 / provisional**；启发式标签**不作正式标签**，须人工或 skill「按考查点重标 LO」 |

用户未提供 API key 时走本 Skill；导出阶段用 `ingest --export` 或 `export-vault`，然后 **`chembank audit`**；**不要省略**整题截图、焦点配图、选项排版、页脚清理、LO、ER（有则必挂）与化学格式。

`chembank ingest --export` 在 tagged JSON 已存在时会导出——**若标签来自 `--mock`，导出内容仍是 provisional**，不得标为打标完成。
