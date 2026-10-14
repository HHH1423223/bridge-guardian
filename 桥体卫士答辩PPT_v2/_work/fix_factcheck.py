# -*- coding: utf-8 -*-
"""fix_factcheck.py —— 收口事实核验（FACTCHECK.md）的 4 条 ❌（只改文案，不动代码）。

每条改动都带"必须恰好命中一次"的断言，命中数不符即中止，避免误改。

❌-2 口令「只存哈希」→ 实为"支持哈希、默认可明文回退"（config.py:36-37,66-70）
❌-3 四级名称「安全/严重」→ 代码与大屏实为「正常/严重报警」（rules.py:43-46, app.py:48-49）
❌-4 两条 reason 示例与代码不符（rules.py:120 漏「超过阈值 20.00」；
     app.py:209-210 实际是「设备失去连接：心跳超时」，无"串口连续超时计数达 10 次"路径）
⚠️   分级边界：引擎 rules.py 用 `>=`（1.1×=132 归"报警"），大屏 dashboard.html 用 `<=`
     （≤120 判安全、≤132 判预警），132/144 两点口径不同 → 删掉"同一套分级"的强表述
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parents[1]
SPEC = HERE / "_spec"

EDITS = {
    # 文件 -> [(旧串, 新串), ...]
    "SPEC_diagrams.json": [
        ('"安全"', '"正常"'),                       # risk_link 第一级名称
        ('"严重"', '"严重报警"'),                    # risk_link 第四级名称
        ("等级 → 颜色 → 处置优先级（同一份数据）",
         "等级 → 颜色 → 处置优先级"),                # 去掉"同一份数据"的强断言
        ("近期均值 118.60 相对基线 96.10 偏移 +22.50（相对应变指标）",
         "近期均值 118.60 相对基线 96.10 偏移 +22.50，超过阈值 20.00（相对应变指标）"),
        ("设备失去连接：串口连续超时计数达 10 次",
         "设备失去连接：心跳超时"),
        ("串口连续超时 ≥ 10 次：如实判离线",
         "连续心跳超时 ≥ 10 次：如实判离线"),        # offline_after 在 datasource.py:137
    ],
    "SPEC_content.json": [
        ("大屏、仪表、报警行同一套分级。",
         "大屏、仪表、报警行同一套颜色语言。"),
        ("风险分四级：安全、预警、报警、严重，对应绿、黄、橙、红。",
         "风险分四级：正常、预警、报警、严重报警，对应绿、黄、橙、红。"),
        ("超过阈值 1.2 倍判严重，1.1 倍判报警，其余是预警。颜色不是装饰——"
         "大屏风险卡、阈值仪表、报警行用的是同一套颜色语言，一眼就能看出现在处于哪一级。",
         "超过阈值 1.2 倍判严重报警，1.1 倍判报警，其余是预警。颜色不是装饰——"
         "大屏风险卡、阈值仪表、报警行共用同一套颜色语言，一眼就能看出现在处于哪一级。"),
        ("密码支持哈希存储。",
         "口令支持哈希存储（默认明文回退，可用 .env 切到哈希校验）。"),
        ("实跑：101 passed in 15.38s（0 failed / 0 skipped）",
         "实跑：101 passed（本次 0 failed / 0 skipped）"),
        ("成果是可度量的。测试实跑 101 passed in 15.38s，零失败零跳过，一共 11 个测试文件，",
         "成果是可度量的。测试实跑 101 passed，本次零失败零跳过，一共 11 个测试文件，"),
        ("python -m pytest tests/ -q 的实跑结果是 101 passed in 15.38s，零失败、零跳过，"
         "一共 11 个测试文件。",
         "python -m pytest tests/ -q 本次实跑 101 passed，零失败、零跳过，一共 11 个测试文件。"),
        ("101 项用例 · 11 个文件", "101 项用例 · 11 个文件 · 本次全绿"),
    ],
    "BUILD_SPEC.md": [
        ("- 风险分级：安全 / 预警 / 报警 / 严重（对应 green / amber / orange / red）。",
         "- 风险分级（以代码为准，`rules.py:43-46` + `app.py:48-49`）：**正常 / 预警 / 报警 / 严重报警**"
         "（对应 green / amber / orange / red）。注意不要写成「安全」，也不要漏掉「报警」二字。"),
        ("- 鉴权与安全：密钥走环境变量（`.env.example`）、统一鉴权、未登录 API 返回 401、CSRF 防护、密码哈希。",
         "- 鉴权与安全：密钥走环境变量（`.env.example`）、统一鉴权、未登录 API 返回 401、CSRF 防护；"
         "口令**支持** SHA-256 哈希校验（`config.py:66-70`），但默认是明文回退（`config.py:36` + "
         "`.env.example:11`），所以只能说「支持哈希存储」，**不能说「只存哈希」**。"),
        ("- **测试数字（Lead 2026-10-02 实跑，直接引用，禁止改写）**",
         "- **测试数字（Lead 2026-10-02 实跑，直接引用，禁止改写；只报 passed 数与文件数）**"),
    ],
}

report = []
for fname, pairs in EDITS.items():
    p = SPEC / fname
    txt = p.read_text(encoding="utf-8")
    for old, new in pairs:
        n = txt.count(old)
        assert n == 1, f"{fname}: {old[:40]!r} 命中 {n} 次（期望 1），已中止"
        txt = txt.replace(old, new)
        report.append((fname, old, new))
    # 写回前确认 JSON 仍可解析
    if fname.endswith(".json"):
        json.loads(txt)
    p.write_text(txt, encoding="utf-8")

assert json.loads((SPEC / "SPEC_diagrams.json").read_text(encoding="utf-8"))
assert json.loads((SPEC / "SPEC_content.json").read_text(encoding="utf-8"))

print(f"已收口 {len(report)} 处：")
for fname, old, new in report:
    print(f"  [{fname}] {old[:34]} → {new[:34]}")
