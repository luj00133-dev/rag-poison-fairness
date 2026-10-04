Prospective validation with a graded label: run, and inconclusive on statistical power

WHAT WAS BUILT AND VERIFIED

The injection was redesigned so the retrieval-side label can be graded. The original
construction was structurally binary: the injection count is uniform per stratum
(poison_count_for) and every poisoned passage carried the same constant ALIGN string, so the
injected passages had near-identical retrieval strength and won or lost as a block. PoisonSpec
now takes align_graded, align_strength and align_min_frac, which spread the passages across a
range of alignment strengths. Defaults are off and analysis/verify_injection_noop.py confirms
against an independent replay of the original algorithm that the default path is byte-identical
(6 of 6 passages), so every previously committed number reproduces.

The effect on the label, measured at the retrieval layer on the lexical channel:

    before grading   {0.0: 120, 0.4: 12, 1.0: 60}                  partial  6.3%
    after grading    {0.0: 96, 0.4: 12, 0.6: 12, 0.8: 12, 1.0: 60}  partial 18.8%

Five label levels where there were three. Under template_plus_projection the distribution stays
192/192 full at every gradient setting, because the subspace projection pushes every injected
vector toward the query directions and the ranking then does not depend on passage text -- the
graded injection acts on the lexical channel only.

A LIMIT THAT MISLED AN EARLIER ATTEMPT

The group favourable rate is computed by averaging the binary fc_fav votes across every query
in a stratum (summarise() in src/eval/attribution.py). It is a batch statistic; a single query
contributes one Bernoulli draw. An earlier validation attempt scored per-query monitors by AUC
against the label and found every monitor at chance (aggregate 0.561, per-group 0.500/0.500/
0.462). That result is not evidence against the paper's recommendation, because it measured a
per-query quantity the paper does not propose. Recorded so the same mistake is not repeated.

THE VALIDATION, AT THE LEVEL THE STATISTIC OPERATES ON

Comparing the group rates and the cross-group gap against the retrieval-side label across all
12 stratum-condition cells (analysis/validation_stratum_level.py):

    statistic           correlation with the label
    fav_g1 (per-group)  -0.294
    fav_g2 (per-group)  -0.041
    gap (aggregate)     +0.307

    gap spread across cells      0.854
    fav_g1 spread across cells   0.896

The aggregate is NOT flat here and the per-group rates do not track the label. Neither follows
from the paper's claim being false; the design has too little power to decide either way:

  * the label varies between conditions in only TWO of the four strata (bbq-disability and
    bbq-gender); in stereoset-race it is 0.000 in all three attacked conditions and in
    stereoset-age it is 0.750 in all three, so those cells cannot contribute to any
    correlation at all;
  * four strata times four conditions gives 12 observational units, but only about six of them
    carry label variation;
  * the aggregate is not expected to be blind in this configuration regardless: blindness is a
    property of BALANCED pairwise injection, and this run uses the projection-free lexical
    attack on the st retriever.

SO WHAT IS THE HONEST STATUS

The prospective validation is NOT achieved. What is achieved is that the reason is now
specific and measured rather than suspected: the label can be made graded (done, and verified),
but the paper's statistic is a stratum-level average, so a validation needs many strata or many
repeats per stratum-condition cell, and this corpus supplies four strata. Collecting the
information needed is a data-collection decision, not a further tuning step.

WHAT WOULD ACTUALLY SETTLE IT

  * more strata, so label variation exists in most cells rather than two of four; or
  * repeated independent query sets per (stratum, condition) cell, so each cell's rate carries
    an interval and a slope can be fitted across label levels with proper uncertainty; and
  * a configuration in which the aggregate is expected to be blind, i.e. the balanced
    template_plus_projection attack, which is exactly the attack whose label is saturated --
    which is the tension that has to be resolved by construction rather than by analysis.

That last point is the crux and is worth stating plainly: the attack that makes the aggregate
blind is the attack that saturates the label, and the attack that grades the label is one where
the aggregate is expected to move. Reaching both at once needs an injection that is balanced
across groups while being partially successful per query, which neither the original nor the
graded construction provides.

API cost of this stage: 293 + 210 + 168 = 671 paid calls, about $0.01, all cached and
reproducible.
