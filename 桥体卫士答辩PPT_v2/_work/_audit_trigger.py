# -*- coding: utf-8 -*-
"""Trigger-idiom probe: how is 'wait for a click' encoded, and how fast does one
click group finish? Read-only, in-memory."""
import io, os, re, time, zipfile, hashlib
from lxml import etree

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
Q = lambda t: "{%s}%s" % (P, t)
BASE = r"C:\Users\CX\Documents\GitHub\bridge guardian\桥体卫士答辩PPT_v2"
FILES = {
    "deliverable": os.path.join(BASE, "\u6865\u4f53\u536b\u58eb\u7b54\u8fa9PPT_12\u5206\u949f\u7248.pptx"),
    "preanim": os.path.join(BASE, "_work", "\u6865\u4f53\u536b\u58eb\u7b54\u8fa9PPT_12\u5206\u949f\u7248.preanim.pptx"),
    "v1perline": os.path.join(BASE, "_work", "\u6865\u4f53\u536b\u58eb\u7b54\u8fa9PPT_12\u5206\u949f\u7248.v1-perline.pptx"),
    "proto": os.path.join(BASE, "_work", "proto", "proto.pptx"),
    "anim_selftest": os.path.join(BASE, "_work", "anim_selftest.pptx"),
    "probe_noanim": os.path.join(BASE, "_work", "probe_noanim.pptx"),
}
out = []
def w(*a):
    s = " ".join(str(x) for x in a); out.append(s); print(s)

def load(path):
    d = open(path, "rb").read()
    return d, hashlib.sha256(d).hexdigest()

def mainseq(root):
    tim = root.find(Q("timing"))
    if tim is None:
        return None
    return tim.find("./%s/%s/%s/%s/%s/%s/%s" % (Q("tnLst"), Q("par"), Q("cTn"), Q("childTnLst"),
                                                Q("seq"), Q("cTn"), Q("childTnLst")))

def conds(ctn):
    return [(c.get("delay"), c.get("evt")) for c in ctn.findall("./%s/%s" % (Q("stCondLst"), Q("cond")))]

for label, path in FILES.items():
    if not os.path.exists(path):
        w("[%s] ABSENT" % label); continue
    data, h = load(path)
    zf = zipfile.ZipFile(io.BytesIO(data))
    sl = sorted([n for n in zf.namelist() if re.match(r"^ppt/slides/slide\d+\.xml$", n)],
                key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))
    w("")
    w("=" * 90)
    w("[%s] sha=%s slides=%d" % (label, h[:16], len(sl)))
    # global idiom histogram over ALL groups of ALL slides
    hist = {}
    inner_hist = {}
    eff_node_types = {}
    leaf = {}
    delays = []
    for n in sl:
        root = etree.fromstring(zf.read(n))
        ms = mainseq(root)
        if ms is None:
            continue
        for gp in ms.findall(Q("par")):
            top = gp.find(Q("cTn"))
            key = tuple(conds(top))
            hist[key] = hist.get(key, 0) + 1
            # inner par conds
            for ip in gp.findall("./%s/%s/%s/%s" % (Q("cTn"), Q("childTnLst"), Q("par"), Q("cTn"))):
                k2 = tuple(conds(ip))
                inner_hist[k2] = inner_hist.get(k2, 0) + 1
            for c in gp.iter(Q("cTn")):
                nt = c.get("nodeType")
                if nt:
                    eff_node_types[nt] = eff_node_types.get(nt, 0) + 1
                if c.get("presetClass") or c.get("presetID"):
                    delays.append((c.get("nodeType"), conds(c)))
                for leafname in ("set", "animEffect"):
                    for lf in c.findall("./%s/%s" % (Q("childTnLst"), Q(leafname))):
                        lc = lf.find("./%s/%s" % (Q("cBhvr"), Q("cTn")))
                        if lc is not None:
                            leaf[(leafname, lc.get("dur"))] = leaf.get((leafname, lc.get("dur")), 0) + 1
    w("  top-level (click group) wrapper p:cond histogram: %s" % (hist,))
    w("  2nd-level wrapper p:cond histogram:            %s" % (inner_hist,))
    w("  cTn nodeType histogram: %s" % (eff_node_types,))
    w("  leaf (set/animEffect) cTn dur histogram: %s" % (leaf,))
    # per-effect-node start delay histogram (effect node's own stCondLst)
    from collections import Counter
    cn = Counter()
    for nt, cs in delays:
        cn[(nt, tuple(cs))] += 1
    w("  effect-node (presetClass) nodeType+own-cond histogram: %s" % (dict(cn),))

    # per-group reveal timeline for the biggest group of the deck
    for probe in (1, 3, 7, 15):
        nm = "ppt/slides/slide%d.xml" % probe
        if nm not in zf.namelist():
            continue
        root = etree.fromstring(zf.read(nm))
        ms = mainseq(root)
        if ms is None:
            w("  slide %d: no mainSeq" % probe); continue
        for gi, gp in enumerate(ms.findall(Q("par")), 1):
            starts = []
            spans = []
            for c in gp.iter(Q("cTn")):
                if not (c.get("presetClass") or c.get("presetID")):
                    continue
                d = conds(c)
                try:
                    dly = int(d[0][0]) if d and d[0][0] is not None else 0
                except ValueError:
                    dly = -1
                # leaf duration under this effect node
                dur = 0
                for lf in ("set", "animEffect"):
                    for l in c.findall("./%s/%s" % (Q("childTnLst"), Q(lf))):
                        lc = l.find("./%s/%s" % (Q("cBhvr"), Q("cTn")))
                        if lc is not None:
                            try:
                                dur = max(dur, int(lc.get("dur") or 0))
                            except ValueError:
                                pass
                starts.append(dly); spans.append(dly + dur)
            if starts:
                w("  slide %2d group#%d: effects=%d own-start-delay min=%d max=%d distinct=%d | group finish≈%dms (leaf dur max=%d) topcond=%s"
                  % (probe, gi, len(starts), min(starts), max(starts), len(set(starts)), max(spans),
                     max(spans) - max(starts), conds(gp.find(Q("cTn")))))

# ---------------------------------------------------------------- source grep
w("")
w("=" * 90)
w("GENERATOR SOURCE: how is the click trigger written?")
for f in ("pptx_anim.py", "build_animated.py", "deck_style.py"):
    p = os.path.join(BASE, f)
    if not os.path.exists(p):
        continue
    txt = open(p, encoding="utf-8").read()
    for i, line in enumerate(txt.splitlines(), 1):
        if re.search(r"indefinite|stCondLst|cond\b|clickEffect|nodeType|delay=", line):
            w("  %-18s %4d | %s" % (f, i, line.strip()[:150]))

with open(os.path.join(BASE, "_work", "_trigger_report.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
