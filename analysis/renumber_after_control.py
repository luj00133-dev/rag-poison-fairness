"""Renumber the body tables after inserting the responsiveness control as Table 2.

The control was inserted into section 3.4, which is before every results table, so
each existing table shifts up by one: the old 2..11 became 3..12. Written as a
descending renumber through placeholders, because a sequential pass chains: renaming
2 to 3 creates a new "Table 2" that the *next* rule would treat as input, which is
exactly how the numbering was corrupted earlier in this project.

Both captions and in-text references are rewritten from one map, so they cannot
drift apart.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

iB = s.find('## Appendix B')
iC = s.find('## Appendix C')

caps = [(m.start(), m.group(1)) for m in
        re.finditer(r'^\*\*Table (\S+?)\.\*\*', s, re.M)]
body = [n for p, n in caps if p < iB and n.isdigit()]
print('body tables before: %s' % ' '.join(body))

# the new control holds 2; everything that was 2..N moves up by one
shift = {n: str(int(n) + 1) for n in body if int(n) >= 2}
print('shift map: %s' % ', '.join('%s->%s' % kv for kv in
                                  sorted(shift.items(), key=lambda kv: int(kv[0]))))

# captions: descending, via placeholders
order = sorted(shift, key=lambda n: int(n), reverse=True)
for n in order:
    s = s.replace('**Table %s.**' % n, '**Table @@%s@@.**' % n)
for n in order:
    s = s.replace('**Table @@%s@@.**' % n, '**Table %s.**' % shift[n])

# references: descending too, and anchored so "Table 2" cannot match "Table 20"
for n in order:
    s = re.sub(r'(?<![\w])Tables %s(?![\d\w])' % re.escape(n),
               'Tables @@%s@@' % n, s)
    s = re.sub(r'(?<![\w])Table %s(?![\d\w])' % re.escape(n),
               'Table @@%s@@' % n, s)
for n in order:
    s = s.replace('@@%s@@' % n, shift[n])

io.open(P, 'w', encoding='utf-8').write(s)

caps2 = re.findall(r'^\*\*Table (\S+?)\.\*\*', s, re.M)
print()
print('after: %s' % ' '.join(caps2))
body2 = [n for n in caps2 if n.isdigit()]
nums = [int(n) for n in body2]
print('contiguous: %s' % (nums == list(range(1, len(nums) + 1))))
