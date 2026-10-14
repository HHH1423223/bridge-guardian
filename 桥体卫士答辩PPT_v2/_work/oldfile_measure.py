# -*- coding: utf-8 -*-
"""判定实验：拿旧 PPT（已知几何，渲染正常）做精确测量，
比较「1.5x 放大」是否也发生在旧文件上。"""
import pathlib
import re
import subprocess
import zipfile
from xml.etree import ElementTree as ET

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NODE = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
CLI = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
IN = 914400


def shapes(pptx, page=1):
    with zipfile.ZipFile(pptx) as z:
        root = ET.fromstring(z.read(f"ppt/slides/slide{page}.xml"))
    out = []
    for sp in root.iter(f"{P}sp"):
        xf = sp.find(f".//{A}xfrm")
        if xf is None:
            continue
        off, ext = xf.find(f"{A}off"), xf.find(f"{A}ext")
        fill = sp.find(f".//{A}solidFill/{A}srgbClr")
        txt = "".join(t.text or "" for t in sp.iter(f"{A}t"))
        out.append((int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy")),
                    fill.get("val") if fill is not None else None, txt))
    return out


old = ROOT / "桥体卫士答辩PPT" / "桥体卫士答辩PPT.pptx"
png = sorted((HERE / "cmp_old").glob("*.png"))[0]
im = Image.open(png).convert("RGB")
W, H = im.size
px = im.load()
scale = W / 13.3333
print(f"旧 PPT 渲染 {W}x{H}，1in = {scale:.1f}px（若按 13.333in 宽换算）\n")
print("旧文件第 1 页形状（EMU → in）与实测：")

for x, y, w, h, fill, txt in shapes(old)[:9]:
    line = (f"  x={x/IN:6.3f}in y={y/IN:6.3f}in w={w/IN:6.3f} h={h/IN:6.3f} "
            f"fill={fill} text={txt[:18]!r}")
    print(line)

# 实测：桥体卫士标题块 fill=0E3F8C 与顶部蓝带同色，会互相干扰，
# 因此改用「顶部蓝带的下边界」来判定 y 是否被放大。
# 顶部蓝带: x=381000/914400=0.4167in, y=0, w=12.5in, h=1.875in
band_h_in = 1714500 / IN
print(f"\n顶部蓝带规格: x=0.417in y=0 h={band_h_in:.3f}in")
print(f"  若 1:1 渲染，带底应在 y={band_h_in*scale:.0f}px")
print(f"  若 1.5x 渲染，带底应在 y={band_h_in*1.5*scale:.0f}px")

navy = (0x0E, 0x3F, 0x8C)


def row_has_navy(yy):
    cnt = 0
    for xx in range(0, W, 4):
        c = px[xx, yy]
        if all(abs(c[i] - navy[i]) <= 30 for i in range(3)):
            cnt += 1
    return cnt


# 顶部连续 navy 行
top_rows = [yy for yy in range(0, 400) if row_has_navy(yy) > 100]
if top_rows:
    print(f"  实测：顶部连续 navy 行 y={top_rows[0]}..{top_rows[-1]}（底边 {top_rows[-1]+1}px）")


def bbox(col, tol=24, y0=0, y1=None):
    y1 = y1 or H
    xs, ys = [], []
    for yy in range(y0, y1):
        for xx in range(W):
            c = px[xx, yy]
            if all(abs(c[i] - col[i]) <= tol for i in range(3)):
                xs.append(xx)
                ys.append(yy)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


# 标题块 4.582in,3.042in,4.167x1.156in（与顶部带同色，取 y>1.9in 区域避开带）
b = bbox(navy, y0=int(1.9 * scale), y1=int(4.8 * scale))
print(f"  标题块规格 x=4.582in y=3.042in w=4.167in h=1.156in")
if b:
    print(f"  实测 bbox(px)={b}  → in: "
          f"({b[0]/scale:.3f},{b[1]/scale:.3f})-({b[2]/scale:.3f},{b[3]/scale:.3f})")
    print(f"  结论: x 起点 {b[0]/scale:.3f}in（规格 4.582）→ 比值 {(b[0]/scale)/4.582:.3f}")
    print(f"        y 起点 {b[1]/scale:.3f}in（规格 3.042）→ 比值 {(b[1]/scale)/3.042:.3f}")
