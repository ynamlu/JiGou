"""AI 安全与可控性：输入审查 + 敏感信息脱敏。

对应赛道评分项「AI 安全与可控性」：
- 输入侧：长度限制、违法/危险请求拦截、提示词注入识别；
- 输出侧：异常信息里的 Key 一律打码，避免通过报错泄露密钥；
- 模型侧：agent_core.SYSTEM_PROMPT 中写明的安全边界。
"""

import re

from config import MAX_INPUT_CHARS

# 命中即拒答的明确违规请求
_BLOCK_RULES = [
    (
        re.compile(
            r"(制作|制造|合成|提炼|自制|做|搞|弄).{0,10}"
            r"(炸弹|炸药|爆炸物|枪支|毒品|冰毒|神经毒剂)(?!检测|识别|防护|预警|排查)"
        ),
        "这个问题涉及危险物品的制作方法，我不能提供。如果你在做安全相关的产品，可以告诉我业务场景，我帮你梳理需求。",
    ),
    (
        re.compile(r"(入侵|黑进|破解|盗取|窃取|拖库).{0,10}(服务器|网站|账号|数据库|密码|系统|APP|应用)"),
        "我不能提供入侵或窃取他人系统、数据的方法。如果你的项目需要安全防护能力，可以说明防护目标，我帮你判断需要哪些安全需求。",
    ),
    (
        re.compile(r"(儿童|未成年|幼女|幼童).{0,6}(色情|裸照|性)"),
        "我不能提供涉及未成年人的色情内容。",
    ),
    (
        re.compile(r"(代写|帮写).{0,6}(论文|毕业设计).{0,6}(包过|代答辩)"),
        "我不能提供代写论文或代做毕业设计并承诺通过的服务。",
    ),
]

# 提示词注入 / 越权套取系统设定
_INJECTION = re.compile(
    r"(忽略|无视|忘记|绕过).{0,10}(之前|以上|上面|所有|系统).{0,6}(指令|提示词|设定|规则)"
    r"|(输出|告诉我|打印|复述|展示).{0,8}(系统提示词|system\s*prompt|开发者指令)"
    r"|开发者模式|\bDAN\b|jailbreak",
    re.IGNORECASE,
)

_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{8,}", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),
]


def mask_secrets(text: str) -> str:
    """把异常信息、日志里可能出现的密钥替换成 ***。"""
    result = str(text or "")
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub("***", result)
    return result


def check_input(text: str) -> tuple[bool, str]:
    """返回 (是否放行, 拒答说明)。"""
    content = (text or "").strip()

    if len(content) > MAX_INPUT_CHARS:
        return False, f"内容太长了（最多 {MAX_INPUT_CHARS} 字），请精简后再发送。"

    for pattern, message in _BLOCK_RULES:
        if pattern.search(content):
            return False, message

    if _INJECTION.search(content):
        return (
            False,
            "我不能执行修改系统设定的指令。你可以直接描述想做的项目，我会按正常流程帮你做需求诊断。",
        )

    return True, ""
