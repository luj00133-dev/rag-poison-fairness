"""Renumber tables via placeholders, so no relabelled value can be re-matched.

The previous attempt produced a caption sequence of 1,2,3,4,5,5,5,7,7,10,11: duplicates, meaning
some captions were relabelled twice. The cause is that substitutions run in sequence over the same
text, so a value produced by one step is visible to the next -- "Table 8 -> Table 6" is fine until
the "Table 6 -> Table 5" step then renames the table that was just renamed.

The fix is to make the intermediate values unmatchable. Every target number is first replaced by a
unique placeholder token that contains no digits and cannot be matched by any other rule, and the
placeholders are resolved only after every rule has run.

The invariant stays the same and is checked: the total number of "Table" tokens must not change,
and appendix-table references must be byte-identical.
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


def relabel(text, sep):
    """Two-phase relabelling: old numbers -> placeholders -> new numbers.

    The separator is captured so the tex keeps its non-breaking space or plain space, and the
    markdown keeps its plain space. Using the whole match plus a placeholder means no rule can see
    a value another rule produced.
    """
    for i, (old, _new) in enumerate(RENUM):
        text = re.sub(r'(Table' + sep + r')' + old + r'(?!\d)',
                      lambda m, k=i: m.group(1) + '@@T%d@@' % k, text)
    for i, (_old, new) in enumerate(RENUM):
        text = text.replace('@@T%d@@' % i, new)
    return text


def tokens(text):
    return len(re.findall(r'Table', text))


def appendix_refs(text):
    return sorted(re.findall(r'Table\s?([BC]\d+)', text))


def main():
    md = io.open(MD, encoding='utf-8').read()
    tex = io.open(TEX, encoding='utf-8').read()

    before = (tokens(md), tokens(tex), appendix_refs(md), appendix_refs(tex))

    md = relabel(md, r' ')
    tex = relabel(tex, r'([~ ])')

    after = (tokens(md), tokens(tex), appendix_refs(md), appendix_refs(tex))
    print('Table tokens  md : %d -> %d' % (before[0], after[0]))
    print('Table tokens  tex: %d -> %d' % (before[1], after[1]))
    print('appendix md  unchanged: %s' % (before[2] == after[2]))
    print('appendix tex unchanged: %s' % (before[3] == after[3]))
    if before != after:
        print('ABORT: relabelling altered an invariant')
        return 1
    if '@@T' in md or '@@T' in tex:
        print('ABORT: unresolved placeholder left behind')
        return 1

    seq = sorted(int(c) for c in re.findall(r'\*\*Table (\d+)\.', md))
    print('caption sequence : %s' % seq)
    if seq != list(range(1, len(seq) + 1)):
        print('ABORT: sequence still has gaps or duplicates')
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
