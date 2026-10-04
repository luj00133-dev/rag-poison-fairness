"""Reapply the tex edits that a killed process's stale write reverted.

An earlier porting script used a regex with nested quantifiers that backtracked catastrophically
on a long line, burning CPU without matching. It was killed, but its in-memory copy of the file
was flushed on the way out and reverted the four edits that had already been applied. This
reapplies them using plain string operations only.

The lesson is recorded rather than just fixed: when killing a process that holds a whole file in
memory and writes it at the end, assume it may write on exit, and re-verify the file afterwards
instead of trusting the earlier confirmation.
"""
import io
import os

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

STR_EDITS = [
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

    anchor = '\\section{Why Distribution-Level Defense Has a Limit}'
    if 'property of the back-end}' in s:
        print('5.9 already present')
    elif anchor in s:
        s = s.replace(anchor, SECTION + anchor, 1)
        print('inserted tex section 5.9')
    else:
        print('ANCHOR FAIL for 5.9')
        return 1

    for old, new in STR_EDITS:
        n = s.count(old)
        print('%-56s %d' % (old[:56], n))
        if n == 1:
            s = s.replace(old, new, 1)
        elif n == 0:
            print('    ^ NOT FOUND (may already be applied)')

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    s2 = io.open(TEX, encoding='utf-8').read()
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in s2:
            print('FAIL: missing %s' % needed)
            return 1
    print()
    print('structure intact')
    for label, ok in (('5.9 present', 'property of the back-end}' in s2),
                      ('8.1 renamed', 'When the aggregate is informative}' in s2),
                      ('3.4 renamed', 'invariances an adversary can impose}' in s2),
                      ('contrib 1 reframed', 'when adversarial fairness statistics are invariant' in s2),
                      ('universal claim gone',
                       'Every statistic that aggregates over group composition is blind' not in s2)):
        print('  %-24s %s' % (label, ok))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
