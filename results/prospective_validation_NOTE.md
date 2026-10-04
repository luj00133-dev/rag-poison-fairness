Prospective validation of the per-group recommendation: attempted, and not achievable
with the committed data. Recorded so it is not attempted again.

WHAT WAS ASKED
Validate prospectively that monitoring per-group quantities detects pairwise poisoning where
the aggregate statistics do not.

WHAT WAS TRIED, AND WHY EACH FAILED

1. Single-query threshold monitors on per-group levels (analysis/prospective_validation.py).
   Every monitor came out at chance: aggregate gap AUC 0.484 on the held-out corpus, best
   per-group 0.543. The construction was wrong, and the failure is instructive: the per-query
   dispersion of a per-group level is sd 0.43 while the attack moves its mean by 0.13, so a
   query's topic dominates its level and a single-query outlier rule cannot see the effect.

2. Paired monitors against each query's own clean run
   (analysis/prospective_validation_v2.py). This produced the opposite of the paper's claim --
   aggregate gap AUC 0.921 against per-group levels at 0.897 and 0.883 -- which prompted the
   check that explains it.

THE BLOCKER: THE LABELS ARE DEGENERATE
`results/*/per_query.csv` carries two candidate ground truths and neither supports a
detection experiment:

  * generation layer, `n_poison_in_context`: 0 for every clean query and 5 for every poisoned,
    r1only and r2both query, on both corpora. Detecting it is detecting the experimental
    condition, so any monitor scores well and the comparison means nothing. The AUC 0.921
    above is an artefact of this.
  * retrieval layer, `poison_in_topk`: a monotone function of the injected rate (0.69 at
    rho = 0.1%, 0.75 thereafter), i.e. a measure of attack STRENGTH, not of attack EFFECT.
    Supervising on it asks whether the monitor can recover the attacker's own parameter, not
    whether it can tell a shifted answer from an unshifted one.

WHAT THE PAPER CAN CLAIM INSTEAD, AND ALREADY DOES
The claim the data does support is about where the signal sits, not about detector
performance, and the same numbers demonstrate it (controlled corpus, qwen-turbo):

    condition   g1       g2       gap
    clean      +0.132   +0.180   0.310
    poisoned   +0.002   +0.310   0.311

The aggregate gap is invariant (0.310 -> 0.311) while the per-group levels relocate by 0.13
each way, and the paired permutation test the paper already reports puts that relocation at
p <= 0.0035. That is the positive control for the per-group signal; it is not a claim that a
deployed monitor would catch the attack.

WHAT A REAL VALIDATION WOULD REQUIRE
A label that is deployment-observable and not the condition itself: for instance a graded,
query-level measure of how far the retrieved evidence was relocated, assigned independently
of the monitor under test. Producing one means new runs whose design fixes the label before
any monitor is scored. That is a new experiment, not a reanalysis, and it is listed as future
work rather than claimed here.
