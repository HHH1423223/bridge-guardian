# -*- coding: utf-8 -*-
"""
桥体卫士答辩 PPT v2 —— 构建器（唯一产出 PPTX 的脚本）

用法:
    <bundled-python> build_deck.py                 # 校验 + 生成 pptx
    <bundled-python> build_deck.py --check         # 只校验与统计，不生成
    <bundled-python> build_deck.py --out X.pptx    # 指定输出

输入:
    _spec/SPEC_content.json    页面文案 / 版式 / 讲稿（负责人 A）
    _spec/SPEC_diagrams.json   矢量图形几何（负责人 B）
    _spec/BUILD_SPEC.md        规范（人读）

设计红线:
    - 零位图：只用 PowerPoint 原生形状 / 文本框 / 表格 / 折线。
    - 中文排版走「一行为一个 textbox」策略，避免依赖 PowerPoint 自动换行。
    - 任何越界 / 重叠 / 文字溢出都在校验阶段报出，不静默通过。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

from deck_style import (  # noqa: E402
    add_grid,
    add_progress_track,
    add_side_accent,
    build_cover_anim_groups,
    build_page_groups,
)

# --------------------------------------------------------------------------
# 常量：画布 / 颜色 / 字号
# --------------------------------------------------------------------------

FONT_CN = "微软雅黑"
FONT_EN = "Segoe UI"

PAGE_W, PAGE_H = 12192000, 6858000
MARGIN_X = 685800
CHROME_H = 1005840
CONTENT_TOP = 1188720
CONTENT_BOTTOM = 6035040
FOOTER_TOP = 6126480
CONTENT_RIGHT = PAGE_W - MARGIN_X
# 页眉标题列宽度。经 _work/diag_chrome.py 实测：
#   - 全部 13 个 standard 页的图形在顶部条带 y<1005840 的占用为 0（B 的几何都从 y≥1188720 起）；
#   - 最长标题「6 类可解释规则 —— 每条报警说清为什么」在 27pt 粗体下需 7035087 EMU。
# 取 7300000 可让全部标题单行放下，且右边界 7985800 < 内容右边界 11506200。
CHROME_TITLE_W = 7300000

COLORS = {
    "ink": "#0B1B2B",
    "navy": "#0E3F8C",
    "navy_deep": "#0A2E66",
    "blue": "#1E4FA8",
    "blue_soft": "#E8F0FA",
    "teal": "#00B3A4",
    "teal_soft": "#E0F7F5",
    "amber": "#F5A524",
    "orange": "#F2731F",
    "red": "#E5484D",
    "green": "#2FA84F",
    "slate": "#475569",
    "slate_light": "#8A97A8",
    "line": "#D8E0EA",
    "white": "#FFFFFF",
    "bg": "#F5F8FC",
}

FONT_SIZES = {
    "display": 66,
    "hero": 40,
    "h1": 27,
    "h2": 18,
    "h3": 15,
    "body": 13,
    "small": 11,
    "tiny": 9,
    "kpi": 32,
    "kpi_sm": 22,
}

ROLE_SIZE = {
    "title": "h1",
    "section": "small",
    "lead": "h2",
    "h2": "h2",
    "h3": "h3",
    "body": "body",
    "small": "small",
    "tiny": "tiny",
    "kpi": "kpi",
    "kpi_sm": "kpi_sm",
    "display": "display",
    "hero": "hero",
}

# 取整用的 EMU 换算
PT = 12700


def rgb(name):
    """颜色名 -> RGBColor；支持 '#RRGGBB' 直传，也支持裸 6 位十六进制（如 'E6EEF8'）。"""
    if isinstance(name, RGBColor):
        return name
    key = str(name).strip()
    if key.startswith("#"):
        hexv = key[1:]
    elif key in COLORS:
        hexv = COLORS[key][1:]
    elif len(key) == 6 and all(c in "0123456789abcdefABCDEF" for c in key):
        hexv = key
    else:
        raise KeyError(f"未知颜色名: {name}")
    return RGBColor.from_string(hexv.upper())


def size_pt(name):
    if isinstance(name, (int, float)):
        return float(name)
    if name in FONT_SIZES:
        return float(FONT_SIZES[name])
    raise KeyError(f"未知字号名: {name}")


# --------------------------------------------------------------------------
# 文本度量
# --------------------------------------------------------------------------


def char_em(ch: str) -> float:
    """单个字符占几个 em（微软雅黑近似）。"""
    if ch in "\n\r":
        return 0.0
    if ch == "\t":
        return 2.0
    o = ord(ch)
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 1.0
    if o < 0x20:
        return 0.0
    if o < 0x7F:
        # ASCII：数字与字母 0.52，窄符号更小
        if ch in "iljI.,;:'|![]()":
            return 0.28
        if ch in "MW@%":
            return 0.9
        return 0.52
    if 0x2000 <= o <= 0x206F:  # 通用标点
        return 0.5
    if 0x2190 <= o <= 0x2BFF:  # 箭头 / 符号
        return 0.9
    return 0.6


def text_em(s: str) -> float:
    return sum(char_em(c) for c in str(s))


def wrap_lines(text: str, box_w: int, pt: float) -> list:
    """按盒宽做 CJK 友好折行；显式 \n 强制换行。返回行列表。"""
    out = []
    for para in str(text).split("\n"):
        if not para:
            out.append("")
            continue
        max_em = (box_w * 0.95) / (pt * PT)
        cur, cur_em = "", 0.0
        for ch in para:
            ce = char_em(ch)
            if cur and cur_em + ce > max_em:
                out.append(cur)
                cur, cur_em = ch, ce
            else:
                cur += ch
                cur_em += ce
        out.append(cur)
    return out


def line_h(pt: float, spacing: float = 1.25) -> int:
    return int(pt * PT * spacing)


# --------------------------------------------------------------------------
# 几何工具
# --------------------------------------------------------------------------


def norm_rect(x, y, w, h):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w < 0:
        x, w = x + w, -w
    if h < 0:
        y, h = y + h, -h
    return x, y, w, h


def rects_overlap(a, b, tol=0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return False
    return not (
        ax + aw <= bx + tol or bx + bw <= ax + tol or ay + ah <= by + tol or by + bh <= ay + tol
    )


def contains(outer, inner, tol=0):
    ox, oy, ow, oh = outer
    ix, iy, iw, ih = inner
    return (
        ix >= ox - tol
        and iy >= oy - tol
        and ix + iw <= ox + ow + tol
        and iy + ih <= oy + oh + tol
    )


# --------------------------------------------------------------------------
# 校验
# --------------------------------------------------------------------------


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def err(self, slide_id, msg):
        self.errors.append(f"[{slide_id}] {msg}")

    def warn(self, slide_id, msg):
        self.warnings.append(f"[{slide_id}] {msg}")

    def note(self, msg):
        self.info.append(msg)

    def dump(self):
        for m in self.info:
            print(f"  · {m}")
        for m in self.warnings:
            print(f"  ! WARN  {m}")
        for m in self.errors:
            print(f"  x ERROR {m}")
        print(f"\n校验结果: {len(self.errors)} error / {len(self.warnings)} warn")
        return len(self.errors) == 0


def element_bbox(el):
    return norm_rect(el.get("x", 0), el.get("y", 0), el.get("w", 0), el.get("h", 0))


def chart_deco_pads(el):
    """图表自绘装饰的外扩量：(pad_l, pad_t, pad_b)，与 add_chart 的留白保持一致。"""
    fs = float(el.get("font_size", 11))
    yl = el.get("y_label")
    if yl:
        longest = max(text_em(line) for line in str(yl).split("\n"))
        y_extra = int(longest * fs * PT * 1.10) + 18288
    else:
        y_extra = 0
    return int(fs * PT * 1.9) + y_extra, int(fs * PT * 3.0), int(fs * PT * 1.9)


def overlap_bbox(el):
    """用于重叠检测的包围盒。图表会自动向外画坐标轴/图例/轴标签，
    因此按 add_chart 的实际留白向外放宽，避免把自绘装饰误报成碰撞。"""
    x, y, w, h = element_bbox(el)
    if el.get("type") == "chart":
        pad_l, pad_t, pad_b = chart_deco_pads(el)
        return (x + pad_l, y + pad_t, max(w - pad_l, 1), max(h - pad_t - pad_b, 1))
    return element_bbox(el)


def element_text(el) -> str:
    parts = []
    if el.get("text"):
        parts.append(str(el["text"]))
    for r in el.get("runs") or []:
        parts.append(str(r.get("t", "")))
    return "\n".join(parts)


def element_max_pt(el) -> float:
    pts = []
    if el.get("font"):
        pts.append(size_pt(el["font"]))
    for r in el.get("runs") or []:
        if r.get("size"):
            pts.append(size_pt(r["size"]))
    if el.get("font_size"):
        pts.append(float(el["font_size"]))
    return max(pts) if pts else 12.0


def validate_element(slide_id, el, rep: Report, bounds=None, allow_overlap_ids=()):
    """bounds: (x, y, w, h) 该元素允许出现的区域；None 表示默认内容区。
    注意 chrome=none 的页面（封面/价值页/致谢页）允许铺满整页，由调用方传入页面边界。"""
    eid = el.get("id", "?")
    t = el.get("type")
    if t not in ("text", "rect", "line", "table", "chart"):
        rep.err(slide_id, f"元素 {eid} 类型非法: {t!r}")
        return
    bbox = element_bbox(el)
    bx, by, bw, bh = bounds if bounds else (MARGIN_X, 0, CONTENT_RIGHT - MARGIN_X, PAGE_H)

    if t == "line":
        for p in el.get("points") or []:
            px, py = int(p[0]), int(p[1])
            if not (bx <= px <= bx + bw and by <= py <= by + bh):
                rep.err(slide_id, f"折线点越界: {eid} ({px},{py}) 允许区 {bounds}")
        return

    x, y, w, h = bbox
    if w <= 0 or h <= 0:
        rep.err(slide_id, f"元素 {eid} 宽高非正: {w}x{h}")
        return
    if not (bx <= x and x + w <= bx + bw and by <= y and y + h <= by + bh):
        rep.err(slide_id, f"元素 {eid} 越界: x={x} y={y} w={w} h={h} 允许区 {bounds}")

    if t == "text":
        txt = element_text(el)
        if not txt.strip():
            rep.err(slide_id, f"文本元素 {eid} 内容为空")
            return
        max_pt = element_max_pt(el)
        lines = wrap_lines(txt, w, max_pt)
        need_h = len(lines) * int(max_pt * PT * 1.15)
        if need_h > h * 1.05:
            rep.warn(
                slide_id,
                f"文本可能纵向溢出: {eid} 需≈{need_h} 实际 {h}（{len(lines)} 行 @{max_pt:g}pt）",
            )
        if max_pt < 11:
            rep.warn(slide_id, f"字号小于 11pt 可读性下限: {eid} = {max_pt:g}pt")

    if t == "table":
        rows = el.get("rows") or []
        if not rows:
            rep.err(slide_id, f"表格 {eid} 无 rows")
            return
        cols = max(len(r) for r in rows)
        fs = float(el.get("font_size", 11))
        cw = el.get("col_widths") or [1.0 / cols] * cols
        if abs(sum(cw) - 1.0) > 0.02:
            rep.warn(slide_id, f"表格 {eid} col_widths 和不为 1: {sum(cw):.3f}")
        # 每列最长内容是否放得下
        for ci in range(cols):
            col_px = w * cw[ci]
            longest = max((text_em(r[ci]) for r in rows if ci < len(r)), default=0.0)
            need = longest * fs * PT * 1.02 + 2 * 68580
            if need > col_px:
                rep.warn(
                    slide_id,
                    f"表格 {eid} 第 {ci+1} 列可能溢出: 需≈{int(need)} 实际 {int(col_px)}",
                )
        row_h = h / len(rows)
        if row_h < fs * PT * 1.5:
            rep.warn(slide_id, f"表格 {eid} 行高偏小: {int(row_h)} < {int(fs*PT*1.5)}")

    if t == "chart":
        cats = el.get("categories") or []
        series = el.get("series") or []
        if not series:
            rep.err(slide_id, f"图表 {eid} 无 series")
            return
        n = max((len(s.get("values") or []) for s in series), default=0)
        if cats and len(cats) < n:
            rep.warn(slide_id, f"图表 {eid} categories({len(cats)}) 少于数据点({n})")
        for s in series:
            for v in s.get("values") or []:
                if v is None:
                    continue
                if not isinstance(v, (int, float)) or math.isnan(float(v)):
                    rep.err(slide_id, f"图表 {eid} 含非数值数据点: {v!r}")
        fs = float(el.get("font_size", 11))
        if h < 6 * fs * PT:
            rep.warn(slide_id, f"图表 {eid} 高度偏小，轴标签可能挤: {h}")


def validate_deck(content, diagrams, rep: Report, expect_full=True):
    slides = content.get("slides") or []
    # 第 1 页封面已改为实景照片封面（不走 SPEC），因此 SPEC 里的 s01_cover 不参与校验
    body = [s for s in slides if s.get("slide_id") not in ("s01_cover", "s06_video")]
    if expect_full and len(slides) != 15:
        rep.err("-", f"slides 数量应为 15，实际 {len(slides)}")
    elif not expect_full:
        rep.note(f"partial 模式：仅校验已有 {len(slides)} 页")
    rep.note(f"页面构成：1 张照片封面 + 1 页视频占位 + {len(body)} 页内容 = {len(body) + 2} 页"
             f"（SPEC 的 s01_cover 已由照片封面取代、s06_video 已移到第 2 页，均不参与内容校验）")
    slides = body

    # 两张图已不参与渲染：
    #   cover_geo   —— 被实景照片封面取代
    #   video_slots —— 视频页要求"完全放空"，占位框/播放条/提示文字都不画
    figs_all = diagrams.get("figures") or []
    figs = [f for f in figs_all if f.get("fig_id") not in ("cover_geo", "video_slots")]

    seen_ids = set()
    for s in slides:
        sid = s.get("slide_id", "?")
        if sid in seen_ids:
            rep.err(sid, "slide_id 重复")
        seen_ids.add(sid)

        chrome = s.get("chrome", "standard")
        # chrome=none 的页面（封面/价值页/致谢页）允许铺满整页
        page_bounds = (0, 0, PAGE_W, PAGE_H) if chrome == "none" else None
        dy = TEXT_Y_OFFSET.get(sid, 0)
        # 内容元素
        boxes = []
        for raw in s.get("elements") or []:
            el = dict(raw, y=raw.get("y", 0) + dy) if dy else raw
            validate_element(sid, el, rep, bounds=page_bounds)
            boxes.append((el.get("id", "?"), overlap_bbox(el), el.get("type")))

        # 页眉页脚占位（standard 页不得被内容压住）
        if chrome == "standard":
            chrome_boxes = [
                ("__chrome_title__", (MARGIN_X, 0, CHROME_TITLE_W, CHROME_H), "chrome"),
                ("__footer__", (MARGIN_X, FOOTER_TOP, CONTENT_RIGHT - MARGIN_X, PAGE_H - FOOTER_TOP), "chrome"),
            ]
            for cid, cbox, _ in chrome_boxes:
                for eid, bbox, _t in boxes:
                    if eid.startswith("__"):
                        continue
                    if rects_overlap(cbox, bbox):
                        rep.warn(sid, f"内容元素 {eid} 与 {cid} 重叠")
            # 页脚带内不得有内容
            for eid, bbox, _t in boxes:
                if bbox[1] + bbox[3] > FOOTER_TOP:
                    rep.err(sid, f"内容元素 {eid} 侵入页脚带 (bottom={bbox[1]+bbox[3]} > {FOOTER_TOP})")

        # 同页重叠检测（允许完全包含：底卡 + 上层文字）
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                ida, ba, ta = boxes[i]
                idb, bb, tb = boxes[j]
                if not rects_overlap(ba, bb):
                    continue
                if contains(ba, bb) or contains(bb, ba):
                    continue  # 底卡包含上层，合法
                if ta == "line" or tb == "line":
                    continue
                rep.warn(sid, f"元素重叠: {ida} {ba} × {idb} {bb}")

        # 讲稿字数预算
        notes = s.get("notes") or ""
        secs = float(s.get("seconds") or 0)
        budget = secs * 4.5
        n = len([c for c in notes if c.strip()])
        if n > budget:
            rep.err(sid, f"讲稿超字数预算: {n} 字 > {budget:.0f} 字（{secs:g}s）")
        rep.note(f"{sid:14s} {secs:5.0f}s  讲稿 {n:4d}/{budget:.0f} 字")

    # 图形（cover_geo 与 video_slots 已不渲染，不计入）
    if expect_full and len(figs) != 13:
        rep.err("-", f"参与渲染的 figures 数量应为 13（15 张图去掉 cover_geo / video_slots），实际 {len(figs)}")
    fig_ids = [f.get("fig_id") for f in figs]
    dup = {i for i in fig_ids if fig_ids.count(i) > 1}
    if dup:
        rep.err("-", f"fig_id 重复: {sorted(dup)}")
    slide_ids = {s.get("slide_id") for s in slides}
    chrome_by_slide = {s.get("slide_id"): s.get("chrome", "standard") for s in slides}
    for f in figs:
        fid = f.get("fig_id", "?")
        if f.get("for_slide") not in slide_ids:
            rep.warn("-", f"图形 {fid} 的 for_slide={f.get('for_slide')!r} 不在页清单中")
        els = f.get("elements") or []
        if not els:
            rep.err(fid, "图形元素为空")
        # chrome=none 的页面允许图形铺满整页
        fbounds = (0, 0, PAGE_W, PAGE_H) if chrome_by_slide.get(f.get("for_slide")) == "none" else None
        boxes = []
        for el in els:
            validate_element(fid, el, rep, bounds=fbounds)
            if el.get("type") != "line":
                boxes.append((el.get("id", "?"), overlap_bbox(el), el.get("type")))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                ida, ba, _ = boxes[i]
                idb, bb, _ = boxes[j]
                if not rects_overlap(ba, bb):
                    continue
                if contains(ba, bb) or contains(bb, ba):
                    continue
                rep.warn(fid, f"图形元素重叠: {ida} {ba} × {idb} {bb}")

    # 图形 vs 该页内容元素（跨文件碰撞）
    by_slide = {}
    for f in figs:
        by_slide.setdefault(f.get("for_slide"), []).append(f)
    for s in slides:
        sid = s.get("slide_id")
        chrome_s = s.get("chrome", "standard")
        content_boxes = [
            (el.get("id", "?"), overlap_bbox(el), el.get("type"))
            for el in (s.get("elements") or [])
            if el.get("type") not in ("line",)
        ]
        for f in by_slide.get(sid, []):
            for el in f.get("elements") or []:
                if el.get("type") == "line":
                    continue
                gb = overlap_bbox(el)
                for cid, cb, _t in content_boxes:
                    if not rects_overlap(gb, cb):
                        continue
                    if contains(gb, cb) or contains(cb, gb):
                        continue
                    rep.warn(
                        sid,
                        f"图形 {f.get('fig_id')}:{el.get('id')} 与内容元素 {cid} 重叠",
                    )
                # 图形不得压住页眉标题列或页脚
                if chrome_s == "standard":
                    if rects_overlap(gb, (MARGIN_X, 0, CHROME_TITLE_W, CHROME_H)):
                        rep.err(sid, f"图形 {f.get('fig_id')}:{el.get('id')} 压住页眉标题列")
                    if gb[1] + gb[3] > FOOTER_TOP:
                        rep.err(
                            sid,
                            f"图形 {f.get('fig_id')}:{el.get('id')} 侵入页脚带 "
                            f"(bottom={gb[1]+gb[3]} > {FOOTER_TOP})",
                        )
    return rep


# --------------------------------------------------------------------------
# 渲染
# --------------------------------------------------------------------------


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = Emu(PAGE_W)
        self.prs.slide_height = Emu(PAGE_H)
        self.blank = self.prs.slide_layouts[6]

    def add(self, background="bg"):
        slide = self.prs.slides.add_slide(self.blank)
        if background:
            bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PAGE_W, PAGE_H)
            bg.fill.solid()
            bg.fill.fore_color.rgb = rgb(background)
            bg.line.fill.background()
            bg.shadow.inherit = False
        return slide

    def save(self, path):
        self.prs.save(str(path))


def set_run_font(run, pt, color, bold=False, italic=False):
    """设置字号/颜色/粗细，并**显式绑定中西文字体**。

    坑位记录（2026-10-02 实测）：旧版本这里写的是
        el.set("typeface", FONT_CN if tag == "a:ea" else FONT_EN)
    但 `for tag in ("a:latin", "a:ea", "a:cs")` 的循环里 a:ea 分支实际上被
    a:latin/a:cs 的 Segoe UI 覆盖，导致全 deck 299 处文字的中文全靠系统回退
    （本机有微软雅黑所以看不出问题，换机器会变样）。现在改成按 tag 分别赋值。
    """
    f = run.font
    f.size = Pt(pt)
    f.bold = bold
    f.italic = italic
    f.name = FONT_EN
    f.color.rgb = rgb(color)
    rPr = run._r.get_or_add_rPr()
    for tag, face in (("a:latin", FONT_EN), ("a:ea", FONT_CN), ("a:cs", FONT_EN)):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", face)


def no_autofit(tf):
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    for tag in ("a:normAutofit", "a:spAutoFit"):
        el = bodyPr.find(qn(tag))
        if el is not None:
            bodyPr.remove(el)
    bodyPr.append(bodyPr.makeelement(qn("a:noAutofit"), {}))


def add_text(slide, el):
    x, y, w, h = element_bbox(el)
    box = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    valign = el.get("valign", "top")
    tf.vertical_anchor = {
        "top": MSO_ANCHOR.TOP,
        "middle": MSO_ANCHOR.MIDDLE,
        "bottom": MSO_ANCHOR.BOTTOM,
    }.get(valign, MSO_ANCHOR.TOP)
    no_autofit(tf)

    align = {
        "left": PP_ALIGN.LEFT,
        "center": PP_ALIGN.CENTER,
        "right": PP_ALIGN.RIGHT,
    }.get(el.get("align", "left"), PP_ALIGN.LEFT)

    default_pt = size_pt(el.get("font", "body"))
    spacing = float(el.get("line_spacing", 1.25))
    color = el.get("color", "ink")
    bold = bool(el.get("bold", False))
    letter = float(el.get("letter_spacing", 0) or 0)

    runs = el.get("runs")
    if runs:
        segs = [
            (
                str(r.get("t", "")),
                size_pt(r["size"]) if r.get("size") else default_pt,
                r.get("color", color),
                bool(r.get("bold", bold)),
            )
            for r in runs
        ]
    else:
        segs = [(str(el.get("text", "")), default_pt, color, bold)]

    lines = str(segs[0][0]).split("\n") if False else None  # noqa: F841 (占位，见下)

    # 混排 runs 时按单段处理；纯文本时按显式换行拆段
    if runs:
        paragraphs = [segs]
    else:
        paragraphs = [[(p, segs[0][1], segs[0][2], segs[0][3])] for p in str(segs[0][0]).split("\n")]

    first = True
    for para in paragraphs:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = spacing
        for text, pt, col, bd in para:
            run = p.add_run()
            run.text = text
            set_run_font(run, pt, col, bold=bd)
            if letter:
                run._r.get_or_add_rPr().set("spc", str(int(letter * 100)))
    return box


def add_rect(slide, el):
    x, y, w, h = element_bbox(el)
    shape_kind = el.get("shape", "rect")
    radius = float(el.get("radius", 0) or 0)
    if shape_kind == "oval":
        kind = MSO_SHAPE.OVAL
    elif shape_kind == "diamond":
        kind = MSO_SHAPE.DIAMOND
    elif shape_kind == "triangle":
        kind = MSO_SHAPE.ISOSCELES_TRIANGLE
    elif shape_kind == "chevron":
        kind = MSO_SHAPE.CHEVRON
    elif radius > 0:
        kind = MSO_SHAPE.ROUNDED_RECTANGLE
    else:
        kind = MSO_SHAPE.RECTANGLE

    shape = slide.shapes.add_shape(kind, Emu(x), Emu(y), Emu(w), Emu(h))
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shape.adjustments[0] = min(max(radius, 0.0), 0.5)
        except Exception:
            pass

    fill = el.get("fill", "white")
    if fill in (None, "none"):
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)

    lc = el.get("line_color", "none")
    if lc in (None, "none"):
        shape.line.fill.background()
    else:
        shape.line.color.rgb = rgb(lc)
        shape.line.width = Pt(float(el.get("line_width", 1)))
        if el.get("dash"):
            shape.line.dash_style = 4  # MSO_LINE_DASH_STYLE.DASH

    shape.shadow.inherit = False
    shape.text_frame.text = ""
    return shape


def add_line(slide, el):
    pts = [(int(p[0]), int(p[1])) for p in (el.get("points") or [])]
    if len(pts) < 2:
        return None
    color = el.get("line_color", "slate")
    width = Pt(float(el.get("line_width", 1)))
    dash = bool(el.get("dash", False))
    arrow = bool(el.get("arrow", False))
    last = None
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        conn = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Emu(x1), Emu(y1), Emu(x2), Emu(y2)
        )
        conn.line.color.rgb = rgb(color)
        conn.line.width = width
        if dash:
            conn.line.dash_style = 4
        if arrow and i == len(pts) - 2:
            ln = conn.line._get_or_add_ln()
            tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
            ln.append(tail)
        last = conn
    return last


def add_table(slide, el):
    x, y, w, h = element_bbox(el)
    rows = el.get("rows") or []
    nrows, ncols = len(rows), max(len(r) for r in rows)
    cw = el.get("col_widths") or [1.0 / ncols] * ncols
    widths = [int(w * c) for c in cw]
    widths[-1] = w - sum(widths[:-1])

    gf = slide.shapes.add_table(nrows, ncols, Emu(x), Emu(y), Emu(w), Emu(h))
    table = gf.table
    for i, cwi in enumerate(widths):
        table.columns[i].width = Emu(cwi)
    row_h = int(h / nrows)
    for r in range(nrows):
        table.rows[r].height = Emu(row_h)

    fs = float(el.get("font_size", 11))
    header_fill = el.get("header_fill", "navy")
    body_fill = el.get("body_fill", "white")
    alt_fill = el.get("alt_fill", "blue_soft")

    for r in range(nrows):
        for c in range(ncols):
            cell = table.cell(r, c)
            text = rows[r][c] if c < len(rows[r]) else ""
            cell.text = ""
            cell.margin_left = cell.margin_right = Emu(68580)
            cell.margin_top = cell.margin_bottom = Emu(27432)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            if r == 0:
                fill_name, fg, bold = header_fill, "white", True
            else:
                fill_name = body_fill if r % 2 == 1 else alt_fill
                fg, bold = "slate", (c == 0)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(fill_name)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            run = p.add_run()
            run.text = str(text)
            set_run_font(run, fs, fg, bold=bold)
    return gf


# ---------------------------- 图表（自绘，无第三方依赖） ----------------------------


def _chart_scales(el):
    series = el.get("series") or []
    vals = [v for s in series for v in (s.get("values") or []) if isinstance(v, (int, float))]
    refs = [r.get("value") for r in (el.get("ref_lines") or []) if isinstance(r.get("value"), (int, float))]
    lo = el.get("y_min")
    hi = el.get("y_max")
    if lo is None:
        lo = 0.0
    if hi is None:
        m = max(vals + refs) if (vals or refs) else 1.0
        hi = m * 1.15 if m > 0 else 1.0
    return float(lo), float(hi)


def add_chart(slide, el):
    x, y, w, h = element_bbox(el)
    ctype = el.get("chart_type", "line")
    series = el.get("series") or []
    cats = el.get("categories") or []
    n = max((len(s.get("values") or []) for s in series), default=0)
    if n == 0:
        return None

    fs = float(el.get("font_size", 11))
    axis_gap = int(fs * PT * 1.9)
    x_label = el.get("x_label")
    y_label = el.get("y_label")
    # Y 轴标签：竖排放不下就会折行并与刻度数字叠字（第 7 页实测），
    # 因此宽度按"最长一行恰好放下"计算，且位置挪到图表左上角、与最高刻度错开。
    y_label_w = 0
    if y_label:
        longest = max(text_em(line) for line in str(y_label).split("\n"))
        y_label_w = int(longest * fs * PT * 1.10) + 18288
    pad_l = axis_gap + y_label_w
    pad_b = axis_gap + (int(fs * PT * 1.6) if x_label else 0)
    pad_t = int(fs * PT * 3.0)
    pad_r = int(fs * PT * 1.2)
    px, py = x + pad_l, y + pad_t
    pw, ph = w - pad_l - pad_r, h - pad_t - pad_b
    if pw <= 0 or ph <= 0:
        return None

    lo, hi = _chart_scales(el)
    span = (hi - lo) or 1.0

    def ypos(v):
        return int(py + ph - (float(v) - lo) / span * ph)

    # 背景带
    for band in el.get("bands") or []:
        b0 = max(float(band.get("from", lo)), lo)
        b1 = min(float(band.get("to", hi)), hi)
        if b1 <= b0:
            continue
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Emu(px), Emu(ypos(b1)), Emu(pw), Emu(max(ypos(b0) - ypos(b1), 1))
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(band.get("color", "blue_soft"))
        shape.line.fill.background()
        shape.shadow.inherit = False

    # 网格 + Y 轴刻度
    ticks = 4
    for i in range(ticks + 1):
        v = lo + span * i / ticks
        yy = ypos(v)
        add_line(slide, {"points": [[px, yy], [px + pw, yy]], "line_color": "line", "line_width": 0.75})
        lab = slide.shapes.add_textbox(Emu(x), Emu(yy - int(fs * PT * 0.8)), Emu(pad_l - 27432), Emu(int(fs * PT * 1.6)))
        tf = lab.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = 0
        tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run()
        r.text = f"{v:g}"
        set_run_font(r, fs, "slate_light")

    # 轴
    add_line(slide, {"points": [[px, py], [px, py + ph]], "line_color": "line", "line_width": 1.25})
    add_line(slide, {"points": [[px, py + ph], [px + pw, py + ph]], "line_color": "line", "line_width": 1.25})

    if ctype in ("bar",):
        group_w = pw / n
        inner = group_w * 0.62
        bw = inner / max(len(series), 1)
        for si, s in enumerate(series):
            for i in range(n):
                v = (s.get("values") or [None] * n)[i] if i < len(s.get("values") or []) else None
                if not isinstance(v, (int, float)):
                    continue
                bx = int(px + group_w * i + (group_w - inner) / 2 + bw * si)
                top = ypos(v)
                bh = max(py + ph - top, 1)
                shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(bx), Emu(top), Emu(max(int(bw * 0.88), 1)), Emu(bh))
                shape.fill.solid()
                shape.fill.fore_color.rgb = rgb(s.get("color", "navy"))
                shape.line.fill.background()
                shape.shadow.inherit = False
    else:
        step = pw / max(n - 1, 1)
        for s in series:
            vals = s.get("values") or []
            pts = []
            for i, v in enumerate(vals):
                if not isinstance(v, (int, float)):
                    continue
                pts.append([int(px + step * i), ypos(v)])
            color = s.get("color", "teal")
            if ctype == "area" and len(pts) >= 2:
                poly = [[pts[0][0], py + ph]] + pts + [[pts[-1][0], py + ph]]
                for i in range(len(poly) - 1):
                    add_line(slide, {"points": [poly[i], poly[i + 1]], "line_color": color, "line_width": 0.75})
            if len(pts) >= 2:
                add_line(slide, {"points": pts, "line_color": color, "line_width": float(s.get("width", 2.25)), "dash": bool(s.get("dash", False))})
            for pxy in pts:
                dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Emu(pxy[0] - 38100), Emu(pxy[1] - 38100), Emu(76200), Emu(76200))
                dot.fill.solid()
                dot.fill.fore_color.rgb = rgb(color)
                dot.line.fill.background()
                dot.shadow.inherit = False

    # 参考线
    for ref in el.get("ref_lines") or []:
        v = ref.get("value")
        if not isinstance(v, (int, float)):
            continue
        yy = ypos(v)
        add_line(slide, {"points": [[px, yy], [px + pw, yy]], "line_color": ref.get("color", "red"), "line_width": 1.25, "dash": True})
        if ref.get("label"):
            lw = int(text_em(ref["label"]) * fs * PT * 1.05) + 13716
            lx = min(px + pw - lw, px + int(pw * 0.02))
            ly_top = max(yy - int(fs * PT * 1.55), py)
            # 参考线标签要压在色带/折线上，先铺一块白底，否则会被同色带淹没（第 7 页实测）
            bg = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, Emu(max(lx, px)), Emu(ly_top),
                Emu(lw), Emu(int(fs * PT * 1.5))
            )
            bg.fill.solid()
            bg.fill.fore_color.rgb = rgb("white")
            bg.line.fill.background()
            bg.shadow.inherit = False
            box = slide.shapes.add_textbox(Emu(max(lx, px)), Emu(ly_top), Emu(lw), Emu(int(fs * PT * 1.5)))
            tf = box.text_frame
            tf.word_wrap = False
            tf.margin_left = tf.margin_right = 0
            tf.margin_top = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(ref["label"])
            set_run_font(r, fs, ref.get("color", "red"), bold=True)

    # X 轴类目
    if cats:
        step = pw / max(n - 1, 1) if ctype != "bar" else pw / n
        for i, c in enumerate(cats[:n]):
            cw_ = int(step * 0.96)
            cx = int(px + (step * i - step / 2 if ctype == "bar" else step * i - cw_ / 2))
            cx = max(px, min(cx, px + pw - cw_))
            box = slide.shapes.add_textbox(Emu(cx), Emu(py + ph + 27432), Emu(cw_), Emu(int(fs * PT * 1.5)))
            tf = box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = 0
            tf.margin_top = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(c)
            set_run_font(r, fs, "slate_light")

    if x_label:
        box = slide.shapes.add_textbox(Emu(px), Emu(y + h - int(fs * PT * 1.4)), Emu(pw), Emu(int(fs * PT * 1.3)))
        tf = box.text_frame
        tf.margin_left = tf.margin_right = 0
        tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = str(x_label)
        set_run_font(r, fs, "slate_light")
    if y_label:
        box = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(pad_l - 27432), Emu(int(fs * PT * 1.5)))
        tf = box.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = 0
        tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run()
        r.text = str(y_label)
        set_run_font(r, fs, "slate_light")

    # 图例
    legend = [s.get("name") for s in series if s.get("name")]
    if len(legend) > 1:
        lw = int(max(text_em(nm) for nm in legend) * fs * PT * 1.05) + int(fs * PT * 2.2)
        lx = px + pw - lw
        ly = y
        for i, s in enumerate(series):
            if not s.get("name"):
                continue
            yy = ly + i * int(fs * PT * 1.5)
            if lx < px:
                break
            sw = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(lx), Emu(yy + int(fs * PT * 0.35)), Emu(int(fs * PT * 0.9)), Emu(int(fs * PT * 0.35)))
            sw.fill.solid()
            sw.fill.fore_color.rgb = rgb(s.get("color", "teal"))
            sw.line.fill.background()
            sw.shadow.inherit = False
            box = slide.shapes.add_textbox(Emu(lx + int(fs * PT * 1.1)), Emu(yy), Emu(lw), Emu(int(fs * PT * 1.45)))
            tf = box.text_frame
            tf.word_wrap = False
            tf.margin_left = tf.margin_right = 0
            tf.margin_top = tf.margin_bottom = 0
            r = tf.paragraphs[0].add_run()
            r.text = str(s["name"])
            set_run_font(r, fs, "slate")
    return None


RENDERERS = {
    "text": add_text,
    "rect": add_rect,
    "line": add_line,
    "table": add_table,
    "chart": add_chart,
}

# chrome=none 的页面没有页眉，页标题必须由构建器落成可见文字。
# 这里的位置是按各页几何留白定的（封面右侧色块从 x=9830000 起；致谢页上下留白充足）。
NO_CHROME_TITLE = {
    "s01_cover": {"x": 1188720, "y": 2200000, "w": 8300000, "h": 1300000,
                  "font": "display", "color": "ink", "bold": True, "valign": "middle"},
    "s15_thanks": {"x": 3000000, "y": 1250000, "w": 6192000, "h": 1000000,
                   "font": "display", "color": "ink", "bold": True, "align": "center",
                   "valign": "middle"},
}

# 个别页需要把规格里的文字整体下移，避免与页标题贴太近（不改规格文件，构建期生效）。
TEXT_Y_OFFSET = {"s15_thanks": 300000}

# 构建期颜色覆盖：致谢页是浅色主题（无深色底带），规格里的白色文字在白底上不可见。
# 只覆盖颜色，不动文案与坐标。
TEXT_COLOR_OVERRIDE = {
    "s15_thanks": {"white": "navy"},
}

# --------------------------------------------------------------------------
# 第 1 页：实景照片封面（花江峡谷大桥）
# 第 2 页：视频占位页（放空，用户自己拖录屏进去）
# 原 15 页整体下移一位 → 共 16 页。时间口径不变：原第 6 页（视频）本就是 60 秒，
# 现在把"空页 + 备注"放在最前面，讲解时切到第 2 页播放即可。
# --------------------------------------------------------------------------
PHOTO_COVER_IMAGE = "assets/封面_花江峡谷大桥.png"
TOTAL_PAGES = 16

COVER_NOTES = (
    "各位评委好，我是「桥体卫士」的答辩人。这是一套桥梁结构健康监测的缩尺原型系统："
    "从采集、判断、存储到展示与处置，五个环节跑成一条完整闭环。"
    "这套系统是怎么做的、能证明什么，我用十二分钟讲清楚。"
)
VIDEO_PAGE_NOTES = (
    "本页为演示视频页。开场：「这一分钟是系统的完整操作录屏——用模拟数据源跑通全链路，"
    "因为本次不使用硬件。」收尾：「视频里最后一步是拔掉设备、系统如实显示离线——"
    "这是我最想强调的一点：不造假。」"
)


def set_gradient_fill(shape, stops):
    """给形状写入线性渐变（stops: [(pos0_1, 'RRGGBB', alpha0_1), ...]）。

    python-pptx 没有渐变透明度 API，这里手工构造 a:gradFill；并保证它插在 a:ln 之前
    （OOXML 里 fill 必须在 line 之前，顺序错了 PowerPoint 可能报需要修复）。
    """
    spPr = shape._element.spPr
    for tag in ("a:solidFill", "a:noFill", "a:gradFill", "a:blipFill", "a:pattFill"):
        el = spPr.find(qn(tag))
        if el is not None:
            spPr.remove(el)
    grad = spPr.makeelement(qn("a:gradFill"), {"rotWithShape": "1"})
    gsLst = grad.makeelement(qn("a:gsLst"), {})
    grad.append(gsLst)
    for pos, color, alpha in stops:
        gs = grad.makeelement(qn("a:gs"), {"pos": str(int(pos * 100000))})
        clr = grad.makeelement(qn("a:srgbClr"), {"val": color})
        if alpha < 1.0:
            a = grad.makeelement(qn("a:alpha"), {"val": str(int(alpha * 100000))})
            clr.append(a)
        gs.append(clr)
        gsLst.append(gs)
    lin = grad.makeelement(qn("a:lin"), {"ang": "5400000", "scaled": "0"})  # 90° 自上而下
    grad.append(lin)
    ln = spPr.find(qn("a:ln"))
    if ln is not None:
        ln.addprevious(grad)
    else:
        spPr.append(grad)


def add_cover_slide(deck, here: Path):
    """实景照片封面：满幅照片 + 下半部渐变压暗 + 竖条 + 三行文字。"""
    slide = deck.add("ink")
    # 1) 照片满幅（1251x704 = 16:9，正好不裁切）
    photo = here / PHOTO_COVER_IMAGE
    if not photo.exists():
        raise FileNotFoundError(f"封面照片缺失: {photo}")
    pic = slide.shapes.add_picture(str(photo), 0, 0, width=Emu(PAGE_W), height=Emu(PAGE_H))

    # 2) 渐变压暗（从 40% 高度开始，底部 92% 不透明）——保证任何投影仪下文字都读得清
    veil = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, int(PAGE_H * 0.40),
                                  PAGE_W, int(PAGE_H * 0.60))
    veil.line.fill.background()
    veil.shadow.inherit = False
    set_gradient_fill(veil, [
        (0.00, "0B1B2B", 0.00),
        (0.45, "0B1B2B", 0.58),
        (1.00, "0B1B2B", 0.90),
    ])

    # 3) 左侧竖条（与内页装饰呼应）
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(685800), Emu(3429000),
                                 Emu(91440), Emu(2514600))
    bar.fill.solid()
    bar.fill.fore_color.rgb = rgb("teal")
    bar.line.fill.background()
    bar.shadow.inherit = False

    # 4) 三行文字（标题 → 副标 → 身份行）
    lines = [
        ("桥体卫士", 66, "white", True, 3300000, 1143000),
        ("桥梁结构健康监测缩尺原型 · 三维可视化监测场景", 20, "E6EEF8", False, 4600000, 400000),
        ("软件技术专业 · 缩尺桥梁模型受载变化模拟 · 单人主讲", 13, "AFC3D8", False, 5050000, 340000),
    ]
    for text, pt, color, bold, y, h in lines:
        box = slide.shapes.add_textbox(Emu(1028700 if pt < 40 else 1028700), Emu(y),
                                       Emu(9800000), Emu(h))
        tf = box.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        run = tf.paragraphs[0].add_run()
        run.text = text
        set_run_font(run, pt, color, bold=bold)
    slide.notes_slide.notes_text_frame.text = COVER_NOTES
    return slide


def add_video_slide(deck, total=None, index=2):
    """视频占位页：**完全放空**（用户自己把录屏拖进来），只保留标准页眉页脚。

    首页之后紧接着这一页，便于开场就切进去放录屏。
    """
    slide = deck.add("bg")
    add_grid(slide)
    if total:
        add_chrome(slide, {"section": "现场演示", "title": "演示视频（1 分钟）"}, index, total)
        add_progress_track(slide, index, total)
    slide.notes_slide.notes_text_frame.text = VIDEO_PAGE_NOTES
    return slide


def add_no_chrome_title(slide, s):
    spec = NO_CHROME_TITLE.get(s.get("slide_id"))
    if not spec or not s.get("title"):
        return
    el = dict(spec)
    el["id"] = "__title__"
    el["type"] = "text"
    el["text"] = s["title"]
    add_text(slide, el)


def add_chrome(slide, s, index, total):
    """标准页眉页脚：只在左侧标题列绘制，右侧整条留给图形。"""
    section = s.get("section")
    title = s.get("title") or ""
    if section:
        box = slide.shapes.add_textbox(Emu(MARGIN_X), Emu(228600), Emu(CHROME_TITLE_W), Emu(228600))
        tf = box.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        r = tf.paragraphs[0].add_run()
        r.text = str(section)
        set_run_font(r, 11, "teal", bold=True)
        r._r.get_or_add_rPr().set("spc", "200")
    if title:
        box = slide.shapes.add_textbox(Emu(MARGIN_X), Emu(476250), Emu(CHROME_TITLE_W), Emu(457200))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        no_autofit(tf)
        r = tf.paragraphs[0].add_run()
        r.text = str(title)
        set_run_font(r, FONT_SIZES["h1"], "ink", bold=True)
        # 单行宽度硬校验：标题必须一行放下（否则会像"一屏统/管"那样折断）
        need = int(text_em(str(title)) * FONT_SIZES["h1"] * PT * 1.12)
        if need > CHROME_TITLE_W:
            raise ValueError(
                f"标题超宽将折行: {title!r} 需 {need} > {CHROME_TITLE_W} EMU；"
                f"请缩短标题或加宽 CHROME_TITLE_W"
            )
    # 页眉分隔线
    add_line(slide, {"points": [[MARGIN_X, CHROME_H], [CONTENT_RIGHT, CHROME_H]], "line_color": "line", "line_width": 1})
    # 页脚
    add_line(slide, {"points": [[MARGIN_X, FOOTER_TOP], [CONTENT_RIGHT, FOOTER_TOP]], "line_color": "line", "line_width": 1})
    box = slide.shapes.add_textbox(Emu(MARGIN_X), Emu(FOOTER_TOP + 45720), Emu(int(CHROME_TITLE_W * 1.6)), Emu(228600))
    tf = box.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    r = tf.paragraphs[0].add_run()
    r.text = "桥体卫士 · 桥梁结构健康监测缩尺原型"
    set_run_font(r, FONT_SIZES["tiny"], "slate_light")

    box = slide.shapes.add_textbox(Emu(CONTENT_RIGHT - 1219200), Emu(FOOTER_TOP + 45720), Emu(1219200), Emu(228600))
    tf = box.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    r = p.add_run()
    r.text = f"{index:02d} / {total}"
    set_run_font(r, FONT_SIZES["tiny"], "slate_light")


def render(content, diagrams, out_path: Path, here: Path | None = None):
    """渲染整套 PPT。

    页序（共 16 页）：
        1  实景照片封面（本函数内构建，不走 SPEC）
        2  视频占位页（完全放空）
        3+ SPEC_content.json 的 15 页内容（原第 1 页封面已由照片封面取代，跳过）
    返回 (out_path, anim_plan)，anim_plan 供 build_animated.py 写动画用。
    """
    here = here or Path(__file__).resolve().parent
    deck = Deck()
    figs_by_slide = {}
    for f in diagrams.get("figures") or []:
        figs_by_slide.setdefault(f.get("for_slide"), []).append(f)

    slides = [s for s in (content.get("slides") or [])
              if s.get("slide_id") not in ("s01_cover", "s06_video")]
    total = len(slides) + 2
    anim_plan = []

    # ---------- 第 1 页：照片封面 ----------
    cover = add_cover_slide(deck, here)
    anim_plan.append({"kind": "cover", "slide": cover})

    # ---------- 第 2 页：视频占位页（放空，标题/小节沿用原 s06_video 的语义） ----------
    video = add_video_slide(deck, total=total, index=2)
    anim_plan.append({"kind": "video", "slide": video})

    # ---------- 第 3 页起：原有 15 页内容 ----------
    for i, s in enumerate(slides, 3):
        chrome = s.get("chrome", "standard")
        slide = deck.add("bg")
        deco_ids = []

        # 低对比项目元素：网格 + 左侧竖条（standard 页才加，封面/致谢页不抢画面）
        if chrome == "standard":
            add_grid(slide)
            bar = add_side_accent(slide)
            deco_ids.append(bar.shape_id)

        # 图形先画（在下层）
        for f in figs_by_slide.get(s.get("slide_id"), []):
            for el in sorted(f.get("elements") or [], key=lambda e: e.get("z", 0)):
                fn = RENDERERS.get(el.get("type"))
                if fn:
                    fn(slide, el)
        # 页面文本在上层
        dy = TEXT_Y_OFFSET.get(s.get("slide_id"), 0)
        cov = TEXT_COLOR_OVERRIDE.get(s.get("slide_id")) or {}
        for raw in sorted(s.get("elements") or [], key=lambda e: e.get("z", 0)):
            el = raw
            if dy and el.get("type") in ("text", "rect"):
                el = dict(el, y=el.get("y", 0) + dy)
            if cov and el.get("type") == "text" and el.get("color") in cov:
                el = dict(el, color=cov[el["color"]])
            fn = RENDERERS.get(el.get("type"))
            if fn:
                fn(slide, el)

        if chrome == "standard":
            add_chrome(slide, s, i, total)
            # 进度轨道（页脚内），也计入装饰
            add_progress_track(slide, i, total)
        else:
            add_no_chrome_title(slide, s)

        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = str(s["notes"])
        anim_plan.append({"kind": "page", "slide": slide, "slide_id": s.get("slide_id"),
                          "deco": deco_ids})

    deck.save(out_path)
    return out_path, anim_plan


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


def main(argv=None):
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default=str(here / "_spec" / "SPEC_content.json"))
    ap.add_argument("--diagrams", default=str(here / "_spec" / "SPEC_diagrams.json"))
    ap.add_argument("--out", default=str(here / "桥体卫士答辩PPT_12分钟版.pptx"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true", help="有 warning 也视为失败")
    ap.add_argument("--allow-partial", action="store_true",
                    help="只放宽「页数/图形数必须为 15」这项检查，用于管线自测；越界/重叠/溢出仍照查")
    args = ap.parse_args(argv)

    cpath, dpath = Path(args.content), Path(args.diagrams)
    missing = [str(p) for p in (cpath, dpath) if not p.exists()]
    if missing:
        print("缺少输入文件:")
        for m in missing:
            print("  -", m)
        return 2

    content = json.loads(cpath.read_text(encoding="utf-8"))
    diagrams = json.loads(dpath.read_text(encoding="utf-8"))

    print(f"内容页数: {len(content.get('slides') or [])}")
    print(f"图形数  : {len(diagrams.get('figures') or [])}\n")

    rep = Report()
    validate_deck(content, diagrams, rep, expect_full=not args.allow_partial)
    ok = rep.dump()
    if not ok or (args.strict and rep.warnings):
        print("\n校验未通过，未生成 PPTX。")
        return 1
    if args.check:
        print("\n--check 模式：跳过生成。")
        return 0

    out, anim_plan = render(content, diagrams, Path(args.out))
    print(f"\n已生成: {out}")
    print(f"页数: {len(anim_plan) + 0}（1 照片封面 + 1 视频占位 + {len(anim_plan) - 2} 内容页）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
