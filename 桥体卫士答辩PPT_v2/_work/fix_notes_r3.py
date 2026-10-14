# -*- coding: utf-8 -*-
"""fix_notes_r3.py —— 让讲稿与已收口的幻灯片口径一致（第三轮）。

背景（复验 ⚠️-2 的延伸）：幻灯片已把「同一套分级」改为「同一套颜色语言」，
但讲稿（notes）里还留着两处更强的表述，现场照着念会与幻灯片/代码不一致：

1) s07 notes「分级口径统一：…」+「用的是同一套颜色语言」——
   引擎 rules.py 用 `>=`（1.1× = 132 归"报警"），趋势页 trend.html:231-232 用 `<=`
   （132 判"预警"），边界值上口径不同，说"统一"不严谨。改为只声称颜色语言一致。
2) s12 notes「数据、阈值、历史三端用的是同一份生效参数，不会各说各话」——
   可核到的是**历史页**动态同步当前阈值（history.html:131 `currentThreshold`、
   :275 `loadThreshold()` 拉 `/api/settings`）与阈值线（:263），"三端同一份参数"过头了。
   改为只讲历史页这一条可核事实。
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parents[1]
P = HERE / "_spec" / "SPEC_content.json"
data = json.loads(P.read_text(encoding="utf-8"))

EDITS = [
    ("s07_risk",
     "分级口径统一：超过阈值 1.2 倍判严重报警，1.1 倍判报警，其余是预警。颜色不是装饰——"
     "大屏风险卡、阈值仪表、报警行共用同一套颜色语言，一眼就能看出现在处于哪一级。",
     "分级口径是：超过阈值 1.2 倍判严重报警，1.1 倍判报警，其余是预警。颜色不是装饰——"
     "大屏风险卡、阈值仪表、报警行共用同一套颜色语言，一眼就能看出现在处于哪一级。"),
    ("s12_evidence",
     "另外，数据、阈值、历史三端用的是同一份生效参数，不会各说各话。",
     "另外，历史页会动态拉取当前生效阈值，超限统计和阈值线跟设置页保持一致。"),
]

for sid, old, new in EDITS:
    s = next(x for x in data["slides"] if x["slide_id"] == sid)
    assert s["notes"].count(old) == 1, f"{sid} 目标句命中 {s['notes'].count(old)} 次，中止"
    s["notes"] = s["notes"].replace(old, new)
    n = len([c for c in s["notes"] if c.strip()])
    budget = s["seconds"] * 4.5
    assert n <= budget, f"{sid} 讲稿超预算：{n} > {budget:.0f}"

P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
json.loads(P.read_text(encoding="utf-8"))
for sid, old, new in EDITS:
    s = next(x for x in data["slides"] if x["slide_id"] == sid)
    print(f"{sid}: 讲稿已改（{len([c for c in s['notes'] if c.strip()])}/{s['seconds']*4.5:.0f} 字）")
print("SPEC_content.json 可解析 ✅")
