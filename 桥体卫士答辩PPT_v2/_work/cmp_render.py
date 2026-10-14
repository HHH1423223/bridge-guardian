# -*- coding: utf-8 -*-
"""对照实验：同一渲染管线分别渲染【旧 PPT（已知几何）】与【我的 probe2】，
精确量出 1 英寸对应多少像素、原点是否在 (0,0)。"""
import glob
import json
import pathlib
import subprocess
import zipfile
from xml.etree import ElementTree as ET

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = r"C:\Users\CX\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
NODE = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
CLI = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js"
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def shapes_of(pptx, page=1):
    with zipfile.ZipFile(pptx) as z:
        xml = z.read(f"ppt/slides/slide{page}.xml")
    root = ET.fromstring(xml)
    out = []
    for sp in root.iter(f"{{{NS['p']}}}sp"):
        xfrm = sp.find(f".//{{{NS['a']}}}xfrm")
        if xfrm is None:
            continue
        off = xfrm.find(f"{{{NS['a']}}}off")
        ext = xfrm.find(f"{{{NS['a']}}}ext")
        txt = "".join(t.text or "" for t in sp.iter(f"{{{NS['a']}}}t"))
        solid = sp.find(f".//{{{NS['a']}}}solidFill/{{{NS['a']}}}srgbClr")
        out.append({
            "x": int(off.get("x")), "y": int(off.get("y")),
            "w": int(ext.get("cx")), "h": int(ext.get("cy")),
            "fill": solid.get("val") if solid is not None else None,
            "text": txt[:20],
        })
    return out


def render(pptx, outdir, page=1):
    subprocess.run([NODE, CLI, "render", "--input", str(pptx), "--output-dir", str(outdir),
                    "--pages", str(page), "--dpi", "120"], capture_output=True, text=True, encoding="utf-8")
    return sorted(pathlib.Path(outdir).glob("*.png"))[0]


def measure(png, color, tol=24):
    im = Image.open(png).convert("RGB")
    W, H = im.size
    px = im.load()
    xs, ys = [], []
    for yy in range(H):
        for xx in range(W):
            c = px[xx, yy]
            if all(abs(c[i] - color[i]) <= tol for i in range(3)):
                xs.append(xx)
                ys.append(yy)
    if not xs:
        return None, (W, H)
    return (min(xs), min(ys), max(xs), max(ys)), (W, H)


print("=" * 78)
print("A) 旧 PPT 第 1 页：已知几何 vs 渲染实测")
old = ROOT / "桥体卫士答辩PPT" / "桥体卫士答辩PPT.pptx"
for s in shapes_of(old)[:8]:
    print(f"    EMU x={s['x']:>9d} y={s['y']:>8d} w={s['w']:>9d} h={s['h']:>8d} fill={s['fill']} {s['text']!r}")
png = render(old, HERE / "cmp_old")
b, size = measure(png, (0x0E, 0x3F, 0x8C))
print(f"    -> 渲染 {size[0]}x{size[1]}，navy 实测 bbox={b}")

print("=" * 78)
print("B) 我的 probe2：已知几何 vs 渲染实测")
mine = HERE / "probe2" / "probe2.pptx"
for s in shapes_of(mine)[:10]:
    print(f"    EMU x={s['x']:>9d} y={s['y']:>8d} w={s['w']:>9d} h={s['h']:>8d} fill={s['fill']} {s['text']!r}")
for name, col in (("red", (0xE5, 0x48, 0x4D)), ("teal", (0x00, 0xB3, 0xA4)),
                  ("navy", (0x0E, 0x3F, 0x8C)), ("amber", (0xF5, 0xA5, 0x24))):
    b, size = measure(sorted((HERE / "probe2" / "preview").glob("*.png"))[0], col)
    print(f"    -> {name:6s} 实测 bbox={b}")

print("=" * 78)
print("关键换算：1 in = 914400 EMU")
for label, emu, pxv in (("旧PPT band 宽 12.5in", 11430000, None),):
    pass
