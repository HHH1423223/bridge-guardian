# -*- coding: utf-8 -*-
"""fix_thanks_band.py —— 删除致谢页那条空的深色底带（tk_band）。

背景：第 15 页渲染出来后，底部 5486400..6858000 是一条 1.5in 高的 ink 实色带，
带内没有任何内容，视觉上像"截断"，与整页浅色风格也不搭（该页 tk_band 之外全是浅色元素）。
致谢页不是深色封面页，去掉后整页留白干净。

安全措施：
  - 先断言该元素确实是 thanks_geo 的 tk_band、fill=ink、且内部没有任何其他元素；
  - 只删除这一个元素，其余 15 个元素一字不动；
  - 删除前后统计元素数并打印。
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parents[1]
P = HERE / "_spec" / "SPEC_diagrams.json"

data = json.loads(P.read_text(encoding="utf-8"))
fig = next(f for f in data["figures"] if f["fig_id"] == "thanks_geo")
els = fig["elements"]

band = next((e for e in els if e.get("id") == "tk_band"), None)
assert band is not None, "未找到 tk_band，文件可能已被改动"
assert band["fill"] == "ink", f"tk_band fill 期望 ink，实际 {band['fill']}"
bx, by, bw, bh = band["x"], band["y"], band["w"], band["h"]
assert (bx, by, bw, bh) == (0, 5486400, 12192000, 1371600), f"tk_band 坐标已变: {bx,by,bw,bh}"

inside = [e["id"] for e in els if e is not band and e.get("x", 0) >= bx and e.get("y", 0) >= by]
assert not inside, f"底带内存在其他元素，不能盲删: {inside}"

before = len(els)
fig["elements"] = [e for e in els if e.get("id") != "tk_band"]
after = len(fig["elements"])
assert after == before - 1

P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"thanks_geo 元素数: {before} -> {after}（已删除空底带 tk_band）")
print(f"文件已写回: {P}  ({P.stat().st_size} bytes)")
