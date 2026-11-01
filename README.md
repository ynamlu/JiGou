# 极构 · 需求诊断顾问

> 2026 第九届传智杯全国大学生数智创新与 AI 应用大赛 · **AI WEB网页开发挑战赛**（团队赛）参赛作品

把一句「我想做个系统」，变成一份能直接拿去开发、询价、立项的**需求诊断报告**。

面向没有技术背景的创业者和小微企业主：他们说不清自己要什么，也判断不了报价是否合理。极构用 AI Agent + RAG，把模糊想法拆成「已经想清楚的 / 还缺的 / 需要拍板的」，并进一步产出 PRD、开发询价清单、成本工期估算和 A/B 方案。

**本地单机版**：手机号注册 / 登录，账号与验收记录存在本机 SQLite，报告按账号隔离；不依赖外部服务器，一条命令启动。

代码仓库：<https://github.com/ynamlu/JiGou>

界面截图、架构图与完整实现说明见 [技术文档 PDF](<docs/技术文档-极构需求诊断顾问.pdf>)。

| 交付物 | 状态 |
| --- | --- |
| 技术文档 | [PDF（21 页）](<docs/技术文档-极构需求诊断顾问.pdf>) + [Markdown](<docs/技术文档-极构需求诊断顾问.md>) |
| 演示视频 | [6:41 / 1080p30 / 35.1 MB](<demo_video/极构-需求诊断顾问-演示视频-成片.mp4>) |
| 静态页总览 | [21 页 PPTX](<demo_video/静态页总览.pptx>) |

## 目录

- [一、赛题对应关系](#一赛题对应关系)
- [二、核心功能](#二核心功能)
- [三、技术架构](#三技术架构)
- [四、目录结构](#四目录结构)
- [五、快速开始](#五快速开始)
- [六、环境变量](#六环境变量)
- [七、常见问题](#七常见问题)
- [八、RAG 设计](#八rag-设计)
- [九、AI 安全与合规](#九ai-安全与合规)
- [十、数据存储](#十数据存储)
- [十一、测试与质量](#十一测试与质量)
- [十二、文档与材料](#十二文档与材料)
- [十三、提交材料清单](#十三提交材料清单)
- [十四、团队信息](#十四团队信息)
- [十五、许可](#十五许可)

---

## 一、赛题对应关系

| 赛道要求 | 本项目做法 |
| --- | --- |
| AI Native Web 应用，AI 是核心而非附属 | 整个产品就是一轮 AI 诊断对话，没有 AI 就没有产品 |
| 现代前端框架 + 组件化 + 状态管理 | Vue 3 + Vite + Pinia + Vue Router，业务组件化拆分、页面懒加载 |
| 大模型高质量集成 | OpenAI 兼容网关统一接入，流式输出、结构化 JSON 约束、失败兜底 |
| AI Agent / 工作流 | LangChain Agent（工具调用 + 会话记忆），问卷→诊断→报告→交付物多阶段工作流 |
| RAG | 12 篇自建软件开发知识库，向量检索 + BM25 关键词检索双通道 |
| 内容输出 | Markdown / PDF / 长截图导出，报告、评分、验收凭证均可分享 |
| AI 安全与可控性 | 输入审查、注入拦截、输出脱敏、提示词安全边界、异常兜底 |
| 工具集成 | Function Calling：`search_knowledge` 知识库检索工具 |

---

## 二、核心功能

1. **对话式需求诊断**：固定结构输出「已具备 / 还缺失 / 待确认」，不教学、只诊断。
2. **AI 逐题问卷**：根据已回答内容动态生成下一题（单选 / 多选 / 文本），信息足够时自动收尾。
3. **需求诊断报告**：项目概述、已具备、还缺失、待确认清单、建议下一步。
4. **待确认事项抽取**：把报告中模糊 / 缺失 / 冲突的点抽成可逐条拍板的清单，支持一键全部确认、进度条与决策记录。
5. **验收与版本管理**：每次验收生成版本号与 diff，凭证落到本地 SQLite；报告本身同时保存在浏览器本地。
6. **六维成熟度评分**：形态、用户、功能、预算、时间、合规，附风险提示。
7. **三份交付物**：需求规格说明书（PRD）、开发询价清单（RFP）、成本与工期估算。
8. **A/B 方案对比**：MVP 版 vs 一步到位版，给出推荐与理由。
9. **报告修订**：按补充意见重写报告，生成新版本并可再次验收。
10. **导出与 Markdown**：Markdown 代码高亮 + 一键复制、PDF 导出、长截图。
11. **账号体系**：手机号注册 / 登录、修改密码、注销账号；报告与验收记录按账号隔离。
12. **模板库与我的图纸**：模板/案例可「以此开始诊断」带入；图纸支持搜索、删除与草稿/验收/评分状态徽章。
13. **交互细节**：对话可停止生成、移动端四项底部导航、统一确认弹窗与组件化交付物/方案卡片。

---

## 三、技术架构

```
┌──────────────────────────── 浏览器 ────────────────────────────┐
│  Vue 3 SPA（Vite 构建，hash 路由，按页懒加载）                   │
│  views: 对话 / 文档 / 模板库 / 历史                              │
│  stores(Pinia): chat · questionnaire · analysis · archive        │
│  组件: ChatBubble · QuestionCard · AssessmentCard · DocCard ...  │
└───────────────┬────────────────────────────────────────────────┘
                │ fetch / NDJSON 流式（/api/chat）
┌───────────────▼────────────────────────────────────────────────┐
│  FastAPI（本地单进程，同时托管前端静态文件）                     │
│  ├─ LangChain Agent：工具调用 + 会话记忆（InMemorySaver）        │
│  ├─ RAG：Chroma 向量检索  ⇄  BM25 关键词检索（自动降级）         │
│  ├─ 结构化输出：问卷 / 评分 / 待确认 / 交付物 / A/B 方案         │
│  ├─ 安全层：输入审查、注入拦截、异常脱敏                          │
│  └─ PDF：reportlab 服务端排版                                    │
│  SQLite：backend/data/jigou.db（账号 / 登录凭证 / 验收记录）      │
└───────────────┬────────────────────────────────────────────────┘
                │ OpenAI 兼容协议（/compatible-mode/v1）
        ┌───────▼────────┐
        │  模型网关       │  deepseek-v4.1-flash-1017
        └────────────────┘
```

### 技术栈

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3.5、Vite 8、Pinia 4、Vue Router 5、markdown-it、html2canvas |
| 后端 | FastAPI、Uvicorn、Pydantic |
| AI | LangChain 1.x、LangGraph（会话记忆）、OpenAI 兼容客户端 |
| RAG | Chroma（可选向量库）+ 自研 BM25 关键词检索（零依赖兜底） |
| 数据 | SQLite（Python 标准库 sqlite3），单文件 |
| 导出 | reportlab（PDF）、html2canvas（长截图） |

---

## 四、目录结构

```
├── run.py                   # ★ 一键启动：装依赖、构建前端、起服务、开浏览器
├── backend/
│   ├── app.py               # FastAPI 入口与全部接口
│   ├── agent_core.py        # Agent、提示词、RAG 工具、结构化生成
│   ├── retrieval.py         # 本地 BM25 检索（向量库不可用时的兜底）
│   ├── safety.py            # 输入审查 / 注入拦截 / 密钥脱敏
│   ├── config.py            # 环境变量集中配置
│   ├── local_config.py      # 可选：本地私密配置（不进 Git）
│   ├── db.py                # SQLite 验收记录
│   ├── pdf_export.py        # Markdown → PDF
│   ├── build_kb.py          # 可选：构建向量库
│   ├── kb/                  # 12 篇软件开发知识库（Markdown）
│   ├── data/jigou.db        # 运行时生成的 SQLite 数据库
│   ├── requirements.txt
│   └── .env.example         # 环境变量模板（复制为 .env 使用）
├── frontend/
│   ├── src/views/           # 页面
│   ├── src/components/      # 业务组件
│   ├── src/stores/          # Pinia 状态
│   ├── src/api/             # 接口封装（含 NDJSON 流式解析）
│   ├── src/utils/           # Markdown、导出
│   └── vite.config.js       # 开发代理 /api → 后端
├── docs/                   # 技术文档 PDF / Markdown
├── demo_video/             # 6:41 成片、静态页总览 PPTX
├── .gitignore
└── README.md
```

---

## 五、快速开始

### 1. 环境要求

- Python 3.11+
- Node.js 20.19+（推荐 22 LTS；仅构建前端需要）

### 2. 配置 API Key（唯一需要手动改的地方）

两种方式，任选一种：

**方式 A：环境变量文件（推荐）**

把 `backend/.env.example` 复制为 `backend/.env`（当前工作区已预置一份，且被 git 忽略），填 Key：

```dotenv
LLM_API_KEY=你的_API_Key
LLM_BASE_URL=https://maas.qianwenaiapi.com/compatible-mode/v1
LLM_MODEL=deepseek-v4.1-flash-1017
```

**方式 B：直接写在本地 py 文件里**

编辑 [backend/local_config.py](backend/local_config.py)（该文件同样被 git 忽略）：

```python
LLM_API_KEY = "你的_API_Key"
```

读取优先级：系统环境变量 > `backend/.env` > `backend/local_config.py` > 默认值。
Key 只来自本机配置，仓库里只有占位模板；公开仓库不会包含真实 Key。

### 3. 启动

```bash
python run.py
```

首次运行会自动完成：

1. 创建 `backend/.venv` 并安装后端依赖；
2. 安装前端依赖并构建 `frontend/dist`；
3. 启动服务并打开 <http://127.0.0.1:8000>。

第一次打开会进入登录页，点「立即注册」用手机号创建账号（密码至少 8 位，包含大写/小写/数字/符号中的三种），注册后自动登录。

之后再启动只需几秒（源码没改就跳过前端构建）。

### 4. 常用参数

| 命令 | 作用 |
| --- | --- |
| `python run.py` | 构建前端 + 启动（推荐） |
| `python run.py --dev` | 同时启动 Vite(5173) 与 FastAPI，前端热更新 |
| `python run.py --port 8001` | 换端口（默认 8000，被占用会自动顺延） |
| `python run.py --rebuild` | 强制重新构建前端 |
| `python run.py --no-browser` | 不自动开浏览器 |

### 5. 单独调试

```bash
cd backend
.venv/Scripts/python app.py        # Windows
# 或 .venv/bin/python app.py       # macOS / Linux
```

前端开发：`cd frontend && npm run dev`（默认代理到 8000）。

### 6. 评审测试账号

本地已创建：

| 项目 | 内容 |
| --- | --- |
| 手机号 | `13800138000` |
| 密码 | `Demo@123456` |

换机器或清空数据库后，可一键重建：

```bash
cd backend
.venv/Scripts/python.exe seed_demo.py    # Windows
# 或 .venv/bin/python seed_demo.py       # macOS / Linux
```

报告归档按浏览器保存，新浏览器首次登录时历史为空属正常现象；可以直接开始一次诊断，或在「模板库」查看案例成品。

---

## 六、环境变量

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `LLM_API_KEY` | ✅ | — | 模型网关 Key，只放在 `.env` |
| `LLM_BASE_URL` | — | `https://maas.qianwenaiapi.com/compatible-mode/v1` | OpenAI 兼容网关 |
| `LLM_MODEL` | — | `deepseek-v4.1-flash-1017` | 模型型号 |
| `LLM_TEMPERATURE` | — | `0` | 采样温度；结构化输出建议保持 0 |
| `LLM_ENABLE_THINKING` | — | 不发送 | 设为 `0` / `1` 才显式传给网关 |
| `EMBEDDING_MODEL` | — | 空 | 留空 = 使用本地 BM25 检索 |
| `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` | — | 复用 LLM 配置 | 向量模型独立网关时填写 |
| `DB_PATH` | — | `backend/data/jigou.db` | SQLite 文件位置；相对路径按 `backend/` 解析 |
| `MAX_INPUT_CHARS` | — | `2000` | 单条输入长度上限 |
| `PORT` | — | `8000` | 仅直接运行 `backend/app.py` 时的端口；`run.py` 由 `--port` 控制 |
| `VITE_API_TARGET` | — | `http://127.0.0.1:8000` | 前端开发代理目标，写在 `frontend/.env` |

环境模板：`backend/.env.example`、`frontend/.env.example`。  
依赖清单：`backend/requirements.txt`、`frontend/package.json` + `package-lock.json`。

---

## 七、常见问题

| 现象 | 原因与处理 |
| --- | --- |
| 对话返回 `401 Invalid API-key` | `LLM_API_KEY` 未填或已失效，改 `backend/.env` 后重启 |
| 一直显示「正在思考…」不出正文 | 网关默认开启思考过程，在 `.env` 里加 `LLM_ENABLE_THINKING=0` 后重启 |
| 8000 端口被占用 | 直接重新运行，脚本会自动顺延；或 `--port 8001` |
| 打开首页 404 | `frontend/dist` 不存在，运行 `python run.py` 会自动构建 |
| 依赖安装慢 / 失败 | 后端默认走清华镜像；前端失败可先手动 `npm install` |
| 登录后突然被退回登录页 | 同一账号在别处登录会替换 token（一个账号同时只有一个登录态），重新登录即可 |
| 忘记密码 | 本地版没有短信找回；可删除 `backend/data/jigou.db` 后重新注册（会清空所有账号与验收记录） |
| PyCharm 提示解释器无效 | 项目只保留一个虚拟环境，解释器选 `backend\.venv\Scripts\python.exe`（macOS/Linux 为 `backend/.venv/bin/python`） |
| 想清空本地数据 | 删除 `backend/data/jigou.db`（验收记录）与浏览器站点数据（报告草稿） |

---

## 八、RAG 设计

- **知识库**：`backend/kb/*.md`，12 篇原创整理，覆盖需求文档、技术选型、开发流程、需求澄清、项目诊断、商业模式、角色权限、报价、工期、资质、风险、非功能需求。
- **主通道**：配置 `EMBEDDING_MODEL` 时，切片（400 字 / 80 重叠）后写入 Chroma，相似度检索 Top-3。
- **兜底通道**：未配置向量模型、或向量服务不可用时，自动切换 `retrieval.py` 的 BM25 检索（中文单字 + 二元切分、停用词过滤、标题加权、同源去重）。
- **可观测**：`GET /api/health` 返回当前检索模式、切片数与数据库文件名。

设计取舍：本地演示环境网络不可控，RAG 不能成为单点故障。关键词检索召回略低，但保证「检索 → 增强 → 生成」链路永远可演示。

---

## 九、AI 安全与合规

- **输入审查**（`backend/safety.py`）：长度限制；危险物品、入侵窃取、未成年人色情、代写论文等请求直接拒答并引导回正常场景。
- **提示词注入防护**：识别「忽略之前的指令 / 输出系统提示词 / 开发者模式」等套取行为。
- **提示词边界**：`SYSTEM_PROMPT` 明确不透露系统提示词、不臆造政策与价格、涉及用户数据时提醒遵守《个人信息保护法》。
- **输出脱敏**：异常信息经 `mask_secrets()` 处理，API Key 不会通过报错回显。
- **失败兜底**：模型超时 / 网关报错时返回友好提示；结构化输出解析失败时回落到默认问题。

---

## 十、数据存储

只有一个 SQLite 文件：`backend/data/jigou.db`（首次启动自动创建），共三张表：

| 表 | 字段 | 存什么 |
| --- | --- | --- |
| `users` | id、username、password_hash、salt、created_at | 账号。手机号唯一；密码用 PBKDF2-SHA256（10 万次迭代 + 随机盐）哈希，不存明文 |
| `tokens` | token、username、created_at | 登录凭证。登录时生成 64 位随机 token，一个账号同时只保留一个有效 token |
| `acceptances` | id、username、doc_hash、content、confirm_items、resolutions、project_key、version、diff、accepted_at | 报告验收凭证：报告原文、待确认项与决策、SHA-256 指纹、版本号、与上一版的 diff |

**不在数据库里的**：报告正文、评分、交付物、A/B 方案、对话草稿。这些存在浏览器 `localStorage`，
并按账号隔离（键名 `jg_archive:<手机号>`），所以同一个浏览器切换账号不会看到彼此的报告。

- 备份：复制 `backend/data/jigou.db`；
- 清空：删除该文件（账号与验收记录都会重置）；
- 注销账号：会级联删除该用户的 tokens 与 acceptances。

---

## 十一、测试与质量

- **后端静态检查**：`ruff check backend run.py`、`python -m compileall backend run.py` 均通过；
- **前端构建**：`npm run build` 通过，产物单文件约 766 KB；
- **接口测试**：TestClient 覆盖注册、登录、401 鉴权、验收、改密、注销与版本 diff；
- **数据隔离**：两个账号对同一项目验收互不影响，删号后另一账号数据保留；
- **浏览器测试**：Playwright 在 320 / 390 / 834 / 1440 四档宽度跑登录、问卷、对话、报告、模板库、我的图纸，无横向滚动、无控制台报错；
- **异常路径**：伪造 Token 自动跳登录、弱密码/重复注册/错密码返回对应错误码、未配置 Key 有明确提示。

## 十二、文档与材料

| 材料 | 文件 | 说明 |
| --- | --- | --- |
| 技术文档（PDF） | [docs/技术文档-极构需求诊断顾问.pdf](<docs/技术文档-极构需求诊断顾问.pdf>) | 21 页，含架构、AI 方案、测试、创新点 |
| 技术文档（Markdown） | [docs/技术文档-极构需求诊断顾问.md](<docs/技术文档-极构需求诊断顾问.md>) | 可编辑版本，章节与 PDF 对应 |
| 演示视频（MP4） | [demo_video/极构-需求诊断顾问-演示视频-成片.mp4](<demo_video/极构-需求诊断顾问-演示视频-成片.mp4>) | 6:41，1920×1080 / 30fps，完整录屏（PyCharm 起）+ 男声 + 烧录字幕 |
| 静态页总览（PPTX） | [demo_video/静态页总览.pptx](<demo_video/静态页总览.pptx>) | 21 张静态页的 16:9 总览 |

---

## 十三、提交材料清单（对照省赛要求）

| 材料 | 要求 | 本仓库状态 |
| --- | --- | --- |
| 代码仓库 | GitHub / Gitee 公开，结构清晰、有注释 | ✅ 已推送：<https://github.com/ynamlu/JiGou> |
| README | 项目介绍、技术架构、安装运行、团队信息 | ✅ 本文（含团队信息） |
| 环境配置 | 环境变量模板 + 依赖清单 | ✅ `backend/.env.example`、`frontend/.env.example` + `requirements.txt` + `package.json` / `package-lock.json` |
| Git 记录 | 保留真实提交历史 | ✅ 已建立提交历史，持续更新 |
| 演示视频 | 5–8 分钟、1080p、MP4、普通话 | ✅ 已完成（6:41，1080p30，35.1MB，完整录屏 + 男声） |
| 技术文档 | PDF、≤30 页，含架构 / AI 方案 / 创新点；附 Markdown 可编辑版 | ✅ 已完成（PDF 21 页 + Markdown） |
| 在线演示 | 公网可访问（可选加分） | 可选，本地演示不影响评审 |

> 提交前确认 `git status` 中没有 `.env`、`backend/local_config.py`、`backend/data/`、`node_modules/`、`frontend/dist/`；API Key 一旦泄露请立即在平台重置。

---

## 十四、团队信息

| 项目 | 内容 |
| --- | --- |
| 学校 | 沧州交通学院 |
| 队伍名称 | 极构团队 |
| 参赛组别 | B 组 |
| 队员 | 贾宇航、吴思彤、马翌焜 |
| 指导教师 | 王玉潇 |
| 作品名称 | 极构 · 需求诊断顾问 |

---

## 十五、许可

本项目为参赛原创作品，仅供学习交流与赛事评审使用。
