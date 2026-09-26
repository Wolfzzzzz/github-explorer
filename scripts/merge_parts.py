#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并并行抓取产生的分片文件（part_*.json）进 data/repos.json（去重、按 star 排序）。
用法: python scripts/merge_parts.py
"""
import glob
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "repos.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[warn] 读取失败 {path}: {e}")
        return []


def main():
    repos = load(DATA)
    by_url = {r["url"]: r for r in repos}
    print(f"主库: {len(repos)}", flush=True)

    parts = sorted(glob.glob(os.path.join(ROOT, "part_*.json")))
    print(f"发现分片: {len(parts)}", flush=True)
    added = updated = 0
    for p in parts:
        rows = load(p)
        print(f"  {os.path.basename(p)}: {len(rows)}", flush=True)
        for r in rows:
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
    print(f"MERGE DONE total={len(repos)} added={added} updated={updated}", flush=True)

    # 归档分片，避免下次重复合并
    arch = os.path.join(ROOT, "parts_archive")
    os.makedirs(arch, exist_ok=True)
    for p in parts:
        shutil.move(p, os.path.join(arch, os.path.basename(p)))
    print(f"分片已归档到 {arch}", flush=True)


if __name__ == "__main__":
    main()
