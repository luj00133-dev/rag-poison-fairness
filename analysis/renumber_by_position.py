"""Renumber the body tables authoritatively, by position.

State left by the previous attempt: two captions numbered 4 (the new responsiveness
control and the old defense comparison) and two numbered 12, with 2, 3 and 13
absent. The cause was a collision: inserting the control as "Table 2" created a
second caption with that number before the old "Table 2" had been moved, and the
placeholder pass then gave both the same result.

This does not try to invert that. It assigns numbers by *position* -- the k-th body
caption becomes k -- and rewrites every in-text reference against the number its
target actually holds before the pass. That is idempotent regardless of the starting
state, which the placeholder approach was not.

Appendix tables (B1, C1..C5) are left alone: they are already unambiguous.

Note on method: an earlier pass in this project chained because replacements were
applied one after another, and the "authoritative by position" approach is what
finally worked for the section references. Applying the same discipline here.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

iB = s.find('## Appendix B')

caps = [(m.start(), m.group(1)) for m in
        re.finditer(r'^\*\*Table (\S+?)\.\*\*', s, re.M)]
body = [(p, n) for p, n in caps if p < iB]
print('body captions in order: %s' % ' '.join(n for _, n in body))

# current label -> final label, by position
mapping = {}
for k, (_, n) in enumerate(body, start=1):
    mapping.setdefault(n, []).append(str(k))
print()
for n, targets in mapping.items():
    print('  %-4s -> %s' % (n, ','.join(targets)))

# Build an occurrence-indexed replacement list, then apply it from the END so that
# earlier offsets stay valid. Mutating left-to-right shifts every later offset, which
# is the bug the first version of this script had.
counters = {}
plan = []
for start, n in body:
    idx = counters.get(n, 0)
    counters[n] = idx + 1
    final = mapping[n][idx]
    if n != final or len(mapping[n]) > 1:
        plan.append((start, n, final))

for start, old, final in sorted(plan, reverse=True):
    old_text = '**Table %s.**' % old
    new_text = '**Table %s.**' % final
    assert s[start:start + len(old_text)] == old_text, (
        'offset mismatch at %d: %r' % (start, s[start:start + len(old_text)]))
    s = s[:start] + new_text + s[start + len(old_text):]
print()
print('captions rewritten: %d' % len(plan))

# in-text references: every body reference must point at a real number
known = set(str(k) for k in range(1, len(body) + 1))
appendix = set(n for p, n in caps if p >= iB)
print()
print('valid body numbers now: %s' % ' '.join(sorted(known, key=int)))

# any reference to a number that no longer exists is reported rather than guessed
refs = set(re.findall(r'[Tt]ables? (\d+[a-z]?)\b', s))
missing = sorted((r for r in refs if r not in known and r not in appendix),
                 key=lambda x: int(re.sub(r'\D', '', x) or 0))
print('references to numbers that do not exist: %s'
      % (missing if missing else 'none'))

io.open(P, 'w', encoding='utf-8').write(s)

caps2 = re.findall(r'^\*\*Table (\S+?)\.\*\*', s, re.M)
print()
print('after: %s' % ' '.join(caps2))
