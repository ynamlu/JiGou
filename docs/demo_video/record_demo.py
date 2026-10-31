# -*- coding: utf-8 -*-
"""用真实浏览器跑一遍系统完整流程并录屏（Chrome + Playwright）。

产出：
    demo_video/raw/video/*.webm   原始录屏（1920x1080）
    demo_video/raw/marks.json     各步骤时间戳（秒，相对录屏起点）
    demo_video/raw/shots/*.png    关键帧截图，便于核对

用法：python docs/demo_video/record_demo.py
前置：python run.py --no-browser  （服务在 http://127.0.0.1:8000）
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

BASE = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "demo_video" / "raw"
SHOTS = RAW / "shots"

T0 = 0.0
marks: dict[str, float] = {}
log: list[str] = []

CTRL_LABELS = {
    "放弃", "补充说明", "💡 补充说明", "上一题", "下一题", "生成需求报告",
    "取消", "确定", "继续", "开始需求分析", "按问卷答题", "自由对话",
}


def mark(name: str) -> None:
    marks[name] = round(time.monotonic() - T0, 2)
    print(f"  · {name:<20} {marks[name]:7.2f}s")


def shot(page: Page, name: str) -> None:
    page.screenshot(path=str(SHOTS / f"{len(marks):02d}_{name}.png"))


def slow_type(page: Page, selector: str, text: str, delay: int = 70) -> None:
    el = page.locator(selector).first
    el.click()
    el.fill("")
    el.type(text, delay=delay)


def click_text(page: Page, text: str, timeout: int = 8000) -> bool:
    pattern = re.compile(re.escape(text))
    for locator in (
        page.get_by_role("button", name=pattern),
        page.get_by_role("link", name=pattern),
        page.get_by_text(pattern),
    ):
        try:
            target = locator.first
            target.wait_for(state="visible", timeout=timeout)
            target.click(timeout=4000)
            return True
        except Exception:  # noqa: BLE001
            continue
    log.append(f"未找到可点击元素：{text}")
    print(f"    ! 未找到：{text}")
    return False


def option_buttons(page: Page) -> list:
    """页面上除控制按钮外的按钮，即当前题目的选项。"""
    out = []
    for btn in page.get_by_role("button").all():
        try:
            text = btn.inner_text().strip()
        except Exception:  # noqa: BLE001
            continue
        if not text or text in CTRL_LABELS or text.isdigit() or len(text) > 32:
            continue
        out.append((text, btn))
    return out


def start_analysis(page: Page, mode: str) -> None:
    """开始需求分析 → 弹窗选模式 → 确定。"""
    click_text(page, "开始需求分析")
    page.wait_for_timeout(900)
    click_text(page, mode, timeout=5000)
    page.wait_for_timeout(600)
    click_text(page, "确定", timeout=3000)
    page.wait_for_timeout(800)


def wait_question(page: Page, timeout: int = 45000) -> bool:
    try:
        page.get_by_role("button", name=re.compile("补充说明")).first.wait_for(
            state="visible", timeout=timeout)
        return True
    except PWTimeout:
        log.append("题目未出现")
        return False


def pick_option(page: Page, prefer: str | None = None, index: int = 0) -> str:
    cands: list = []
    for _ in range(24):
        cands = option_buttons(page)
        if cands:
            break
        page.wait_for_timeout(500)
    if not cands:
        log.append("没有找到可选项")
        return ""
    if prefer:
        for text, btn in cands:
            if prefer in text:
                btn.click()
                return text
    text, btn = cands[min(index, len(cands) - 1)]
    btn.click()
    return text


def run(page: Page) -> None:
    # ---------- 登录 ----------
    page.goto(f"{BASE}/#/login", wait_until="networkidle")
    page.wait_for_timeout(1200)
    mark("login_view")
    shot(page, "login")

    slow_type(page, 'input[placeholder*="手机号"]', "13800138000", 55)
    page.wait_for_timeout(400)
    slow_type(page, 'input[type="password"]', "Demo@123456", 45)
    page.wait_for_timeout(900)
    mark("login_typing")
    click_text(page, "登录")
    page.wait_for_url(re.compile(r".*#/(doc/\w+|templates|history)?$"), timeout=20000)
    page.wait_for_timeout(2200)
    mark("login_done")
    shot(page, "home")

    # ---------- 首页：两种模式 ----------
    page.mouse.move(700, 520, steps=18)
    page.wait_for_timeout(1300)
    page.mouse.move(1180, 640, steps=16)
    page.wait_for_timeout(1500)
    page.mouse.move(1000, 470, steps=14)
    page.wait_for_timeout(1300)
    mark("home_hover")

    # ---------- 账号信息 ----------
    if click_text(page, "13800138000", timeout=4000):
        page.wait_for_timeout(2600)
        mark("profile")
        shot(page, "profile")
        page.go_back()
        page.wait_for_timeout(1800)
    mark("profile_done")

    # ---------- 问卷 ----------
    start_analysis(page, "按问卷答题")
    wait_question(page)
    page.wait_for_timeout(2600)
    mark("quiz_q1")
    shot(page, "quiz_q1")

    def answer(prefer: str | None = None, index: int = 0) -> str:
        """答当前题；选项题点选项，填空题填文本。返回所选内容。"""
        before = [t for t, _ in option_buttons(page)]
        got = pick_option(page, prefer=prefer, index=index)
        if got:
            return got
        # 填空题兜底
        try:
            field = page.locator(".card textarea, .card input[type=text], textarea").first
            field.wait_for(state="visible", timeout=4000)
            field.click()
            field.type("扫码点单，顾客到店下单并在线支付", delay=45)
            page.wait_for_timeout(500)
            click_text(page, "下一题", timeout=3000)
            return "（填空）"
        except Exception:  # noqa: BLE001
            return ""

    q1 = answer("微信小程序")
    print(f"    第 1 题：{q1}")
    page.wait_for_timeout(7000)
    mark("quiz_a1")

    q2 = answer("顾客")
    print(f"    第 2 题：{q2}")
    page.wait_for_timeout(7000)
    mark("quiz_a2")
    shot(page, "quiz_q2")

    q3 = answer("扫码")
    if q3:
        print(f"    第 3 题：{q3}")
        page.wait_for_timeout(6500)
        mark("quiz_a3")

    if click_text(page, "补充说明", timeout=4000):
        page.wait_for_timeout(700)
        try:
            note = page.locator('textarea[placeholder*="想法"]').first
            note.wait_for(state="visible", timeout=4000)
            note.click()
            note.type("预算大概 3 到 5 万，想先上一个能用的版本。", delay=48)
            page.wait_for_timeout(600)
            mark("quiz_note")
            shot(page, "quiz_note")
        except PWTimeout:
            log.append("补充说明输入框未出现")

    back = page.get_by_role("button", name=re.compile("上一题")).first
    try:
        if back.is_enabled():
            back.click()
            page.wait_for_timeout(2400)
            mark("quiz_back")
            page.get_by_role("button", name=re.compile("下一题")).first.click()
            page.wait_for_timeout(2000)
            mark("quiz_next")
    except Exception:  # noqa: BLE001
        log.append("上一题/下一题不可用")

    # ---------- 生成报告 ----------
    page.wait_for_timeout(600)
    click_text(page, "生成需求报告", timeout=6000)
    page.wait_for_timeout(3000)
    mark("gen_start")
    shot(page, "generating")
    try:
        page.wait_for_url(re.compile(r".*#/doc/"), timeout=180000)
        page.wait_for_timeout(1800)
        mark("gen_done")
        shot(page, "doc_top")
    except PWTimeout:
        log.append("报告生成超时")
        mark("gen_done")

    for i in range(6):
        page.mouse.wheel(0, 560)
        page.wait_for_timeout(1300)
        mark(f"doc_scroll{i + 1}")
    shot(page, "doc_mid")
    marks["doc_scroll_end"] = round(time.monotonic() - T0, 2)
    print(f"  · doc_scroll_end        {marks['doc_scroll_end']:7.2f}s")

    # ---------- 自由对话 ----------
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1400)
    start_analysis(page, "自由对话")
    page.wait_for_timeout(1200)
    mark("chat_open")

    box = page.locator("textarea").last
    box.wait_for(state="visible", timeout=8000)
    box.click()
    box.type("我想做奶茶店扫码点单小程序", delay=58)
    page.wait_for_timeout(600)
    mark("chat_typed")
    shot(page, "chat_typed")
    box.press("Enter")
    page.wait_for_timeout(1600)
    mark("chat_send")
    page.wait_for_timeout(4500)
    shot(page, "chat_retrieval")
    mark("chat_retrieval")
    page.wait_for_timeout(18000)
    shot(page, "chat_stream")
    mark("chat_stream")
    page.mouse.wheel(0, 420)
    page.wait_for_timeout(3400)
    mark("chat_scroll")
    shot(page, "chat_scroll")

    # ---------- 回到报告 ----------
    page.goto(f"{BASE}/#/history", wait_until="networkidle")
    page.wait_for_timeout(2000)
    # 离开对话可能弹出「放弃本次分析」
    if page.get_by_role("button", name=re.compile("放弃并离开")).count():
        page.get_by_role("button", name=re.compile("放弃并离开")).first.click()
        page.wait_for_timeout(1500)
    mark("history_open")
    shot(page, "history")

    cards = page.locator(".doc-item")
    if cards.count():
        cards.first.click()
        page.wait_for_timeout(2200)
        mark("doc_again")
        shot(page, "doc_again")
    else:
        log.append("我的图纸为空，无法打开报告")

    page.mouse.wheel(0, 2600)
    page.wait_for_timeout(1600)
    mark("doc_confirm_area")
    shot(page, "confirm_area")
    if click_text(page, "一键全部已确认", timeout=6000):
        page.wait_for_timeout(2400)
        mark("confirm_all")
        shot(page, "confirm_all")

    if click_text(page, "确认验收", timeout=6000):
        page.wait_for_timeout(2800)
        mark("accepted")
        shot(page, "accepted")

    page.mouse.wheel(0, 700)
    page.wait_for_timeout(1200)
    if click_text(page, "生成 A/B 方案对比", timeout=6000):
        page.wait_for_timeout(9000)
        mark("ab_plan")
        shot(page, "ab_plan")

    page.mouse.wheel(0, 900)
    page.wait_for_timeout(1200)
    if click_text(page, "生成新版本", timeout=6000):
        page.wait_for_timeout(12000)
        mark("new_version")
        shot(page, "new_version")
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(1800)
    mark("diff")
    shot(page, "diff")

    # ---------- 回到报告顶部，通读 + 导出 ----------
    page.goto(page.url.split("#")[0] + "#/history", wait_until="networkidle")
    page.wait_for_timeout(1800)
    if page.locator(".doc-item").count():
        page.locator(".doc-item").first.click()
        page.wait_for_timeout(2200)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1200)
    mark("doc_tour_start")
    shot(page, "doc_tour_top")
    for i in range(8):
        page.mouse.wheel(0, 460)
        page.wait_for_timeout(1250)
        mark(f"doc_tour{i + 1}")
    shot(page, "doc_tour_mid")
    for i in range(5):
        page.mouse.wheel(0, 520)
        page.wait_for_timeout(1250)
        mark(f"doc_tour_end{i + 1}")
    shot(page, "doc_tour_bottom")

    if click_text(page, "导出 PDF", timeout=6000):
        page.wait_for_timeout(3200)
        mark("export_pdf")
        shot(page, "export_pdf")
    if click_text(page, "导出长截图", timeout=6000):
        page.wait_for_timeout(3600)
        mark("export_png")
        shot(page, "export_png")

    # ---------- 模板库 ----------
    page.goto(f"{BASE}/#/templates", wait_until="networkidle")
    page.wait_for_timeout(2400)
    mark("tpl_open")
    shot(page, "tpl")
    page.mouse.move(760, 520, steps=14)
    page.wait_for_timeout(1200)
    tpl = page.locator(".tpl-card")
    if tpl.count():
        tpl.first.click()
        page.wait_for_timeout(1800)
        mark("tpl_detail")
        shot(page, "tpl_detail")
    try:
        page.get_by_role("button", name=re.compile("以此开始诊断")).first.click(
            timeout=6000, force=True)
        page.wait_for_timeout(2400)
        mark("tpl_applied")
        shot(page, "tpl_applied")
    except Exception:  # noqa: BLE001
        log.append("模板带入失败")

    # ---------- 我的图纸（状态徽章 / 搜索） ----------
    page.goto(f"{BASE}/#/history", wait_until="networkidle")
    page.wait_for_timeout(2200)
    mark("hist_badges")
    page.mouse.move(900, 320, steps=10)
    page.wait_for_timeout(1400)
    shot(page, "hist_badges")
    try:
        box = page.locator('input[placeholder*="搜索图纸"]').first
        if box.count():
            box.click()
            box.type("小程序", delay=140)
            page.wait_for_timeout(1600)
            mark("hist_search")
            shot(page, "hist_search")
    except Exception:  # noqa: BLE001
        log.append("搜索框不可用")
    page.wait_for_timeout(1400)
    page.wait_for_timeout(1500)
    mark("end")


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    for f in SHOTS.glob("*.png"):
        f.unlink()

    global T0
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--force-device-scale-factor=2", "--hide-scrollbars",
                  "--disable-lcd-text", "--font-render-hinting=none"],
        )
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            record_video_dir=str(RAW / "video"),
            record_video_size={"width": 3840, "height": 2160},
        )
        ctx.set_default_timeout(20000)
        page = ctx.new_page()
        try:
            T0 = time.monotonic()
            run(page)
        except Exception as exc:  # noqa: BLE001
            log.append(f"中断：{type(exc).__name__}: {exc}")
            print(f"!! {exc}")
            try:
                page.screenshot(path=str(SHOTS / "error.png"))
            except Exception:  # noqa: BLE001
                pass
        finally:
            video = page.video
            tmp_path = video.path() if video else None
            ctx.close()
            browser.close()

    if tmp_path:
        target = RAW / "main.webm"
        if target.exists():
            target.unlink()
        Path(tmp_path).replace(target)

    (RAW / "marks_main.json").write_text(
        json.dumps({**marks, "_log": log}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n录屏：{RAW / 'video'}")
    for item in log:
        print("  -", item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
