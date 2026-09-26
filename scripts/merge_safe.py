#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全增量合并：只读 part_*.json 合并进 data/repos.json（不移动分片，可在抓取运行中反复执行）。
用法: python scripts/merge_safe.py
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "repos.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[warn] {os.path.basename(path)}: {e}")
        return []


def main():
    repos = load(DATA)
    by_url = {r["url"]: r for r in repos}
    base = len(repos)
    parts = sorted(glob.glob(os.path.join(ROOT, "part_*.json")))
    added = updated = 0
    for p in parts:
        for r in load(p):
            u = r.get("url")
            if not u:
                continue
            if u in by_url:
                old = by_url[u]
                for k in ("stars", "forks", "updatedAt"):
                    if k in r:
                        old[k] = r[k]
                updated += 1
            else:
                repos.append(r)
                by_url[u] = r
                added += 1
    repos.sort(key=lambda x: -x.get("stars", 0))
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False)
    os.replace(tmp, DATA)
    print(f"MERGE(安全) 原 {base} → 现 {len(repos)} | 新增 {added} 更新 {updated} | 分片 {len(parts)} 个")


if __name__ == "__main__":
    main()
