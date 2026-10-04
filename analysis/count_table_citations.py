"""Count how often each table number is cited, before any renumbering.

The renumbering is only safe if every occurrence of a table number in the text is a reference to
that table. Counting first means the replacement can be verified: the total number of table
citations must be unchanged, and each number's count must move with its caption.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

BODY = ['1', '2', '3', '4', '6', '8', '9', '12', '13', '14', '15']


def main():
    md = io.open(MD, encoding='utf-8').read()
    print('%-8s %-10s %s' % ('table', 'as caption', 'times cited in text'))
    total = 0
    for n in BODY:
        cap = len(re.findall(r'\*\*Table %s\.' % n, md))
        # a citation is "Table N" not followed by a '.' immediately (which marks the caption)
        cites = len(re.findall(r'Table %s(?!\.)' % n, md))
        total += cites
        print('  %-6s %-10d %d' % (n, cap, cites))
    print()
    print('total in-text table citations: %d' % total)

    # is any bare number at risk of being caught by a replace? report the neighbourhood of each
    print()
    print('word-boundary check: any "Table N" occurrence immediately followed by a digit?')
    risky = re.findall(r'Table \d\d+', md)
    print('   %s' % (risky or 'none'))

    # the same count for the tex, since it must be renumbered too
    tex = io.open(TEX, encoding='utf-8').read()
    print()
    print('tex in-text citations:')
    for n in BODY:
        c = len(re.findall(r'Table[~ ]%s(?!\d)' % n, tex))
        print('  Table %-4s %d' % (n, c))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
