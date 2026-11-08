# AGENTS.md

本文件面向在此仓库中工作的 AI/工程代理，说明项目结构、启动方式、验证命令和修改边界。  
项目名称：**极构 · 需求诊断顾问**（AI WEB 网页开发挑战赛参赛作品，本地单机版）。

> 原则：先读代码再改；不要提交密钥、数据库、依赖目录和构建产物；不要为了“跑起来”而破坏离线降级能力。

---

## 1. 项目概览

- 产品：面向非技术用户的 AI 需求诊断 Web 应用，覆盖「问卷 / 对话 → 诊断报告 → 待确认事项 → 六维评分 → 交付物 / A/B 方案 → 验收版本 → 导出」。
- 形态：Vue 3 单页应用 + 本地 FastAPI 服务；生产启动时 FastAPI 直接托管 `frontend/dist`，只需要一个进程。
- AI：LangChain Agent + 工具调用（`search_knowledge`）；RAG 优先 Chroma 向量检索，不可用时自动降级到本地 BM25。
- 数据：SQLite 单文件保存账号、登录 Token、验收记录；报告正文/草稿按账号保存在浏览器 `localStorage`。
- 运行：`python run.py` 一条命令完成依赖、前端构建、启动和打开浏览器。

---

## 2. 技术栈

| 层 | 技术 |
| --- | --- |
| 前端框架 | Vue 3.5、Vite 8、`vite-plugin-singlefile` |
| 前端状态 / 路由 | Pinia 4、Vue Router 5（hash 路由 + 登录守卫） |
| 前端渲染 / 导出 | markdown-it、highlight.js、html2canvas |
| 后端 | Python 3.11+、FastAPI 0.141.1、Uvicorn 0.52.4、Pydantic |
| AI 编排 | LangChain 1.4、LangGraph 1.2.11、langchain-openai、OpenAI 兼容网关 |
| 模型 | 默认 `deepseek-v4.1-flash-1017`（可用 `LLM_MODEL` 覆盖） |
| RAG | Chroma 1.5.9（可选）+ 自研 BM25（零外部依赖兜底） |
| 数据库 | SQLite（Python 标准库 `sqlite3`），单文件 |
| 导出 | reportlab（PDF）、html2canvas（长截图） |
| 代码规范 | Ruff，配置见 `pyproject.toml`（`E4/E7/E9/F/I`，行宽 110） |

版本以 `backend/requirements.txt`、`frontend/package.json` 和 `package-lock.json` 为准。Node 要求 **>= 20.19.0**（`engines`）。

---

## 3. 目录结构

```text
JGchuanzhibei/
├── run.py                     # 一键启动器：venv、依赖、前端构建、端口、浏览器
├── pyproject.toml             # Ruff 配置
├── README.md                  # 项目介绍 / 快速开始 / 架构 / 测试说明
├── .gitignore
├── .gitattributes
├── backend/
│   ├── app.py                 # FastAPI 入口、鉴权、业务接口、静态托管、/api/health
│   ├── agent_core.py          # 模型客户端、提示词、Agent、RAG 工具、结构化生成、NDJSON 事件
│   ├── retrieval.py           # 本地 BM25：单字/二元切分、停用词、标题加权、同源去重
│   ├── safety.py              # 输入审查、注入拦截、密钥脱敏
│   ├── config.py              # 环境变量集中读取（进程 env > .env > local_config.py > 默认值）
│   ├── db.py                  # SQLite：users / tokens / acceptances，含轻量迁移
│   ├── pdf_export.py          # Markdown 报告 → PDF
│   ├── build_kb.py            # 可选：配置 EMBEDDING_MODEL 后构建 Chroma 向量库
│   ├── seed_demo.py           # 创建评审测试账号
│   ├── requirements.txt
│   ├── .env.example           # 后端环境变量模板
│   ├── kb/                    # 12 篇原创软件开发知识库（Markdown）
│   ├── data/                  # 运行时 SQLite（jigou.db，已忽略，不要提交）
│   └── .venv/                 # run.py 创建/使用的后端虚拟环境（已忽略）
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js         # /api 代理到 VITE_API_TARGET，singlefile 构建
│   ├── index.html
│   ├── .env.example           # 前端开发代理模板
│   ├── src/
│   │   ├── main.js / App.vue
│   │   ├── api/               # client.js（Token/NDJSON）、index.js
│   │   ├── components/        # 对话、问题卡、评分卡、文档卡等 13 个业务组件
│   │   ├── data/              # cases.js / templates.js（案例与模板库）
│   │   ├── router/            # 路由表 + 登录守卫
│   │   ├── stores/            # user / chat / questionnaire / analysis / archive
│   │   ├── utils/             # markdown / export / toast
│   │   └── views/             # Login / Register / Chat / Doc / TemplateLibrary / History / Profile
│   ├── dist/                  # 构建产物（已忽略；运行时由 FastAPI 托管）
│   └── node_modules/          # 依赖（已忽略）
├── docs/
│   ├── md/                    # Markdown 源文件（5 份）
│   ├── word/                  # Word 版（5 份）
│   ├── pdf/                   # PDF 版（5 份）
│   └── images/                # 作品介绍配图（7 张）
└── demo_video/                # 演示视频 MP4、静态页总览 PPTX
```

根目录 `.venv` 在当前工作区是一个指向 `backend/.venv` 的 junction，仅方便 IDE 选择解释器；实际启动脚本使用的是 `backend/.venv`。不要把它当成第二个环境。

---

## 4. 启动命令

### 4.1 环境要求

- Python **3.11+**
- Node.js **20.19+**（仅构建前端 / 开发热更新需要）
- Windows 示例使用 `backend\.venv\Scripts\python.exe`；macOS/Linux 对应 `backend/.venv/bin/python`

### 4.2 推荐启动

```bash
python run.py
```

首次运行会自动：

1. 创建 `backend/.venv`；
2. 安装 `backend/requirements.txt`；
3. 安装前端依赖并构建 `frontend/dist`；
4. 从 8000 起选择可用端口，启动 FastAPI，并自动打开浏览器。

常用参数：

```bash
python run.py --dev          # Vite 5173 热更新 + FastAPI
python run.py --port 8001    # 指定后端起始端口（被占用会自动顺延）
python run.py --rebuild      # 强制重新构建前端
python run.py --no-browser   # 不自动打开浏览器
```

### 4.3 分开调试

```bash
# 后端（Windows）
backend\.venv\Scripts\python.exe backend\app.py

# 后端（macOS / Linux）
backend/.venv/bin/python backend/app.py
```

```bash
cd frontend
npm install
npm run dev        # Vite 5173，/api 代理到 VITE_API_TARGET（默认 8000）
```

### 4.4 评审测试账号

```text
手机号：13800138000
密码：Demo@123456
```

换机器或清空数据库后可重建：

```bash
cd backend
.venv\Scripts\python.exe seed_demo.py
```

---

## 5. 测试与检查命令

### 重要说明

仓库已提交后端接口自动化测试：`backend/tests/test_api.py`，使用标准库 `unittest` + FastAPI TestClient，共 12 个测试方法。测试库写入系统临时目录，不污染 `backend/data/jigou.db`，也不需要真实模型 Key。  
前端仍未提交 Vitest / Playwright 自动化套件，UI 回归以人工冒烟为准。

在修改后，至少执行以下检查：

```bash
# 1) 后端接口自动化（在 backend 目录执行）
cd backend
.venv\Scripts\python.exe -m unittest discover -s tests -v

# 2) Python 语法/导入级检查
python -m compileall backend run.py

# 3) Ruff（仓库未把 ruff 写入 requirements；未安装时先 pip install ruff）
ruff check backend run.py

# 4) 前端生产构建（会检查 Vue 模板、导入和打包）
cd frontend
npm install
npm run build

# 5) 启动后检查健康接口（无需登录）
curl http://127.0.0.1:8000/api/health
```

`/api/health` 会返回模型名、`key_configured`、知识库统计、数据库文件名、用户数与验收数。  
涉及真实对话 / 报告 / 评分 / 交付物的接口需要有效 `LLM_API_KEY`；没有 Key 时应用仍能启动，AI 接口会返回 503 提示。

### 建议的人工冒烟路径

1. 注册 → 登录 → 首页；
2. 问卷答 3–5 题 → 生成报告；
3. 待确认事项逐条确认 → 六维评分；
4. 交付物 / A/B 方案；
5. 验收 → 版本 diff；
6. 模板库「以此开始诊断」；
7. 我的图纸搜索 / 删除；
8. 320px / 390px / 834px / 1440px 宽度检查横向溢出；
9. 未登录访问受保护路由应跳转登录；伪造 Token 应回登录页。

---

## 6. 环境变量

### 6.1 读取优先级

```text
系统/进程环境变量
  > backend/.env
  > backend/local_config.py
  > 代码默认值
```

- `config.py` 只在环境变量不存在时用 `setdefault` 写入 `.env`，因此系统环境变量优先。
- 不要把真实 Key 写进 `config.py`、README、测试文件或提交信息。
- `backend/.env`、`backend/local_config.py`、`backend/data/`、`backend/vector_store/` 均已被 `.gitignore` 忽略。

### 6.2 后端变量

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `LLM_API_KEY` | 是（AI 接口） | — | 模型网关 Key；无 Key 时页面可开，AI 接口返回 503 |
| `LLM_BASE_URL` | 否 | `https://maas.qianwenaiapi.com/compatible-mode/v1` | OpenAI 兼容网关 |
| `LLM_MODEL` | 否 | `deepseek-v4.1-flash-1017` | 模型型号 |
| `LLM_TEMPERATURE` | 否 | `0` | 采样温度；结构化输出建议保持 0 |
| `LLM_ENABLE_THINKING` | 否 | 不发送 | 设为 `0` / `1` 才显式传给网关 |
| `EMBEDDING_MODEL` | 否 | 空 | 配置后才可能启用 Chroma；留空走 BM25 |
| `EMBEDDING_API_KEY` | 否 | 复用 `LLM_API_KEY` | 向量模型独立网关时填写 |
| `EMBEDDING_BASE_URL` | 否 | 复用 `LLM_BASE_URL` | 向量模型独立网关时填写 |
| `DB_PATH` | 否 | `backend/data/jigou.db` | SQLite 路径；相对路径按 `backend/` 解析 |
| `MAX_INPUT_CHARS` | 否 | `2000` | 单条输入长度上限 |
| `PORT` | 否 | `8000` | **仅直接运行 `backend/app.py` 时生效**；`run.py --port` 优先 |

兼容旧变量：`BAILIAN_API_KEY` / `BAILIAN_BASE_URL` 可作为 `LLM_*` 的别名，但新配置请用 `LLM_*`。

### 6.3 前端变量

| 变量 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- |
| `VITE_API_TARGET` | 否 | `http://127.0.0.1:8000` | Vite 开发代理 `/api` 的目标；`run.py --dev` 会注入实际端口 |

模板：

```text
backend/.env.example
frontend/.env.example
```

---

## 7. 架构与数据流

```text
浏览器 Vue SPA
  ├─ /api/*  ───────────────► FastAPI（app.py）
  │                             ├─ Bearer Token 鉴权
  │                             ├─ Agent / RAG（agent_core.py）
  │                             │    ├─ Chroma（可选）
  │                             │    └─ BM25（retrieval.py，兜底）
  │                             ├─ SQLite（db.py：users/tokens/acceptances）
  │                             └─ reportlab PDF
  ├─ localStorage
  │    ├─ jg_session                 当前账号 + Token
  │    ├─ jg_archive:<手机号>         报告归档
  │    └─ jg_analysis_draft:<账号>    分析草稿
  └─ hash 路由（#/、#/login、#/doc/:id ...）
```

关键点：

- 对话接口使用 **NDJSON 流式** 返回 `token / tool_start / tool_end / thinking / done / error` 事件；前端 `src/api` 统一解析。
- 生产模式不启动 Vite：FastAPI 直接返回 `frontend/dist/index.html`，所以修改前端后必须重新 `npm run build` 或 `python run.py --rebuild`。
- 报告正文不写入 SQLite：SQLite 只存账号、Token 和验收凭证；报告按账号存浏览器，换浏览器/设备历史为空是预期行为。
- 向量库不是启动必需项：`EMBEDDING_MODEL` 为空、向量库不存在或调用失败时，`retrieval.py` 的 BM25 会接管；不要移除这条降级路径。

---

## 8. 修改边界与注意事项

1. **不要提交密钥/本地数据**  
   `.env`、`local_config.py`、`backend/data/`、`backend/vector_store/`、数据库 WAL/SHM 都不要提交，也不要在日志/回复中回显 Key。

2. **不要随意删除或重置数据库**  
   `backend/data/jigou.db` 是运行数据；删除会清空账号、Token、验收记录。需要重建测试账号用 `seed_demo.py`，不要直接改表。

3. **不要手改 `frontend/dist/`**  
   它是构建产物（也被 `.gitignore` 忽略）。改 `src/` 后重新构建；`vite-plugin-singlefile` 会把资源内联成单文件。

4. **不要破坏离线降级**  
   保持 BM25 可用、保持未配置 `EMBEDDING_MODEL` 时正常启动；不要在模块 import 阶段强制连接外部向量服务。

5. **无 Key 场景要保留**  
   页面能打开、`/api/health` 正常、AI 接口给出明确 503；不要把无 Key 当成启动失败。

6. **端口与进程**  
   `run.py` 会从 `--port` 起自动找空端口。不要在同一端口重复启动服务；`--dev` 会额外占用 5173。

7. **文档/视频是交付物**  
   `docs/md/`、`docs/word/`、`docs/pdf/` 下五份文档、`docs/images/` 配图与 `demo_video/` 下 MP4/PPTX 是最终交付材料；除非明确要求，不要重生成或覆盖。PDF 与 Word 必须保持同版：技术文档 27 页、需求分析 25 页、项目介绍 15 页、作品介绍 24 页、测试文档 20 页；改内容后要重新导出 PDF 并同步静态目录页码。

8. **测试现状**  
   后端有 12 个 unittest 接口用例，可运行 `python -m unittest discover -s tests -v`；前端仍以人工冒烟为主。不要把“后端用例通过”说成“全部测试通过”，真实模型链路还需要有效 Key 和单独验证。

9. **中文 UI / Windows 兼容**  
   界面与提示以中文为主；启动脚本已处理 Windows `npm.cmd`、`taskkill`、UTF-8 输出；改动启动逻辑时保留 macOS/Linux 分支。

10. **代码风格**  
    Python 行宽 110，Ruff 规则见 `pyproject.toml`；前端使用 Vue 3 组合式 API、单文件组件、无 UI 框架。

---

## 9. 快速索引

| 需求 | 位置 |
| --- | --- |
| HTTP 路由 / 鉴权 / 静态托管 | `backend/app.py` |
| 提示词 / Agent / 结构化输出 | `backend/agent_core.py` |
| BM25 检索 | `backend/retrieval.py` |
| 环境变量 | `backend/config.py`、`backend/.env.example` |
| SQLite 表结构 / 迁移 | `backend/db.py` |
| PDF 导出 | `backend/pdf_export.py` |
| 可选向量库构建 | `backend/build_kb.py` |
| 测试账号 | `backend/seed_demo.py` |
| 启动器 | `run.py` |
| 前端页面 | `frontend/src/views/` |
| 路由与守卫 | `frontend/src/router/index.js` |
| Pinia 状态 | `frontend/src/stores/` |
| API / NDJSON 解析 | `frontend/src/api/` |
| 构建配置 | `frontend/vite.config.js` |
| 交付文档 | `docs/md/`、`docs/word/`、`docs/pdf/`，配图在 `docs/images/` |
| 成片 / PPTX | `demo_video/` |

---

## 10. 当前已知限制

- 后端有 unittest 接口用例，前端无自动化测试（见第 5 节）；UI 回归仍依赖人工冒烟。
- 报告正文/草稿只在浏览器 `localStorage`，不跨设备同步。
- SQLite 是单机单文件，不适合多实例并发部署。
- 向量检索依赖可选的 embedding 网关；默认 BM25 的召回率低于向量检索，但保证离线可用。
- 模型/网关不可用时 AI 功能不可用；应用本身仍可启动，健康接口可诊断配置状态。
- `docs/` 与 `demo_video/` 是成品材料，重新生成需要额外工具/素材，不属于日常代码构建流程。
