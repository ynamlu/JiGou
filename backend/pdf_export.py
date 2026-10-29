"""Markdown 报告 → PDF（reportlab）。

只做排版，不解析业务语义：标题、段落、列表、代码块、表格按出现顺序渲染。
中文字体使用 reportlab 内置的 STSong-Light，不依赖系统安装字体。
"""

import re
from html import escape as _escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONT = "STSong-Light"

_registered = False


def _ensure_font():
    global _registered
    if _registered:
        return
    pdfmetrics.registerFont(UnicodeCIDFont(FONT))
    pdfmetrics.registerFontFamily(
        FONT, normal=FONT, bold=FONT, italic=FONT, boldItalic=FONT
    )
    _registered = True


def _styles():
    return {
        "title": ParagraphStyle(
            "CNTitle", fontName=FONT, fontSize=20, leading=28,
            textColor=colors.HexColor("#111827"), spaceAfter=14, wordWrap="CJK",
        ),
        "h1": ParagraphStyle(
            "CNH1", fontName=FONT, fontSize=15, leading=22,
            textColor=colors.HexColor("#111827"), spaceBefore=13, spaceAfter=7, wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "CNH2", fontName=FONT, fontSize=13, leading=20,
            textColor=colors.HexColor("#4f46e5"), spaceBefore=10, spaceAfter=5, wordWrap="CJK",
        ),
        "h3": ParagraphStyle(
            "CNH3", fontName=FONT, fontSize=11.5, leading=18,
            textColor=colors.HexColor("#111827"), spaceBefore=8, spaceAfter=4, wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "CNBody", fontName=FONT, fontSize=10.5, leading=17,
            textColor=colors.HexColor("#1f2937"), spaceAfter=5, wordWrap="CJK",
        ),
        "li": ParagraphStyle(
            "CNLi", fontName=FONT, fontSize=10.5, leading=17,
            textColor=colors.HexColor("#1f2937"), leftIndent=12, spaceAfter=3, wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "CNCode", fontName=FONT, fontSize=9, leading=14,
            textColor=colors.HexColor("#111827"), leftIndent=10, spaceBefore=4, spaceAfter=8,
            wordWrap="CJK",
        ),
        "cell": ParagraphStyle(
            "CNCell", fontName=FONT, fontSize=9.5, leading=14,
            textColor=colors.HexColor("#1f2937"), wordWrap="CJK",
        ),
    }


def _inline(text):
    text = _escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<font color='#c2410c'>\1</font>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return text


_HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
_UL_RE = re.compile(r"^[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^\d+[.)]\s+(.*)$")


def _starts_block(line):
    s = line.strip()
    return bool(
        _HEAD_RE.match(s)
        or s.startswith("```")
        or s.startswith("|")
        or _HR_RE.match(s)
        or _UL_RE.match(s)
        or _OL_RE.match(s)
    )


def _parse(md):
    lines = (md or "").splitlines()
    blocks = []
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", "\n".join(buf)))
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            blocks.append(("table", rows))
            continue
        if _HR_RE.match(s):
            blocks.append(("hr", None))
            i += 1
            continue
        m = _HEAD_RE.match(s)
        if m:
            blocks.append(("h" + str(len(m.group(1))), m.group(2).strip()))
            i += 1
            continue
        if _UL_RE.match(s):
            items = []
            while i < n and _UL_RE.match(lines[i].strip()):
                items.append(_UL_RE.match(lines[i].strip()).group(1))
                i += 1
            blocks.append(("ul", items))
            continue
        if _OL_RE.match(s):
            items = []
            while i < n and _OL_RE.match(lines[i].strip()):
                items.append(_OL_RE.match(lines[i].strip()).group(1))
                i += 1
            blocks.append(("ol", items))
            continue
        para = [s]
        i += 1
        while i < n and lines[i].strip() and not _starts_block(lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(("p", " ".join(para)))
    return blocks


def _table(rows, st):
    parsed = []
    for raw in rows:
        parsed.append([c.strip() for c in raw.strip().strip("|").split("|")])
    if not parsed:
        return Spacer(1, 1)
    if len(parsed) > 1 and all(re.fullmatch(r":?-{2,}:?", c) for c in parsed[1]):
        parsed.pop(1)
    ncols = max(len(r) for r in parsed)
    data = []
    for r in parsed:
        r = r + [""] * (ncols - len(r))
        data.append([Paragraph(_inline(c), st["cell"]) for c in r])
    tbl = Table(data, colWidths=[(A4[0] - 36 * mm) / ncols] * ncols)
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def _to_flowables(blocks, st):
    out = []
    for kind, val in blocks:
        if kind == "h1":
            out.append(Paragraph(_inline(val), st["title"]))
        elif kind == "h2":
            out.append(Paragraph(_inline(val), st["h1"]))
        elif kind == "h3":
            out.append(Paragraph(_inline(val), st["h2"]))
        elif kind in ("h4", "h5", "h6"):
            out.append(Paragraph(_inline(val), st["h3"]))
        elif kind == "hr":
            out.append(HRFlowable(
                width="100%", thickness=0.6,
                color=colors.HexColor("#e5e7eb"), spaceBefore=6, spaceAfter=6,
            ))
        elif kind == "p":
            out.append(Paragraph(_inline(val), st["body"]))
        elif kind == "ul":
            for it in val:
                out.append(Paragraph("•&nbsp;&nbsp;" + _inline(it), st["li"]))
        elif kind == "ol":
            for idx, it in enumerate(val, 1):
                out.append(Paragraph(f"{idx}.&nbsp;&nbsp;" + _inline(it), st["li"]))
        elif kind == "code":
            out.append(Preformatted(val, st["code"]))
        elif kind == "table":
            out.append(_table(val, st))
    return out


def render_pdf(markdown_text, title="需求诊断报告"):
    """把 Markdown 文本渲染成 PDF 字节流，供接口直接返回给浏览器下载。"""
    _ensure_font()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=title, author="极构 · 需求诊断顾问",
    )
    st = _styles()

    def footer(canvas, docobj):
        canvas.saveState()
        canvas.setFont(FONT, 8)
        canvas.setFillColor(colors.HexColor("#9aa3b5"))
        canvas.drawCentredString(A4[0] / 2, 10 * mm, f"- {docobj.page} -")
        canvas.restoreState()

    flow = _to_flowables(_parse(markdown_text), st)
    if not flow:
        flow = [Paragraph("（无内容）", st["body"])]
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
