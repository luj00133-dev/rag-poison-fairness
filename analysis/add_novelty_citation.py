"""Add the metamorphic-fairness-testing citation the novelty check surfaced.

Oliveira et al. (2026) report, from software testing rather than from an adversarial construction,
that a model-specific RAG fairness regression was "invisible to aggregate testing" -- the same
aggregate-hides-it argument this paper makes, arrived at independently. Citing it in the paragraph
that already discusses Ekstrand's version of that argument strengthens the motivation and, more
practically, forecloses a reviewer asking why a directly relevant 2026 paper is absent.

Bagwe et al. (EMNLP 2025) is already cited as [13]; the novelty check found it to be the closest
attack-side work, so its differentiation is made explicit in the same edit rather than left implicit.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

# the paragraph to extend, matched on a stable fragment
MD_OLD = ('Ekstrand et al. [18] make the same argument inside information access, where an '
          'aggregate over groups hides the per-group and per-stakeholder structure that a '
          'fairness claim depends on.')
MD_NEW = ('Ekstrand et al. [18] make the same argument inside information access, where an '
          'aggregate over groups hides the per-group and per-stakeholder structure that a '
          'fairness claim depends on, and Oliveira et al. [25] reach it independently from '
          'software testing, reporting a RAG fairness regression that a per-model analysis '
          'detects and aggregate testing does not.')

# the attack-side differentiation, which the novelty check showed was worth making explicit
MD_OLD2 = ('A parallel thread targets the retrieval process itself rather than passage content, '
           'manipulating embedding space so that injected passages rank highly regardless of '
           'their text.')
MD_NEW2 = ('A parallel thread targets the retrieval process itself rather than passage content, '
           'manipulating embedding space so that injected passages rank highly regardless of '
           'their text. Bagwe et al. [13] carry the attack direction into fairness specifically, '
           'showing that a backdoor can establish a persistent and covert influence on which '
           'groups a RAG system favours. That work establishes that the attack exists and '
           'persists; the question this paper asks is different, namely whether the statistics '
           'used to select and validate fairness defenses can see such an attack at all.')

REF = ('[25] M. Oliveira, B. J. Vergilio, R. Sobrinho, J. de Andrade Silva, A. Fontao. '
       'Metamorphic fairness testing of retrieval-augmented generation: Diagnosing retriever '
       'bias and evaluating graph-based mitigation. *Journal of Software Engineering Research '
       'and Development*, 14(1):179-208, 2026.\n')


def main():
    md = io.open(MD, encoding='utf-8').read()
    for old, new, label in ((MD_OLD, MD_NEW, 'measurement paragraph'),
                            (MD_OLD2, MD_NEW2, 'attack differentiation')):
        n = md.count(old)
        print('%-26s %d match(es)' % (label, n))
        if n == 1:
            md = md.replace(old, new, 1)

    if '[25]' not in md:
        # append after the last reference, keeping the trailing blank line
        refs_at = md.find('## References')
        tail = md.rfind('[24]')
        end = md.find('\n\n', tail)
        if end < 0:
            end = len(md)
        md = md[:end] + '\n' + REF.rstrip() + md[end:]
        print('appended reference [25]')
    else:
        print('reference [25] already present')

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(md)

    md2 = io.open(MD, encoding='utf-8').read()
    print()
    print('[25] cited in text : %d' % len(re.findall(r'\[25\]', md2)))
    print('Oliveira named     : %s' % ('Oliveira et al.' in md2))
    print('Bagwe differentiated: %s' % ('That work establishes that the attack exists' in md2))
    print('reference count    : %d' % len(re.findall(r'^\[\d+\]', md2, re.M)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
