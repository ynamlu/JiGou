#!/usr/bin/env python
"""极构 · 需求诊断顾问 —— 本地一键启动。

用法：
    python run.py              # 构建前端 + 启动服务，自动打开浏览器
    python run.py --dev        # 前后端分开跑：Vite 热更新(5173) + FastAPI(8000)
    python run.py --port 8001  # 指定后端端口
    python run.py --rebuild    # 强制重新构建前端
    python run.py --no-browser # 不自动打开浏览器

脚本会自动完成：
1. 创建 backend/.venv（如果不存在）
2. 安装后端依赖（requirements.txt）
3. 安装前端依赖并构建（node_modules / dist 缺失或源码更新时）
4. 启动 FastAPI，并在浏览器打开 http://127.0.0.1:<port>
"""

import argparse
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = BACKEND / ".venv"
REQUIREMENTS = BACKEND / "requirements.txt"
SCRIPT = Path(__file__).resolve()

PIP_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def in_target_venv() -> bool:
    """用 sys.prefix 判断，比比较 exe 路径更可靠（避免符号链接导致反复重启）。"""
    try:
        return Path(sys.prefix).resolve() == VENV.resolve()
    except OSError:
        return False


def relaunch_in_venv() -> None:
    """切换到 backend/.venv 里的解释器，只切换一次。

    Windows 的 venv 启动器会派生一个基础解释器子进程，sys.prefix 不一定可靠，
    因此再用环境变量做一次兜底，避免反复重启。
    """
    py = venv_python()
    if not py.exists() or in_target_venv():
        return
    if os.environ.get("JG_VENV_REEXEC") == "1":
        return
    env = os.environ.copy()
    env["JG_VENV_REEXEC"] = "1"
    raise SystemExit(subprocess.call([str(py), str(SCRIPT), *sys.argv[1:]], env=env))


def ensure_venv() -> None:
    if venv_python().exists():
        return
    print("[setup] 首次运行，创建虚拟环境 backend/.venv ...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])


def ensure_backend_deps() -> None:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        print("[setup] 安装后端依赖（首次运行需要几分钟）...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS), "-i", PIP_MIRROR]
        )


def npm_command(args: list[str], cwd: Path) -> None:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        raise SystemExit(
            "没有找到 npm。请先安装 Node.js 18+（https://nodejs.org/zh-cn），再重新运行 python run.py"
        )
    cmd = [npm, *args]
    if os.name == "nt":
        # Windows 上 npm 是 .cmd，需要经 cmd.exe 执行
        cmd = [os.environ.get("COMSPEC", "cmd.exe"), "/c", *cmd]
    subprocess.check_call(cmd, cwd=str(cwd))


def frontend_needs_build() -> bool:
    dist = FRONTEND / "dist" / "index.html"
    if not dist.exists():
        return True
    newest = 0.0
    for path in (FRONTEND / "src").rglob("*"):
        if path.is_file():
            newest = max(newest, path.stat().st_mtime)
    for extra in ("index.html", "vite.config.js", "package.json", "package-lock.json"):
        path = FRONTEND / extra
        if path.is_file():
            newest = max(newest, path.stat().st_mtime)
    return newest > dist.stat().st_mtime


def build_frontend(force: bool = False) -> None:
    """仅在源码有更新或显式要求时构建，避免每次都等 npm。"""
    if not force and not frontend_needs_build():
        print("[web] 前端已是构建后的版本，跳过构建")
        return
    if not (FRONTEND / "node_modules").exists():
        print("[web] 安装前端依赖 ...")
        npm_command(["install", "--no-audit", "--no-fund"], FRONTEND)
    print("[web] 构建前端 ...")
    npm_command(["run", "build"], FRONTEND)


def pick_port(preferred: int) -> int:
    """从 preferred 开始找第一个可用端口，避免 8000 被占用时启动失败。"""
    for port in range(preferred, preferred + 30):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit(f"从 {preferred} 开始的 30 个端口都被占用了，请用 --port 指定其它端口")


def load_app():
    """按文件路径加载 backend/app.py，避免受当前工作目录影响。"""
    spec = importlib.util.spec_from_file_location("jigou_app", str(BACKEND / "app.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["jigou_app"] = module
    spec.loader.exec_module(module)
    return module


def stop_process(proc) -> None:
    """结束子进程（Windows 下连同 npm 派生的 node 一起结束）。"""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.call(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> None:
    parser = argparse.ArgumentParser(description="极构 · 需求诊断顾问 本地启动器")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--dev", action="store_true", help="启动 Vite 开发服务器（前端热更新）")
    parser.add_argument("--rebuild", action="store_true", help="强制重新构建前端")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        raise SystemExit(f"需要 Python 3.11 及以上，当前是 {sys.version.split()[0]}")

    ensure_venv()
    relaunch_in_venv()
    ensure_backend_deps()

    port = pick_port(args.port)

    dev_proc = None
    if args.dev:
        if not (FRONTEND / "node_modules").exists():
            print("[web] 安装前端依赖 ...")
            npm_command(["install", "--no-audit", "--no-fund"], FRONTEND)
        env = os.environ.copy()
        env["VITE_API_TARGET"] = f"http://127.0.0.1:{port}"
        print(f"[web] 启动 Vite 开发服务器（/api 代理到 {port}）...")
        npm = shutil.which("npm") or shutil.which("npm.cmd")
        if not npm:
            raise SystemExit(
                "没有找到 npm。请先安装 Node.js 18+（https://nodejs.org/zh-cn）"
            )
        cmd = [npm, "run", "dev"]
        if os.name == "nt":
            cmd = [os.environ.get("COMSPEC", "cmd.exe"), "/c", *cmd]
        dev_proc = subprocess.Popen(cmd, cwd=str(FRONTEND), env=env)
        url = "http://127.0.0.1:5173"
    else:
        build_frontend(force=args.rebuild)
        url = f"http://127.0.0.1:{port}"

    module = load_app()

    print("=" * 62)
    print("极构 · 需求诊断顾问（本地版）")
    print(f"访问地址：{url}")
    print(f"模型：{module.MODEL_NAME}")
    print(f"数据库：{module.DB_PATH}")
    if module.missing_key():
        print("提示：还没填 API Key —— 请编辑 backend/.env 的 LLM_API_KEY 后重启")
    print("按 Ctrl+C 停止")
    print("=" * 62)

    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()

    try:
        import uvicorn

        uvicorn.run(module.app, host="127.0.0.1", port=port, log_level="info")
    finally:
        if dev_proc:
            stop_process(dev_proc)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已停止。")
