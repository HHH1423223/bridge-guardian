# -*- coding: utf-8 -*-
"""fix_s12_e5.py —— 第三轮确认的最后一处 ❌（第 12 页正文 e5）。

现象：s12 正文卡片「口径一致」的正文仍写「数据、阈值、历史三端用同一生效参数。」，
而同一页 notes 已改为「历史页会动态拉取当前生效阈值，超限统计和阈值线跟设置页保持一致」
→ 正文与讲稿自相矛盾。

核验员补充的事实（比原表述更准，采纳）：
  - 三处确实同源于渲染期的 `simulator.latest["threshold"]`（app.py:393,412,421,429,437 + /api/data + /api/settings）；
  - 但**不是实时一致**：templates/trend.html:201 `var INITIAL_THRESHOLD = {{ threshold }};` 是渲染时快照，
    :375/:377 的阈值 markLine 与标签都用它，trend.html 全文没有 /api/settings 调用；
  - 只有 templates/history.html 会动态拉取（:275-289 loadThreshold()，页面加载时调用一次）。
故正文改为「阈值与历史口径对齐设置页。」——只声称能证明的部分。
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from build_deck import PT, text_em  # noqa: E402

P = HERE / "_spec" / "SPEC_content.json"
data = json.loads(P.read_text(encoding="utf-8"))
sl = next(s for s in data["slides"] if s["slide_id"] == "s12_evidence")
el = next(e for e in sl["elements"] if e.get("id") == "e5")

old = el["text"]
new = "阈值与历史口径对齐设置页。"
assert old == "数据、阈值、历史三端用同一生效参数。", f"e5 已变，中止：{old!r}"
el["text"] = new

need = int(text_em(new) * 13 * PT * 1.05)
assert need <= el["w"] * 0.95, f"新文本超宽：{need} > {int(el['w'] * 0.95)}"

# 卡片标题「口径一致」也随之更贴切
t = next(e for e in sl["elements"] if e.get("id") == "e4")
assert t["text"] == "口径一致", f"卡片标题已变：{t['text']!r}"
t["text"] = "阈值口径同步"

P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
json.loads(P.read_text(encoding="utf-8"))
print(f"e5: {old!r} → {new!r}（13pt 需宽 {need} ≤ {int(el['w'] * 0.95)}）")
print(f"e4 卡片标题: '口径一致' → '阈值口径同步'")
