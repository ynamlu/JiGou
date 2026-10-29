"""集中配置：进程环境变量 > backend/.env > backend/local_config.py > 默认值。

两种填 Key 的方式，二选一即可：
1. 写在 backend/.env（推荐，比赛要求 API Key 走环境变量）
2. 写在 backend/local_config.py（就是普通 py 文件，已被 .gitignore 忽略）

注意：config.py 本身会提交到公开仓库，不要把真实 Key 写在这里。
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    """本地开发时读取 backend/.env；也可以用系统环境变量覆盖。"""
    path = os.path.join(BASE_DIR, ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                if key:
                    os.environ.setdefault(key, value.strip().strip('"').strip("'"))
    except OSError:
        pass


_load_dotenv()

try:  # 可选的本地私密配置（不在 git 里）
    import local_config as _local
except Exception:  # noqa: BLE001
    _local = None


def _env(*names, default=""):
    """按顺序取第一个非空值：环境变量 / .env → local_config.py → 默认值。"""
    for name in names:
        value = os.environ.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    if _local is not None:
        for name in names:
            value = getattr(_local, name, None)
            if value is not None and str(value).strip() != "":
                return str(value).strip()
    return default


def _optional_flag(name):
    """返回 True / False；未设置时返回 None（表示"不向接口发送该参数"）。"""
    raw = os.environ.get(name)
    if (raw is None or str(raw).strip() == "") and _local is not None:
        raw = getattr(_local, name, None)
    if raw is None or str(raw).strip() == "":
        return None
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


# ---------- 大语言模型（必填） ----------
# 默认走 OpenAI 兼容网关，可用 LLM_BASE_URL / LLM_MODEL 覆盖。
API_KEY = _env("LLM_API_KEY", "BAILIAN_API_KEY")
BASE_URL = _env(
    "LLM_BASE_URL",
    "BAILIAN_BASE_URL",
    default="https://maas.qianwenaiapi.com/compatible-mode/v1",
)
MODEL_NAME = _env("LLM_MODEL", default="deepseek-v4.1-flash-1017")
TEMPERATURE = float(_env("LLM_TEMPERATURE", default="0"))

# 兼容模式网关对 enable_thinking 的支持并不统一：
# 不设置该变量就不发送；设为 1/0 才会显式传给模型。
ENABLE_THINKING = _optional_flag("LLM_ENABLE_THINKING")

# ---------- 向量模型（可选） ----------
# 留空则不做向量化，运行时自动使用本地关键词检索（BM25），不依赖任何外部服务。
EMBEDDING_MODEL = _env("EMBEDDING_MODEL")
EMBEDDING_API_KEY = _env("EMBEDDING_API_KEY", "LLM_API_KEY", "BAILIAN_API_KEY")
EMBEDDING_BASE_URL = _env(
    "EMBEDDING_BASE_URL", "LLM_BASE_URL", "BAILIAN_BASE_URL", default=BASE_URL
)

# ---------- 应用限制 ----------
MAX_INPUT_CHARS = int(_env("MAX_INPUT_CHARS", default="2000"))

# ---------- 数据库（单文件 SQLite） ----------
DB_PATH = _env("DB_PATH", default=os.path.join(BASE_DIR, "data", "jigou.db"))
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(BASE_DIR, DB_PATH)
DB_PATH = os.path.normpath(DB_PATH)


def missing_key() -> bool:
    return not API_KEY


def llm_extra_body() -> dict:
    if ENABLE_THINKING is None:
        return {}
    return {"enable_thinking": ENABLE_THINKING}
