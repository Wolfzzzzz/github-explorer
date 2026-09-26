#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建：data/repos.json + assets/template.html + assets/highlights.json -> index.html（根目录 & _site/）
只用标准库。自动生成"新星榜 / 活跃榜"替代 trending 数据源。
"""
import json
import os
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

repos = json.load(open(os.path.join(ROOT, "data", "repos.json"), encoding="utf-8"))
template = open(os.path.join(ROOT, "assets", "template.html"), encoding="utf-8").read()

hp = os.path.join(ROOT, "assets", "highlights.json")
highlights = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else {}

# 方向顺序与语言统计
dir_order = []
for r in repos:
    if r.get("direction") and r["direction"] not in dir_order:
        dir_order.append(r["direction"])
lang = {}
for r in repos:
    lang[r.get("language", "—")] = lang.get(r.get("language", "—"), 0) + 1
top_langs = sorted(lang.items(), key=lambda x: -x[1])[:18]

now = datetime.datetime.now(datetime.timezone.utc)


def age_days(s):
    try:
        return (now - datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))).days
    except Exception:
        return 99999


def to_card(r):
    return {"full": r["owner"] + "/" + r["name"], "lang": r.get("language", "—"),
            "stars": r.get("stars", 0), "desc": r.get("description", "")}


new_repos = sorted([r for r in repos if age_days(r.get("createdAt", "")) <= 14 and r.get("stars", 0) >= 300],
                   key=lambda x: -x["stars"])[:20]
active = sorted([r for r in repos if age_days(r.get("updatedAt", "")) <= 1 and r.get("stars", 0) >= 10000],
                key=lambda x: -x["stars"])[:20]

trending = {"capturedAt": now.strftime("%Y-%m-%d %H:%M"), "groups": [
    {"id": "new", "label": "🆕 最近 7 天新星", "note": "创建不满 7 天且 ≥500★",
     "repos": [to_card(r) for r in new_repos]},
    {"id": "hot", "label": "🔥 近 24h 高星活跃", "note": "≥10000★ 且 24h 内有更新",
     "repos": [to_card(r) for r in active]},
]}

insights = [{
    "title": "关于本页", "count": f"{len(repos)} 个仓库", "dir": "",
    "paras": [
        "本页由 GitHub Actions <b>每天自动抓取</b>：按主题关键词调 GitHub Search API，合并去重后重新生成，无需任何服务器。",
        "顶部搜索框可即时筛选全部仓库；<b>🌐 在线搜索</b>支持 GitHub 完整语法（如 stars:&gt;5000 language:swift），结果实时并入。",
        "数据来自公开的 GitHub Search API，Star 数为每次构建时的快照。",
    ],
    "bullets": [
        "卡片支持：收藏（本地保存）/ 对比 / 存为图片 / 相似推荐",
        "导出按钮可把当前筛选结果存为 Markdown / JSON / 纯文本",
    ],
    "action": "收藏本页，每天来看新星榜和活跃榜的变化。",
    "prio": "🟢 提示", "prioClass": "p3",
}]

data = {
    "generatedAt": now.strftime("%Y-%m-%d %H:%M") + " UTC",
    "repos": repos,
    "dirNames": dir_order,
    "topLangs": top_langs,
    "trending": trending,
    "insights": insights,
    "highlights": highlights,
}

# 关键：数据里可能含 </script>（XSS payload 类描述），必须转义否则页面白屏
payload = (json.dumps(data, ensure_ascii=False)
           .replace("</", "<\\/")
           .replace("\u2028", "\\u2028")
           .replace("\u2029", "\\u2029"))
html = template.replace("/*__DATA__*/ {}", payload)

os.makedirs(os.path.join(ROOT, "_site"), exist_ok=True)
with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
with open(os.path.join(ROOT, "_site", "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK index.html | repos={len(repos)} dirs={len(dir_order)} highlights={len(highlights)}")
