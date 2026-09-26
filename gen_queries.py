#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成大规模抓取用的查询列表（queries.txt），每行: 方向<TAB>查询
策略：方向核心词 × 后缀组合 + star 分层 + 语言×词 + topic + 创建时间分层
"""
import io

# 方向 -> 核心词
DIRECTIONS = {
    "摄影 / 图库 / 社区": ["photo", "photography", "image", "gallery", "album", "exif", "picture"],
    "航图 / 航空 / 飞行": ["aviation", "aircraft", "flight", "airport", "pilot", "aeronautical", "adsb"],
    "化学 / 科学工具": ["chemistry", "chemical", "molecule", "periodic", "element", "cheminformatics", "lab"],
    "macOS / 硬件监控 / 菜单栏": ["macos", "menubar", "monitor", "system", "hardware", "battery", "cpu"],
    "SwiftUI / iOS / macOS 开发": ["swiftui", "swift", "ios", "iphone", "apple", "cocoa", "xcode"],
    "地图 / 数据可视化": ["map", "chart", "visualization", "dashboard", "geo", "weather", "graph"],
    "AI Agent / MCP / LLM": ["agent", "llm", "mcp", "chatbot", "ai", "gpt", "prompt", "rag"],
    "Web 安全 / CTF / 渗透": ["security", "ctf", "pentest", "vulnerability", "hacking", "exploit", "scanner"],
    "学习 / 效率工具": ["study", "learning", "education", "flashcard", "note", "tutorial", "course", "quiz"],
    "音频 / 视频 / 媒体": ["audio", "video", "music", "media", "player", "stream", "sound"],
    "自托管 / 家庭实验室": ["self-hosted", "homelab", "nas", "docker", "server", "personal-cloud"],
    "前端框架 / 原生 JS / PWA": ["javascript", "frontend", "vanilla", "pwa", "website", "static", "spa"],
    "UI 组件 / 图表 / 动效": ["ui", "component", "animation", "css", "tailwind", "icon", "design"],
    "后端 / 数据库 / API": ["backend", "api", "database", "sql", "rest", "graphql", "orm", "server"],
    "部署 / DevOps / 运维": ["deploy", "devops", "ci", "cd", "pipeline", "kubernetes", "infrastructure"],
    "3D / WebGL / 视觉": ["3d", "webgl", "three", "shader", "opengl", "render", "graphics"],
    "相机 / 器材 / 远程控制": ["camera", "dslr", "shutter", "photography-gear", "raw"],
    "移动端 App · Android": ["android", "kotlin", "apk", "mobile"],
    "移动端 App · iOS": ["ios-app", "widgetkit", "swift-package"],
    "跨平台框架": ["flutter", "react-native", "compose-multiplatform", "dart"],
    "跨设备协同": ["sync", "file-transfer", "clipboard", "remote"],
    "CLI / TUI 终端工具": ["cli", "tui", "terminal", "command-line", "console"],
    "浏览器扩展 / 用户脚本": ["extension", "chrome", "firefox", "userscript", "browser"],
    "AI 图像 / 语音处理": ["upscale", "background-removal", "speech", "tts", "diffusion", "ocr"],
    "桌面美化 / 主题": ["theme", "wallpaper", "dock", "widget", "desktop"],
    "笔记 / 知识库": ["note", "wiki", "knowledge", "obsidian", "markdown"],
    "教育 / 科学仿真": ["simulation", "physics", "circuit", "math", "tutor"],
    "开发者小工具": ["tool", "utility", "converter", "generator", "formatter"],
    "游戏与模拟": ["game", "godot", "unity", "engine", "gamedev"],
    "数据库 / 存储": ["database", "storage", "redis", "postgres", "sqlite", "mongodb", "vector"],
    "测试 / 质量保障": ["test", "testing", "e2e", "mock", "qa", "coverage"],
    "爬虫 / 数据采集": ["crawler", "scraper", "spider", "scrapy", "crawl"],
    "云计算 / Serverless": ["cloud", "serverless", "aws", "azure", "gcp", "lambda"],
    "容器 / 编排": ["docker", "container", "k8s", "kubernetes", "compose"],
    "监控 / 日志 / 可观测性": ["monitoring", "logging", "observability", "metrics", "tracing", "prometheus"],
    "编辑器 / IDE 插件": ["editor", "ide", "vscode", "vim", "plugin", "neovim"],
    "区块链 / Web3": ["blockchain", "web3", "ethereum", "solidity", "crypto", "defi"],
    "机器学习框架": ["machine-learning", "deep-learning", "pytorch", "tensorflow", "neural"],
    "计算机视觉": ["computer-vision", "opencv", "image-recognition", "detection", "yolo"],
    "NLP / 语音": ["nlp", "natural-language", "asr", "whisper", "translation"],
    "数据工程 / 分析": ["data", "etl", "analytics", "pandas", "spark", "pipeline"],
    "自动化 / 工作流": ["automation", "workflow", "bot", "scheduler", "task"],
    "无障碍 / 国际化": ["accessibility", "a11y", "i18n", "l10n", "localization"],
    "字体 / 图标 / 设计资源": ["font", "icon", "icons", "typography", "design-resource"],
    "办公 / 文档 / PDF": ["pdf", "document", "office", "docx", "excel", "spreadsheet", "presentation"],
    "隐私 / 安全工具": ["privacy", "password", "encryption", "anonymous", "tracker"],
    "网络 / 代理 / VPN": ["proxy", "network", "vpn", "dns", "http", "tunnel"],
    "物联网 / 硬件 / 嵌入式": ["iot", "embedded", "arduino", "esp32", "raspberry-pi", "firmware"],
    "机器人 / 无人机": ["robot", "ros", "drone", "uav", "quadcopter"],
    "金融 / 量化": ["finance", "quant", "trading", "stock", "backtest"],
    "医疗 / 生物信息": ["bioinformatics", "medical", "health", "genomics", "dna"],
    "地理 / GIS": ["gis", "geospatial", "osm", "openstreetmap", "geocoding"],
    "包管理 / 构建工具": ["package", "build", "bundler", "webpack", "vite", "npm", "monorepo"],
    "代码质量 / 重构": ["linter", "formatter", "refactor", "code-quality", "static-analysis"],
    "开源 Awesome 清单": ["awesome", "curated", "resources", "list"],
    "中文开发者资源": ["chinese", "cn", "中文", "chinese-docs", "awesome-cn"],
}

SUFFIXES = ["app", "tool", "library", "framework", "server", "client", "cli", "ui",
            "api", "sdk", "plugin", "template", "starter", "demo", "example",
            "utils", "kit", "engine", "manager", "viewer", "generator", "parser"]

TOPICS = [
    "photography", "aviation", "chemistry", "macos", "swiftui", "ios", "android", "flutter",
    "react-native", "javascript", "typescript", "python", "go", "rust", "java", "kotlin",
    "swift", "dart", "php", "ruby", "c", "cpp", "csharp", "shell", "docker", "kubernetes",
    "self-hosted", "homelab", "security", "ctf", "penetration-testing", "cybersecurity",
    "machine-learning", "deep-learning", "llm", "ai", "agent", "mcp", "rag", "nlp",
    "computer-vision", "data-science", "data-visualization", "charts", "maps", "gis",
    "weather", "iot", "arduino", "raspberry-pi", "robot", "drone", "game-development",
    "godot", "unity", "webgl", "threejs", "animation", "ui", "design", "css", "tailwindcss",
    "frontend", "backend", "api", "database", "redis", "postgres", "sqlite", "mongodb",
    "devops", "ci-cd", "monitoring", "logging", "testing", "automation", "workflow",
    "productivity", "notes", "education", "learning", "flashcards", "anki", "markdown",
    "editor", "vscode", "vim", "neovim", "terminal", "cli", "tui", "browser-extension",
    "privacy", "encryption", "password", "vpn", "proxy", "network", "blockchain", "web3",
    "ethereum", "finance", "trading", "crypto", "bioinformatics", "medical", "health",
    "pdf", "document", "spreadsheet", "office", "font", "icon", "accessibility",
    "i18n", "localization", "scraper", "crawler", "package-manager", "bundler", "linter",
    "static-analysis", "serverless", "cloud", "aws", "azure", "gcp", "embeddedsystems",
    "audio", "video", "music", "media", "streaming", "podcast", "camera", "image-processing",
    "exif", "photo-gallery", "album", "wallpaper", "theme", "widget", "dashboard",
    "mobile", "cross-platform", "desktop", "sync", "backup", "storage", "file-transfer",
    "chatbot", "openai", "anthropic", "claude", "gemini", "ollama", "huggingface",
]

LANGS = ["python", "javascript", "typescript", "go", "rust", "java", "swift", "kotlin",
         "php", "ruby", "c", "cpp", "csharp", "dart", "shell", "html"]

GENERAL_WORDS = ["app", "tool", "framework", "library", "cli", "server", "sdk", "plugin"]


def main():
    out = []
    seen = set()

    def add(direction, q, pages=1):
        key = q.strip().lower()
        if not key or key in seen:
            return
        seen.add(key)
        out.append((direction, q.strip(), min(10, pages)))

    # ===== ① 细粒度 star 分层（几乎零重复，最高收益）=====
    # 粗一点的分层：低星区间查询极慢，减少数量换速度
    bands = [(20, 100), (100, 200), (200, 400), (400, 700)]
    v = 700
    while v < 5000: bands.append((v, v + 150)); v += 150
    while v < 20000: bands.append((v, v + 600)); v += 600
    while v < 60000: bands.append((v, v + 2500)); v += 2500
    bands.append((60000, 1000000))
    for a, b in bands:
        add("GitHub 全站明星项目", f"stars:{a}..{b}", 1)

    # ===== ② topic（精准主题，重复率低）=====
    for t in TOPICS:
        add("开源 Awesome 清单", f"topic:{t}", 1)

    # ===== ③ 创建时间分层 =====
    for y in [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]:
        add("🆕 新项目时间线", f"created:{y}-01-01..{y}-06-30 stars:>100", 1)
        add("🆕 新项目时间线", f"created:{y}-07-01..{y}-12-31 stars:>100", 1)

    # ===== ④ 语言 × 词 / 语言 × star =====
    for lang in LANGS:
        for w in GENERAL_WORDS[:4]:
            add("开源 Awesome 清单", f"{w} language:{lang}", 1)
        add("开源 Awesome 清单", f"language:{lang} stars:>2000", 1)
        add("开源 Awesome 清单", f"language:{lang} stars:500..2000", 1)

    # ===== ⑤ 方向关键词组合（精选，控制数量）=====
    for direction, words in DIRECTIONS.items():
        for w in words[:3]:
            add(direction, w, 1)
            for s in SUFFIXES[:8]:
                add(direction, f"{w} {s}", 1)

    with io.open("queries.txt", "w", encoding="utf-8") as f:
        for d, q, p in out:
            f.write(f"{d}\t{q}\t{p}\n")
    print(f"生成查询: {len(out)} 条 -> queries.txt（含翻页，预计最多 {sum(p for _,_,p in out)} 次请求）")
    from collections import Counter
    c = Counter(d for d, _, _ in out)
    print(f"方向数: {len(c)}")


if __name__ == "__main__":
    main()
