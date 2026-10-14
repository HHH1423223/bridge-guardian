# -*- coding: utf-8 -*-
"""make_script.py —— 由 SPEC_content.json 生成 12 分钟逐页讲稿与时间分配表。

用法:
    <bundled-python> make_script.py            # 输出 讲稿_12分钟.md
    <bundled-python> make_script.py --out X.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROLE_HINT = {
    "s01_cover": "开场定调：30 秒内说清「我是谁、做了什么」",
    "s02_pain": "抛出问题：为什么要做，以及诚实的定位",
    "s03_arch": "给出答案的骨架：六层解耦、数据源可插拔",
    "s04_source": "工程兜底能力：双模式、断线不造假",
    "s05_scene": "全场高潮：三维可视化监测场景（放慢语速）",
    "s06_video": "视频替身：播放录屏期间只讲两句串场",
    "s07_risk": "解释高潮：颜色怎么随风险等级联动",
    "s08_rules": "技术核心：6 类可解释规则，每条说清为什么",
    "s09_loop": "业务价值：报警必须被处置才算闭环",
    "s10_data": "可信度：五表 + 审计留痕，历史可查可导出",
    "s11_security": "工程质量：安全防线与工程化清单",
    "s12_evidence": "硬证据：101 个用例、11 个测试文件与测试域覆盖",
    "s13_boundary": "诚实边界：做不到什么、下一步做什么",
    "s14_value": "收束金句：全场唯一金句页",
    "s15_thanks": "致谢收尾：回到一句承诺",
}


def fmt_sec(s: int) -> str:
    m, r = divmod(int(s), 60)
    return f"{m}:{r:02d}" if m else f"{r}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default=str(HERE / "_spec" / "SPEC_content.json"))
    ap.add_argument("--out", default=str(HERE / "讲稿_12分钟.md"))
    args = ap.parse_args()

    data = json.loads(Path(args.content).read_text(encoding="utf-8"))
    slides = data["slides"]
    total = sum(int(s.get("seconds") or 0) for s in slides)

    L = []
    L.append("# 桥体卫士 · 12 分钟答辩讲稿（单人主讲）\n")
    L.append(f"- 总时长预算：**{total} 秒 ≈ {total//60} 分 {total%60:02d} 秒**（赛制 12 分钟，预留 {720-total} 秒机动）")
    L.append("- 口径：不使用硬件实物；现场跑软件（模拟数据源 + 浏览器三维监测场景）")
    L.append("- 讲稿按 **4.5 字/秒** 中文口语速记；每页字数均已压在预算内")
    L.append("- 加粗处为重音；括号内为动作提示（不念出来）\n")

    L.append("## 一、时间分配表\n")
    L.append("| # | 页 | 小节 | 时长 | 累计 | 关键动作 |")
    L.append("|---|---|---|---|---|---|")
    acc = 0
    for i, s in enumerate(slides, 1):
        sec = int(s["seconds"])
        acc += sec
        L.append(
            f"| {i:02d} | {s.get('title') or '（封面）'} | {s.get('section') or '—'} | "
            f"{fmt_sec(sec)} | {fmt_sec(acc)} | {ROLE_HINT.get(s['slide_id'], '')} |"
        )
    L.append(f"\n合计 **{fmt_sec(total)}**；第 6 页视频占位页的 60 秒里，讲稿只占约 12 秒，其余留给视频本身。\n")

    L.append("## 二、逐页讲稿\n")
    for i, s in enumerate(slides, 1):
        notes = (s.get("notes") or "").strip()
        n = len([c for c in notes if c.strip()])
        L.append(f"### {i:02d} · {s.get('title') or '封面'}　`{fmt_sec(int(s['seconds']))}｜{n} 字`\n")
        if s["slide_id"] == "s06_video":
            L.append("> 本页为视频占位页：把录屏插进占位框，播放期间只讲下面两句。\n")
        L.append(notes if notes else "_（无讲稿）_")
        L.append("")

    L.append("## 三、现场衔接与兜底\n")
    L.append("- **第 5–7 页是全场重心**：切到浏览器三维监测场景，边讲边操作（旋转、切预设视角、看测点标注）。")
    L.append("- **第 6 页视频**：视频卡住就跳过，直接说「细节我口头补」，切回第 7 页继续讲风险联动，不要停在那儿等。")
    L.append("- **现场软件出问题**：模拟数据源本身就是兜底方案；实在打不开就只看 PPT，第 5 页的线框示意图能替代现场画面。")
    L.append("- **时间不够（超过 11 分钟）**：可压缩顺序为 第 11 页 → 第 10 页 → 第 3 页（各压 15 秒），**不要压缩第 5、8、12 页**。")
    L.append("- **评委追问**：口径依据见 `docs/答辩材料.md` 第六节；「不能说的话」清单见同文件第七节。\n")
    L.append("## 四、不能说的话（红线）\n")
    L.append("1. 不说「真实桥梁应变监测」——是**缩尺模型受载模拟**。")
    L.append("2. 不说「工程级标定 / 高精度 / 符合国家规范」——未做工程标定。")
    L.append("3. 不说「AI 智能预警 / 机器学习 / 预测分析」——只有可解释规则。")
    L.append("4. 不说「大数据 / 数字孪生」——统一说**三维可视化监测场景**。")
    L.append("5. 不承诺「±X 微应变精度」——输出是相对应变指标（无量纲）。")

    out = Path(args.out)
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"已生成讲稿: {out}")
    print(f"总时长预算: {total}s ({total//60}分{total%60:02d}秒)，机动 {720-total}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
