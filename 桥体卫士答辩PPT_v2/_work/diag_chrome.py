# -*- coding: utf-8 -*-
"""诊断：standard 页中，各图形元素在页眉条带 (y < 1005840) 的 x 占用，
以及标题所需宽度。用于决定页眉标题列的安全宽度。"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from build_deck import (  # noqa: E402
    CHROME_H, CONTENT_RIGHT, FONT_SIZES, MARGIN_X, PT, text_em,
)

spec = json.loads((HERE / "_spec" / "SPEC_content.json").read_text(encoding="utf-8"))
figs = json.loads((HERE / "_spec" / "SPEC_diagrams.json").read_text(encoding="utf-8"))
chrome = {s["slide_id"]: s.get("chrome", "standard") for s in spec["slides"]}

print("=== 一、页眉条带（y < 1005840）内图形元素的 x 占用 ===")
max_x = 0
for f in figs["figures"]:
    sid = f["for_slide"]
    if chrome.get(sid) == "none":
        continue
    hits = []
    for el in f["elements"]:
        if el.get("type") == "line":
            ys = [p[1] for p in el.get("points") or []]
            xs = [p[0] for p in el.get("points") or []]
            if ys and min(ys) < CHROME_H:
                hits.append((el["id"], min(xs), max(xs)))
            continue
        y, h = el.get("y", 0), el.get("h", 0)
        if y < CHROME_H:
            hits.append((el["id"], el.get("x", 0), el.get("x", 0) + el.get("w", 0)))
    if hits:
        hi = max(h[2] for h in hits)
        max_x = max(max_x, hi)
        print(f"  {sid:13s} {f['fig_id']:14s} 占用到 x={hi:>9d}  "
              f"({len(hits)} 个: {', '.join(h[0] for h in hits[:6])})")
print(f"\n  条带内图形最大右边界: x={max_x} → 标题列最大可用右边界建议 ≤ {max_x - 137160}")

print("\n=== 二、各页标题宽度需求（h1 = 27pt, 粗体） ===")
need = 0
for s in spec["slides"]:
    if chrome.get(s["slide_id"]) == "none":
        continue
    t = s.get("title") or ""
    w = int(text_em(t) * FONT_SIZES["h1"] * PT * 1.12) + 91500  # 粗体 + 安全余量
    need = max(need, w)
    avail = CONTENT_RIGHT - MARGIN_X
    print(f"  {s['slide_id']:13s} {t[:34]:36s} 需要 {w:>8d} EMU ({w/914400:.2f}in)")
print(f"\n  标题最大需求: {need} EMU ({need/914400:.2f}in)")
print(f"  当前 CHROME_TITLE_W = 4314200（{4314200/914400:.2f}in）→ "
      f"{'不足 ❌' if need > 4314200 else '够 ✅'}")
print(f"\n  建议: 标题列宽取 {max(need, 6000000)} EMU，"
      f"则页眉可延伸到 x={MARGIN_X + max(need, 6000000)}")
