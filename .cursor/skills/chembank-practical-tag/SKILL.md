---
name: chembank-practical-tag
description: >-
  Tags CIE 9701 Chemistry Paper 3 practical/experimental questions by controlled
  practical topic (not fine part-level), with optional syllabus LO codes, full
  experiment-block QP paper clips, and Mark Scheme screenshots. Exports only to
  vault-practical/. Use when the user asks to 实验题、Paper 3、practical、滴定、
  qualitative analysis、thermometric、gravimetric、gas volume、rate experiment、
  vault-practical、questions-practical、chembank practical, or map qp31/qp32/qp33
  questions to practical topics.
---

# ChemBank 实验题打标签 + Obsidian 导出（vault-practical）

在本对话里：读 **每个实验板块 / 主问题** → 受控 `practical_topic`（± 可选考纲 LO）→ **化学格式化** → **该板块 QP 整段截图 + MS 截图** → 写入 **`vault-practical/`**（**禁止**写入 `vault/` 或 `vault-structured/`）。

**禁止**调用外部 LLM API；**禁止**发明词表外的 `syllabus_codes` / `learning_outcomes` ids；**禁止**发明下列以外的 `practical_topic`。

| 试卷 | Skill | Vault |
|------|-------|-------|
| Paper 1x MCQ | [chembank-syllabus-tag](../chembank-syllabus-tag/SKILL.md) | `vault/` |
| Paper 2/4/5x 结构题 | [chembank-structured-tag](../chembank-structured-tag/SKILL.md) | `vault-structured/` |
| **Paper 3x 实验** | **本 Skill** | **`vault-practical/`** |

批量编排见 [chembank-ingest](../chembank-ingest/SKILL.md)。

## 默认笔记粒度（topic / 实验板块 — 非 part 级）

| 选择 | 说明 |
|------|------|
| **默认：一实验板块一篇** | 一道主问题（Q1 / Q2 / Q3…）或卷内清晰的实验 section → 一篇笔记 |
| **FORBIDDEN** | 不要像 Paper 2 那样拆成 `1(a)(i)` / `1(a)(ii)` 最小小题各一篇 |
| 主题优先 | 若一道主问题横跨两个实验类型，按主导操作选 **一个** `practical_topic`；必要时拆成两篇（仍按板块，不按罗马小问） |

示例 id：`cie-9701-2021-mj-p31-q1`（**不是** `…-q1a-i`）。

Frontmatter 必填：

- `question: "1"`（主问题号；可选 `parent_question` 同值）
- `practical_topic`: 下表六选一（**精确字符串**）
- `question_type: practical`
- 可选：`syllabus_codes` + `learning_outcomes`（考纲映射清晰时再填；可不强求每题 ≥1 LO）

### 受控 practical_topic（精确使用）

1. `Titrations`
2. `Thermometric experiments`
3. `Gravimetric experiments`
4. `Gas volume experiments`
5. `Rate experiments`
6. `Qualitative analysis`

Assets：

- `assets/<id>-paper.png` — 该实验板块完整 QP 裁切（整题/整 section）
- `assets/<id>-ms.png` — 对应 MS 截图（有则必贴）

## Pre-done checklist（FORBIDDEN — 未清零不得标完成）

| # | FORBIDDEN | 说明 |
|---|-----------|------|
| F1 | 缺 `*-paper.png` / embed | 板块级 QP 主阅读面 |
| F1b | 有 MS 却缺 `*-ms.png` / embed | 图像优先；乱码 OCR 勿写入正文 |
| F1c | 右侧 mark grid 被裁切 | 必须含完整页宽 / 右缘 examiner I–IV 格与 `[n]`；拒收右缘被切的 `*-paper.png` |
| F2 | 错题 / 串题裁切 | 不得裁进下一主问题 |
| F3 | 细粒度 part 笔记 | 禁止 `q1a-i` 式最小小题导出 |
| F4 | 非法 `practical_topic` | 必须六选一精确字符串 |
| F5 | 写入错误 vault | 只写 `vault-practical/` + `questions-practical/` |
| F6 | 页脚 / 页码泄漏 | 与其他 skill 相同 |
| F7 | 发明 LO / syllabus code | 可选字段也必须来自词表 |

```bash
source .venv/bin/activate
chembank audit s21:31          # auto → vault-practical/
# 或：chembank audit s21:31 --vault vault-practical
```

完成前对当前卷跑 `chembank audit <ref>`；exit ≠ 0 → **禁止**标完成。  
（实验题 audit 门禁会随实现加严；至少保证路径落在 `vault-practical/`、有 paper clip、topic 合法。）

## 硬性规则（MUST）

0. **每篇必须有合法 `practical_topic`**（上表精确值）。
1. **`question_type`: `practical`**。
2. **粒度 = 实验板块 / 主问题**，不是 `(a)(i)` part。
3. **每篇必有 QP 截图**：`## Question` 顶部 `![[assets/<id>-paper.png]]`。
4. **有 MS 则必有 MS 截图**：`## Mark Scheme` 下 `![[assets/<id>-ms.png]]`；乱码文本可空。
5. **化学格式**：与 MCQ/结构题 skill 相同（ΔH^ominus、箭头、离子电荷、去页脚）。
6. **双写**：`questions-practical/` **和** `vault-practical/questions/`；图在 `vault-practical/assets/`。考纲 hub：`vault-practical/syllabus` → `vault/syllabus` 符号链接。
7. **禁止**把 Paper 3 导出到 `vault-structured/`。
8. 提醒用户 Obsidian **Cmd+R**（打开的是 `vault-practical`）。
9. **QP paper clip 必须含完整页宽 / 右侧 mark box**：CIE Paper 3 常把 examiner criteria 格（竖排 I、II、III、IV + `[n]`）贴在右缘。裁切时 **禁止** 大右边距裁掉格线；抽查 gravimetric / titration Results 旁的 I–IV 格是否完整可见。`chembank audit` 会以 `clipped_right_mark_grid` 拒收过窄裁切。

## 进度清单（每卷）

```
ChemBank 实验题导出验收:
- [ ] 1. QP+MS 已命名放入 raw/papers/（如 9701_s21_qp_31.pdf）
- [ ] 2. chembank ingest <season> <paper> → draft/ 切主问题（勿追求 part 级导出）
- [ ] 3. 按实验板块打标：practical_topic；清晰时加 syllabus_codes / LO
- [ ] 4. 化学格式 + 去页脚；MS 文本无乱码
- [ ] 5. ingest --export → vault-practical/：每板块 *-paper.png（+ *-ms.png）
- [ ] 5b. 抽查右侧 mark grid：I–IV / `[n]` 完整入画（拒收右缘被切）
- [ ] 6. ★ chembank audit <ref> exit 0（含 `clipped_right_mark_grid`）
- [ ] 7. 抽查：笔记数 ≈ 主问题/实验板块数（远少于 Paper 2 part 数）
- [ ] 8. 提醒用户打开 vault-practical 并 Cmd+R
```

## 路径

| 用途 | 路径 |
|------|------|
| 考纲词表 | `syllabus/cie-9701-as-a-level-chemistry.yaml` |
| 切题草稿 | `draft/<paper_id>/q1.txt` …（主问题级优先） |
| 打标 JSON | `draft/<paper_id>/tagged/q1.json` |
| **QP 截图** | `vault-practical/assets/<id>-paper.png` |
| **MS 截图** | `vault-practical/assets/<id>-ms.png` |
| 输出 | `questions-practical/<id>.md` + `vault-practical/questions/<id>.md` |
| MCQ / 结构题库（勿写入） | `vault/` · `vault-structured/` |

## 批量导入

```bash
source .venv/bin/activate

# 1) 放入：
#    raw/papers/9701_s21_qp_31.pdf
#    raw/papers/9701_s21_ms_31.pdf

chembank ingest s21 31
# → kind=practical vault=vault-practical
# → draft/9701_s21_qp_31/…

# 2) 本对话按实验板块打标（practical_topic 六选一）
# 写 draft/.../tagged/q1.json 后：

chembank ingest s21 31 --export
chembank audit s21:31   # MUST exit 0
```

Downloads 里已有 June 2021 Paper 31/32/33 时，先拷贝再 ingest：

```bash
# 例：从 Downloads 规范化命名
cp "/path/to/9701 Chemistry June 2021 Question paper  31.pdf" raw/papers/9701_s21_qp_31.pdf
cp "/path/to/9701 Chemistry June 2021 Mark Scheme  31.pdf"     raw/papers/9701_s21_ms_31.pdf
chembank ingest s21 31
```

## 打标签规则

1. **先定 `practical_topic`**（卷面操作：滴定 / 量热 / 称重 / 气体体积 / 速率 / 定性分析）。
2. 考纲 LO **可选**：只有题意明确对应词表节点时才填；不要为凑数堆 LO。
3. `skills` 常含 `practical`；`marks` = 该主问题卷面总分（若可知）。
4. 校验 topic：字符串必须与上表完全一致（含大小写与复数）。

## 示例 frontmatter

```yaml
id: cie-9701-2021-mj-p31-q1
exam_board: CIE
syllabus_code: "9701"
year: 2021
session: MJ
paper: 31
question: "1"
question_type: practical
practical_topic: Titrations
skills: [practical, calculate]
marks: 16
syllabus_codes: []          # 可选；清晰时再填
learning_outcomes: []       # 可选
```

## 与 CLI / 其他 skill 的关系

| 方式 | 何时用 |
|------|--------|
| `chembank ingest s21 31` | 实验卷机械步骤；自动 `vault-practical/` |
| **本 Skill** | 按实验 topic 打标 + 验收 |
| `chembank-structured-tag` | Paper 2/4/5 最小小题 → `vault-structured/` |
| `chembank-syllabus-tag` | Paper 1 MCQ → `vault/` |
| `chembank audit s21:31` | 实验题质量门 |
