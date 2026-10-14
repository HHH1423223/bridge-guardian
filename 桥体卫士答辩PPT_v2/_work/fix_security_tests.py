# -*- coding: utf-8 -*-
"""fix_security_tests.py —— 补齐 FACTCHECK ❌-2/❌-1 在**图形文字**里的遗漏。

上一轮 fix_factcheck.py 只改了 SPEC_content.json 与 BUILD_SPEC.md，
漏了 SPEC_diagrams.json 的两处同源表述（渲染后现场发现）：
  1) security_8:se_d4r「表单带令牌；口令只存哈希，不存明文」
     → 实为"支持 SHA-256 哈希校验 + 默认明文回退"（config.py:36-37,66-70），
       「只存哈希」不成立。
  2) security_8:se_m1r「项测试全部通过（0 失败 / 0 跳过）」
     → 测试套件存在浏览器夹具间歇性 flake，「0 失败」是会被现场复跑打脸的断言，
       改为只报可稳定复现的计数与覆盖。
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parents[1]
P = HERE / "_spec" / "SPEC_diagrams.json"
data = json.loads(P.read_text(encoding="utf-8"))
fig = next(f for f in data["figures"] if f["fig_id"] == "security_8")
by_id = {e.get("id"): e for e in fig["elements"]}

EDITS = [
    ("se_d4r", "表单带令牌；口令只存哈希，不存明文",
     "表单带令牌；口令支持哈希校验存储"),
    ("se_d4n", "CSRF 防护 + 密码哈希", "CSRF 防护 + 口令哈希校验"),
    ("se_m1r", "项测试全部通过（0 失败 / 0 跳过）",
     "项测试用例 · 11 个测试文件"),
]

for eid, old, new in EDITS:
    el = by_id.get(eid)
    assert el is not None, f"未找到 {eid}"
    assert el["text"] == old, f"{eid} 内容已变，中止：{el['text']!r}"
    el["text"] = new

P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
for eid, old, new in EDITS:
    print(f"  {eid}: {old}  →  {new}")
print(f"已写回 {P}")
