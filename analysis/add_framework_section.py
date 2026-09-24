"""Add the organising framework: one form for all candidate metrics, and a
taxonomy of the three ways an aggregate statistic loses the signal.

The paper currently reports three measurement failures as separate results --
composition statistics that count what the attack balances, reference-based stance
statistics that measure topic rather than stance, and absolute differences that
cancel a joint relocation. Each is correct, and each was found separately. Read
together they are one thing: every metric in this literature is an aggregate of
group-level quantities, and an adversary who knows that can defeat the aggregation
in exactly three ways.

Stating that as a framework does three things the current text does not:
  * it makes the contribution general rather than a list of case studies, which is
    what a reviewer weighs when deciding whether a negative result is a paper;
  * it tells a reader which existing metric is exposed to which failure, which is
    immediately actionable;
  * it makes each failure *predictable* rather than observed, so the observations
    become confirmations of a stated model rather than the model itself.

Nothing here is a new experiment. It is the same measurements, organised.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

SECTION = r'''### 3.4 One form for every candidate metric, and three ways it loses the signal

Every fairness statistic in this literature, including the ones we introduce, has the same shape: a per-group quantity aggregated across groups.

$$M(\mathcal{D}) \;=\; A_{g \in \mathcal{G}}\bigl[\,\phi_g(\mathcal{D})\,\bigr] \tag{2}$$

where $\phi_g(\mathcal{D})$ is some per-group measurement — the share of group-relevant passages belonging to $g$, the proportion of those passages that are favourable, the exposure of $g$'s items — and $A$ is an aggregation over groups (a count, a deviation from a reference, a difference, a variance). R1 statistics take $\phi_g$ to be a composition and $A$ to be a deviation or a count; R2 statistics take $\phi_g$ to be a stance proportion and $A$ to be a deviation, a difference or an extremeness.

This form is useful because it exposes exactly where an adversary can act. An attack on a fairness metric has two available moves and only two: leave the aggregate $A$ where it is while moving $\phi_g$, or move $A$ in a direction the defender reads as harmless. Every attack we study does the first. The consequence is a taxonomy of three failure modes, and they are the reason the experiments in §5 come out as they do.

| Failure mode | Mechanism | Which $A$ is exposed | Where we observe it |
|---|---|---|---|
| **F1 — balanced count** | The injection contributes equally to every group, so any aggregate over group counts returns its clean value | any count or share across groups | §5.1, §5.2 (R1 statistics) |
| **F2 — preserved nuisance** | A statistic is anchored to a reference the attack does not change, so it reports the component that varies with the query rather than the one that varies with the attack | any deviation from a reference | §3.2, §5.1 (`stance_div`, `stance_onesided`) |
| **F3 — cancelled shift** | The attack relocates all groups in the same direction, so a difference between groups is unchanged even though every $\phi_g$ moved a long way | any difference, variance or gap across groups | §5.1, §5.7 (`stance_gap` and its generation-layer twin) |

**The taxonomy is a test, not a description.** For a candidate statistic $M$, the three failure modes correspond to three questions that can be asked before any attack is built:

1. *Does the injection balance the quantity $M$ counts?* If the attacker's construction is symmetric across groups — and pairwise poisoning is, because it reuses the legitimate template inventory in matched pairs — then any counting aggregate is invariant by construction and no amount of data will show the attack.
2. *Is $M$ referenced to something the attack preserves?* If the reference is a per-query clean retrieval or a corpus-level rate, the attack leaves it intact by design, and $M$ measures the query's topic rather than the attacker's skew.
3. *Is $M$ an aggregate that cancels a common-mode movement?* A difference or variance across groups is invariant under $g \mapsto g + c$ for every group at once. An attack that moves all groups together is therefore invisible to it, no matter how large the movement.

A statistic that survives all three is, in our setting, one that reports **per-group levels** rather than a difference between them, because that is the only form that is not invariant under at least one of the three moves. §5.1 and §5.7 test this prediction: on the same retrieval conditions where a difference statistics reports a change of 0.002, the per-group levels move by 0.13 and the paired test rejects at $p < 0.01$. The prediction was made from the form of the statistic, not fitted to those numbers, and §8 records that we violated it ourselves in an earlier version of the generation-layer analysis.

**What the taxonomy does not claim.** It is not a claim that no fairness metric can be robust. It is a claim about the class of statistics that appear in this literature, all of which are aggregates of the form (2), together with a constructive statement of what escapes the three modes: report $\phi_g$ for each $g$, and report how each moves. That recommendation is cheap, it is what §5.7 does, and it is the difference between detecting the attack and not.

'''

# insert before section 4
anchor = '## 4. Attack and Evaluation Setup'
assert s.count(anchor) == 1, s.count(anchor)
s = s.replace(anchor, SECTION.rstrip() + '\n\n---\n\n' + anchor)

io.open(P, 'w', encoding='utf-8').write(s)
print('section 3.4 added (%d chars)' % len(SECTION))
print('paper length: %d chars' % len(s))
