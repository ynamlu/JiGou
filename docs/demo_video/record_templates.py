# -*- coding: utf-8 -*-
"""补录模板库片段（模板列表 → 详情 → 以此开始诊断 → 首页带入）。

产出：demo_video/raw/tpl.webm、demo_video/raw/marks_tpl.json
用法：python docs/demo_video/record_templates.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "demo_video" / "raw"
SHOTS = RAW / "shots_tpl"

T0 = 0.0
marks: dict[str, float] = {}
log: list[str] = []


def mark(name: str) -> None:
    marks[name] = round(time.monotonic() - T0, 2)
    print(f"  · {name:<16} {marks[name]:7.2f}s")


def run(page: Page) -> None:
    page.goto(f"{BASE}/#/login", wait_until="load")
    page.wait_for_timeout(900)
    page.locator('input[placeholder*="手机号"]').first.fill("13800138000")
    page.locator('input[type="password"]').first.fill("Demo@123456")
    page.get_by_role("button", name=re.compile("登录")).first.click()
    page.wait_for_timeout(2000)

    page.goto(f"{BASE}/#/templates", wait_until="load")
    page.wait_for_timeout(2600)
    mark("tpl_open")
    page.screenshot(path=str(SHOTS / "01_tpl.png"))

    page.mouse.move(760, 520, steps=16)
    page.wait_for_timeout(1500)
    page.mouse.move(1050, 600, steps=14)
    page.wait_for_timeout(1500)
    mark("tpl_hover")

    card = page.locator(".tpl-card").first
    if card.count():
        card.click()
        page.wait_for_timeout(2000)
        mark("tpl_detail")
        page.screenshot(path=str(SHOTS / "02_detail.png"))

    try:
        page.get_by_role("button", name=re.compile("以此开始诊断")).first.click(
            timeout=6000, force=True)
        page.wait_for_timeout(2200)
        mark("tpl_applied")
        page.screenshot(path=str(SHOTS / "03_applied.png"))
    except Exception as exc:  # noqa: BLE001
        log.append(f"带入失败：{exc}")

    page.wait_for_timeout(2600)
    mark("end")


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)

    global T0
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True,
                                    args=["--force-device-scale-factor=2", "--hide-scrollbars"])
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080}, device_scale_factor=2,
            locale="zh-CN", record_video_dir=str(RAW / "video_tpl"),
            record_video_size={"width": 3840, "height": 2160},
        )
        ctx.set_default_timeout(20000)
        page = ctx.new_page()
        tmp = None
        try:
            T0 = time.monotonic()
            run(page)
        except Exception as exc:  # noqa: BLE001
            log.append(f"中断：{exc}")
            print("!!", exc)
        finally:
            video = page.video
            tmp = video.path() if video else None
            ctx.close()
            browser.close()

    if tmp:
        target = RAW / "tpl.webm"
        if target.exists():
            target.unlink()
        Path(tmp).replace(target)
    (RAW / "marks_tpl.json").write_text(
        json.dumps({**marks, "_log": log}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("完成")
    for item in log:
        print("  -", item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
