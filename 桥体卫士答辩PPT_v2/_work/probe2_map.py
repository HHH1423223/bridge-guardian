# -*- coding: utf-8 -*-
"""标记点阵实验：6 个已知坐标的彩色方块 -> 渲染 -> 量出真实映射。"""
import json
import pathlib
import subprocess

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
PY = r"C:\Users\CX\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
NODE = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\runtime\primary-runtime\dependencies\node\bin\node.exe"
CLI = r"C:\Users\CX\AppData\Local\Programs\DeepSeek Harness\resources\app.asar.unpacked\dsh\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js"

D = HERE / "probe2"
D.mkdir(parents=True, exist_ok=True)

S = 914400  # 1in 方块
COLS = {"red": (0xE5, 0x48, 0x4D), "teal": (0x00, 0xB3, 0xA4), "green": (0x2F, 0xA8, 0x4F),
        "navy": (0x0E, 0x3F, 0x8C), "amber": (0xF5, 0xA5, 0x24), "orange": (0xF2, 0x73, 0x1F)}
marks = [
    ("m1", 0, 0, "red"),
    ("m2", 4572000, 0, "teal"),
    ("m3", 9144000, 0, "green"),
    ("m4", 0, 2743200, "navy"),
    ("m5", 4572000, 2743200, "amber"),
    ("m6", 9144000, 2743200, "orange"),
]
elements = [{"id": i, "type": "rect", "x": x, "y": y, "w": S, "h": S, "fill": c, "line_color": "none"}
            for i, x, y, c in marks]

content = {"deck": {"title": "probe2"},
           "slides": [{"slide_id": "s01_cover", "chrome": "none", "title": "", "seconds": 10,
                       "elements": [], "notes": "probe"}]}
figs = {"figures": [{"fig_id": "probe2", "for_slide": "s01_cover",
                     "canvas": {"x": 0, "y": 0, "w": 12192000, "h": 6858000},
                     "elements": elements}]}
(D / "SPEC_content.json").write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
(D / "SPEC_diagrams.json").write_text(json.dumps(figs, ensure_ascii=False), encoding="utf-8")

subprocess.run([PY, "-X", "utf8", str(HERE.parent / "build_deck.py"), "--allow-partial",
                "--content", str(D / "SPEC_content.json"), "--diagrams", str(D / "SPEC_diagrams.json"),
                "--out", str(D / "probe2.pptx")], capture_output=True, text=True, encoding="utf-8")
r = subprocess.run([NODE, CLI, "render", "--input", str(D / "probe2.pptx"),
                    "--output-dir", str(D / "preview"), "--dpi", "120"],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout[-260:])

png = sorted((D / "preview").glob("*.png"))[0]
im = Image.open(png).convert("RGB")
W, H = im.size
px = im.load()
print(f"preview {png.name} {W}x{H}\n")

# 网格：每格 10x10 px 内的主色
cell = 10
print("网格色块图（每格 10x10px）：")
legend = {"R": "red", "T": "teal", "G": "green", "N": "navy", "A": "amber", "O": "orange", ".": "bg"}
rev = {}
for k, c in COLS.items():
    rev[c] = k[0].upper()
for gy in range(0, H, cell):
    row = ""
    for gx in range(0, W, cell):
        counts = {}
        for yy in range(gy, min(gy + cell, H)):
            for xx in range(gx, min(gx + cell, W)):
                c = px[xx, yy]
                best, bd = None, 999
                for col, _ in COLS.items():
                    cc = COLS[col]
                    d = sum(abs(c[i] - cc[i]) for i in range(3))
                    if d < bd:
                        bd, best = d, col
                if bd <= 30:
                    counts[best] = counts.get(best, 0) + 1
        if counts:
            top = max(counts, key=counts.get)
            row += rev[COLS[top]]
        else:
            row += "."
    print(f"{gy:4d} {row}")


def bbox(col, tol=30):
    xs, ys = [], []
    for yy in range(H):
        for xx in range(W):
            c = px[xx, yy]
            if all(abs(c[i] - col[i]) <= tol for i in range(3)):
                xs.append(xx)
                ys.append(yy)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


print("\n标记实测：")
print(f"{'mark':6s} {'EMU坐标':22s} {'实测px bbox':26s} {'换算回EMU(×152.4)':22s}")
for i, x, y, c in marks:
    b = bbox(COLS[c])
    if b is None:
        print(f"{i:6s} ({x},{y})".ljust(30) + "未找到")
        continue
    k = 12192000 / W
    print(f"{i:6s} ({x:>8d},{y:>8d})   {str(b):26s} "
          f"({b[0]*k:.0f},{b[1]*k:.0f})-({b[2]*k:.0f},{b[3]*k:.0f})")
