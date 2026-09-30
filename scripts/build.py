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
# 体积优化：描述截断到 120 字 + 剔除多余字段（10 万级数据可显著减小页面体积）
for r in repos:
    d = r.get("description") or ""
    if len(d) > 120:
        r["description"] = d[:117] + "..."
    mq = r.get("matchedQuery") or ""
    if len(mq) > 24:
        r["matchedQuery"] = mq[:24]
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
        "卡片支持：收藏（本地保存）/ 对比 / 存为图片 / 相似推荐 / 上一个下一个导航",
        "导出按钮可把当前筛选结果存为 Markdown / JSON / 纯文本",
        "支持随机排序（🎲）发现没见过的项目，支持 URL 分享当前筛选状态",
    ],
    "action": "收藏本页，每天来看新星榜和活跃榜的变化。",
    "prio": "🟢 提示", "prioClass": "p3",
}]

# 为每个方向自动生成数据洞察（方向越多，洞察越丰富）
for d in dir_order:
    rs = [r for r in repos if r.get("direction") == d]
    if len(rs) < 15:
        continue
    total_star = sum(r.get("stars", 0) for r in rs)
    avg = total_star // len(rs)
    top5 = sorted(rs, key=lambda x: -x.get("stars", 0))[:5]
    lcnt = {}
    for r in rs:
        lcnt[r.get("language", "—")] = lcnt.get(r.get("language", "—"), 0) + 1
    top_langs = sorted(lcnt.items(), key=lambda x: -x[1])[:4]
    t0 = top5[0]
    insights.append({
        "title": d, "count": f"{len(rs)} 个仓库", "dir": d,
        "paras": [
            f"本方向收录 <b>{len(rs)}</b> 个仓库，Star 合计 <b>{total_star:,}</b>，平均 <b>{avg:,}</b> ★。",
            f"代表项目：<b>{t0['owner']}/{t0['name']}</b>（{t0.get('stars',0):,}★）——{(t0.get('description') or '').strip()[:70]}",
            "主流语言：" + "、".join(f"{l}（{n}）" for l, n in top_langs),
        ],
        "bullets": [f"<b>{r['owner']}/{r['name']}</b> — {r.get('stars',0):,}★ {(r.get('description') or '').strip()[:48]}" for r in top5],
        "action": "点击上方「方向」里的同名标签，即可单独浏览该方向全部仓库。",
        "prio": "🟢 自动", "prioClass": "p3",
    })

CHUNK = 15000
meta = {
    "generatedAt": now.strftime("%Y-%m-%d %H:%M") + " UTC",
    "chunkSize": CHUNK,
    "metaChunks": (len(repos) + CHUNK - 1) // CHUNK,
    "totalRepos": len(repos),
    "dirNames": dir_order,
    "topLangs": top_langs,
    "trending": trending,
    "insights": insights,
    "highlights": highlights,
}

# ===== 渐进式加载：数据全部动态加载，首屏不被阻塞 =====
meta_payload = (json.dumps(meta, ensure_ascii=False)
                .replace("<", "\\u003c")
                .replace("\u2028", "\\u2028")
                .replace("\u2029", "\\u2029"))

chunks = [repos[i:i + CHUNK] for i in range(0, len(repos), CHUNK)] or [[]]

all_langs = sorted({r.get("language", "—") for r in repos})
lang_idx = {l: i for i, l in enumerate(all_langs)}
dir_idx = {d: i for i, d in enumerate(dir_order)}

os.makedirs(os.path.join(ROOT, "_site", "data"), exist_ok=True)

# ① 轻量索引分片：与 full 分片同 CHUNK → 全局索引对齐，支持任意片先到先用
for ci, ch in enumerate(chunks):
    lc = []
    for r in ch:
        d = r.get("description") or ""
        if len(d) > 60:
            d = d[:57] + "..."
        lc.append([r["name"], r["owner"], r.get("stars", 0), r.get("forks", 0),
                   dir_idx.get(r.get("direction"), 0),
                   lang_idx.get(r.get("language", "—"), 0),
                   d, (r.get("updatedAt") or "")[:10],
                   (r.get("createdAt") or "")[:10], (r.get("matchedQuery") or "")[:20]])
    body = ("window.__META_PARTS__=window.__META_PARTS__||[];window.__META_PARTS__.push({from:"
            + str(ci * CHUNK)
            + ",dirs:" + json.dumps(dir_order, ensure_ascii=False)
            + ",langs:" + json.dumps(all_langs, ensure_ascii=False)
            + ",repos:" + json.dumps(lc, ensure_ascii=False).replace("<", "\\u003c")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029") + "});")
    with open(os.path.join(ROOT, "_site", "data", f"meta-{ci}.js"), "w", encoding="utf-8") as f:
        f.write(body)

# ② 完整分片：点开详情/深度搜索时才动态加载
for i, ch in enumerate(chunks):
    body = ("window.__FULL__=window.__FULL__||[];window.__FULL__.push({from:" + str(i * CHUNK)
            + ",repos:" + json.dumps(ch, ensure_ascii=False).replace("<", "\\u003c")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029") + "});")
    with open(os.path.join(ROOT, "_site", "data", f"full-{i}.js"), "w", encoding="utf-8") as f:
        f.write(body)

scripts = []  # 数据改为运行时动态加载，HTML 立即渲染
html = (template
        .replace("<!--DATA_SCRIPTS-->", "\n".join(scripts))
        .replace("/*__META__*/ {}", meta_payload))

with open(os.path.join(ROOT, "_site", "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print(f"OK _site: index.html + meta/{len(chunks)} 片(渐进) + full/{len(chunks)} 片(按需) | repos={len(repos)} dirs={len(dir_order)}")
