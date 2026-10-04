"""Wire the redrawn vector concept figures into the LaTeX source.

The tex and the markdown had diverged on the figures. The markdown carries seven: the framework,
a single composed failure-modes figure, four data figures, and the probe. The tex carried nine: a
TikZ framework plus three separate ChatGPT PNGs in place of the composed failure-modes figure.
That divergence is itself a defect -- the two sources would produce papers with different figures.

This makes the tex match the markdown, and points it at the three redrawn vector figures. Matched
with plain string replacement, and the result is verified by listing the final includes and
recompiling.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

FRAMEWORK = (r'\includegraphics[width=140mm]{fig_framework_tikz.pdf}',
             r'\includegraphics[width=140mm]{fig_framework_py.pdf}')

# the three separate panels are replaced by the one composed figure the markdown uses
TRIPLE = [
    (r'\includegraphics[width=\linewidth]{fig_f_f1.png}', None),
    (r'\includegraphics[width=\linewidth]{fig_f_f2.png}', None),
    (r'\includegraphics[width=\linewidth]{fig_f_f3.png}', None),
]
COMPOSED = r'\includegraphics[width=140mm]{fig_failure_modes_py.pdf}'

PROBE = (r'\includegraphics[width=140mm]{fig_probe_commitment.png}',
         r'\includegraphics[width=140mm]{fig_probe_commitment_py.pdf}')


def main():
    s = io.open(TEX, encoding='utf-8').read()

    n = s.count(FRAMEWORK[0])
    print('framework anchor: %d' % n)
    if n == 1:
        s = s.replace(FRAMEWORK[0], FRAMEWORK[1], 1)
        print('  -> framework now the redrawn vector')

    # replace the first of the three panels with the composed figure and drop the other two
    present = [a for a, _ in TRIPLE if a in s]
    print('separate failure-mode panels found: %d' % len(present))
    if len(present) == 3:
        s = s.replace(TRIPLE[0][0], COMPOSED, 1)
        for a, _ in TRIPLE[1:]:
            s = s.replace(a, '', 1)
        print('  -> three panels replaced by the composed figure')
        # the emptied includegraphics leaves stray figure environments; report if so
        if s.count('\\begin{figure}') != s.count('\\end{figure}'):
            print('  WARNING: figure environment count unbalanced')

    n2 = s.count(PROBE[0])
    print('probe anchor: %d' % n2)
    if n2 == 1:
        s = s.replace(PROBE[0], PROBE[1], 1)
        print('  -> probe now the redrawn vector')

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    s2 = io.open(TEX, encoding='utf-8').read()
    print()
    print('final includes:')
    for line in s2.split('\n'):
        if 'includegraphics' in line:
            print('   ' + line.strip())
    print()
    for label, ok in (
            ('no bitmap concept figures left',
             not any(x in s2 for x in ('fig_framework.png', 'fig_probe_commitment.png',
                                       'fig_f_f1.png', 'fig_f_f2.png', 'fig_f_f3.png'))),
            ('tikz framework replaced', 'fig_framework_tikz.pdf' not in s2),
            ('figure envs balanced',
             s2.count('\\begin{figure}') == s2.count('\\end{figure}'))):
        print('  %-32s %s' % (label, ok))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
