# -*- coding: utf-8 -*-
"""按分镜整段合成配音（保留自然语流），再切分字幕时间轴。

与逐句合成相比：以「分镜」为单位一次性合成，句与句之间的停顿由模型自然产生，
不会出现一句一顿的机械感；字幕边界通过静音检测 + 字符比例回填得到。

产物（输出到 demo_video/）：
    配音-完整.mp3        整段旁白
    字幕-中文字幕.srt/.ass
    时间轴-分镜对位.csv
    时间轴.json          分镜级与句子级时间
    audio/B01.mp3 ...    每个分镜的语音（可单独替换重录）

用法：python docs/demo_video/build_voiceover.py
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from video_content import BLOCKS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "demo_video"
AUDIO = OUT / "audio"
WORK = OUT / "tmp"

SR = 48000
LEAD_IN = 1.2
TAIL = 1.6
GAP_BLOCK = 0.42      # 分镜之间
CHAPTER_GAP = 0.95    # 章节之间
SPEED = 5             # 百度语速 0-15
PER = 0               # 0 女声
REQ_DELAY = 0.8

TTS_URL = "https://tts.baidu.com/text2audio"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# 英文缩写的中文化读法（只影响语音，不影响字幕）
TTS_OVERRIDE = {
    "AI WEB 网页开发挑战赛": "AI Web 网页开发挑战赛",
    "diff": "差异",
    "PRD": "P R D",
    "MVP": "M V P",
    "A/B 方案": "A、B 方案",
    "A/B": "A、B",
    "SQLite": "circle light 数据库",
    "NDJSON": "N D JSON",
    "PBKDF2-SHA256": "P B K D F 2 加 S H A 256",
    "html2canvas": "html two canvas",
    "markdown-it": "markdown it",
    "highlight.js": "highlight 点 js",
    "LangChain": "Lang Chain",
    "LangGraph": "Lang Graph",
    "FastAPI": "Fast A P I",
    "reportlab": "report lab",
    "deepseek-v4.1-flash-1017": "deepseek V 4.1 flash 1017",
    "BM25": "B M 25",
}


def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def tts_text(text: str) -> str:
    out = text
    for k, v in TTS_OVERRIDE.items():
        out = out.replace(k, v)
    return out.replace("「", "").replace("」", "")


def synth(text: str, dest: Path, tries: int = 6) -> None:
    query = urllib.parse.urlencode({
        "tex": tts_text(text), "lan": "zh", "cuid": "jigou-demo",
        "ctp": "1", "pdt": "301", "vol": "9", "rate": "32",
        "spd": str(SPEED), "per": str(PER),
    })
    last = ""
    for i in range(tries):
        req = urllib.request.Request(
            f"{TTS_URL}?{query}",
            headers={"User-Agent": UA, "Referer": "https://tts.baidu.com/"},
        )
        try:
            with urllib.request.urlopen(req, timeout=40) as resp:
                ctype = resp.headers.get("Content-Type", "")
                data = resp.read()
            if "audio" in ctype and len(data) > 3000:
                dest.write_bytes(data)
                time.sleep(REQ_DELAY)
                return
            last = f"非音频：{ctype} {data[:100]!r}"
            if b"ratelimit" in data or b"529" in data:
                time.sleep(8 * (i + 1))
                continue
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(1.2 * (i + 1))
    raise RuntimeError(f"合成失败：{text[:20]} → {last}")


def to_pcm(src: Path, dst: Path) -> None:
    subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
         "-ac", "1", "-ar", str(SR), "-f", "s16le", "-acodec", "pcm_s16le", str(dst)],
        check=True,
    )


def trim_silence(pcm: Path, head_keep: int = 700, tail_keep: int = 2200) -> bytes:
    """只裁掉首尾长静音，句间停顿原样保留。"""
    raw = pcm.read_bytes()
    samples = memoryview(raw).cast("h")
    total = len(samples)
    thresh = 400
    head = 0
    while head < total - 1 and abs(samples[head]) < thresh:
        head += 1
    tail = total - 1
    while tail > head and abs(samples[tail]) < thresh:
        tail -= 1
    start = max(0, head - head_keep)
    end = min(total, tail + tail_keep)
    return raw[start * 2: end * 2]


def detect_silences(pcm: Path) -> list[tuple[float, float]]:
    """返回静音区间（秒）。"""
    p = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(pcm), "-af",
         "silencedetect=noise=-33dB:d=0.07", "-f", "null", "-"],
        capture_output=True, text=True, errors="replace",
    )
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    return [(s, e) for s, e in zip(starts, ends) if e - s >= 0.06]


def split_lines(text: str, limit: float = 17.0) -> list[str]:
    """字幕断行：只在标点/词边界断，绝不在英文单词中间断开。"""
    base = text.strip().rstrip("，。；、,.;：:!?！？")
    tokens = re.findall(
        r"[A-Za-z0-9][A-Za-z0-9\.\-+_/']*(?: [A-Za-z0-9][A-Za-z0-9\.\-+_/']*)*|\s+|\S",
        base,
    )
    if not tokens:
        return [base]

    def tw(t: str) -> float:
        if t.isspace():
            return 0.34
        return len(t) * 0.50 if re.match(r"[A-Za-z0-9]", t) else 1.0

    widths = [tw(t) for t in tokens]
    total = sum(widths)
    if total <= limit:
        return [base]

    def cut(tokens: list[str], widths: list[float]) -> list[str]:
        tot = sum(widths)
        if tot <= limit or len(tokens) < 2:
            return ["".join(tokens)]
        mid = tot / 2
        best, best_score = 1, 1e9
        acc = 0.0
        for i in range(1, len(tokens)):
            acc += widths[i - 1]
            if re.match(r"[A-Za-z0-9]", tokens[i]) and re.match(r"[A-Za-z0-9]", tokens[i - 1]):
                continue
            score = abs(acc - mid)
            if tokens[i - 1].isspace() or tokens[i].isspace():
                score += 0.9
            if tokens[i - 1] in "，、；：,;:":
                score -= 3.4
            if tokens[i] in "，、；：,;:。":
                score += 1.2
            if score < best_score:
                best, best_score = i, score
        left, right = tokens[:best], tokens[best:]
        lw, rw = widths[:best], widths[best:]
        if sum(lw) > limit * 1.12:
            return cut(left, lw) + ["".join(right)]
        if sum(rw) > limit * 1.12:
            return ["".join(left)] + cut(right, rw)
        return ["".join(left), "".join(right)]

    lines = [re.sub(r"\s+", " ", ln).strip().rstrip("，、；：,;:") for ln in cut(tokens, widths)]
    return [ln for ln in lines if ln] or [base]


def srt_time(sec: float) -> str:
    ms = int(round(max(0.0, sec) * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ass_time(sec: float) -> str:
    cs = int(round(max(0.0, sec) * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6_000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def align_cues(block: dict, body: bytes, silences: list[tuple[float, float]]) -> list[dict]:
    """在一个分镜音频内，把各句字幕对齐到自然停顿处。"""
    dur = len(body) / 2 / SR
    texts = block["cues"]
    if len(texts) == 1:
        return [{"text": texts[0], "start": 0.0, "end": dur}]

    chars = [max(len(t), 1) for t in texts]
    total_chars = sum(chars)
    cands = [(s + e) / 2 for s, e in silences]
    bounds = [0.0]
    cum = 0
    for i in range(len(texts) - 1):
        cum += chars[i]
        expect = dur * cum / total_chars
        pick, best = expect, 1.35
        for c in cands:
            d = abs(c - expect)
            if d < best:
                pick, best = c, d
        bounds.append(pick)
    bounds.append(dur)
    bounds = sorted(bounds)
    for i in range(1, len(bounds)):
        bounds[i] = max(bounds[i], bounds[i - 1] + 0.5)
    bounds[-1] = dur

    return [
        {"text": t, "start": bounds[i], "end": bounds[i + 1]}
        for i, t in enumerate(texts)
    ]


def main() -> int:
    for d in (OUT, AUDIO, WORK):
        d.mkdir(parents=True, exist_ok=True)

    blocks_audio: list[dict] = []
    for bi, block in enumerate(BLOCKS):
        mp3 = AUDIO / f"{block['id']}.mp3"
        text = "".join(block["cues"])
        if not mp3.exists() or mp3.stat().st_size < 3000:
            synth(text, mp3)
        pcm = WORK / f"{block['id']}.pcm"
        to_pcm(mp3, pcm)
        body = trim_silence(pcm)
        silences = detect_silences(pcm)
        cues = align_cues(block, body, silences)
        blocks_audio.append({
            "index": bi, "id": block["id"], "tag": block["tag"],
            "chapter": block["chapter"], "pcm": body, "cues": cues,
            "dur": len(body) / 2 / SR,
        })
        print(f"[{bi + 1:02d}/{len(BLOCKS)}] {block['id']} {len(body)/2/SR:5.2f}s "
              f"{len(cues)} 句  {block['tag']}")

    def sil(sec: float) -> bytes:
        return b"\x00\x00" * int(sec * SR)

    buf = bytearray(sil(LEAD_IN))
    prev_chapter = None
    flat: list[dict] = []
    for i, b in enumerate(blocks_audio):
        if i:
            gap = CHAPTER_GAP if b["chapter"] != prev_chapter else GAP_BLOCK
            buf.extend(sil(gap))
        block_start = len(buf) / 2 / SR
        b["start"] = block_start
        for c in b["cues"]:
            flat.append({
                "block_id": b["id"], "block_tag": b["tag"], "chapter": b["chapter"],
                "text": c["text"],
                "start": block_start + c["start"],
                "end": block_start + c["end"],
            })
        buf.extend(b["pcm"])
        b["end"] = len(buf) / 2 / SR
        prev_chapter = b["chapter"]
    buf.extend(sil(TAIL))
    duration = len(buf) / 2 / SR

    wav = WORK / "voiceover.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(bytes(buf))

    subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
         "-af", "highpass=f=60,acompressor=threshold=-18dB:ratio=3:attack=8:release=180,"
                "loudnorm=I=-16:TP=-2:LRA=9",
         "-ac", "2", "-ar", "44100", "-b:a", "192k", "-write_xing", "1",
         str(OUT / "配音-完整.mp3")],
        check=True,
    )
    subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
         "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le", str(OUT / "配音-完整.wav")],
        check=True,
    )

    srt, ass = [], []
    for i, c in enumerate(flat, 1):
        nxt = flat[i]["start"] if i < len(flat) else c["end"] + 0.6
        end = min(c["end"], nxt - 0.04) if nxt - c["end"] < 0.3 else c["end"]
        end = max(end, c["start"] + 0.8)
        srt.append(f"{i}\n{srt_time(c['start'])} --> {srt_time(end)}\n"
                   + "\n".join(split_lines(c["text"])) + "\n")
        ass.append(f"Dialogue: 0,{ass_time(c['start'])},{ass_time(end)},Main,,0,0,0,,"
                   f"{{\\fad(120,120)}}" + "\\N".join(split_lines(c["text"])))
    (OUT / "字幕-中文字幕.srt").write_text("\n".join(srt), encoding="utf-8")

    head = """[Script Info]
Title: 极构 · 需求诊断顾问 - 演示视频字幕
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Microsoft YaHei,54,&H00FFFFFF,&H00FFFFFF,&HCC1A1410,&H96000000,0,0,0,0,100,100,0.6,0,1,3.4,1.6,2,140,140,86,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    (OUT / "字幕-中文字幕.ass").write_text(head + "\n".join(ass) + "\n", encoding="utf-8")

    with (OUT / "时间轴-分镜对位.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["序号", "分镜", "环节", "章节", "起(s)", "止(s)", "时长(s)",
                    "起(时间码)", "止(时间码)", "字幕"])
        for i, c in enumerate(flat, 1):
            w.writerow([i, c["block_id"], c["block_tag"], c["chapter"],
                        f"{c['start']:.2f}", f"{c['end']:.2f}",
                        f"{c['end'] - c['start']:.2f}",
                        srt_time(c["start"]), srt_time(c["end"]), c["text"]])

    (OUT / "时间轴.json").write_text(json.dumps({
        "duration": round(duration, 3),
        "lead_in": LEAD_IN, "tail": TAIL,
        "voice": f"baidu per={PER} speed={SPEED}",
        "blocks": [{k: v for k, v in b.items() if k != "pcm"} for b in blocks_audio],
        "cues": [{**c, "dur": round(c["end"] - c["start"], 3)} for c in flat],
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n总时长 {duration/60:.2f} 分（{srt_time(duration)}），{len(flat)} 条字幕，"
          f"{len(blocks_audio)} 个分镜音频")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
