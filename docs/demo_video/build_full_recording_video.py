# -*- coding: utf-8 -*-
"""开头静态页 + 用户完整录屏（不剪） + 结尾，AI 男声与字幕。"""

from __future__ import annotations

import asyncio
import hashlib
import re
import subprocess
import wave
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "demo_video" / "静态页"
USER = Path(r"C:\Users\YNA\Videos\屏幕录制\屏幕录制 2026-11-01 011201.mp4")
WORK = ROOT / "demo_video" / "full_build"
AUDIO = WORK / "audio"
SEGS = WORK / "segs"
OUT = ROOT / "demo_video" / "极构-需求诊断顾问-演示视频-成片.mp4"

VOICE = "zh-CN-YunxiNeural"
RATE = "-8%"
SR = 48000
LEAD = 0.35
GAP = 0.28
TAIL = 0.8
FPS = 30

OPEN = [
    ("O1", "01-封面.png", "大家好，我们是极构团队。参赛作品是「极构 · 需求诊断顾问」，参加 AI WEB 网页开发挑战赛。"),
    ("O2", "02-首页.png", "很多创业者和个体店主想做一个系统，却说不清要做什么、大概多少钱、还缺哪些准备。极构用 AI 把一句「我想做个系统」，变成一份可以直接拿去开发、询价、立项的需求报告。"),
    ("O3", "09-功能-总览.png", "产品有六块核心能力：AI 问卷与自由对话、五段式报告、六维评分、三份交付物、验收版本，以及模板库和多格式导出。"),
    ("O4", "10-技术栈-前端.png", "前端是 Vue 3 + Vite，Pinia 管理状态，Vue Router 做登录守卫；Markdown 用 markdown-it 渲染，highlight.js 做代码高亮。"),
    ("O5", "11-技术栈-后端与AI.png", "后端是 FastAPI + Uvicorn，AI 编排用 LangChain 和 LangGraph，通过 OpenAI 兼容网关接入 deepseek-v4.1-flash-1017。"),
    ("O6", "12-技术栈-数据与输出.png", "数据层只用单文件 SQLite，密码用 PBKDF2-SHA256；PDF 用 reportlab，长截图用 html2canvas。"),
    ("O7", "13-RAG双通道.png", "RAG 是双通道：Chroma 向量检索加自研 BM25，向量服务不可用时自动降级，知识库 12 篇、32 个片段。"),
    ("O8", "14-总体架构.png", "整套系统不依赖数据库服务或容器，python run.py 一条命令启动。下面从 PyCharm 启动项目开始，完整看一遍流程。"),
]

# 录屏画面区间 + 该区间旁白（段尾不足时定格）
SECTIONS = [
    ("S1", 0.0, 12.0, "先在 PyCharm 里启动项目，浏览器打开本地服务。下面用问卷方式做一次完整的需求诊断。"),
    ("S2", 12.0, 45.0, "问卷不是固定题库，而是根据上一题动态生成下一题。先选产品形态，再补充目标用户、核心功能、预算和上线时间；每道题都能补充说明，也能回上一题修改。信息够了就收尾，不会没完没了地问。整个过程像和一位懂技术的顾问聊天，你只要把想法说清楚；不想回答的可以先跳过，后面再补。问卷的价值不是收集字段，而是帮你把模糊想法拆成可以判断的问题。"),
    ("S3", 45.0, 95.0, "提交后，系统先做意图整理，再检索十二篇软件开发知识库，最后组织五段式报告。这里等待的时间，就是模型在生成报告、抽取待确认事项和六维评分。知识库覆盖需求文档、技术选型、报价、工期、资质、风险和非功能需求，所以它能指出具体缺口，而不是泛泛而谈。前端通过 NDJSON 接收事件，能看到思考、检索和逐字输出；即使向量服务不可用，也会自动降级到 BM25，保证流程能走完。报告不是一次性黑盒，后面还可以继续确认和修订。等待期间页面会保持状态，不会丢问题。"),
    ("S4", 95.0, 150.0, "报告生成后回到首页，再打开我的图纸。正文按五段组织：项目概述、已具备、还缺失、待确认清单、建议下一步。已具备的部分逐条确认，缺失的部分对照知识库指出具体缺口，比如支付资质、会员体系、后台权限。待确认事项会单独列成清单，方便逐条拍板。往下是六维评分和风险提示，再往下是交付物：PRD、开发询价清单、成本工期。报告会引用你刚才的回答，不是模板套话；每一条缺口都对应一个需要补的信息，继续回答或修订就能补齐。这样报告既是诊断结果，也是下一步行动的清单。"),
    ("S5", 150.0, 210.0, "这里是 A/B 方案：MVP 和完整版对比预算、工期、功能范围、优点和代价，并给出推荐。MVP 先用极低成本验证需求，完整版一次覆盖支付、会员、后台等能力，按预算和上线时间取舍。再往下是待确认事项，可以一键全部确认；确认验收后生成版本号、报告指纹和与上一版的差异。以后改需求，能清楚看到每一版确认了什么。验收凭证也可以导出，作为书面依据。预算紧就选 MVP，先上线验证；预算充足、希望一次到位就选完整版。推荐只是建议，最终由你拍板。如果报告里有没想清楚的地方，可以随时回到问卷补充，或者直接修订报告。系统按账号隔离，换账号不会互相看到。"),
    ("S6", 210.0, 280.0, "自由对话走 Agent：先检索知识库，再按已具备、还缺失、待确认三段回答；前端通过 NDJSON 接收事件，所以能看到检索状态和逐字输出。生成过程中可以随时停止，已输出内容会保留；向量检索不可用时自动降级到 BM25。对话和问卷的结果都会合并进最终报告，即使你只说了一句模糊的想法，也能被追问成可执行的需求。Agent 会根据上下文决定是否继续追问，而不是固定轮次；它调用 search_knowledge 工具检索知识库，再把结果组织成回答。这样同一个问题，问法不同也能得到一致的结构。对话历史会保留在当前会话里，切回问卷也不会丢。如果对回答不满意，可以停止生成、补充说明或重新提问。前端会把工具调用、思考状态和正文分开显示，便于判断它到底做了什么。"),
    ("S7", 280.0, 291.4, "最后看成熟度评分和导出；Markdown、PDF、长截图都支持，手机也能查看。"),
]

END = ("E1", "21-结尾.png", "以上就是极构需求诊断顾问。让不懂技术的人，也能先把需求想清楚，再去找开发。谢谢大家。")


def ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def probe_duration(path: Path) -> float:
    p = subprocess.run([ffmpeg(), "-hide_banner", "-i", str(path)], capture_output=True, text=True, errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        raise RuntimeError("无法读取录屏时长")
    h, mnt, sec = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(sec)


def synth(text: str, bid: str) -> Path:
    key = hashlib.sha1(f"{VOICE}|{RATE}|{text}".encode()).hexdigest()[:12]
    mp3 = AUDIO / f"{bid}-{key}.mp3"
    if mp3.exists() and mp3.stat().st_size > 3000:
        return mp3
    async def run() -> None:
        await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(mp3))
    asyncio.run(run())
    return mp3


def to_pcm(mp3: Path, pcm: Path) -> None:
    subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp3),
                    "-ac", "1", "-ar", str(SR), "-f", "s16le", "-acodec", "pcm_s16le", str(pcm)], check=True)


def trim(pcm: Path, head_keep=500, tail_keep=700) -> bytes:
    raw = pcm.read_bytes()
    a = memoryview(raw).cast("h")
    n = len(a)
    th = 400
    head = 0
    while head < n - 1 and abs(a[head]) < th:
        head += 1
    tail = n - 1
    while tail > head and abs(a[tail]) < th:
        tail -= 1
    return raw[max(0, head - head_keep) * 2:min(n, tail + tail_keep) * 2]


def detect_silences(pcm: Path) -> list[tuple[float, float]]:
    p = subprocess.run(
        [ffmpeg(), "-hide_banner", "-i", str(pcm), "-af",
         "silencedetect=noise=-33dB:d=0.07", "-f", "null", "-"],
        capture_output=True, text=True, errors="replace",
    )
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    return [(s, e) for s, e in zip(starts, ends) if e - s >= 0.06]


def pcm_dur(b: bytes) -> float:
    return len(b) / 2 / SR


def sil(sec: float) -> bytes:
    return b"\x00\x00" * int(sec * SR)


def split_text(text: str, limit: int = 22) -> list[str]:
    out, buf = [], ""
    for ch in text:
        buf += ch
        if len(buf) >= limit and ch in "，。；、：":
            out.append(buf.strip())
            buf = ""
    if buf.strip():
        out.append(buf.strip())
    return out or [text]


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ass_time(t: float) -> str:
    cs = round(t * 100)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def main() -> int:
    for d in (WORK, AUDIO, SEGS):
        d.mkdir(parents=True, exist_ok=True)

    rec_dur = probe_duration(USER)
    cues: list[dict] = []

    # 开头音频
    open_pcm = bytearray(sil(LEAD))
    open_blocks: list[dict] = []
    for bid, png, text in OPEN:
        mp3 = synth(text, bid)
        pcm_path = WORK / f"{bid}.pcm"
        to_pcm(mp3, pcm_path)
        body = trim(pcm_path)
        dur = pcm_dur(body)
        start = pcm_dur(bytes(open_pcm))
        open_blocks.append({"id": bid, "png": png, "start": start, "dur": dur})
        chunks = split_text(text)
        total_chars = sum(len(c) for c in chunks) or 1
        cur = start
        for c in chunks:
            cd = max(1.0, dur * len(c) / total_chars)
            cues.append({"text": c, "start": cur, "end": min(start + dur, cur + cd)})
            cur += cd
        open_pcm.extend(body)
        open_pcm.extend(sil(GAP))

    open_total = pcm_dur(bytes(open_pcm))
    rec_start = open_total

    # 录屏音频：逐段连续放置；画面不足时视频段尾定格
    rec_buf = bytearray()
    sections = []
    t = rec_start
    for idx, (bid, a, z, text) in enumerate(SECTIONS):
        mp3 = synth(text, bid)
        pcm_path = WORK / f"{bid}.pcm"
        to_pcm(mp3, pcm_path)
        body = pcm_path.read_bytes()
        narr = pcm_dur(body)
        silences = detect_silences(pcm_path)
        src_dur = z - a
        seg_dur = max(src_dur, narr + 0.15)
        sections.append({"id": bid, "a": a, "z": z, "video_start": t,
                         "seg_dur": seg_dur, "narr_dur": narr})
        rec_buf.extend(body)
        rec_buf.extend(sil(max(0.0, seg_dur - narr)))
        if idx < len(SECTIONS) - 1:
            rec_buf.extend(sil(GAP))
            t += seg_dur + GAP
        else:
            t += seg_dur
        chunks = split_text(text)
        total_chars = sum(len(c) for c in chunks) or 1
        # 字幕句界吸附到自然停顿，避免长段按字数均分累积误差
        cands = [(x + y) / 2 for x, y in silences]
        bounds = [0.0]
        cum = 0
        for i in range(len(chunks) - 1):
            cum += len(chunks[i])
            expect = narr * cum / total_chars
            pick, best = expect, 1.1
            for c in cands:
                d = abs(c - expect)
                if d < best:
                    pick, best = c, d
            bounds.append(pick)
        bounds.append(narr)
        bounds = sorted(bounds)
        for i in range(1, len(bounds)):
            bounds[i] = max(bounds[i], bounds[i - 1] + 0.45)
        bounds[-1] = narr
        for i, c in enumerate(chunks):
            cues.append({"text": c, "start": sections[-1]["video_start"] + bounds[i],
                         "end": sections[-1]["video_start"] + bounds[i + 1]})

    rec_end = t

    # 结尾音频
    end_mp3 = synth(END[2], END[0])
    end_pcm_path = WORK / f"{END[0]}.pcm"
    to_pcm(end_mp3, end_pcm_path)
    end_body = trim(end_pcm_path)
    end_dur = pcm_dur(end_body)
    end_start = rec_end
    chunks = split_text(END[2])
    total_chars = sum(len(c) for c in chunks) or 1
    cur = end_start
    for c in chunks:
        cd = max(1.0, end_dur * len(c) / total_chars)
        cues.append({"text": c, "start": cur, "end": min(end_start + end_dur, cur + cd)})
        cur += cd

    total = end_start + end_dur + TAIL
    wav_path = WORK / "voice.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(bytes(open_pcm) + bytes(rec_buf) + end_body + sil(TAIL))

    # 字幕
    srt, ass = [], []
    for i, c in enumerate(cues, 1):
        srt.append(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n")
        ass.append(f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Main,,0,0,0,,{{\\fad(100,100)}}{c['text']}")
    (WORK / "字幕.srt").write_text("\n".join(srt), encoding="utf-8")
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Microsoft YaHei,40,&H00FFFFFF,&H00FFFFFF,&HCC1A1410,&H96000000,0,0,0,0,100,100,0.6,0,1,3.2,1.4,2,140,140,66,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    (WORK / "字幕.ass").write_text(head + "\n".join(ass) + "\n", encoding="utf-8")

    # 画面：开头静态
    segs = []
    for i, b in enumerate(open_blocks):
        nxt = open_blocks[i + 1]["start"] if i + 1 < len(open_blocks) else open_total
        dur = nxt - b["start"]
        dest = SEGS / f"open{i:02d}.mp4"
        subprocess.run([ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
                        "-loop", "1", "-framerate", str(FPS), "-i", str(STATIC / b["png"]),
                        "-t", f"{dur:.3f}",
                        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,format=yuv420p",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS), str(dest)], check=True)
        segs.append(dest)

    # 逐段录屏：保持原速，段尾不足时定格
    for idx, b in enumerate(sections):
        src_dur = b["z"] - b["a"]
        seg_dur = b["seg_dur"] + (GAP if idx < len(sections) - 1 else 0)
        dest = SEGS / f"rec{idx:02d}.mp4"
        vf = (
            "crop=2558:1286:0:80,"
            "scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,"
            "crop=1920:1080,fps=30,"
            f"tpad=stop_mode=clone:stop_duration={seg_dur - src_dur + 1:.3f},"
            f"trim=duration={seg_dur:.3f},setpts=PTS-STARTPTS,format=yuv420p"
        )
        subprocess.run([
            ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{b['a']:.3f}", "-i", str(USER),
            "-t", f"{src_dur:.3f}", "-vf", vf,
            "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-r", str(FPS), str(dest),
        ], check=True)
        segs.append(dest)
        print(f"{b['id']} 源 {src_dur:.1f}s 旁白 {b['narr_dur']:.1f}s 段长 {seg_dur:.1f}s")

    end_seg = SEGS / "end.mp4"
    subprocess.run([ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
                    "-loop", "1", "-framerate", str(FPS), "-i", str(STATIC / END[1]),
                    "-t", f"{end_dur + TAIL:.3f}",
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=white,format=yuv420p",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS), str(end_seg)], check=True)
    segs.append(end_seg)

    listing = WORK / "concat.txt"
    listing.write_text("\n".join(f"file '{s.as_posix()}'" for s in segs) + "\n", encoding="utf-8")
    base = WORK / "base.mp4"
    subprocess.run([ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(base)], check=True)

    subprocess.run([
        ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(base), "-i", str(wav_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "ass=字幕.ass:fontsdir='C\\:/Windows/Fonts'",
        "-af", "loudnorm=I=-16:TP=-2:LRA=9",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-t", f"{total:.3f}", "-movflags", "+faststart", str(OUT),
    ], check=True, cwd=str(WORK))

    print(f"成片：{OUT}  {OUT.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"时长：{total / 60:.2f} min（开头 {open_total:.1f}s + 录屏 {rec_dur:.1f}s + 结尾）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
