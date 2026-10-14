# -*- coding: utf-8 -*-
"""pick_se_d4n.py —— 为本就不宽的 se_d4n 标题选一个 15pt 单行放得下的措辞。"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from build_deck import text_em, PT  # noqa: E402

P = HERE / "_spec" / "SPEC_diagrams.json"
data = json.loads(P.read_text(encoding="utf-8"))
fig = next(f for f in data["figures"] if f["fig_id"] == "security_8")
el = next(e for e in fig["elements"] if e.get("id") == "se_d4n")
w = el["w"]
print(f"se_d4n 元素宽 {w}，当前文本 {el['text']!r}\n")
best = None
for cand in ("CSRF 防护 + 口令哈希校验", "CSRF 防护 + 口令哈希", "CSRF + 口令哈希校验",
             "CSRF 防护 + 哈希口令", "CSRF + 口令哈希"):
    need = int(text_em(cand) * 15 * PT * 1.12)
    ok = need <= w * 0.95
    print(f"  {cand!r:34s} 需宽 {need:>8d}  {'OK' if ok else 'OVER'}")
    if ok and best is None:
        best = cand

assert best, "没有候选放得下，需要放宽元素宽或改字号"
el["text"] = best
P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n已采用: {best!r}（写回 {P.name}）")
