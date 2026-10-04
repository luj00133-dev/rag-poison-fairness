"""Add the Oliveira reference to the tex bibliography and cite it, in the tex's own style.

The tex uses natbib author-date, so the markdown's numeric [25] has no counterpart: the entry needs
a \\bibitem with an author-year label and the prose needs a \\citet. This reads the existing entry
format first and matches it rather than assuming one.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')
ITEM = chr(92) + 'bibitem'


def main():
    tex = io.open(TEX, encoding='utf-8').read()

    idx = [m.start() for m in re.finditer(re.escape(ITEM), tex)]
    print('%s entries in the tex: %d' % (ITEM, len(idx)))
    if not idx:
        print('ABORT: no bibliography entries found')
        return 1

    # show one entry verbatim so the format is copied, not guessed
    print()
    print('--- existing entry (format reference) ---')
    print(tex[idx[-1]:idx[-1] + 380])
    print()

    # the Bagwe entry, which the new citation sits next to
    b = tex.find('Bagwe')
    k = max([i for i in idx if i < b], default=None)
    print('--- the Bagwe entry ---')
    if k is not None:
        print(tex[k:k + 420])
    print()

    # does a key for Oliveira already exist?
    if 'oliveira2026' in tex:
        print('oliveira2026 already present; no entry added')
    else:
        entry = (ITEM + '[Oliveira et al.(2026)]{oliveira2026} '
                 'Oliveira, M., Vergilio, B.~J., Sobrinho, R., de Andrade Silva, J., '
                 '\\& Font\\~ao, A. (2026). Metamorphic fairness testing of '
                 'retrieval-augmented generation: Diagnosing retriever bias and evaluating '
                 'graph-based mitigation. \\emph{Journal of Software Engineering Research and '
                 'Development}, 14(1), 179--208.')
        # insert directly after the Bagwe entry, which is the topically adjacent one
        if k is not None:
            end = tex.find(chr(10), tex.find('}', tex.find('Bagwe')))
            end = tex.find(chr(10), end + 1) if False else end
            # find the end of the Bagwe bibitem: the next bibitem or the end environment
            nxt = [i for i in idx if i > k]
            stop = nxt[0] if nxt else tex.find('\\end{thebibliography}')
            tex = tex[:stop] + entry + chr(10) + tex[stop:]
            print('inserted the Oliveira entry after the Bagwe entry')
        else:
            stop = tex.find('\\end{thebibliography}')
            tex = tex[:stop] + entry + chr(10) + tex[stop:]
            print('inserted the Oliveira entry before the end of the bibliography')

    # cite it in the same sentence where the markdown cites [25]
    old = ('where an aggregate over groups hides the per-group and per-stakeholder structure '
           'that a fairness claim depends on.')
    new = ('where an aggregate over groups hides the per-group and per-stakeholder structure '
           'that a fairness claim depends on, and \\citet{oliveira2026} reach it independently '
           'from software testing, reporting a RAG fairness regression that a per-model analysis '
           'detects and aggregate testing does not.')
    if 'oliveira2026' in tex and old in tex and '\\citet{oliveira2026}' not in tex:
        tex = tex.replace(old, new, 1)
        print('added the citation in prose')
    else:
        print('prose citation already present, or anchor not found')

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(tex)

    tex2 = io.open(TEX, encoding='utf-8').read()
    print()
    print('bibitem count now : %d' % len(re.findall(re.escape(ITEM), tex2)))
    print('oliveira key cited: %d' % len(re.findall(r'\\cite[tp]?\{oliveira2026\}', tex2)))
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in tex2:
            print('FAIL: missing %s' % needed)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
