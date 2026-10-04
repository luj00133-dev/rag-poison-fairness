The balanced-but-partial regime exists, but only in a narrow window with a small yield

WHAT WAS ASKED, AND THE ANSWER

Design an attack that is balanced across groups (so the aggregate statistic is blind) while
only partially successful per query (so the retrieval-side label is graded and the validation
has something to test).

The answer, after seven configurations and about two hours of retrieval compute: the regime
exists, and it exists ONLY for the graded injection at align_strength 0.25 on the st retriever
with the lexical attack. Measured on the undefended cell, counting queries whose label is
partial AND whose drift_tv is exactly zero:

    run        attack                    grading                        partial  bal+part
    pv_graded2 template                  ungraded, strength 1.0              12         0
    pv_graded3 template                  graded, strength 0.25               36        36
    pv_bal_a   template                  graded, strength 0.10                0         0
    pv_bal_b   template                  graded, strength 0.05                0         0
    pv_bal_c   template_plus_projection  graded + projection, strength 0.25   0         0
    pv_graded  template_plus_projection  graded + projection, strength 1.0    0         0

So grading is NECESSARY (ungraded gives 12 partial but 0 balanced) and 0.25 is ESSENTIAL
(0.10 and 0.05 collapse to all-or-nothing, reintroducing the original degeneracy). Projection
remains impossible to grade at any strength, because it sets the ranking from vectors and
overrides passage text.

WHY THE YIELD IS THE BINDING CONSTRAINT

The single working cell holds 36 balanced-and-partial queries across four strata. The paper's
group favourable rate is an average of binary votes over a stratum -- a batch statistic -- so
estimating it needs many batches, and the replica-level validation built earlier produced
bootstrap intervals that include zero for both group rates (fav_g1 +0.170 [-0.002, +0.343],
fav_g2 +0.096 [-0.042, +0.251]) while the aggregate gap moved significantly
(-0.266 [-0.443, -0.078]). With 36 queries that contrast cannot be tightened.

The reason the yield is small is now clear and is a property of the construction: align_strength
has to place the alignment gradient's RANGE across the retrieval boundary. At 0.25 it does and
36 queries land on the boundary; at 0.10 and 0.05 the whole injected set falls below the
boundary and nothing is retrieved; at 1.0 the whole set rises above it and everything is
retrieved. The window is narrow because the gradient is linear while the boundary is sharp.

WHAT WOULD ACTUALLY DELIVER ENOUGH QUERIES

Not more tuning of the same knob, which the sweep above shows collapses on both sides. Either:

  * an injection whose per-passage strength is distributed around the boundary rather than
    spread linearly across it, so a substantial fraction of queries land on the boundary
    rather than a sliver; or
  * a much larger query set at the working setting (0.25), since the balanced-and-partial
    yield is about 36 per 192 attacked queries, i.e. 19%; roughly 1,500 attacked queries would
    give ~280 in the regime; or
  * repeated independent query sets per (stratum, condition) cell, which raises the power of
    the batch statistic without needing new strata -- and is the cheapest of the three, since
    it needs no new attack construction at all.

The third option is the one worth doing first: it uses the configuration already shown to work
and attacks the actual limiting factor, which is batch count rather than construction.
