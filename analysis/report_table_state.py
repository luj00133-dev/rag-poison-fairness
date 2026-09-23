"""Report the current caption and reference state after the failed renumbering.

The previous pass applied replacements sequentially, so mappings chained:
renumbering 4->3 created new text "Table 3", which the later rule 5->4 did not
touch but the rule for the *old* "3" (absent) and the caption pass had already
rewritten -- the result is duplicate captions (two "Table 3", two "Table 8") and
a missing 9. This prints the true current state so the repair can be written
against it rather than against an assumption.
"""
import io
import os
import re
import collections

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

iB = s.find('## Appendix B')
iC = s.find('## Appendix C')
iR = s.find('## References')

print('captions (line, label, first words, region):')
for m in re.finditer(r'^\*\*Table (\S+?)\.\*\*(.{0,46})', s, re.M):
    ln = s[:m.start()].count('\n') + 1
    region = 'body' if m.start() < iB else ('appB' if m.start() < iC else 'appC')
    print('  %4d  %-5s %-42s %s' % (ln, m.group(1), m.group(2), region))

print()
refs = collections.Counter(re.findall(r'[Tt]ables? ([A-Z]?\d+[a-z]?)', s))
print('in-text references: %s' % dict(sorted(refs.items())))
