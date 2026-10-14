# -*- coding: utf-8 -*-
"""FACTCHECK step 1: dump ALL visible text of the frozen PPTX (shapes + tables +
group shapes + graphicFrames) plus speaker notes, then a raw-XML <a:t> sweep as
an independent cross-check.  Read-only: never writes to the pptx."""
import sys, io, zipfile, re
from pptx import Presentation
from pptx.util import Emu

PPTX = sys.argv[1]
OUT = sys.argv[2]
raw = []


def w(s=""):
    raw.append(s)


def walk(shapes, indent="  "):
    for sh in shapes:
        st = sh.shape_type
        try:
            pos = "x=%.3f y=%.3f w=%.3f h=%.3f" % (
                sh.left / 914400, sh.top / 914400,
                sh.width / 914400, sh.height / 914400)
        except Exception:
            pos = "x=? y=? w=? h=?"
        w("%s[shape] name=%r type=%s id=%s %s" % (indent, sh.name, st, sh.shape_id, pos))
        if sh.shape_type == 6 or sh.__class__.__name__ == "GroupShape":
            w("%s  <group children>" % indent)
            walk(sh.shapes, indent + "    ")
            continue
        if getattr(sh, "has_text_frame", False):
            tf = sh.text_frame
            for pi, p in enumerate(tf.paragraphs):
                if p.text.strip():
                    w("%s  p%d: %r" % (indent, pi, p.text))
        if getattr(sh, "has_table", False):
            tbl = sh.table
            w("%s  TABLE %dx%d" % (indent, len(tbl.rows), len(tbl.columns)))
            for ri, row in enumerate(tbl.rows):
                cells = [c.text for c in row.cells]
                w("%s    row%d: %r" % (indent, ri, cells))
        if getattr(sh, "has_chart", False):
            ch = sh.chart
            w("%s  CHART type=%s" % (indent, ch.chart_type))
            try:
                cats = [str(c) for c in ch.plots[0].categories]
                w("%s    categories=%r" % (indent, cats))
            except Exception as e:
                w("%s    categories ERR %s" % (indent, e))
            for s in ch.series:
                w("%s    series %r = %r" % (indent, s.name, list(s.values)))
        # graphicFrame SmartArt / other embedded text lives in raw XML sweep below


prs = Presentation(PPTX)
w("#" * 78)
w("# PPTX TEXT DUMP  file=%s" % PPTX)
w("# slides=%d  size=%sx%s EMU (%sx%s in)" % (
    len(prs.slides), prs.slide_width, prs.slide_height,
    prs.slide_width / 914400, prs.slide_height / 914400))
w("#" * 78)

for idx, slide in enumerate(prs.slides, 1):
    w("")
    w("=" * 78)
    layout = slide.slide_layout.name
    w("SLIDE %d   layout=%r   shapes=%d" % (idx, layout, len(slide.shapes)))
    w("=" * 78)
    walk(slide.shapes)
    # notes
    if slide.has_notes_slide:
        nt = slide.notes_slide.notes_text_frame.text
        w("  --- NOTES ---")
        for line in nt.splitlines():
            w("  | " + line)
    else:
        w("  --- NOTES --- (none)")

# ---- raw XML sweep: every <a:t> per slide, independent of python-pptx API ----
w("")
w("#" * 78)
w("# RAW XML SWEEP  (every <a:t> text node per slide part)")
w("#" * 78)
z = zipfile.ZipFile(PPTX)
names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
names.sort(key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))
for n in names:
    xml = z.read(n).decode("utf-8")
    ts = re.findall(r"<a:t>(.*?)</a:t>", xml, re.S)
    ts = [t for t in ts if t.strip()]
    unesc = [t.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
              .replace("&quot;", '"').replace("&apos;", "'") for t in ts]
    w("")
    w("--- %s : %d text nodes ---" % (n, len(unesc)))
    for t in unesc:
        w("   " + repr(t))

# notes parts raw
w("")
w("#" * 78)
w("# RAW XML SWEEP  (notesSlides)")
w("#" * 78)
nn = [x for x in z.namelist() if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", x)]
nn.sort(key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))
for n in nn:
    xml = z.read(n).decode("utf-8")
    ts = [t for t in re.findall(r"<a:t>(.*?)</a:t>", xml, re.S) if t.strip()]
    w("")
    w("--- %s : %d text nodes ---" % (n, len(ts)))
    for t in ts:
        w("   " + repr(t))

txt = "\n".join(raw)
with io.open(OUT, "w", encoding="utf-8") as f:
    f.write(txt)
print("WROTE %s  (%d chars, %d lines)" % (OUT, len(txt), len(raw)))
print("slides=%d" % len(prs.slides))
for idx, slide in enumerate(prs.slides, 1):
    titles = []
    for sh in slide.shapes:
        if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip():
            titles.append(sh.text_frame.text.strip().replace("\n", " / ")[:60])
    print("S%-2d | %s" % (idx, " || ".join(titles[:4])))
