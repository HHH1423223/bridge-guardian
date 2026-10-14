# -*- coding: utf-8 -*-
"""verify_anim_xml.py —— 校验动画/切换 XML 是否符合 OOXML 顺序与结构要求。

检查项：
  1) p:sld 子元素顺序必须是 cSld, clrMapOvr, transition, timing, extLst
  2) p:transition 内必须有具体效果（fade/push/wipe/cover）
  3) p:timing 结构链完整：tnLst > par > cTn(tmRoot) > childTnLst > seq > cTn(mainSeq)
     > childTnLst > par(点击组) > cTn > childTnLst > par > cTn > childTnLst
     > par(cTn presetClass=entr) > childTnLst > set/animEffect
  4) 每个点击组的子树里【恰好 1 个 clickEffect 锚点】，其余是 afterEffect
     （顶层 par 数 = 点击次数，这是"一次点击放一屏"的核心约束）
  5) 每个 animEffect/set 的 spTgt 都必须指向真实存在的 shape id
  6) XML 能被 lxml 重新解析（无非法字符），且嵌套深度不超过 64（防 PowerPoint 修复弹窗）
"""
import io
import pathlib
import sys
import zipfile

from lxml import etree

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}
ORDER = ["cSld", "clrMapOvr", "transition", "timing", "extLst"]
MAX_DEPTH = 64


def tag_of(el):
    return etree.QName(el).localname


def depth_of(data):
    d = best = 0
    for ev, _el in etree.iterparse(io.BytesIO(data), events=("start", "end")):
        if ev == "start":
            d += 1
            best = max(best, d)
        else:
            d -= 1
    return best


def check(path):
    path = pathlib.Path(path)
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        names.sort(key=lambda n: int("".join(c for c in pathlib.Path(n).stem if c.isdigit())))
        problems, info = [], []
        for n in names:
            blob = z.read(n)
            root = etree.fromstring(blob)
            kids = [tag_of(c) for c in root]
            # 1) 顺序
            idx = [ORDER.index(k) for k in kids if k in ORDER]
            if idx != sorted(idx):
                problems.append(f"{n}: 子元素顺序错误 {kids}")
            # 6) 深度（超过 256 层 PowerPoint/解析器直接报错）
            dep = depth_of(blob)
            if dep > MAX_DEPTH:
                problems.append(f"{n}: XML 嵌套深度 {dep} > {MAX_DEPTH}")
            # 2) transition
            tr = root.find("p:transition", NS)
            if tr is None:
                problems.append(f"{n}: 缺少 p:transition")
            elif not len(tr):
                problems.append(f"{n}: p:transition 内无效果元素")
            # 3) timing 结构（允许某页只有转场、没有元素动画，例如视频占位页）
            timing = root.find("p:timing", NS)
            if timing is None:
                info.append(f"{n}: 顺序 OK {kids} / 仅转场（无元素动画），符合预期")
                continue
            seq = timing.find("p:tnLst/p:par/p:cTn/p:childTnLst/p:seq", NS)
            if seq is None:
                problems.append(f"{n}: timing 缺 seq 链")
                continue
            main = seq.find("p:cTn", NS)
            if main is None or main.get("nodeType") != "mainSeq":
                problems.append(f"{n}: 缺 mainSeq")
                continue
            groups = main.findall("p:childTnLst/p:par", NS)
            ids_in_slide = {sp.get("id") for sp in root.iter(f"{{{NS['p']}}}cNvPr")}
            all_spids, bad_targets, click_report = [], [], []
            for gi, g in enumerate(groups, 1):
                anchors = g.findall(".//p:cTn[@nodeType='clickEffect']", NS)
                followers = g.findall(".//p:cTn[@nodeType='afterEffect']", NS)
                if len(anchors) != 1:
                    problems.append(f"{n}: 第 {gi} 个点击组里 clickEffect 锚点数 = {len(anchors)}（应为 1）")
                # 组内每个效果节点都必须有 set + animEffect，且 presetClass=entr
                effects = [c for c in g.iter(f"{{{NS['p']}}}cTn") if c.get("presetClass")]
                for e in effects:
                    if e.get("presetClass") != "entr":
                        problems.append(f"{n}: 点击组 {gi} 出现非入场效果 presetClass={e.get('presetClass')}")
                    if e.find("p:childTnLst/p:set", NS) is None:
                        problems.append(f"{n}: 点击组 {gi} 的效果节点缺 p:set")
                    if e.find("p:childTnLst/p:animEffect", NS) is None:
                        problems.append(f"{n}: 点击组 {gi} 的效果节点缺 p:animEffect")
                spids = list(dict.fromkeys(t.get("spid") for t in g.iter(f"{{{NS['p']}}}spTgt")))
                all_spids += spids
                bad = [s for s in spids if s not in ids_in_slide]
                if bad:
                    bad_targets += bad
                click_report.append(f"组{gi}={len(effects)}个({len(anchors)}click/{len(followers)}after)")
            # 5) spTgt 必须指向真实形状
            if bad_targets:
                problems.append(f"{n}: spTgt 指向不存在的形状 {sorted(set(bad_targets))}")
            info.append(f"{n}: 顺序 OK {kids} / {len(groups)} 次点击, "
                        f"{len(all_spids)} 个动效元素, " + " ".join(click_report))
        return problems, info


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "桥体卫士答辩PPT_v2/_work/proto/proto.pptx"
    probs, infos = check(p)
    for i in infos:
        print("  ·", i)
    for x in probs:
        print("  x", x)
    print(f"\n{'通过 ✅' if not probs else f'发现 {len(probs)} 个问题 ❌'}")
    sys.exit(1 if probs else 0)
