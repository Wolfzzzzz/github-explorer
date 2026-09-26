#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大规模抓取：读 queries.txt 的 [start:end) 区间（每行: 方向<TAB>查询<TAB>页数），
调 GitHub Search API（每页 100 条，可翻页），去重合并进 data/repos.json。
支持断点续传（已完成查询记录到 done.txt）。
用法: python scripts/fetch_massive.py --start 0 --end 200
"""
import argparse
import json
import os
import time
import urllib.parse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data", "repos.json")
QUERIES = os.path.join(ROOT, "queries.txt")
DONE = os.path.join(ROOT, "done.txt")
TOKEN = os.environ.get("GH_TOKEN", "")
SLEEP = 2.1


def api(q, limit=100, page=1):
    """用 gh search repos（实测最快最稳：每查询约 2.4 秒）"""
    cmd = ["gh", "search", "repos", q, "--sort", "stars",
           "--limit", str(limit), "--json", FIELDS]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if out.returncode != 0:
        raise Exception((out.stderr or "gh search error").strip()[:140])
    return {"items": json.loads(out.stdout or "[]")}

FIELDS = "name,owner,url,description,stargazersCount,forksCount,language,updatedAt,createdAt"


def load_repos():
    if os.path.exists(DATA):
        with open(DATA, encoding="utf-8") as f:
            return json.load(f)
    return []


def save(repos):
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(repos, f, ensure_ascii=False)
    os.replace(tmp, DATA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=100000)
    ap.add_argument("--out", default=None, help="输出文件（并行抓取时用不同文件名）")
    args = ap.parse_args()
    global DATA
    if args.out:
        DATA = args.out

    lines = [l.rstrip("\n") for l in open(QUERIES, encoding="utf-8") if l.strip()]
    end = min(args.end, len(lines))
    todo = lines[args.start:end]
    print(f"queries total={len(lines)} batch=[{args.start}:{end}) = {len(todo)}", flush=True)

    repos = load_repos()
    by_url = {r["url"]: r for r in repos}
    print(f"existing repos={len(repos)}", flush=True)

    updated = created = failed = 0
    done_file = open(DONE, "a", encoding="utf-8")

    for i, line in enumerate(todo, args.start):
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        direction, q = parts[0], parts[1]
        pages = 1
        if len(parts) > 2 and parts[2].strip().isdigit():
            pages = min(10, int(parts[2].strip()))
        for pg in range(1, pages + 1):
            try:
                data = api(q, 100, pg)
            except Exception as e:
                msg = str(e)
                low = msg.lower()
                if 'rate limit' in low or '403' in low or '429' in low or 'secondary' in low:
                    print(f"  [{i}] 限流，等待 35s 重试…", flush=True)
                    time.sleep(35)
                    try:
                        data = api(q, 100, pg)
                    except Exception:
                        print(f"  [{i}] 重试仍失败，跳过", flush=True)
                        failed += 1
                        break
                else:
                    print(f"  [{i}] WARN {q} p{pg} -> {msg[:80]}", flush=True)
                    failed += 1
                    time.sleep(5)
                    break
            items = data.get("items", [])
            if not items:
                break
            for it in items:
                u = it.get("html_url") or it.get("url")
                if not u:
                    continue
                row = {
                    "name": it.get("name", ""),
                    "owner": (it.get("owner") or {}).get("login", ""),
                    "url": u,
                    "description": (it.get("description") or "")[:200],
                    "stars": it.get("stargazersCount", 0) or it.get("stargazers_count", 0) or 0,
                    "forks": it.get("forksCount", 0) or it.get("forks_count", 0) or 0,
                    "language": it.get("language") or "—",
                    "updatedAt": it.get("updated_at", ""),
                    "createdAt": it.get("created_at", ""),
                    "matchedQuery": q[:60],
                    "direction": direction,
                }
                if u in by_url:
                    old = by_url[u]
                    for k in ("stars", "forks", "updatedAt"):
                        old[k] = row[k]
                    updated += 1
                else:
                    repos.append(row)
                    by_url[u] = row
                    created += 1
            if len(items) < 100:
                break
            time.sleep(SLEEP)

        done_file.write(f"{i}\n")
        idx = i - args.start
        if idx % 20 == 0:
            done_file.flush()
            print(f"  [{i}] +{created} upd{updated} total={len(repos)}", flush=True)
        if idx % 30 == 0 and idx > 0:
            save(repos)
            print(f"  [save] total={len(repos)}", flush=True)
        time.sleep(SLEEP)

    done_file.close()
    repos.sort(key=lambda x: -x.get("stars", 0))
    save(repos)
    print(f"BATCH DONE total={len(repos)} new={created} updated={updated} failed={failed}", flush=True)


if __name__ == "__main__":
    main()
