"""生成技术文档用的三张示意图（Pillow 绘制，不依赖外部工具）。"""

import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagrams")
os.makedirs(OUT, exist_ok=True)

FONT_REG = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"

INK = "#0F172A"
MUTED = "#5B6478"
LINE = "#D9E0F2"
INDIGO = "#4F46E5"
VIOLET = "#7C3AED"
CYAN = "#0891B2"
SOFT = "#EEF1FF"
WHITE = "#FFFFFF"
BG = "#F8FAFF"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def shadow_box(d, box, radius=24, fill=WHITE, outline=LINE, width=2, offset=6):
    x1, y1, x2, y2 = box
    d.rounded_rectangle((x1 + offset, y1 + offset, x2 + offset, y2 + offset), radius, fill="#E9EDF9")
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)


def text(d, xy, s, size=24, fill=INK, bold=False, anchor="la", spacing=8):
    f = font(size, bold)
    if "\n" in s:
        d.multiline_text(xy, s, font=f, fill=fill, anchor=anchor, spacing=spacing)
    else:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)


def arrow(d, start, end, fill=INDIGO, width=4):
    d.line([start, end], fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    if abs(x2 - x1) >= abs(y2 - y1):
        sign = 1 if x2 > x1 else -1
        pts = [(x2, y2), (x2 - 16 * sign, y2 - 8), (x2 - 16 * sign, y2 + 8)]
    else:
        sign = 1 if y2 > y1 else -1
        pts = [(x2, y2), (x2 - 8, y2 - 16 * sign), (x2 + 8, y2 - 16 * sign)]
    d.polygon(pts, fill=fill)


# ---------------- 总体架构 ----------------
def architecture():
    W, H = 1800, 1000
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    text(d, (70, 46), "极构 · 总体技术架构", 40, INK, True)

    # 浏览器
    shadow_box(d, (70, 150, 560, 900))
    text(d, (315, 195), "浏览器 · Vue 3 SPA", 30, INDIGO, True, "ma")
    text(d, (315, 235), "Vite 构建 · Pinia 状态 · 路由守卫", 19, MUTED, False, "ma")
    items = ["登录 / 注册", "对话诊断", "问卷答题", "报告详情", "模板库", "我的图纸"]
    for i, it in enumerate(items):
        y = 300 + i * 82
        d.rounded_rectangle((110, y, 520, y + 58), 16, fill=SOFT, outline="#DDE3FF")
        text(d, (315, y + 29), it, 23, "#3730A3", False, "mm")

    # 后端
    shadow_box(d, (650, 120, 1240, 930), fill=WHITE, outline="#C7D2FE")
    text(d, (945, 165), "FastAPI 本地服务", 30, INDIGO, True, "ma")
    text(d, (945, 205), "单进程 · 同时托管前端静态文件", 19, MUTED, False, "ma")
    services = [
        ("账号与鉴权", "手机号注册 / 登录 · Bearer Token"),
        ("Agent 工作流", "LangChain · 工具调用 · 会话记忆"),
        ("RAG 检索", "Chroma 向量 / BM25 关键词（自动降级）"),
        ("结构化输出", "问卷 / 评分 / 待确认项 / 交付物"),
        ("安全与导出", "输入审查 · 脱敏 · PDF / 截图"),
    ]
    for i, (title, desc) in enumerate(services):
        y = 255 + i * 128
        d.rounded_rectangle((690, y, 1200, y + 108), 18, fill="#FBFCFE", outline=LINE)
        text(d, (715, y + 26), title, 23, INK, True)
        text(d, (715, y + 64), desc, 17, MUTED)

    # 模型
    shadow_box(d, (1330, 150, 1730, 400), fill="#F5F3FF", outline="#DDD6FE")
    text(d, (1530, 195), "模型网关", 28, VIOLET, True, "ma")
    text(d, (1530, 245), "OpenAI 兼容协议", 19, MUTED, False, "ma")
    text(d, (1530, 300), "deepseek-v4.1-flash-1017", 20, "#5B21B6", True, "ma")
    text(d, (1530, 340), "/compatible-mode/v1", 17, MUTED, False, "ma")

    # 数据
    shadow_box(d, (1330, 450, 1730, 650), fill="#ECFEFF", outline="#A5F3FC")
    text(d, (1530, 485), "SQLite（单文件）", 24, CYAN, True, "ma")
    text(d, (1530, 530), "users / tokens", 18, "#155E75", False, "ma")
    text(d, (1530, 562), "acceptances（验收记录）", 18, "#155E75", False, "ma")
    text(d, (1530, 606), "backend/data/jigou.db", 16, MUTED, False, "ma")

    shadow_box(d, (1330, 700, 1730, 880), fill="#F0FDF4", outline="#BBF7D0")
    text(d, (1530, 735), "localStorage", 24, "#15803D", True, "ma")
    text(d, (1530, 780), "报告归档 · 分析草稿", 18, "#166534", False, "ma")
    text(d, (1530, 815), "按账号隔离", 16, MUTED, False, "ma")

    # 箭头
    arrow(d, (560, 520), (648, 520))
    text(d, (604, 486), "NDJSON", 17, INDIGO, True, "ma")
    text(d, (604, 552), "流式", 16, MUTED, False, "ma")

    arrow(d, (1240, 300), (1328, 300), VIOLET)
    text(d, (1284, 266), "HTTPS", 17, VIOLET, True, "ma")

    d.line([(1240, 560), (1285, 560), (1285, 560)], fill="#94A3B8", width=3)
    d.line([(1285, 560), (1285, 560)], fill="#94A3B8", width=3)
    arrow(d, (1240, 560), (1328, 560), "#0891B2")
    text(d, (1284, 526), "SQL", 16, CYAN, True, "ma")

    d.line([(1240, 790), (1285, 790)], fill="#94A3B8", width=3)
    arrow(d, (1240, 790), (1328, 790), "#16A34A")
    text(d, (1284, 756), "本地", 16, "#15803D", True, "ma")

    img.save(os.path.join(OUT, "architecture.png"))


# ---------------- RAG 双通道 ----------------
def rag():
    W, H = 1800, 900
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    text(d, (70, 46), "RAG 双通道与自动降级", 40, INK, True)

    shadow_box(d, (70, 360, 330, 500), fill=SOFT, outline="#C7D2FE")
    text(d, (200, 410), "用户问题", 26, "#3730A3", True, "ma")
    text(d, (200, 452), "自然语言 / 语音转写", 17, MUTED, False, "ma")

    shadow_box(d, (420, 180, 800, 340), fill=WHITE)
    text(d, (610, 215), "通道 A：向量检索", 25, INDIGO, True, "ma")
    text(d, (610, 262), "Chroma + Embedding", 19, MUTED, False, "ma")
    text(d, (610, 300), "相似度 Top-3", 18, "#3730A3", False, "ma")

    shadow_box(d, (420, 560, 800, 720), fill=WHITE)
    text(d, (610, 595), "通道 B：BM25 检索", 25, CYAN, True, "ma")
    text(d, (610, 642), "中文二元切分 · 停用词", 19, MUTED, False, "ma")
    text(d, (610, 680), "标题加权 · 同源去重 Top-3", 18, "#155E75", False, "ma")

    arrow(d, (335, 430), (415, 260))
    arrow(d, (335, 430), (415, 640))
    text(d, (365, 300), "已配置", 15, MUTED)
    text(d, (365, 560), "兜底", 15, MUTED)

    shadow_box(d, (880, 300, 1180, 600), fill="#FBFCFE")
    text(d, (1030, 340), "检索结果", 24, INK, True, "ma")
    text(d, (1030, 390), "知识片段 + 来源", 18, MUTED, False, "ma")
    text(d, (1030, 430), "最多 3 条", 17, MUTED, False, "ma")
    d.line([(1030, 470), (1030, 540)], fill=LINE, width=2)
    text(d, (1030, 500), "失败自动降级", 16, "#B45309", False, "ma")

    arrow(d, (800, 260), (875, 380))
    arrow(d, (800, 640), (875, 520))

    shadow_box(d, (1260, 300, 1540, 600), fill="#F5F3FF", outline="#DDD6FE")
    text(d, (1400, 340), "提示词组装", 23, VIOLET, True, "ma")
    text(d, (1400, 390), "问题 + 知识片段", 17, MUTED, False, "ma")
    text(d, (1400, 430), "约束与安全边界", 17, MUTED, False, "ma")

    arrow(d, (1185, 450), (1255, 450), VIOLET)

    shadow_box(d, (1620, 320, 1730, 580), fill="#ECFEFF", outline="#A5F3FC")
    text(d, (1675, 410), "模型", 22, CYAN, True, "ma")
    text(d, (1675, 450), "生成", 22, CYAN, True, "ma")
    text(d, (1675, 500), "带来源", 15, MUTED, False, "ma")
    arrow(d, (1545, 450), (1615, 450), CYAN)

    text(d, (70, 790), "规则：EMBEDDING_MODEL 未配置、向量库不存在或调用失败时，自动切换到 BM25，保证 RAG 链路始终可用。", 18, MUTED)
    img.save(os.path.join(OUT, "rag.png"))


# ---------------- 业务工作流 ----------------
def workflow():
    W, H = 1800, 520
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    text(d, (70, 40), "核心业务流程", 40, INK, True)

    steps = [
        ("注册 / 登录", "手机号 + 强密码"),
        ("选择方式", "问卷 / 自由对话"),
        ("信息收集", "AI 逐题追问"),
        ("生成报告", "五段式诊断"),
        ("待确认项", "逐条拍板"),
        ("验收版本", "凭证 + diff"),
        ("交付物", "PRD/询价/工期"),
    ]
    start_x, y = 60, 190
    w, h, gap = 220, 150, 24
    colors = ["#EEF1FF", "#EDE9FE", "#E0F2FE", "#CCFBF1", "#FEF3C7", "#FFE4E6", "#DCFCE7"]
    edges = ["#C7D2FE", "#DDD6FE", "#BAE6FD", "#99F6E4", "#FDE68A", "#FECDD3", "#BBF7D0"]
    texts = [INDIGO, VIOLET, CYAN, "#0F766E", "#B45309", "#BE123C", "#15803D"]

    for i, (title, desc) in enumerate(steps):
        x = start_x + i * (w + gap)
        d.rounded_rectangle((x, y, x + w, y + h), 20, fill=colors[i], outline=edges[i], width=2)
        text(d, (x + w / 2, y + 52), f"{i + 1}", 20, texts[i], True, "ma")
        text(d, (x + w / 2, y + 92), title, 24, texts[i], True, "ma")
        text(d, (x + w / 2, y + 128), desc, 15, MUTED, False, "ma")
        if i < len(steps) - 1:
            ax = x + w + 4
            arrow(d, (ax, y + h / 2), (ax + gap - 6, y + h / 2), "#94A3B8", 3)

    text(d, (60, 400), "每一步的结果都可回退：问卷可上一题、对话可放弃、报告可修订并重新验收。", 18, MUTED)
    img.save(os.path.join(OUT, "workflow.png"))


architecture()
rag()
workflow()
print("diagrams saved to", OUT)
