#!/bin/bash
# 一键收尾：安全合并分片 → 构建页面 → 提交 → 推送 → 触发云端重建部署
# 用法: ./finish.sh "提交说明"
set -e
PY=/Users/zzn/.workbuddy/binaries/python/versions/3.13.12/bin/python3
cd "$(dirname "$0")"
MSG=${1:-"data: update repositories"}

echo "== 1/5 合并分片 =="
$PY scripts/merge_safe.py

echo "== 2/5 构建页面 =="
$PY scripts/build.py

echo "== 3/5 提交 =="
git add -A
if git diff --cached --quiet; then
  echo "无变更，跳过提交"
else
  git commit -q -m "$MSG"
fi

echo "== 4/5 推送（网络不稳会自动重试）=="
for i in 1 2 3 4; do
  if git push -q; then echo "推送成功"; break; fi
  echo "推送失败，20 秒后重试 ($i/4)"; sleep 20
done

echo "== 5/5 触发云端重建 =="
gh workflow run update.yml -R Wolfzzzzz/github-explorer && echo "已触发"
echo "完成。页面: https://wolfzzzzz.github.io/github-explorer/"
