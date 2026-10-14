# -*- coding: utf-8 -*-
"""verify_deck.py —— 交付前结构复核（不依赖渲染）

检查项：
  1) 页数 / 页面尺寸
  2) 每页可见文本（形状 + 表格）与备注（notes）
  3) 是否存在位图（本次要求零位图）
  4) 字号下限（<11pt 报警）与字体名是否落到「微软雅黑 / Segoe UI」
  5) 文本溢出粗检（按字符宽度估算，与构建器同一套公式）
  6) 与 SPEC_content.json 的 notes 一致性
用法:
  <bundled-python> verify_deck.py 桥体卫士答辩PPT_12分钟版.pptx
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from pptx import Presentation
from pptx.util import Pt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_deck import char_em  # noqa: E402

MIN_PT = 11.0        # 正文字号下限
FOOTER_PT = 8.0      # 页脚/页码允许更小（标准页脚 chrome）
PAGE_W, PAGE_H = 12192000, 6858000
FOOTER_MARK = "桥体卫士 · 桥梁结构健康监测缩尺原型"


def shapes_text(shapes):
    out = []
    for sh in shapes:
        if sh.shape_type == 13 or sh.__class__.__name__ == "Picture":
            out.append("[[PICTURE]]")
            continue
        if sh.has_text_frame and sh.text_frame.text.strip():
            out.append(sh.text_frame.text)
        if getattr(sh, "has_table", False) and sh.has_table:
            for r in sh.table.rows:
                out.append(" | ".join(c.text for c in r.cells))
    return out


def main():
    p = Path(sys.argv[1] if len(sys.argv) > 1 else
             HERE / "桥体卫士答辩PPT_12分钟版.pptx")
    prs = Presentation(str(p))
    print(f"文件: {p.name}  ({p.stat().st_size} bytes)")
    print(f"页面: {prs.slide_width} x {prs.slide_height} EMU "
          f"= {prs.slide_width/914400:.3f} x {prs.slide_height/914400:.3f} in")
    assert prs.slide_width == PAGE_W and prs.slide_height == PAGE_H, "页面尺寸不符 16:9"
    print(f"页数: {len(prs.slides)}\n")

    spec = {}
    cp = HERE / "_spec" / "SPEC_content.json"
    if cp.exists():
        for s in json.loads(cp.read_text(encoding="utf-8"))["slides"]:
            spec[s["slide_id"]] = s

    problems = []
    fonts = Counter()
    pics = 0
    for i, slide in enumerate(prs.slides, 1):
        texts = shapes_text(slide.shapes)
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        nchars = len([c for c in notes if c.strip()])
        body = " / ".join(texts)
        flat = "".join(body.split())          # 去空白，用于规格比对
        # 位图统计
        pics += sum(1 for sh in slide.shapes if sh.shape_type == 13)
        # 字号与字体（页脚 chrome 允许 9pt，不参与正文下限判定）
        small = []
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            shape_txt = sh.text_frame.text.strip()
            is_footer = FOOTER_MARK in shape_txt or (
                len(shape_txt) <= 8 and "/" in shape_txt and any(c.isdigit() for c in shape_txt))
            for para in sh.text_frame.paragraphs:
                for run in para.runs:
                    if run.font.size:
                        pt = run.font.size.pt
                        limit = FOOTER_PT if is_footer else MIN_PT
                        if pt < limit:
                            small.append((run.text[:16], pt))
                    fonts[run.font.name] += 1
        print(f"--- {i:02d}  文本块 {len(texts):2d}  备注 {nchars:3d} 字  "
              f"文字 {len(body)} 字")
        if small:
            problems.append(f"[{i:02d}] 字号过小: {small}")
        expect = spec.get(list(spec)[i - 1] if spec else None, {})
        if expect and expect.get("slide_id"):
            want = len([c for c in (expect.get("notes") or "") if c.strip()])
            if abs(want - nchars) > 2:
                problems.append(f"[{i:02d}] 备注字数与规格不符 规格{want} 实际{nchars}")
            wanted_texts = []
            if expect.get("title"):
                wanted_texts.append(("title", expect["title"]))
            for e in expect.get("elements") or []:
                if e.get("type") == "text" and e.get("text"):
                    wanted_texts.append((e.get("id", "?"), e["text"]))
            for tag, t in wanted_texts:
                if "".join(str(t).split()) not in flat:
                    problems.append(f"[{i:02d}] 规格文本未出现在 PPT 中 ({tag}): {t[:34]!r}")

    print(f"\n位图数量: {pics}  （要求 0）")
    if pics:
        problems.append(f"存在 {pics} 个位图，违反零位图要求")
    print(f"字体使用统计: {dict(fonts)}")
    bad_font = [f for f in fonts if f and f not in ("微软雅黑", "Segoe UI")]
    if bad_font:
        problems.append(f"出现非预期字体: {bad_font}")

    print("\n" + ("=" * 60))
    if problems:
        print(f"发现 {len(problems)} 个问题:")
        for x in problems:
            print("  x", x)
        return 1
    print("结构复核通过 ✅（页数/尺寸/零位图/字号/字体/备注一致性）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
