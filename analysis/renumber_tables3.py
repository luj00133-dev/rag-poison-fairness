"""Swap Tables 12 and 13 so numbering follows document order (the mechanism
table now precedes the inertness-at-scale table)."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

# park the two headings on sentinels, then assign by position
s = s.replace('**Table 13.** Where the GTE scale effect comes from.',
              '**Table @@MECH@@.** Where the GTE scale effect comes from.')
s = s.replace('**Table 12.** R1-only constraint inertness on large back-ends.',
              '**Table @@INERT@@.** R1-only constraint inertness on large back-ends.')
s = s.replace('**Table @@MECH@@.**', '**Table 12.**')
s = s.replace('**Table @@INERT@@.**', '**Table 13.**')

# fix the in-text pointer to the inertness table
s = s.replace('Table 12 extends the \u00a75.2 inertness check',
              'Table 13 extends the \u00a75.2 inertness check')

io.open(P, 'w', encoding='utf-8').write(s)

import re
print('ordering now:')
for m in re.finditer(r'^\*\*Table (\d+)\.\*\*(.{0,58})', s, re.M):
    print('  T%-3s %s' % (m.group(1), m.group(2)))
nums = [int(x) for x in re.findall(r'^\*\*Table (\d+)\.\*\*', s, re.M)]
print()
print('duplicates:', [n for n in set(nums) if nums.count(n) > 1] or 'none')
print('appendix duplicate (Table 3) is in a separate numbering space')
