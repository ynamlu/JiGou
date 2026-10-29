"""极构 · 本地后端（FastAPI）。

职责：
- 托管 frontend/dist，提供 /api/* 接口；
- 账号体系：注册 / 登录 / 改密 / 注销，接口用 Bearer token 鉴权；
- AI 能力：对话、问卷、报告、评分、交付物、A/B 方案、修订；
- 数据：SQLite 单文件（默认 backend/data/jigou.db）。

单独调试：python app.py
推荐启动：在项目根目录 python run.py
"""

import difflib
import hashlib
import json
import os
import re
import sys

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent_core import (
    OPENING_MESSAGE,
    STORE_DIR,
    build_agent,
    extract_assessment,
    extract_confirm_items,
    generate_ab_plan,
    generate_deliverables,
    generate_document,
    next_question,
    revise_document,
    stream_events,
)
from config import DB_PATH, MODEL_NAME, missing_key
from retrieval import stats as kb_stats

import db
import pdf_export
import safety

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")

if not os.path.isdir(STORE_DIR) or not os.path.exists(
    os.path.join(STORE_DIR, "chroma.sqlite3")
):
    print("[kb] 未发现向量库，本次运行使用本地关键词检索（BM25），无需外部 embedding 服务")

if missing_key():
    print("[config] 未配置 LLM_API_KEY，对话类接口会提示先填 Key；请在 backend/.env 中填写")

app = FastAPI(title="极构 · 需求诊断顾问")

_AGENT = None


def get_agent():
    """首次对话时才初始化 Agent：没配 Key 也能正常打开页面。"""
    global _AGENT
    if _AGENT is None:
        _AGENT = build_agent()
    return _AGENT


def require_llm_key():
    """没配模型 Key 时直接 503，避免把网关的鉴权错误伪装成业务错误。"""
    if missing_key():
        raise HTTPException(
            status_code=503,
            detail="还没配置模型 Key（LLM_API_KEY），请在 backend/.env 中填写后重启",
        )


try:
    db.init_db()
except Exception as exc:  # noqa: BLE001
    print(f"[db] 无法打开数据库文件：{safety.mask_secrets(exc)}")
    print(f"[db] 路径：{DB_PATH}，请确认目录可写，或在 backend/.env 中用 DB_PATH 指定其它位置")
    raise
else:
    print(f"[db] 数据库文件：{DB_PATH}")

SESSION_QA: dict[str, list[dict]] = {}


def is_phone(username: str) -> bool:
    return bool(re.fullmatch(r"1[3-9]\d{9}", username))


def is_strong_password(password: str) -> bool:
    if len(password) < 8:
        return False
    kinds = 0
    if re.search(r"[a-z]", password):
        kinds += 1
    if re.search(r"[A-Z]", password):
        kinds += 1
    if re.search(r"\d", password):
        kinds += 1
    if re.search(r"[^A-Za-z0-9]", password):
        kinds += 1
    return kinds >= 3


def get_current_user(authorization: str | None = Header(None)) -> str:
    """从 Authorization: Bearer <token> 解析当前账号；失败统一返回 401。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[len("Bearer ") :].strip()
    username = db.get_username_by_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return username


# ---------- 请求模型 ----------
class ChatRequest(BaseModel):
    message: str
    session_id: str = "web-default"


class CheckAccountRequest(BaseModel):
    username: str


class AuthRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    password: str


class DocRequest(BaseModel):
    session_id: str = "web-default"
    answers: list[dict] = []


class QuestionnaireRequest(BaseModel):
    session_id: str = "web-default"
    answers: list[dict] = []
    force_continue: bool = False


class AcceptRequest(BaseModel):
    document: str
    confirm_items: list[dict] = []
    resolutions: list[dict] = []
    project_key: str = ""


class DeliverablesRequest(BaseModel):
    document: str


class AbPlanRequest(BaseModel):
    document: str


class RevisionRequest(BaseModel):
    document: str
    instructions: str = ""


class AssessmentRequest(BaseModel):
    document: str


class PdfRequest(BaseModel):
    document: str


def acceptance_hash(document: str, resolutions: list[dict]) -> str:
    payload = json.dumps(
        {"document": document, "resolutions": resolutions},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def doc_diff(old: str, new: str) -> str:
    if not old:
        return ""
    a = (old or "").splitlines()
    b = (new or "").splitlines()
    lines = list(
        difflib.unified_diff(a, b, fromfile="上一版本", tofile="当前版本", lineterm="")
    )
    return "\n".join(lines)


def _error_stream(message: str) -> StreamingResponse:
    """把校验类错误也包装成流式事件，前端可以用同一套逻辑展示。"""
    def gen():
        yield json.dumps({"type": "error", "content": message}, ensure_ascii=False) + "\n"

    return StreamingResponse(
        gen(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------- AI 内容接口（需要登录） ----------
@app.post("/api/chat")
def chat(req: ChatRequest, username: str = Depends(get_current_user)):
    """流式对话：安全检查 → 拼接问卷上下文 → 以 NDJSON 推送 Agent 事件。"""
    if missing_key():
        return _error_stream(
            "还没配置模型 Key（LLM_API_KEY），请先在 backend/.env 中填写，然后重启服务。"
        )

    ok, reason = safety.check_input(req.message)
    if not ok:
        return _error_stream(reason)

    message = req.message
    qa = SESSION_QA.get(req.session_id)
    if qa:
        ctx = "（此前问卷已收集以下信息，供你参考）\n" + "\n".join(
            f"- {a.get('question', '')} → {a.get('answer', '')}" for a in qa
        ) + "\n\n用户现在补充说：\n"
        message = ctx + req.message

    def gen():
        try:
            for ev in stream_events(get_agent(), message, req.session_id):
                yield json.dumps(ev, ensure_ascii=False) + "\n"
        except Exception as exc:  # noqa: BLE001
            yield json.dumps(
                {"type": "error", "content": f"服务端出错：{safety.mask_secrets(exc)}"},
                ensure_ascii=False,
            ) + "\n"

    return StreamingResponse(
        gen(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/opening")
def opening():
    """开场白，公开接口，避免登录页/首屏依赖鉴权。"""
    return {"content": OPENING_MESSAGE}


# ---------- 账号 ----------
@app.post("/api/check_account")
def check_account(req: CheckAccountRequest):
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="请输入手机号")
    if not is_phone(username):
        raise HTTPException(status_code=400, detail="账号需为 11 位手机号")
    try:
        return {"exists": db.user_exists(username)}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"数据库查询失败：{safety.mask_secrets(exc)}"
        )


@app.post("/api/register")
def register(req: AuthRequest):
    username = req.username.strip()
    password = req.password or ""
    if not username:
        raise HTTPException(status_code=400, detail="请输入手机号")
    if not is_phone(username):
        raise HTTPException(status_code=400, detail="账号需为 11 位手机号")
    if not is_strong_password(password):
        raise HTTPException(
            status_code=400,
            detail="密码至少 8 位，且需包含大写字母、小写字母、数字、特殊字符中的至少三种",
        )
    try:
        if db.user_exists(username):
            raise HTTPException(status_code=409, detail="该手机号已注册，请直接登录")
        db.create_user(username, password)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"注册失败：{safety.mask_secrets(exc)}"
        )
    return {"ok": True, "username": username}


@app.post("/api/login")
def login(req: AuthRequest):
    username = req.username.strip()
    password = req.password or ""
    if not username or not password:
        raise HTTPException(status_code=400, detail="请输入手机号和密码")
    if not is_phone(username):
        raise HTTPException(status_code=400, detail="账号需为 11 位手机号")
    try:
        if not db.user_exists(username):
            raise HTTPException(status_code=401, detail="该账号尚未注册，请先注册")
        if not db.check_login(username, password):
            raise HTTPException(status_code=401, detail="手机号或密码错误")
        token = db.create_token(username)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"登录失败：{safety.mask_secrets(exc)}"
        )
    return {"ok": True, "username": username, "token": token}


@app.post("/api/logout")
def logout(authorization: str | None = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        db.delete_token(authorization[len("Bearer ") :].strip())
    return {"ok": True}


@app.get("/api/me")
def me(username: str = Depends(get_current_user)):
    row = db.get_user(username)
    return {
        "username": username,
        "created_at": (row["created_at"] if row else ""),
    }


@app.post("/api/change_password")
def change_password(
    req: ChangePasswordRequest, username: str = Depends(get_current_user)
):
    old_password = req.old_password or ""
    new_password = req.new_password or ""
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="请输入旧密码和新密码")
    if not is_strong_password(new_password):
        raise HTTPException(
            status_code=400,
            detail="新密码至少 8 位，且需包含大写字母、小写字母、数字、特殊字符中的至少三种",
        )
    try:
        if not db.check_login(username, old_password):
            raise HTTPException(status_code=400, detail="旧密码不正确")
        db.set_password(username, new_password)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"修改密码失败：{safety.mask_secrets(exc)}"
        )
    return {"ok": True}


@app.post("/api/delete_account")
def delete_account(
    req: DeleteAccountRequest, username: str = Depends(get_current_user)
):
    if not req.password or not db.check_login(username, req.password):
        raise HTTPException(status_code=400, detail="密码错误，无法注销")
    try:
        db.delete_account(username)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"注销失败：{safety.mask_secrets(exc)}"
        )
    return {"ok": True}


@app.post("/api/generate_doc")
def generate_doc(req: DocRequest, username: str = Depends(get_current_user), _key: None = Depends(require_llm_key)):
    """生成需求诊断报告，并同步产出待确认事项与成熟度评分。"""
    if req.answers:
        qa = [
            {
                "question": (a.get("question") or "").strip(),
                "answer": (a.get("answer") or "").strip(),
            }
            for a in req.answers
            if (a.get("question") or "").strip() or (a.get("answer") or "").strip()
        ]
        SESSION_QA[req.session_id] = qa
    extra = SESSION_QA.get(req.session_id)

    try:
        document = generate_document(get_agent(), req.session_id, extra_answers=extra)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"文档生成失败：{safety.mask_secrets(exc)}"
        )

    SESSION_QA.pop(req.session_id, None)
    return {
        "document": document,
        "confirm_items": extract_confirm_items(document),
        "assessment": extract_assessment(document),
    }


@app.post("/api/accept")
def accept(req: AcceptRequest, username: str = Depends(get_current_user)):
    """保存验收凭证：同一账号、同一 project_key 下版本号递增，并记录与上一版的 diff。"""
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空，无法验收")
    resolutions = [
        {
            "title": (r.get("title") or "").strip(),
            "detail": (r.get("detail") or "").strip(),
            "kind": (r.get("kind") or "").strip(),
            "decision": (r.get("decision") or "").strip(),
            "note": (r.get("note") or "").strip(),
        }
        for r in req.resolutions
        if isinstance(r, dict)
    ]
    doc_hash = acceptance_hash(req.document, resolutions)
    project_key = (req.project_key or "").strip()
    latest = db.get_latest_acceptance(username, project_key)
    version = (int(latest["version"]) + 1) if latest else 1
    diff = doc_diff(latest["content"], req.document) if latest else ""
    try:
        acceptance_id, accepted_at = db.save_acceptance(
            username,
            doc_hash,
            req.document,
            json.dumps(req.confirm_items, ensure_ascii=False),
            json.dumps(resolutions, ensure_ascii=False),
            project_key=project_key,
            version=version,
            diff=diff,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"保存验收记录失败：{safety.mask_secrets(exc)}"
        )
    return {
        "id": acceptance_id,
        "username": username,
        "doc_hash": doc_hash,
        "accepted_at": accepted_at,
        "resolutions": resolutions,
        "project_key": project_key,
        "version": version,
        "diff": diff,
    }


@app.post("/api/export_pdf")
def export_pdf(req: PdfRequest, username: str = Depends(get_current_user)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    try:
        pdf_bytes = pdf_export.render_pdf(req.document)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"PDF 生成失败：{safety.mask_secrets(exc)}"
        )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="report.pdf"'},
    )


@app.post("/api/assessment")
def assessment(req: AssessmentRequest, username: str = Depends(get_current_user), _key: None = Depends(require_llm_key)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    result = extract_assessment(req.document)
    return result if result is not None else {}


@app.post("/api/deliverables")
def deliverables(req: DeliverablesRequest, username: str = Depends(get_current_user), _key: None = Depends(require_llm_key)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    try:
        return generate_deliverables(req.document)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"生成交付物失败：{safety.mask_secrets(exc)}"
        )


@app.post("/api/ab_plan")
def ab_plan(req: AbPlanRequest, username: str = Depends(get_current_user), _key: None = Depends(require_llm_key)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    try:
        result = generate_ab_plan(req.document)
        return result if result is not None else {}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"生成方案失败：{safety.mask_secrets(exc)}"
        )


@app.post("/api/revision")
def revision(req: RevisionRequest, username: str = Depends(get_current_user), _key: None = Depends(require_llm_key)):
    if not (req.document or "").strip():
        raise HTTPException(status_code=400, detail="文档内容为空")
    if not (req.instructions or "").strip():
        raise HTTPException(status_code=400, detail="请填写补充或修改意见")
    try:
        new_doc = revise_document(req.document, req.instructions)
        return {
            "document": new_doc,
            "confirm_items": extract_confirm_items(new_doc),
            "assessment": extract_assessment(new_doc),
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"生成新版本失败：{safety.mask_secrets(exc)}"
        )


@app.post("/api/questionnaire")
def questionnaire(req: QuestionnaireRequest, username: str = Depends(get_current_user), _key: None = Depends(require_llm_key)):
    qa = [
        {
            "question": (a.get("question") or "").strip(),
            "answer": (a.get("answer") or "").strip(),
            "note": (a.get("note") or "").strip(),
        }
        for a in req.answers
        if (a.get("question") or "").strip()
        or (a.get("answer") or "").strip()
        or (a.get("note") or "").strip()
    ]
    SESSION_QA[req.session_id] = qa

    qa_text = "\n".join(f"问：{a['question']}\n答：{a['answer']}" for a in qa)
    notes_text = "\n".join(f"- {a['note']}" for a in qa if a["note"])
    try:
        question = next_question(qa_text, notes_text, force_continue=req.force_continue)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500, detail=f"生成题目失败：{safety.mask_secrets(exc)}"
        )

    return {
        "question": question,
        "answered_count": len(qa),
        "done": question.get("done", False),
        "summary": question.get("summary", ""),
    }


# ---------- 系统接口 ----------
@app.get("/api/health")
def health():
    """自检：确认服务、模型配置、知识库与数据库状态。"""
    stats = kb_stats()
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "key_configured": not missing_key(),
        "kb": stats,
        "db": os.path.basename(DB_PATH),
        "users": db.count_users(),
        "acceptances": db.count_acceptances(),
    }


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "8000")),
        log_level="info",
    )
