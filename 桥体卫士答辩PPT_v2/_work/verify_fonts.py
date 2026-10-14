# -*- coding: utf-8 -*-
"""verify_fonts.py —— 检查每页文字是否都绑定了中文字体（eastAsia）。

背景：旧版 build_deck.py 的 set_run_font 里 a:ea 分支被 a:latin 覆盖，
全 deck 的中文实际只绑了 Segoe UI，靠系统回退显示。本脚本用于回归验证。
"""
import pathlib
import re
import sys
import zipfile

import collections

p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                 else "桥体卫士答辩PPT_v2/桥体卫士答辩PPT_12分钟版.pptx")
EA = 'typeface="微软雅黑"'

with zipfile.ZipFile(p) as z:
    names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    names.sort(key=lambda s: int(re.findall(r"\d+", s)[0]))
    tot_runs = tot_ea = 0
    detail = []
    for n in names:
        x = z.read(n).decode("utf-8")
        # 每个 <a:rPr> 视为一个 run 的文字属性
        rprs = re.findall(r"<a:rPr[^>]*>.*?</a:rPr>|<a:rPr[^>]*/>", x, re.S)
        with_text = [r for r in rprs if "<a:t>" in x or True]
        runs = len(re.findall(r"<a:r>", x))
        ea = len(re.findall(r"<a:ea " + EA, x))
        tot_runs += runs
        tot_ea += ea
        detail.append((n.split("/")[-1], runs, ea))
    # 也统计表格/文本框里可能存在的其他文字容器
print(f"文件: {p.name}")
print(f"总 <a:r> run 数: {tot_runs}")
print(f"其中显式绑定 eastAsia=微软雅黑 的 <a:ea> 数: {tot_ea}")
cov = 100 * tot_ea / tot_runs if tot_runs else 0
print(f"覆盖率: {cov:.1f}%")
print("\n分页 (run, ea):")
bad = []
for name, runs, ea in detail:
    flag = "" if ea >= runs else "  ← 不足"
    if ea < runs:
        bad.append(name)
    print(f"  {name:16s} {runs:>4} {ea:>4}{flag}")
print(f"\n{'全部绑定 ✅' if not bad else f'存在未绑定页面 ❌: {bad}'}")
sys.exit(1 if bad else 0)
