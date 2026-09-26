#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动抓取：按方向关键词调 GitHub Search API，合并更新 data/repos.json（累积式）。
只用标准库，无第三方依赖。Token 从环境变量 GH_TOKEN 读取（Actions 自带）。
"""
import json
import os
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "repos.json")
TOKEN = os.environ.get("GH_TOKEN", "")
SLEEP = 2.5

QUERIES = [
    # (方向, 搜索词)
    ("摄影 / 图库 / 社区", "photo gallery"),
    ("摄影 / 图库 / 社区", "self-hosted photos"),
    ("摄影 / 图库 / 社区", "exif"),
    ("摄影 / 图库 / 社区", "image processing"),
    ("航图 / 航空 / 飞行", "aviation"),
    ("航图 / 航空 / 飞行", "flight planning"),
    ("航图 / 航空 / 飞行", "metar"),
    ("化学 / 科学工具", "chemistry"),
    ("化学 / 科学工具", "periodic table"),
    ("化学 / 科学工具", "cheminformatics"),
    ("macOS / 硬件监控 / 菜单栏", "macos menubar"),
    ("macOS / 硬件监控 / 菜单栏", "system monitor"),
    ("SwiftUI / iOS / macOS 开发", "swiftui"),
    ("SwiftUI / iOS / macOS 开发", "awesome swift"),
    ("地图 / 数据可视化", "leaflet"),
    ("地图 / 数据可视化", "weather api"),
    ("地图 / 数据可视化", "data visualization"),
    ("AI Agent / MCP / LLM", "ai agent"),
    ("AI Agent / MCP / LLM", "mcp server"),
    ("AI Agent / MCP / LLM", "llm app"),
    ("AI Agent / MCP / LLM", "agent skills"),
    ("Web 安全 / CTF / 渗透", "ctf"),
    ("Web 安全 / CTF / 渗透", "web security"),
    ("Web 安全 / CTF / 渗透", "vulnerable app"),
    ("学习 / A-Level / 效率", "flashcard"),
    ("学习 / A-Level / 效率", "spaced repetition"),
    ("学习 / A-Level / 效率", "study tool"),
    ("音频 / 视频 / 媒体工具", "audio converter"),
    ("音频 / 视频 / 媒体工具", "ffmpeg"),
    ("自托管 / 家庭实验室", "self-hosted"),
    ("自托管 / 家庭实验室", "homelab"),
    ("移动端 App · Android", "android app open source"),
    ("移动端 App · Android", "kotlin android"),
    ("移动端 App · iOS", "ios app open source"),
    ("跨平台框架（Flutter / RN）", "flutter app"),
    ("跨设备协同（手机↔电脑）", "file transfer local network"),
    ("GitHub 全站明星项目", "stars:>300000"),
    ("GitHub 全站明星项目", "stars:50000..300000"),
    ("GitHub 全站明星项目", "stars:10000..50000"),
    ("GitHub 全站明星项目", "stars:3000..10000"),
]


def api(q, limit=30):
    url = ("https://api.github.com/search/repositories?q="
           + urllib.parse.quote(q) + "&sort=stars&order=desc&per_page=" + str(limit))
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "github-explorer"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    if os.path.exists(DATA):
        repos = json.load(open(DATA, encoding="utf-8"))
    else:
        repos = []
    by_url = {r["url"]: r for r in repos}
    updated = created = failed = 0

    for i, (direction, q) in enumerate(QUERIES, 1):
        print(f"[{i}/{len(QUERIES)}] {direction} :: {q}", flush=True)
        try:
            data = api(q)
        except Exception as e:
            print(f"  [warn] {e}", flush=True)
            failed += 1
            time.sleep(4)
            continue
        for it in data.get("items", []):
            u = it.get("html_url")
            if not u:
                continue
            row = {
                "name": it.get("name", ""),
                "owner": (it.get("owner") or {}).get("login", ""),
                "url": u,
                "description": it.get("description") or "",
                "stars": it.get("stargazersCount", 0) or it.get("stargazers_count", 0) or 0,
                "forks": it.get("forksCount", 0) or it.get("forks_count", 0) or 0,
                "language": it.get("language") or "—",
                "updatedAt": it.get("updated_at", ""),
                "createdAt": it.get("created_at", ""),
                "matchedQuery": q,
                "direction": direction,
            }
            if u in by_url:
                old = by_url[u]
                for k in ("stars", "forks", "updatedAt", "description", "language"):
                    old[k] = row[k]
                updated += 1
            else:
                repos.append(row)
                by_url[u] = row
                created += 1
        time.sleep(SLEEP)

    repos.sort(key=lambda x: -x.get("stars", 0))
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False)
    print(f"DONE total={len(repos)} updated={updated} new={created} failed={failed}")


if __name__ == "__main__":
    main()
