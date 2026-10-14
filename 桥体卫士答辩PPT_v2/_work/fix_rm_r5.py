# -*- coding: utf-8 -*-
"""fix_rm_r5.py —— 让 rules_matrix 的 rm_r5 单行放下（11pt 下超宽 3.4%）。

背景：按 FACTCHECK ❌-4 给 rm_r5 补上 rules.py:120 实际会输出的「，超过阈值 20.00」后，
该行在 11pt 下需宽 5,215,280 EMU，而卡片里文字框宽 5,045,400 → 折成 2 行并溢出卡片高度
（check_spec 已报 warn）。其它 5 张卡的 reason 都在 11pt 下单行放得下。

处理：只删掉 rm_r5 末尾的括注「（相对应变指标）」——「相对应变指标/无量纲」的口径
本页页头与 s07/s13 都已交代，此处删掉不损失事实，且保留核验员要求补回的关键子句。
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from build_deck import PT, text_em  # noqa: E402

P = HERE / "_spec" / "SPEC_diagrams.json"
data = json.loads(P.read_text(encoding="utf-8"))
fig = next(f for f in data["figures"] if f["fig_id"] == "rules_matrix")
el = next(e for e in fig["elements"] if e.get("id") == "rm_r5")

old = el["text"]
assert "，超过阈值 20.00（相对应变指标）" in old, f"rm_r5 内容已变，中止：{old!r}"
new = old.replace("（相对应变指标）", "")
el["text"] = new

need = int(text_em(new) * 11 * PT * 1.02)
avail = el["w"]
assert need <= avail * 0.95, f"改完仍超宽：需 {need} vs 可用 {int(avail*0.95)}"
assert "超过阈值 20.00" in new, "关键子句丢失"

P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"rm_r5:\n  旧: {old}\n  新: {new}\n  11pt 需宽 {need} ≤ 可用 {avail} ✅")
