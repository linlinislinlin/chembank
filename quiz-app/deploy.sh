#!/usr/bin/env bash
# 一键部署：本地重新生成题库网页 -> 提交 -> 推到 GitHub，触发 Actions 自动上线。
# 用法：在仓库根目录执行  ./deploy.sh   （打包进一个 commit）
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "==> 重新构建题库网页 (quiz-app/build.py)"
python3 quiz-app/build.py

echo "==> 暂存所有改动 (含重新生成的 quiz-app/site)"
git add -A

# 生成一个有意义的 commit 信息
MSG="更新题库：$(date +%Y-%m-%d\ %H:%M)"
if git diff --cached --name-only | grep -q '^questions/'; then
  MSG="更新题库（新增/修改题目）：$(date +%Y-%m-%d\ %H:%M)"
fi

echo "==> 提交：$MSG"
git commit -m "$MSG" --no-verify || echo "(没有新的改动需要提交)"

echo "==> 推送到 GitHub (main)"
git push origin main

echo
echo "✅ 已推送。等待约 1 分钟，GitHub Actions 会自动把新题库部署上线。"
echo "学生正在刷题的话，页面顶部会出现“有新题目更新”提示，点刷新即可。"
