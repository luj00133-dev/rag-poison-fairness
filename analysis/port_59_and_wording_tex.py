"""Port section 5.9 and the wording corrections into the LaTeX source.

Matches the markdown change. The tex wraps differently and uses its own conventions, so the new
subsection is written out again. The wording corrections are matched on stable fragments of the
tex's own text.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

SECTION = r'''\subsection{The composition statistic's validity is a property of the back-end}\label{the-composition-statistics-validity-is-a-property-of-the-back-end}

The results so far establish the invariance and its cause. This section establishes where it holds, which turns out to vary by retrieval back-end in a way that is measurable and that a practitioner can check before trusting a null aggregate.

\textbf{Design.} The same balanced pairwise injection is applied to four retrieval back-ends under identical conditions, and the composition statistic is read as a function of how much of the retrieved set is adversarial. If composition drifts nowhere, the invariance is a property of the statistic. If it drifts on some back-ends and not others, the invariance is a property of the back-end, and that distinction decides whether a clean aggregate means anything.

\textbf{Result.} Undefended composition drift, by relocated fraction:

\begin{center}
\begin{tabular}{lll}
\hline
back-end & attack & composition drift \\
\hline
\texttt{st} (GTE-base) & lexical & \textbf{0.0000 at every partial level}, 0.2400 only at full relocation \\
dense & lexical & 0.0000 at the lowest level, rising to \textbf{0.1750} at full relocation \\
BM25 & lexical, projected & 0.0000 at low relocation, rising to \textbf{0.2280} at full relocation \\
SPLADE & lexical, projected & 0.0000 at zero, 0.2000--0.4000 through the middle, \textbf{0.2250} at full \\
\hline
\end{tabular}
\end{center}

On \texttt{st} the injected set is compositionally balanced and stays balanced however much of it is retrieved, so the composition statistic reads clean while the evidence moves: the regime in which the aggregate is uninformative. On the other three back-ends the retrieved set relocates composition as well and the statistic moves with it, so a clean reading there would carry information.

\textbf{The dependence is not a monotone function of the relocated fraction.} BM25 reads 0.0000 at a relocated fraction of 0.8 while reading 0.2000 at 0.6, and SPLADE peaks in the middle (0.4000 at 0.6) and falls back (0.2250 at 1.0). The relation between how much adversarial evidence is present and how much composition moves therefore cannot be summarised by a single slope, which is the practical reason to measure the regime rather than extrapolate to it.

\textbf{Why this is a result and not a caveat.} The balanced pairwise construction is a sufficient condition for the invariance, not a universal one. Stated that way the finding is actionable: the three-question test of §3.4 predicts whether a candidate statistic is invariant \emph{for a stated back-end and threat model}, and this section supplies the measurement that tells a practitioner which regime they are in. A paper reporting a null aggregate cannot interpret it without this, and the table is the check.

'''

EDITS = [
    ('\\textbf{A framework for why adversarial fairness statistics fail.}',
     '\\textbf{A framework for when adversarial fairness statistics are invariant.} The form is '
     'universal; the invariance is conditional, and checkable in advance.'),
    ('\\subsection{One form for every candidate metric, and three ways it loses the signal}',
     '\\subsection{One form for every candidate metric, and three invariances an adversary can impose}'),
    ('\\subsection{Scope of the invariance}',
     '\\subsection{When the aggregate is informative}'),
]


def main():
    s = io.open(TEX, encoding='utf-8').read()

    # 1. insert 5.9 at the end of the results chapter, i.e. before section 6
    anchor = '\\section{Why Distribution-Level Defense Has a Limit}'
    if anchor not in s:
        print('ANCHOR FAIL: section 6 not found')
        return 1
    if 'property of the back-end}' in s:
        print('5.9 already present')
    else:
        s = s.replace(anchor, SECTION + anchor, 1)
        print('inserted tex section 5.9')

    # 2. wording corrections
    for old, new in EDITS:
        n = s.count(old)
        print('%-58s %d' % (old[:58], n))
        if n == 1:
            s = s.replace(old, new, 1)

    # 3. the universal blindness claim, matched across the tex's own wrapping
    m = re.search(r'Every statistic that aggregates over group composition is blind to this\.'
                  r'(?:\s+[^\n]*)*?returns success\.', s)
    if m:
        new = ('Every candidate metric has that form; whether it reads clean depends on whether '
               'the injection balances the terms it aggregates. That is a property of the '
               'back-end rather than of the metric, and §5.9 measures it across four of them.')
        s = s[:m.start()] + new + s[m.end():]
        print('tex: universal blindness claim corrected')
    else:
        print('tex: universal blindness claim NOT FOUND')

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    s2 = io.open(TEX, encoding='utf-8').read()
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in s2:
            print('FAIL: missing %s' % needed)
            return 1
    print()
    print('structure intact')
    print('5.9 present              : %s' % ('property of the back-end}' in s2))
    print('8.1 renamed              : %s' % ('When the aggregate is informative}' in s2))
    print('3.4 renamed              : %s' % ('invariances an adversary can impose}' in s2))
    print('universal claim gone     : %s'
          % ('Every statistic that aggregates over group composition is blind' not in s2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
