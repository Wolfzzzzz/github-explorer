# GitHub Explorer · 自动更新的开源资源库

一个**每天自动抓取 GitHub、自动重建页面、自动部署**的开源资源导航站。无需服务器，全靠 GitHub 自己。

## ✨ 特性

- 🔎 **15000+ 精选仓库**：按 30+ 个主题方向广度抓取（摄影 / 航空 / 化学 / macOS / SwiftUI / 地图 / AI Agent / Web 安全 / 学习工具 / 自托管 / 移动端……）
- 🗂 **可交互页面**：实时搜索（多词 AND + 高亮）、方向/语言多选、★ 下限、排序、卡片/列表/表格三视图、收藏（本地保存）、对比篮、卡片存 PNG、导出 Markdown/JSON
- 🌐 **在线实时搜索**：页面内直接调 GitHub Search API（支持 `stars:>5000 language:swift` 等完整语法），结果自动并入
- 🤖 **全自动管道**：GitHub Actions 每天 10:00（北京时间）自动抓取 → 合并 → 重建 → 部署 Pages
- 📦 **零依赖**：纯标准库 Python + 单文件 HTML，clone 下来本地打开就能用

## 🚀 自己部署一份

1. Fork 或 Use this template
2. 仓库 Settings → Actions 允许运行（默认允许）
3. Pages 会由 workflow 里的 `actions/configure-pages` 自动开启
4. 手动触发：Actions → Update data & deploy → Run workflow

## 🧩 数据管道

```
scripts/fetch.py   按主题关键词抓取 GitHub Search API（增量合并、每天更新 Star 数）
      ↓
data/repos.json    累积式数据仓库（随时间越滚越全）
      ↓
scripts/build.py   注入模板 → index.html（含新星榜 / 活跃榜）
      ↓
GitHub Pages       https://<user>.github.io/github-explorer/
```

## 🔐 隐私说明

- 本仓库不含任何个人数据；页面里的「推荐理由」为通用内容
- 页面内可选填的 GitHub Token 只保存在浏览器 localStorage，只发送给 api.github.com（建议 fine-grained、只读 Public）
- 抓取仅使用 GitHub 公开 Search API，遵守速率限制

## 📄 License

MIT
