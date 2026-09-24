"""Close the discussion on the framework rather than on the specific defenses.

The discussion currently generalises from the failed defense family ("any evaluation
whose statistic aggregates over the quantity an adversary controls is exposed to this
class of error"). That is the right instinct but it arrives after the reader has read
a paper about a specific family. Since section 3.4 now states the three modes and the
results confirm them, the discussion should collect the confirmations in one place
and state what the framework predicts about work we did not run -- which is what
makes it a contribution rather than a summary.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

ANCHOR = '**Limitations.**'
assert s.count(ANCHOR) == 1, s.count(ANCHOR)

NEW = r'''**The three failure modes, and what each one predicts about work we did not run.** §3.4 stated the taxonomy from the form of the statistics; §5 confirmed it on measurements. Collecting the confirmations makes the framework's reach explicit, including for defenses we did not implement.

*F1, balanced count.* Confirmed twice: the R1 statistics are invariant under pairwise injection (§5.1), and the positive control shows the same statistics detect a 3000-passage composition change with the corpus size held fixed (Table 1). So the invariance is a property of the attack, not the instrument. **The prediction for work we did not run**: any defense whose objective is a group count or share — the re-ranking of [5], the proportion adjustment of [6], the embedder control of [7], the exposure equalisation of [8] — inherits this invariance exactly, without regard to how well it is optimised, because the injection is constructed to satisfy whatever composition the defense prefers. Our measurements on re-implementations of that objective support this and we have no reason to expect a different outcome from a better-optimised version of the same statistic.

*F2, preserved nuisance.* Confirmed twice, and the second confirmation is the stronger one: `stance_div` and `stance_onesided` are flat across the clean and fully attacked conditions (§5.1), *and* they are flat across the positive control where the true composition swings from 0.022 to 0.978 (Table 1). A statistic that does not move when the ground truth moves will not move for an adversary either. **The prediction**: any metric anchored to a per-query clean retrieval or a corpus-level rate is measuring the query's topic conditioning, which the attack preserves by construction, so evaluations that report such a metric alongside a clean baseline are reporting a quantity orthogonal to the threat.

*F3, cancelled shift.* Confirmed at two layers, and this is the one we got wrong ourselves: the cross-group gap is blind to the retrieval-layer attack (§5.1) and to the generation-layer attack (§5.7), and on the generation layer our first analysis used it anyway and reported a null. **The prediction**: any difference, gap or variance across groups is invariant under a common-mode move, so a defense or an evaluation that reports only a gap will under-report any attack that relocates groups together rather than separating them — which is what a matched-pair injection does by construction.

The three modes also compose, which is why the defense family fails as a family rather than in parts. F1 accounts for the composition-constrained members; §6.4 proves that no refinement along that axis escapes it. F3 accounts for the non-compositional members that report a group difference. And §6.5 shows the remaining mechanisms — public randomisation and an observable penalty — fail for a fourth reason that is not a measurement failure at all: an informed attacker optimises the expectation of a public distribution, and treats a computable penalty as a constraint rather than a barrier.

**The constructive half.** A taxonomy of failure modes is only useful if something escapes it, and the three modes share one structural feature: each is an invariance of an *aggregation* over groups. Reporting the per-group quantities $\phi_g$ and their paired changes is not invariant under any of the three, because it makes no aggregation claim for the adversary to preserve. That is a cheap change to how a result is reported, it requires no new defense, and §5.7 is an existence proof that it works: on identical retrieval conditions, the aggregated gap moved by 0.002 while the per-group levels moved by 0.13 at $p < 0.01$. The recommendation is therefore not "build a better defense metric" but "stop reporting only the aggregate".

**A caveat we insist on.** The per-group report is more sensitive, and sensitivity is not validity. §5.7 also shows that on the controlled corpus the per-group shift is large and replicates across four generators while on the naturally written corpus it largely disappears, and our negative control attributes that to the controlled corpus's questions presupposing their answers. A more sensitive statistic will report a larger effect on an instrument that manufactures one. Sensitivity without a control is how a measurement paper produces a finding that does not exist, and we report both outcomes rather than the favourable one.

**Limitations.**'''

s = s.replace(ANCHOR, NEW)
io.open(P, 'w', encoding='utf-8').write(s)

print('discussion now closes on the framework')
print('paper length: %d chars' % len(s))
