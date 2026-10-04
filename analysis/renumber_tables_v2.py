"""Renumber the tables to close the gaps, guard against the right invariant.

The invariant is not "the citation count is unchanged", which was the wrong check twice over -- it
counted captions as citations, and after renumbering it looked for labels that no longer exist. The
invariant that actually holds and actually matters is: THE TOTAL NUMBER OF "Table" TOKENS DOES NOT
CHANGE. Every one of them, caption or citation, refers to the same table, so a renumbering is a
pure relabelling and cannot create or destroy a reference.

Sequence to close: 1,2,3,4,6,8,9,12,13,14,15 -> 1..11, with
    6->5  8->6  9->7  12->8  13->9  14->10  15->11
applied highest-first so a new label is never re-substituted. Appendix tables (B1, C1-C9) are
untouched and their references must also be untouched.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

RENUM = [('15', '11'), ('14', '10'), ('13', '9'), ('12', '8'),
         ('9', '7'), ('8', '6'), ('6', '5')]

FIG_TITLES = [
    ("The paper's framework in one panel.", 'Figure 1.'),
    ('The three failure modes, shown on the same retrieval setting.', 'Figure 2.'),
    ('Responsiveness control.', 'Figure 3.'),
    ('R1-constraint inertness.', 'Figure 4.'),
    ('Text-attack susceptibility at base and large scale', 'Figure 5.'),
    ('The aggregate statistic against the per-group shifts', 'Figure 6.'),
    ('The instrument, not the corpus, was the reason', 'Figure 7.'),
]


def tokens(text):
    """Total number of 'Table' tokens: the quantity a relabelling must preserve."""
    return len(re.findall(r'Table', text))


def appendix_tokens(text):
    """Appendix-table references, which must be byte-identical afterwards."""
    return sorted(re.findall(r'Table\s?([BC]\d+)', text))


def main():
    md = io.open(MD, encoding='utf-8').read()
    tex = io.open(TEX, encoding='utf-8').read()

    md0, tex0 = tokens(md), tokens(tex)
    md_app0, tex_app0 = appendix_tokens(md), appendix_tokens(tex)

    for old, new in RENUM:
        md = re.sub(r'Table %s(?!\d)' % old, 'Table %s' % new, md)
        tex = re.sub(r'Table([~ ])%s(?!\d)' % old, r'Table\g<1>%s' % new, tex)

    md1, tex1 = tokens(md), tokens(tex)
    print('Table tokens  markdown: %d -> %d' % (md0, md1))
    print('Table tokens  tex     : %d -> %d' % (tex0, tex1))
    print('appendix refs markdown unchanged: %s' % (appendix_tokens(md) == md_app0))
    print('appendix refs tex      unchanged: %s' % (appendix_tokens(tex) == tex_app0))
    if (md0, tex0) != (md1, tex1) or appendix_tokens(md) != md_app0 \
            or appendix_tokens(tex) != tex_app0:
        print('ABORT: the relabelling changed something it should not have')
        return 1

    seq = sorted(int(c) for c in re.findall(r'\*\*Table (\d+)\.', md))
    print('caption sequence now : %s' % seq)
    if seq != list(range(1, len(seq) + 1)):
        print('ABORT: sequence still has gaps')
        return 1

    added = 0
    for start, label in FIG_TITLES:
        pat = r'(!\[)' + re.escape(start)
        if re.search(pat, md) and label not in md:
            md = re.sub(pat, lambda m, lab=label, st=start: m.group(1) + lab + ' ' + st,
                        md, count=1)
            added += 1
    print('figure captions numbered: %d of 7' % added)
    if added != 7:
        print('ABORT: figure numbering incomplete')
        return 1

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(md)
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(tex)

    md2 = io.open(MD, encoding='utf-8').read()
    print()
    print('markdown tables : %s' % re.findall(r'\*\*Table ([A-Z]?\d+)\.', md2))
    print('markdown figures: %s' % re.findall(r'!\[Figure (\d)\.', md2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
