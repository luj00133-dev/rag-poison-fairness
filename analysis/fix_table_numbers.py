"""Give every table its correct final number, positionally, in one safe pass.

The first attempt applied replacements sequentially and they chained: rewriting
"Table 4" to "Table 3" produced a new "Table 3" that a later rule treated as
input, leaving duplicate captions (two 3s, two 8s) and a missing 9, with in-text
references split between old and new numbers.

This repair does not invert that damage. It assigns labels by *position* -- the
k-th table in the body becomes k -- and rewrites in-text references against the
content each one points at, read off the document rather than inferred from the
damaged numbering. Every replacement asserts its expected occurrence count, and
the file is written only after all of them succeed, so a partial application
cannot leave the manuscript in a third inconsistent state.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

iB = s.find('## Appendix B')
iC = s.find('## Appendix C')

# --- 1. captions by position ------------------------------------------------- #
caps = list(re.finditer(r'^\*\*Table (\S+?)\.\*\*', s, re.M))
body = [m for m in caps if m.start() < iB]
appB = [m for m in caps if iB < m.start() < iC]
appC = [m for m in caps if m.start() > iC]

plan = []
for k, m in enumerate(body, start=1):
    plan.append((m.start(), m.end(), '**Table %d.**' % k))
for k, m in enumerate(appB, start=1):
    plan.append((m.start(), m.end(), '**Table B%d.**' % k))
for k, m in enumerate(appC, start=1):
    plan.append((m.start(), m.end(), '**Table C%d.**' % k))
for start, end, text in sorted(plan, reverse=True):
    s = s[:start] + text + s[end:]
print('captions: %d body -> 1..%d, %d appB, %d appC'
      % (len(body), len(body), len(appB), len(appC)))

# --- 2. in-text references --------------------------------------------------- #
FIX = [
    ('(Table 16)', '(Table B1)', 1),
    ('reproduces Table 12 with 18', 'reproduces Table C1 with 18', 1),
    ('Read Table 13 and Table 11 together',
     'Read Table C2 and Table 10 together', 1),
    ('# the mechanism behind Table 12', '# the mechanism behind Table C1', 1),
    ('Table 15 reports the prediction', 'Table C3 reports the prediction', 1),
]
for old, new, expect in FIX:
    n = s.count(old)
    assert n == expect, 'expected %d, found %d for %r' % (expect, n, old[:50])
    if old != new:
        s = s.replace(old, new)
    print('ok  %r' % old[:52])

io.open(P, 'w', encoding='utf-8').write(s)

print()
for m in re.finditer(r'^\*\*Table (\S+?)\.\*\*(.{0,46})', s, re.M):
    ln = s[:m.start()].count('\n') + 1
    print('  %4d  T%-5s %s' % (ln, m.group(1), m.group(2)))
