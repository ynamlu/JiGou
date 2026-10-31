# -*- coding: utf-8 -*-
"""导出演示视频前面的概念页（1920x1080 PNG），供人工配音/录屏/剪辑使用。

用法：backend\\.venv\\Scripts\\python.exe docs/demo_video/export_static_pages.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_video as B  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "demo_video" / "静态页"

PAGES = [
    ("01-封面", "title"),
    ("02-首页", "shot:screenshots/landing-desktop.jpg:首页 · 一句话开始一次需求诊断"),
    ("03-输出物", "shot:screenshots/report-desktop.jpg:输出物 · 可直接拿去开发与询价的需求报告"),
    ("04-功能-问卷与对话", "cards6:0,1"),
    ("05-功能-五段式报告", "cards6:2"),
    ("06-功能-六维评分", "cards6:3"),
    ("07-功能-交付物", "cards6:4"),
    ("08-功能-验收版本", "cards6:5"),
    ("09-功能-总览", "cards6:0,1,2,3,4,5"),
    ("10-技术栈-前端", "tech3:0"),
    ("11-技术栈-后端与AI", "tech3:1"),
    ("12-技术栈-数据与输出", "tech3:2"),
    ("13-RAG双通道", "shot:diagrams/rag.png:RAG · Chroma 向量检索／BM25 关键词检索"),
    ("14-总体架构", "shot:diagrams/architecture.png:总体架构 · 单进程 FastAPI + 单文件 SQLite"),
    ("15-六维评分", "score"),
    ("16-交付物与AB", "deliverables"),
    ("17-验收版本", "version"),
    ("18-模板库", "shot:screenshots/templates-desktop.jpg:模板库 · 多行业模板与案例"),
    ("19-我的图纸", "shot:screenshots/history-desktop.jpg:我的图纸 · 搜索 / 删除 / 状态徽章"),
    ("20-多端导出", "shot:screenshots/doc-mobile.jpg:多格式导出 · Markdown / PDF / 长截图"),
    ("21-结尾", "end"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, key in PAGES:
        src = B.render_slide(key)
        dest = OUT / f"{name}.png"
        shutil.copyfile(src, dest)
        print(f"{dest.name}  <- {key}")
    print(f"\n{len(PAGES)} 张静态页：{OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
