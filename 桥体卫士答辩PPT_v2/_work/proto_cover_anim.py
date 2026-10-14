# -*- coding: utf-8 -*-
"""proto_cover_anim.py —— 最小原型验证两件事：

  1) 封面：实景照片铺满 + 底部渐变压暗（保证任何投影仪下文字都读得清）；
     渐变用「图片向下溢出页面 + 半透明矩形」实现，避免直接给图片做渐变裁切。
  2) 动画：p:transition + p:timing 能否被 PPTX 结构校验与 LibreOffice 接受。

产物写到 _work/proto/，不动正式 PPTX。
"""
from __future__ import annotations

import copy
import pathlib
import sys

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from pptx_anim import (  # noqa: E402
    set_ea_font,
    set_entrance_sequence,
    set_transition,
)

PAGE_W, PAGE_H = 12192000, 6858000
OUT = HERE / "_work" / "proto"
OUT.mkdir(parents=True, exist_ok=True)
PHOTO = HERE / "assets" / "封面_花江峡谷大桥.png"


def set_alpha(shape, alpha_pct):
    """给纯色填充加透明度（python-pptx 没有 alpha API，手工写 a:alpha）。"""
    solidFill = shape.fill._xPr.find(qn("a:solidFill"))
    clr = solidFill.find(qn("a:srgbClr"))
    alpha = etree.SubElement(clr, qn("a:alpha"))
    alpha.set("val", str(int(alpha_pct * 1000)))  # 0–100000


def set_gradient(shape, stops):
    """stops: [(pos0_1, 'RRGGBB', alpha0_1), ...]  —— 手工构造 a:gradFill。"""
    spPr = shape._element.spPr
    for tag in ("a:solidFill", "a:noFill", "a:gradFill", "a:blipFill", "a:pattFill"):
        el = spPr.find(qn(tag))
        if el is not None:
            spPr.remove(el)
    grad = etree.SubElement(spPr, qn("a:gradFill"))
    grad.set("rotWithShape", "1")
    gsLst = etree.SubElement(grad, qn("a:gsLst"))
    for pos, color, alpha in stops:
        gs = etree.SubElement(gsLst, qn("a:gs"))
        gs.set("pos", str(int(pos * 100000)))
        clr = etree.SubElement(gs, qn("a:srgbClr"))
        clr.set("val", color)
        if alpha < 1.0:
            a = etree.SubElement(clr, qn("a:alpha"))
            a.set("val", str(int(alpha * 100000)))
    lin = etree.SubElement(grad, qn("a:lin"))
    lin.set("ang", "5400000")   # 90° = 从上到下
    lin.set("scaled", "0")
    # 顺序：fill 必须在 a:ln 之前
    ln = spPr.find(qn("a:ln"))
    if ln is not None:
        ln.addprevious(grad)


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(PAGE_W), Emu(PAGE_H)
    blank = prs.slide_layouts[6]

    # ---------- 第 1 页：照片封面 ----------
    s = prs.slides.add_slide(blank)
    # 底色（照片未覆盖处兜底）
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PAGE_W, PAGE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor.from_string("0B1B2B")
    bg.line.fill.background()
    bg.shadow.inherit = False

    # 照片：铺满整页（16:9 正好，无需裁切）
    pic = s.shapes.add_picture(str(PHOTO), 0, 0, width=Emu(PAGE_W), height=Emu(PAGE_H))

    # 底部渐变压暗：从 42% 高度处透明 → 底部 78% 不透明，中间过渡
    veil = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, int(PAGE_H * 0.40),
                              PAGE_W, int(PAGE_H * 0.60))
    veil.line.fill.background()
    veil.shadow.inherit = False
    set_gradient(veil, [
        (0.00, "0B1B2B", 0.00),
        (0.45, "0B1B2B", 0.62),
        (1.00, "0B1B2B", 0.92),
    ])

    # 左侧竖条 + 标题 + 副标
    # 版式实测修正：60pt 以上的行盒高度≈字号×1.5，原先把标题基线放太高会与副标重叠，
    # 因此标题框上移、副标与标题留出 2 个空行高度。
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(685800), Emu(3429000),
                             Emu(91440), Emu(2514600))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor.from_string("00B3A4")
    bar.line.fill.background()
    bar.shadow.inherit = False

    tb = s.shapes.add_textbox(Emu(1028700), Emu(3300000), Emu(8001000), Emu(1143000))
    tb.text_frame.word_wrap = False
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = "桥体卫士"
    r.font.size = Pt(66)
    r.font.bold = True
    r.font.color.rgb = RGBColor.from_string("FFFFFF")
    set_ea_font(r)

    sb = s.shapes.add_textbox(Emu(1066800), Emu(4600000), Emu(8001000), Emu(400000))
    sb.text_frame.word_wrap = False
    p2 = sb.text_frame.paragraphs[0]
    r2 = p2.add_run()
    r2.text = "桥梁结构健康监测缩尺原型 · 三维可视化监测场景"
    r2.font.size = Pt(20)
    r2.font.color.rgb = RGBColor.from_string("E6EEF8")
    set_ea_font(r2)

    tb3 = s.shapes.add_textbox(Emu(1066800), Emu(5050000), Emu(8001000), Emu(340000))
    tb3.text_frame.word_wrap = False
    p3 = tb3.text_frame.paragraphs[0]
    r3 = p3.add_run()
    r3.text = "软件技术专业 · 缩尺桥梁模型受载变化模拟 · 单人主讲"
    r3.font.size = Pt(13)
    r3.font.color.rgb = RGBColor.from_string("AFC3D8")
    set_ea_font(r3)

    ids = [sh.shape_id for sh in s.shapes]
    print("  封面 shape_id:", ids)
    set_transition(s, "fade")
    # 新版 API：外层 = 点击次数，内层 = 同一次点击里一起进场的组
    set_entrance_sequence(s, [
        [("fade", [s.shapes[0], s.shapes[1], s.shapes[2]])],
        [("fade", [s.shapes[3]]), ("rise", [s.shapes[4], s.shapes[5], s.shapes[6]])],
    ])

    # ---------- 第 2 页：验证分组动画 ----------
    s2 = prs.slides.add_slide(blank)
    a = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(1000000), Emu(1000000),
                            Emu(3000000), Emu(1000000))
    a.fill.solid(); a.fill.fore_color.rgb = RGBColor.from_string("E8F0FA"); a.line.fill.background()
    b = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(5000000), Emu(3000000),
                            Emu(3000000), Emu(1000000))
    b.fill.solid(); b.fill.fore_color.rgb = RGBColor.from_string("E0F7F5"); b.line.fill.background()
    c = s2.shapes.add_textbox(Emu(1000000), Emu(5000000), Emu(5000000), Emu(500000))
    c.text_frame.text = "第三组：文字"
    set_transition(s2, "push")
    set_entrance_sequence(s2, [
        [("wipe", [a])],
        [("rise", [b]), ("fade", [c])],
    ])

    out = OUT / "proto.pptx"
    prs.save(str(out))
    return out


if __name__ == "__main__":
    p = build()
    print(f"\n已生成原型: {p}  ({p.stat().st_size} bytes)")
