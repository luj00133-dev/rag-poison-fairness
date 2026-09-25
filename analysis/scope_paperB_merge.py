"""Scope the merge of Paper B into Paper A: overlap, unique content, reference debt.

Merging is not concatenation. Three things have to be measured first:

  1. how much of B repeats what A already says, since duplicated results inflate the paper
     without adding contribution;
  2. which of B's results are unique, i.e. the actual value of merging;
  3. how many references B cites that A does not have, because A's bibliography is now in
     author-date form and every added work needs a verified APA entry.

Refs are compared by first-author surname plus year, which works across A's author-date
keys and B's numeric list.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
B = os.path.join(P, 'paper', 'manuscript_B_adaptive_v1.md')


def body_and_refs(path):
    s = io.open(path, encoding='utf-8').read()
    i = s.rfind('\n[1] ')
    if i < 0:
        i = s.find('## References')
    return s[:i], s[i:]


def refs_of(text):
    out = {}
    for m in re.finditer(r'^\[(\d+)\] (.{0,90})', text, re.M):
        out[int(m.group(1))] = ' '.join(m.group(2).split())
    return out


a_body, a_refs = body_and_refs(A)
b_body, b_refs = body_and_refs(B)
ra, rb = refs_of(a_refs), refs_of(b_refs)

print('A: %d chars body, %d refs' % (len(a_body), len(ra)))
print('B: %d chars body, %d refs' % (len(b_body), len(rb)))
print()

# --- reference debt: which of B's works A lacks?
def key(entry):
    m = re.match(r'([A-Z][A-Za-z\-]+)', entry)
    y = re.search(r'\b(19|20)\d{2}\b', entry)
    return (m.group(1).lower() if m else '?', y.group(0) if y else '?')

a_keys = {key(v) for v in ra.values()}
missing = []
for n, v in sorted(rb.items()):
    k = key(v)
    if k not in a_keys:
        missing.append((n, v))
print('B references A does not cite: %d of %d' % (len(missing), len(rb)))
for n, v in missing:
    print('   B[%d] %s' % (n, v[:88]))
print()

# --- section-by-section size of B, to see what merging would add
secs = [(m.start(), m.group(2)) for m in re.finditer(r'^(##) (.+)$', b_body, re.M)]
secs.append((len(b_body), 'EOF'))
print('%-46s %7s %7s' % ('B section', 'words', 'tables'))
print('-' * 64)
for (i, name), (j, _) in zip(secs, secs[1:]):
    seg = b_body[i:j]
    print('%-46s %7d %7d' % (name[:46], len(re.findall(r'\b[\w-]+\b', seg)),
                             len(re.findall(r'^\*\*Table ', seg, re.M))))
