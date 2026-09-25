"""Mirror the limitations compaction in the LaTeX source (body table + Appendix D).

The tex holds the list as an `enumerate` environment running from the bold
"Limitations." lead-in to just before the Conclusion section. That whole environment
moves verbatim into a new Appendix D, and the body gets a summary longtable instead, so
the two sources keep the same shape as the markdown.

The replacement table uses the same font conventions as the rest of the paper
(\textbf for the limitation title, \texttt for code-like names) and the
`{\\def\\LTcaptype{none} ... }` wrapper that every other hand-built table in this file
uses to avoid incrementing the table counter.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', 'paper', 'latex', 'paperA_R1R2.tex')

START = '\\textbf{Limitations.}'
END = '\\section{Conclusion}\\label{conclusion}'

TABLE = r"""\textbf{Limitations.} Ten constraints bound what this study establishes. The table states each one and what it costs; the full statement of each, with the measurements behind it, is in Appendix D.

{\def\LTcaptype{none} % do not increment counter
\begin{longtable}[]{@{}
  >{\raggedright\arraybackslash}p{(\linewidth - 6\tabcolsep) * \real{0.0500}}
  >{\raggedright\arraybackslash}p{(\linewidth - 6\tabcolsep) * \real{0.3700}}
  >{\raggedright\arraybackslash}p{(\linewidth - 6\tabcolsep) * \real{0.5800}}@{}}
\toprule\noalign{}
\begin{minipage}[b]{\linewidth}\raggedright
\#
\end{minipage} & \begin{minipage}[b]{\linewidth}\raggedright
Limitation
\end{minipage} & \begin{minipage}[b]{\linewidth}\raggedright
What it constrains, or what already handles it
\end{minipage} \\
\midrule\noalign{}

\bottomrule\noalign{}

1 & \textbf{Group- and stance-annotated passages are required, and neutral retrieval corpora do not carry them} & The binding constraint on this whole line of work: the framework's applicability is bounded by annotation, not computation. R1 needs a group label per passage and R2 a stance label, and no standard neutral corpus (NQ, MS MARCO) has either, nor can stance toward a group be inferred from a neutral passage. Described in full in Appendix D.1. \\
2 & \textbf{Neither corpus is a neutral retrieval benchmark, and they disagree in two respects} & The text-only attack works only on the controlled corpus; the R2 constraint reduces inclusion only on BBQ. Both conditions are reported rather than the favourable one, and the mechanism behind the first disagreement is identified (§5.4). \\
3 & \textbf{The absolute R2 metric does not transfer across corpora} & \texttt{stance\_gap} is exactly 0 on the balanced controlled corpus but 0.9326 on BBQ \emph{before any attack}. Only the change from the clean baseline is informative there, and §5.4 relies on the change throughout. \\
4 & \textbf{Injection budget must be reported as a rate, not a count} & A fixed count measures corpus size rather than attack strength. §5.4 sweeps \(\rho \in \{0.1\%, \dots, 2\%\}\); readers comparing against absolute counts must convert. \\
5 & \textbf{Nine retrieval back-ends, and the scale check changed the conclusion} & GTE-base \(\rightarrow\) GTE-large moves susceptibility from 0.0625 to 0.5000 within one family and recipe, so a single-encoder robustness claim reports an unmeasured checkpoint property (§5.5). Contriever is not swept at large scale and multilingual or instruction-tuned embedders are not tested. \\
6 & \textbf{The generation-stage evaluation is multi-generator and multi-probe, and the probes disagree} & Three sub-limits, each with a measurement behind it: retrieval conditions are fixed to one backbone; the free-form probe commits to a position in only 15.6\% (controlled) and 1.0\% (BBQ) of cases, which is why the forced-choice probe is primary; and the effect is generator-dependent. Appendix D.6 also records the inverted-context negative control and a corrected attribution metric. \\
7 & \textbf{Binary groups: \(\vert\mathcal{G}\vert = 2\) throughout} & Extension to \(\vert\mathcal{G}\vert > 2\) is mechanical for R1 and R2 but is not evaluated here. BBQ's race/ethnicity category is also markedly imbalanced in our build (960 vs 88 passages). \\
\end{longtable}
}

"""


def main():
    s = io.open(TEX, encoding='utf-8').read()

    i = s.find(START)
    j = s.find(END)
    if i < 0 or j < 0 or j < i:
        print('BOUNDARY FAIL: start=%d end=%d' % (i, j))
        return 1
    block = s[i:j]
    if '\\begin{enumerate}' not in block or '\\end{enumerate}' not in block:
        print('ENUMERATE FAIL: the limitations block is not the expected enumerate')
        return 1

    appendix_d = ('\\section{Appendix D. Limitations in full}'
                  '\\label{appendix-d.-limitations-in-full}\n\n'
                  'The body states each limitation in one line and what it costs; this '
                  'appendix states them in full, with the measurements behind each. The '
                  'numbering matches the body table.\n\n'
                  + block[len(START):].strip() + '\n\n'
                  '\\begin{center}\\rule{0.5\\linewidth}{0.5pt}\\end{center}\n\n')

    # body: table replaces the enumerate
    s = s[:i] + TABLE + s[j:]

    # appendix D goes immediately before the References section heading
    refs = s.find('\\section{References}')
    if refs < 0:
        print('REFERENCES ANCHOR FAIL')
        return 1
    # keep it inside the appendix block: insert before the rule that precedes References
    rule_before_refs = s.rfind('\\begin{center}\\rule{0.5\\linewidth}{0.5pt}\\end{center}',
                               0, refs)
    insert_at = rule_before_refs if rule_before_refs > 0 else refs
    s = s[:insert_at] + appendix_d + s[insert_at:]

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print('appendix D inserted at char %d' % insert_at)
    print('body tables : %d' % len(__import__('re').findall(r'\\textbf\{Table \d+\.\}', s)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
