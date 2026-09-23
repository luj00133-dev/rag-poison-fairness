"""Normalise every table number to a clean scheme after the compression.

State before this pass, left by the preceding structural edits: the body had gaps
(T1, T2, T4..T11, T14, T17) because tables were moved or merged, and the appendix
mixed plain numerics (19..23, continuing from Appendix B's 17 and 18) with
letters.

Scheme applied:
  * body tables are renumbered contiguously 1..N in reading order;
  * appendix tables get a letter prefix for their appendix (B1, B2, C1..C5), which
    is the usual convention and removes the ambiguity of one numeric sequence
    spanning body and appendix.

Every in-text "Table X" reference is rewritten with the same map, in one pass, so
a caption and its references cannot drift apart.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

# Locate appendix boundaries
iB = s.find('## Appendix B')
iC = s.find('## Appendix C')
iR = s.find('## References')
assert 0 < iB < iC < iR, (iB, iC, iR)

caps = [(m.start(), m.group(1)) for m in
        re.finditer(r'^\*\*Table (\S+?)\.\*\*', s, re.M)]
body_caps = [(p, n) for p, n in caps if p < iB]
b_caps = [(p, n) for p, n in caps if iB < p < iC]
c_caps = [(p, n) for p, n in caps if iC < p < iR]

# Build the map old -> new
mapping = {}
for k, (_, n) in enumerate(body_caps, start=1):
    mapping[n] = str(k)
for k, (_, n) in enumerate(b_caps, start=1):
    mapping[n] = 'B%d' % k
for k, (_, n) in enumerate(c_caps, start=1):
    mapping[n] = 'C%d' % k

print('body tables : %s' % ' '.join(n for _, n in body_caps))
print('appendix B  : %s' % ' '.join(n for _, n in b_caps))
print('appendix C  : %s' % ' '.join(n for _, n in c_caps))
print()
print('mapping: %s' % ', '.join('%s->%s' % kv for kv in mapping.items()))

# Rewrite captions first (they are unambiguous: line starts with **Table N.**)
def cap_repl(m):
    old = m.group(1)
    return '**Table %s.**' % mapping.get(old, old)


s = re.sub(r'^\*\*Table (\S+?)\.\*\*', cap_repl, s, flags=re.M)

# Then in-text references. Longest keys first so "19" is not clipped by "1".
for old in sorted(mapping, key=len, reverse=True):
    new = mapping[old]
    if old == new:
        continue
    s = re.sub(r'(?<![\w])Table %s(?![\d\w])' % re.escape(old),
               'Table %s' % new, s)
    s = re.sub(r'(?<![\w])Tables %s(?![\d\w])' % re.escape(old),
               'Tables %s' % new, s)

io.open(P, 'w', encoding='utf-8').write(s)

print()
print('after renumbering:')
for m in re.finditer(r'^\*\*Table (\S+?)\.\*\*(.{0,48})', s, re.M):
    ln = s[:m.start()].count('\n') + 1
    print('  line %4d  T%-5s %s' % (ln, m.group(1), m.group(2)))

known = set(mapping.values())
intext = set(re.findall(r'[Tt]able[s]? (\S+?)[\s,\.\)]', s))
dangling = sorted(x for x in intext if x[0].isdigit() or x.startswith(('B', 'C')))
dangling = [x for x in dangling if x not in known]
print()
print('DANGLING refs: %s' % (dangling if dangling else 'none'))
