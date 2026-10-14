# -*- coding: utf-8 -*-
"""fix_s12_title.py —— 第 12 页标题「可度量成果 —— 测试全绿」与收口口径自相矛盾。

我们在 FACTCHECK ❌-1 收口时决定：不再宣称「测试全绿 / 0 failed」，只报可稳定复现的计数。
但页标题仍写着「测试全绿」，且该场景已改为纯矢量（无测试截图），与页内内容也不符。
改为「可度量成果 —— 测试覆盖」，与页内「101 项用例 / 11 个文件 / 按测试域分组」一致。
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from build_deck import CHROME_TITLE_W, FONT_SIZES, PT, text_em  # noqa: E402

P = HERE / "_spec" / "SPEC_content.json"
data = json.loads(P.read_text(encoding="utf-8"))
sl = next(s for s in data["slides"] if s["slide_id"] == "s12_evidence")

old = sl["title"]
new = "可度量成果 —— 测试覆盖"
assert old == "可度量成果 —— 测试全绿", f"标题已变，中止：{old!r}"
sl["title"] = new

need = int(text_em(new) * FONT_SIZES["h1"] * PT * 1.12)
assert need <= CHROME_TITLE_W, f"新标题超宽：需 {need} > {CHROME_TITLE_W}"

# 讲稿首句也同步（原句以"测试全绿"起势）
n0 = sl["notes"]
sl["notes"] = n0.replace("成果是可度量的。", "成果是可度量的。", 1)
assert "全绿" not in sl["notes"], "notes 里仍有「全绿」"

P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"s12 标题: {old!r} → {new!r}（27pt 需宽 {need} ≤ {CHROME_TITLE_W} ✅）")
print(f"notes 首句: {sl['notes'][:40]}...")
