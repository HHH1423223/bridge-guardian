# -*- coding: utf-8 -*-
"""定位实验：三个已知坐标的实色矩形，渲染后量出实际映射关系。"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PY = r"C:\Users\CX\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
NODE = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
CLI = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js"

D = HERE / "probe"
D.mkdir(parents=True, exist_ok=True)

# 标记：A 左上角 1000x1000EMU 见方的小块在 (0,0)；B 中心；C 右下
marks = [
    ("A", 0, 0, 914400, 914400, "red"),        # 左上角 1in 方块
    ("B", 6096000, 3429000, 914400, 914400, "teal"),  # 正中心
    ("C", 11277600, 5943600, 914400, 914400, "green"),  # 右下角
]
elements = [
    {"id": f"m{k}", "type": "rect", "x": x, "y": y, "w": w, "h": h,
     "fill": c, "line_color": "none"}
    for k, x, y, w, h, c in marks
]

content = {
    "deck": {"title": "probe"},
    "slides": [{"slide_id": "s01_cover", "chrome": "none", "title": "", "seconds": 10,
                "elements": [], "notes": "probe"}],
}
figs = {"figures": [{"fig_id": "probe", "for_slide": "s01_cover",
                     "canvas": {"x": 0, "y": 0, "w": 12192000, "h": 6858000},
                     "elements": elements}]}

(D / "SPEC_content.json").write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
(D / "SPEC_diagrams.json").write_text(json.dumps(figs, ensure_ascii=False), encoding="utf-8")

r = subprocess.run(
    [PY, "-X", "utf8", str(HERE.parent / "build_deck.py"),
     "--allow-partial",
     "--content", str(D / "SPEC_content.json"),
     "--diagrams", str(D / "SPEC_diagrams.json"),
     "--out", str(D / "probe.pptx")],
    capture_output=True, text=True, encoding="utf-8")
print(r.stdout[-600:], r.stderr[-600:])

r = subprocess.run([NODE, CLI, "render", "--input", str(D / "probe.pptx"),
                    "--output-dir", str(D / "preview"), "--dpi", "120"],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout[-400:], r.stderr[-400:])

from PIL import Image  # noqa: E402

png = sorted((D / "preview").glob("*.png"))[0]
im = Image.open(png).convert("RGB")
W, H = im.size
print(f"\n预览: {png.name} {W}x{H}")
px = im.load()


def bbox(col, tol=30):
    xs, ys = [], []
    for yy in range(H):
        for xx in range(W):
            c = px[xx, yy]
            if all(abs(c[i] - col[i]) <= tol for i in range(3)):
                xs.append(xx)
                ys.append(yy)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


for name, col in (("A(red 0,0)", (0xE5, 0x48, 0x4D)),
                  ("B(teal 6096000,3429000)", (0x00, 0xB3, 0xA4)),
                  ("C(green 11277600,5943600)", (0x2F, 0xA8, 0x4F))):
    b = bbox(col)
    print(f"  {name:28s} -> {b}")
print(f"\n  期望: 1 EMU = {W}/12192000 px = {W/12192000:.6f} px; 1in = {W/13.3333:.1f} px")
