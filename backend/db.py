"""SQLite 数据层（单文件，默认 backend/data/jigou.db）。

三张表：
- users        账号：id / username / password_hash / salt / created_at
- tokens       登录凭证：token / username / created_at（一个账号同时只保留一个有效 token）
- acceptances  验收记录：id / username / doc_hash / content / confirm_items /
               resolutions / project_key / version / diff / accepted_at

报告正文和草稿不在这里：它们按账号存在浏览器 localStorage（见前端 archive store），
数据库只存「账号 + 登录态 + 验收凭证」这三类需要跨会话保留的数据。
"""

import datetime
import hashlib
import os
import secrets
import sqlite3

from config import DB_PATH

_PBKDF2_ITERATIONS = 100_000


def _conn() -> sqlite3.Connection:
    """每次操作新建连接，避免 FastAPI 多线程共享同一个 sqlite 连接。"""
    directory = os.path.dirname(DB_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_missing_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]):
    """老版本 .db 文件的轻量迁移：缺哪列补哪列。"""
    existing = _columns(conn, table)
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db():
    """建表建索引，并给旧版 .db 补缺失字段；重复执行安全。"""
    conn = _conn()
    try:
        with conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tokens (
                    token TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS acceptances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL DEFAULT '',
                    doc_hash TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confirm_items TEXT NOT NULL DEFAULT '[]',
                    resolutions TEXT NOT NULL DEFAULT '[]',
                    project_key TEXT NOT NULL DEFAULT '',
                    version INTEGER NOT NULL DEFAULT 1,
                    diff TEXT,
                    accepted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_tokens_username
                    ON tokens (username);
                CREATE INDEX IF NOT EXISTS idx_acceptances_user_project
                    ON acceptances (username, project_key, version);
                """
            )
            _add_missing_columns(
                conn,
                "acceptances",
                {
                    "username": "TEXT NOT NULL DEFAULT ''",
                    "project_key": "TEXT NOT NULL DEFAULT ''",
                    "version": "INTEGER NOT NULL DEFAULT 1",
                    "diff": "TEXT",
                },
            )
    finally:
        conn.close()


# ---------- 密码 ----------
def hash_password(password: str, salt: str | None = None):
    if salt is None:
        salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS
    ).hex()
    return digest, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    digest, _ = hash_password(password, salt)
    return digest == expected_hash


# ---------- 账号 ----------
def user_exists(username: str) -> bool:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def create_user(username: str, password: str) -> None:
    digest, salt = hash_password(password)
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _conn()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, created_at) "
                "VALUES (?, ?, ?, ?)",
                (username, digest, salt, created_at),
            )
    finally:
        conn.close()


def check_login(username: str, password: str) -> bool:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT password_hash, salt FROM users WHERE username = ? LIMIT 1",
            (username,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return False
    return verify_password(password, row["salt"], row["password_hash"])


def get_user(username: str) -> dict | None:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT username, created_at FROM users WHERE username = ? LIMIT 1",
            (username,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_password(username: str, new_password: str) -> None:
    digest, salt = hash_password(new_password)
    conn = _conn()
    try:
        with conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
                (digest, salt, username),
            )
    finally:
        conn.close()


def delete_account(username: str) -> None:
    conn = _conn()
    try:
        with conn:
            conn.execute("DELETE FROM tokens WHERE username = ?", (username,))
            conn.execute("DELETE FROM acceptances WHERE username = ?", (username,))
            conn.execute("DELETE FROM users WHERE username = ?", (username,))
    finally:
        conn.close()


# ---------- 登录凭证 ----------
def create_token(username: str) -> str:
    token = secrets.token_hex(32)
    conn = _conn()
    try:
        with conn:
            conn.execute("DELETE FROM tokens WHERE username = ?", (username,))
            conn.execute(
                "INSERT INTO tokens (token, username) VALUES (?, ?)",
                (token, username),
            )
    finally:
        conn.close()
    return token


def get_username_by_token(token: str) -> str | None:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT username FROM tokens WHERE token = ? LIMIT 1", (token,)
        ).fetchone()
        return row["username"] if row else None
    finally:
        conn.close()


def delete_token(token: str) -> None:
    conn = _conn()
    try:
        with conn:
            conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
    finally:
        conn.close()


# ---------- 验收记录 ----------
def save_acceptance(
    username: str,
    doc_hash: str,
    content: str,
    confirm_items: str,
    resolutions: str,
    project_key: str = "",
    version: int = 1,
    diff: str = "",
):
    """写入一条验收记录，返回自增 id 与本地时间字符串。"""
    accepted_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _conn()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO acceptances "
                "(username, doc_hash, content, confirm_items, resolutions, "
                "project_key, version, diff, accepted_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    username,
                    doc_hash,
                    content,
                    confirm_items,
                    resolutions,
                    project_key,
                    version,
                    diff,
                    accepted_at,
                ),
            )
            return cur.lastrowid, accepted_at
    finally:
        conn.close()


def get_latest_acceptance(username: str, project_key: str) -> dict | None:
    """取某账号在某项目下的最新版本，用于计算下一版版本号与 diff。"""
    if not project_key:
        return None
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM acceptances WHERE username = ? AND project_key = ? "
            "ORDER BY version DESC LIMIT 1",
            (username, project_key),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def count_users() -> int:
    conn = _conn()
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()


def count_acceptances() -> int:
    conn = _conn()
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM acceptances").fetchone()
        return int(row["n"]) if row else 0
    finally:
        conn.close()
