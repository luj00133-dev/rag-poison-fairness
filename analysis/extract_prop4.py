"""Insert the extracted structural argument from Paper B into Paper A as section 6.5.

Paper B's Proposition 1 (randomised defense under a known distribution) and its
two corollaries are absent from Paper A, and they cover the non-compositional
members of the defense family that Propositions 1-3 do not reach. Placing them
after the trilemma lets the trilemma stand as the composition-constraint case of
a broader statement, which is why they go here rather than in a section of their
own.

Renumbering, done in one pass to avoid the off-by-one that a two-step edit
invites:
    old 6.5 (dimensionality / detection)  ->  6.6
    new 6.5 (Proposition 4)               ->  inserted before it
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

OLD_65 = ('### 6.5 Dimensionality does not help, and the only escape is '
          'individual-level evidence')
assert s.count(OLD_65) == 1, s.count(OLD_65)

NEW = r'''### 6.5 Proposition 4 — why the family is *structurally* exposed, not merely mis-tuned

Propositions 1–3 show that a distribution constraint cannot exclude the injection. A reader may reasonably ask whether that is a property of *composition* constraints specifically, or of this defense family more broadly — and in particular whether the non-compositional members, which the literature presents as the more robust alternatives, escape it. They do not, and the reason is worth stating separately because it covers the family as a whole.

**Proposition 4 (randomised defense under a known distribution).** Let a defense's selection mechanism be a fixed distribution $\pi(\mathcal{D} \mid q, \mathcal{C})$ over retrieved sets, public to the attacker, and let $U(\mathcal{D})$ be the attacker's utility (e.g. the indicator that $\mathcal{D}$ contains an injected passage). If any set in the support of $\pi$ has $U = 1$, the attacker can drive $\mathbb{E}_{\pi}[U] \to 1$ by choosing an injection that places adversarial passages in every set with non-negligible probability mass.

*Proof sketch.* Since $\pi$ is fixed and known, $\mathbb{E}_\pi[U]$ is computable in closed form as a function of the injection, and the attacker maximises it by search or by gradient. Randomisation does not bound $\mathbb{E}_\pi[U]$; it bounds the *variance* of $U$ across realisations. An attacker whose success is measured in expectation over queries — the usual case — is indifferent to that variance. $\square$

The proposition is elementary, and that is the point: **randomisation defends against unpredictability, not against knowledge.** Two corollaries identify the cases that arise in this literature.

**Corollary 1 (public-distribution defenses).** Multi-query consistency [4] perturbs the query by token dropout at rate $\delta$ and aggregates over $n_v$ variants. The perturbation is random, but its *rate* and its *count* are public constants, so the expected aggregate score of a passage is a deterministic, differentiable function of the injected embedding which the attacker can maximise directly. Adding variants does not change this: the attacker optimises the expectation, and with many variants the empirical mean converges to it. The adaptive sweep reports the predicted collapse, from 0.729 at $\lambda = 0$ to 1.000 by $\lambda = 0.5$.

**Corollary 2 (penalty-observable defenses).** A defense that down-weights passages by a penalty $f(d)$ computable from public information hands the attacker the constraint "remain in the low-penalty region". Whenever that constraint can be satisfied while raising similarity — possible whenever the penalty is a continuous function of a perturbation the attacker controls — the defense imposes a *cost* rather than a *barrier*. Off-manifold filtering is exactly this case, and the measured consequence is that it is the strongest defense statically (0.250 against 0.750 for no defense) and is defeated by $\lambda = 0.25$.

We do not claim these observations are novel in general; they are the standard reason adaptive evaluation is required, and they are why security venues expect it. The claim is that **this defense family is structurally exposed to them**, because its two dominant mechanisms — public randomisation and an observable penalty — are precisely the two cases the proposition covers. Proposition 3 then explains why the remaining members fail for an independent reason, so the family is squeezed from both sides: composition constraints cannot exclude an individually admissible passage, and the non-compositional alternatives are defeated by an informed attacker. That is why we treat the failure as structural rather than as a matter of tuning, and why the honest remedy is detection (§6.6) rather than a better objective.

### 6.6 Dimensionality does not help, and the only escape is individual-level evidence'''

s = s.replace(OLD_65, NEW)
io.open(P, 'w', encoding='utf-8').write(s)

print('section 6 subsections now:')
for m in re.finditer(r'^### (6\.\d+ .+)$', s, re.M):
    print('  ' + m.group(1)[:78])
