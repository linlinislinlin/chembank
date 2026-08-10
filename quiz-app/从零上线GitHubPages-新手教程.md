# 从零把刷题网页上线到 GitHub Pages（新手教程）

本文面向**第一次用 git / GitHub** 的你。只需照做，就能把你的刷题网页上线，且以后更新题自动生效。

> 参考用时：约 20 分钟（前 10 分钟装软件 + 创建账号）。

---

## 第 0 步：准备（只需做一次）

1. **注册 GitHub 账号**：打开 https://github.com/signup ，随便填邮箱密码完成注册（免费）。
2. **安装 git**：电脑上打开「终端」（Terminal），粘贴下面命令回车确认已装：
   ```bash
   git --version
   ```
   - 有版本号 → 跳过安装，进第 1 步。
   - 提示 `command not found` → 去 https://git-scm.com/downloads 下载安装（一路 Next 即可），重开终端。

> 小抄：打开「终端」的命令是 `Command(⌘) + 空格`，输入“Terminal”回车（如果装了 iTerm 就用 iTerm）。

---

## 第 1 步：告诉 git 你是谁（只需做一次）

在终端输入下面两行（替换成你的名字和邮箱）：
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

---

## 第 2 步：在 GitHub 上建一个**私有**仓库

1. 打开 https://github.com/new
2. **Repository name**：随便起，比如 `chembank` 或 `quiz`。
3. 勾选 **Private**（私有）——这样你的真题截图只有你自己和受邀的人能看到。
4. 其他默认，点最下面绿色的 **Create repository**。
5. 创建后页面会显示仓库地址，长这样：
   ```
   https://github.com/你的用户名/chembank.git
   ```
   （记不住的可以先把这页留着。）

---

## 第 3 步：把现有题库网页接上这个仓库（只做一次）

回到终端，切到你的题库文件夹，然后执行：
```bash
cd /Users/tsinglan-school/Desktop/题库
git remote add origin https://github.com/你的用户名/chembank.git
git branch -M main
git push -u origin main
```
> 第一次 push 会弹出 GitHub 登录窗口（或要求输入用户名 + 密码，密码填 **personal access token**，见下方“常见问题”）。输对后就开始上传。

上传完成后，打开你仓库的页面，能看到 `quiz-app/` 等文件夹就成功了。

---

## 第 4 步：开启 GitHub Pages（只做一次）

1. 打开你仓库页面 → 顶部 `Settings`（齿轮图标）。
2. 左侧栏点 `Pages`。
3. **Build and deployment** → Source 选 **GitHub Actions**（不是 Deploy from a branch）。
   - 如果看不到“GitHub Actions”选项，先确认第 3 步的 `git push -u origin main` 真的成功了（Actions 工作流文件 `.github/workflows/deploy.yml` 已经在你仓库里了）。
4. 等 1~2 分钟，工作流会自动运行并部署。
5. 部署完成后，你的网址是：
   ```
   https://你的用户名.github.io/chembank/
   ```
   （浏览器打开看看能不能刷题。）

> 网址里的 `chembank` 就是你第 2 步起的仓库名。

---

## 第 5 步：以后每次更新题目（只需这一步）

你（用 Cursor skill 等）往题库加了新题后，在终端执行：
```bash
cd /Users/tsinglan-school/Desktop/题库
./quiz-app/deploy.sh
```
脚本会自动：
1. 重新构建网页（`build.py`），生成最新题库；
2. 提交改动（commit）并推送到 GitHub（push）；
3. GitHub Actions 自动上线新版本。

**约 1 分钟后**，学生打开网页就是新版；正在刷的学生页面顶部会出现「📥 有新题目更新 → 点击刷新」。

---

## 学生那边是怎么自动更新的？

- 网页每次打开都是最新版（浏览器会重新下载数据）。
- 一直开着刷题页的学生，前端每 45 秒自动检查一次远程数据版本，变了就弹顶部提示条，点「刷新」即可，**不用手动 F5**。
- 网络断开时，改为检测到联网后立刻检查。

---

## 常见问题 / 故障排查

**Q1：push 时让我输密码，输什么？**
GitHub 现在不用账号密码，要用 **token**：
1. 打开 https://github.com/settings/tokens → 右上 `Generate new token (classic)`。
2. 勾选 `repo` 这一整项，生成一串以 `ghp_` 开头的字符串。
3. 在终端输入密码的地方，粘贴这串 token 回车即可（粘贴看不见是正常的）。
> 也可以改用更顺手的工具：装 GitHub Desktop（https://desktop.github.com），图形化操作，登录一次就不用再管 token。

**Q2：`deploy.sh` 怎么运行不了？**
先赋予执行权限：`chmod +x quiz-app/deploy.sh`，再运行。

**Q3：部署到 GitHub 却看不到新题？**
到仓库 `Actions` 标签页看工作流有没有红色 ❌。常见原因：`quiz-app/site` 没被一起提交（检查是否误删了 .gitignore 里的说明，`site/` 必须提交）。确认后在仓库 `Actions` 页点 `Run workflow` 手动重跑一次。

**Q4：学生在中国大陆打不开 github.io？**
GitHub Pages 国内偶尔慢/被墙。可以再开一个 Gitee 镜像，或用 Vercel（国内可访问）。需要我帮你配 Gitee 的话告诉我。

**Q5：题目版权问题？**
真题截图版权归 Cambridge。建议把仓库设为 `Private`，只把刷题网址发给你的学生，不要公开发布、不用于商业。

---

## 命令备忘

| 你想做的 | 命令 |
|---|---|
| 更新并上线 | `cd ~/Desktop/题库 && ./quiz-app/deploy.sh` |
| 只看改动没提交 | `cd ~/Desktop/题库 && git status` |
| 离线本地预览 | `cd ~/Desktop/题库/quiz-app/site && python3 -m http.server 8000` → 浏览器打开 `http://localhost:8000` |
