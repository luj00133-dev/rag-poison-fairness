"""Repair the failure-modes figure block in the tex.

The previous replacement put the composed figure inside a 0.315-width subfigure and left two
empty subfigures behind, which is three compile errors and a figure that would print a third of a
page wide. The composed figure already contains F1, F2 and F3 as three panels, so the subfigure
wrappers are not needed at all: the block becomes one figure with the existing caption, which
already describes (a)(b)(c) and names the sections holding the measurements.

Reconstructed from the file's own markers rather than by pattern, and the result is checked by
counting subfigure environments and by recompiling.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

NEW = (
    '\\begin{figure*}[t]\n'
    '\\centering\n'
    '\\includegraphics[width=140mm]{fig_failure_modes_py.pdf}\n'
    '\\caption{The three failure modes, shown on the same retrieval setting. '
    '\\textbf{(a) F1:} the injection contributes equally to every group, so a counting or '
    'composition statistic returns its clean value --- the attack is invisible to it (measured '
    'in \\S5.1 and \\S5.2). \\textbf{(b) F2:} the statistic is anchored to a reference the attack '
    'does not move, so it reports the component that varies with the query rather than the one '
    'that varies with the attack (\\texttt{stance\\_div} and \\texttt{stance\\_onesided}, '
    '\\S3.2 and \\S5.1). \\textbf{(c) F3:} all groups are relocated together, so any difference '
    'between groups is unchanged however far the groups move (\\texttt{stance\\_gap} and its '
    'generation-layer twin, \\S5.1 and \\S5.7). The three panels are conceptual and carry no '
    'measured values; the corresponding measurements are in the sections named above.}\n'
    '\\label{fig:failure-modes}\n'
    '\\end{figure*}\n'
)


def main():
    s = io.open(TEX, encoding='utf-8').read()
    i = s.find('\\begin{figure*}')
    # find the figure* block that contains the composed failure-modes include
    target = None
    for m in re.finditer(r'\\begin\{figure\*\}', s):
        j = s.find('\\end{figure*}', m.start())
        if 'fig_failure_modes_py.pdf' in s[m.start():j]:
            target = (m.start(), j + len('\\end{figure*}'))
            break
    if not target:
        print('ANCHOR FAIL: no figure* block holds the composed figure')
        return 1

    a, b = target
    print('replacing block of %d chars' % (b - a))
    s = s[:a] + NEW + s[b:]
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    s2 = io.open(TEX, encoding='utf-8').read()
    checks = [
        ('no subfigure left', 'subfigure' not in s2),
        ('figure envs balanced',
         s2.count('\\begin{figure}') == s2.count('\\end{figure}')
         and s2.count('\\begin{figure*}') == s2.count('\\end{figure*}')),
        ('composed figure included once', s2.count('fig_failure_modes_py.pdf') == 1),
        ('no dead bitmap includes',
         not any(x in s2 for x in ('fig_f_f1.png', 'fig_f_f2.png', 'fig_f_f3.png',
                                   'fig_framework_tikz.pdf', 'fig_probe_commitment.png'))),
    ]
    for label, ok in checks:
        print('  %-32s %s' % (label, ok))
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
