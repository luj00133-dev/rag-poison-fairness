"""Add Appendix E to the LaTeX source: the record of changes to our own measurements.

Placed after Appendix D and before the AI declaration, which is where the markdown has it
and the correct position for an appendix. The content is the markdown appendix ported to
LaTeX conventions (\\texttt for code-like tokens, \\(...\\) for values, ASCII hyphens for
minus signs since the document is pdflatex without inputenc).

This content is a material disclosure, not a weakness being hidden: it records every value
that earlier versions of this work reported differently, including the factor-of-six error
and the reversed entailment convention. It sits in an appendix so that the main narrative
opens on the contribution rather than on a list of our corrections -- the facts remain in
the published paper and a reader can audit them.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

ANCHOR = ('\\section{Declaration of generative AI and AI-assisted technologies in the '
          'manuscript preparation process}')

APPENDIX = r'''\section{Appendix E. The record of changes to our own measurements}\label{appendix-e.-the-record-of-changes-to-our-own-measurements}

The body reports the measurements as they stand. This appendix records where earlier versions of this work reported something different, so that a reader who has seen an earlier draft can see exactly what changed and why. Every number quoted here is the superseded value; the value that replaced it is the one used in the body.

\begin{enumerate}
\def\labelenumi{\arabic{enumi}.}
\tightlist
\item
  \textbf{The static advantage of off-manifold filtering.} An earlier draft reported 0.125 / 0.438 / 0.750 across the perturbation sweep and described the static advantage as a factor of six over no defense. Those values came from a run written to a scratch directory excluded from version control, rather than from the configuration that produces every other number in this paper. Re-running the committed configuration reproduces Table C1 with 18 of 18 adaptive cells bit-identical, and gives a static advantage of a factor of three. The qualitative conclusion is unchanged; the factor is.
\item
  \textbf{The shape of the adaptive collapse.} We first reported that the collapse is steeper on a pretrained encoder than on our own hashed retriever, and framed the result as ``real encoders collapse faster''. With six back-ends the pattern does not support that framing: GTE-base and E5-base-v2 fail in a single perturbation step, while Contriever and both SPLADE sizes climb gradually and resemble the hashed retriever. The framing was replaced by the three claims in §5.8, which hold on all six.
\item
  \textbf{The R2 reference convention.} Our first implementation scored stance as \texttt{P(entail | statement, answer)}. Calibrated against the correct convention on the same data, the reversed form returns \(\pm 0.002\) for a favourable answer, an unfavourable answer, an unrelated answer and a vacuous one alike; the correct direction, \texttt{P(entail | answer, statement)}, returns \(+0.997\) and \(-0.997\) for the two extremes. The convention is not interchangeable, and the failure mode is indistinguishable from a genuine null result.
\item
  \textbf{The attribution direction.} The expected-attributed-exposure statistic was first implemented by asking the generator whether its answer relied on each retrieved passage. It returned 1.000 in every condition. The cause is direction: attribution must ask whether the \textbf{passage entails the answer}. With the direction corrected the statistic discriminates properly, 0.798--0.828 clean rising to 0.831--0.968 under injection.
\item
  \textbf{The injection parameter.} An earlier version injected a fixed six passages per stratum and concluded that the text-only attack does not transfer to natural data. Six passages is roughly 10\% of a small candidate pool but 0.03\% of an 18k-passage corpus, so a fixed count measures corpus size rather than attack strength. The sweep in §5.4 is reported as an injection rate.
\item
  \textbf{An inference from Corollary 1.} An earlier version concluded that the number of passages required is bounded by a small constant independent of corpus size. That conflates two requirements which behave differently, and the corrected statement is in §6.
\item
  \textbf{A cross-reference defect found by our own checker.} During an automated edit, three \texttt{\textbackslash bibitem} keys were assigned the same label. \texttt{pdflatex} resolves duplicate labels silently to the last definition, so every citation affected was pointing at the wrong entry while the document still compiled with no errors. It was found by comparing the citation set against an independent source and corrected; the check that found it is released with the code.
\end{enumerate}

'''


def main():
    s = io.open(TEX, encoding='utf-8').read()
    if ANCHOR not in s:
        print('ANCHOR FAIL: AI declaration section not found')
        return 1
    if '\\section{Appendix E.' in s:
        print('Appendix E already present; nothing to do')
        return 0
    s = s.replace(ANCHOR, APPENDIX + ANCHOR, 1)
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    # ---- verify: order, structure, and no stray control characters
    s2 = io.open(TEX, encoding='utf-8').read()
    order = re.findall(r'\\section\{(Appendix [A-E][^}]*)\}', s2) if (re := __import__('re')) else []
    print('appendix order:')
    for name in order:
        print('   %s' % name[:74])
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in s2:
            print('FAIL: missing %s' % needed)
            return 1
    ctrl = [c for c in s2 if ord(c) < 32 and c not in '\n\r\t']
    print()
    print('structure intact; control characters: %s' % (len(ctrl) or 'none'))
    print('enumerate blocks now: %d' % s2.count('\\begin{enumerate}'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
