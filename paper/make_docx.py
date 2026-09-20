"""
Render the fission report and the manuscript to Word (.docx).

Formatting follows the spec in references/fission-report-template.md:
  A4, margins 2.54cm top/bottom and 2.0cm left/right
  headings  Microsoft YaHei, bold
  body      SimSun 11pt, 1.5 line spacing
  warning   yellow highlight #FFF3CD
  routing   green #1E7A34

Two outputs:
  R2维度混淆_论文灌水科研创新点裂变报告.docx   -- the fission plan
  manuscript_R1R2_v1.docx                      -- the paper

Run: python paper/make_docx.py
"""

from __future__ import annotations

import os
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)

CJK_BODY = "SimSun"
CJK_HEAD = "Microsoft YaHei"
LATIN = "Times New Roman"
GREEN = RGBColor(0x1E, 0x7A, 0x34)
YELLOW = "FFF3CD"
LIGHT_BLUE = "DCE6F1"


def set_font(run, *, cjk=CJK_BODY, latin=LATIN, size=None, bold=None,
             color=None):
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:ascii"), latin)
    rf.set(qn("w:hAnsi"), latin)
    rf.set(qn("w:eastAsia"), cjk)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def shade(el, fill):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), fill)
    el.append(sh)


def setup(doc):
    for s in doc.sections:
        s.page_height = Cm(29.7)
        s.page_width = Cm(21.0)
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(2.0)
        s.right_margin = Cm(2.0)
    st = doc.styles["Normal"]
    st.font.name = LATIN
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), CJK_BODY)
    pf = st.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(4)


INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)")


def add_rich(par, text, size=11):
    """Render **bold**, *italic* and `code` inline."""
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = par.add_run(part[2:-2]); set_font(r, size=size, bold=True)
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            r = par.add_run(part[1:-1])
            set_font(r, cjk="Consolas", latin="Consolas", size=size - 0.5)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); set_font(r, size=size); r.font.italic = True
        else:
            r = par.add_run(part); set_font(r, size=size)


def heading(doc, text, level):
    p = doc.add_paragraph()
    if level == 0:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text); set_font(r, cjk=CJK_HEAD, size=20, bold=True)
        p.paragraph_format.space_after = Pt(14)
    elif level == 1:
        r = p.add_run(text); set_font(r, cjk=CJK_HEAD, size=14, bold=True)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
    elif level == 2:
        r = p.add_run(text); set_font(r, cjk=CJK_HEAD, size=13, bold=True)
        shade(p._p.get_or_add_pPr(), LIGHT_BLUE)
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
    else:
        r = p.add_run(text); set_font(r, cjk=CJK_HEAD, size=11.5, bold=True)
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(3)
    return p


def table(doc, rows):
    if not rows:
        return
    ncol = max(len(r) for r in rows)
    t = doc.add_table(rows=0, cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j in range(ncol):
            txt = row[j] if j < len(row) else ""
            cp = cells[j].paragraphs[0]
            cp.paragraph_format.line_spacing = 1.0
            cp.paragraph_format.space_after = Pt(0)
            add_rich(cp, txt, size=9.5)
            if i == 0:
                shade(cells[j]._tc.get_or_add_tcPr(), LIGHT_BLUE)
                for r in cp.runs:
                    r.font.bold = True
    doc.add_paragraph()


def render_markdown(md_path, docx_path, title, subtitle=None):
    with open(md_path, "r", encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    doc = Document()
    setup(doc)

    i = 0
    first_h1 = True
    while i < len(lines):
        line = lines[i].rstrip()

        # tables
        if line.startswith("|") and i + 1 < len(lines) and \
           re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            rows = []
            hdr = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(hdr)
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            table(doc, rows)
            continue

        if line.startswith("#"):
            m = re.match(r"^(#+)\s*(.*)$", line)
            lvl = len(m.group(1))
            txt = m.group(2)
            if lvl == 1 and first_h1:
                heading(doc, title, 0)
                if subtitle:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    r = p.add_run(subtitle)
                    set_font(r, cjk=CJK_HEAD, size=10.5, color=RGBColor(0x60, 0x60, 0x60))
                first_h1 = False
                i += 1
                continue
            heading(doc, txt, min(lvl - 1, 3) if not first_h1 else lvl)
            i += 1
            continue

        if line.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            shade(p._p.get_or_add_pPr(), YELLOW)
            add_rich(p, line[2:], size=10.5)
            i += 1
            continue

        if line.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            for b in buf:
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.left_indent = Cm(0.5)
                r = p.add_run(b if b else " ")
                set_font(r, cjk="Consolas", latin="Consolas", size=9)
            continue

        if re.match(r"^\s*[-*]\s+", line):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.line_spacing = 1.5
            add_rich(p, re.sub(r"^\s*[-*]\s+", "", line))
            i += 1
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.line_spacing = 1.5
            add_rich(p, re.sub(r"^\s*\d+\.\s+", "", line))
            i += 1
            continue

        if line.strip() in ("---", "***", ""):
            i += 1
            continue

        p = doc.add_paragraph()
        add_rich(p, line)
        i += 1

    doc.save(docx_path)
    return docx_path


def main():
    out = []
    out.append(render_markdown(
        os.path.join(HERE, "R2维度混淆_论文灌水科研创新点裂变报告.md"),
        os.path.join(PROJ, "R2维度混淆_论文灌水科研创新点裂变报告.docx"),
        "论文灌水科研创新点裂变报告",
        "母体：RAG 公平性防御的维度混淆（R1/R2） · 目标 1→4 篇",
    ))
    out.append(render_markdown(
        os.path.join(HERE, "manuscript_R1R2_v1.md"),
        os.path.join(HERE, "manuscript_R1R2_v1.docx"),
        "Two Dimensions of Retrieval Fairness",
        "Why Group-Proportion Constraints Cannot Defend RAG Against Pairwise Poisoning",
    ))
    out.append(render_markdown(
        os.path.join(HERE, "manuscript_B_adaptive_v1.md"),
        os.path.join(HERE, "manuscript_B_adaptive_v1.docx"),
        "The Fragility of Fair Retrieval Under an Informed Attacker",
        "Why Randomized and Composition-Constrained RAG Defenses Do Not Survive Adaptation",
    ))
    for p in out:
        print(f"wrote {p}  ({os.path.getsize(p):,} bytes)")


if __name__ == "__main__":
    main()
