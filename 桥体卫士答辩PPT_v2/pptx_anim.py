# -*- coding: utf-8 -*-
"""pptx_anim.py —— 给 python-pptx 生成的幻灯片注入转场与入场动画（原生 OOXML）。

为什么需要这个模块：
    python-pptx 1.0.2 没有任何动画/切换 API（枚举里只有 action/base/chart/dml/lang/shapes/text）。
    要实现"每页有动效"，只能手工往 slide XML 里写 <p:transition> 与 <p:timing>。

写入的 XML 结构（已按 ECMA-376 的 CT_SlideTiming / CT_TimeNodeList 组织）。

⚠️ 关键教训（本文件第二次改写的起因）：mainSeq 下【顶层 par 的个数 = 需要点击的次数】。
第一版把"每个形状"都写成一个顶层 par，于是 52 个形状的页面要点 52 次鼠标，
实测用户反馈就是"点一下出一行"。正确做法是【一个点击组 = 一个顶层 par】：

    <p:transition spd="med"><p:fade/></p:transition>        # 页面切换
    <p:timing>
      <p:tnLst>
        <p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
          <p:childTnLst>
            <p:seq concurrent="1" nextAc="seek">              # 主时间线序列
              <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                <p:childTnLst>
                  <p:par>                                     # ① 点击组 1（= 第 1 次点击）
                    <p:cTn id="3" fill="hold">
                      <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                      <p:childTnLst>
                        <p:par>
                          <p:cTn id="4" fill="hold">
                            <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                            <p:childTnLst>
                              <p:par>                             # 组内第 1 个形状：锚点
                                <p:cTn id="5" presetID="22" presetClass="entr" nodeType="clickEffect">
                                  <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                                  <p:childTnLst>
                                    <p:set/> <p:animEffect/>
                                    <p:par>                       # 组内第 2 个形状：跟随
                                      <p:cTn id="9" presetID="22" presetClass="entr"
                                             nodeType="afterEffect">
                                        <p:stCondLst><p:cond delay="110"/></p:stCondLst>
                                        <p:childTnLst>
                                          <p:set/> <p:animEffect/>
                                          <p:par> ... 第 3 个形状 ... </p:par>
                                        </p:childTnLst>
                                      </p:cTn>
                                    </p:par>
                                  </p:childTnLst>
                                </p:cTn>
                              </p:par>
                            </p:childTnLst>
                          </p:cTn>
                        </p:par>
                      </p:childTnLst>
                    </p:cTn>
                  </p:par>
                  <p:par> ... 点击组 2 ... </p:par>
                </p:childTnLst>
              </p:cTn>
              <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
              <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
            </p:seq>
          </p:childTnLst>
        </p:cTn></p:par>
      </p:tnLst>
    </p:timing>

组内 shape 依次嵌套（每个形状挂在上一个形状的 childTnLst 里），delay 用
STAGGER_MS 铺开，用户只按一次鼠标就看到"一大块内容"一起进场，而不是一行一行蹦。

支持的效果（都基于 entr 类）：
    fade       presetID 10  淡入
    rise       presetID 22  上浮淡入（presetSubtype 4 = from bottom）
    wipe       presetID 22  擦除（presetSubtype 8 = from left）
    zoom       presetID 23  缩放淡入
    float      presetID 26  轻微浮动进入

用法：
    from pptx_anim import set_transition, set_entrance_sequence
    set_transition(slide, "fade")
    # click_groups: [[(effect_kind, [shape, ...]), ...], ...]
    #   外层 list   = 点击次数（点一次放一组）
    #   内层 list   = 同一次点击里一起进场的若干组（按顺序微错开）
    set_entrance_sequence(slide, [[("fade", [photo, veil]), ("fade", [bar])],
                                  [("rise", [title, subtitle, identity])]])
"""

from __future__ import annotations

from pptx.oxml.ns import qn
from lxml import etree

NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

# 同一次点击内，形状之间错开的毫秒数（视觉上仍是"一起出来"，只是有轻微层次感）。
# 想更硬朗（完全同时）就把最后一个元素改成 0。
STAGGER_MS = (0, 110, 220, 330, 440, 550, 660, 770)
# 同一屏里"组与组"之间的错开步长（例如内页：页眉先出、主体紧跟着铺开）
STAGGER_SPAN = 220

_EFFECTS = {
    # name: (presetID, presetClass, presetSubtype, extra_filter)
    "fade": (10, "entr", 0, "fade"),
    "rise": (22, "entr", 4, "fade"),
    "wipe": (22, "entr", 8, "wipe(left)"),
    "zoom": (23, "entr", 16, "fade"),
    "float": (26, "entr", 0, "fade"),
}


def set_ea_font(run, font_cn="微软雅黑", font_en="Segoe UI"):
    """显式设置中文字体（eastAsia）。

    坑位记录：只设 run.font.name（= a:latin）对中文无效；而用
    `etree.SubElement(rPr, qn("a:ea"))` 建一个空 a:ea 同样无效——必须给
    a:ea 设 typeface，否则中文会落回 Segoe UI（实测"桥体卫士"的"卫"字被压扁）。
    """
    rPr = run._r.get_or_add_rPr()
    for tag, face in (("a:latin", font_en), ("a:ea", font_cn), ("a:cs", font_en)):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", face)
    return run


def _sub(parent, tag, **attrs):
    el = etree.SubElement(parent, qn(tag))
    for k, v in attrs.items():
        el.set(k, str(v))
    return el


def _insert_ordered(sld, el, before_tags):
    """按 OOXML schema 顺序插入 el：放到第一个属于 before_tags 的元素之前，否则追加。

    p:sld 的子元素顺序是固定的：
      cSld, clrMapOvr, transition, timing, extLst
    用 SubElement 直接 append 会插到 clrMapOvr 之前（位置非法），PowerPoint 可能报"需要修复"。
    """
    for child in sld:
        if child.tag in before_tags:
            child.addprevious(el)
            return el
    sld.append(el)
    return el


def set_transition(slide, kind="fade", speed="med"):
    """写入页面切换。kind: fade | push | wipe | cover | none"""
    sld = slide._element
    for old in sld.findall(qn("p:transition")):
        sld.remove(old)
    if kind == "none":
        return
    tr = etree.Element(qn("p:transition"))
    tr.set("spd", speed)
    if kind == "fade":
        etree.SubElement(tr, qn("p:fade"))
    elif kind == "push":
        el = etree.SubElement(tr, qn("p:push"))
        el.set("dir", "u")
    elif kind == "wipe":
        el = etree.SubElement(tr, qn("p:wipe"))
        el.set("dir", "l")
    elif kind == "cover":
        el = etree.SubElement(tr, qn("p:cover"))
        el.set("dir", "l")
    _insert_ordered(sld, tr, before_tags={qn("p:timing"), qn("p:extLst")})


def _effect_children(parent, ids, shape_id, kind, dur=500):
    """在 parent（某个效果的 childTnLst）里写入 set + animEffect。

    set 先把形状置为可见（进入动画必须，否则动画播完形状仍是隐藏的），
    再由 animEffect 做淡入/擦除/缩放。

    坑位记录：p:set / p:animEffect 的 cBhvr 里那个 cTn 不加 delay——
    "延迟"只认时序树上的 stCondLst，写在这里会被忽略甚至让 PowerPoint 困惑。
    """
    preset_id, preset_class, subtype, filt = _EFFECTS.get(kind, _EFFECTS["fade"])

    setel = _sub(parent, "p:set")
    cbhvr = _sub(setel, "p:cBhvr")
    _sub(cbhvr, "p:cTn", id=ids[0], dur=1, fill="hold")
    ids[0] += 1
    tgt = _sub(cbhvr, "p:tgtEl")
    _sub(tgt, "p:spTgt", spid=shape_id)
    attr = _sub(cbhvr, "p:attrNameLst")
    _sub(attr, "p:attrName").text = "style.visibility"
    to = _sub(setel, "p:to")
    _sub(to, "p:strVal", val="visible")

    anim = _sub(parent, "p:animEffect", transition="in", filter=filt)
    cbhvr2 = _sub(anim, "p:cBhvr")
    _sub(cbhvr2, "p:cTn", id=ids[0], dur=dur)
    ids[0] += 1
    tgt2 = _sub(cbhvr2, "p:tgtEl")
    _sub(tgt2, "p:spTgt", spid=shape_id)


def _group_tree(parent, ids, items, anchor_type="clickEffect"):
    """把「同一次点击里的所有形状」写进 parent，返回最外层 cTn。

    结构是 **3 层嵌套 + 组内平铺**：

        par -> cTn(nodeType=clickEffect)          # 第 1 个形状 = 点击锚点
                 -> childTnLst
                      par -> cTn(nodeType=afterEffect) -> childTnLst -> set/animEffect
                      par -> cTn(nodeType=afterEffect) -> childTnLst -> set/animEffect
                      ...

    为什么不把一个形状嵌进上一个形状的 childTnLst：
      那样 XML 深度随形状数线性增长，88 个元素的页面深度接近 200 层，
      PowerPoint / libxml2 会直接报 "Excessive depth in document: 256"
      （实测 python-pptx 打不开自己刚写出的文件）。现在深度固定 3 层，
      全 deck 最深 XML 深度 22 层。

    为什么 afterEffect 能算"同一次点击"：
      mainSeq 只按【顶层 par 的个数】计点击次数（第一个顶层 par 里那个
      clickEffect 消费掉这一次点击）。剩余 afterEffect 都挂在这个锚点的
      childTnLst 里，只按 stCondLst 的 delay 依次播放，不再消费点击。
      实测：本文件 52~88 个元素的页面都只需要点 2 次。
    """
    if not items:
        return None
    first = True
    anchor_ctn = None
    for shape_id, kind, delay in items:
        preset_id, preset_class, subtype, _filt = _EFFECTS.get(kind, _EFFECTS["fade"])
        par = _sub(parent, "p:par")
        attrs = {"id": ids[0], "presetID": preset_id, "presetClass": preset_class,
                 "presetSubtype": subtype, "fill": "hold", "grpId": 0,
                 "nodeType": anchor_type if first else "afterEffect"}
        ctn = _sub(par, "p:cTn", **attrs)
        ids[0] += 1
        st = _sub(ctn, "p:stCondLst")
        _sub(st, "p:cond", delay=delay)
        child = _sub(ctn, "p:childTnLst")
        _effect_children(child, ids, shape_id, kind)
        if first:
            anchor_ctn = ctn
            first = False
    return anchor_ctn


def set_entrance_sequence(slide, click_groups):
    """写入点击触发的入场动画。

    click_groups: 外层 list 的每一项 = 一次点击，形如
        [(effect_kind, [shape, ...]), ...]
      同一次点击里的多个组按组顺序继续错开（第一个组 0ms，第二组 +220ms…），
      所以"一次点击 = 一屏内容一起出现"，不是一行一行蹦。

    传空 list / 全空 = 只保留转场，不写 p:timing。
    """
    sld = slide._element
    for old in sld.findall(qn("p:timing")):
        sld.remove(old)

    # 展开成 [(shape_id, kind, delay_ms), ...]，并丢掉空组
    groups = []
    for click in click_groups or []:
        items = []
        seq_i = 0
        for kind, shapes in click:
            for sh in shapes:
                items.append((sh.shape_id, kind, int(STAGGER_MS[seq_i % len(STAGGER_MS)])))
                seq_i += 1
        if items:
            groups.append(items)
    if not groups:
        return

    timing = etree.Element(qn("p:timing"))
    tnLst = _sub(timing, "p:tnLst")
    par = _sub(tnLst, "p:par")
    root = _sub(par, "p:cTn", id=1, dur="indefinite", restart="never", nodeType="tmRoot")
    root_child = _sub(root, "p:childTnLst")

    seq = _sub(root_child, "p:seq", concurrent=1, nextAc="seek")
    seq_ctn = _sub(seq, "p:cTn", id=2, dur="indefinite", nodeType="mainSeq")
    seq_child = _sub(seq_ctn, "p:childTnLst")

    ids = [3]
    for items in groups:
        # 每次点击一个顶层 par：外层 cTn 只负责"等这次点击"，内层才挂动画。
        click_par = _sub(seq_child, "p:par")
        click_ctn = _sub(click_par, "p:cTn", id=ids[0], fill="hold")
        ids[0] += 1
        st = _sub(click_ctn, "p:stCondLst")
        _sub(st, "p:cond", delay=0)
        click_child = _sub(click_ctn, "p:childTnLst")

        holder_par = _sub(click_child, "p:par")
        holder_ctn = _sub(holder_par, "p:cTn", id=ids[0], fill="hold")
        ids[0] += 1
        st2 = _sub(holder_ctn, "p:stCondLst")
        _sub(st2, "p:cond", delay=0)
        holder_child = _sub(holder_ctn, "p:childTnLst")

        # 组内形状：第一个是 clickEffect 锚点（等用户点这一下），其余 afterEffect 跟随
        _group_tree(holder_child, ids, items, anchor_type="clickEffect")

    prev = _sub(seq, "p:prevCondLst")
    c1 = _sub(prev, "p:cond", evt="onPrev", delay=0)
    t1 = _sub(c1, "p:tgtEl")
    _sub(t1, "p:sldTgt")
    nxt = _sub(seq, "p:nextCondLst")
    c2 = _sub(nxt, "p:cond", evt="onNext", delay=0)
    t2 = _sub(c2, "p:tgtEl")
    _sub(t2, "p:sldTgt")

    _insert_ordered(sld, timing, before_tags={qn("p:extLst")})


def build_slide_has_timing(slide):
    """该页是否已经有元素动画（用来判断输入文件是不是"已含动画版"）。"""
    return slide._element.find(qn("p:timing")) is not None


def count_click_groups(slide):
    """返回该页需要点击的次数（顶层 par 数），供构建期自检。"""
    sld = slide._element
    timing = sld.find(qn("p:timing"))
    if timing is None:
        return 0
    main = timing.find(qn("p:tnLst") + "/" + qn("p:par") + "/" + qn("p:cTn") +
                       "/" + qn("p:childTnLst") + "/" + qn("p:seq") + "/" + qn("p:cTn"))
    if main is None:
        return 0
    child = main.find(qn("p:childTnLst"))
    if child is None:
        return 0
    return len(child.findall(qn("p:par")))

