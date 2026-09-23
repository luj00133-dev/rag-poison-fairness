"""Quantify the overlap between Paper A and Paper B.

Merging the two is a real option, and the answer depends on how much of Paper B
is already inside Paper A. Measuring it is cheap; guessing at it is what we have
been doing.
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PA = os.path.join(ROOT, 'paper', 'manuscript_R1R2_v1.md')
PB = os.path.join(ROOT, 'paper', 'manuscript_B_adaptive_v1.md')

a = io.open(PA, encoding='utf-8').read()
b = io.open(PB, encoding='utf-8').read()

print('lengths')
print('  Paper A : %7d chars, %2d tables, %2d findings, %2d refs'
      % (len(a), len(re.findall(r'^\*\*Table ', a, re.M)),
         len(re.findall(r'\*\*Finding \d', a)),
         len(re.findall(r'^\[\d+\]', a, re.M))))
print('  Paper B : %7d chars, %2d tables, %2d findings, %2d refs'
      % (len(b), len(re.findall(r'^\*\*Table ', b, re.M)),
         len(re.findall(r'\*\*Finding \d', b)),
         len(re.findall(r'^\[\d+\]', b, re.M))))
print('  merged  : %7d chars' % (len(a) + len(b)))


def ref_titles(s):
    out = []
    for m in re.finditer(r'^\[(\d+)\]\s+(.+)$', s, re.M):
        out.append(re.sub(r'\s+', ' ', m.group(2)).strip())
    return out


ta = ref_titles(a)
tb = ref_titles(b)


def key(t):
    """Match on author-year prefix: citation styles differ between the papers."""
    return t[:40]


ka = set(key(t) for t in ta)
kb = set(key(t) for t in tb)
shared = ka & kb
print()
print('bibliography')
print('  Paper A refs: %d   Paper B refs: %d   shared: %d'
      % (len(ta), len(tb), len(shared)))
print('  Paper B unique:')
for t in sorted(kb - ka):
    print('     %s' % t[:88])


def section_titles(s):
    return [m.group(1).strip() for m in re.finditer(r'^##+ (.+)$', s, re.M)]


print()
print('Paper B sections and whether Paper A has an equivalent')
a_low = a.lower()
for t in section_titles(b):
    probe = t.lower().split(':')[0].strip()
    words = [w for w in re.findall(r'[a-z]{5,}', probe)]
    hit = any(w in a_low for w in words) if words else False
    print('  %-58s %s' % (t[:56], 'topic appears in A' if hit else '-- unique --'))
