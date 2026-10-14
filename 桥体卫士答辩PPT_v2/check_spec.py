# -*- coding: utf-8 -*-
"""check_spec.py —— 独立几何/文案校验工具（不生成 PPTX）

用途：
    1) 图形负责人自检 SPEC_diagrams.json（越界 / 重叠 / 文字溢出 / 色名与字号合法性）
    2) Lead 在合并前做快速回归
    3) 任何人在改完规格后一键复查

用法:
    <bundled-python> check_spec.py                    # 全量校验
    <bundled-python> check_spec.py --figs-only        # 只查图形
    <bundled-python> check_spec.py --slide s05_scene  # 只查某一页
    <bundled-python> check_spec.py --quiet            # 只输出结论
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_deck import (  # noqa: E402
    CHROME_H,
    CHROME_TITLE_W,
    COLORS,
    CONTENT_RIGHT,
    FOOTER_TOP,
    FONT_SIZES,
    MARGIN_X,
    PAGE_H,
    PAGE_W,
    Report,
    element_bbox,
    element_max_pt,
    element_text,
    overlap_bbox,
    rects_overlap,
    contains,
    wrap_lines,
    PT,
)

HERE = Path(__file__).resolve().parent


def check_color_fonts(fig_id, el, rep: Report):
    eid = el.get("id", "?")
    for key in ("fill", "line_color", "color", "header_fill", "body_fill", "alt_fill"):
        v = el.get(key)
        if v in (None, "none"):
            continue
        if str(v).startswith("#"):
            if len(str(v)) != 7:
                rep.err(fig_id, f"{eid} {key} 颜色格式非法: {v}")
            continue
        if v not in COLORS:
            rep.err(fig_id, f"{eid} {key} 未知颜色名: {v!r}（可用: {', '.join(COLORS)}）")
    for key in ("font",):
        v = el.get(key)
        if v is not None and v not in FONT_SIZES:
            rep.err(fig_id, f"{eid} 未知字号名: {v!r}")
    for r in el.get("runs") or []:
        if r.get("size") and r["size"] not in FONT_SIZES:
            rep.err(fig_id, f"{eid} run 未知字号名: {r['size']!r}")
        if r.get("color") and not str(r["color"]).startswith("#") and r["color"] not in COLORS:
            rep.err(fig_id, f"{eid} run 未知颜色名: {r['color']!r}")
    for s in el.get("series") or []:
        if s.get("color") and s["color"] not in COLORS:
            rep.err(fig_id, f"{eid} series 未知颜色名: {s['color']!r}")
    for b in el.get("bands") or []:
        if b.get("color") and b["color"] not in COLORS:
            rep.err(fig_id, f"{eid} band 未知颜色名: {b['color']!r}")
    for rl in el.get("ref_lines") or []:
        if rl.get("color") and rl["color"] not in COLORS:
            rep.err(fig_id, f"{eid} ref_line 未知颜色名: {rl['color']!r}")


def text_metrics(el):
    """返回 (行数, 最大字号pt, 文本) 或 None（非文本）。"""
    if el.get("type") != "text":
        return None
    txt = element_text(el)
    pt = element_max_pt(el)
    _, _, w, h = element_bbox(el)
    lines = wrap_lines(txt, w, pt)
    return len(lines), pt, txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default=str(HERE / "_spec" / "SPEC_content.json"))
    ap.add_argument("--diagrams", default=str(HERE / "_spec" / "SPEC_diagrams.json"))
    ap.add_argument("--figs-only", action="store_true")
    ap.add_argument("--slide", default=None)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--allow-partial", action="store_true")
    args = ap.parse_args()

    rep = Report()
    figs = []
    fp = Path(args.diagrams)
    if fp.exists():
        figs = json.loads(fp.read_text(encoding="utf-8")).get("figures") or []
    else:
        rep.err("-", f"缺少 {fp}")

    # chrome=none 的页面（封面/价值页/致谢页）允许几何铺满整页，不按页脚带判错
    chrome_by_slide = {}
    cp0 = Path(args.content)
    if cp0.exists():
        for s in json.loads(cp0.read_text(encoding="utf-8")).get("slides") or []:
            chrome_by_slide[s.get("slide_id")] = s.get("chrome", "standard")

    # ---------- 图形 ----------
    for f in figs:
        fid = f.get("fig_id", "?")
        if args.slide and f.get("for_slide") != args.slide:
            continue
        full_bleed = chrome_by_slide.get(f.get("for_slide")) == "none"
        els = f.get("elements") or []
        if not els:
            rep.err(fid, "图形元素为空")
        boxes = []
        for el in els:
            check_color_fonts(fid, el, rep)
            t = el.get("type")
            if t == "line":
                pts = el.get("points") or []
                if len(pts) < 2:
                    rep.err(fid, f"{el.get('id')} 折线点少于 2 个")
                for p in pts:
                    x, y = int(p[0]), int(p[1])
                    if not (MARGIN_X <= x <= CONTENT_RIGHT and 0 <= y <= PAGE_H):
                        rep.err(fid, f"{el.get('id')} 折线点越界 ({x},{y})")
                continue
            x, y, w, h = element_bbox(el)
            if w <= 0 or h <= 0:
                rep.err(fid, f"{el.get('id')} 宽高非正 {w}x{h}")
                continue
            if full_bleed:
                bx, by, bw, bh = 0, 0, PAGE_W, PAGE_H
            else:
                bx, by, bw, bh = MARGIN_X, 0, CONTENT_RIGHT - MARGIN_X, PAGE_H
            if not (bx <= x and x + w <= bx + bw and by <= y and y + h <= by + bh):
                rep.err(fid, f"{el.get('id')} 越界 x={x} y={y} w={w} h={h} (full_bleed={full_bleed})")
            if not full_bleed and y + h > FOOTER_TOP:
                rep.err(fid, f"{el.get('id')} 侵入页脚带 bottom={y+h} > {FOOTER_TOP}")
            # 页眉标题列（仅 standard 页）：会被页标题占住，图形不得进入
            if not full_bleed and rects_overlap(
                    (x, y, w, h), (MARGIN_X, 0, CHROME_TITLE_W, CHROME_H)):
                rep.err(fid, f"{el.get('id')} 压住页眉标题列 "
                             f"(x<{MARGIN_X + CHROME_TITLE_W}, y<{CHROME_H})")
            m = text_metrics(el)
            if m:
                nlines, pt, txt = m
                need = nlines * int(pt * PT * 1.15)
                if need > h * 1.05:
                    rep.warn(fid, f"{el.get('id')} 文字可能纵向溢出 需≈{need} 实际 {h}（{nlines} 行 @{pt:g}pt）")
                if pt < 11:
                    rep.warn(fid, f"{el.get('id')} 字号 {pt:g}pt < 11pt")
            if t == "table":
                rows = el.get("rows") or []
                if not rows:
                    rep.err(fid, f"{el.get('id')} 表格无 rows")
                else:
                    cols = max(len(r) for r in rows)
                    cw = el.get("col_widths") or [1.0 / cols] * cols
                    if abs(sum(cw) - 1.0) > 0.02:
                        rep.warn(fid, f"{el.get('id')} col_widths 和={sum(cw):.3f} ≠ 1")
            if t == "chart":
                if not el.get("series"):
                    rep.err(fid, f"{el.get('id')} chart 无 series")
                for s in el.get("series") or []:
                    for v in s.get("values") or []:
                        if v is not None and not isinstance(v, (int, float)):
                            rep.err(fid, f"{el.get('id')} 非数值数据点 {v!r}")
            boxes.append((el.get("id", "?"), overlap_bbox(el), t))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                ida, ba, _ = boxes[i]
                idb, bb, _ = boxes[j]
                if not rects_overlap(ba, bb):
                    continue
                if contains(ba, bb) or contains(bb, ba):
                    continue
                rep.warn(fid, f"元素重叠 {ida} {ba} × {idb} {bb}")

    # ---------- 文案 ----------
    if not args.figs_only:
        cp = Path(args.content)
        slides = json.loads(cp.read_text(encoding="utf-8")).get("slides") or [] if cp.exists() else []
        if not args.allow_partial and len(slides) != 15:
            rep.err("-", f"slides 数量应为 15，实际 {len(slides)}")
        for s in slides:
            sid = s.get("slide_id", "?")
            if args.slide and sid != args.slide:
                continue
            page_bounds = (0, 0, PAGE_W, PAGE_H) if s.get("chrome") == "none" else None
            boxes = []
            for el in s.get("elements") or []:
                check_color_fonts(sid, el, rep)
                x, y, w, h = element_bbox(el)
                if page_bounds:
                    bx, by, bw, bh = page_bounds
                else:
                    bx, by, bw, bh = MARGIN_X, 0, CONTENT_RIGHT - MARGIN_X, PAGE_H
                if not (bx <= x and x + w <= bx + bw and by <= y and y + h <= by + bh):
                    rep.err(sid, f"{el.get('id')} 越界 x={x} y={y} w={w} h={h}")
                if s.get("chrome", "standard") == "standard" and y + h > FOOTER_TOP:
                    rep.err(sid, f"{el.get('id')} 侵入页脚带 bottom={y+h} > {FOOTER_TOP}")
                m = text_metrics(el)
                if m:
                    nlines, pt, _ = m
                    if nlines * int(pt * PT * 1.15) > h * 1.05:
                        rep.warn(sid, f"{el.get('id')} 文字可能纵向溢出（{nlines} 行 @{pt:g}pt 需≈{nlines*int(pt*PT*1.15)} > {h}）")
                    if pt < 11:
                        rep.warn(sid, f"{el.get('id')} 字号 {pt:g}pt < 11pt")
                boxes.append((el.get("id", "?"), overlap_bbox(el), el.get("type")))
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    ida, ba, _ = boxes[i]
                    idb, bb, _ = boxes[j]
                    if rects_overlap(ba, bb) and not (contains(ba, bb) or contains(bb, ba)):
                        rep.warn(sid, f"内容元素重叠 {ida} {ba} × {idb} {bb}")
            notes = s.get("notes") or ""
            secs = float(s.get("seconds") or 0)
            n = len([c for c in notes if c.strip()])
            if n > secs * 4.5:
                rep.err(sid, f"讲稿超预算 {n} > {secs*4.5:.0f} 字")
            if not args.quiet:
                rep.note(f"{sid:13s} {secs:3.0f}s notes={n:4d}/{secs*4.5:.0f}")

        # 交叉：图形 vs 该页文字
        for s in slides:
            sid = s.get("slide_id")
            if args.slide and sid != args.slide:
                continue
            cboxes = [(el.get("id", "?"), overlap_bbox(el)) for el in (s.get("elements") or [])
                      if el.get("type") not in ("line",)]
            for f in figs:
                if f.get("for_slide") != sid:
                    continue
                for el in f.get("elements") or []:
                    if el.get("type") == "line":
                        continue
                    gb = overlap_bbox(el)
                    for cid, cb in cboxes:
                        if rects_overlap(gb, cb) and not (contains(gb, cb) or contains(cb, gb)):
                            rep.warn(sid, f"图形 {f.get('fig_id')}:{el.get('id')} × 文字 {cid} 重叠")

    ok = rep.dump()
    print("\n结论:", "通过 ✅" if ok else "存在 ERROR ❌")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
