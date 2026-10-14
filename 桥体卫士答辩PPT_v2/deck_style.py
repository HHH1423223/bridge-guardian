# -*- coding: utf-8 -*-
"""deck_style.py —— 页面视觉增强与动画编排。

A) 视觉增强（"不能太素、也不能太花哨"）
   内页统一加三样低对比项目元素，刻意压低存在感，只提供"工程感"底子，不抢内容：
     1. 极淡网格纹理（模拟结构工程图纸，alpha 5%）
     2. 左侧 teal 竖标记（与封面竖条呼应）
     3. 页脚右侧的「进度轨道」：16 段小格，当前页高亮 —— 既是页码也是进度条

B) 动画编排（点击逐"屏"触发，一次点击 = 一大块内容）
   刻意做粗，不做"点一下出一行"：
     封面   2 次点击：① 照片 + 压暗层 + 竖条  ② 标题 / 副标 / 身份行（几乎同时）
     视频页 0 次点击：只有转场，元素不动（用户自己拖录屏进来，免得打架）
     内页   2 次点击：① 页眉 + 主体图形 + 卡片 + 正文  ② 页脚与页码
     无页眉页（致谢等）1 次点击：整页内容一起进
   每次点击内部用 STAGGER_MS 做 0/110/220ms 的轻微错开——看起来是一块内容一起出来，
   但有层次感，不会"啪"地糊成一片。
"""

from __future__ import annotations

from lxml import etree
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

PAGE_W, PAGE_H = 12192000, 6858000
MARGIN_X, CONTENT_RIGHT = 685800, 11506200
CHROME_H, FOOTER_TOP = 1005840, 6126480
TEAL = "00B3A4"
LINE = "D8E0EA"


def _set_alpha(color_el, alpha_pct):
    a = etree.SubElement(color_el, qn("a:alpha"))
    a.set("val", str(int(alpha_pct * 1000)))


def _no_line(shape):
    shape.line.fill.background()
    shape.shadow.inherit = False


def _fade_line(conn, alpha):
    """给线条加透明度（python-pptx 无 API，手工写 a:alpha），并关掉默认阴影。

    坑位记录：连接线默认带阴影，网格密集时阴影叠加会在页脚处形成一根灰带；
    必须 shadow.inherit = False。
    """
    conn.shadow.inherit = False
    ln = conn.line._get_or_add_ln()
    solid = ln.find(qn("a:solidFill"))
    if solid is not None:
        clr = solid.find(qn("a:srgbClr"))
        if clr is not None:
            _set_alpha(clr, alpha)


def add_grid(slide, step=609600, alpha=5, y_max=6035040):
    """极淡网格纹理：模拟结构工程图纸底纹（5% 透明度，只在近看时有质感）。

    只画到内容下界（6035040），不侵入页脚带——否则网格线横穿页脚会显得脏。
    """
    for x in range(step, PAGE_W, step):
        ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x), 0, Emu(x), Emu(y_max))
        ln.line.color.rgb = RGBColor.from_string(LINE)
        ln.line.width = Pt(0.5)
        _fade_line(ln, alpha)
    for y in range(step, y_max, step):
        ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, Emu(y), Emu(PAGE_W), Emu(y))
        ln.line.color.rgb = RGBColor.from_string(LINE)
        ln.line.width = Pt(0.5)
        _fade_line(ln, alpha)


def add_side_accent(slide):
    """左侧 teal 竖标记：与封面竖条呼应，给内页统一的家族记认。

    下移到 y=CHROME_H+182880：实测贴在分隔线下方会压住标题基线下沿（"为什么做这件事"的撇）。
    """
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(MARGIN_X), Emu(CHROME_H + 182880),
                                 Emu(45720), Emu(548640))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor.from_string(TEAL)
    _no_line(bar)
    return bar


def add_progress_track(slide, index, total=16, seg_w=118872, seg_h=59436, gap=36576,
                       right_limit=10183680):
    """页脚右侧进度轨道：total 段小格，当前页高亮。

    right_limit 默认 10241280，给页码文字（'NN / 16'，右对齐到 CONTENT_RIGHT）留出空间——
    实测把轨道一直铺到 CONTENT_RIGHT 会压住页码。
    """
    total_w = total * seg_w + (total - 1) * gap
    x0 = right_limit - total_w
    y = FOOTER_TOP + 155448
    for i in range(1, total + 1):
        x = x0 + (i - 1) * (seg_w + gap)
        seg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(x), Emu(y), Emu(seg_w), Emu(seg_h))
        seg.fill.solid()
        seg.fill.fore_color.rgb = RGBColor.from_string(TEAL if i == index else LINE)
        _no_line(seg)
    return x0


# --------------------------------------------------------------------------
# 动画分组
# --------------------------------------------------------------------------

def _is_picture(sh):
    return "PICTURE" in str(sh.shape_type) or (sh.width or 0) >= 6000000


def build_cover_anim_groups(slide, decoration_ids=()):
    """封面：**2 次点击**。

    点击 1：照片 + 渐变压暗层 + 左侧竖条 —— 背景整块到位；
    点击 2：标题 + 副标题 + 身份行 —— 文字整块到位（内部 0/110/220ms 轻错开）。

    纯背景底板（铺满整页的底色矩形）不参与动画：始终在场，
    免得翻到封面先看到一片空白。
    """
    deco = set(decoration_ids)
    visual, detail, texts = [], [], []
    for sh in slide.shapes:
        if (sh.width or 0) == PAGE_W and (sh.height or 0) == PAGE_H:
            continue                       # 纯色底板：常驻
        if sh.shape_id in deco:
            continue
        has_text = bool(sh.text_frame.text.strip()) if sh.has_text_frame else False
        if has_text:
            texts.append(sh)
        elif _is_picture(sh):
            visual.append(sh)
        elif (sh.height or 0) >= PAGE_H // 2:
            visual.append(sh)              # 下半页渐变压暗层
        else:
            detail.append(sh)              # 左侧 teal 竖条等

    return [
        [("fade", visual), ("fade", detail)],
        [("rise", texts)],
    ]


def build_page_groups(slide, decoration_ids=()):
    """内页：**2 次点击**（无页眉页时 1 次）。

    点击 1：页眉（小节标签 + 页标题）+ 主体图形 + 卡片 + 正文文字 —— 整页主体一次到位；
    点击 2：页脚带（页脚文字 / 页码 / 内容底部分隔线）。

    装饰元素（网格 / 左侧竖条 / 进度轨道）不参与动画，始终在场。
    用户明确要"粗略一点"，所以这里刻意不再按段落/逐行切分：
    一页最多两次点击，第二次只是收个尾。
    """
    deco = set(decoration_ids)
    header, body, tail = [], [], []
    for sh in slide.shapes:
        if sh.shape_id in deco:
            continue
        top = sh.top or 0
        has_text = sh.text_frame.text.strip() if sh.has_text_frame else ""
        if top >= FOOTER_TOP:
            tail.append(sh)
        elif has_text and top < CHROME_H:
            header.append(sh)
        else:
            body.append(sh)

    click1 = []
    if header:
        click1.append(("fade", header))
    if body:
        click1.append(("rise", body))
    click2 = [("fade", tail)] if tail else []
    return [g for g in (click1, click2) if g]
