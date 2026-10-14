# -*- coding: utf-8 -*-
"""build_animated.py —— 在原构建之上追加【页面转场 + 点击逐屏触发动画】。

为什么单独一层：
    python-pptx 没有动画 API，转场/动画必须手写 OOXML（见 pptx_anim.py）。
    把它放在构建之后单独跑，好处是 build_deck.py 仍可独立产出"无动画版"，
    出问题能快速二分定位是内容问题还是动画问题。

分组策略（**一次点击 = 一屏内容**，刻意做粗，不做"点一下出一行"）：
    封面    2 次点击：① 照片 + 压暗层 + 竖条   ② 标题 + 副标 + 身份行
    视频页  0 次点击：只做转场，元素不动（用户要自己拖录屏进来）
    内页    2 次点击：① 页眉 + 主体图形 + 卡片 + 正文   ② 页脚与页码
            无页眉页（致谢等）1 次点击：整页一起进
    装饰元素（网格/竖条/进度轨道）不参与动画，始终在场。
    同一次点击内部 0/110/220ms 轻错开：整块出来，但有层次感。

    第一版把每个形状都写成一次点击（元素最多的那页要点 88 次），
    实际用起来就是"点一下出一行"——这次按用户反馈改成逐屏。

用法:
    <bundled-python> build_animated.py [--src deck.pptx] [--out deck_anim.pptx]
"""
from __future__ import annotations

import argparse
import datetime
import shutil
import sys
from pathlib import Path

from pptx import Presentation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from deck_style import build_cover_anim_groups, build_page_groups  # noqa: E402
from pptx_anim import (  # noqa: E402
    build_slide_has_timing,
    count_click_groups,
    set_entrance_sequence,
    set_transition,
)

# 转场：按页类型给不同手感，避免 16 页全是同一种淡入显得单调
TRANSITIONS = {
    "cover": "fade",
    "video": "fade",
    "page": "push",
}
# 少数关键页用别的转场做节奏变化（页号从 1 开始）
SPECIAL_TRANSITION = {6: "wipe", 15: "fade", 16: "fade"}


def decoration_ids_for(slide):
    """识别装饰元素：极窄矩形（竖条/进度格）与全页细线（网格）。

    这些是 deck_style 加的，不参与动画分组；用几何特征识别，不依赖 id 传递。
    """
    ids = set()
    for sh in slide.shapes:
        w = sh.width or 0
        h = sh.height or 0
        # 进度轨道小格 / 左侧竖条：都很窄
        if h and w and (w <= 130000 or h <= 70000):
            ids.add(sh.shape_id)
        # 网格：横跨整页但很细
        if (w >= 12000000 and h <= 20000) or (h >= 6800000 and w <= 20000):
            ids.add(sh.shape_id)
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(HERE / "桥体卫士答辩PPT_12分钟版.pptx"))
    ap.add_argument("--out", default=None,
                    help="默认原地覆盖 --src（先备份到 _work/）")
    args = ap.parse_args()

    src = Path(args.src)
    out = Path(args.out) if args.out else src
    if not src.exists():
        print(f"缺少输入: {src}")
        return 2

    prs = Presentation(str(src))
    slides = list(prs.slides)
    total = len(slides)
    print(f"处理 {total} 页")

    # 输入的每一页都自带 p:timing 吗？（决定备份该叫什么名字）
    src_animated = all(build_slide_has_timing(s) for s in slides)
    if src_animated:
        print("输入文件是【已含动画版】：会先清空旧 p:timing 再重写。")

    # 原地覆盖前先备份。
    # 坑位记录：默认 --src 就是交付版本身（已含动画），这时若仍把备份写成
    # `<名字>.preanim.pptx`，会用"已含动画"的文件覆盖掉真正的无动画基线，
    # 让 build_deck.py 那份干净产物白白丢失。所以按输入状态决定备份名：
    #   输入无动画 -> 覆盖/建立 *.preanim.pptx（干净基线）
    #   输入已含动画 -> 备份成 *.v{时间戳}-animated.pptx，绝不动干净基线
    if out == src:
        if src_animated:
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = HERE / "_work" / f"{src.stem}.{stamp}-animated.pptx"
        else:
            backup = HERE / "_work" / (src.stem + ".preanim.pptx")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, backup)
        print(f"已备份原文件: {backup}")

    report = []
    for idx, slide in enumerate(slides, 1):
        if idx == 1:
            kind = "cover"
            decoration = set()
            click_groups = build_cover_anim_groups(slide, decoration)
        elif idx == 2:
            kind = "video"
            click_groups = []          # 视频页只做转场
        else:
            kind = "page"
            decoration = decoration_ids_for(slide)
            click_groups = build_page_groups(slide, decoration)

        tr = SPECIAL_TRANSITION.get(idx, TRANSITIONS[kind])
        set_transition(slide, tr)
        set_entrance_sequence(slide, click_groups)

        clicks = count_click_groups(slide)
        nshapes = sum(len(shapes) for click in click_groups for _eff, shapes in click)
        report.append((idx, kind, tr, clicks, nshapes))

    prs.save(str(out))
    print(f"\n已生成（含动画）: {out}  ({out.stat().st_size} bytes)\n")
    print(f"{'页':>3} {'类型':<6} {'转场':<6} {'点击次数':>8} {'动效元素':>8}")
    total_clicks = 0
    for idx, kind, tr, clicks, ni in report:
        total_clicks += clicks
        print(f"{idx:>3} {kind:<6} {tr:<6} {clicks:>8} {ni:>8}")
    print(f"\n全套 {total_clicks} 次点击（一次点击放一整屏内容）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
