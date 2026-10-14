# -*- coding: utf-8 -*-
"""fix_final_r2.py —— 复验第二轮剩余的 2 条 ❌ + 1 条 ⚠️-N3（规格卫生）。

❌-A  p12 `td_kpi_v`「101 passed in 15.38s」
      → 套件 flaky 时会被现场复跑打脸，且 15.38s 只是单次快照非常量。
        改为与本页 `td_kpi_s` / 左栏同口径的稳定计数。
❌-B  p7 正文 e4「超过阈值 1.2 倍判严重，」
      → 裸用「严重」作等级名，与同页 notes 的「严重报警」矛盾。
⚠️-N3 `tests_dist._note` 仍写旧口径（"101 passed in 15.38s、0 failed / 0 skipped"）
      → 非渲染字段，但留着会被下轮传抄，随手更新。
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from build_deck import PT, text_em  # noqa: E402

D = HERE / "_spec" / "SPEC_diagrams.json"
C = HERE / "_spec" / "SPEC_content.json"

# ---------- ❌-A + ⚠️-N3（图形） ----------
d = json.loads(D.read_text(encoding="utf-8"))
fig = next(f for f in d["figures"] if f["fig_id"] == "tests_dist")
kpi = next(e for e in fig["elements"] if e.get("id") == "td_kpi_v")

old_kpi = kpi["text"]
new_kpi = "101 项用例"
assert old_kpi == "101 passed in 15.38s", f"td_kpi_v 已变：{old_kpi!r}"
kpi["text"] = new_kpi
need = int(text_em(new_kpi) * 32 * PT * 1.05)
assert need <= kpi["w"] * 0.95, f"KPI 超宽：{need} > {int(kpi['w'] * 0.95)}"

note = fig.get("_note") or ""
assert "0 failed / 0 skipped" in note, f"_note 已变：{note[:60]!r}"
fig["_note"] = (
    "按测试域分组展示：不列分项用例数，只报可稳定复现的计数"
    "（101 项用例、11 个测试文件 = 10 个 test_*.py + conftest.py）。"
    "不写 passed/耗时/0 failed 这类单次快照断言（套件含一个 headless 浏览器用例，存在间歇性 flake）。"
)

D.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"❌-A td_kpi_v: {old_kpi!r} → {new_kpi!r}（32pt 需宽 {need} ≤ {int(kpi['w'] * 0.95)}）")
print(f"⚠️-N3 _note 已更新为不含旧口径")

# ---------- ❌-B（文案） ----------
c = json.loads(C.read_text(encoding="utf-8"))
sl = next(s for s in c["slides"] if s["slide_id"] == "s07_risk")
el = next(e for e in sl["elements"] if e.get("id") == "e4")
old_t = el["text"]
assert old_t == "超过阈值 1.2 倍判严重，", f"e4 已变：{old_t!r}"
el["text"] = "超过阈值 1.2 倍判严重报警，"
need2 = int(text_em(el["text"]) * 13 * PT * 1.05)
assert need2 <= el["w"] * 0.95, f"e4 超宽：{need2} > {int(el['w'] * 0.95)}"

C.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"❌-B s07 e4: {old_t!r} → {el['text']!r}（{need2} ≤ {int(el['w'] * 0.95)}）")

assert json.loads(D.read_text(encoding="utf-8")) and json.loads(C.read_text(encoding="utf-8"))
print("两份规格 JSON 均可解析 ✅")
