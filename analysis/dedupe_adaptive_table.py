"""Remove the now-duplicated adaptive table from the body and normalise appendix labels.

Two problems found by inspecting the result of move_tables_to_appendix.py.

1. The adaptive-attacker table existed twice. Section 5.2 has carried its own copy
   since before section 5.6 was written, and creating 5.6 added a second copy
   without removing the first -- so the same experiment was printed twice with
   identical values. Both are now the appendix table; the body keeps the prose.

2. Appendix labels came out as "C1".."C5", but the manuscript's convention for the
   other appendices is plain numeric continuation (17, 18). Renumbering them
   continues the sequence instead of switching notation mid-paper.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

# --- 1. drop the duplicate body table --------------------------------------- #
m = re.search(r'^\*\*Table 3\.\*\* Adaptive attacker.*?(?=\n\nThe adaptive attacker)',
              s, re.M | re.S)
assert m, 'body adaptive table not found'
s = s[:m.start()] + ('The adaptive sweep is in Appendix C, Table C1; the ranking '
                     'inverts as described below.') + s[m.end():]
print('removed the duplicate body adaptive table')

# --- 2. appendices continue the numeric sequence ---------------------------- #
# C1..C5 -> 19..23, but 17 and 18 already exist in Appendix B, so the new tables
# become 19 through 23.
for old, new in (('C1', '19'), ('C2', '20'), ('C3', '21'), ('C4', '22'), ('C5', '23')):
    s = s.replace('**Table %s.**' % old, '**Table %s.**' % new)
    s = s.replace('Appendix C, Table %s' % old, 'Appendix C, Table %s' % new)
s = s.replace('Appendix Table C1', 'Appendix Table 19')

io.open(P, 'w', encoding='utf-8').write(s)

print()
for m in re.finditer(r'^\*\*Table (\S+?)\.\*\*(.{0,52})', s, re.M):
    ln = s[:m.start()].count('\n') + 1
    print('line %4d  T%-5s %s' % (ln, m.group(1), m.group(2)))
