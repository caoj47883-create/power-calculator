# -*- coding: utf-8 -*-
"""Build the PRD DOCX for Power Ledger v2.1.2."""

from pathlib import Path
import re
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
SHOTS = ROOT / "screenshots"
OUT = ROOT / "docs" / "功耗计算器-产品需求文档-PRD-v2.1.2.docx"

# ---- palette ---------------------------------------------------------------
PAPER = "F7F4EE"
PAPER_2 = "FBF9F5"
INK = "201C17"
BODY = "3B352D"
MUTED = "766D61"
BLUE = "159BB9"
BLUE_DARK = "0B7894"
BLUE_SOFT = "EAF6F9"
LINE = "DED7CC"
WARM = "F3EBDD"
WHITE = "FFFDF8"

CN_FONT = "Microsoft YaHei"
CODE_FONT = "Consolas"


def rgb(hex_value):
    return RGBColor.from_string(hex_value)


doc = Document()

# Page setup ---------------------------------------------------------------
section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.left_margin = Cm(2.0)
section.right_margin = Cm(2.0)
section.top_margin = Cm(2.0)
section.bottom_margin = Cm(1.8)
section.header_distance = Cm(0.8)
section.footer_distance = Cm(0.7)
section.different_first_page_header_footer = True
CONTENT_IN = 6.62

# Document properties ------------------------------------------------------
props = doc.core_properties
props.title = "功耗计算器 Power Ledger 产品需求文档（PRD）"
props.subject = "Android / iOS / PWA 离线每日功耗账本"
props.author = "产品组"
props.last_modified_by = "产品组"
props.keywords = "功耗计算器, PRD, 离线, 能量账本, Android, iOS, PWA"
props.comments = "对应已交付版本 v2.1.2（Android versionCode 13 / iOS Build 13 / PWA cache 2.1.2）"


def set_font(run, name=CN_FONT, size=None, bold=None, color=None, italic=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), name if name != CODE_FONT else CN_FONT)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = rgb(color)


def style_font(style, size, bold=None, color=None, name=CN_FONT):
    style.font.name = name
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if color is not None:
        style.font.color.rgb = rgb(color)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    rfonts.set(qn("w:eastAsia"), CN_FONT)


def set_paragraph_spacing(style, before=0, after=4, line=1.5):
    pf = style.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line


def add_para_markup(paragraph, text, size=None, color=None, bold_all=False):
    """Supports **bold** fragments."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if not part:
            continue
        bold = False
        value = part
        if part.startswith("**") and part.endswith("**") and len(part) >= 4:
            value = part[2:-2]
            bold = True
        run = paragraph.add_run(value)
        set_font(run, size=size, bold=(bold or bold_all), color=color)


def style_text(style, size=10.5, color=BODY, bold=None, before=0, after=4, line=1.5):
    style_font(style, size, bold=bold, color=color)
    set_paragraph_spacing(style, before, after, line)


# Styles -------------------------------------------------------------------
styles = doc.styles

normal = styles["Normal"]
style_text(normal, 10.5, BODY, None, 0, 4, 1.5)
normal.paragraph_format.widow_control = True

h1 = styles["Heading 1"]
style_font(h1, 16, True, INK)
set_paragraph_spacing(h1, 10, 10, 1.2)
h1.paragraph_format.keep_with_next = True
h1.paragraph_format.page_break_before = False

h2 = styles["Heading 2"]
style_font(h2, 12.5, True, BLUE_DARK)
set_paragraph_spacing(h2, 12, 4, 1.2)
h2.paragraph_format.keep_with_next = True

h3 = styles["Heading 3"]
style_font(h3, 10.8, True, INK)
set_paragraph_spacing(h3, 8, 3, 1.2)
h3.paragraph_format.keep_with_next = True

for name, size, color in [("PRD Body", 10.5, BODY), ("PRD Small", 9, MUTED)]:
    st = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = normal
    style_text(st, size, color, None, 0, 4, 1.5)

bullet = styles["List Bullet"]
style_text(bullet, 10.5, BODY, None, 0, 2, 1.4)
bullet.paragraph_format.left_indent = Cm(0.62)
bullet.paragraph_format.first_line_indent = Cm(-0.28)

caption = styles.add_style("PRD Caption", WD_STYLE_TYPE.PARAGRAPH)
caption.base_style = normal
style_font(caption, 8.8, False, MUTED)
caption.font.italic = True
set_paragraph_spacing(caption, 2, 8, 1.3)
caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

req_title = styles.add_style("PRD ReqTitle", WD_STYLE_TYPE.PARAGRAPH)
req_title.base_style = normal
style_font(req_title, 10.9, True, BLUE_DARK)
set_paragraph_spacing(req_title, 10, 3, 1.2)
req_title.paragraph_format.keep_with_next = True

accept = styles.add_style("PRD Acceptance", WD_STYLE_TYPE.PARAGRAPH)
accept.base_style = normal
style_font(accept, 9.4, False, BLUE_DARK)
set_paragraph_spacing(accept, 1, 8, 1.4)
accept.paragraph_format.left_indent = Cm(0.18)

code = styles.add_style("PRD Code", WD_STYLE_TYPE.PARAGRAPH)
code.base_style = normal
style_font(code, 8.8, False, BODY, name=CODE_FONT)
set_paragraph_spacing(code, 2, 2, 1.3)
code.paragraph_format.left_indent = Cm(0.3)

small = styles["PRD Small"]


def h1_add(text, new_page=True):
    p = doc.add_paragraph(style="Heading 1")
    if new_page:
        p.paragraph_format.page_break_before = True
    add_para_markup(p, text, size=16, color=INK, bold_all=True)
    # blue rule under H1
    ppr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "5")
    bottom.set(qn("w:color"), BLUE)
    pbdr.append(bottom)
    ppr.append(pbdr)
    return p


def h2_add(text):
    p = doc.add_paragraph(style="Heading 2")
    add_para_markup(p, text, size=12.5, color=BLUE_DARK, bold_all=True)
    return p


def h3_add(text):
    p = doc.add_paragraph(style="Heading 3")
    add_para_markup(p, text, size=10.8, color=INK, bold_all=True)
    return p


def p_add(text, style="PRD Body", size=None, color=None):
    p = doc.add_paragraph(style=style)
    add_para_markup(p, text, size=size, color=color)
    return p


def bullet_add(text):
    p = doc.add_paragraph(style="List Bullet")
    add_para_markup(p, text)
    return p


def small_add(text, color=MUTED):
    p = doc.add_paragraph(style="PRD Small")
    add_para_markup(p, text, color=color)
    return p


def req_add(req_id, title, priority, rules, acceptance):
    p = doc.add_paragraph(style="PRD ReqTitle")
    run = p.add_run(f"{req_id}  {title}")
    set_font(run, size=10.9, bold=True, color=BLUE_DARK)
    run2 = p.add_run(f"   {priority}")
    set_font(run2, size=8.8, bold=True, color=MUTED)
    for rule in rules:
        bullet_add(rule)
    a = doc.add_paragraph(style="PRD Acceptance")
    label = a.add_run("验收标准：")
    set_font(label, size=9.4, bold=True, color=BLUE_DARK)
    add_para_markup(a, acceptance, size=9.4, color=BLUE_DARK)


def caption_add(text):
    p = doc.add_paragraph(style="PRD Caption")
    add_para_markup(p, text, size=8.8, color=MUTED)
    return p


def shade_cell(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = tcpr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcpr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)


def cell_margins(cell, top=55, start=80, bottom=55, end=80):
    tcpr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = OxmlElement(f"w:{tag}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tcpr.append(mar)


def set_table_borders(table, color=LINE, size=4):
    tblpr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblpr.append(borders)


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def cant_split(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def set_cell_text(cell, text, bold=False, color=BODY, size=8.7, align=None):
    cell.text = ""
    parts = str(text).split("\n")
    for index, part in enumerate(parts):
        p = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.22
        if align is not None:
            p.alignment = align
        add_para_markup(p, part, size=size, color=color, bold_all=bold)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def add_table(headers, rows, widths, font_size=8.7, first_col_bold=False, center_cols=(), zebra=True):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    hdr = table.rows[0]
    repeat_header(hdr)
    cant_split(hdr)
    for i, head in enumerate(headers):
        cell = hdr.cells[i]
        shade_cell(cell, BLUE_DARK)
        cell_margins(cell)
        set_cell_text(cell, head, bold=True, color=WHITE, size=font_size)
    for r_idx, row in enumerate(rows):
        tr = table.add_row()
        cant_split(tr)
        for c_idx, value in enumerate(row):
            cell = tr.cells[c_idx]
            cell_margins(cell)
            if zebra and r_idx % 2 == 1:
                shade_cell(cell, PAPER_2)
            align = WD_ALIGN_PARAGRAPH.CENTER if c_idx in center_cols else None
            set_cell_text(
                cell,
                value,
                bold=(first_col_bold and c_idx == 0),
                color=INK if (first_col_bold and c_idx == 0) else BODY,
                size=font_size,
                align=align,
            )
    for row in table.rows:
        for i, width in enumerate(widths):
            row.cells[i].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_info_table(rows, widths=(1.55, 5.02), label_fill=WARM):
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    for label, value in rows:
        tr = table.add_row()
        cant_split(tr)
        c0, c1 = tr.cells
        cell_margins(c0)
        cell_margins(c1)
        shade_cell(c0, label_fill)
        set_cell_text(c0, label, bold=True, color=INK, size=9.2)
        set_cell_text(c1, value, color=BODY, size=9.2)
    for row in table.rows:
        row.cells[0].width = Inches(widths[0])
        row.cells[1].width = Inches(widths[1])
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def callout(title, body, fill=WARM, accent=BLUE):
    p = doc.add_paragraph(style="PRD Body")
    p.paragraph_format.left_indent = Cm(0.2)
    p.paragraph_format.right_indent = Cm(0.1)
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(8)
    ppr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    ppr.append(shd)
    pbdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:space"), "10")
    left.set(qn("w:color"), accent)
    pbdr.append(left)
    ppr.append(pbdr)
    r = p.add_run(title + "  ")
    set_font(r, size=10.2, bold=True, color=accent)
    add_para_markup(p, body, size=10.1, color=BODY)
    return p


def code_block(lines):
    for index, line in enumerate(lines):
        p = doc.add_paragraph(style="PRD Code")
        if index == 0:
            p.paragraph_format.space_before = Pt(4)
        if index == len(lines) - 1:
            p.paragraph_format.space_after = Pt(8)
        ppr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), PAPER_2)
        ppr.append(shd)
        run = p.add_run(line)
        set_font(run, name=CODE_FONT, size=8.6, color=BODY)


def picture(path, width_in, caption):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(path), width=Inches(width_in))
    caption_add(caption)


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(txt)
    run._r.append(fld_end)
    set_font(run, size=8.5, color=MUTED)


# Header and footer --------------------------------------------------------
header = section.header
hp = header.paragraphs[0]
hp.paragraph_format.space_after = Pt(0)
r = hp.add_run("功耗计算器 · 产品需求文档")
set_font(r, size=8.4, color=MUTED)
r2 = hp.add_run("\t\tv2.1.2  /  文档 v1.0")
set_font(r2, size=8.4, color=MUTED)
hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
# right-aligned tab stops
pf = hp.paragraph_format
pf.tab_stops.add_tab_stop(Cm(16.9), alignment=2)

# remove first-page header/footer content
section.first_page_header.paragraphs[0].text = ""
section.first_page_footer.paragraphs[0].text = ""

footer = section.footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run("—  ")
set_font(r, size=8.5, color=MUTED)
add_page_number(fp)
r = fp.add_run("  —")
set_font(r, size=8.5, color=MUTED)

# request Word to update PAGE / NUMPAGES fields on open
settings = doc.settings.element
update = OxmlElement("w:updateFields")
update.set(qn("w:val"), "true")
settings.append(update)

# ==========================================================================
# COVER
# ==========================================================================
for _ in range(2):
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(0)

icon = doc.add_paragraph()
icon.alignment = WD_ALIGN_PARAGRAPH.CENTER
icon.paragraph_format.space_after = Pt(12)
icon.add_run().add_picture(str(ROOT / "ios" / "PowerLedger" / "Assets.xcassets" / "AppIcon.appiconset" / "Icon-1024.png"), width=Inches(0.82))

eyebrow = doc.add_paragraph()
eyebrow.alignment = WD_ALIGN_PARAGRAPH.CENTER
eyebrow.paragraph_format.space_after = Pt(7)
r = eyebrow.add_run("P R O D U C T   R E Q U I R E M E N T S   D O C U M E N T")
set_font(r, size=8.4, bold=True, color=BLUE_DARK)

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(0)
r = title.add_run("功耗计算器")
set_font(r, size=34, bold=True, color=INK)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.paragraph_format.space_after = Pt(3)
r = sub.add_run("Power Ledger")
set_font(r, size=16, bold=True, color=BLUE_DARK)

tag = doc.add_paragraph()
tag.alignment = WD_ALIGN_PARAGRAPH.CENTER
tag.paragraph_format.space_before = Pt(4)
tag.paragraph_format.space_after = Pt(18)
r = tag.add_run("把身体代谢、设备、家电、网络固定项与出行，放进同一本每天自动归零的能量账本。")
set_font(r, size=10.8, color=MUTED)

rule = doc.add_paragraph()
rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
rule.paragraph_format.space_after = Pt(16)
r = rule.add_run(" ")
set_font(r, size=2)
ppr = rule._p.get_or_add_pPr()
pbdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single")
bottom.set(qn("w:sz"), "18")
bottom.set(qn("w:space"), "2")
bottom.set(qn("w:color"), BLUE)
pbdr.append(bottom)
ppr.append(pbdr)

meta = add_info_table([
    ("文档版本", "v1.0（定稿）"),
    ("产品版本", "v2.1.2  ·  Android versionCode 13  ·  iOS Build 13  ·  PWA cache 2.1.2"),
    ("适用平台", "Android  ·  iOS  ·  PWA / 移动网页"),
    ("文档状态", "已定稿，作为当前交付与后续迭代基线"),
    ("更新日期", "2026-11-07"),
], widths=(1.25, 4.45))
# use only 5 rows; center table
meta.alignment = WD_TABLE_ALIGNMENT.CENTER

closing = doc.add_paragraph()
closing.alignment = WD_ALIGN_PARAGRAPH.CENTER
closing.paragraph_format.space_before = Pt(18)
r = closing.add_run("离线  ·  本地存储  ·  无权限  ·  无网络")
set_font(r, size=9.2, bold=True, color=BLUE_DARK)



# ==========================================================================
# DOCUMENT CONTROL / TOC
# ==========================================================================
h1_add("文档信息与阅读指南", new_page=True)

p_add("本文档描述「功耗计算器 Power Ledger」在 v2.1.2 版本的产品目标、范围、功能需求、业务规则、验收标准与发布约束。文档以已交付版本为需求基线，既用于当前验收，也作为后续迭代的变更基准。")

add_info_table([
    ("文档名称", "功耗计算器 Power Ledger 产品需求文档（PRD）"),
    ("文档编号", "PRD-PL-2.1.2-001"),
    ("文档版本", "v1.0"),
    ("产品版本", "v2.1.2 / Android versionCode 13 / iOS Build 13 / PWA cache 2.1.2"),
    ("编制", "产品组"),
    ("评审角色", "产品、设计、研发、测试"),
    ("更新日期", "2026-11-07"),
    ("状态", "定稿（待签署，对应已交付版本）"),
    ("关联产物", "Android APK、iOS Xcode 工程、PWA 包、单文件网页版、模型与 UI 验收记录"),
])

h2_add("修订记录")
add_table(
    ["版本", "日期", "修订内容", "修订人"],
    [
        ["0.1", "2026-11-06", "初稿：梳理 v2.1.2 产品范围与功能结构", "产品组"],
        ["1.0", "2026-11-07", "补全需求、规则、验收、风险与发布说明，形成定稿", "产品组"],
    ],
    widths=(0.55, 0.9, 4.45, 0.68),
    font_size=8.6,
)

h2_add("评审与批准")
add_table(
    ["角色", "姓名 / 部门", "评审意见", "日期"],
    [
        ["产品负责人", "", "", ""],
        ["设计负责人", "", "", ""],
        ["研发负责人", "", "", ""],
        ["测试负责人", "", "", ""],
    ],
    widths=(1.1, 1.6, 2.6, 1.28),
    font_size=8.8,
)

h2_add("阅读对象与使用方式")
bullet_add("**产品 / 设计**：确认范围、流程、交互与验收标准；变更时同步更新本文档。")
bullet_add("**研发**：以第 5、6、7 章作为实现基线；以第 10 章作为自测与联调清单。")
bullet_add("**测试**：以需求编号、业务规则和验收矩阵组织测试；平台交付约束见第 3、11 章。")
bullet_add("**运营 / 支持**：以第 2、3、11、12 章理解定位、平台限制和用户沟通口径。")
p_add("本文档不替代技术设计文档。实现层面的签名方式、构建脚本、iOS 安装路径等属于交付约束，在相关章节说明，不作为产品功能本身。")

h2_add("优先级定义")
add_table(
    ["优先级", "定义", "处理原则"],
    [
        ["P0", "核心闭环或不可妥协的合规 / 数据要求", "必须随版本交付；缺失时不可发布"],
        ["P1", "显著影响体验、效率或可维护性", "应在当前版本交付；可在特殊情况下拆分为后续版本"],
        ["P2", "增强型能力或长期演进方向", "记录在路线图中，不阻塞当前版本"],
    ],
    widths=(0.75, 3.3, 2.5),
    font_size=8.8,
)

h2_add("目录")
add_table(
    ["章节", "内容", "章节", "内容"],
    [
        ["1", "产品概述", "8", "交互与视觉规范"],
        ["2", "用户与场景", "9", "非功能需求"],
        ["3", "范围与平台", "10", "验收与测试"],
        ["4", "信息架构与核心流程", "11", "版本与发布"],
        ["5", "功能需求", "12", "风险与开放问题"],
        ["6", "业务规则与算法", "13", "附录"],
        ["7", "数据与隐私", "", ""],
    ],
    widths=(0.5, 2.45, 0.5, 2.45),
    font_size=8.6,
    center_cols=(0, 2),
)
small_add("提示：各章标题即 Word 大纲标题，可使用「视图 → 导航窗格」快速跳转；本文档不插入自动目录域，避免打开时出现未更新占位。")



# ==========================================================================
# 1 PRODUCT OVERVIEW
# ==========================================================================
h1_add("1. 产品概述", new_page=True)

callout("一句话定义", "功耗计算器是一本**每天自动归零、只保存在本机**的能量账本：把身体代谢、设备用电、家用电器、网络固定项和出行换算成同一单位，帮助普通用户看见并调整自己的日常能耗。")

h2_add("1.1 背景")
p_add("现代人的日常能耗分散在多个看不见的环节：身体的基础代谢、手机与电脑的充电、冰箱和空调的持续运行、WiFi / 基站 / 云服务的固定分摊，以及地铁、打车、城际出行。单独看电费账单或步数，很难把这些环节放进同一个视角，更难判断“今天到底用了多少、主要花在哪里”。")
p_add("现有工具通常只覆盖单一类别，或要求联网、注册、接入智能电表；对于只想每天花几十秒记一笔、且不愿上传个人数据的用户，这些方案都过重。产品以**轻量估算 + 完全离线 + 本机历史**为切口，让用户在不被打扰的前提下建立日常能耗感知。")

h2_add("1.2 产品定位")
add_table(
    ["维度", "定位"],
    [
        ["产品类型", "离线每日能量账本 / 生活方式工具"],
        ["核心价值", "把多来源能耗放进同一页，快速看见今天的用量和结构"],
        ["差异点", "无需账号、无网络权限；每天自动归零；单卡三态固定；可锁定容量与功率"],
        ["表达方式", "暖白纸感、白卡片、大字号、天青蓝操作色；背景随能耗轻微变化，但永远保持明亮"],
        ["非定位", "不是智能电表、不是碳足迹认证、不是账单核对工具、不是专业能源审计软件"],
    ],
    widths=(1.2, 5.3),
    font_size=8.8,
)

h2_add("1.3 产品目标")
add_table(
    ["目标", "说明", "对应需求"],
    [
        ["G1 看见", "用一页总览呈现三类占比、总能耗、等价换算和当日评价", "FR-12 / FR-13"],
        ["G2 低摩擦", "首次只录一次资料；每天只调当日用量；核心项在首屏，其余按需展开", "FR-01 / FR-06 / FR-11"],
        ["G3 可控制", "单卡固定防误触；配置锁保护容量 / 功率；换日只清用量", "FR-07 / FR-15 / FR-16"],
        ["G4 可持续", "本地历史保留 730 天，按自然日连续记录，帮助比较趋势", "FR-14"],
        ["G5 私密与离线", "无账号、无网络、无权限；数据只在本机；PWA 仅托管静态文件", "FR-18"],
    ],
    widths=(0.95, 4.1, 1.45),
    font_size=8.8,
)

h2_add("1.4 成功标准")
p_add("产品不做埋点、不联网，因此不采用在线 DAU 类指标作为验收依据。以下为产品验收指标与观察指标：")
add_table(
    ["指标", "目标 / 判定", "验证方式"],
    [
        ["首次配置", "首次打开能独立完成年龄 / 身高 / 体重录入；保存后再次打开不再询问", "全新安装 + 刷新回归"],
        ["日常核心流程", "从打开到看懂今日总量 ≤ 30 秒（配置完成后）", "可用性走查（5 人目标）"],
        ["防误触", "固定或配置锁开启后，滚动页面不会改变受保护数值", "触屏 / 视口交互测试"],
        ["数据连续性", "跨天后可调用量归零，容量 / 功率不变；历史保留前一日", "日期注入回归 + 历史断言"],
        ["隐私", "无网络请求、无 uses-permission、无账号、无埋点", "APK / 工程 / 页面静态检查"],
        ["跨端一致性", "Android、iOS、PWA 使用同一套页面与规则（平台壳除外）", "资源哈希 + 规则测试"],
    ],
    widths=(1.1, 3.7, 1.7),
    font_size=8.6,
)

h2_add("1.5 非目标")
for item in [
    "不做实时电表读数、智能家居对接或自动识别设备。",
    "不做碳足迹认证、碳交易或正式碳排放报告。",
    "不提供账号、云同步、多人共享、社交排名或推送。",
    "不追求精确到真实账单；所有数值均为可解释的估算。",
    "当前版本不通过 App Store 分发；iOS 以 Xcode 工程和签名构建为前提。",
]:
    bullet_add(item)

h2_add("1.6 产品原则")
add_table(
    ["原则", "落地要求"],
    [
        ["真实感", "公式可解释，口径写清楚；不把估算包装成精确计量。"],
        ["低摩擦", "一次资料、默认核心项、常用步数 / 强度预设、记住选择。"],
        ["可控性", "单卡三态固定、配置锁、重置示例值；不强迫用户一次填完所有设备。"],
        ["明亮轻盈", "暖白纸面、白卡片、黑字、天青蓝操作色；任何能耗状态都不使用黑色背景。"],
        ["私密优先", "数据本地保存；没有网络权限；PWA 只托管静态文件。"],
    ],
    widths=(1.05, 5.45),
    font_size=8.8,
)

# ==========================================================================
# 2 USERS AND SCENARIOS
# ==========================================================================
h1_add("2. 用户与场景", new_page=False)

h2_add("2.1 目标用户")
for item in [
    "20–45 岁的智能手机用户，对电费、环保或能量话题有兴趣，但不是能源行业从业者。",
    "希望每天花几十秒记录大致用量，而不是接入硬件或填写复杂问卷。",
    "对隐私敏感，不愿注册账号、上传家庭数据或使用需要联网的工具。",
    "同时拥有手机、耳机、电脑等数码设备，并关心通勤 / 出行能耗。",
    "使用 Android 手机、iPhone / iPad，或愿意以 PWA 方式在 Safari 中使用。",
]:
    bullet_add(item)

h2_add("2.2 Persona")
add_table(
    ["Persona", "特征", "核心诉求", "关键功能"],
    [
        ["独居上班族", "租住公寓；手机、耳机、笔记本、地铁；对电费有感知但没时间细算", "快速知道今天大概用了多少、哪些设备在贡献", "首次资料、设备列表、步数、总览"],
        ["家庭能源管家", "关注冰箱、空调、热水器、洗衣机的使用；周末会出行", "按天比较家电与出行，避免能源账单失控", "电器、固定项、历史、评价"],
        ["数码 / 出行爱好者", "多设备、打车 / 城际出行；喜欢数字和等价换算", "查看设备与出行的相对贡献，获得直观反馈", "设备容量 / 功率、出行、等价换算"],
        ["隐私敏感用户", "不愿注册、不愿联网；使用 iPhone / iPad 或 Android", "只在设备本地保存，无网络权限", "离线、PWA、本机存储、iOS 工程"],
    ],
    widths=(1.05, 2.0, 2.0, 1.55),
    font_size=8.4,
)

h2_add("2.3 用户任务（JTBD）")
add_table(
    ["当……", "我想……", "这样我就可以……", "对应需求"],
    [
        ["第一次打开应用时", "一次性录入年龄、身高、体重", "不用每天重复填写，基础代谢按实际年龄计算", "FR-01 / FR-03"],
        ["每天使用手机、电脑、耳机时", "快速调整充电次数和主机时长", "看见设备部分的能量开销", "FR-06 / FR-08"],
        ["开空调、洗衣服、坐地铁时", "记录电器时长和出行里程", "知道周边能耗主要花在哪", "FR-09 / FR-11"],
        ["想看今天整体表现时", "一页看到总量、占比、等价换算和评价", "判断是否偏省电或偏高耗能", "FR-12 / FR-13"],
        ["滑动页面怕误触时", "把当天调好的卡片固定，或锁定容量 / 功率", "放心滚动浏览，不改变数据", "FR-07 / FR-16"],
        ["第二天再次打开时", "让昨日归档、今日用量归零，但资料和配置不变", "开始新一天的记录", "FR-15"],
        ["想回看最近几天的趋势时", "看到最近 7 天的柱状图", "比较每天的变化", "FR-14"],
    ],
    widths=(1.55, 1.75, 2.2, 1.1),
    font_size=8.3,
)

h2_add("2.4 关键场景")
add_table(
    ["场景", "触发", "用户行为", "产品响应"],
    [
        ["首次配置", "全新安装 / 清除数据", "填写年龄、身高、体重", "一次性资料 sheet；保存后进入主界面"],
        ["日常记录", "早上或晚上打开", "在四个分页调整滑条、勾选、输入", "实时更新分页顶部和总览"],
        ["当日复盘", "饭后 / 睡前", "进入总览看评价、占比、等价换算", "按周边功耗给出五档评价与 7 天历史"],
        ["防误触", "调整完成后继续滑动", "点卡片右上角锁定，或打开配置锁", "卡片 / 容量功率冻结；其他内容仍可滚动"],
        ["跨日", "第二天首次打开 / 跨午夜", "继续使用", "自动归档昨日、清零今日可调用量，并提示"],
        ["跨端使用", "换设备 / 换平台", "Android 用 APK；iOS 用原生包；Safari 添加到主屏幕", "同一套规则；数据各自保存在本机"],
    ],
    widths=(1.05, 1.55, 2.1, 1.9),
    font_size=8.3,
)

h2_add("2.5 痛点与对应设计")
add_table(
    ["用户痛点", "设计回应", "验收关注点"],
    [
        ["每天填身高体重太麻烦", "首次录入一次，设置里修改；自体页只展示资料卡", "保存后不再询问；改资料后立即重算"],
        ["滑条在滚动时容易误触", "单卡三态固定；配置锁；固定后禁用卡片内控件", "固定后卡片内滑条 / 输入不可操作"],
        ["设备太多、页面太长", "核心设备 4 项 + 展开更多设备 6 项；出行 2 + 9 项", "首屏信息量可控；展开后完整可编辑"],
        ["第二天数据没有重置", "按自然日归档 + 归零可调用量；保留配置与选择", "跨日步骤、次数、时长、出行归零"],
        ["担心容量 / 功率被误改", "设置里新增容量 / 功率锁定", "锁定后只冻结配置，不影响每日用量"],
        ["不想上传数据", "无网络、无账号、无权限；PWA 仅静态托管", "零网络请求、零权限、本机存储"],
    ],
    widths=(1.45, 3.0, 2.05),
    font_size=8.4,
)

# ==========================================================================
# 3 SCOPE AND PLATFORMS
# ==========================================================================
h1_add("3. 范围与平台", new_page=False)

h2_add("3.1 本期范围")
add_table(
    ["模块", "交付内容", "优先级"],
    [
        ["首次与设置", "年龄 / 身高 / 体重一次性录入；资料修改；配置锁", "P0"],
        ["自体", "实际年龄 BMR、BMI、静息 / 活动功率、步数 50 步精度与预设、MET 与预设", "P0"],
        ["设备", "10 类设备；核心 / 可选分组；单卡三态；电池容量 / 功率 / 充电次数 / 时长", "P0"],
        ["周边", "WiFi / 基站 / 云固定项；5 类电器；11 种出行（含城际）", "P0"],
        ["总览", "三类汇总、总功耗、平均功率、标准煤 / 特斯拉换算、周边五档评价、7 天历史", "P0"],
        ["时间与数据", "自然日归档、730 天历史、跨日归零、旧版本迁移", "P0"],
        ["平台交付", "Android APK；iOS Xcode 工程；PWA 站点；单文件网页版", "P0"],
        ["体验", "暖白主题、响应式、底部导航、底部 sheet、空状态、可访问性标签", "P1"],
    ],
    widths=(1.35, 4.55, 0.7),
    font_size=8.5,
)

h2_add("3.2 明确不在本期范围")
for item in [
    "账号体系、云同步、多设备同步、家庭共享。",
    "智能硬件接入、实时电表读数、OCR 识别电费账单。",
    "正式碳足迹报告、碳交易、环保认证。",
    "社交、排行榜、推送、广告、付费订阅。",
    "App Store 上架与自动更新；当前版本只交付签名 / 源码形态。",
]:
    bullet_add(item)

h2_add("3.3 平台交付形态")
add_table(
    ["平台", "形态", "当前版本", "关键限制"],
    [
        ["Android", "原生 WebView 壳 + 离线 APK", "v2.1.2 / versionCode 13", "仅本地签名；无 Google Play 上架"],
        ["iOS", "SwiftUI + WKWebView 的 Xcode 工程", "v2.1.2 / Build 13", "Windows 环境不能编译 / 签名 IPA；需 Mac、云端 macOS 或 Windows + Sideloadly"],
        ["PWA", "静态站点 + manifest + service worker", "cache 2.1.2", "需 HTTPS 托管；首次联网加载后离线；非 App Store 应用"],
        ["Web 单文件", "单 HTML 内联 CSS / JS", "v2.1.2", "没有 service worker；适合快速预览或简单托管"],
    ],
    widths=(0.75, 2.15, 1.35, 2.3),
    font_size=8.3,
)

h2_add("3.4 运行环境与假设")
add_table(
    ["项目", "假设 / 要求"],
    [
        ["设备", "以手机竖屏为主；iPad / 平板使用同一响应式布局"],
        ["系统", "Android 6.0（API 23）+；iOS 15.0+；现代 Safari / Chromium"],
        ["时区", "按设备本地时区确定自然日；历史日期键格式 YYYY-MM-DD"],
        ["用户", "一台设备一个用户；不区分家庭多成员"],
        ["网络", "Android / iOS 完全离线；PWA 首次加载需要 HTTPS 网络，之后缓存"],
        ["数据", "仅本机；无账号、无云端、无备份/导出（当前版本）"],
    ],
    widths=(1.1, 5.4),
    font_size=8.7,
)

# ==========================================================================
# 4 IA AND FLOWS
# ==========================================================================
h1_add("4. 信息架构与核心流程", new_page=False)

h2_add("4.1 信息架构")
add_table(
    ["一级", "二级内容", "说明"],
    [
        ["自体", "身体资料摘要 / 静息与活动功率 / 每日步数 / 活动强度", "展示实际年龄 BMR、BMI 和步数活动；资料只读，修改走设置"],
        ["设备", "核心设备（手机、真无线耳机、平板、台式主机）+ 展开更多设备（6 项）", "每张卡右上角三态按钮；未勾选不计入"],
        ["周边", "固定项（WiFi / 基站 / 云）+ 电器（5 项）+ 今日出行（地铁、电动车 + 展开 9 项）", "固定项不可关闭；电器 / 出行可勾选和固定"],
        ["总览", "今日评价 / 三类明细 / 等价换算 / 最近 7 天", "总功耗、占比、评价、特斯拉续航与历史"],
        ["设置", "年龄、身高、体重 / 数据保护开关", "从顶部齿轮或身体资料「修改」进入"],
        ["说明", "公式、口径、离线与隐私说明", "顶部信息按钮打开"],
    ],
    widths=(0.85, 3.5, 2.25),
    font_size=8.4,
)

h2_add("4.2 核心流程")
h3_add("流程 A：首次使用")
p_add("打开应用 → 检测到无完整身体资料 → 弹出「先认识一下你」→ 输入年龄 / 身高 / 体重 → 保存并开始 → 进入自体页；之后启动不再询问。")
h3_add("流程 B：每日记录与查看")
p_add("切换底部分页 → 调整对应滑条 / 勾选 / 录入公里数 → 顶部 hero 与总览实时更新 → 在总览查看评价、占比、等价换算和 7 天历史。")
h3_add("流程 C：跨日归零")
p_add("首次打开 / 回到前台 / 页面跨过午夜 → 比较本地日期与状态日期 → 将昨日状态归档到昨日历史 → 清零今日可调用量 → 保留资料、配置、已选项目 → 提示「新的一天」。")
h3_add("流程 D：固定与配置保护")
p_add("点击卡片右上角：未勾选 → 勾选（计入、可调）；已勾选 → 固定（计入、卡片内控件冻结）；已固定 → 取消勾选。设置中另有容量 / 功率总开关，只冻结配置字段。")
h3_add("流程 E：修改资料")
p_add("顶部齿轮或自体页「修改」→ 设置 sheet → 修改年龄 / 身高 / 体重 / 配置锁 → 保存 → 立即重算 BMR、步长、BMI 与今日账本。")

h2_add("4.3 页面结构规则")
for item in [
    "全局顶部 hero 属于当前页：自体显示自体分项、设备显示设备分项、周边显示周边分项、总览显示总功耗。",
    "底部分页固定为自体 / 设备 / 周边 / 总览，四个分页不嵌套路由。",
    "顶部工具区包含日期、设置齿轮、说明按钮；总览没有全局锁按钮，固定能力下放到子卡片和设置。",
    "设置与说明均以底部 sheet 呈现；背景模糊，内容保持明亮；不出现全黑页面。",
    "首屏只展示核心项；「展开更多」只影响显示，不改变已勾选或已固定状态。",
]:
    bullet_add(item)

h2_add("4.4 关键状态矩阵")
add_table(
    ["状态", "触发", "界面表现", "允许的操作"],
    [
        ["首次资料", "无完整 profile", "资料 sheet 自动打开，关闭按钮隐藏", "录入并保存；不可通过背景返回"],
        ["正常", "已有资料", "四个分页、卡片可编辑", "调滑条 / 勾选 / 展开 / 切换设置"],
        ["卡片固定", "同一按钮第二次点击", "圆圈变蓝色锁，卡片内滑条 / 输入禁用", "再次点击取消计入；其他卡片可编辑"],
        ["配置锁定", "设置开关打开", "容量 / 功率滑条禁用；使用时长仍可编辑", "关闭开关恢复；换日保持"],
        ["跨日重置", "日期戳早于今天", "用量归零，资料 / 配置保留，出现提示", "继续记录新一天"],
        ["PWA 离线", "首次加载后断网", "service worker 返回缓存页面", "离线浏览与记录；数据在站点存储"],
        ["无历史 / 空状态", "新安装且未记录", "历史柱为空，文案提示从今天开始", "正常录入，记录自动生成"],
    ],
    widths=(1.15, 1.6, 2.25, 1.6),
    font_size=8.2,
)

# ==========================================================================
# 5 FUNCTIONAL REQUIREMENTS
# ==========================================================================
h1_add("5. 功能需求")

p_add("本章按模块列出需求编号、规则与验收标准。P0 为当前版本必须满足的闭环需求；P1 为体验与可访问性要求。所有需求的状态均为「已实现 v2.1.2」，验收以第 10 章为准。")

h2_add("5.1 需求索引")
add_table(
    ["编号", "模块", "需求", "优先级", "状态"],
    [
        ["FR-01", "首次资料", "一次性录入年龄 / 身高 / 体重", "P0", "已实现"],
        ["FR-02", "设置", "修改资料并立即重算", "P0", "已实现"],
        ["FR-03", "自体", "实际年龄 BMR 与身体摘要", "P0", "已实现"],
        ["FR-04", "自体", "每日步数 50 步精度与快捷预设", "P0", "已实现"],
        ["FR-05", "自体", "活动强度与快捷预设", "P0", "已实现"],
        ["FR-06", "设备", "10 类设备与核心 / 可选分组", "P0", "已实现"],
        ["FR-07", "设备", "子卡片单卡三态与固定", "P0", "已实现"],
        ["FR-08", "设备", "设备电池 / 功率能耗规则", "P0", "已实现"],
        ["FR-09", "周边", "5 类电器与勾选", "P0", "已实现"],
        ["FR-10", "周边", "WiFi / 基站 / 云固定项", "P0", "已实现"],
        ["FR-11", "周边", "11 种出行与分层展开", "P0", "已实现"],
        ["FR-12", "总览", "汇总、等价换算、特斯拉续航", "P0", "已实现"],
        ["FR-13", "总览", "周边五档评价", "P0", "已实现"],
        ["FR-14", "历史", "自然日记录与 730 天保留", "P0", "已实现"],
        ["FR-15", "历史", "跨日归档与每日用量归零", "P0", "已实现"],
        ["FR-16", "设置", "容量 / 功率锁定开关", "P0", "已实现"],
        ["FR-17", "设置", "恢复示例值与说明", "P1", "已实现"],
        ["FR-18", "系统", "本地存储、离线与隐私", "P0", "已实现"],
        ["FR-19", "体验", "暖白视觉、响应式、可访问性", "P1", "已实现"],
        ["FR-20", "交付", "Android / iOS / PWA 多端交付", "P0", "已实现"],
    ],
    widths=(0.65, 0.75, 3.45, 0.8, 0.9),
    font_size=7.8,
)

# 5.2 onboarding
h2_add("5.2 首次使用与身体资料")
req_add("FR-01", "首次资料录入", "P0", [
    "首次启动且本地没有完整 profile 时，自动打开「先认识一下你」资料 sheet；必须录入年龄、身高、体重。",
    "年龄范围 16–80 岁，身高 140–210 cm，体重 40–120 kg；越界值按边界夹取。",
    "资料 sheet 在 onboarding 模式下不显示关闭按钮，点背景也不关闭；保存后写入本机 profile，并进入主界面。",
    "保存后再次启动不再询问；资料只保存在本机。",
], "全新安装可见；保存后刷新不再出现；未保存不能通过背景返回；边界输入被夹取；换日不清资料。")

req_add("FR-02", "资料修改与设置入口", "P0", [
    "顶部齿轮或自体页「身体资料 → 修改」打开设置模式；设置模式可关闭、可保存。",
    "设置 sheet 包含年龄、身高、体重，以及数据保护配置锁。",
    "保存后立即重算 BMR、静息 / 活动功率、步长、BMI 与今日历史；取消关闭不生效。",
    "onboarding 模式隐藏配置锁区域，仅设置模式展示。",
], "齿轮 / 修改均可进入；保存后页面立即更新；关闭不保存；onboarding 不出现配置锁。")

req_add("FR-03", "实际年龄 BMR 与身体摘要", "P0", [
    "自体页显示只读资料卡：年龄、身高、体重、BMI 和 BMI 标签；身高体重滑条已移除。",
    "BMR 使用实际年龄：BMR（kcal/天）= 10×体重 + 6.25×身高 − 5×年龄 − 78；性别取男女平均常数。",
    "静息功率 = BMR × (4184/86400)；活动功率 = 静息功率 × MET；BMI = 体重 / (身高/100)²。",
    "资料卡展示「基础代谢按实际年龄计算」，并提供「修改」入口。",
], "示例 30 岁 / 170 cm / 68 kg 时 BMR = 1514.5 kcal；修改年龄后 BMR 与静息 / 活动功率同步变化；不出现身高 / 体重滑条。")

# 5.3 body
h2_add("5.3 自体每日数据")
req_add("FR-04", "每日步数与快捷预设", "P0", [
    "步数范围 0–30,000，步进 50；顶部输出千分位格式。",
    "提供 3,000 / 5,000 / 8,000 / 10,000 / 15,000 / 20,000 六个快捷预设；点击后滑条与数值同步。",
    "按 100 步/分钟、步长 0.413×身高 计算步行距离、活动分钟和活动耗能。",
    "换日后步数归零；配置锁不影响步数。",
], "滑条步进 50；预设点击即生效；输出与公式一致；换日后为 0；锁定状态下仍可编辑（除非卡片本身固定）。")

req_add("FR-05", "活动强度与快捷预设", "P0", [
    "MET 范围 1–12，步进 0.05；显示活动标签（静坐 / 站立 / 散步 / 快走 / 慢跑 / 骑行 / 跑步 / 高强度）。",
    "提供 1.3 / 2.5 / 4.2 / 5.5 / 7.0 / 10.0 六个预设；当前值匹配时高亮。",
    "活动耗能 = 静息功率 × (MET − 1) × 步数活动小时 / 1000；步数为 0 时活动耗能恒为 0。",
    "换日后 MET 回到 1.3（静坐）。",
], "预设与滑条联动；步数 0 时活动耗能为 0；MET 边界正确；换日后显示 1.3。")

# 5.4 devices
h2_add("5.4 设备")
req_add("FR-06", "设备清单与核心 / 可选分组", "P0", [
    "设备共 10 类：手机、真无线耳机、平板电脑、台式主机为核心；笔记本、移动电源、头戴式耳机、运动相机、相机、拍立得为可选。",
    "首屏只渲染 4 类核心设备；可选 6 类位于「展开更多设备」，默认未勾选。",
    "每类设备有自己的容量 / 功率范围、步进和默认值；新增安装只勾选核心设备。",
    "旧版本升级时，历史上正在计入的设备按旧用量推断为已勾选，避免升级后直接归零。",
], "首屏 4 类核心；展开后 6 类可选；新安装默认只计入核心；旧数据升级保留原有勾选状态（按旧值推断）。")

req_add("FR-07", "子卡片三态与单卡固定", "P0", [
    "每张设备卡右上角是一个状态按钮：未勾选（空心圆）→ 点击勾选（黑色对勾，计入且可调）→ 再点固定（蓝色锁，计入且卡片内控件禁用）→ 再点取消勾选（空心圆，不计入）。",
    "固定只作用于当前卡片；其他卡片仍可调。状态按设备键保存在本机。",
    "勾选与否决定该设备是否计入；固定不改变计入状态，只冻结控件。",
    "换日归零会清除单卡固定，但保留勾选状态。",
    "顶部汇总没有全局锁按钮；全局配置锁见 FR-16。",
], "三种状态循环正确；固定后只有该卡滑条 / 输入禁用；其他卡可编辑；刷新后状态保留；换日后固定解除、勾选保留。")

req_add("FR-08", "设备能耗计算", "P0", [
    "电池设备：容量 Wh = mAh × 3.7 / 1000（笔记本按 Wh 直接输入）；墙端每次充满 = 容量 Wh / 0.85；日耗 = 墙端 Wh × 每日完整充电次数 / 1000。",
    "功率设备（台式主机）：日耗 = 功率 W × 每日使用小时 / 1000。",
    "未勾选时该设备对总能耗贡献为 0；容量 / 功率 / 次数保留，重新勾选后恢复。",
    "容量与功率属于设备配置；换日不改变，配置锁可防止误改。",
], "手机 5000 mAh × 1 次约 0.0218 kWh；台式 300 W × 2 h = 0.6 kWh；未勾选为 0；换日后容量 / 功率不变。")

# 5.5 appliances/fixed
h2_add("5.5 电器与固定项")
req_add("FR-09", "电器清单与勾选", "P0", [
    "电器共 5 类：冰箱、空调、电热水器、洗衣机、电视。",
    "默认只勾选冰箱（80 W × 24 h = 1.92 kWh）；其余默认未勾选。",
    "每台电器右上角三态按钮；未勾选时不计入，勾选后按功率 × 时长计入；固定时冻结功率 / 时长控件。",
    "换日只将电器使用时长归零，功率和勾选保留；配置锁可冻结电器功率。",
], "默认冰箱 1.92 kWh；空调 1200 W × 2 h = 2.4 kWh；未勾选为 0；换日后时长 0、功率不变。")

req_add("FR-10", "固定项", "P0", [
    "WiFi 路由器：8 W × 24 h = 0.192 kWh/天。",
    "通信基站：固定 0.25 kWh/天；云服务器及传输：固定 0.25 kWh/天。",
    "固定项合计 0.692 kWh/天，每天都计入，不提供勾选 / 关闭入口。",
    "固定项与换日归零无关：即使所有可调用量为 0，固定项仍构成基线的一部分。",
], "周边固定项显示 0.69 kWh/天；总账包含 0.692；刷新 / 换日后仍存在；无关闭入口。")

# 5.6 travel
h2_add("5.6 今日出行")
req_add("FR-11", "出行方式与分层展开", "P0", [
    "共 11 种出行：地铁、电动车、打车·电车、打车·油车、公交车、电车（私家）、油车（私家）、大巴、火车、高铁、飞机。",
    "首屏仅显示地铁、电动车；其余 5 种日常 + 4 种城际位于「展开更多出行」，默认未勾选。",
    "日常滑条出行按因素计算；城际为手动公里输入、按人均公里能耗计算。",
    "每张出行卡右上角三态按钮；固定时冻结该卡的滑条 / 输入；换日只清零里程 / 时长，保留勾选和配置。",
], "首屏 2 项；展开后 9 项；默认地铁 30 分钟 + 电动车 30 分钟 = 1.23 kWh；城际输入正常；换日后为 0。")

# 5.7 overview
h2_add("5.7 总览与评价")
req_add("FR-12", "汇总、占比与等价换算", "P0", [
    "总功耗 = 自体 + 设备 + 周边；周边 = 固定项 + 电器 + 出行。",
    "总览展示三类明细、占比、总功耗、等效平均功率；顶部 hero 随当前分页显示对应分项，总览显示总功耗。",
    "每个分页的 hero 显示等价换算：标准煤 kg（1 kWh ≈ 0.12284 kg）与特斯拉 Model X 可跑公里数（1 kWh ≈ 4.8 km，按约 20.8 kWh/100km）。",
    "等价换算只是数量级参考，不代表真实计量或车辆充电行为。",
], "总览 6.57 kWh / 274 W（示例）；三类合计相等；标准煤 0.81 kg、特斯拉 31.5 km；无「炸鸡排」旧文案。")

req_add("FR-13", "周边五档评价", "P0", [
    "评价依据为周边功耗（固定项 + 电器 + 出行），不是总功耗；评价卡显示「按周边 X kWh 评定」。",
    "五档阈值：省电模式 ≤5；节能模式 ≤15；均衡模式 ≤25；性能模式 ≤40；高耗能模式 >40 kWh。",
    "每档使用用户指定的文案：第一档至第五档分别为「点几块炭够你活一天，牛逼」等五条。",
    "历史中的档位也按当日周边功耗重新判定；评价卡颜色、印章数字与五格刻度随档位变化。",
], "周边 3.84 kWh → 省电模式；15 kWh → 节能模式；40.1 kWh → 高耗能模式；历史档位同步。")

# 5.8 history/rollover
h2_add("5.8 历史与跨日")
req_add("FR-14", "自然日历史与 730 天保留", "P0", [
    "每个本地自然日最多一条记录，字段包括日期、总功耗、自体、设备、周边。",
    "历史最多保留 730 天（约 2 年）；按日期倒序保存；总览展示最近 7 天柱状图。",
    "今天的数据随录入实时更新；昨天及更早的数据保持不变。",
    "历史只保存在本机；清除应用 / 站点数据会丢失；当前版本不提供导出 / 云备份。",
], "同日更新不新增重复记录；最多 730 条；7 天柱显示；换日后前一日仍在；无网络写入。")

req_add("FR-15", "跨日归档与用量归零", "P0", [
    "触发：应用启动、从后台回到前台、页面持续打开跨过本地午夜（每 60 秒检查）。",
    "触发后先将上一日按上一日期归档，再清零今日可调用量：步数、MET 1.3、设备充电次数 / 主机时长、电器时长、出行里程 / 时长。",
    "保留：身体资料、设备容量 / 功率、电器功率、已勾选项目、配置锁开关；单卡固定会解除。",
    "旧版本升级（无日期戳）首次打开会清一次旧的可调用量；全新安装未完成 onboarding 时保留示例默认值。",
    "归零后总额不为 0：基础代谢 + 固定项约 2.45 kWh（示例资料）；显示「新的一天：昨日用量已归档，今日可调用量已归零」。",
], "日期设为过去后重载：步骤 / 充电次数 / 冰箱时长 / 地铁里程为 0；4300 mAh、440 W、70 W 保留；日期为今天；提示出现。")

# 5.9 config/reset
h2_add("5.9 配置保护与恢复")
req_add("FR-16", "容量 / 功率锁定开关", "P0", [
    "设置中提供开关，文案为「锁定设备和电器电池容量、功率」；仅在设置模式显示，onboarding 不显示。",
    "开启后冻结：设备电池容量、笔记本 Wh、台式主机功率、电器功率；不冻结每天的充电次数、使用时长和出行。",
    "开关状态保存在本机，跨日不丢失；关闭后恢复可调；与单卡三态固定互相独立。",
    "配置锁不改变任何计算结果，只影响可编辑性。",
], "开启后容量 / 功率不可调、次数 / 时长 / 出行可调；关闭后容量可调；跨日 / 刷新后开关保持；锁定时总功耗不变。")

req_add("FR-17", "恢复示例值与说明", "P1", [
    "说明页提供「恢复示例值」：把当前设置恢复为示例值，保留身体资料与历史，清空单卡固定，配置锁开关保留。",
    "说明页列出公式、口径、评价分级、历史保留、等价换算、离线隐私说明。",
    "重置不删除历史；不把历史条目标记为已删除。",
], "重置后当前分页回到示例值；历史条数不变；身体资料保留；单卡固定清空；提示出现。")

# 5.10 system/platform
h2_add("5.10 系统、体验与平台")
req_add("FR-18", "本地存储、离线与隐私", "P0", [
    "Android / iOS 完全离线，不申请网络 / 存储 / 定位等运行时权限；无账号、无埋点、无第三方 SDK。",
    "数据存于本机：当前设置、历史、身体资料、单卡固定；iOS 通过 WKWebView 桥接写入 UserDefaults，Android / PWA 使用 localStorage。",
    "PWA 需要 HTTPS 静态托管；Service Worker 首次加载后缓存页面；数据保存在浏览器站点存储。",
    "历史与设置写入异常时应用仍可计算；不会因为存储异常阻塞核心流程。",
], "APK 无 uses-permission；页面无网络请求；PWA 停掉静态服务器后仍能打开；清除数据后重新进入首次录入。")

req_add("FR-19", "视觉、响应式与可访问性", "P1", [
    "暖白纸感：奶油底色、白卡片、深色粗体标题、天青蓝操作色；背景随能耗在浅绿 / 浅蓝 / 杏色 / 浅珊瑚 / 暖玫瑰之间变化，任何状态不得变黑。",
    "四个分页、底部导航、卡片化布局；360×800 与 390×844 视口均可用；适配安全区、竖屏。",
    "交互控件提供可读标签、ARIA 状态、键盘焦点；支持 prefers-reduced-motion；固定 / 勾选状态有视觉差异。",
    "动效轻量，不做强烈霓虹 / 玻璃拟态；滑条与按钮在触屏上可操作。",
], "360 / 390 视口无横向溢出；高能耗背景保持浅色；按钮有 aria-label；开关 / 三态按钮可通过键盘聚焦。")

req_add("FR-20", "多平台交付", "P0", [
    "Android：签名 APK，minSdk 23、targetSdk 34；当前版本 v2.1.2 / versionCode 13。",
    "iOS：SwiftUI + WKWebView 的 Xcode 工程，iOS 15+；当前版本 v2.1.2 / Build 13；受签名与 macOS 编译限制。",
    "PWA：HTTPS 静态站点 + manifest + service worker；PWA cache 2.1.2；可添加到主屏幕并在首次加载后离线使用。",
    "三端共用同一套 HTML/CSS/JS 与计算模型；平台壳只负责容器、键盘、返回、存储桥接。",
], "三端规则一致；Android 包可安装、签名通过、无权限；iOS 工程可被 Xcode 打开；PWA 可离线启动。")




# ==========================================================================
# 6 RULES AND ALGORITHMS
# ==========================================================================
h1_add("6. 业务规则与算法", new_page=False)

p_add("本章给出产品数值口径。所有公式均为估算，不用于正式碳核算；用户可在说明页看到同一套口径。")

h2_add("6.1 自体与活动")
code_block([
    "BMR(kcal/day) = 10 × weight(kg) + 6.25 × height(cm) − 5 × age − 78",
    "rest_power(W) = BMR × 4184 / 86400",
    "active_power(W) = rest_power × MET",
    "walk_minutes = steps / 100",
    "activity_kWh = rest_power × (MET − 1) × (walk_minutes / 60) / 1000",
    "body_kWh = rest_power × 24 / 1000 + activity_kWh",
    "BMI = weight / (height / 100)^2",
])
add_info_table([
    ("示例资料", "30 岁 / 170 cm / 68 kg；BMR 1514.5 kcal/天；静息 73.34 W；快走 4.2 MET 时活动 308.03 W"),
    ("示例步数", "8,000 步；5.62 km；80 分钟；活动耗能 0.3129 kWh"),
    ("换日基线", "步数 0、MET 1.3 时，自体约 1.76 kWh（不含活动），加固定项 0.692 后约 2.45 kWh"),
], widths=(1.2, 5.3))

h2_add("6.2 设备")
code_block([
    "battery_Wh = capacity_mAh × 3.7 / 1000         # 笔记本直接使用 Wh",
    "wall_Wh_per_charge = battery_Wh / 0.85",
    "battery_kWh = wall_Wh_per_charge × cycles / 1000",
    "power_kWh = watts × hours / 1000                 # 台式主机",
])
add_table(
    ["设备", "模式", "默认容量 / 功率", "默认计入"],
    [
        ["手机", "电池", "5000 mAh × 1 次", "是（核心）"],
        ["真无线耳机", "电池", "500 mAh × 1 次", "是（核心）"],
        ["平板电脑", "电池", "8000 mAh × 0.75 次", "是（核心）"],
        ["台式主机", "功率", "300 W × 2 h", "是（核心）"],
        ["笔记本", "电池 Wh", "60 Wh × 1 次", "否（可选）"],
        ["移动电源", "电池", "10000 mAh × 0.5 次", "否（可选）"],
        ["头戴式耳机", "电池", "800 mAh × 0.75 次", "否（可选）"],
        ["运动相机", "电池", "1800 mAh × 0.5 次", "否（可选）"],
        ["相机", "电池", "2400 mAh × 0.25 次", "否（可选）"],
        ["拍立得", "电池", "1200 mAh × 0.25 次", "否（可选）"],
    ],
    widths=(1.05, 0.85, 2.4, 2.2),
    font_size=8.4,
)

h2_add("6.3 电器与固定项")
code_block([
    "appliance_kWh = watts × hours / 1000",
    "WiFi = 8 W × 24 h / 1000 = 0.192 kWh/day",
    "base_station = 0.25 kWh/day",
    "cloud = 0.25 kWh/day",
    "fixed_total = 0.692 kWh/day",
])
add_table(
    ["电器", "功率范围 / 默认功率", "默认时长", "默认计入"],
    [
        ["冰箱", "50–300 W / 80 W", "24 h", "是"],
        ["空调", "700–3,500 W / 1,200 W", "0 h", "否"],
        ["电热水器", "1,000–3,000 W / 2,000 W", "0 h", "否"],
        ["洗衣机", "200–1,200 W / 500 W", "0 h", "否"],
        ["电视", "50–400 W / 120 W", "0 h", "否"],
    ],
    widths=(1.0, 2.4, 1.1, 1.0),
    font_size=8.4,
)

h2_add("6.4 出行因素")
add_table(
    ["出行", "输入", "因素", "默认", "默认计入"],
    [
        ["地铁", "时长 min", "35 km/h；0.060 kWh/人·km", "30 min", "是"],
        ["电动车", "时长 min", "20 km/h；0.018 kWh/km", "30 min", "是"],
        ["打车·电车", "里程 km", "0.150 kWh/km", "0", "否"],
        ["打车·油车", "里程 km", "0.550 kWh/km；≈6 L/100km", "0", "否"],
        ["公交车", "里程 km", "0.035 kWh/人·km", "0", "否"],
        ["电车（私家）", "里程 km", "0.150 kWh/km", "0", "否"],
        ["油车（私家）", "里程 km", "0.600 kWh/km", "0", "否"],
        ["大巴", "公里输入", "0.050 kWh/人·km", "0", "否"],
        ["火车", "公里输入", "0.045 kWh/人·km", "0", "否"],
        ["高铁", "公里输入", "0.065 kWh/人·km", "0", "否"],
        ["飞机", "公里输入", "0.300 kWh/人·km", "0", "否"],
    ],
    widths=(1.1, 1.15, 2.35, 0.95, 0.8),
    font_size=8.3,
)

h2_add("6.5 总账与等价换算")
code_block([
    "surrounding = fixed + appliances + trips",
    "total = body + device + surrounding",
    "share_x = x / total",
    "average_W = total_kWh × 1000 / 24",
    "coal_kg = total_kWh × 0.12284",
    "tesla_km = total_kWh × 4.8     # ≈20.8 kWh/100km",
])
p_add("示例：自体 2.0731 + 设备 0.6501 + 周边 3.842 = 6.5652 kWh；平均 273.55 W；完全燃烧标准煤 0.8065 kg；特斯拉 Model X 约 31.5 km。")

h2_add("6.6 评价规则")
add_table(
    ["周边功耗", "档位", "评价文案（用户指定）"],
    [
        ["≤ 5 kWh", "省电模式", "点几块炭够你活一天，牛逼"],
        ["≤ 15 kWh", "节能模式", "控制全球变暖有你一份功劳"],
        ["≤ 25 kWh", "均衡模式", "试着把空调固定在26度，指不定会少花几块钱"],
        ["≤ 40 kWh", "性能模式", "耗能有点高，是不是需要注意下账单..."],
        ["> 40 kWh", "高耗能模式", "你知道你带得动几张GPU吗...不告诉你！"],
    ],
    widths=(1.1, 1.2, 4.2),
    font_size=8.5,
)
p_add("评价卡显示档位、文案和「按周边 X kWh 评定」；五格刻度点亮当前档位及以下。历史记录不保存档位，展示时按当日周边功耗重新判定。")

h2_add("6.7 换日规则")
add_table(
    ["项", "规则"],
    [
        ["日期来源", "设备本地时区的自然日；日期键 YYYY-MM-DD"],
        ["触发时机", "启动、回到前台、页面跨午夜（60 秒检查）"],
        ["归档", "把上一日总功耗 / 自体 / 设备 / 周边写入上一日历史记录"],
        ["归零", "步数 0、MET 1.3、设备 cycles 0 / hours 0、电器 hours 0、出行值 0"],
        ["保留", "年龄 / 身高 / 体重、容量 / 功率、已勾选 / 已展开、配置锁开关、历史"],
        ["解锁", "单卡三态固定清零，方便新一天编辑"],
        ["提示", "「新的一天：昨日用量已归档，今日可调用量已归零」"],
        ["迁移", "旧数据无日期戳：升级后首次打开清一次可调用量；全新安装保留示例默认值"],
    ],
    widths=(1.0, 5.5),
    font_size=8.5,
)

h2_add("6.8 输入夹取与步进")
add_table(
    ["输入", "范围", "步进 / 规则"],
    [
        ["年龄", "16–80 岁", "整数"],
        ["身高", "140–210 cm", "整数"],
        ["体重", "40–120 kg", "整数"],
        ["步数", "0–30,000", "50"],
        ["MET", "1–12", "0.05"],
        ["设备容量 / 功率", "按设备定义", "按设备 step 夹取"],
        ["完整充电次数", "0–3", "0.25"],
        ["设备 / 电器时长", "0–24 h", "0.5"],
        ["出行时长 / 里程", "按交通方式定义", "按定义 step"],
    ],
    widths=(1.45, 2.2, 2.85),
    font_size=8.5,
)



# ==========================================================================
# 7 DATA / PRIVACY
# ==========================================================================
h1_add("7. 数据与隐私", new_page=False)

h2_add("7.1 数据实体")
add_table(
    ["实体", "字段", "用途", "存储位置"],
    [
        ["Profile", "age / height / weight / complete", "一次性身体资料与 BMR", "powercalc.profile.v1"],
        ["State", "day / configLocked / age / height / weight / steps / met / devices / appliances / trips / tripEnabled / tab", "当前计算状态与 UI 选择", "powercalc.state.v2"],
        ["History", "date / total / body / device / transit", "每日历史与 7 天柱", "powercalc.history.v1"],
        ["ItemLocks", "device / appliance / trip → key→true", "单卡三态固定", "powercalc.itemLocks.v1"],
    ],
    widths=(0.95, 2.5, 1.85, 1.3),
    font_size=8.2,
)

h2_add("7.2 存储键与 iOS 桥接")
add_table(
    ["Web 键", "iOS UserDefaults 键", "内容"],
    [
        ["powercalc.state.v2", "powerLedger.state.v2", "当前设置 / 状态（含日期、配置锁）"],
        ["powercalc.history.v1", "powerLedger.history.v1", "每日历史，最多 730 条"],
        ["powercalc.profile.v1", "powerLedger.profile.v1", "一次性身体资料"],
        ["powercalc.itemLocks.v1", "powerLedger.itemLocks.v1", "单卡固定状态"],
    ],
    widths=(2.1, 2.35, 2.1),
    font_size=8.4,
)
p_add("iOS 通过 WKUserScript 在文档开始时注入 localStorage shim，再由 WKScriptMessageHandler 写入 UserDefaults；Android / PWA 使用 WebView / 浏览器的 localStorage。两端不共享数据。")

h2_add("7.3 数据生命周期")
add_table(
    ["时机", "行为"],
    [
        ["当天输入", "实时写入 state / history；history 同日只保留一条"],
        ["跨日", "上一日归档，可调用量清零，day 更新为今天"],
        ["730 天", "历史超出上限时从最旧记录开始丢弃"],
        ["恢复示例值", "重置当前设置，保留 profile 与 history；清空 itemLocks；configLocked 保留"],
        ["清除应用 / 站点数据", "全部本地数据删除，重新进入首次录入"],
        ["卸载 / 删除主屏幕图标", "系统可能删除站点数据；不提供云恢复"],
    ],
    widths=(1.5, 5.0),
    font_size=8.5,
)

h2_add("7.4 隐私与网络边界")
for item in [
    "Android / iOS 不申请任何权限；没有网络请求；无账号、无埋点、无第三方 SDK。",
    "PWA 仅托管静态 HTML / CSS / JS / 图标；不上传计算数据；需要 HTTPS 与一次联网加载。",
    "历史、身体资料、配置锁状态只保存在本机；卸载 / 清理数据后不可恢复。",
    "应用不用于医疗、碳核算或电费结算；等价换算仅作数量级参考。",
]:
    bullet_add(item)

h2_add("7.5 迁移与兼容")
p_add("v2.1.1 引入 day 字段，用于跨日判断；v2.1.2 将 configLocked 放入 state，不新增持久化键。旧版本数据无 day 字段时，首次打开会触发一次可调用量清理，同时保留容量 / 功率 / 资料。")



# ==========================================================================
# 8 UX / VISUAL
# ==========================================================================
h1_add("8. 交互与视觉规范", new_page=False)

h2_add("8.1 设计方向")
p_add("整体采用「暖白纸感」：奶油纸底、白色圆角卡片、深色粗体标题、天青蓝操作色；背景随当前页能耗轻微变化，但只使用浅绿、浅蓝、杏色、浅珊瑚、暖玫瑰，任何状态下都不出现黑色背景。目标是让能源数据看起来亲切、可读，而不是仪表盘或工业监控。")

h2_add("8.2 颜色与字体")
add_table(
    ["Token", "值", "用途"],
    [
        ["Paper", "#F7F4EE", "页面底色"],
        ["Surface", "#FFFDF8", "卡片"],
        ["Ink", "#201C17", "主文字 / 标题"],
        ["Muted", "#766D61", "说明 / 次要信息"],
        ["Blue", "#159BB9", "操作 / 选中 / 锁状态"],
        ["Blue Soft", "#EAF6F9", "标签 / 表头浅底"],
        ["Line", "#DED7CC", "边框 / 分隔"],
        ["Warm Rose", "#E7B8AE", "最高背景氛围（仍为浅色）"],
    ],
    widths=(0.9, 1.2, 2.3),
    font_size=8.4,
)
p_add("字体：微软雅黑 / 系统中文无衬线；标题使用粗体与紧凑字距，正文 10.5 pt，表格 8–9 pt。数字使用等宽数字特性，便于比较。")

h2_add("8.3 布局与导航")
for item in [
    "顶部 hero：当前分类标签、日期、设置 / 说明、大号 kWh、等效平均功率、等价换算；总览额外显示三类占比条。",
    "底部分页：自体 / 设备 / 周边 / 总览；固定底部，适配安全区。",
    "卡片：圆角、浅边框、白色；每张卡有图标、名称、说明、数值和右上角三态按钮。",
    "首屏核心项 + 虚线「展开更多」；展开不改变计入状态。",
    "设置 / 说明使用底部 sheet；onboarding 不可关闭，设置可关闭。",
]:
    bullet_add(item)

h2_add("8.4 控件与状态")
add_table(
    ["控件", "规范"],
    [
        ["滑条", "触控拇指明显；垂直滚动时通过卡片固定 / 配置锁避免误触；步进按业务规则"],
        ["三态按钮", "空心圆 / 黑底对勾 / 蓝底锁；aria-label 描述下一动作"],
        ["开关", "44×26 px；开蓝、关灰；角色 switch；状态持久化"],
        ["预设按钮", "6 个步数预设、6 个 MET 预设；当前值高亮蓝色"],
        ["数字输入", "公里数输入；输入时仅在失焦 / 变更时夹取；键盘可收起"],
        ["反馈", "Toast 1.9 秒；不遮挡主要操作；不依赖网络"],
    ],
    widths=(1.3, 5.2),
    font_size=8.5,
)

h2_add("8.5 响应式与可访问性")
for item in [
    "移动优先，最大内容宽度 560 px；360×800 与 390×844 通过布局验证；iPad 使用同一居中布局。",
    "竖屏；底部导航与 sheet 适配 safe-area-inset；页面滚动区域独立于固定导航。",
    "按钮、滑条、开关有可读 aria-label / aria-checked；键盘可聚焦；支持 prefers-reduced-motion。",
    "不依赖颜色单独传递状态：三态同时用图标与形状；档位同时用数字、文字和刻度。",
    "任何高能耗状态都保持浅色纸面，不出现黑底反色。",
]:
    bullet_add(item)

picture(ASSETS / "four-tabs.png", 5.95, "图 1 · 四个分页：自体、设备、周边、总览（v2.1.2）")



# ==========================================================================
# 9 NFR
# ==========================================================================
h1_add("9. 非功能需求", new_page=False)

add_table(
    ["编号", "类别", "要求", "验收方式"],
    [
        ["NFR-01", "离线", "Android / iOS 无网络依赖；所有计算、存储、历史在本机完成", "断网使用；静态检查无网络请求"],
        ["NFR-02", "隐私", "无权限、无账号、无埋点、无第三方 SDK；PWA 只托管静态文件", "APK badging 无 uses-permission；页面无 fetch/XHR"],
        ["NFR-03", "性能", "冷启动内容可见 ≤2 秒（中端机目标）；单次滑条更新 ≤100 ms；历史重绘 ≤300 ms", "真机 / WebView 走查"],
        ["NFR-04", "可靠性", "存储异常不阻塞计算；输入夹取；历史上限 730；同日更新不重复", "异常注入 / 边界输入"],
        ["NFR-05", "兼容性", "Android 6+；iOS 15+；现代 Safari / Chromium；360–390 px 宽度", "模拟器 / 浏览器视口 / Xcode 工程检查"],
        ["NFR-06", "可访问性", "可读标签、键盘焦点、对比度、减少动效；关键按钮可触达", "人工走查 + 键盘 / 读屏基础检查"],
        ["NFR-07", "包体", "Android APK 约 100 KB；PWA 站点资源 <1 MB；不引入大依赖", "构建产物大小检查"],
        ["NFR-08", "安全 / 签名", "Android 使用本地 keystore 签名；公开分发应换自己的密钥；iOS 需 Apple 签名", "apksigner / Xcode 签名检查"],
        ["NFR-09", "可维护性", "共享一份 HTML/CSS/JS 与模型；版本号 / 迁移 / 测试可追溯", "代码结构、测试、README"],
        ["NFR-10", "本地化", "简体中文；公制单位；日期本地化；货币 / 语言当前不扩展", "文案走查"],
    ],
    widths=(0.7, 0.8, 3.2, 1.85),
    font_size=8.1,
)
p_add("当前交付验证：Android APK 通过 aapt2 / zipalign / apksigner 校验，无 uses-permission；iOS 工程通过 pbxproj、Info.plist、隐私清单、资源 JSON 与 AppIcon 尺寸检查，但未在 macOS 编译；PWA service worker 在本地 HTTP 环境完成离线启动验证。")



# ==========================================================================
# 10 ACCEPTANCE
# ==========================================================================
h1_add("10. 验收与测试", new_page=True)

h2_add("10.1 验收矩阵")
add_table(
    ["编号", "场景", "预期结果", "关联需求"],
    [
        ["AC-01", "全新安装首次打开", "出现资料 sheet；录入并保存；刷新不再出现", "FR-01"],
        ["AC-02", "设置修改年龄", "BMR / 静息 / 活动功率立即更新；资料卡同步", "FR-02 / FR-03"],
        ["AC-03", "步数 8,123 输入", "归到 8,100；距离 / 分钟 / 活动耗能重算", "FR-04"],
        ["AC-04", "MET 预设点击", "滑条和输出同步；活动标签变化", "FR-05"],
        ["AC-05", "设备未勾选 / 勾选 / 固定", "三态循环；未勾选 0；固定只冻结该卡", "FR-06 / FR-07 / FR-08"],
        ["AC-06", "电器勾选与固定", "未勾选 0；勾选后按时长；固定冻结功率 / 时长", "FR-09"],
        ["AC-07", "出行展开与录入", "首屏 2 项；展开 9 项；城际公里输入生效", "FR-11"],
        ["AC-08", "总览与评价", "占比合计 100%；评价按周边分档；特斯拉 / 标准煤正确", "FR-12 / FR-13"],
        ["AC-09", "跨日刷新", "昨日归档；步数 / 次数 / 时长 / 出行 0；容量 / 功率保留", "FR-14 / FR-15"],
        ["AC-10", "配置锁", "容量 / 功率不可调；次数 / 时长 / 出行可调；跨日保持", "FR-16"],
        ["AC-11", "恢复示例值", "当前值恢复；资料 / 历史保留；单卡固定清空", "FR-17"],
        ["AC-12", "离线和隐私", "断网可用；无权限；无网络请求", "FR-18"],
        ["AC-13", "360 / 390 视口", "无横向溢出；高能耗背景浅色；分页可切换", "FR-19"],
        ["AC-14", "Android 包", "签名通过；versionCode 13 / 2.1.2；无权限", "FR-20"],
        ["AC-15", "PWA 离线", "SW 激活；停止服务器后仍能打开", "FR-18 / FR-20"],
    ],
    widths=(0.55, 1.7, 3.2, 1.1),
    font_size=8.0,
)

h2_add("10.2 当前验收结论")
add_table(
    ["范围", "结果"],
    [
        ["模型测试", "125 项全部通过：BMR、步数、设备、电器、出行、评价边界、特斯拉换算、日期 / 配置锁状态等"],
        ["UI 交互", "390×844 与 360×800 四页切换、首次资料、设置、单卡三态、配置锁、开关、换日重置、历史"],
        ["换日断言", "旧日期 + 旧用量重载：步骤 / 设备次数 / 冰箱时长 / 地铁归零；4300 mAh / 440 W / 70 W 保留；配置锁仍生效"],
        ["Android 包", "v2.1.2 / versionCode 13；已签名；zipalign 通过；无 uses-permission"],
        ["iOS 工程", "v2.1.2 / Build 13；pbxproj / plist / 资源 / 图标通过结构检查；未在本机编译或签名"],
        ["PWA", "manifest + service worker；本地 HTTP 离线启动通过；需 HTTPS 托管"],
    ],
    widths=(1.2, 5.3),
    font_size=8.3,
)
p_add("iOS 原生 IPA 的缺省不是产品缺陷，而是当前 Windows 环境的构建 / 签名限制；iOS 交付为 Xcode 工程，需 Mac 或云端 macOS + 自己的签名。")

h2_add("10.3 Definition of Done")
for item in [
    "所有 P0 需求通过验收矩阵；P1 需求完成或有明确的后续版本说明。",
    "模型测试、UI 交互、跨日、配置锁、平台打包检查通过。",
    "Android APK 可安装、无权限、签名正常；iOS 工程可在 Xcode 打开；PWA 可在 HTTPS 上离线启动。",
    "无阻断性崩溃、无数据未保存、无跨日不归零问题。",
    "README / PRD / 版本号 / 变更记录保持一致。",
]:
    bullet_add(item)



# ==========================================================================
# 11 RELEASE
# ==========================================================================
h1_add("11. 版本与发布", new_page=True)

h2_add("11.1 当前交付物")
add_table(
    ["产物", "版本", "形态", "分发说明"],
    [
        ["Android APK", "v2.1.2 / code 13", "签名 APK", "本地安装；无 Google Play 上架"],
        ["iOS Xcode 工程", "v2.1.2 / Build 13", "SwiftUI + WKWebView 源码", "Mac / 云端 macOS 编译签名；Windows 可走 GitHub Actions + Sideloadly"],
        ["PWA", "cache 2.1.2", "静态站点 zip", "HTTPS 托管；添加到主屏幕；首次联网后可离线"],
        ["单文件网页版", "v2.1.2", "单个 HTML", "快速预览 / 简单托管；无 service worker"],
    ],
    widths=(1.2, 1.15, 1.6, 2.55),
    font_size=8.3,
)

h2_add("11.2 产品版本历史")
add_table(
    ["版本", "主题", "关键变化"],
    [
        ["v1.5", "暖白主题", "深色霓虹改为暖白纸感；背景仍随能耗变化但不发黑"],
        ["v1.6", "打车拆分", "打车拆为电车 / 油车；出行方式 11 种"],
        ["v1.7", "评价与历史", "五档评价、7 天历史、iOS Xcode 工程"],
        ["v1.7.1", "历史保留", "Android 历史延长至 730 天"],
        ["v2.0", "交互重构", "一次性身体资料、实际年龄 BMR、勾选、展开、步数 50 步、单卡三态"],
        ["v2.1.0", "评价与固定", "轴对称齿轮、单卡三态、周边五档、特斯拉换算"],
        ["v2.1.1", "跨日归零", "日期戳、昨日归档、每日可调用量清零"],
        ["v2.1.2", "配置保护", "容量 / 功率锁定开关；换日保留配置；最终当前版本"],
    ],
    widths=(0.8, 1.35, 4.35),
    font_size=8.2,
)

h2_add("11.3 发布流程")
add_table(
    ["阶段", "动作", "产出 / 门槛"],
    [
        ["需求", "收集反馈、确认范围和优先级", "PRD 评审稿"],
        ["设计 / 技术", "交互、视觉、数据模型与平台方案评审", "设计定稿 / 技术评估"],
        ["开发", "共享页面层 + Android / iOS / PWA 壳", "可构建包"],
        ["QA", "模型、UI、跨日、平台打包、隐私检查", "验收报告"],
        ["发布", "版本号、签名、产物、说明、哈希", "APK / iOS zip / PWA zip"],
        ["复盘", "收集用户反馈，记录下一版本候选项", "路线图 / 变更记录"],
    ],
    widths=(0.9, 3.0, 2.6),
    font_size=8.3,
)

h2_add("11.4 变更管理")
for item in [
    "需求变更必须更新本 PRD 的需求编号、优先级、验收标准和修订记录。",
    "P0 范围变更需要产品、研发、测试共同确认；必要时顺延版本。",
    "发布版本采用语义化版本：功能 / 交互变化提升 minor；修复与兼容提升 patch。",
    "跨平台共用页面时，Android / iOS / PWA 的页面资源应保持同一份并分别验证平台壳。",
]:
    bullet_add(item)

h2_add("11.5 后续路线图（未承诺）")
add_table(
    ["优先级", "候选能力", "价值"],
    [
        ["P2", "历史详情 / 导出 / 备份", "让用户查看和迁移每日明细，降低本地数据丢失风险"],
        ["P2", "按性别 / 体脂等细化 BMR", "提升基础代谢估算准确度"],
        ["P2", "多成员 / 多家庭配置", "支持家庭场景，但会增加复杂度"],
        ["P2", "可选云同步", "跨设备使用；需明确隐私与账号方案"],
        ["P2", "App Store / TestFlight 正式分发", "降低安装门槛；需 Apple Developer 与审核"],
    ],
    widths=(0.75, 2.2, 3.55),
    font_size=8.3,
)



# ==========================================================================
# 12 RISKS
# ==========================================================================
h1_add("12. 风险与开放问题", new_page=False)

h2_add("12.1 风险")
add_table(
    ["风险", "影响", "缓解", "等级"],
    [
        ["iOS 无 Mac / 无法本地签名", "无法直接产出 IPA，影响原生安装", "提供 Xcode 工程、GitHub Actions 未签名 IPA 流程、Sideloadly 说明；或 TestFlight", "高"],
        ["本地数据丢失", "清理应用 / 站点数据后历史与资料不可恢复", "明确提示；未来提供导出 / 备份", "中"],
        ["估算偏差", "用户把估算当真实电费 / 碳排", "说明页写清口径；文案使用「估算 / 等价」", "中"],
        ["PWA 存储被系统回收", "长期未打开可能丢失站点数据", "说明本地存储属性；未来备份", "中"],
        ["容量 / 功率误改", "长期配置被改变，影响后续记录", "配置锁开关；换日保留", "低"],
        ["时区 / 系统时间变化", "跨日判断偏移", "本地自然日；启动 / 前台 / 定时检查", "低"],
        ["签名密钥管理", "公开分发使用本地密钥有风险", "公开上架前更换自己的 keystore / Apple 证书", "中"],
        ["可访问性不足", "小触控目标 / 读屏支持有限", "ARIA、焦点、减少动效；持续改进", "中"],
    ],
    widths=(1.35, 1.5, 2.8, 0.65),
    font_size=8.0,
)

h2_add("12.2 开放问题")
add_table(
    ["问题", "当前处理", "需要决定"],
    [
        ["配置锁默认开还是关？", "默认关，用户按需开启", "是否改为默认开，以更强保护配置"],
        ["BMR 是否区分性别？", "当前男女平均常数", "是否加入性别字段，提升估算准确度"],
        ["历史是否需要明细 / 导出？", "当前仅保存每日总量", "是否增加日详情、CSV / JSON 导出"],
        ["是否需要云同步 / 多设备？", "当前无", "是否引入账号与隐私方案"],
        ["iOS 正式分发方式？", "Xcode 源码 + Windows 自签路线", "走 TestFlight、App Store 还是长期侧载"],
        ["示例重置是否应保留锁定的容量 / 功率？", "重置恢复示例值，配置锁开关保留", "是否把配置值也保护起来"],
    ],
    widths=(2.0, 2.1, 2.3),
    font_size=8.1,
)



# ==========================================================================
# 13 APPENDIX
# ==========================================================================
h1_add("13. 附录", new_page=True)

h2_add("附录 A · 五档评价文案")
add_table(
    ["档位", "标签", "文案"],
    [
        ["1", "省电模式", "点几块炭够你活一天，牛逼"],
        ["2", "节能模式", "控制全球变暖有你一份功劳"],
        ["3", "均衡模式", "试着把空调固定在26度，指不定会少花几块钱"],
        ["4", "性能模式", "耗能有点高，是不是需要注意下账单..."],
        ["5", "高耗能模式", "你知道你带得动几张GPU吗...不告诉你！"],
    ],
    widths=(0.5, 1.2, 4.8),
    font_size=8.5,
)

h2_add("附录 B · 默认配置")
add_table(
    ["项目", "默认值"],
    [
        ["示例资料", "30 岁 / 170 cm / 68 kg / BMR 1514.5 kcal/天"],
        ["步数 / 活动强度", "8,000 步 / 4.20 MET"],
        ["默认设备", "手机 5000 mAh × 1；真无线耳机 500 mAh × 1；平板 8000 mAh × 0.75；台式 300 W × 2 h"],
        ["默认可选设备", "笔记本 60 Wh × 1；移动电源 10000 mAh × 0.5；头戴 800 mAh × 0.75；运动相机 1800 mAh × 0.5；相机 2400 mAh × 0.25；拍立得 1200 mAh × 0.25"],
        ["默认电器", "冰箱 80 W × 24 h；其余电器勾选未开、时长 0"],
        ["默认出行", "地铁 30 min；电动车 30 min；其余 0"],
        ["默认总账", "自体 2.073 + 设备 0.650 + 周边 3.842 = 6.565 kWh / 273.55 W；周边评价：省电模式"],
        ["归零基线", "步数 0、MET 1.3、无设备 / 电器 / 出行时约 2.45 kWh"],
    ],
    widths=(1.25, 5.25),
    font_size=8.2,
)

h2_add("附录 C · 术语表")
add_table(
    ["术语", "定义"],
    [
        ["自体", "身体基础代谢 + 步数活动产生的能量，按食物代谢折算"],
        ["设备", "手机、耳机、电脑等电池 / 功率设备"],
        ["周边", "WiFi、基站、云服务器固定项 + 家用电器 + 出行"],
        ["周边功耗", "固定项 + 电器 + 出行，评价所依据的口径"],
        ["静息功率", "基础代谢折算到 24 小时的平均功率"],
        ["活动功率", "静息功率 × MET"],
        ["单卡三态", "未勾选 / 已勾选 / 已固定 三种状态循环"],
        ["配置锁", "只冻结容量、功率等配置字段的总开关"],
        ["跨日归零", "把昨日用量归档，并清零今日可调用量"],
        ["PWA", "可添加到主屏幕、带 service worker 的网页应用"],
    ],
    widths=(1.25, 5.25),
    font_size=8.3,
)

h2_add("附录 D · 界面参考")
picture(ASSETS / "settings-and-fixed.png", 4.9, "图 2 · 设置中的数据保护开关（左）与单卡固定状态（右）")
small_add("截图来自 v2.1.2 的 390×844 视口；暖白主题、容量 / 功率设置、单卡固定为最终视觉基线。")

doc.save(str(OUT))
print("saved", OUT)
