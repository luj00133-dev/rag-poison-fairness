"""Shift the two tables downstream of the new mechanism table (Table 13)."""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

subs = [
    ('**Table 13.** Generation-layer stance by condition.',
     '**Table 14.** Generation-layer stance by condition.'),
    ('**Table 14.** Prop. 1 prediction vs. measurement.',
     '**Table 15.** Prop. 1 prediction vs. measurement.'),
]
for old, new in subs:
    n = s.count(old)
    s = s.replace(old, new)
    print('%d x %s -> %s' % (n, old[:44], new[:44]))

io.open(P, 'w', encoding='utf-8').write(s)

print()
caps = re.findall(r'^\*\*Table (\d+)\.\*\*', s, re.M)
print('table captions in order:', caps)
nums = [int(c) for c in caps]
dupes = [n for n in set(nums) if nums.count(n) > 1]
print('duplicates:', dupes if dupes else 'none')
