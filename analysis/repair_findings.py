"""Repair three defects from the 5.5/5.6 compression.

1. Tables 13 and 14 appear in the wrong order: the generation-stage table was
   renumbered to 13 but sits *after* the historical forced-choice table, which
   kept 14. Swapping the numbers fixes the reading order.

2. Three numbered Findings lost their labels in the rewrite. Their *content* is
   present -- the sparsity account, the R1-constraint inertness across encoders,
   and the non-monotonicity of susceptibility in scale are all still argued in
   the prose -- but without the "Finding N." marks they are no longer findable by
   the cross-references that cite them (the README's findings table, the
   contributions list, and other sections). Re-labelling is the fix; the claims
   themselves are unchanged.

   This is the failure mode of compression by replacement rather than by editing:
   prose survives, structure does not. check_refs.py did not catch it because it
   verifies that references resolve, not that labelled objects still exist.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

# --- 1. table order --------------------------------------------------------- #
s = s.replace('**Table 14.** The first generation-layer measurement',
              '**Table @@A@@.** The first generation-layer measurement')
s = s.replace('**Table 13.** Generation-layer stance, entailment-scored',
              '**Table @@B@@.** Generation-layer stance, entailment-scored')
s = s.replace('**Table @@A@@.**', '**Table 14.**')
s = s.replace('**Table @@B@@.**', '**Table 13.**')
print('table order: 13 then 14')

# --- 2. restore the Finding labels ------------------------------------------ #
patches = [
    # sparsity account, formerly Finding 7
    ('**Sparsity, not "neuralness", predicts susceptibility at a fixed size.**',
     '**Finding 7. Sparsity, not "neuralness", predicts susceptibility at a fixed '
     'size, but it is a correlate rather than a law.**'),
    # R1 inertness across encoders and scales, formerly Finding 6b
    ('In all sixteen constrained configurations the difference is exactly zero.',
     '**Finding 6b. The R1 constraint is inert across every encoder and at every '
     'scale tested.** In all sixteen constrained configurations the difference is '
     'exactly zero.'),
    # non-monotonicity in scale, formerly Finding 11
    ('**Scaling does not close the spread, and it is not monotone.**',
     '**Finding 11. Susceptibility is not monotone in encoder scale, and scaling '
     'can destroy resistance entirely.**'),
]
for old, new in patches:
    c = s.count(old)
    assert c == 1, (c, old[:60])
    s = s.replace(old, new)
    print('restored: %s' % new[:52])

io.open(P, 'w', encoding='utf-8').write(s)

print()
print('findings now: %s' % ' '.join(re.findall(r'\*\*Finding (\d+[a-z]?)\.', s)))
print('tables now  : %s' % ' '.join(re.findall(r'^\*\*Table (\S+?)\.\*\*', s, re.M)))
print('length: %d chars' % len(s))
