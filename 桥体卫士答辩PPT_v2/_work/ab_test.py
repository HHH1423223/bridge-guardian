# -*- coding: utf-8 -*-
"""最小 A/B：定位 1.5x 偏移的来源。
A: 纯 python-pptx add_shape（不用我的 helper）
B: 我的 builder 走的路径（add_rect）
两者方块坐标完全相同，比较渲染结果。"""
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
D = HERE / "ab"
D.mkdir(parents=True, exist_ok=True)

S = 914400  # 1in


def add(prs, x, y, color):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(x), Emu(y), Emu(S), Emu(S))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor.from_string(color)
    sh.line.fill.background()
    return s


# A: 默认模板 + 显式设置尺寸
prsA = Presentation()
prsA.slide_width, prsA.slide_height = Emu(12192000), Emu(6858000)
add(prsA, 0, 0, "E5484D")
add(prsA, 4572000, 0, "00B3A4")
prsA.save(str(D / "A.pptx"))

# B: 不设置尺寸（用 python-pptx 默认 10x7.5in）—— 看尺寸设置是否影响渲染
prsB = Presentation()
add(prsB, 0, 0, "E5484D")
add(prsB, 4572000, 0, "00B3A4")
prsB.save(str(D / "B.pptx"))
print("A slide size:", prsA.slide_width, prsA.slide_height)
print("B slide size:", prsB.slide_width, prsB.slide_height)

for tag in ("A", "B"):
    r = subprocess.run([NODE, CLI, "render", "--input", str(D / f"{tag}.pptx"),
                        "--output-dir", str(D / f"prev_{tag}"), "--dpi", "120"],
                       capture_output=True, text=True, encoding="utf-8")
    print(f"--- {tag} render rc={r.returncode}")
    png = sorted((D / f"prev_{tag}").glob("*.png"))[0]
    im = Image.open(png).convert("RGB")
    W, H = im.size
    px = im.load()

    def bbox(col, tol=24):
        xs, ys = [], []
        for yy in range(H):
            for xx in range(W):
                c = px[xx, yy]
                if all(abs(c[i] - col[i]) <= tol for i in range(3)):
                    xs.append(xx)
                    ys.append(yy)
        return (min(xs), min(ys), max(xs), max(ys)) if xs else None

    print(f"    png {W}x{H}  red={bbox((0xE5,0x48,0x4D))}  teal={bbox((0x00,0xB3,0xA4))}")
    print(f"    期望: red=(0,0,~90,~90) teal=(~451,0,~541,~90)")
