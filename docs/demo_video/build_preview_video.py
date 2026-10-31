# -*- coding: utf-8 -*-
"""按分镜合成演示视频画面（1080p），叠加已生成的配音与烧录字幕。

输入：
    docs/demo_video/video_content.py   分镜与画面类型
    demo_video/时间轴.json             每条字幕的起止时间（由 build_voiceover.py 产出）
    demo_video/字幕-中文字幕.ass       样式字幕
    demo_video/配音-完整.mp3           整段配音

输出：
    demo_video/极构-需求诊断顾问-演示视频（配音字幕预览）.mp4

用法：python docs/demo_video/build_preview_video.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from video_content import BLOCKS, CARDS, DELIVERABLES, SCORES, TECH_COLUMNS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "demo_video"
DOCS = ROOT / "docs"
FRAMES = OUT / "frames"
SEGS = OUT / "tmp" / "segs"

W, H = 1920, 1080
FPS = 25

INK = (28, 25, 72)
INK2 = (66, 62, 108)
MUTED = (112, 108, 142)
LINE = (225, 223, 244)
WHITE = (255, 255, 255)
ACC = (95, 78, 232)
ACC2 = (124, 58, 237)
CYAN = (10, 175, 205)
BG1 = (251, 250, 255)
BG2 = (238, 236, 255)

FONT_R = "C:/Windows/Fonts/msyh.ttc"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"


@lru_cache(maxsize=64)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def text_w(draw: ImageDraw.ImageDraw, s: str, f) -> int:
    return int(draw.textlength(s, font=f))


def gradient(size, top, bottom) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / max(h - 1, 1)
        d.point((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    return img.resize((w, h), Image.BILINEAR)


def glow(img: Image.Image, xy, radius: int, color, alpha: int = 60) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    d.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius // 2))
    img.alpha_composite(layer)


def shadow(img: Image.Image, box, r: int, blur: int = 26, dy: int = 14, alpha: int = 42):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0, y0 + dy, x1, y1 + dy], radius=r, fill=(35, 30, 85, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)


def base_canvas() -> Image.Image:
    canvas = gradient((W, H), BG1, BG2).convert("RGBA")
    glow(canvas, (W - 120, 60), 520, ACC, 26)
    glow(canvas, (120, H - 40), 460, CYAN, 20)
    return canvas


def label_block(img: Image.Image, chapter: str, title: str, sub: str = "") -> None:
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([120, 62, 120 + text_w(d, chapter, font(24, True)) + 44, 110],
                        radius=24, fill=(255, 255, 255, 235), outline=LINE)
    d.text((142, 74), chapter, font=font(24, True), fill=ACC)
    d.text((120, 128), title, font=font(56, True), fill=INK)
    if sub:
        d.text((122 + text_w(d, title, font(56, True)) + 24, 150), sub, font=font(26), fill=MUTED)


def rounded_image(path: Path, size, radius: int = 18) -> Image.Image:
    im = Image.open(path).convert("RGB")
    tw, th = size
    scale = min(tw / im.width, th / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width, im.height], radius=radius, fill=255)
    im = im.convert("RGBA")
    im.putalpha(mask)
    return im


def frame_shot(shot: dict) -> Image.Image:
    img = base_canvas()
    path = DOCS / shot["image"]
    area = (1520, 736)
    pic = rounded_image(path, area, 18)
    x = (W - pic.width) // 2
    y = 122 + (area[1] - pic.height) // 2
    shadow(img, [x, y, x + pic.width, y + pic.height], 18, 30, 16, 52)
    img.alpha_composite(pic, (x, y))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + pic.width, y + pic.height], radius=18,
                        outline=(255, 255, 255, 200), width=2)

    cap = shot.get("caption", "")
    if cap:
        cf = font(27)
        cw = text_w(d, cap, cf) + 92
        cx0 = (W - cw) // 2
        d.rounded_rectangle([cx0, 44, cx0 + cw, 96], radius=26,
                            fill=(255, 255, 255), outline=LINE, width=2)
        d.ellipse([cx0 + 34, 62, cx0 + 46, 74], fill=ACC)
        d.text((cx0 + 60, 54), cap, font=cf, fill=INK2)
    return img


def frame_title() -> Image.Image:
    img = gradient((W, H), (32, 25, 84), (18, 40, 82)).convert("RGBA")
    glow(img, (W // 2, 340), 620, (124, 58, 237), 60)
    glow(img, (240, H - 80), 480, (6, 150, 190), 40)
    d = ImageDraw.Draw(img)
    badge = "2026 第九届传智杯 · AI WEB 网页开发挑战赛"
    bw = text_w(d, badge, font(26, True)) + 56
    d.rounded_rectangle([(W - bw) // 2, 236, (W + bw) // 2, 292], radius=28,
                        fill=(255, 255, 255, 28), outline=(255, 255, 255, 80))
    d.text(((W - text_w(d, badge, font(26, True))) // 2, 250), badge, font=font(26, True),
           fill=(214, 208, 255))

    title = "极构 · 需求诊断顾问"
    d.text(((W - text_w(d, title, font(104, True))) // 2, 352), title, font=font(104, True),
           fill=WHITE)
    sub = "把「我想做个系统」，变成一份可执行的需求报告"
    d.text(((W - text_w(d, sub, font(40))) // 2, 512), sub, font=font(40), fill=(214, 210, 240))
    line_y = 620
    d.rounded_rectangle([W // 2 - 90, line_y, W // 2 + 90, line_y + 5], radius=3,
                        fill=(120, 110, 255))
    team = "沧州交通学院 · 极构团队 · B 组"
    d.text(((W - text_w(d, team, font(30))) // 2, 672), team, font=font(30), fill=(178, 174, 215))
    return img


def frame_end() -> Image.Image:
    img = gradient((W, H), (32, 25, 84), (18, 40, 82)).convert("RGBA")
    glow(img, (W // 2, 300), 560, (124, 58, 237), 52)
    d = ImageDraw.Draw(img)
    t = "谢谢观看"
    d.text(((W - text_w(d, t, font(96, True))) // 2, 316), t, font=font(96, True), fill=WHITE)
    s = "极构 · 需求诊断顾问 —— 让不懂技术的人，也能先把需求想清楚"
    d.text(((W - text_w(d, s, font(34))) // 2, 452), s, font=font(34), fill=(210, 206, 240))
    line = "沧州交通学院 · 极构团队 · B 组 · 贾宇航、吴思彤、马翌焜 · 指导教师 王玉潇"
    d.text(((W - text_w(d, line, font(28))) // 2, 640), line, font=font(28), fill=(160, 156, 200))
    return img


def card(img, box, radius=22, fill=(255, 255, 255, 246), outline=LINE, width=2, dy=12):
    shadow(img, box, radius, 24, dy, 34)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap(d, s: str, f, limit: int) -> list[str]:
    lines, cur = [], ""
    for ch in s:
        if text_w(d, cur + ch, f) > limit:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def frame_cards6(highlight: list[int]) -> Image.Image:
    img = base_canvas()
    label_block(img, "02 功能地图", "六块核心能力", "从一句想法到可执行材料")
    d = ImageDraw.Draw(img)
    x0, y0 = 120, 268
    cw, chh, gap, gy = 536, 274, 36, 40
    for i, (no, title, desc) in enumerate(CARDS):
        col, row = i % 3, i // 3
        x = x0 + col * (cw + gap)
        y = y0 + row * (chh + gy)
        on = i in highlight
        card(img, [x, y, x + cw, y + chh], 24,
             fill=(255, 255, 255, 250) if on else (255, 255, 255, 190),
             outline=ACC if on else LINE, width=3 if on else 2)
        d = ImageDraw.Draw(img)
        d.text((x + 34, y + 30), no, font=font(34, True), fill=ACC if on else (196, 192, 220))
        d.text((x + 34, y + 84), title, font=font(32, True), fill=INK if on else INK2)
        for j, ln in enumerate(wrap(d, desc, font(22), cw - 70)[:3]):
            d.text((x + 34, y + 146 + j * 32), ln, font=font(22),
                   fill=MUTED if on else (150, 146, 178))
    return img


def frame_tech3(idx: int) -> Image.Image:
    img = base_canvas()
    label_block(img, "03 技术栈", "三层架构", "前端 · 后端与 AI · 数据与输出")
    d = ImageDraw.Draw(img)
    x0, y0, cw, chh, gap = 120, 268, 536, 556, 36
    for i, (head, lead, rows) in enumerate(TECH_COLUMNS):
        x = x0 + i * (cw + gap)
        on = i == idx
        card(img, [x, y0, x + cw, y0 + chh], 24,
             fill=(255, 255, 255, 250) if on else (255, 255, 255, 185),
             outline=ACC if on else LINE, width=3 if on else 2)
        d = ImageDraw.Draw(img)
        pw = text_w(d, head, font(26, True)) + 44
        d.rounded_rectangle([x + 34, y0 + 34, x + 34 + pw, y0 + 82], radius=24,
                            fill=(ACC if on else (238, 236, 250)))
        d.text((x + 56, y0 + 46), head, font=font(26, True),
               fill=WHITE if on else INK2)
        d.text((x + 34, y0 + 108), lead, font=font(26, True), fill=INK if on else INK2)
        for j, r in enumerate(rows):
            yy = y0 + 176 + j * 96
            d.ellipse([x + 36, yy + 12, x + 44, yy + 20], fill=ACC if on else (190, 186, 220))
            for k, ln in enumerate(wrap(d, r, font(23), cw - 90)[:2]):
                d.text((x + 58, yy + k * 30), ln, font=font(23),
                       fill=INK2 if on else (140, 136, 172))
    return img


def frame_score() -> Image.Image:
    img = base_canvas()
    label_block(img, "05 报告与交付物", "六维成熟度评分", "一眼看出需求还想清了没")
    d = ImageDraw.Draw(img)
    x0, y0 = 120, 300
    for i, (name, val) in enumerate(SCORES):
        y = y0 + i * 92
        d.text((x0, y - 4), name, font=font(28, True), fill=INK2)
        track = [x0 + 120, y + 6, x0 + 1180, y + 40]
        d.rounded_rectangle(track, radius=17, fill=(255, 255, 255, 210), outline=LINE)
        fill_box = [track[0], track[1], track[0] + int((track[2] - track[0]) * val / 100), track[3]]
        d.rounded_rectangle(fill_box, radius=17, fill=ACC if val >= 70 else ACC2)
        d.text((x0 + 1210, y - 2), str(val), font=font(34, True), fill=ACC)
    panel = [1420, 280, 1800, 800]
    card(img, panel, 24)
    d = ImageDraw.Draw(img)
    d.text((1456, 314), "风险提示", font=font(30, True), fill=INK)
    risks = ["预算区间尚未锁定", "时间窗口偏紧（约 6 周）", "合规条款需补充确认"]
    for j, r in enumerate(risks):
        yy = 380 + j * 76
        d.rounded_rectangle([1456, yy + 8, 1470, yy + 22], radius=4, fill=(214, 96, 70))
        for k, ln in enumerate(wrap(d, r, font(22), 300)[:2]):
            d.text((1486, yy + k * 28), ln, font=font(22), fill=INK2)
    d.text((1456, 700), "总分  ·  70 / 100", font=font(26, True), fill=MUTED)
    return img


def frame_deliverables() -> Image.Image:
    img = base_canvas()
    label_block(img, "05 报告与交付物", "三份交付物 + A/B 方案", "能直接发给开发方")
    d = ImageDraw.Draw(img)
    x0, y0, cw, chh, gap = 120, 268, 520, 300, 40
    for i, (tag, name, desc) in enumerate(DELIVERABLES):
        x = x0 + i * (cw + gap)
        card(img, [x, y0, x + cw, y0 + chh], 24)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([x + 34, y0 + 34, x + 34 + text_w(d, tag, font(24, True)) + 44,
                             y0 + 82], radius=22, fill=(240, 238, 252))
        d.text((x + 56, y0 + 46), tag, font=font(24, True), fill=ACC)
        d.text((x + 34, y0 + 104), name, font=font(32, True), fill=INK)
        for j, ln in enumerate(wrap(d, desc, font(23), cw - 70)[:3]):
            d.text((x + 34, y0 + 164 + j * 32), ln, font=font(23), fill=MUTED)
    # A/B 方案
    ab = [120, 596, 1800, 856]
    card(img, ab, 26, fill=(255, 255, 255, 236))
    d = ImageDraw.Draw(img)
    d.text((162, 626), "A / B 两套方案", font=font(30, True), fill=INK)
    half = [156, 686, 936, 826]
    for i, (name, note) in enumerate(
        [("MVP 版", "先跑通核心流程，4 周可上线"), ("完整版", "含运营后台与数据看板，8–10 周")]
    ):
        x = half[0] + i * 852
        box = [x, half[1], x + 780, half[3]]
        d.rounded_rectangle(box, radius=18, fill=(247, 246, 255) if i == 0 else (240, 249, 252),
                            outline=ACC if i == 0 else CYAN, width=2)
        d.text((x + 28, half[1] + 22), name, font=font(28, True), fill=ACC if i == 0 else (8, 140, 170))
        d.text((x + 28, half[1] + 70), note, font=font(24), fill=INK2)
    return img


def frame_version() -> Image.Image:
    img = base_canvas()
    label_block(img, "05 报告与交付物", "验收版本与 diff", "留下书面凭证")
    d = ImageDraw.Draw(img)
    panel = [120, 262, 1800, 858]
    card(img, panel, 26)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([162, 300, 250, 366], radius=16, fill=ACC)
    d.text((178, 314), "v2", font=font(34, True), fill=WHITE)
    d.text((272, 306), "已验收 · 2026-10-31 21:08", font=font(26), fill=MUTED)
    d.text((162, 386), "报告指纹", font=font(24, True), fill=INK2)
    d.text((162, 422), "8f3c·a91d·5b27·e4f0·7c16·2ab9", font=font(26), fill=INK)
    d.text((162, 486), "与 v1 的差异", font=font(24, True), fill=INK2)
    rows = [
        ("+", "新增：六维评分补充「合规」维度的判定依据", (16, 138, 96)),
        ("~", "调整：预算区间 3–5 万改为 4–6 万，工期 +1 周", (176, 118, 20)),
        ("-", "删除：原「后台权限分级」条款并入完整版", (190, 70, 60)),
    ]
    for i, (mark, txt, color) in enumerate(rows):
        y = 534 + i * 92
        tint = tuple(int(c + (255 - c) * 0.86) for c in color)
        d.rounded_rectangle([162, y + 6, 210, y + 54], radius=12, fill=tint)
        dtext = mark
        d.text((162 + (48 - text_w(d, dtext, font(28, True))) // 2, y + 12),
               dtext, font=font(28, True), fill=color)
        d.text((232, y + 12), txt, font=font(26), fill=INK2)
    d.rounded_rectangle([162, 788, 1758, 790], radius=1, fill=LINE)
    d.text((162, 806), "每次确认都会生成版本号、指纹与差异，改需求不再靠口头沟通",
           font=font(24), fill=MUTED)
    return img


# ---------------------------------------------------------------- 时间轴与合成

def safe(text: str) -> str:
    """替换微软雅黑缺字的符号，避免出现方框。"""
    return text.replace("⇄", "／").replace("⇋", "／")


def build_segments(tl: dict) -> list[dict]:
    """按分镜切分镜头：镜头在其首条字幕前 0.35s 切入，最短保留 0.9s。"""
    cues = tl["cues"]
    by_block: dict[str, list[int]] = {}
    for i, c in enumerate(cues):
        by_block.setdefault(c["block_id"], []).append(i)

    shots: list[dict] = []
    desired: list[float] = []
    for block in BLOCKS:
        idxs = by_block[block["id"]]
        for shot in block["shots"]:
            a = idxs[shot["cues"][0]]
            shots.append(shot)
            desired.append(0.0 if not desired else max(0.0, cues[a]["start"] - 0.35))

    MIN_GAP = 0.9
    starts = [desired[0]]
    for d in desired[1:]:
        starts.append(max(d, starts[-1] + MIN_GAP))

    segs = []
    for i, shot in enumerate(shots):
        segs.append({
            "shot": shot,
            "start": starts[i],
            "end": starts[i + 1] if i + 1 < len(starts) else tl["duration"],
        })
    return segs


def render_frame(shot: dict) -> Image.Image:
    t = shot["type"]
    if t == "title":
        return frame_title()
    if t == "end":
        return frame_end()
    if t == "shot":
        shot = dict(shot)
        shot["caption"] = safe(shot.get("caption", ""))
        return frame_shot(shot)
    if t == "cards6":
        return frame_cards6(shot.get("highlight", []))
    if t == "tech3":
        return frame_tech3(shot.get("highlight", 0))
    if t == "score":
        return frame_score()
    if t == "deliverables":
        return frame_deliverables()
    if t == "version":
        return frame_version()
    raise ValueError(t)


def ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def main() -> int:
    tl = json.loads((OUT / "时间轴.json").read_text(encoding="utf-8"))
    FRAMES.mkdir(parents=True, exist_ok=True)
    SEGS.mkdir(parents=True, exist_ok=True)

    segs = build_segments(tl)
    print(f"共 {len(segs)} 个镜头，总时长 {tl['duration']:.2f}s")

    exe = ffmpeg()
    concat_list = []
    for i, s in enumerate(segs):
        dur = max(0.9, s["end"] - s["start"])
        png = FRAMES / f"{i:02d}_{s['shot']['type']}.png"
        img = render_frame(s["shot"])
        img.convert("RGB").save(png)
        seg = SEGS / f"{i:02d}.mp4"
        fade = 0.30 if dur > 1.4 else 0.15
        vf = (
            "scale=2074:1166:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop=1920:1080:(iw-1920)/2:(ih-1080)*min(t/{dur:.3f}\\,1),"
            f"fade=t=in:st=0:d={fade},fade=t=out:st={max(0.0, dur - fade):.3f}:d={fade},"
            "format=yuv420p"
        )
        subprocess.run(
            [exe, "-y", "-hide_banner", "-loglevel", "error",
             "-loop", "1", "-framerate", str(FPS), "-i", str(png),
             "-t", f"{dur:.3f}", "-vf", vf,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
             "-r", str(FPS), "-pix_fmt", "yuv420p", str(seg)],
            check=True,
        )
        concat_list.append(f"file '{seg.as_posix()}'")
        print(f"  [{i + 1:02d}/{len(segs)}] {s['shot']['type']:<12} {dur:6.2f}s")

    listing = OUT / "tmp" / "concat.txt"
    listing.write_text("\n".join(concat_list) + "\n", encoding="utf-8")
    base = OUT / "tmp" / "base.mp4"
    subprocess.run(
        [exe, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
         "-safe", "0", "-i", str(listing), "-c", "copy", str(base)],
        check=True,
    )

    final = OUT / "极构-需求诊断顾问-演示视频（配音字幕预览）.mp4"
    ass = (OUT / "字幕-中文字幕.ass")
    subprocess.run(
        [exe, "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(base), "-i", str(OUT / "配音-完整.mp3"),
         "-map", "0:v:0", "-map", "1:a:0",
         "-vf", f"ass={ass.name}:fontsdir='C\\:/Windows/Fonts'",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
         "-t", f"{tl['duration']:.3f}", "-movflags", "+faststart", str(final)],
        check=True, cwd=str(OUT),
    )
    size = final.stat().st_size / 1024 / 1024
    print(f"\n成片：{final}  ({size:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
