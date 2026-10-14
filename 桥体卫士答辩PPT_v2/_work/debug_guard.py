# -*- coding: utf-8 -*-
"""debug_guard.py —— 排查"输入已含动画"误报 / 备份覆盖干净基线的问题。"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from pptx import Presentation  # noqa: E402

from pptx_anim import build_slide_has_timing  # noqa: E402

deck = HERE / "桥体卫士答辩PPT_12分钟版.pptx"
preanim = HERE / "_work" / "桥体卫士答辩PPT_12分钟版.preanim.pptx"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


for label, p in (("交付版 deck", deck), ("无动画 preanim", preanim)):
    prs = Presentation(str(p))
    slides = list(prs.slides)
    flags = [build_slide_has_timing(s) for s in slides]
    print(f"{label}: {p}")
    print(f"   sha256[:16]={digest(p)}  大小={p.stat().st_size}")
    print(f"   有 timing 的页数={sum(flags)} / {len(slides)}  首页={flags[0]}  末页={flags[-1]}")

print()
print("二者 sha256 相同（= preanim 已被交付版覆盖）:", digest(deck) == digest(preanim))
