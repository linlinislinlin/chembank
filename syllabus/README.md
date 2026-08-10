# Syllabus taxonomies

题库的主分类轴是**考纲节点**（`syllabus_codes`），不是自由文本主题。

## Primary: CIE 9701

| 文件 | 说明 |
|------|------|
| `cie-9701-as-a-level-chemistry.yaml` | Cambridge International AS & A Level Chemistry 9701（2025–2027） |

- **AS Level**：topics `1`–`22`（及子节点如 `1.1`、`7.2`）
- **A Level**：另加 `23`–`37`
- Paper 1 / Paper 2 以 AS 节点为主打标签

代码来自官方 syllabus PDF 的 Subject content 编号，**禁止 AI 发明新 code**。

### Learning outcomes

Each subtopic may list official LOs with stable ids:

| Id | Example |
|----|---------|
| `{subtopic}-{n}` | `3.1-1` |
| `{subtopic}-{n}{letter}` | `2.4-1a` |

Re-extract from PDF: `python scripts/extract_learning_outcomes.py`

## 规则

1. 每道题至少一个 `syllabus_codes`（优先最细的子主题，如 `2.4`）。
2. 尽量再标最具体 `learning_outcomes`（如 `3.1-1`）；有 LO 时必须保留父级 `syllabus_codes`。
3. **禁止**发明 LO id 或改写官方 LO 原文；`learning_objectives` 仅自由文本备注，不是考纲 LO。
4. 可用父节点（如 `2`）表示跨子主题综合题。
5. 换考纲版本时新增 YAML，不要改已入库题目用过的 code。
6. Obsidian 用 `syllabus_codes` / `learning_outcomes` 检索即按考纲浏览。

```bash
chembank codes --as-only
chembank los --code 3.1
chembank codes --lo --as-only
```
