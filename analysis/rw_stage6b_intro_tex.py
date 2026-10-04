"""Port the last three introduction edits into the tex.

The markdown was updated in stage 2; these are the same three changes in the tex's own
LaTeX/citation conventions. Matched on the LaTeX form of each passage, verified by
re-reading the file afterwards.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

EDITS = [
    ('fell_into',
     r'\textbf{A second, subtler failure --- one we fell into ourselves.}',
     r'\textbf{A second failure, and it is a property of a metric class rather than of any one choice.}'),

    ('credible_clause',
     ' We report that second occurrence in full, because a measurement paper whose authors '
     'did not notice their own instance of the error would not be credible about anyone '
     "else's.",
     ' A metric that is dominated by a corpus constant reports that constant and not the '
     'attack.'),

    ('corrected_bullet',
     r'and the gap between groups is the wrong one --- a distinction we had to be corrected '
     r'by our own data to see.',
     r'and the gap between groups is the wrong one.'),

    ('provenance_bullet',
     r'\textbf{A provenance signal is necessary, and we report an exploratory candidate.}',
     r'\textbf{Aggregates are not the only option: an individual-level signal separates '
     r'clean from adversarial passages.}'),
]


def main():
    s = io.open(TEX, encoding='utf-8').read()
    for name, old, new in EDITS:
        n = s.count(old)
        print('%-20s %d match(es)' % (name, n))
        if n == 1:
            s = s.replace(old, new, 1)
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    s2 = io.open(TEX, encoding='utf-8').read()
    print()
    for probe in ['fell into ourselves', 'had to be corrected by our own data',
                  'not be credible about anyone', 'exploratory candidate',
                  'we state plainly']:
        print('  removed %-42s : %s' % (probe, probe not in s2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
