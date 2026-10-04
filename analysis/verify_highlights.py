"""Verify the claims in the proposed Highlights against the manuscript.

Highlights are a submission artefact that IP&M prints separately, so a wrong number or a
wrong count there is a defect that never gets checked by the paper's own proofing. Each
proposed highlight is checked here against the tex.

In particular the fifth claims a "six-point protocol". The paper has a protocol in 5.8.1 and
a second, longer one in section 8; if the numbers differ, the highlight must name the right
one or the count must be fixed.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')


def count_items(text):
    return len(re.findall(r'\\item\b', text))


def section(text, start_marker, end_marker):
    i = text.find(start_marker)
    if i < 0:
        return ''
    j = text.find(end_marker, i)
    return text[i:j if j > 0 else i + 20000]


def main():
    s = io.open(TEX, encoding='utf-8').read()

    p581 = section(s, 'The evaluation protocol these results imply', '\\subsection')
    p8 = section(s, 'We close with the protocol the results imply', '\\section')
    print('protocol in 5.8.1 : %d items (%d chars)' % (count_items(p581), len(p581)))
    print('protocol in sec 8 : %d items (%d chars)' % (count_items(p8), len(p8)))

    print()
    print('--- claim checks ---')
    claims = [
        ('H1 structural invariance',
         'adversarially invariant' in s,
         'abstract states the statistics are adversarially invariant'),
        ('H2 three modes',
         all(m in s for m in ('balanced count', 'preserved nuisance', 'cancelled shift')),
         'F1/F2/F3 named in the taxonomy'),
        ('H3 0.13 vs 0.002',
         ('0.13' in s and '0.002' in s and 'per-group' in s),
         'per-group shifts 0.13 against a gap under 0.002'),
        ('H4 largest on pretrained encoders',
         'four begin at exactly 0.000' in s,
         'four of six back-ends begin at exactly 0.000 inclusion'),
        ('H5 protocol count', count_items(p581) == 6 or count_items(p8) == 6,
         'a six-item protocol exists'),
    ]
    for name, ok, why in claims:
        print('  %-34s %-5s %s' % (name, 'OK' if ok else 'CHECK', why))

    print()
    print('--- the word "six-point" in the paper refers to which protocol? ---')
    for m in re.finditer(r'.{110}six-point.{80}', s, re.S):
        print('  ...%s...' % ' '.join(m.group(0).split()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
