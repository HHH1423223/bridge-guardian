# -*- coding: utf-8 -*-
"""fix_tests_kpi.py —— 最后一处「0 failed / 0 skipped」残留（tests_dist:td_kpi_s）。

全 PPT + notes 扫描确认这是唯一残留。测试套件存在浏览器夹具间歇性 flake，
「0 failed / 0 skipped」是会被现场复跑打脸的断言，改为只报可稳定复现的量化事实。
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from build_deck import PT, text_em  # noqa: E402

P = HERE / "_spec" / "SPEC_diagrams.json"
data = json.loads(P.read_text(encoding="utf-8"))
fig = next(f for f in data["figures"] if f["fig_id"] == "tests_dist")
el = next(e for e in fig["elements"] if e.get("id") == "td_kpi_s")

old = el["text"]
new = "101 项用例 · 11 个测试文件（10 个 test_*.py + conftest.py）"
assert old.startswith("0 failed / 0 skipped"), f"内容已变，中止：{old!r}"
el["text"] = new

need = int(text_em(new) * 11 * PT * 1.02)
assert need <= el["w"] * 0.95, f"改完超宽：需 {need} vs 可用 {int(el['w'] * 0.95)}"
assert "0 failed" not in new and "0 skipped" not in new

P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"td_kpi_s:\n  旧: {old}\n  新: {new}\n  11pt 需宽 {need} ≤ 可用 {int(el['w'] * 0.95)} ✅")
