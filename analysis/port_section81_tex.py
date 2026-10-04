"""Port section 8.1 and the claim correction into the LaTeX source.

Matches the markdown change. The tex wraps differently from the markdown and uses its own
conventions (\\subsection, ``...'', \\texttt, ---), so the block is written out again rather than
copied, and the inserted claim is matched on the tex's own line wrapping.
"""
import io
import os
import py_compile

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

SCOPE = r'''\subsection{Scope of the invariance}\label{scope-of-the-invariance}

The invariance results above are conditional, and the conditions are measurable, so they are stated here rather than left for a reader to infer. They also identify which settings the framework covers.

\textbf{The composition statistic is flat on the lexical retriever, and moves elsewhere.} Undefended composition drift on the controlled corpus, at the relocation levels where the label is partial:

\begin{center}
\begin{tabular}{lll}
\hline
back-end & attack & composition drift at partial relocation \\
\hline
\texttt{st} (GTE-base) & lexical & 0.0000 at every partial level \\
dense & lexical & 0.0000 at the lowest level, rising to 0.1750 at full relocation \\
BM25 & lexical, projected & 0.0000 at low relocation, rising to 0.2280 at full relocation \\
SPLADE & lexical, projected & 0.0000 at zero, 0.2000--0.4000 through the middle, 0.2250 at full \\
\hline
\end{tabular}
\end{center}

On \texttt{st} the injected set is compositionally balanced and stays so however much of it is retrieved, so the aggregate reads clean while the evidence moves --- the regime the framework describes. On the other back-ends the retrieved set relocates composition as well, and the aggregate moves with it, reaching 0.1750 on dense and 0.2 or above on the projected lexical back-ends. The dependence is not strictly monotone in the relocated fraction, which is itself a reason to measure the regime rather than assume it. The balanced pairwise construction is therefore a sufficient condition for the blindness and not a universal one, and the practical reading is: check which regime your retriever is in before treating a null aggregate as evidence of robustness.

\textbf{Subspace projection removes the passage text from the ranking decision.} Under \texttt{template\_plus\_projection} the relocated fraction was 1.000 for all 192 queries at every alignment setting we tried. Projection sets the ranking from document and query vectors, so the composition the composition statistics observe is fixed by the projection rather than by the passages. This bounds what any text-side defence or perturbation can achieve against that back-end, and it is the mechanism behind the saturation reported in §5.8.

\textbf{The per-group statistic is a batch average, and its power is bounded by batch count.} Every group-level rate in this paper averages binary stance decisions over the queries in a stratum. A single query contributes one draw, so the diagnostic is not a per-query test and should not be evaluated as one; we report it per stratum for this reason. The consequence is a power bound that does not yield to more queries of the same kind: on a corpus whose queries are instantiations of a small template set, raising the query count repeats the same texts, and we measured this rather than assuming it --- a regime that held 36 of 192 queries held 0 of 1,536 once the count was raised. Obtaining more power requires more independent strata or repeated audits over time, not a larger sample of the same queries.

\textbf{What this means for reporting.} The framework's three questions (§3.4) and the protocol above identify blindness in advance, but they identify it for a stated retriever and threat model. A robustness claim should say which of these regimes it was evaluated in, because a null result in the first regime is informative and a null result in the others is not.

'''

OLD_CLAIM = (r'R1 drift stays at or below the level legitimate retrieval variance produces; '
             r'two of three candidate R2 statistics are flat across the clean and fully '
             r'attacked conditions.')


def main():
    s = io.open(TEX, encoding='utf-8').read()
    anchor = '\\section{Conclusion}'
    if anchor not in s:
        print('ANCHOR FAIL')
        return 1
    if 'subsection{Scope of the invariance}' in s:
        print('scope subsection already present')
    else:
        s = s.replace(anchor, SCOPE + anchor, 1)
        print('inserted tex subsection Scope of the invariance')

    # the claim is wrapped in the tex; find it by its opening fragment and replace the sentence
    i = s.find('R1 drift stays at or below')
    if i >= 0:
        # the sentence ends at the semicolon before "two of three"
        j = s.find('two of three candidate R2 statistics are flat across the clean and fully', i)
        k = s.find('conditions.', j)
        if j > i and k > j:
            new = ('On the lexical retriever the composition statistic reads clean however much '
                   'of the injected set is retrieved; two of three candidate R2 statistics are '
                   'flat across the clean and fully attacked conditions; §8.1 states the '
                   'retrievers and attacks on which each part of this holds.')
            s = s[:i] + new + s[k + len('conditions.'):]
            print('corrected the claim in the tex')
    else:
        print('claim not found in tex (already corrected?)')

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    s2 = io.open(TEX, encoding='utf-8').read()
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in s2:
            print('FAIL: missing %s' % needed)
            return 1
    print()
    print('structure intact')
    print('stale claim gone      : %s' % ('legitimate retrieval variance' not in s2))
    print('scope subsection      : %s' % ('subsection{Scope of the invariance}' in s2))
    print('section 8.1 numbering : %s' % ('label{scope-of-the-invariance}' in s2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
