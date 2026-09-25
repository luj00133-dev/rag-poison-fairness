"""Compare Paper A's adaptive-attack material with Paper B's, section by section.

The merge decision turns on how much of B's experiment section repeats what A already
reports. A has §5.6 "Adaptive attacker: no defense survives an informed adversary" and §6
"Why distribution-level defense has a limit"; B has §4 (why randomised defense cannot be
robust), §5.2/5.2b/5.3/5.4 (experiments) and §6 (a reporting protocol).

This prints the opening of each relevant section from both papers side by side, so the
overlap can be judged from the text rather than assumed.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
B = os.path.join(P, 'paper', 'manuscript_B_adaptive_v1.md')

WANT_A = ['Adaptive attacker', 'Why Distribution-Level']
WANT_B = ['Why Randomised', 'Static ranking inverts', 'Collapse abruptness',
          'penalty is the attacker', 'What retains benefit', 'A Reporting Protocol']


def sections(path, wants, n=1100):
    s = io.open(path, encoding='utf-8').read()
    s = s[:s.rfind('\n[1] ')] if '\n[1] ' in s else s
    marks = [(m.start(), m.group(2)) for m in re.finditer(r'^(#{2,3}) (.+)$', s, re.M)]
    marks.append((len(s), 'EOF'))
    for (i, name), (j, _) in zip(marks, marks[1:]):
        if any(w.lower() in name.lower() for w in wants):
            yield name, s[i:i + n]


print('=' * 100)
print('PAPER A')
print('=' * 100)
for name, body in sections(A, WANT_A):
    print('\n### %s' % name)
    print(' '.join(body.split())[:900])
    print('   [...%d chars total]' % len(body))

print()
print('=' * 100)
print('PAPER B')
print('=' * 100)
for name, body in sections(B, WANT_B):
    print('\n### %s' % name)
    print(' '.join(body.split())[:900])
    print('   [...%d chars total]' % len(body))
