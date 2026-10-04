The balanced-but-partial regime: where it exists and where it does not

THE DESIGN QUESTION

The prospective validation needs one configuration that is simultaneously

  (a) balanced across groups, so the R1 composition statistic is unmoved, giving the paper's
      "aggregate is blind" condition; and
  (b) only partially successful per query, so the retrieval-side label is graded rather than
      all-or-nothing, giving something to validate against.

The original construction could not do both, and neither could the uniform injection. This note
records where the combination actually occurs, established by measurement rather than reasoning.

WHY THE ORIGINAL CONSTRUCTION FAILED AT (b)

The injection count is uniform per stratum (poison_count_for) and every poisoned passage carried
the same constant ALIGN string, so the injected passages had near-identical retrieval strength
and crossed the retrieval boundary as a block. Every attacked query was therefore either fully
contaminated or untouched: the generation runs were exactly {0:144, 5:432} and {0:192, 5:576}.

WHERE (a) AND (b) BOTH HOLD

Measured across every committed run, the relation between the R1 statistic (drift_tv) and the
retrieved adversarial fraction (poison_share), for undefended cells, splits cleanly by retriever:

  * on the st retriever with the lexical attack, drift_tv is 0.0000 at EVERY partial label level;
  * on bm25, dense and splade, drift_tv rises monotonically with poison_share, because retrieval
    there moves group composition rather than relocating both groups evenly.

The st / template cell in the graded run, which is the configuration to build on:

    share   n    drift_tv mean   drift_tv max
    0.0     96   0.0000          0.0000
    0.4     12   0.0000          0.0000     <- balanced AND partial
    0.6     12   0.0000          0.0000     <- balanced AND partial
    0.8     12   0.0000          0.0000     <- balanced AND partial
    1.0     60   0.2400          0.8000

Ten cells across the repository were found where drift at partial levels does not exceed clean:
align_ctl, align_e5, align_gte_ad, st_gte, verify (bm25), full and repro_check (dense), pv_mild
and pv_graded3 (st). None of them existed before the graded injection except the ones inherited
from earlier alignment runs, and none carries enough partial queries to validate on yet.

A CORRECTION TO AN EARLIER CLAIM IN THIS PROJECT

results/validation_graded_NOTE.md states as "the crux" that the attack making the aggregate
blind is necessarily the attack that saturates the label. That is too strong and is corrected
here: it holds for bm25/dense/splade, where partial retrieval moves composition, but NOT for the
st retriever with the lexical attack, where partial retrieval leaves composition exactly
balanced. The two requirements are in tension on some retrievers, not in principle.

WHAT IS STILL MISSING

Power, not construction. At align_strength 0.25 the balanced-and-partial regime holds 36 queries
across four strata. The paper's group favourable rate is an average of binary votes over a
stratum, so estimating it needs many batches; the validation therefore needs several hundred
queries in the partial regime. The tuning runs pv_bal_a (align_strength 0.10) and pv_bal_b
(0.05) test whether lowering the alignment strength moves queries out of saturation and into
that regime without reintroducing drift.
