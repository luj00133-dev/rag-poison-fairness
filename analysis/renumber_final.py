"""Renumber the last three tables so the whole manuscript runs in one sequence.

The exploratory provenance section (§7) had kept its original "Table 3" label
from a draft in which it appeared third. Sections 3-6 have since grown, leaving a
"Table 3" sandwiched between "Table 15b" and "Table 16". Chapter numbering is not
a real problem in a journal submission, but a reference like "Table 3" that
points into the middle of the paper is a reviewing hazard, so the sequence is
normalised here.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

subs = [
    # the three labels, applied before any in-text rewrite so a caption cannot
    # be caught by the reference rules below
    ('**Table 3.** Over-generalisation signal.',
     '**Table 16.** Over-generalisation signal.'),
    ('**Table 16.** Paired tests of R1-constraint inertness',
     '**Table 17.** Paired tests of R1-constraint inertness'),
    ('**Table 17.** Bootstrap 95% CIs on the positive claims',
     '**Table 18.** Bootstrap 95% CIs on the positive claims'),
]
for old, new in subs:
    n = s.count(old)
    assert n == 1, (n, old[:60])
    s = s.replace(old, new)
    print('%s -> %s' % (old[:38], new[:38]))

# in-text references, done as explicit literal replacements
refs = [
    ('the supporting evidence in Table 3', 'the supporting evidence in Table 16'),
    ('Table 3 reports', 'Table 16 reports'),
    ('Table 16 reports the prediction of Prop. 1',
     'Table 15b reports the prediction of Prop. 1'),
    ('the point of \u00a7Table 16 is', 'the point of Table 17 is'),
    ('The point of Table 16 is', 'The point of Table 17 is'),
]
for old, new in refs:
    n = s.count(old)
    if n:
        s = s.replace(old, new)
        print('%d x %r -> %r' % (n, old[:40], new[:40]))

io.open(P, 'w', encoding='utf-8').write(s)

caps = re.findall(r'^\*\*Table (\S+?)\.\*\*', s, re.M)
print()
print('table captions now: %s' % ' '.join(caps))
