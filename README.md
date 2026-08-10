# ChemBank — CIE 9701 考纲驱动化学题库（MVP）

把 Cambridge International AS & A Level Chemistry（**9701**）真题切成单题，**按考纲节点分类**，并与 Mark Scheme / Examiner Report 绑定，最终导出到 Obsidian。

> 版权：本仓库只开源工具与考纲 taxonomy。Past Paper / 官方 syllabus PDF **默认不提交**（见 `.gitignore`）。请自行合法持有试卷。

## 设计原则：Syllabus-first

1. 分类主键 = `syllabus_codes` + **≥1 `learning_outcomes`**（受控词表）  
   [`syllabus/cie-9701-as-a-level-chemistry.yaml`](syllabus/cie-9701-as-a-level-chemistry.yaml)
2. AS 内容 = topics **1–22**；A Level 追加 **23–37**
3. 流水线：导入 → 抽取/切题 → 打标 →（ER）→ 导出；Agent skill 强制验收清单

## 目录

```text
syllabus/                 # 考纲 taxonomy（主分类）
schema/                   # 题目 JSON schema
src/chembank/             # extract / split / tag / ingest / export
raw/papers/               # QP + MS PDF（gitignored）— 命名见下
raw/reports/              # Examiner Report PDF（gitignored）— 按年
draft/                    # 切题草稿 + tagged/ + er/ + manifest.json
papers.yaml               # 试卷登记表（batch 用）
questions/                # MCQ 正式 Markdown（Paper 1）
questions-structured/     # 结构题正式 Markdown（Paper 2/4/5）
questions-practical/      # 实验题正式 Markdown（Paper 3）
vault/                    # Obsidian：Paper 1 MCQ
vault-structured/         # Obsidian：Paper 2/4/5 简答/结构题
vault-practical/          # Obsidian：Paper 3 实验/实操题
examples/                 # 样例题
```

### 三库布局（MCQ / 结构题 / 实验题）

| 试卷 | 例 | Obsidian vault | 双写 Markdown | Skill |
|------|-----|----------------|---------------|-------|
| Paper **1x** MCQ | `9701_s21_qp_12.pdf` | `vault/` | `questions/` | `chembank-syllabus-tag` |
| Paper **2/4/5x** 结构/简答 | `9701_s21_qp_21.pdf` | `vault-structured/` | `questions-structured/` | `chembank-structured-tag` |
| Paper **3x** 实验 | `9701_s21_qp_31.pdf` | `vault-practical/` | `questions-practical/` | `chembank-practical-tag` |

`chembank ingest` / `export-vault` / `audit` 按题号**自动选库**（可用 `--vault` 覆盖）。  
`vault-structured/syllabus` 与 `vault-practical/syllabus` → 符号链接到 `vault/syllabus`（共享 LO hubs）。

## 批量导入：加一卷新题（推荐路径）

### 1. 按约定命名放入 PDF

| 文件 | 约定 |
|------|------|
| QP | `raw/papers/9701_<season>_qp_<paper>.pdf` |
| MS | `raw/papers/9701_<season>_ms_<paper>.pdf` |
| ER（可选，按年） | `raw/reports/9701_<year>_<season>_er.pdf` |

`season`：`s21` = June 2021，`w21` = Nov 2021，`m22` = March 2022。  
`paper`：`11/12/13` = Paper 1 MCQ；`21/22/23` = Paper 2；`31/32/33` = Paper 3 实验；`41/42/43` = Paper 4。

**示例 — 加 June 2021 Paper 12（MCQ）：**

```bash
# 放到：
#   raw/papers/9701_s21_qp_12.pdf
#   raw/papers/9701_s21_ms_12.pdf
# ER 若已有 2021 June 报告则复用：
#   raw/reports/9701_2021_s21_er.pdf
```

**示例 — 加 Paper 2 结构题（导出到 vault-structured）：**

```bash
# 放到：
#   raw/papers/9701_s21_qp_21.pdf
#   raw/papers/9701_s21_ms_21.pdf

chembank ingest s21 21
# 打标：Cursor skill chembank-structured-tag
chembank ingest s21 21 --export
chembank audit s21:21
```

**示例 — 加 Paper 3 实验题（导出到 vault-practical）：**

```bash
# 放到：
#   raw/papers/9701_s21_qp_31.pdf
#   raw/papers/9701_s21_ms_31.pdf

chembank ingest s21 31
# 打标：Cursor skill chembank-practical-tag（按实验 topic，非 part）
chembank ingest s21 31 --export
chembank audit s21:31
```

若仓库里还没有对应 PDF，放入上述文件后再跑即可（三库 / skill / CLI 路由已 scaffold）。

### 2. 一键机械流水线（extract → split → 可选 ER → 可选 export）

```bash
cd /Users/tsinglan-school/Desktop/题库
source .venv/bin/activate

chembank ingest s21 12
# 等价：chembank ingest 9701_s21_qp_12
# 等价：chembank ingest s21:12
```

这一步会：

1. 抽取 QP（含 ΔH / 箭头等符号恢复）+ 切题 + 绑 MS  
2. 若有 ER PDF → `er-extract`（按 paper 切片）  
3. 若已有 `draft/.../tagged/` → `er-merge` + `export-vault`（每题 `*-paper.png`）  
4. 更新 `papers.yaml` 与 `draft/manifest.json`

**新卷第一次**通常还没有标签：ingest 会停在 `extracted`，并提示先打标。

### 3. 打标（syllabus_codes + learning_outcomes）

无 API key 时用 Cursor skill（推荐）：

> 按 chembank-syllabus-tag 给 `draft/9701_s21_qp_12` 全卷打标并导出

或 CLI（需 key / `--mock` 仅冒烟）：

```bash
chembank tag draft/9701_s21_qp_12 --export-md questions --vault vault/questions
```

**重要：** `chembank tag --mock` 与任何启发式标签都是 **provisional（临时）**。`chembank ingest --export` 只会导出已有 `tagged/*.json`，**不会**把 mock 变成正式考纲标签。正式打标须按**考查点**（command word + 计算/MS），见下方「按考查点重标 LO」。

### 4. 导出 / 刷新整题截图

打标后重跑 ingest（或只 export）：

```bash
chembank ingest s21 12 --export
# 或
chembank export-vault raw/papers/9701_s21_qp_12.pdf \
  -d draft/9701_s21_qp_12 \
  -m raw/papers/9701_s21_ms_12.pdf \
  --vault vault --export-md questions
```

### 5. 下一卷 / 批量

```bash
# 再加一卷：放入 PDF 后
chembank ingest s21 13

# 或登记多卷后批量（机械步骤；打标仍建议按卷用 skill）
chembank batch s21:12 s21:13 w22:11

# 处理 papers.yaml 里 status=pending/extracted 的卷
chembank papers                  # 查看登记表
chembank batch --status pending,extracted
```

## 端到端流水线（必须满足）

| # | 步骤 | 工具 |
|---|------|------|
| 1 | 导入 QP + MS（+ 可选同年 ER） | 文件命名约定 + `papers.yaml` |
| 2 | 抽取文本 + 符号恢复（ΔH、箭头；禁止 ≡） | `chembank extract` / `ingest` |
| 3 | 切题；去页脚噪音 | `chembank split` / `ingest` |
| 4 | **每题**整题截图 `*-paper.png` | `export-vault` / `ingest --export` |
| 5 | 无错裁 / 无原子沙拉 OCR / 选项排版正确 | skill 验收清单 |
| 6 | `syllabus_codes` + **≥1 `learning_outcomes`** | skill / `chembank tag` |
| 7 | 绑定 MS 答案 | pipeline / ingest |
| 8 | 有 ER 则 merge（定性 band OK；禁止编造 %） | `er-extract` / `er-merge` |
| 9 | 导出 `questions/` + `vault/questions/` + `vault/assets/` + LO hubs | `export-vault` |
| 10 | Skill 强制 checklist | `.cursor/skills/chembank-*` |

## 快速开始（已有环境）

```bash
cd /Users/tsinglan-school/Desktop/题库
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

chembank codes --as-only
chembank papers
chembank ingest s21 11          # 冒烟：已有 MVP 卷
```

分步命令（调试用）：

```bash
chembank pipeline raw/papers/9701_s21_qp_11.pdf -m raw/papers/9701_s21_ms_11.pdf -d draft
chembank er-extract raw/reports/9701_2021_s21_er.pdf --paper 11
chembank er-merge draft/er/9701_s21_er_11.json -t draft/9701_s21_qp_11/tagged
chembank export-vault raw/papers/9701_s21_qp_11.pdf \
  -d draft/9701_s21_qp_11 -m raw/papers/9701_s21_ms_11.pdf \
  --vault vault --export-md questions
```

### PDF 符号恢复与配图

CIE 卷常把 `ΔH⦵` 画成矢量路径。`chembank extract` 默认恢复 ΔH / 箭头，并把 `≡` 等伪影规范为 `→`。  
导出时转 MathJax，并**为每一题**生成 `vault/assets/<id>-qN-paper.png`。

## 按考纲打标签

Paper 1/2 默认 **AS-only**（topics 1–22）。每题必须有 ≥1 个词表内 `learning_outcomes`。

### 推荐：Cursor Skill（无需 API key）

- 全流程编排：[`.cursor/skills/chembank-ingest/SKILL.md`](.cursor/skills/chembank-ingest/SKILL.md)
- Paper 1 MCQ 打标 + 导出 `vault/`：[`.cursor/skills/chembank-syllabus-tag/SKILL.md`](.cursor/skills/chembank-syllabus-tag/SKILL.md)
- Paper 2/4 结构题打标 + 导出 `vault-structured/`：[`.cursor/skills/chembank-structured-tag/SKILL.md`](.cursor/skills/chembank-structured-tag/SKILL.md)
- Paper 3 实验题打标 + 导出 `vault-practical/`：[`.cursor/skills/chembank-practical-tag/SKILL.md`](.cursor/skills/chembank-practical-tag/SKILL.md)

### 可选：CLI + 外部 API

```bash
export OPENAI_API_KEY="sk-..."
chembank tag draft/9701_s21_qp_11 --only 1,2,3 \
  --export-md questions --vault vault/questions
```

无 key 冒烟：`chembank tag ... --mock`（**provisional only**，不作正式标签）。

### 按考查点重标 LO

发现 LO 贴错主题（典型：焓变/Hess 被标成 `4.2` Bonding，只因题干有 Period 3 氧化物列表）时，对 Cursor 说：

> **按考查点重标 LO**（可附题 id / 卷号，如 `cie-9701-2022-fm-p22-q2c-iii` 或 `m22:22`）

Agent / 你应：

1. 读该 part 的 command word + 所问计算 + mark scheme（不是整题开场化合物列表）  
2. 用 `chembank los --code 5.1` / `5.2` 等选**最具体**词表内 LO  
3. 改 `draft/<paper_id>/tagged/<part>.json` 的 `syllabus_codes` + `learning_outcomes`  
4. `chembank ingest <season>:<paper> --export` 写回 `vault-structured/`（或 MCQ 的 `vault/`）  
5. 批末抽查约 5 篇笔记核对 LO 是否贴合考查点  

硬规则摘要：标**考查技能**不标装饰背景；焓变/Hess/ΔH → **5.x 永不 4.2**；多主题时跟 MS/所问计算；禁止仅凭 intro 化合物列表打标。

## 讲义 / 组卷（select + assemble）

按考纲/规则从 `draft/*/tagged/` **选题 → 排版成一张 Obsidian 讲义**。两步分离：`select` 只选题，`assemble` 只排版。

```bash
source .venv/bin/activate

# 1) 按规则选成一个 pick 列表
chembank select pick/5.1-demo.yaml -o build/pick.json
# → build/pick.json（rules + questions）

# 2) 排版成讲义 Markdown
chembank assemble build/pick.json -o vault/handouts/5.1-demo.md --vault vault
# → vault/handouts/<slug>.md
```

规则 YAML（`pick/*.yaml`，见 `pick/5.1-demo.yaml`，除 `title` 外均可省略）：

| 字段 | 含义 |
|------|------|
| `title` | 讲义标题（必填；`slug` 由它生成） |
| `syllabus_codes` | 保留的考纲编码列表（OR 匹配，如 `["5.2"]`） |
| `topic_title` | 按 `topic_titles` 子串过滤 |
| `year_min` / `year_max` | 年份闭区间 |
| `difficulty_min` / `difficulty_max` | 1–5 难度区间（来自 ER 定性 band，存在时） |
| `max_marks` | 只取分值 ≤ 该值的题 |
| `question_type` | `mcq` / `structured` / `extended` / `practical` / `data` |
| `count` | 讲义题目上限（截断） |
| `sort` | 排序字段，默认 `[year, question]`；demo 用 `[year, paper, question]` |
| `shuffle` | bool，截断前是否随机（可带 `seed`） |

**排版（stacked 布局）：** 每题一个 `---` 分隔的整行块，内嵌大图 `<img src="file://…">`（max-width 820px，绝对路径，跨 vault 根也能在 Obsidian 渲染），图注 `第N题 · <year> <session> · Q<orig> · <marks>分`，并附 `[[questions/<id>]]` 详情链接。`select` 按题 `id` 去重，编号 `第N题` 在题目区与答案区共用，方便对题。资源图（`*-paper.png` / `*-ms.png`）经 `resolve_asset_path` 搜索 `vault/`、`vault-structured/`、`vault-practical/` 兄弟 vault 解析。

**答案区 `_answer_section`** 按题型分两种：
- **MCQ**（带短 `ms_answer`）→ 直接列字母（如 `C`）。
- **结构题 / 实验题**（无 `ms_answer`）→ 内嵌其 `…-ms.png` Mark Scheme 截图，可原位对照给分。

## 题目格式（Obsidian）

见 [`examples/cie-9701-2021-mj-p11-q1.md`](examples/cie-9701-2021-mj-p11-q1.md)。

核心字段：`syllabus_codes`、`learning_outcomes`、`ms_answer`、`source_qp` / `source_ms`；有 ER 时含 `er_year` / `examiner_band`。

## Open in Obsidian

MCQ（Paper 1）：

```text
/Users/tsinglan-school/Desktop/题库/vault
```

结构题 / 简答（Paper 2/4…）：

```text
/Users/tsinglan-school/Desktop/题库/vault-structured
```

实验题（Paper 3）：

```text
/Users/tsinglan-school/Desktop/题库/vault-practical
```

安装 **Dataview** 后可按 `syllabus_codes` / `learning_outcomes` / `practical_topic` / `er_year` 筛选。导出后 **Cmd+R** 刷新。

## 当前 MVP 范围

- [x] 9701 考纲树 + LO 词表
- [x] PDF 抽取（符号恢复）+ Paper 1 切题 + MS 绑定
- [x] 整题 `*-paper.png` + 焦点配图 + vault 双写
- [x] Examiner Report（按年 merge）
- [x] `chembank ingest` / `batch` + `papers.yaml` 批量入口
- [x] `vault-structured/` + 结构题 skill / 按卷自动选库
- [x] `vault-practical/` + 实验题 skill / Paper 3x 自动选库（scaffold）
- [x] `select` + `assemble` 讲义/组卷（stacked 布局 + 截图 + MS 答案区）
- [ ] Paper 2 长题几何裁切增强（多页主问题）
- [ ] Paper 3 实验板块裁切 / topic 门禁增强
- [ ] 相似题 / 错题本
