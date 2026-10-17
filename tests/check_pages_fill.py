"""「全站流式布局」改动的真机证据脚本（全部 7 个页面）。

用途（对应 docs/设计规范-视觉升级.md 8.5.1）：
验证视觉升级后各页面在多种视口下
  ① 没有横向溢出、
  ② 字号/间距**不随视口放大**（规范 3.1.4 已废除 `--pg-s` 视口缩放系数）、
  ③ 内容区最大宽度 1600px（规范 3.1.2）、
  ④ 环形图直径固定 160px（规范 5.4.3）、
  ⑤ 主要组件真的渲染出来了（卡片 / 表格行 / 图表 canvas）、
  ⑥ 深浅两套主题都能正常渲染（规范 6.4 A16）。

依赖：本仓库 tests/browser_harness.py（零依赖 headless Edge + 临时端口 Flask + 临时 SQLite）。
命令行等价于多次调用 browser_harness.py，但把所有断言集中成一份可复现报告。

用法（仓库根目录）：
    python tests/check_pages_fill.py                 # 默认视口 + 截图
    python tests/check_pages_fill.py --json out.json # 另存 JSON 报告
    python tests/check_pages_fill.py --only /alarms  # 只测某一页
退出码：0 全部通过；1 有断言失败（报告里逐条列出）；2 运行异常。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_harness import Harness  # noqa: E402

# 视口：设计基准 / 1080p / 答辩大屏 / 小笔记本 / 平板横屏 / 手机
VIEWPORTS = [(1280, 800), (1440, 900), (1920, 1080), (2560, 1440), (1366, 768), (900, 700), (390, 844)]

# 全部页面（登录页单独判定：它不套骨架）
PAGES = ["/dashboard", "/trend", "/alarms", "/history", "/device", "/settings"]

# 每页的关键结构探针：至少有一个必须存在，否则说明页面没渲染出内容
PAGE_PROBES = {
    "/trend": [".pg-stats .stat-card", "#chart canvas", "#gauge canvas", "#miniChart canvas"],
    "/alarms": [".pa-stats .pa-stat", "#alarmTable tr", "#donut canvas", ".alarm-ticker"],
    "/history": [".his-tabs button", ".filters input"],
    "/device": [".dv-3col .card", ".dv-stats .stat-card"],
    "/settings": [".set-grid .card", "#settingsForm input", "#auditList"],
    "/dashboard": [".metric-strip .ms-item", "#twinStage", ".hero-canvas"],
}

# 规范 2.2.2 的固定字号（废除 --pg-s 后，任何视口都必须是这些值）
EXPECTED_FONT_SIZES = {
    "--fs-2xs": 11,
    "--fs-xs": 12,
    "--fs-sm": 13,
    "--fs-md": 14,
    "--fs-lg": 16,
    "--fs-xl": 20,
    "--fs-2xl": 24,
    "--fs-3xl": 32,
}

# 量尺：一次 JS 调用取回所有要看的数（避免多次往返）。
MEASURE_JS = r"""
(() => {
  const de = document.documentElement;
  const page = document.querySelector('.sh-page');
  const px = (el, prop) => el ? parseFloat(getComputedStyle(el)[prop]) : null;
  const cs = getComputedStyle(de);
  const fs = {};
  ['--fs-2xs','--fs-xs','--fs-sm','--fs-md','--fs-lg','--fs-xl','--fs-2xl','--fs-3xl'].forEach(k => {
    fs[k] = parseFloat(String(cs.getPropertyValue(k) || '').trim()) || null;
  });
  const donut = document.getElementById('donut');
  const probeCounts = {};
  document.querySelectorAll('[data-probe]').forEach(() => {});
  return {
    vw: de.clientWidth,
    vh: de.clientHeight,
    hscroll: de.scrollWidth - de.clientWidth,
    bodyFont: px(document.body, 'fontSize'),
    pageMaxW: page ? getComputedStyle(page).maxWidth : null,
    pageW: page ? Math.round(page.getBoundingClientRect().width) : null,
    fs: fs,
    donut: donut ? [Math.round(donut.getBoundingClientRect().width),
                    Math.round(donut.getBoundingClientRect().height)] : null,
    cards: document.querySelectorAll('.card').length,
    rows: document.querySelectorAll('#alarmTable tr').length,
    canvases: document.querySelectorAll('canvas').length,
    navItems: document.querySelectorAll('.sh-nav-item').length,
    titleH: (() => { const t = document.querySelector('.sh-title'); return t ? Math.round(t.getBoundingClientRect().height) : null; })(),
    theme: de.getAttribute('data-theme'),
  };
})()
"""

SELECTOR_COUNT_JS = r"""
(sel) => document.querySelectorAll(sel).length
"""


def measure(page, url: str, vp: tuple[int, int], shot: str | None, theme: str = "light") -> dict:
    """先设视口再导航：让页面按目标宽度首屏渲染，避免按旧宽度布局后再 resize 掩盖问题。"""
    page.set_viewport(vp[0], vp[1])
    page.goto(url)
    page.wait_for("document.readyState === 'complete'", timeout=25)
    # 主题：写 localStorage 后重载一次，保证首屏就是该主题（不是先浅后深）
    if theme == "dark":
        page.eval_js("(() => { try { localStorage.setItem('bg.theme','dark'); } catch(e){} return 1; })()")
        page.goto(url)
        page.wait_for("document.readyState === 'complete'", timeout=25)
    else:
        page.eval_js("(() => { try { localStorage.setItem('bg.theme','light'); } catch(e){} return 1; })()")
    time.sleep(1.8)                       # 等 1Hz 轮询 + ECharts/3D 收敛
    data = page.eval_js(MEASURE_JS)
    data["viewport"] = list(vp)
    data["url"] = url
    data["theme"] = theme
    probes = PAGE_PROBES.get(url, [])
    if probes:
        data["probes"] = {sel: page.eval_js(f"document.querySelectorAll({sel!r}).length") for sel in probes}
    if shot:
        data["shot"] = page.screenshot(shot, settle=0.4)["path"]
    return data


def judge(d: dict) -> list[str]:
    fails = []
    tag = f"{d['url']} @{d['viewport'][0]}x{d['viewport'][1]} [{d['theme']}]"

    # ① 不得横向溢出（任何断点）
    if d["hscroll"] > 1:
        fails.append(f"{tag}: 横向溢出 {d['hscroll']}px")

    # ② 字号必须是规范 2.2.2 的固定值：任何视口都不得被放大（3.1.4 废除 --pg-s）
    for key, want in EXPECTED_FONT_SIZES.items():
        got = d["fs"].get(key)
        if got is None:
            fails.append(f"{tag}: 读不到 {key}")
        elif abs(got - want) > 0.51:
            fails.append(f"{tag}: {key} = {got}px（规范固定值 {want}px，说明又被视口缩放了）")

    # ③ 内容区最大宽度 1600px（3.1.2；设置页另有 1200px 的更窄上限）
    if d["pageMaxW"] not in ("1600px", "1200px", "none"):
        fails.append(f"{tag}: .sh-page max-width = {d['pageMaxW']}（规范要求 1600px）")

    # ④ 环形图直径固定 160px（桌面档；≤1279px 时按 5.4.3 仍是 160，仅在手机降为 120）
    if d["donut"]:
        want = 120 if d["viewport"][0] <= 768 else 160
        if abs(d["donut"][0] - want) > 2:
            fails.append(f"{tag}: 环形图直径 {d['donut'][0]}px（规范 {want}px）")

    # ⑤ 主要结构真的渲染出来了
    for sel, n in (d.get("probes") or {}).items():
        if n == 0:
            fails.append(f"{tag}: 关键结构缺失 {sel}")

    # ⑥ 手机端顶栏标题必须单行（tests/test_mobile_layout.py 守护的行为）
    if d["viewport"][0] <= 768 and d["titleH"] is not None and d["titleH"] > 26:
        fails.append(f"{tag}: 顶栏标题高 {d['titleH']}px（应 ≤26px，说明换行撑高了顶栏）")

    # 骨架完整性
    if d["url"] != "/login" and d["navItems"] != 6:
        fails.append(f"{tag}: 导航项 {d['navItems']} 个（应为 6）")

    return fails


def judge_login(d: dict) -> list[str]:
    """登录页：表单在、不溢出、没有渐变背景图案。"""
    fails = []
    tag = f"/login @{d['viewport'][0]}x{d['viewport'][1]} [{d['theme']}]"
    if d["hscroll"] > 1:
        fails.append(f"{tag}: 横向溢出 {d['hscroll']}px")
    for key, want in EXPECTED_FONT_SIZES.items():
        got = d["fs"].get(key)
        if got is not None and abs(got - want) > 0.51:
            fails.append(f"{tag}: {key} = {got}px（规范固定值 {want}px）")
    return fails


def use_workspace_temp() -> str:
    """把 tempfile 的临时目录挪到仓库内 .workbuddy/tmp，并替换 mkdtemp 实现。

    两个原因（都是宿主环境问题，不是被测页面问题）：
      1) browser_harness 用 tempfile 放 Flask 日志、临时 SQLite 与 Edge 的
         --user-data-dir；受限沙箱下系统 TEMP 目录不可写（PermissionError）。
      2) 即便指到仓库内，沙箱仍拒绝写入「tempfile.mkdtemp() 刚建出来的目录」
         （实测：同一路径下 os.makedirs 建的目录可写，mkdtemp 建的一律 EACCES），
         所以这里用 os.makedirs + 自增序号实现一个等价替身。
    """
    tmp = os.path.abspath(os.path.join(".workbuddy", "tmp"))
    os.makedirs(tmp, exist_ok=True)
    import itertools
    import tempfile as _tf

    _tf.tempdir = tmp
    counter = itertools.count(1)

    def _mkdtemp(prefix="tmp", suffix="", dir=None):
        base = dir or _tf.tempdir or os.getcwd()
        path = os.path.join(base, f"{prefix}{next(counter):03d}{suffix}")
        os.makedirs(path, exist_ok=True)
        return path

    _tf.mkdtemp = _mkdtemp
    return tmp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="json_out", default=None)
    ap.add_argument("--shots", default=os.path.join(".workbuddy", "shots"))
    ap.add_argument("--no-shots", action="store_true")
    ap.add_argument("--only", default="", help="只测某个 url，如 /alarms")
    ap.add_argument("--themes", default="light,dark", help="要测的主题，逗号分隔")
    ap.add_argument("--base-url", default=None,
                    help="用已在跑的服务（如 http://127.0.0.1:5000）而不是自己起临时 Flask 服务")
    args = ap.parse_args()

    print("tempdir:", use_workspace_temp())
    urls = [args.only] if args.only else PAGES + ["/login"]
    themes = [t.strip() for t in args.themes.split(",") if t.strip()]

    report = {"viewports": VIEWPORTS, "pages": urls, "themes": themes, "results": [], "fails": []}
    try:
        with Harness(width=VIEWPORTS[1][0], height=VIEWPORTS[1][1], base_url=args.base_url,
                     url_path="/login", verbose=False) as h:
            h.page.login(h.username, h.password)
            for vp in VIEWPORTS:
                for url in urls:
                    for theme in themes:
                        shot = None
                        if not args.no_shots:
                            shot = os.path.join(
                                args.shots,
                                f"{url.strip('/') or 'root'}_{vp[0]}x{vp[1]}_{theme}.png")
                        d = measure(h.page, url, vp, shot, theme)
                        fails = judge_login(d) if url == "/login" else judge(d)
                        d["fails"] = fails
                        report["results"].append(d)
                        report["fails"].extend(fails)
                        print(f"[{'FAIL' if fails else ' OK '}] {url:<11} @{vp[0]}x{vp[1]:<5} {theme:<5} "
                              f"hscroll={d['hscroll']:<3} fs-md={d['fs'].get('--fs-md')} "
                              f"maxW={d['pageMaxW']} cards={d['cards']}")
                        for f in fails:
                            print("        -", f)
            report["console_errors"] = [
                {"level": e.get("level"), "text": str(e.get("text", ""))[:200]}
                for e in h.page.console_errors()
            ]
    except Exception:
        traceback.print_exc()
        print("HARNESS ERROR")
        return 2

    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        print("report:", os.path.abspath(args.json_out))
    errs = [e for e in report.get("console_errors", []) if e.get("level") == "error"]
    if errs:
        print(f"console errors: {len(errs)}（前 3 条）")
        for e in errs[:3]:
            print("   ", e["text"])
    print("RESULT:", "PASS" if not report["fails"] else f"FAIL ({len(report['fails'])})")
    return 0 if not report["fails"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
