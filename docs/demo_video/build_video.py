# -*- coding: utf-8 -*-
"""合成演示视频：真实录屏 + 概念卡 + 配音 + 烧录字幕。

画面来源两类：
  slide —— PIL 渲染的概念页面（片头、功能地图、技术栈、评分、版本、片尾）
  clip  —— demo_video/raw/main.webm 里的真实操作录屏，按 marks_main.json 的步骤裁切

每个分镜的画面时长与配音严格等长，块内硬切、不做黑场淡入淡出，保证播放连贯。
字幕在最后一趟统一烧录。

用法：python docs/demo_video/build_video.py
前置：build_voiceover.py（时间轴）、record_demo.py（录屏 + 标记）
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_preview_video as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "demo_video"
RAW = OUT / "raw"
WORK = OUT / "tmp" / "v2"
SLIDES = OUT / "slides"
CLIPS = WORK / "clips"

W, H = 1920, 1080
FPS = 30
SPEED_MIN, SPEED_MAX = 0.62, 2.6


def ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


# 每个分镜的画面编排：("slide", key, 权重) / ("clip", 起, 止, 权重)
def clip(src: str, a: str, b: str, w: float = 1.0) -> dict:
    return {"t": "clip", "src": src, "a": a, "b": b, "w": w}


def slide(key: str, w: float = 1.0) -> dict:
    return {"t": "slide", "key": key, "w": w}


PLAN: dict[str, list[dict]] = {
    "B01": [slide("title")],
    "B02": [slide("shot:screenshots/landing-desktop.jpg:首页 · 一句话开始一次需求诊断", 0.55),
            slide("shot:screenshots/report-desktop.jpg:输出物 · 可直接拿去开发与询价的需求报告", 0.45)],
    "B03": [slide("cards6:0,1")],
    "B04": [slide("cards6:2", 0.45), slide("cards6:3", 0.55)],
    "B05": [slide("cards6:4", 0.34), slide("cards6:5", 0.30), slide("cards6:0,1,2,3,4,5", 0.36)],
    "B06": [slide("tech3:0")],
    "B07": [slide("tech3:1")],
    "B08": [slide("shot:diagrams/rag.png:RAG · Chroma 向量检索／BM25 关键词检索")],
    "B09": [slide("tech3:2", 0.58),
            slide("shot:diagrams/architecture.png:总体架构 · 单进程 FastAPI + 单文件 SQLite", 0.42)],
    "B10": [clip("main", "login_view", "home_hover")],
    "B11": [clip("main", "login_done", "profile")],
    "B12": [clip("main", "profile", "quiz_q1")],
    "B13": [clip("main", "quiz_q1", "gen_start")],
    "B14": [clip("main", "chat_open", "chat_scroll", 0.74),
            slide("shot:diagrams/rag.png:双通道降级 · 向量不可用自动切 BM25", 0.26)],
    "B15": [clip("main", "doc_tour_start", "doc_tour8", 0.62), slide("score", 0.38)],
    "B16": [clip("main", "ab_plan", "new_version", 0.62), slide("deliverables", 0.38)],
    "B17": [clip("main", "doc_again", "accepted", 0.34), slide("version", 0.36),
            clip("main", "new_version", "doc_tour_start", 0.30)],
    "B18": [clip("tpl", "tpl_open", "end")],
    "B19": [clip("main", "history_open", "doc_again", 0.34),
            clip("main", "doc_tour_end4", "export_png", 0.36),
            slide("shot:screenshots/doc-mobile.jpg:多格式导出 · Markdown / PDF / 长截图", 0.30)],
    "B20": [slide("end")],
}

FALLBACK = {
    "B10": "shot:screenshots/login-desktop.jpg:登录 · 手机号 + 强度校验密码",
    "B11": "shot:screenshots/landing-desktop.jpg:首页 · 两种诊断方式随时可换",
    "B12": "shot:screenshots/profile-desktop.jpg:账号体系 · 报告与验收记录按账号隔离",
    "B13": "shot:screenshots/chat-desktop.jpg:AI 问卷 · 逐题追问，也可自由描述",
    "B14": "shot:screenshots/doc-chat.jpg:自由对话 · 检索状态 + 流式输出",
    "B15": "shot:screenshots/report-desktop.jpg:五段式报告 · 概述 / 已具备 / 还缺失 / 待确认 / 下一步",
    "B16": "deliverables",
    "B17": "version",
    "B18": "shot:screenshots/templates-desktop.jpg:模板库 · 多行业模板与案例",
    "B19": "shot:screenshots/history-desktop.jpg:我的图纸 · 搜索 / 删除 / 状态徽章",
}


def safe_name(key: str) -> str:
    import re

    return re.sub(r"[^\w一-鿿]+", "_", key)[:80] + ".png"


def render_slide(key: str) -> Path:
    SLIDES.mkdir(parents=True, exist_ok=True)
    path = SLIDES / safe_name(key)
    if path.exists():
        return path
    if key == "title":
        img = S.frame_title()
    elif key == "end":
        img = S.frame_end()
    elif key == "score":
        img = S.frame_score()
    elif key == "deliverables":
        img = S.frame_deliverables()
    elif key == "version":
        img = S.frame_version()
    elif key.startswith("cards6:"):
        idx = [int(x) for x in key.split(":", 1)[1].split(",") if x.strip()]
        img = S.frame_cards6(idx)
    elif key.startswith("tech3:"):
        img = S.frame_tech3(int(key.split(":", 1)[1]))
    elif key.startswith("shot:"):
        rest = key.split(":", 1)[1]
        img_path, _, caption = rest.partition(":")
        img = S.frame_shot({"image": img_path, "caption": S.safe(caption)})
    else:
        raise ValueError(key)
    img.convert("RGB").save(path)
    return path


def slide_clip(key: str, dur: float, dest: Path) -> None:
    png = render_slide(key)
    # 只做极缓推镜，不做淡入淡出
    vf = (
        "scale=2016:1134:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop=1920:1080:(iw-1920)/2:(ih-1080)*min(t/{dur:.3f}\\,1),"
        "format=yuv420p"
    )
    subprocess.run(
        [ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
         "-loop", "1", "-framerate", str(FPS), "-i", str(png),
         "-t", f"{dur:.3f}", "-vf", vf,
         "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-r", str(FPS), "-pix_fmt", "yuv420p", str(dest)],
        check=True,
    )


def clip_clip(src: Path, marks: dict, spans: list[tuple[str, str]], dur: float, dest: Path) -> str:
    ranges = []
    for a, b in spans:
        ta, tb = marks.get(a), marks.get(b)
        if ta is None or tb is None or tb <= ta:
            raise RuntimeError(f"缺少录屏区间 {a}→{b}")
        ranges.append((ta, tb))
    total_src = sum(b - a for a, b in ranges)
    speed = max(SPEED_MIN, min(SPEED_MAX, total_src / dur))

    parts = [f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}]"
             for i, (a, b) in enumerate(ranges)]
    labels = "".join(f"[v{i}]" for i in range(len(ranges)))
    graph = ";".join(parts) + ";"
    if len(ranges) > 1:
        graph += f"{labels}concat=n={len(ranges)}:v=1:a=0[cc];"
        src_label = "[cc]"
    else:
        graph += ""
        src_label = "[v0]"
    graph += (
        f"{src_label}setpts=PTS/{speed:.4f},fps={FPS},"
        "scale=1920:1080:flags=lanczos,"
        "tpad=stop_mode=clone:stop_duration=8,"
        f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,"
        "unsharp=5:5:0.4:5:5:0.0,format=yuv420p[v]"
    )
    subprocess.run(
        [ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(src), "-filter_complex", graph, "-map", "[v]",
         "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium",
         "-crf", "17", "-r", str(FPS), "-pix_fmt", "yuv420p", str(dest)],
        check=True,
    )
    return f"{total_src:5.1f}s→{dur:5.1f}s ({speed:.2f}x)"


def main() -> int:
    for d in (WORK, CLIPS, SLIDES):
        d.mkdir(parents=True, exist_ok=True)

    tl = json.loads((OUT / "时间轴.json").read_text(encoding="utf-8"))

    def load(name: str):
        video = RAW / f"{name}.webm"
        mfile = RAW / f"marks_{name}.json"
        if not video.exists() or not mfile.exists():
            raise SystemExit(f"缺少 {video} 或 {mfile}")
        return video, json.loads(mfile.read_text(encoding="utf-8"))

    SOURCES = {"main": load("main"), "tpl": load("tpl")}

    blocks = tl["blocks"]
    total = tl["duration"]
    clips: list[Path] = []

    for i, b in enumerate(blocks):
        start = b["start"]
        end = blocks[i + 1]["start"] if i + 1 < len(blocks) else total
        dur = max(1.2, end - start)
        parts = PLAN.get(b["id"], [slide("title")])
        weight = sum(p["w"] for p in parts)
        print(f"[{i + 1:02d}/{len(blocks)}] {b['id']} {dur:5.2f}s  {len(parts)} 个画面")
        done = 0.0
        for j, part in enumerate(parts):
            pdur = dur * part["w"] / weight
            if j == len(parts) - 1:
                pdur = dur - done
            dest = CLIPS / f"{i:02d}_{j:02d}.mp4"
            if part["t"] == "slide":
                slide_clip(part["key"], pdur, dest)
            else:
                try:
                    src_path, src_marks = SOURCES[part["src"]]
                    info = clip_clip(src_path, src_marks, [(part["a"], part["b"])], pdur, dest)
                    print(f"      {part['src']}:{part['a']}→{part['b']}  {info}")
                except RuntimeError as exc:
                    print(f"      ! {exc}，改用静态页")
                    slide_clip(FALLBACK.get(b["id"], "title"), pdur, dest)
            clips.append(dest)
            done += pdur

    listing = WORK / "concat.txt"
    listing.write_text("\n".join(f"file '{c.as_posix()}'" for c in clips) + "\n",
                       encoding="utf-8")
    base = WORK / "base.mp4"
    subprocess.run([ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(base)], check=True)

    final = OUT / "极构-需求诊断顾问-演示视频.mp4"
    subprocess.run(
        [ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(base), "-i", str(OUT / "配音-完整.mp3"),
         "-map", "0:v:0", "-map", "1:a:0",
         "-vf", "ass=字幕-中文字幕.ass:fontsdir='C\\:/Windows/Fonts'",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
         "-t", f"{total:.3f}", "-movflags", "+faststart", str(final)],
        check=True, cwd=str(OUT),
    )
    print(f"\n成片：{final}  ({final.stat().st_size / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
