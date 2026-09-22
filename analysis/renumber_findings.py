"""Resolve the Finding-number collision introduced by the new encoder-scale
section.

Order of appearance in the manuscript is now:
    5.1..5.5  -> Findings 1-7
    5.6 (new) -> was 8, 9   (encoder scale, R1 inertness at scale)
    5.7       -> was 8, 9, 10 (generation stage)

Findings are read in document order, so the generation-stage ones keep their
existing numbers (which other text already cites as 8/9/10 in context) and the
new encoder-scale pair moves to the end of the sequence as 10 and 11. The R1
inertness finding is a direct extension of Finding 6, so it is labelled 6b
rather than taking a new slot.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

subs = [
    # the scale finding becomes the last one in the sequence
    ('**Finding 8. Text-attack susceptibility is a per-checkpoint property',
     '**Finding 10. Text-attack susceptibility is a per-checkpoint property'),
    # inertness at scale is an extension of Finding 6, not a new claim
    ('**Finding 9. The R1 constraint remains inert at large scale.**',
     '**Finding 6b. The R1 constraint remains inert at large scale.**'),
    ('Table 12 extends the \u00a75.2 inertness check',
     'Table 12 extends the \u00a75.2 inertness check'),
]
for old, new in subs:
    n = s.count(old)
    s = s.replace(old, new)
    print('%d replacement(s): %s' % (n, old[:60]))

io.open(P, 'w', encoding='utf-8').write(s)

print()
print('Finding labels in document order:',
      re.findall(r'\*\*Finding (\d+[a-z]?)\.', s))
print('table captions:', len(re.findall(r'^\*\*Table \d+\.', s, re.M)))
