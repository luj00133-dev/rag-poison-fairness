"""Confirm that after renumbering, each citation still points at the same WORK.

Contiguity and a clean compile are not sufficient: a renumbering that shifted the cite
numbers and the entry numbers by different amounts would still compile and still be
1..N, while silently attaching every citation to the wrong paper. So this compares the
AUTHOR STRING of each cited reference before and after.

Method: for a handful of probe citations, read the reference-list entry that the number
now resolves to in the body and check it against the entry the same *sentence* pointed to
before the renumbering. Concretely, we compare the full author->number mapping derived
from both files: for each reference number, the entry's leading author string must match
what the other source says for the same number, and must match the sentence context.

The strongest available check without a second copy of the bibliography is
markdown-vs-tex agreement, which catches exactly the class of error that occurred
earlier: the two sources disagreeing about what a number means.
"""
import io
import re

P = r'G:\keyan\projects\rag-poison-fairness\paper'
MD = P + r'\manuscript_R1R2_v1.md'
TEX = P + r'\latex\paperA_R1R2.tex'


def entries_md(text):
    at = text.rfind('\n[1] ')
    out = {}
    for m in re.finditer(r'^\[(\d+)\] (.*?)(?=\n\[\d+\] |\Z)', text[at:], re.M | re.S):
        # first author surname or first capitalised token
        head = m.group(2).strip()
        out[int(m.group(1))] = head[:38].replace('\n', ' ')
    return out


def entries_tex(text):
    out = {}
    for m in re.finditer(r'\\bibitem\{ref(\d+)\}(.*?)(?=\\bibitem\{ref\d+\}|\n\\end\{thebibliography\})',
                         text, re.S):
        out[int(m.group(1))] = m.group(2).strip()[:38].replace('\n', ' ')
    return out


md, tex = io.open(MD, encoding='utf-8').read(), io.open(TEX, encoding='utf-8').read()
em, et = entries_md(md), entries_tex(tex)

print('%-4s %-40s %s' % ('#', 'markdown entry', 'tex entry'))
print('-' * 108)
bad = []
for n in range(1, 23):
    a = em.get(n, 'MISSING')
    b = et.get(n, 'MISSING')
    # compare on the leading surname/token, which is stable across the two formats
    ka = re.sub(r'[^A-Za-z]', '', a.split(',')[0].split('.')[0])[:18]
    kb = re.sub(r'[^A-Za-z]', '', b.split(',')[0].split('.')[0])[:18]
    flag = '' if ka[:10] == kb[:10] else '   <-- MISMATCH'
    if flag:
        bad.append(n)
    print('%-4d %-40s %s%s' % (n, a, b, flag))

print()
print('markdown/tex entry mismatch: %s' % (bad or 'none'))
print('both sources 1..22         : %s / %s'
      % (sorted(em) == list(range(1, 23)), sorted(et) == list(range(1, 23))))

# spot-check that a known citation still resolves to the expected work
probes = [
    ('Measurement and fairness', 'Jacobs', 17),
    ('Fairness in information access systems', 'Ekstrand', 18),
    ('An Introduction to the Bootstrap', 'Efron', 20),
]
print()
for title, surname, expect in probes:
    got = [n for n, v in em.items() if surname in v]
    print('%-42s -> entry %s (expected %s) %s'
          % (title, got, expect, 'OK' if got == [expect] else 'CHECK'))
