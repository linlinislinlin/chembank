# ChemBank 刷题网页（给学生的）

从你已有的 ChemBank 题库（Obsidian vault）一键生成一个**纯静态刷题网页**，发给学生用手机/电脑打开就能刷。

- **考纲驱动**：左侧按 22 个 AS 考纲节点（1.1、2.2…）树状导航，点节点即刷该知识点真题。
- **自动判分**：MCQ（Paper 1）点 ABCD 立刻判对错、显示正确答案与考查点（学习目标 LO）。
- **进度 & 错题**：答题记录存浏览器 `localStorage`，底部实时显示「已做 / 正确率 / 错题」，可一键重置。
- **随机抽题**：点击顶部「顺序 ▲/随机 🔀」切换，支持一轮随机复习。
- **搜索**：按考纲标题 / 关键词过滤。
- **零依赖**：原生 HTML + JS，不需要框架、不需要后端、不需要登录。

> 第一版只含 **Paper 1 MCQ（自动判分）**。简答题（Paper 2/4/5）与实验题（Paper 3）因带 Mark Scheme 截图，需要“自我对照判分”，后续版本再接入。

## 目录结构

```text
quiz-app/
  build.py        # 构建脚本：解析 questions/*.md → site/data.js + 复制截图
  index.html      # 前端单页（源码）
  site/           # 已生成的静态站点（直接部署这个目录）
    index.html
    data.js       # 全部题目 + 考纲树（由 build.py 生成，勿手改）
    assets/*.png  # 题目截图（由 build.py 复制）
```

## 如何重新构建（新增了题库后）

```bash
cd /Users/tsinglan-school/Desktop/题库
python3 quiz-app/build.py

# 输出：OK: 760 questions, 893 assets, 22 top-level syllabus nodes.
```

构建脚本做的事：

1. 读取 `questions/*.md`（Paper 1 MCQ）的 YAML frontmatter。
2. 把每题的 `-paper.png` 截图从 `vault/assets/` 复制到 `site/assets/`（按需去重）。
3. 从 `vault/syllabus/*.md` 读取考纲节点标题，构建考纲树（含每题所属数量）。
4. 生成 `site/data.js`，并（若存在）把 `quiz-app/index.html` 复制为 `site/index.html`。

## 本地预览

```bash
cd /Users/tsinglan-school/Desktop/题库/quiz-app/site
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

## 部署：一键上线 + 学生端自动更新（推荐用 GitHub Pages）

本工程配好了 **GitHub Pages 自动部署 + 前端自动检测更新**：

- 每次推送到 `main`，GitHub Actions 自动把 `quiz-app/site/` 部署上线（无需手动操作）。
- 学生开着刷题页时，前端每 45 秒自动检查远程 `data.js` 的版本号；你更新了题库，学生页面顶部会出现「📥 有新题目更新 → 点击刷新」，点一下即可看到新题，**不用手动刷新**。

> 📘 **零 git 基础？** 跟着 [从零上线 GitHub Pages 新手教程](./从零上线GitHubPages-新手教程.md) 一步步来（建号→建私有仓库→部署→日常更新全都有）。

### 你只需要做一步：跑 `deploy.sh`（自动构建 + 提交 + 推送）

```bash
cd /Users/tsinglan-school/Desktop/题库
./quiz-app/deploy.sh
```

脚本会：重新 `build.py` 生成 `site/` → `git commit` → `git push origin main`。然后等约 1 分钟，GitHub Actions 自动上线新版本。

> 首次使用前：先把仓库推到 GitHub（.gitignore 已确保 `quiz-app/site/` 会一起提交——因为 CI 直接部署这个文件夹，不需要在服务器上有源数据）。**建议把这个 repo 设为 Private**，真题截图仅你自己和授权的学生可见。

## 部署到其他平台（可选，非自动）

`quiz-app/site/` 是**纯静态文件**，也可手动拖到任意托管：

| 平台 | 备注 |
|------|------|
| **Gitee Pages** | 国内访问快，适合学生在中国大陆 |
| **Vercel / Netlify** | 免费，拖文件夹即可 |
| **内网 / 微信** | 直接把 `site/` 整个文件夹发给学生，双击 `index.html` 也能用 |

> 这些平台的"自动更新"需要你每次都重新上传；只有 GitHub Pages 方案做到了全自动。

## 关于数据来源与版权

题目截图与文本来自你本仓库的 `questions/` 与 `vault/assets/`。这些是 CIE 官方 past paper，版权归 Cambridge 所有。此工具仅用于**个人/教学内部**刷题，请勿公开传播原始试卷或用于商业用途。

## 后续可加（Roadmap）

- [ ] 简答题 / 实验题接入（展示题干 + 内嵌 Mark Scheme 截图，自我对照判分）
- [ ] 错题本详情页（回溯错了的题，按 LO 跳到相似题）
- [ ] 限时模考（按卷 Paper 1 全卷 40 题计时）
- [ ] 数据导出 / 教师看板（各知识点掌握度）
- [ ] PWA 离线缓存，方便无网络时刷题
