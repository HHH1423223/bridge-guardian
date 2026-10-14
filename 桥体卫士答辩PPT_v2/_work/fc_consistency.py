# -*- coding: utf-8 -*-
"""FACTCHECK step 3: (a) verbatim PPT-visible-text vs SPEC_*.json consistency,
(b) forbidden-term / red-line scan with slide numbers, (c) ESP32 / 压力传感器
location scan.  Read-only."""
import sys, io, json, re
from pptx import Presentation

ROOT = r"C:\Users\CX\Documents\GitHub\bridge guardian\PPTV2"  # placeholder, overridden
V2 = sys.argv[1]      # ...\桥体卫士答辩PPT_v2
PPTX = sys.argv[2]

content = json.load(io.open(V2 + r"\_spec\SPEC_content.json", encoding="utf-8"))
diagrams = json.load(io.open(V2 + r"\_spec\SPEC_diagrams.json", encoding="utf-8"))

# ---- replicate builder constants (build_deck.py) ----
NO_CHROME_TITLE_IDS = {"s01_cover", "s15_thanks"}
FOOTER = "桥体卫士 · 桥梁结构健康监测缩尺原型"


def el_texts(el):
    """Visible strings produced by one spec element (text/table/chart)."""
    out = []
    t = el.get("type")
    if t == "text":
        if el.get("runs"):
            out.append("".join(str(r.get("t", "")) for r in el["runs"]))
        elif el.get("text") is not None:
            out.append(str(el["text"]))
    elif t == "table":
        for row in el.get("rows") or []:
            for c in row:
                out.append(str(c))
    elif t == "chart":
        for s in el.get("series") or []:
            if s.get("name"):
                out.append(str(s["name"]))
        if el.get("x_label"):
            out.append(str(el["x_label"]))
        if el.get("y_label"):
            out.append(str(el["y_label"]))
        for rl in el.get("ref_lines") or []:
            if rl.get("label"):
                out.append(str(rl["label"]))
        for c in el.get("categories") or []:
            out.append(str(c))
    return out


figs = {}
for f in diagrams.get("figures") or []:
    figs.setdefault(f.get("for_slide"), []).append(f)

slides = content["slides"]
expected = []          # list of dict(slide_index, slide_id, kind, text)
for i, s in enumerate(slides, 1):
    sid = s["slide_id"]
    exp = []
    for f in figs.get(sid, []):
        for el in f.get("elements") or []:
            for t in el_texts(el):
                exp.append(("fig:" + str(el.get("id")), t))
    for el in s.get("elements") or []:
        for t in el_texts(el):
            exp.append(("content:" + str(el.get("id")), t))
    if s.get("chrome", "standard") == "standard":
        if s.get("section"):
            exp.append(("chrome:section", str(s["section"])))
        if s.get("title"):
            exp.append(("chrome:title", str(s["title"])))
        exp.append(("chrome:footer", FOOTER))
        exp.append(("chrome:pageno", "%02d / %d" % (i, len(slides))))
    else:
        if sid in NO_CHROME_TITLE_IDS and s.get("title"):
            exp.append(("chrome:nochrome_title", str(s["title"])))
    expected.append({"i": i, "sid": sid, "chrome": s.get("chrome", "standard"),
                     "title": s.get("title"), "section": s.get("section"),
                     "notes": s.get("notes") or "", "exp": exp})

# ---- actual PPT text ----
prs = Presentation(PPTX)


def shape_texts(shapes, acc):
    for sh in shapes:
        if sh.__class__.__name__ == "GroupShape" or sh.shape_type == 6:
            shape_texts(sh.shapes, acc)
            continue
        if getattr(sh, "has_text_frame", False):
            for p in sh.text_frame.paragraphs:
                if p.text.strip():
                    acc.append(p.text)
        if getattr(sh, "has_table", False):
            for row in sh.table.rows:
                for c in row.cells:
                    if c.text.strip():
                        acc.append(c.text)
        if getattr(sh, "has_chart", False):
            try:
                for cat in sh.chart.plots[0].categories:
                    acc.append(str(cat))
            except Exception:
                pass
            for s in sh.chart.series:
                if s.name:
                    acc.append(str(s.name))
                for v in s.values:
                    acc.append(str(v))


actual = []
for idx, sl in enumerate(prs.slides, 1):
    acc = []
    shape_texts(sl.shapes, acc)
    notes = sl.notes_slide.notes_text_frame.text if sl.has_notes_slide else ""
    actual.append({"i": idx, "texts": acc, "notes": notes})

print("=" * 78)
print("A. PAGE ORDER / slide_id MAPPING")
print("=" * 78)
ok_order = len(actual) == len(expected)
print("PPTX slides = %d ; SPEC slides = %d ; equal = %s" % (len(actual), len(expected), ok_order))
for e, a in zip(expected, actual):
    print("  p%-2d %-14s chrome=%-8s title=%r" % (e["i"], e["sid"], e["chrome"], e["title"]))

print()
print("=" * 78)
print("B. VERBATIM TEXT DIFF  (expected-from-spec  vs  actual-in-pptx)")
print("=" * 78)
tot_missing = tot_extra = 0
for e, a in zip(expected, actual):
    exp_map = {}
    for kind, t in e["exp"]:
        exp_map.setdefault(t, []).append(kind)
    act_set = set(a["texts"])
    missing = [(k, t) for t, ks in exp_map.items() for k in ks if t not in act_set]
    # chart numeric labels are builder-generated -> whitelist pure numbers/dates
    def is_derived(t):
        return bool(re.fullmatch(r"-?\d+(\.\d+)?", t or ""))
    extra = [t for t in a["texts"]
             if t not in exp_map and not is_derived(t)]
    if missing or extra:
        print("--- slide %d (%s) ---" % (e["i"], e["sid"]))
        for k, t in missing:
            print("   MISSING in pptx  [%s] %r" % (k, t))
        for t in extra:
            print("   EXTRA in pptx    %r" % t)
        tot_missing += len(missing)
        tot_extra += len(extra)
print("TOTAL missing = %d ; TOTAL extra = %d" % (tot_missing, tot_extra))

print()
print("=" * 78)
print("C. NOTES vs SPEC notes (verbatim)")
print("=" * 78)
nbad = 0
for e, a in zip(expected, actual):
    if e["notes"] != a["notes"]:
        nbad += 1
        print("--- slide %d (%s) DIFFERS ---" % (e["i"], e["sid"]))
        print("   SPEC : %r" % e["notes"][:300])
        print("   PPTX : %r" % a["notes"][:300])
print("notes mismatched slides = %d / %d" % (nbad, len(expected)))

print()
print("=" * 78)
print("D. RED-LINE / FORBIDDEN TERM SCAN")
print("=" * 78)
FORBIDDEN = ["数字孪生", "机器学习", "人工智能", "大数据", "微应变", "工程级精度",
             "高精度", "真实桥梁应变监测", "我们", "团队", "领先", "革命性",
             "AI", "预测", "深度学习", "智能算法"]
for term in FORBIDDEN:
    hits = []
    for a in actual:
        for t in a["texts"]:
            if term in t:
                hits.append(("p%d/body" % a["i"], t))
        if term in (a["notes"] or ""):
            hits.append(("p%d/NOTES" % a["i"], a["notes"]))
    if hits:
        print("!! FORBIDDEN %r -> %d hit(s)" % (term, len(hits)))
        for loc, t in hits:
            idx = t.find(term)
            print("     %-10s ...%s..." % (loc, t[max(0, idx - 25):idx + 25]))
    else:
        print("   clean: %r" % term)

print()
print("=" * 78)
print("D2. '工程级' OCCURRENCES  (allowed ONLY in s13 negative sentence)")
print("=" * 78)
ALLOWED_GONGCHENGJI = "未做工程级标定与量值溯源"
gc_total = gc_bad = 0
for a in actual:
    for t in a["texts"]:
        if "工程级" in t:
            gc_total += 1
            ok = (a["i"] == 13 and t.strip() == ALLOWED_GONGCHENGJI)
            if not ok:
                gc_bad += 1
            print("   p%-2d body  %s  %r" % (a["i"], "OK  " if ok else "BAD ", t))
    if "工程级" in (a["notes"] or ""):
        gc_total += 1
        print("   p%-2d NOTES %r" % (a["i"], a["notes"]))
print("   total '工程级' occurrences = %d ; disallowed = %d" % (gc_total, gc_bad))

print()
print("=" * 78)
print("D3. '3D' OCCURRENCES  (allowed only inside three.js / WebGL tech names)")
print("=" * 78)
import re as _re
d3_total = d3_bad = 0
for a in actual:
    pool = list(a["texts"]) + ([a["notes"]] if a["notes"] else [])
    for t in pool:
        for m in _re.finditer("3D", t):
            d3_total += 1
            ctx = t[max(0, m.start() - 40):m.start() + 40]
            # allow only when the token sits inside a technical identifier
            technical = bool(_re.search(r"(three\.js|WebGL)[^ ]{0,12}3D|3D[^ ]{0,12}(three\.js|WebGL)", t)) \
                or "three.js r160" in t or "webgl" in t.lower()
            # narrative-style hit = 3D followed/preceded by CJK without a tech token
            narrative = bool(_re.search(r"3D\s*[\u4e00-\u9fff]|[\u4e00-\u9fff]\s*3D", t))
            ok = (not narrative)
            if not ok:
                d3_bad += 1
            print("   p%-2d %-5s %s ...%s..." % (a["i"], "body" if t in a["texts"] else "NOTES",
                                                 "OK  " if ok else "BAD ", ctx))
print("   total '3D' occurrences = %d ; narrative(disallowed) = %d" % (d3_total, d3_bad))

print()
print("=" * 78)
print("E. '压力传感器' / 'ESP32' / '传感器' LOCATIONS")
print("=" * 78)
for term in ["压力传感器", "ESP32", "传感器", "应变片", "硬件"]:
    print("-- %r --" % term)
    for a in actual:
        for t in a["texts"]:
            if term in t:
                print("   p%-2d body : %r" % (a["i"], t))
        if term in (a["notes"] or ""):
            print("   p%-2d NOTES: contains %r" % (a["i"], term))
