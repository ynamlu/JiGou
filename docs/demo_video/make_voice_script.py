# -*- coding: utf-8 -*-
"""根据 video_content.BLOCKS 生成人工配音稿（Markdown + CSV）。"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from video_content import BLOCKS  # noqa: E402

OUT = ROOT / "demo_video"
PAGES = {
    "B01": "01-封面",
    "B02": "02-首页 / 03-输出物",
    "B03": "04-功能-问卷与对话",
    "B04": "05-功能-五段式报告 / 06-功能-六维评分",
    "B05": "07-功能-交付物 / 08-功能-验收版本 / 09-功能-总览",
    "B06": "10-技术栈-前端",
    "B07": "11-技术栈-后端与AI",
    "B08": "13-RAG双通道",
    "B09": "12-技术栈-数据与输出 / 14-总体架构",
    "B10": "录屏：登录页 → 首页",
    "B11": "录屏：首页两种模式",
    "B12": "录屏：个人中心 / 账号信息",
    "B13": "录屏：问卷答题（2–3 题 + 补充说明 + 上一题）",
    "B14": "录屏：自由对话（检索状态 + 流式回答）",
    "B15": "录屏：报告正文与评分（可叠 15-六维评分）",
    "B16": "录屏：交付物 / A-B 方案（可叠 16-交付物与AB）",
    "B17": "录屏：一键确认 / 验收 / v2 diff（可叠 17-验收版本）",
    "B18": "18-模板库",
    "B19": "录屏：我的图纸搜索 / 导出 PDF、长截图（可叠 19、20）",
    "B20": "21-结尾",
}

tl = json.loads((OUT / "时间轴.json").read_text(encoding="utf-8"))
durs = {b["id"]: b.get("dur", 0) for b in tl["blocks"]}

md = [
    "# 演示视频配音稿（人工配音版）",
    "",
    "> 按分镜逐段录音，文件名与分镜号一致：`B01.wav` … `B20.wav`，48kHz / 24bit / 单声道或立体声均可。",
    "> 每段前后留 0.5–1 秒静音，方便剪辑对齐；不需要自己配字幕，最终按你的音频重新对齐。",
    "> 括号内时长是参考值，不必严格卡点；语速自然、清楚即可。",
    "",
    "## 分镜清单",
    "",
    "| 分镜 | 环节 | 画面对应 | 参考时长 |",
    "| --- | --- | --- | --- |",
]
for b in BLOCKS:
    md.append(f"| {b['id']} | {b['tag']} | {PAGES.get(b['id'], '')} | {durs.get(b['id'], 0):.0f}s |")

md += ["", "---", ""]
for b in BLOCKS:
    text = "".join(b["cues"])
    md += [
        f"## {b['id']} · {b['tag']}（约 {durs.get(b['id'], 0):.0f} 秒）",
        "",
        f"**画面对应**：{PAGES.get(b['id'], '')}",
        "",
        text,
        "",
    ]

(OUT / "配音稿.md").write_text("\n".join(md), encoding="utf-8")

with (OUT / "配音稿-分镜.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["分镜", "环节", "画面对应", "参考时长(s)", "配音文本"])
    for b in BLOCKS:
        w.writerow([b["id"], b["tag"], PAGES.get(b["id"], ""), f"{durs.get(b['id'], 0):.1f}",
                    "".join(b["cues"])])

print("生成：demo_video/配音稿.md")
print("生成：demo_video/配音稿-分镜.csv")
