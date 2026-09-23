"""Fix the two defects the compression introduced.

1. The replacement block ended with the "### 5.7 ..." heading and the original
   text after the cut also began with it, so the heading is now duplicated.
2. Removing a table left the numbering with a gap at 13; the displaced generation
   table and everything after it shift down by one so the sequence is contiguous.

Table map after this pass:
    1-12  unchanged
    13    generation-layer stance, entailment-scored (was 15)
    14    generation-layer forced-choice, historical  (was 14)
    15    Prop. 1 prediction                          (was 15b)
    16    over-generalisation signal                  (was 16)
    17    paired tests                                (was 17)
    18    bootstrap CIs                               (was 18)
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

HEAD = '### 5.7 Generation-stage propagation: does the retrieval skew reach the output?'
n = s.count(HEAD)
print('5.7 heading occurrences: %d' % n)
if n == 2:
    # drop the second occurrence and the blank line that follows it
    first = s.find(HEAD)
    second = s.find(HEAD, first + 1)
    s = s[:second] + s[second + len(HEAD):]
    s = s.replace('\n\n\n', '\n\n')
    print('duplicate heading removed')

# the displaced generation table becomes 13, and the historical one 14
pairs = [
    ('**Table 15.** Generation-layer stance, entailment-scored',
     '**Table 13.** Generation-layer stance, entailment-scored'),
    ('**Table 14.** The first generation-layer measurement',
     '**Table 14.** The first generation-layer measurement'),
    ('**Table 15b.** Prop. 1 prediction',
     '**Table 15.** Prop. 1 prediction'),
    ('Table 15b reports the prediction of Prop. 1',
     'Table 15 reports the prediction of Prop. 1'),
]
for old, new in pairs:
    c = s.count(old)
    if c:
        s = s.replace(old, new)
        print('%d x %r -> %r' % (c, old[:44], new[:44]))

io.open(P, 'w', encoding='utf-8').write(s)

print()
print('sections:')
for m in re.finditer(r'^### (5\.\d+ .+)$', s, re.M):
    print('  ' + m.group(1)[:72])
print()
print('tables: %s' % ' '.join(re.findall(r'^\*\*Table (\S+?)\.\*\*', s, re.M)))
