# -*- coding: utf-8 -*-
"""anim_grain.py —— 动画"颗粒度"量化：每页需要点几次、每次点放多少元素。

判据（用户要求"点一次切换一个动画，粗略一点，不要点一下出一行"）：
  - clicks: 顶层 par 数 = 需要点击的次数（越少越粗）
  - per_click: 每次点击带出多少个形状
  - bad: 一次点击只带 1 个形状的"碎步"（封面/收尾的第二次点击属于预期）

用法: <python> anim_grain.py deck.pptx
"""
from __future__ import annotations

import pathlib
import sys
import zipfile

from lxml import etree

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def slide_no(name):
    stem = pathlib.Path(name).stem
    return int("".join(c for c in stem if c.isdigit()))


def analyze(path):
    with zipfile.ZipFile(path) as z:
        names = sorted(
            (n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
            key=slide_no,
        )
        rows = []
        for n in names:
            root = etree.fromstring(z.read(n))
            timing = root.find("p:timing", NS)
            per_click, bad = [], []
            if timing is not None:
                seq = timing.find("p:tnLst/p:par/p:cTn/p:childTnLst/p:seq", NS)
                main = seq.find("p:cTn", NS) if seq is not None else None
                if main is not None:
                    for par in main.findall("p:childTnLst/p:par", NS):
                        # 每个顶层 par = 一次点击；它下面的所有 spTgt 都靠这一次点击带出
                        spids = [t.get("spid") for t in par.iter(f"{{{NS['p']}}}spTgt")]
                        # 去重：set 与 animEffect 各引用一次
                        uniq = list(dict.fromkeys(spids))
                        per_click.append(uniq)
                        anchors = par.findall(".//p:cTn[@nodeType='clickEffect']", NS)
                        if len(anchors) != 1:
                            bad.append(f"点击组内 clickEffect 数 = {len(anchors)}（应为 1）")
                        if len(uniq) <= 1:
                            bad.append("这次点击只带出 %d 个元素" % len(uniq))
            rows.append((slide_no(n), per_click, bad))
        return rows


if __name__ == "__main__":
    p = sys.argv[1]
    print(f"# {p}")
    print(f"{'页':>3} {'点击次数':>8} {'每次点击带出的元素数':<44} 问题")
    total = 0
    problems = []
    for no, per_click, bad in analyze(p):
        total += len(per_click)
        detail = " | ".join(f"{len(g)}个" for g in per_click) or "—"
        print(f"{no:>3} {len(per_click):>8} {detail:<44} {'; '.join(bad)}")
        problems += [f"第{no}页: {b}" for b in bad]
    print(f"\n全套合计 {total} 次点击")
    if problems:
        print(f"发现问题 {len(problems)} 个:")
        for x in problems:
            print("  x", x)
    else:
        print("颗粒度检查通过 ✅")
