"""创建评审用测试账号（可重复执行，不会覆盖已有账号）。

用法：
    cd backend
    .venv\\Scripts\\python.exe seed_demo.py
"""

import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import db

DEMO_USERNAME = "13800138000"
DEMO_PASSWORD = "Demo@123456"


def main():
    db.init_db()
    if db.user_exists(DEMO_USERNAME):
        print(f"[demo] 账号已存在：{DEMO_USERNAME}")
    else:
        db.create_user(DEMO_USERNAME, DEMO_PASSWORD)
        print(f"[demo] 已创建测试账号：{DEMO_USERNAME}")
    print(f"[demo] 手机号：{DEMO_USERNAME}")
    print(f"[demo] 密码：{DEMO_PASSWORD}")
    print(f"[demo] 数据库：{db.DB_PATH}")


if __name__ == "__main__":
    main()
