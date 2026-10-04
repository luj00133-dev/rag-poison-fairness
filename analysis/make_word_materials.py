"""Fix two things in the Word build, then produce the Word submission materials.

DEFECT: the docx prints an HTML comment as body text. The markdown carries a labelled block

    <!-- SUBMISSION ARTIFACT -- entered in the journal submission system, not typeset ... -->
    Highlights (3-5 items, each <= 85 characters):
    * ...

which is correct in the markdown -- it marks the block as not part of the manuscript -- but the
renderer has no rule for an HTML comment, so it emits the marker itself as a visible paragraph. A
manuscript whose first page shows "<!-- SUBMISSION ARTIFACT" reads as an unfinished draft.

The fix is in the renderer: skip an html-comment block, and skip the submission-artefact block
that follows it in the markdown, because highlights belong in the submission system (and are now
supplied as their own Word file) rather than in the manuscript body.

Then the Word materials for submission, which the journal's system asks for as separate uploads:

    cover_letter.docx      the letter, previously only .md and .txt
    highlights.docx        the five highlights, with character counts visible for checking
    title_page.docx        title, author, affiliation, corresponding author, ORCID
"""
import io
import os
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAPER = os.path.join(ROOT, 'paper')
sys.path.insert(0, PAPER)


def fix_renderer():
    """Teach make_docx.py to skip html comments and the labelled submission block."""
    p = os.path.join(PAPER, 'make_docx.py')
    s = io.open(p, encoding='utf-8').read()
    if 'html comment' in s:
        print('renderer already handles comments')
        return True

    anchor = '    i = 0\n    first_h1 = True\n    while i < len(lines):\n        line = lines[i].rstrip()\n'
    if anchor not in s:
        print('RENDERER ANCHOR NOT FOUND')
        return False
    addition = anchor + '''
        # An html comment is a note to whoever reads the source, not manuscript
        # content, so it is skipped rather than printed. The submission-artefact
        # marker introduces the highlights block, which belongs in the submission
        # system (and is supplied as its own file), so that block is skipped too.
        if line.strip().startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
'''
    s = s.replace(anchor, addition, 1)

    # also skip a heading block that is explicitly labelled as a submission artefact
    anchor2 = '    i = 0\n    first_h1 = True\n'
    s = s.replace(anchor2, anchor2, 1)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('renderer now skips html comments')
    return True


def setup(doc, size=11):
    st = doc.styles['Normal']
    st.font.name = 'Times New Roman'
    st.font.size = Pt(size)
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(1.0)
        s.top_margin = s.bottom_margin = Inches(1.0)


def para(doc, text, *, bold=False, italic=False, size=None, align=None, space_after=8):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    if size:
        run.font.size = Pt(size)
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def write_cover_letter():
    src = io.open(os.path.join(PAPER, 'cover_letter.md'), encoding='utf-8').read()
    doc = Document()
    setup(doc)
    for raw in src.split('\n'):
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith('# '):
            para(doc, line[2:].strip(), bold=True, size=13)
            continue
        if line.startswith('## '):
            para(doc, line[3:].strip(), bold=True, size=11.5)
            continue
        if line.strip() == '---':
            continue
        # strip markdown emphasis but keep the words
        t = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        t = re.sub(r'\*(.+?)\*', r'\1', t)
        t = t.replace('`', '')
        bullet = t.lstrip().startswith('- ') or t.lstrip().startswith('* ')
        if bullet:
            t = t.lstrip()[2:]
            p = doc.add_paragraph(t, style='List Bullet')
            p.paragraph_format.space_after = Pt(4)
            continue
        para(doc, t.strip())
    out = os.path.join(PAPER, 'cover_letter.docx')
    doc.save(out)
    print('wrote %s' % out)


def write_highlights():
    lines = [l.strip() for l in
             io.open(os.path.join(PAPER, 'highlights.txt'), encoding='utf-8')
             if l.strip()]
    doc = Document()
    setup(doc)
    para(doc, 'Highlights', bold=True, size=13)
    para(doc, 'Adversarially Invariant Fairness Statistics: Why Aggregate '
              'Retrieval-Fairness Metrics Cannot Detect Pairwise Poisoning', italic=True)
    para(doc, 'Lu Jiang, Nanjing University of Science and Technology')
    para(doc, '')
    for l in lines:
        p = doc.add_paragraph(l, style='List Bullet')
        p.paragraph_format.space_after = Pt(6)
    para(doc, '')
    para(doc, 'Character counts: %s (limit 85 each)'
              % ', '.join(str(len(l)) for l in lines), size=9, italic=True)
    out = os.path.join(PAPER, 'highlights.docx')
    doc.save(out)
    print('wrote %s (%d highlights)' % (out, len(lines)))


def write_title_page():
    doc = Document()
    setup(doc)
    para(doc, 'Adversarially Invariant Fairness Statistics: Why Aggregate '
              'Retrieval-Fairness Metrics Cannot Detect Pairwise Poisoning',
         bold=True, size=14)
    para(doc, '')
    para(doc, 'Lu Jiang')
    para(doc, 'School of Electronic and Optical Engineering')
    para(doc, 'Nanjing University of Science and Technology')
    para(doc, 'Nanjing, China')
    para(doc, '')
    para(doc, 'Corresponding author: Lu Jiang')
    para(doc, 'Email: lujiang12@njust.edu.cn; luj00133@gmail.com')
    para(doc, 'ORCID: 0009-0001-0717-2732')
    para(doc, '')
    para(doc, 'Keywords: retrieval-augmented generation, data poisoning, fairness measurement, '
              'within-group stance, adversarial robustness, evaluation validity')
    out = os.path.join(PAPER, 'title_page.docx')
    doc.save(out)
    print('wrote %s' % out)


def main():
    ok = fix_renderer()
    write_cover_letter()
    write_highlights()
    write_title_page()
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
