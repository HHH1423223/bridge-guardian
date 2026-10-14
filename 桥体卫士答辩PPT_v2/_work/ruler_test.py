# -*- coding: utf-8 -*-
"""标尺实验：已知坐标与边长的多色方块 -> 量出精确的 像素/EMU 映射与原点。"""
import pathlib
import subprocess

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu

HERE = pathlib.Path(__file__).resolve().parent
NODE = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
CLI = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js"
D = HERE / "ruler"
D.mkdir(parents=True, exist_ok=True)

IN = 914400
# (颜色, x_in, y_in, w_in, h_in)  —— 全部用整数英寸，便于换算
SPECS = [
    ("E5484D", 0.0, 0.0, 1.0, 1.0),   # 红：1in 方块在原点
    ("00B3A4", 2.0, 0.0, 1.0, 1.0),   # 青：x=2in
    ("2FA84F", 0.0, 2.0, 1.0, 1.0),   # 绿：y=2in
    ("0E3F8C", 0.0, 0.0, 4.0, 0.5),   # 深蓝：宽 4in 高 0.5in 长条（在最底层会被覆盖一半）
    ("F5A524", 4.0, 2.0, 2.0, 1.0),   # 橙：x=4in y=2in 宽 2in
]
BAND = ("0E3F8C", 0.0, 5.0, 13.3333, 0.5)  # 深蓝长条：y=5in，通栏（用于测宽度与比例）

prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
sl = prs.slides.add_slide(prs.slide_layouts[6])
# 先铺一条通栏蓝带（y=5in），再放方块
all_specs = [(BAND[0], BAND[1], BAND[2], BAND[3], BAND[4])] + SPECS
for color, xi, yi, wi, hi in all_specs:
    sh = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                             Emu(int(xi * IN)), Emu(int(yi * IN)),
                             Emu(int(wi * IN)), Emu(int(hi * IN)))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor.from_string(color)
    sh.line.fill.background()
prs.save(str(D / "ruler.pptx"))

r = subprocess.run([NODE, CLI, "render", "--input", str(D / "ruler.pptx"),
                    "--output-dir", str(D / "preview"), "--dpi", "120"],
                   capture_output=True, text=True, encoding="utf-8")
print("render rc:", r.returncode)

png = sorted((D / "preview").glob("*.png"))[0]
im = Image.open(png).convert("RGB")
W, H = im.size
px = im.load()
print(f"png {W}x{H}")

def bbox(col, tol=24):
    xs, ys = [], []
    for yy in range(H):
        for xx in range(W):
            c = px[xx, yy]
            if all(abs(c[i] - col[i]) <= tol for i in range(3)):
                xs.append(xx)
                ys.append(yy)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None

print(f"\n{'标记':22s} {'规格(in x,y,w,h)':26s} {'实测 bbox(px)':28s} {'实测(in, 按 W/13.333)':22s}")
scale = W / 13.3333
for color, xi, yi, wi, hi in all_specs:
    b = bbox(tuple(int(color[i:i+2], 16) for i in (0, 2, 4)))
    if b is None:
        print(f"{color:22s} ({xi},{yi},{wi},{hi})".ljust(50) + "未找到")
        continue
    inb = tuple(round(v / scale, 3) for v in b)
    print(f"{color:22s} ({xi},{yi},{wi},{hi})".ljust(50) + f"{str(b):28s} {inb}")
