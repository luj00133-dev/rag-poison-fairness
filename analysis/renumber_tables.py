"""Renumber the generation-stage tables and section cross-references displaced
by the new §5.6 (encoder scale) and §5.7 (generation stage)."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

subs = [
    ('**Table 11.** Generation-layer stance by condition.',
     '**Table 13.** Generation-layer stance by condition.'),
    ('**Table 12.** Prop. 1 prediction vs. measurement.',
     '**Table 14.** Prop. 1 prediction vs. measurement.'),
    ('propagates to the generated output** (§5.6)',
     'propagates to the generated output** (§5.7)'),
    ('No generation-stage evaluation *beyond §5.6*',
     'No generation-stage evaluation *beyond §5.7*'),
    ('the key used for the §5.6 runs', 'the key used for the §5.7 runs'),
    ('§5.6 adds a first generation-stage check',
     '§5.7 adds a first generation-stage check'),
]
for old, new in subs:
    n = s.count(old)
    if n == 0:
        print('NOT FOUND: %r' % old[:60])
    s = s.replace(old, new)
    print('%d replacement(s): %r -> %r' % (n, old[:52], new[:52]))

io.open(P, 'w', encoding='utf-8').write(s)

import re
print()
print('table captions now:')
for m in re.finditer(r'^\*\*(Table \d+)\.\*\*(.{0,55})', s, re.M):
    print('  %-9s %s' % (m.group(1), m.group(2)))
print()
print('section headings now:')
for m in re.finditer(r'^### (5\.\d+ .{0,60})', s, re.M):
    print('  ' + m.group(1))
