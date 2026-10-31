# -*- coding: utf-8 -*-
"""演示视频分镜脚本数据（严格对应 docs/演示视频脚本.md 的口播稿）。

cues     = 字幕句，每个元素是一条字幕（也决定断句与换气）
shots    = 画面，cues 区间用 [起, 止] 表示：
           "cues": (0, 3) 表示承接第 0~3 条字幕
"""

VOICE = "zh-CN-YunxiNeural"
RATE = "+4%"
BLOCK_GAP = 0.30  # 分镜之间的停顿（秒）

BLOCKS = [
    {
        "id": "B01", "tag": "开场", "chapter": "01 开场",
        "cues": [
            "大家好，我们是极构团队。",
            "参赛作品是「极构 · 需求诊断顾问」，",
            "参加 AI WEB 网页开发挑战赛。",
        ],
        "shots": [{"cues": (0, 2), "type": "title"}],
    },
    {
        "id": "B02", "tag": "缘起", "chapter": "01 开场",
        "cues": [
            "我们解决的问题很具体。",
            "很多创业者和个体店主想做一个系统，",
            "却说不清要做什么、大概多少钱、",
            "还缺哪些准备。",
            "极构用 AI 把一句「我想做个系统」，",
            "变成一份可以直接拿去开发、",
            "询价、立项的需求报告。",
        ],
        "shots": [
            {"cues": (0, 4), "type": "shot", "image": "screenshots/landing-desktop.jpg",
             "caption": "首页 · 一句话开始一次需求诊断"},
            {"cues": (5, 6), "type": "shot", "image": "screenshots/report-desktop.jpg",
             "caption": "输出物 · 可直接拿去开发与询价的需求报告"},
        ],
    },
    {
        "id": "B03", "tag": "功能地图", "chapter": "02 功能",
        "cues": [
            "产品有六块核心能力。",
            "第一，AI 问卷和自由对话。",
            "问卷会一题一题追问，",
            "自由对话适合已经有想法的人。",
            "第二，五段式诊断报告。",
            "项目概述、已具备、还缺失、",
            "待确认清单、建议下一步。",
        ],
        "shots": [
            {"cues": (0, 3), "type": "cards6", "highlight": [0, 1]},
            {"cues": (4, 6), "type": "cards6", "highlight": [1]},
        ],
    },
    {
        "id": "B04", "tag": "功能地图", "chapter": "02 功能",
        "cues": [
            "第三，六维成熟度评分和风险提示，",
            "一眼看出需求还想清了没。",
            "第四，三份交付物：",
            "PRD、开发询价清单、成本工期，",
            "外加 MVP 与完整版的 A/B 方案。",
        ],
        "shots": [
            {"cues": (0, 1), "type": "cards6", "highlight": [2]},
            {"cues": (2, 4), "type": "cards6", "highlight": [3]},
        ],
    },
    {
        "id": "B05", "tag": "功能地图", "chapter": "02 功能",
        "cues": [
            "第五，验收版本。",
            "每次确认生成版本号、指纹和 diff，",
            "留下书面凭证。",
            "第六，模板库、我的图纸和多格式导出，",
            "报告可以导出 Markdown、PDF 和长截图。",
            "这就是从一句想法，到可执行材料的完整闭环。",
        ],
        "shots": [
            {"cues": (0, 2), "type": "cards6", "highlight": [4]},
            {"cues": (3, 4), "type": "cards6", "highlight": [5]},
            {"cues": (5, 5), "type": "cards6", "highlight": [0, 1, 2, 3, 4, 5]},
        ],
    },
    {
        "id": "B06", "tag": "技术栈", "chapter": "03 技术栈",
        "cues": [
            "技术栈分三层。",
            "前端是 Vue 3.5 + Vite 8，",
            "Pinia 管理账号、对话和报告状态，",
            "Vue Router 做登录守卫；",
            "Markdown 用 markdown-it 渲染，",
            "highlight.js 做代码高亮。",
        ],
        "shots": [{"cues": (0, 5), "type": "tech3", "highlight": 0}],
    },
    {
        "id": "B07", "tag": "技术栈", "chapter": "03 技术栈",
        "cues": [
            "后端是 FastAPI + Uvicorn，",
            "AI 编排用 LangChain 1.4 和 LangGraph 1.2，",
            "模型通过 OpenAI 兼容网关接入",
            "deepseek-v4.1-flash-1017。",
        ],
        "shots": [{"cues": (0, 3), "type": "tech3", "highlight": 1}],
    },
    {
        "id": "B08", "tag": "RAG 双通道", "chapter": "03 技术栈",
        "cues": [
            "RAG 是双通道。",
            "配置了向量模型，就走 Chroma 相似度检索，",
            "否则自动降级到自研 BM25；",
            "知识库是 12 篇原创文档、32 个片段。",
        ],
        "shots": [{"cues": (0, 3), "type": "shot", "image": "diagrams/rag.png",
                   "caption": "RAG · Chroma 向量检索 ⇄ BM25 关键词检索（自动降级）"}],
    },
    {
        "id": "B09", "tag": "数据层", "chapter": "03 技术栈",
        "cues": [
            "数据层只用单文件 SQLite，",
            "密码用 PBKDF2-SHA256 加随机盐；",
            "PDF 用 reportlab 排版，",
            "长截图用 html2canvas。",
            "整套系统不依赖数据库服务或容器，",
            "python run.py 一条命令启动。",
        ],
        "shots": [
            {"cues": (0, 3), "type": "tech3", "highlight": 2},
            {"cues": (4, 5), "type": "shot", "image": "diagrams/architecture.png",
             "caption": "总体架构 · 单进程 FastAPI + 单文件 SQLite"},
        ],
    },
    {
        "id": "B10", "tag": "登录", "chapter": "04 操作演示",
        "cues": [
            "系统是本地运行的完整 Web 应用。",
            "首次使用先注册，",
            "手机号加强度校验的密码。",
        ],
        "shots": [{"cues": (0, 2), "type": "shot", "image": "screenshots/login-desktop.jpg",
                   "caption": "登录 · 手机号 + 强度校验密码"}],
    },
    {
        "id": "B11", "tag": "首页", "chapter": "04 操作演示",
        "cues": [
            "登录后进入首页。",
            "这里给出两种诊断方式：",
            "问卷适合还说不清的人，",
            "自由对话适合已经有想法的人。",
        ],
        "shots": [{"cues": (0, 3), "type": "shot", "image": "screenshots/landing-desktop.jpg",
                   "caption": "首页 · 问卷 / 自由对话，两种方式随时可换"}],
    },
    {
        "id": "B12", "tag": "账号隔离", "chapter": "04 操作演示",
        "cues": [
            "右上角是当前账号，",
            "报告和验收记录按账号隔离，",
            "换账号不会互相看到。",
        ],
        "shots": [{"cues": (0, 2), "type": "shot", "image": "screenshots/profile-desktop.jpg",
                   "caption": "账号体系 · 报告与验收记录按账号隔离"}],
    },
    {
        "id": "B13", "tag": "AI 问卷", "chapter": "04 操作演示",
        "cues": [
            "问卷不是固定题库，",
            "而是 AI 根据上一题动态生成下一题。",
            "比如我先选微信小程序，",
            "再说给门店顾客用，",
            "它会继续追问核心功能和预算。",
            "每道题都能补充说明，",
            "也能回上一题修改；",
            "信息够了，它会主动收尾，",
            "而不是没完没了地问。",
        ],
        "shots": [{"cues": (0, 8), "type": "shot", "image": "screenshots/chat-desktop.jpg",
                   "caption": "AI 问卷 · 逐题追问，也可自由描述"}],
    },
    {
        "id": "B14", "tag": "Agent + RAG", "chapter": "04 操作演示",
        "cues": [
            "自由对话走的是 Agent。",
            "先检索知识库，",
            "再按已具备、还缺失、待确认三段回答。",
            "前端通过 NDJSON 接收事件，",
            "所以能看到检索状态和逐字输出；",
            "生成过程中可以随时停止，",
            "已输出内容会保留。",
            "检索有两条通道：",
            "Chroma 向量检索和 BM25 关键词检索，",
            "向量服务不可用时自动降级，",
            "保证离线也能演示。",
        ],
        "shots": [
            {"cues": (0, 6), "type": "shot", "image": "screenshots/doc-chat.jpg",
             "caption": "自由对话 · 检索状态 + 流式逐字输出"},
            {"cues": (7, 10), "type": "shot", "image": "diagrams/rag.png",
             "caption": "双通道降级 · 向量不可用自动切 BM25"},
        ],
    },
    {
        "id": "B15", "tag": "诊断报告", "chapter": "05 报告与交付物",
        "cues": [
            "生成后会得到五段式诊断报告：",
            "项目概述、已具备、还缺失、",
            "待确认清单、建议下一步。",
            "同时给出六维成熟度评分和风险提示，",
            "再把需要拍板的事项逐条列出来。",
        ],
        "shots": [
            {"cues": (0, 2), "type": "shot", "image": "screenshots/report-desktop.jpg",
             "caption": "五段式报告 · 概述 / 已具备 / 还缺失 / 待确认 / 下一步"},
            {"cues": (3, 4), "type": "score"},
        ],
    },
    {
        "id": "B16", "tag": "交付物", "chapter": "05 报告与交付物",
        "cues": [
            "继续可以生成 PRD、",
            "开发询价清单、成本工期估算，",
            "以及 MVP 和完整版两套 A/B 方案。",
            "这些不是聊天记录，",
            "而是可以直接发给开发方、",
            "用来比价和验收的材料。",
        ],
        "shots": [{"cues": (0, 5), "type": "deliverables"}],
    },
    {
        "id": "B17", "tag": "验收与版本", "chapter": "05 报告与交付物",
        "cues": [
            "待确认事项支持逐条选择",
            "已确认、不涉及、补充说明，",
            "也可以一键全部确认，",
            "进度条会提示还剩几项。",
            "全部决定后才能验收。",
            "系统会计算报告指纹、生成版本号，",
            "以及与上一版的差异。",
            "以后改需求，能清楚看到每一版确认了什么，",
            "避免口头扯皮。",
        ],
        "shots": [
            {"cues": (0, 4), "type": "shot", "image": "screenshots/doc-report.jpg",
             "caption": "待确认清单 · 逐条拍板，已确认 2/2"},
            {"cues": (5, 8), "type": "version"},
        ],
    },
    {
        "id": "B18", "tag": "模板库", "chapter": "06 模板与导出",
        "cues": [
            "模板库内置多行业模板和案例，",
            "可以一键把模板摘要带入首页，",
            "直接开始诊断。",
        ],
        "shots": [{"cues": (0, 2), "type": "shot", "image": "screenshots/templates-desktop.jpg",
                   "caption": "模板库 · 多行业模板与案例，一键带入诊断"}],
    },
    {
        "id": "B19", "tag": "我的图纸", "chapter": "06 模板与导出",
        "cues": [
            "我的图纸支持搜索、删除和状态徽章，",
            "草稿、已验收、成熟度、交付物一眼可见。",
            "报告支持 Markdown、PDF 和长截图导出，",
            "手机浏览器也能直接查看。",
        ],
        "shots": [
            {"cues": (0, 1), "type": "shot", "image": "screenshots/history-desktop.jpg",
             "caption": "我的图纸 · 搜索 / 删除 / 状态徽章"},
            {"cues": (2, 3), "type": "shot", "image": "screenshots/doc-mobile.jpg",
             "caption": "多格式导出 · Markdown / PDF / 长截图，移动端可看"},
        ],
    },
    {
        "id": "B20", "tag": "收尾", "chapter": "07 收尾",
        "cues": [
            "以上就是极构需求诊断顾问。",
            "它让不懂技术的人，",
            "也能先把需求想清楚，再去找开发。",
            "谢谢大家。",
        ],
        "shots": [{"cues": (0, 3), "type": "end"}],
    },
]

# 六张功能卡
CARDS = [
    ("01", "AI 问卷 / 自由对话", "问卷逐题追问，也能自由描述想法"),
    ("02", "五段式诊断报告", "概述 · 已具备 · 还缺失 · 待确认 · 下一步"),
    ("03", "六维成熟度评分", "形态 / 用户 / 功能 / 预算 / 时间 / 合规 + 风险"),
    ("04", "三份交付物 + A/B 方案", "PRD · 询价清单 · 成本工期，MVP 与完整版"),
    ("05", "验收版本 + diff + 凭证", "版本号、报告指纹、与上一版的差异留痕"),
    ("06", "模板库 / 我的图纸 / 导出", "多行业模板，Markdown / PDF / 长截图"),
]

TECH_COLUMNS = [
    ("前端", "Vue 3.5 + Vite 8", [
        "Vue 3.5 + Vite 8",
        "Pinia 4 + Vue Router 5",
        "markdown-it + highlight.js",
        "原生 CSS 响应式",
    ]),
    ("后端与 AI", "FastAPI + LangChain", [
        "FastAPI + Uvicorn",
        "LangChain 1.4 + LangGraph 1.2",
        "OpenAI 兼容网关 · deepseek-v4.1-flash-1017",
        "RAG：Chroma + BM25 双通道",
    ]),
    ("数据与输出", "SQLite + reportlab", [
        "SQLite 单文件",
        "reportlab（PDF）",
        "html2canvas（长截图）",
        "PBKDF2-SHA256 密码哈希",
    ]),
]

SCORES = [
    ("形态", 90), ("用户", 78), ("功能", 72),
    ("预算", 60), ("时间", 55), ("合规", 68),
]

DELIVERABLES = [
    ("PRD", "需求规格说明书", "功能清单、页面流程、数据字段"),
    ("RFP", "开发询价清单", "按模块拆项，方便逐项比价"),
    ("估算", "成本与工期", "分阶段报价与排期参考"),
]
