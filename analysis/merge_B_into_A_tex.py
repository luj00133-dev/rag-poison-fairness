"""Port the merged section into the LaTeX source, with natbib citations and a longtable.

The markdown and the tex carry the same prose but different citation machinery: markdown is
numeric internally, the tex is natbib author-date. So the section is written out twice from
one source of truth here, and the two new references are added to the tex bibliography as
author-date entries with proper \\bibitem[Label]{key} labels -- without a label, natbib
falls back to numeric and prints "[?]", which is the failure this paper already hit once.

Table 15 (the six-back-end sweep) is emitted as a longtable in the same shape as the other
tables in the file, with \\endfirsthead/\\endhead, because a longtable without them treats
its data rows as footer material and prints nothing -- the Table 12 defect.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

ANCHOR = '\\subsection{Generation-stage propagation: does the retrieval skew reach the output?}'

HEADERS = ['Back-end', 'representation', r'\(\lambda=0\)', r'\(\lambda=0.25\)',
           r'\(\lambda=0.5\)', r'\(\lambda=1\)', r'\(\lambda=2\)', r'\(\lambda=4\)',
           r'\texttt{usage} at \(\lambda=1\)']

ROWS = [
    ['hash-dense (own)', 'dense, hashed', '0.250', '0.562', '0.812', '0.938', '1.000', '1.000', '0.945'],
    [r'\textbf{GTE-base}', 'dense semantic', r'\textbf{0.000}', r'\textbf{1.000}', '1.000', '1.000', '1.000', '1.000', '0.978'],
    [r'\textbf{E5-base-v2}', 'dense semantic', r'\textbf{0.000}', r'\textbf{1.000}', '1.000', '1.000', '1.000', '1.000', '0.971'],
    [r'\textbf{Contriever}', 'dense semantic', r'\textbf{0.000}', '0.625', '1.000', '1.000', '1.000', '1.000', '0.943'],
    [r'\textbf{SPLADE} (distil)', 'sparse, learned', '0.188', '0.500', '0.812', '1.000', '1.000', '1.000', '0.954'],
    [r'\textbf{SPLADE large}', 'sparse, learned', r'\textbf{0.000}', '0.500', '0.750', '0.938', '1.000', '1.000', '0.952'],
]

NEW_REFS = [
    ('Carlini et al.(2019)', 'carlini2019',
     'Carlini, N., Athalye, A., Papernot, N., Brendel, W., Rauber, J., Tsipras, D., '
     'Goodfellow, I., \\& Madry, A. (2019). On evaluating adversarial robustness. '
     'arXiv preprint arXiv:1902.06705.'),
    ('Tramer et al.(2020)', 'tramer2020',
     'Tramer, F., Carlini, N., Brendel, W., \\& Madry, A. (2020). On adaptive attacks to '
     'adversarial example defenses. In Advances in Neural Information Processing Systems.'),
]


def longtable():
    n = len(HEADERS)
    frac = ' * \\real{%.4f}' % (1.0 / n)

    def colspec():
        return '\n'.join(
            '  >{\\raggedright\\arraybackslash}p{(\\linewidth - %d\\tabcolsep)%s}'
            % (2 * (n - 1), frac) for _ in range(n))

    def head():
        cells = ['\\begin{minipage}[b]{\\linewidth}\\raggedright\n%s\n\\end{minipage}' % h
                 for h in HEADERS]
        return ' & '.join(cells) + r' \\'

    out = [r'{\def\LTcaptype{none} % do not increment counter',
           r'\begin{longtable}[]{@{}', colspec() + '@{}}',
           r'\toprule\noalign{}', head(), r'\midrule\noalign{}',
           r'\endfirsthead',
           r'\toprule\noalign{}', head(), r'\midrule\noalign{}',
           r'\endhead',
           r'\bottomrule\noalign{}',
           r'\endlastfoot']
    for r in ROWS:
        out.append(' & '.join(r) + r' \\')
    out.append(r'\end{longtable}')
    out.append('}')
    return '\n'.join(out)


SECTION = r'''\subsection{The collapse is not an artefact of one retriever}\label{the-collapse-is-not-an-artefact-of-one-retriever}

The sweep above uses our own feature-hashing dense retriever. Because the \emph{shape} of the collapse --- not merely its endpoint --- could depend on the encoder, we repeated it on four further back-ends: \textbf{GTE-base} (the encoder used by the closest prior work on fairness-aware retrieval optimisation \citeyearpar{zhao2026}), \textbf{E5-base-v2} (used by the RAG fairness evaluations above), \textbf{Contriever}, and \textbf{SPLADE}, a learned \emph{sparse} retriever. SPLADE is what makes the comparison diagnostic: it is a trained neural encoder, like GTE and E5, but its representation is sparse, like BM25's.

\textbf{Table 15.} \texttt{poison@k} under the adaptive attacker for off-manifold filtering, by back-end. Six back-ends; \texttt{usage} (the attacker's semantic fidelity) in the last column.

__LONGTABLE__

The picture is not the one we expected when we added these back-ends, and it took all six to see why. Four of the five pretrained encoders (GTE-base, E5-base-v2, Contriever and SPLADE-large) begin at \textbf{exactly zero} adversarial inclusion against the static attacker and are effectively defeated after a single perturbation step. But ``one step'' means a \emph{complete} failure immediately for GTE-base and E5-base-v2 (\(0.000 \rightarrow 1.000\)), whereas Contriever (\(0.000 \rightarrow 0.625 \rightarrow 1.000\)) and both SPLADE sizes climb gradually and resemble our own hashed retriever (\(0.188 / 0.500 / 0.812\) and \(0.000 / 0.500 / 0.750\) against \(0.250 / 0.562 / 0.812\)). Scaling SPLADE up even \emph{improves} the defense's static position (\(0.188 \rightarrow 0.000\) at \(\lambda = 0\)) while leaving the collapse rate unchanged. Neither ``pretrained versus hashed'' nor ``dense versus sparse'' describes the collapse on its own.

\textbf{Finding 12.} Three claims are stable across all six back-ends and are what this finding rests on. First, \textbf{the static advantage is largest on the pretrained encoders}: all five begin below our hashed retriever's 0.250, and four begin at 0.000 --- the reverse of the concern that motivated the experiment, and awkward for the compared literature, because the static numbers one would use to select a defense are most optimistic precisely on the back-ends that literature uses. Second, \textbf{no defense retains any measurable benefit beyond \(\lambda = 1\)} on any of the six, and on four of them none survives \(\lambda = 0.25\). Third, \textbf{the attacker pays essentially nothing}: \texttt{usage} is at least 0.943 at \(\lambda = 1\) on every back-end, so the injected material is over 94\% semantically intact at the point where the defenses have lost most or all of their advantage.

The honest statement about the \emph{shape} of the collapse is therefore weaker than we first wrote: the abruptness varies by encoder in a way we cannot reduce to a single property, and an earlier framing of ours --- that the collapse is steeper on a ``real'' encoder --- was too coarse and is replaced here. The practical consequence is unchanged and, if anything, sharper. A defense selected on its static advantage is defeated comprehensively, and a robustness claim measured on one back-end inherits an unmeasured dependence on which back-end was chosen. This is the same lesson as §5.5, arrived at from the opposite direction: there, the encoder determined whether a \emph{text} attack worked at all; here, it determines whether a defense collapses in one perturbation step or three. \textbf{In both cases the encoder is not a nuisance parameter.}

\textbf{Finding 13. What survives adaptation, and why.} Only one configuration retains measurable benefit, and only in part of the sweep: the R1+R2 constraint on BBQ holds \texttt{poison@k} at 0.049 / 0.111 / 0.319 for \(\lambda \le 0.5\) while preserving the utility proxy (\texttt{in\_pool\_rate} 0.442 against 0.363 for no defense), and it beats multi-query consistency throughout (0.319 against 0.535 at \(\lambda = 0.5\); 0.764 against 0.847 at \(\lambda = 1\)). We attribute this to the defense's \emph{objective} rather than to any attack-specific matching. It is the only defense whose constraint is expressed over the composition of the retrieved set rather than over individual passage statistics, so it cannot be satisfied by choosing perturbations --- only by changing which passages are mutually compatible. That is a weaker effect than the static evaluation suggested, and it disappears by \(\lambda = 2\). The asymmetry is the useful part: \textbf{constraints on properties of an individual passage are optimisable-against because the attacker controls that passage; constraints on the set are not, but they are correspondingly weaker.}

\subsubsection{The evaluation protocol these results imply}\label{the-evaluation-protocol-these-results-imply}

Findings 12 and 13 are not sensitive to our particular attack. They follow from the attacker being informed, which is the standard against which robustness claims are judged in the adversarial literature \citep{carlini2019,tramer2020}. We therefore state the protocol as a requirement rather than a suggestion, and it is the second half of the measurement contribution this paper makes: §3.4 gave the conditions under which a \emph{statistic} is blind, and this gives the conditions under which a \emph{robustness claim} is interpretable.

\begin{enumerate}
\def\labelenumi{\arabic{enumi}.}
\tightlist
\item
  \textbf{State the threat model, including whether the attacker knows the defense.} A claim of robustness without this qualifier is uninterpretable, and it is the qualifier that separates the two evaluations in §5.2 and §5.6.
\item
  \textbf{Report adversarial inclusion as a function of attacker strength, not at one operating point.} A single value cannot distinguish a defense that is robust from one evaluated below its failure threshold. In our sweep every defense fails by \(\lambda = 2\); a sweep stopping at \(\lambda = 0.25\) would have shown three apparently robust defenses.
\item
  \textbf{Sweep to the point of failure and report where it occurs.} The location of the failure is the result; the endpoint alone is not.
\item
  \textbf{Report a utility-preserving baseline}, since a defense trivially achieves low inclusion by returning fewer or worse passages; we report \texttt{in\_pool\_rate} alongside \texttt{poison@k} throughout.
\item
  \textbf{For a randomised defense, state the distribution and assume it is known}, and report the attacker's optimal response to its expectation rather than to a sample. By Proposition 4, randomisation bounds the variance of the attacker's utility and not its mean.
\item
  \textbf{For a penalty-based defense, report whether the penalty is computable from public information}, and if it is, treat it as a constraint in the attacker's optimisation rather than as an unknown. This is Corollary 2, and in our experiments it is decisive for the defense that looked strongest statically: publishing a scoring function, which auditability requires, is equivalent to handing the attacker a differentiable objective.
\end{enumerate}

'''


def main():
    s = io.open(TEX, encoding='utf-8').read()
    if ANCHOR not in s:
        print('ANCHOR FAIL')
        return 1
    section = SECTION.replace('__LONGTABLE__', longtable())
    s = s.replace(ANCHOR, section + ANCHOR, 1)

    # add the two references before \end{thebibliography}, alphabetically placed
    bib_end = s.find('\\end{thebibliography}')
    entries = ''.join('\\bibitem[%s]{%s} %s\n' % r for r in NEW_REFS)
    s = s[:bib_end] + entries + s[bib_end:]

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print('inserted tex section: %d chars' % len(section))
    print('bibliography entries added: %d' % len(NEW_REFS))
    print('bibitems now: %d' % s.count('\\bibitem['))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
