# -*- coding: utf-8 -*-
"""fix_wording.py —— 两处口径措辞统一（图形内文字，带断言保护）。

1) s02：「依赖工程级标定」→「依赖专业标定」
   理由：「工程级」属红线敏感词（docs/答辩材料.md 第七节"不能说的话"），
   本句在描述传统监测之难、并非我方宣称，但答辩场合"工程级"出现在 PPT 上容易被追问，
   改成「专业标定」语义不变且更稳。
   注：s13「未做工程级标定与量值溯源」是**否定句**（如实声明边界），保留不改。
2) s03：「3D 场景」→「三维场景」
   理由：全场统一用「三维」（s01/s05/s15 已是「三维可视化监测场景」），术语一致。
   这是把「三维可视化监测场景」作为统一口径的自然延伸。
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parents[1]
P = HERE / "_spec" / "SPEC_diagrams.json"
data = json.loads(P.read_text(encoding="utf-8"))
figs = {f["fig_id"]: f for f in data["figures"]}

EDITS = [
    ("pain_compare", "依赖工程级标定", "依赖专业标定"),
    ("arch6", "3D 场景", "三维场景"),
]

changed = []
for fid, old, new in EDITS:
    fig = figs[fid]
    hit = 0
    for el in fig["elements"]:
        if el.get("text") and old in el["text"]:
            el["text"] = el["text"].replace(old, new)
            hit += 1
            changed.append((fid, el.get("id"), el["text"]))
    assert hit == 1, f"{fid} 中 {old!r} 命中 {hit} 次（期望 1），已中止以免误改"

for fid in ("pain_compare", "arch6"):
    assert not any(old in (e.get("text") or "") for e in figs[fid]["elements"] for old, _ in [(EDITS[0][1], 0)]), \
        f"{fid} 仍存在旧措辞" if fid == "pain_compare" else ""

P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print("已应用措辞统一：")
for fid, eid, txt in changed:
    print(f"  {fid}:{eid}  -> {txt}")
print(f"文件已写回: {P}")
