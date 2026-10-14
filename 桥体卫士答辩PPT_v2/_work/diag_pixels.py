# -*- coding: utf-8 -*-
"""像素分析：确认预览图是否为 16:9、标题墨色像素的实际包围盒。"""
import pathlib
import sys

from PIL import Image

p = pathlib.Path(sys.argv[1])
im = Image.open(p).convert("RGB")
W, H = im.size
print(f"file={p.name} size={W}x{H} aspect={W/H:.4f}  (16:9={16/9:.4f})")

px = im.load()
targets = {
    "ink#0B1B2B": (0x0B, 0x1B, 0x2B),
    "navy#0E3F8C": (0x0E, 0x3F, 0x8C),
    "teal#00B3A4": (0x00, 0xB3, 0xA4),
    "red#E5484D": (0xE5, 0x48, 0x4D),
    "green#2FA84F": (0x2F, 0xA8, 0x4F),
}


def near(c, t, tol=26):
    return all(abs(c[i] - t[i]) <= tol for i in range(3))


def bbox_of(col):
    xs, ys = [], []
    for yy in range(H):
        for xx in range(W):
            if near(px[xx, yy], col):
                xs.append(xx)
                ys.append(yy)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


for name, col in targets.items():
    b = bbox_of(col)
    if b is None:
        print(f"  {name:14s} 未找到")
        continue
    x0, y0, x1, y1 = b
    print(
        f"  {name:14s} bbox px=({x0},{y0})-({x1},{y1})  "
        f"相对位置 x={x0/W:.3f}..{x1/W:.3f} y={y0/H:.3f}..{y1/H:.3f}"
    )

# 逐行扫描 ink 像素数的分布，定位标题实际所在行区间
rows = []
for yy in range(H):
    c = sum(1 for xx in range(0, W, 3) if near(px[xx, yy], targets["ink#0B1B2B"]))
    if c > 6:
        rows.append(yy)
if rows:
    print(f"  ink 文本行区间: y={rows[0]}..{rows[-1]} (共 {len(rows)} 行)")
