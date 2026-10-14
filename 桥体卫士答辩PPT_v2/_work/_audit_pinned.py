# -*- coding: utf-8 -*-
"""Pinned in-memory audit: reads each PPTX ONCE into memory (with a stability
re-check) and measures everything from those bytes. Writes nothing except this
report file under _work. Never touches the decks."""
import hashlib
import io
import os
import re
import sys
import time
import zipfile
from lxml import etree
from pptx import Presentation

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
Q = lambda t: "{%s}%s" % (P, t)
BASE = r"C:\Users\CX\Documents\GitHub\bridge guardian\桥体卫士答辩PPT_v2"
DELIV = os.path.join(BASE, "\u6865\u4f53\u536b\u58eb\u7b54\u8fa9PPT_12\u5206\u949f\u7248.pptx")
PREANIM = os.path.join(BASE, "_work", "\u6865\u4f53\u536b\u58eb\u7b54\u8fa9PPT_12\u5206\u949f\u7248.preanim.pptx")
V1 = os.path.join(BASE, "_work", "\u6865\u4f53\u536b\u58eb\u7b54\u8fa9PPT_12\u5206\u949f\u7248.v1-perline.pptx")
CORE = [("deliverable", DELIV), ("preanim", PREANIM), ("v1perline", V1)]
EXTRA = [("rebuild_a", os.path.join(BASE, "_work", "rebuild_a.pptx")),
         ("rebuild_b", os.path.join(BASE, "_work", "rebuild_b.pptx")),
         ("anim_selftest", os.path.join(BASE, "_work", "anim_selftest.pptx")),
         ("clean_check", os.path.join(BASE, "_work", "clean_check.pptx")),
         ("probe_copy", os.path.join(BASE, "_work", "probe_copy.pptx")),
         ("probe_noanim", os.path.join(BASE, "_work", "probe_noanim.pptx"))]

out = []
def w(*a):
    out.append(" ".join(str(x) for x in a))

def sha(b):
    return hashlib.sha256(b).hexdigest()

def snap(path):
    """Return (bytes, sha256, stable, mtime) read entirely into memory."""
    last = None
    for _ in range(6):
        d1 = open(path, "rb").read()
        h1 = sha(d1)
        time.sleep(0.7)
        d2 = open(path, "rb").read()
        h2 = sha(d2)
        last = (d2, h2)
        if h1 == h2:
            return d2, h2, True, os.path.getmtime(path)
    return last[0], last[1], False, os.path.getmtime(path)

def sl_parts(zf):
    ns = [n for n in zf.namelist() if re.match(r"^ppt/slides/slide\d+\.xml$", n)]
    return sorted(ns, key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))

def nt_parts(zf):
    ns = [n for n in zf.namelist() if re.match(r"^ppt/notesSlides/notesSlide\d+\.xml$", n)]
    return sorted(ns, key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)))

def depth(e):
    d = 0
    while e is not None:
        d += 1
        e = e.getparent()
    return d

def loc(t):
    return t.split("}")[-1] if isinstance(t, str) else str(t)

TR_RE = r"<p:transition\b[^>]*?/>|<p:transition\b.*?</p:transition>"
TM_RE = r"<p:timing\b.*?</p:timing>"

def strip_anim(raw):
    s = raw.decode("utf-8")
    ntr = len(re.findall(TR_RE, s, flags=re.S))
    s = re.sub(TR_RE, "", s, flags=re.S)
    ntm = len(re.findall(TM_RE, s, flags=re.S))
    s = re.sub(TM_RE, "", s, flags=re.S)
    return s.encode("utf-8"), ntr, ntm

def mainseq_of(root):
    tim = root.find(Q("timing"))
    if tim is None:
        return None, None
    for path in ("./%s/%s/%s[@nodeType='tmRoot']/%s/%s/%s[@nodeType='mainSeq']/%s",
                 "./%s/%s/%s/%s/%s/%s/%s"):
        ms = tim.find(path % (Q("tnLst"), Q("par"), Q("cTn"), Q("childTnLst"),
                              Q("seq"), Q("cTn"), Q("childTnLst")))
        if ms is not None:
            return ms, tim
    return None, tim

def analyze(data, label, path):
    zf = zipfile.ZipFile(io.BytesIO(data))
    w("")
    w("#" * 96)
    w("FILE[%s] %s" % (label, path))
    w("  size=%d sha256=%s snapshot_stable=%s mtime=%s" % (
        len(data), sha(data), SNAP[label][2],
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(SNAP[label][3]))))
    w("  zip.testzip()=%r entries=%d" % (zf.testzip(), len(zf.namelist())))

    worst = []
    perr = 0
    for n in zf.namelist():
        if not (n.endswith(".xml") or n.endswith(".rels")):
            continue
        try:
            root = etree.fromstring(zf.read(n))
        except Exception as ex:
            perr += 1
            w("  !! XML PARSE FAIL %s %s" % (n, ex))
            continue
        d, t = max((depth(e), e.tag) for e in root.iter() if isinstance(e.tag, str))
        worst.append((d, n, loc(t)))
    worst.sort(reverse=True)
    w("  XML parts ok=%d parse_errors=%d ; deepest overall: %s" % (len(worst), perr, worst[0]))
    w("  parts deeper than 64: %s" % ([x for x in worst if x[0] > 64] or "NONE"))
    w("  top-3 depths: %s" % (worst[:3],))

    try:
        prs = Presentation(io.BytesIO(data))
        w("  python-pptx Presentation() OK: slides=%d sldSz=%dx%d EMU = %.4f x %.4f in" % (
            len(prs.slides), prs.slide_width, prs.slide_height,
            prs.slide_width / 914400, prs.slide_height / 914400))
    except Exception as ex:
        w("  !! python-pptx OPEN FAILED: %r" % (ex,))
        prs = None

    # presentation.xml sldSz raw + sldIdLst count
    proot = etree.fromstring(zf.read("ppt/presentation.xml"))
    sz = proot.find(Q("sldSz"))
    ids = proot.find(Q("sldIdLst"))
    w("  presentation.xml: sldSz=%s ; sldIdLst children=%d" % (
        dict(sz.attrib) if sz is not None else None, len(ids) if ids is not None else -1))

    rows = []
    for n in sl_parts(zf):
        idx = int(re.search(r"(\d+)", n.split("/")[-1]).group(1))
        raw = zf.read(n)
        root = etree.fromstring(raw)
        idname = {c.get("id"): c.get("name") for c in root.iter(Q("cNvPr"))}
        order = [loc(c.tag) for c in root if isinstance(c.tag, str)]
        trs = root.findall(Q("transition"))
        tr_children = [loc(c.tag) for t in trs for c in t]
        tr_attrs = {k.split("}")[-1]: v for k, v in trs[0].attrib.items()} if trs else {}
        ids_all = [c.get("id") for c in root.iter(Q("cTn"))]
        dup = sorted({i for i in ids_all if i is not None and ids_all.count(i) > 1})
        groups = []
        ms, tim = mainseq_of(root)
        if ms is not None:
            for gp in ms.findall(Q("par")):
                ctn = gp.find(Q("cTn"))
                conds = [(c.get("delay"), c.get("evt")) for c in
                         (ctn.findall("./%s/%s" % (Q("stCondLst"), Q("cond"))) if ctn is not None else [])]
                nts, spids, eff = {}, [], []
                for c in gp.iter(Q("cTn")):
                    if c.get("nodeType"):
                        nts[c.get("nodeType")] = nts.get(c.get("nodeType"), 0) + 1
                    if c.get("presetClass") or c.get("presetID"):
                        eff.append(c)
                    try:
                        pass
                    except Exception:
                        pass
                for sp in gp.iter(Q("spTgt")):
                    spids.append(sp.get("spid"))
                seen = []
                for s in spids:
                    if s not in seen:
                        seen.append(s)
                durs = []
                for c in eff:
                    try:
                        durs.append(int(c.get("dur") or 0))
                    except ValueError:
                        durs.append(-1)
                groups.append(dict(
                    conds=conds, nts=nts, n_eff=len(eff), distinct=seen,
                    names=[idname.get(s, "!!MISSING:%s" % s) for s in seen],
                    classes=sorted({c.get("presetClass") for c in eff}),
                    pids=sorted({c.get("presetID") for c in eff}),
                    noset=[c.get("id") for c in eff
                           if c.find("./%s/%s" % (Q("childTnLst"), Q("set"))) is None],
                    noanim=[c.get("id") for c in eff
                            if c.find("./%s/%s" % (Q("childTnLst"), Q("animEffect"))) is None],
                    durs=durs,
                    lvl=[(c.get("id"), c.get("nodeType"), c.get("presetClass"), c.get("presetID"),
                          c.get("dur"), depth(c)) for c in gp.iter(Q("cTn"))]))
        badcls = [(c.get("id"), c.get("presetClass")) for c in root.iter(Q("cTn"))
                  if (c.get("presetClass") or c.get("presetID")) and c.get("presetClass") != "entr"]
        noset = [c.get("id") for c in root.iter(Q("cTn"))
                 if (c.get("presetClass") or c.get("presetID"))
                 and c.find("./%s/%s" % (Q("childTnLst"), Q("set"))) is None]
        noanim = [c.get("id") for c in root.iter(Q("cTn"))
                  if (c.get("presetClass") or c.get("presetID"))
                  and c.find("./%s/%s" % (Q("childTnLst"), Q("animEffect"))) is None]
        allsp = {s.get("spid") for s in root.iter(Q("spTgt"))}
        rows.append(dict(idx=idx, part=n, groups=groups, order=order, ntr=len(trs),
                         trc=tr_children, tra=tr_attrs, tim=tim is not None,
                         dup=dup, badcls=badcls, noset=noset, noanim=noanim,
                         missing=sorted(s for s in allsp if s not in idname),
                         ncn=len(idname), xmllen=len(raw), raw=raw, root=root,
                         maxdepth=max(depth(e) for e in root.iter() if isinstance(e.tag, str))))
    w("  slides=%d  TOTAL top-level click groups=%d  per-slide=%s" % (
        len(rows), sum(len(r["groups"]) for r in rows), [len(r["groups"]) for r in rows]))
    geo = {}
    if prs is not None:
        for i, sl in enumerate(prs.slides, 1):
            geo[i] = {str(sh.shape_id): (sh.name, sh.top, sh.left, sh.width, sh.height)
                      for sh in sl.shapes}
    for r in rows:
        i = r["idx"]
        w("  slide %2d | clicks=%d | transition=%d%s%s | timing=%s | cNvPr=%d | xml=%dB | maxdepth=%d" % (
            i, len(r["groups"]), r["ntr"], r["trc"], (" attrs=%s" % r["tra"]) if r["tra"] else "",
            r["tim"], r["ncn"], r["xmllen"], r["maxdepth"]))
        w("        sld order=%s" % (r["order"],))
        for tag, lst in (("dup cTn ids", r["dup"]), ("presetClass!=entr", r["badcls"]),
                         ("effect cTn missing p:set", r["noset"]),
                         ("effect cTn missing p:animEffect", r["noanim"]),
                         ("spTgt spid not in slide", r["missing"])):
            if lst:
                w("        !! %s: %s" % (tag, lst))
        for gi, g in enumerate(r["groups"], 1):
            w("        click#%d cond=%s nodeTypes=%s effects=%d distinctTargets=%d class=%s presetID=%s sum(dur)=%dms" % (
                gi, g["conds"], g["nts"], g["n_eff"], len(g["distinct"]), g["classes"], g["pids"], sum(g["durs"])))
            w("            names(%d): %s" % (len(g["names"]), ", ".join(g["names"][:10]) +
                                            (" ..." if len(g["names"]) > 10 else "")))
            if i in geo:
                tail = []
                for s in g["distinct"][-4:]:
                    gg = geo[i].get(str(s))
                    tail.append("%s(top=%.2fin h=%.2fin)" % (gg[0], (gg[1] or 0) / 914400.0, (gg[4] or 0) / 914400.0) if gg else s)
                w("            last-targets geo: %s" % (", ".join(tail),))
    return dict(rows=rows, zf=zf, data=data, path=path, worst=worst)

# ------------------------------------------------------------------ run
SNAP = {}
RES = {}
for label, path in CORE + [(l, p) for l, p in EXTRA if os.path.exists(p)]:
    d, h, stable, mt = snap(path)
    SNAP[label] = (d, h, stable, mt)
for label, path in CORE:
    d, h, stable, mt = SNAP[label]
    RES[label] = analyze(d, label, path)

w("")
w("#" * 96)
w("ITEM 3: CONTENT-UNCHANGED PROOF (raw-byte strip of p:transition + p:timing)")
def pmap(zf):
    return {n: sha(zf.read(n)) for n in zf.namelist()}

for other in ("preanim", "v1perline"):
    a, b = RES["deliverable"], RES[other]
    w("")
    w("  deliverable vs %s" % other)
    w("    base sha=%s" % SNAP[other][1])
    ma, mb = pmap(a["zf"]), pmap(b["zf"])
    onlya = sorted(set(ma) - set(mb))
    onlyb = sorted(set(mb) - set(ma))
    diff = sorted(n for n in set(ma) & set(mb) if ma[n] != mb[n])
    w("    entries: A=%d B=%d onlyA=%s onlyB=%s differing=%d" % (len(ma), len(mb), onlya, onlyb, len(diff)))
    w("    differing entries: %s" % (diff if len(diff) <= 40 else diff[:40] + ["..."]))
    an = {n.split("/")[-1]: n for n in sl_parts(a["zf"])}
    bn = {n.split("/")[-1]: n for n in sl_parts(b["zf"])}
    ident, non = 0, []
    for k in sorted(an, key=lambda x: int(re.search(r"(\d+)", x).group(1))):
        if k not in bn:
            non.append((k, "absent in base"))
            continue
        ra, ta, ma_ = strip_anim(a["zf"].read(an[k]))
        rb, tb, mb_ = strip_anim(b["zf"].read(bn[k]))
        if ra == rb:
            ident += 1
        else:
            non.append((k, "differs lenA=%d lenB=%d" % (len(ra), len(rb))))
    w("    slides byte-identical after stripping transition+timing: %d/%d" % (ident, len(an)))
    for k, why in non:
        w("      !! %s %s" % (k, why))
    if non and non[0][1].startswith("differs"):
        k = non[0][0]
        sa = strip_anim(a["zf"].read(an[k]))[0].decode()
        sb = strip_anim(b["zf"].read(bn[k]))[0].decode()
        j = 0
        while j < min(len(sa), len(sb)) and sa[j] == sb[j]:
            j += 1
        w("      first divergence slide %s at char %d" % (k, j))
        w("        A: %s" % sa[max(0, j - 100):j + 250].replace("\n", " "))
        w("        B: %s" % sb[max(0, j - 100):j + 250].replace("\n", " "))
    na = {n.split("/")[-1]: sha(a["zf"].read(n)) for n in nt_parts(a["zf"])}
    nb = {n.split("/")[-1]: sha(b["zf"].read(n)) for n in nt_parts(b["zf"])}
    w("    notesSlides A=%d B=%d identical=%d differing=%s" % (
        len(na), len(nb), sum(1 for k in na if nb.get(k) == na[k]),
        sorted(k for k in set(na) | set(nb) if na.get(k) != nb.get(k))))

# ------------------------------------------------------------------ summary
w("")
w("#" * 96)
w("ITEM 1/2/4 SUMMARY")
for label in [l for l, _ in CORE] + [l for l, _ in EXTRA if l in RES]:
    r = RES.get(label)
    if not r:
        continue
    w("  %-14s totalClicks=%-4d perSlide=%s" % (label, sum(len(x["groups"]) for x in r["rows"]),
                                                [len(x["groups"]) for x in r["rows"]]))
dg = RES["deliverable"]
w("")
w("  deliverable sha256 = %s" % SNAP["deliverable"][1])
w("  slides = %d" % len(dg["rows"]))
w("  slides needing >3 clicks: %s" % ([x["idx"] for x in dg["rows"] if len(x["groups"]) > 3] or "NONE"))
multi = [(x["idx"], gi, g["nts"].get("clickEffect", 0))
         for x in dg["rows"] for gi, g in enumerate(x["groups"], 1) if g["nts"].get("clickEffect", 0) > 1]
w("  click groups with >1 nodeType=clickEffect: %s" % (multi or "NONE"))
ge3 = sorted({g["nts"].get("clickEffect", 0) for x in dg["rows"] for g in x["groups"]})
w("  distinct clickEffect counts per group: %s" % ge3)
w("  any effect node presetClass != entr: %s" % ([x["idx"] for x in dg["rows"] if x["badcls"]] or "NONE"))
w("  any effect node missing p:set: %s" % ([x["idx"] for x in dg["rows"] if x["noset"]] or "NONE"))
w("  any effect node missing p:animEffect: %s" % ([x["idx"] for x in dg["rows"] if x["noanim"]] or "NONE"))
w("  any dangling spTgt spid: %s" % ([x["idx"] for x in dg["rows"] if x["missing"]] or "NONE"))
w("  any duplicate cTn id: %s" % ([x["idx"] for x in dg["rows"] if x["dup"]] or "NONE"))
w("  sld child order violations: %s" % ([x["idx"] for x in dg["rows"]
                                         if x["order"] != ["cSld", "clrMapOvr"] + (["transition"] if x["ntr"] else [])
                                         + (["timing"] if x["tim"] else [])] or "NONE"))
w("  slides with != 1 p:transition: %s" % ([x["idx"] for x in dg["rows"] if x["ntr"] != 1] or "NONE"))
w("  transitions without a real effect child: %s" % ([x["idx"] for x in dg["rows"]
                                                      if not [c for c in x["trc"] if c != "sndAc"]] or "NONE"))
w("  transition effect per slide: %s" % ([ (x["idx"], x["trc"]) for x in dg["rows"] ]))
w("  WARNING any part depth>64: %s" % ([t for t in dg["worst"] if t[0] > 64] or "NONE",))
w("  max depth overall (incl. all parts) = %s" % (dg["worst"][0],))
w("  slide2: timing=%s transition=%s order=%s" % (dg["rows"][1]["tim"], dg["rows"][1]["trc"], dg["rows"][1]["order"]))
w("  first-click target counts slides 3-14: %s" % ([len(x["groups"][0]["distinct"]) for x in dg["rows"][2:14]],))
w("  second-click target counts slides 3-14: %s" % ([len(x["groups"][1]["distinct"]) for x in dg["rows"][2:14]],))
w("  second-click shape names (slides 3,6,15): %s | %s | %s" % (
    dg["rows"][2]["groups"][1]["names"], dg["rows"][5]["groups"][1]["names"],
    dg["rows"][14]["groups"][0]["names"]))
w("  first-click nodeTypes slide3 = %s ; slide7 = %s" % (
    dg["rows"][2]["groups"][0]["nts"], dg["rows"][6]["groups"][0]["nts"]))
tot = sum(len(x["groups"]) for x in dg["rows"])
w("  TOTAL CLICKS = %d  (claim 27)" % tot)

# raw xml of one group for trigger semantics
root = etree.fromstring(dg["rows"][0]["raw"])
ms, tim = mainseq_of(root)
gp = ms.findall(Q("par"))[0]
s = etree.tostring(gp, pretty_print=True).decode()
w("")
w("RAW first click group, slide 1 (verbatim, %d lines):" % len(s.splitlines()))
for ln in s.splitlines():
    w("    " + ln)

with open(os.path.join(BASE, "_work", "_audit_report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n".join(out[:60]))
print("... full report: _work\\_audit_report.txt (%d lines)" % len(out))
