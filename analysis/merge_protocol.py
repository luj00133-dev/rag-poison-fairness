"""Merge Paper B's reporting protocol into Paper A's conclusion.

Paper A's protocol covers measurement validity; Paper B's covers adversarial
evaluation hygiene (state the threat model, sweep to failure, include a
utility-preserving baseline, assume a randomised defense's distribution is known,
treat an observable penalty as the attacker's constraint). They are complementary
and neither paper had both, so the merged list is what a reader should be left
with. Overlapping points are folded rather than duplicated.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

OLD_START = 'We close with the protocol the results imply'
OLD_END = 'We have reported an exploratory provenance'
i = s.find(OLD_START)
j = s.find(OLD_END)
assert i != -1 and j != -1 and j > i

NEW = r'''We close with the protocol the results imply. The first four points are about **measurement validity** — whether a statistic can see the attack at all — and the last five about **adversarial evaluation hygiene**, which is what makes a robustness claim interpretable:

1. **Measure per-group shifts, not cross-group differences.** An absolute gap between groups is dominated by pre-existing corpus asymmetry and is blind to an attack that relocates both groups together. Report both group-level quantities, and report the change in each.
2. **Report injection as a rate, not a count.** A fixed passage count measures corpus size rather than attack strength, and produced a spurious conclusion in our own earlier experiment.
3. **Report the encoder as a factor.** Susceptibility is a per-checkpoint property that is not monotone in encoder size — within one family and training recipe, scaling GTE raised text-attack success eight-fold while scaling E5 lowered it to zero. A single-encoder robustness claim reports an unmeasured property of that checkpoint.
4. **Give equivalence bounds for null claims.** "No effect detected" and "no effect" are different claims, and only the second supports a conclusion about a defense family. Where the per-query difference is identically zero this is easy and conclusive; where it is not, the bound is the honest statement.
5. **State the threat model explicitly, including whether the attacker knows the defense.** A robustness claim without this qualifier is uninterpretable, and the qualifier is what separates the two evaluations in §5.2.
6. **Report adversarial inclusion as a function of attacker strength, not at a single operating point.** One value cannot distinguish a robust defense from one evaluated below its failure threshold. In our sweep every defense fails by $\lambda \le 2$; a sweep stopping at $\lambda = 0.25$ would have shown three apparently robust defenses.
7. **Report a utility-preserving baseline.** A defense can achieve low adversarial inclusion trivially by returning fewer or worse passages, which is why §5.2 reports `in_pool_rate` alongside `poison@k`.
8. **For a randomised defense, state the distribution and assume it is known.** Report the attacker's optimal response to the expectation rather than to a sample; by Proposition 4, randomisation bounds variance and not the expectation.
9. **For a penalty-based defense, report whether the penalty is computable from public information.** If it is, treat it as a constraint in the attacker's optimisation rather than as an unknown; by Corollary 2 that is the difference between a cost and a barrier.

Point 9 is the one most easily overlooked and, in our experiments, decisive for the defense that looked strongest statically. Point 5 is the one most often omitted in this literature. We suggest that points 1–4 are prerequisites for a fairness statistic to be reported at all under adversarial conditions, and points 5–9 for a robustness claim to be credited.

'''

s = s[:i] + NEW + s[j:]
io.open(P, 'w', encoding='utf-8').write(s)

import re
print('protocol points now: %d' % len(re.findall(r'^\d+\. \*\*', NEW, re.M)))
print('paper length: %d chars' % len(s))
