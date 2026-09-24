"""Insert the four data figures at the sections whose claims they carry.

Placement is chosen so each figure sits beside the argument it supports, rather than
being collected at the front:

  * the responsiveness control goes in 3.4, next to the taxonomy it validates. It is
    the evidence that the indicted statistics are working instruments, so it has to
    be visible where that claim is made.
  * the aggregate-versus-per-group figure goes in 5.7, at the point where the paper
    says the aggregate is blind and the per-group shift is not.
  * R1 inertness goes in 5.2, where the null is stated.
  * the encoder-scale figure goes in 5.5, where non-monotonicity is reported.

Captions carry the explanatory prose that used to be drawn inside the images, so the
text stays editable, searchable and styled by the venue class.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

INSERTS = [
    # (anchor, figure markdown, position: 'before'|'after')
    (
        '**What the taxonomy does not claim.**',
        '![Responsiveness control. Corpus size is held constant at 17{,}792 '
        'passages and passages are swapped between two well-populated groups, so '
        'the retrieval pool and the score threshold do not move and composition is '
        'the only variable. The ground-truth group share changes from 0.500 to '
        '0.978 and back to 0.022; the R1 drift statistics track it monotonically '
        'and in the right direction, while the two reference-based R2 statistics '
        'are flat even here. The indicted statistics are therefore working '
        'instruments that are specifically invariant to an injection balancing '
        'group counts, not unreliable ones.]'
        '(figures/fig_responsiveness.pdf){width=140mm}\n\n',
        'before',
    ),
    (
        '**The absolute cross-group gap — the metric we originally used — is blind '
        'to this effect',
        '![The aggregate statistic against the per-group shifts, on the same '
        'retrieval conditions and the same queries. Left: the change in the '
        'absolute cross-group gap, which stays within $\\pm 0.05$ because the '
        'attack relocates both groups rather than separating them. Right: the '
        'change in each group\'s stance separately, which is large, consistent in '
        'sign and significant for every generator. An asterisk marks $p<0.05$ '
        'under a paired permutation test against the clean condition. Note that '
        'the two panels use different vertical scales: the aggregate moves by less '
        'than 0.002 where the groups move by about 0.13.]'
        '(figures/fig_aggregate_vs_pergroup.pdf){width=140mm}\n\n',
        'before',
    ),
    (
        '**This is a null result, so we state its strength rather than leaving a '
        'reader to guess.**',
        '![R1-constraint inertness. Adversarial-passage inclusion as a function of '
        'the constraint budget $\\varepsilon$, for the strictest ($\\varepsilon=0$) '
        'through the loosest ($\\varepsilon=1$) setting. Every constrained '
        'configuration coincides exactly with the unconstrained baseline -- the '
        'lines are not merely close, the per-query values are identical -- so the '
        'equivalence bound is $\\pm 0.0000$ and the data exclude any effect on '
        'adversarial inclusion rather than an effect above some threshold.]'
        '(figures/fig_r1_inertness.pdf){width=88mm}\n\n',
        'before',
    ),
    (
        '**Finding 11. Susceptibility is not monotone in encoder scale',
        '![Text-attack susceptibility at base and large scale, within each encoder '
        'family and training recipe. GTE and E5 are equally resistant at base size '
        'and move in opposite directions when enlarged: E5 becomes fully resistant '
        '($0.0625 \\rightarrow 0.0000$) while GTE becomes eight times more '
        'susceptible ($0.0625 \\rightarrow 0.5000$). The learned-sparse retriever '
        'is susceptible at both sizes. Since the only variable is the checkpoint, '
        'susceptibility is a per-checkpoint property that cannot be inferred from '
        'architecture, size or representation family.]'
        '(figures/fig_encoder_scale.pdf){width=88mm}\n\n',
        'before',
    ),
]

placed = 0
for anchor, fig, pos in INSERTS:
    if anchor not in s:
        print('ANCHOR NOT FOUND: %r' % anchor[:60])
        continue
    s = s.replace(anchor, fig + anchor, 1)
    placed += 1
    print('inserted figure before %r' % anchor[:52])

io.open(P, 'w', encoding='utf-8').write(s)
print()
print('%d of %d figures placed' % (placed, len(INSERTS)))
print('images in manuscript: %d' % s.count('!['))
