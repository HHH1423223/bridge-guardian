# -*- coding: utf-8 -*-
"""make_script_docx.py —— 把《讲稿_12分钟.md》转成可打印的 Word 文档。

设计目标（答辩现场实用优先）：
  1. 表格不跨页断裂、表头行跨页自动重复（打印/翻页时不会看不懂列）；
  2. 每页讲稿独立成块，页标题带「时长 + 字数」，方便卡时间；
  3. 讲稿正文用较大字号与行距（台上照着念不费眼），加粗重音保留；
  4. 中文显式指定 eastAsia 字体（python-docx 只设 font.name 对中文无效）；
  5. 页脚带页码，方便多人分工时对页。

用法:
    <bundled-python> make_script_docx.py
    <bundled-python> make_script_docx.py --md 讲稿_12分钟.md --out 讲稿_12分钟.docx
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent

FONT_CN = "微软雅黑"
FONT_EN = "Segoe UI"
INK = RGBColor(0x0B, 0x1B, 0x2B)
NAVY = RGBColor(0x0E, 0x3F, 0x8C)
TEAL = RGBColor(0x00, 0x9E, 0x92)
SLATE = RGBColor(0x47, 0x55, 0x69)
SLATE_LIGHT = RGBColor(0x8A, 0x97, 0xA8)
RED = RGBColor(0xC0, 0x2B, 0x30)
NAVY_HEX = "0E3F8C"
ROW_ALT_HEX = "F2F6FC"


# ---------------------------------------------------------------- 基础工具


def set_run(run, size=10.5, bold=False, color=INK, font_cn=FONT_CN, font_en=FONT_EN, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font_en
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), font_en)
    rFonts.set(qn("w:hAnsi"), font_en)
    rFonts.set(qn("w:eastAsia"), font_cn)
    return run


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    el = OxmlElement("w:shd")
    el.set(qn("w:val"), "clear")
    el.set(qn("w:color"), "auto")
    el.set(qn("w:fill"), hex_fill)
    tcPr.append(el)


def cell_text(cell, text, size=10, bold=False, color=INK, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    set_run(p.add_run(text), size=size, bold=bold, color=color)


def repeat_header(row):
    """表头行跨页重复（打印时每页都有列名）。"""
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def keep_together(p):
    """段中不分页 + 与下段同页。"""
    pPr = p._p.get_or_add_pPr()
    for tag in ("w:keepNext", "w:keepLines"):
        el = OxmlElement(tag)
        el.set(qn("w:val"), "true")
        pPr.append(el)


def no_row_split(row):
    """表格行不跨页断裂。"""
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    trPr.append(el)


def add_page_number_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("桥体卫士 · 12 分钟答辩讲稿　第 "), size=8, color=SLATE_LIGHT)
    run = p.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._element.addnext(fld)
    set_run(p.add_run(" 页"), size=8, color=SLATE_LIGHT)


# ---------------------------------------------------------------- Markdown 解析


def parse_inline(text):
    """把 **粗体** 拆成 (片段, 是否粗体)。"""
    out = []
    for i, seg in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if seg == "":
            continue
        out.append((seg, i % 2 == 1))
    return out or [(text, False)]


def add_md_paragraph(doc, text, size=10.5, color=INK, space_after=6, indent_left=0,
                     align=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.35, keep=False):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(0)
    pf.line_spacing = line_spacing
    if indent_left:
        pf.left_indent = Cm(indent_left)
    for seg, bold in parse_inline(text):
        seg = seg.replace("`", "")
        set_run(p.add_run(seg), size=size, bold=bold, color=color)
    if keep:
        keep_together(p)
    return p


def parse_markdown(md_text):
    """返回结构：{'title':..., 'intro':[...], 'sections':[{'heading':...,'blocks':[...]}]}"""
    lines = md_text.splitlines()
    title = ""
    intro = []
    sections = []
    cur = None
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            cur = {"heading": line[3:].strip(), "blocks": []}
            sections.append(cur)
            continue
        if line.startswith("### "):
            if cur is None:
                cur = {"heading": "", "blocks": []}
                sections.append(cur)
            cur["blocks"].append(("h3", line[4:].strip()))
            continue
        if line.startswith("> "):
            (cur["blocks"] if cur else intro).append(("quote", line[2:].strip()))
            continue
        if line.startswith("|"):
            (cur["blocks"] if cur else intro).append(("table_row", line))
            continue
        if re.match(r"^\d+\.\s", line):
            (cur["blocks"] if cur else intro).append(("ol", line))
            continue
        if line.startswith("- "):
            (cur["blocks"] if cur else intro).append(("ul", line[2:].strip()))
            continue
        if not line.strip():
            continue
        (cur["blocks"] if cur else intro).append(("p", line.strip()))
    return {"title": title, "intro": intro, "sections": sections}


def render_table(doc, rows, usable_cm=17.8):
    """rows: markdown 表行（含分隔行）。

    表格宽度必须自己算：LibreOffice/Word 默认 autofit 会按内容撑宽，
    实测列宽合计 19.8cm 时右侧两列直接被切到页面外（正文宽只有 17.8cm）。
    这里关闭 autofit、固定布局，并把列宽按可用宽度等比缩放。
    """
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in r)]
    if not cells:
        return
    ncol = max(len(r) for r in cells)

    # 6 列（时间分配表）的权重；其它列数退回等宽
    weights = {6: [1.3, 5.0, 1.9, 1.5, 1.5, 6.6]}.get(ncol, [1.0] * ncol)
    scale = usable_cm / sum(weights)
    widths = [w * scale for w in weights]

    t = doc.add_table(rows=len(cells), cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    # 固定布局：告诉 Word/LO 不要按内容重新分配列宽
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    for ri, row in enumerate(cells):
        no_row_split(t.rows[ri])
        for ci in range(ncol):
            txt = row[ci] if ci < len(row) else ""
            cell = t.cell(ri, ci)
            cell.width = Cm(widths[ci])          # 单元格级也要设，缺一不可
            if ri == 0:
                shade(cell, NAVY_HEX)
                cell_text(cell, txt, size=9.5, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF),
                          align=WD_ALIGN_PARAGRAPH.CENTER)
            else:
                if ri % 2 == 0:
                    shade(cell, ROW_ALT_HEX)
                cell_text(cell, txt, size=9.5,
                          color=INK if ci in (0, 1) else SLATE,
                          align=WD_ALIGN_PARAGRAPH.CENTER if ci in (0, 3, 4) else WD_ALIGN_PARAGRAPH.LEFT)
    for ci, wcm in enumerate(widths):
        t.columns[ci].width = Cm(wcm)            # 列级
    repeat_header(t.rows[0])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ---------------------------------------------------------------- 主流程


def build(md_path: Path, out_path: Path):
    data = parse_markdown(md_path.read_text(encoding="utf-8"))
    doc = Document()

    # 页面设置：A4 + 较窄页边距（内容多，便于打印）
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(1.9)
    sec.left_margin = sec.right_margin = Cm(1.6)
    add_page_number_footer(sec)

    # 正文默认字体
    style = doc.styles["Normal"]
    style.font.name = FONT_EN
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_CN)

    # 标题
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    set_run(p.add_run(data["title"] or "桥体卫士 · 12 分钟答辩讲稿"), size=19, bold=True, color=NAVY)
    sub = doc.add_paragraph()
    sub.paragraph_format.space_after = Pt(10)
    set_run(sub.add_run("配套文件：桥体卫士答辩PPT_12分钟版.pptx（15 页）"), size=9, color=SLATE_LIGHT)

    # 开头要点
    for kind, text in data["intro"]:
        if kind == "ul":
            add_md_paragraph(doc, "· " + text, size=10, color=SLATE, indent_left=0.4, space_after=3)
        elif kind == "p":
            add_md_paragraph(doc, text, size=10, color=SLATE)

    for section in data["sections"]:
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(6)
        set_run(h.add_run(section["heading"]), size=14, bold=True, color=NAVY)
        keep_together(h)

        table_rows, blocks = [], section["blocks"]
        i = 0
        while i < len(blocks):
            kind, val = blocks[i]
            if kind == "table_row":
                table_rows.append(val)
                i += 1
                continue
            if table_rows:
                render_table(doc, table_rows)
                table_rows = []
            if kind == "h3":
                # 「01 · 标题　`30s｜94 字`」→ 页标题：时长用青色强调
                m = re.match(r"^(\d+)\s*·\s*(.*?)[　\s]*`([^`]+)`\s*$", val)
                hp = doc.add_paragraph()
                hp.paragraph_format.space_before = Pt(11)
                hp.paragraph_format.space_after = Pt(4)
                if m:
                    num, name, meta = m.groups()
                    set_run(hp.add_run(f"第 {num} 页　"), size=12, bold=True, color=NAVY)
                    set_run(hp.add_run(name), size=12, bold=True, color=INK)
                    set_run(hp.add_run(f"　（{meta}）"), size=10, bold=True, color=TEAL)
                else:
                    set_run(hp.add_run(val), size=12, bold=True, color=INK)
                keep_together(hp)
            elif kind == "p":
                # 讲稿正文里引用内部规格文件（_spec/…）只对维护者有意义，
                # 交付文档里去掉这个前缀，读者不需要知道内部文件结构。
                # 注意：不能用非贪婪 \S+?[.。]，它会在 "SPEC_s06_video.md" 的
                # 第一个点就停下，留下 "md。" 残句（实测踩过）。这里吃掉整条路径。
                val = re.sub(r"^见\s*_spec/\S*", "", val).strip()
                add_md_paragraph(doc, val, size=12, color=INK, space_after=8,
                                 line_spacing=1.5, indent_left=0.3)
            elif kind == "quote":
                add_md_paragraph(doc, "※ " + val, size=9.5, color=SLATE, space_after=4,
                                 indent_left=0.3)
            elif kind == "ul":
                add_md_paragraph(doc, "· " + val, size=10.5, color=INK, indent_left=0.6, space_after=4)
            elif kind == "ol":
                add_md_paragraph(doc, val, size=10.5, color=INK, indent_left=0.6, space_after=4)
            i += 1
        if table_rows:
            render_table(doc, table_rows)

    doc.save(str(out_path))
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=str(HERE / "讲稿_12分钟.md"))
    ap.add_argument("--out", default=str(HERE / "讲稿_12分钟.docx"))
    args = ap.parse_args()
    md = Path(args.md)
    if not md.exists():
        print(f"缺少讲稿源文件: {md}")
        return 2
    out = build(md, Path(args.out))
    print(f"已生成: {out}")
    print(f"大小: {out.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
