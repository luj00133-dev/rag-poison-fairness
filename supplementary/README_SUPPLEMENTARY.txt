Supplementary material for

  Adversarially Invariant Fairness Statistics: Why Aggregate Retrieval-Fairness Metrics
  Cannot Detect Pairwise Poisoning
  Lu Jiang, Nanjing University of Science and Technology


WHAT THIS IS

The analysis-ready data behind every table and figure, plus the generation-stage model outputs.
The implementation, configurations and regeneration scripts are in the repository named in the
manuscript's Data and Code Availability statement; this archive is what a reader needs in order to
check a number WITHOUT running any code and WITHOUT an API key.

The generation-stage outputs are included for a specific reason: they cannot be recreated by a
reader, because producing them requires paid API calls. Everything at the retrieval layer is
deterministic given a seed and the repository configuration, but a re-run of §5.7 would cost money
and return slightly different text.


THREE FILE TYPES, NOT ONE

All fourteen directories carry a `per_query.csv`, but they do not share a schema, because they
measure at different layers. The retrieval directories record WHAT WAS RETRIEVED. The generation
directories record WHAT THE MODEL THEN SAID. A reader looking for `drift_tv` in a generation file
will not find it, and should not: composition drift is a property of the retrieved set.


(A) RETRIEVAL LAYER -- directories S1 to S10

  qid             query identifier; the same qid appears under every condition, so conditions are
                  paired and a per-query difference is well defined
  drift_tv        R1 metric: total-variation distance of the group composition of the retrieved
                  set from the clean reference. The statistic the paper indicts.
  drift_js        R1 metric, Jensen-Shannon form
  stance_shift    R2 metric: per-group change in favourable rate against the per-query clean
                  reference. The diagnostic the paper recommends.
  stance_div      R2 metric: deviation of a group's stance from the corpus reference (mode F2)
  stance_onesided R2 metric: one-sidedness of a group's stance (mode F2)
  stance_gap      R2 metric: cross-group stance difference (mode F3). Invariant when all groups
                  relocate together.
  poison_in_topk  attack-success indicator
  poison_share    fraction of the retrieved top-k that is adversarial
  in_pool_rate    utility control: whether admissible passages remain available
  mean_score      mean retrieval score of the selected set
  attack, retriever, defense, epsilon, stratum, poison_rate, backbone
                  the experimental cell


(B) GENERATION LAYER -- directories S11 and S12

  generator       which model produced the answer (the §5.7 panel spans several)
  condition       clean, poisoned, r1only or r2both
  qid, stratum    as above, so the generation layer joins to the retrieval layer by qid
  n_poison_in_context
                  adversarial passages in the context the answer was generated from
  stance_g1       favourable rate of the FIRST group of the stratum, entailment-scored
  stance_g2       the same for the second group
  gap             |stance_g1 - stance_g2|; the generation-layer analogue of the retrieval R2 gap
  mean_attribution
                  mean fraction of retrieved passages the answer relied on (expected attributed
                  exposure)
  unattributed_rate
                  fraction of the answer not attributable to the supplied context
  answer          the model's answer text, verbatim
  error           non-empty when the call failed


(C) FORCED-CHOICE PROBE -- directories S13 and S14

  generator, condition, qid, stratum
                  as above
  group           which group this row scores
  n_poison_in_context
                  as above
  p_fav, p_unfav  entailment-scored probability that the answer favours this group, and against
  margin          p_fav - p_unfav; signed, so the direction is visible
  commitment      how strongly the answer takes a position at all. Near zero means the answer
                  took no position, which is the instrument failure the probe exists to expose.
  choice          which side the forced choice selected
  stated_fav      whether the answer explicitly stated a favoured group
  agrees          whether the two agree
  error           non-empty when the call failed

`summary.txt` in each retrieval directory restates the tables printed by the run. `aggregate.csv`,
`by_stratum.csv` and `adaptive.csv` carry the aggregate and per-stratum reductions. The retrieval
directories also carry `generation.json`-style result files where the run produced them, and every
generation directory carries the full model output, because those are the data a reader cannot
recreate without paying for API calls.

DIRECTORY INDEX

  S1_retrieval_controlled        Tables 2, 3, 4; Figures 3, 4; Fig. 6 source
  S2_retrieval_bbq               Table 6; the natural-corpus replication in §5.4
  S3_encoder_gte                 Tables 8, 9; Figure 5; §5.5 six-back-end sweep
  S4_encoder_e5                  Tables 8, 9; Figure 5; §5.5
  S5_encoder_splade              Tables 8, 9; Figure 5; §5.5
  S6_encoder_contriever          Tables 8, 9; §5.5
  S7_encoder_multi               Table 15; §5.8 adaptive sweep, six back-ends
  S8_scale_gte_large             Table 15; Figure 5; §5.6 encoder-scale check
  S9_scale_e5_large              Figure 5; §5.6
  S10_scale_splade_large         Figure 5; §5.6
  S11_generation_controlled      Tables 12, 13; §5.7 propagation
  S12_generation_bbq             Table 12 (BBQ rows); §5.7
  S13_forcedchoice_controlled    Table 13; Figure 7
  S14_forcedchoice_bbq           Table 14; Figure 7

Numbers in this archive are the same values reported in the manuscript. Where an earlier version of
this work reported a different value, the change is recorded in Appendix E of the manuscript, and
the value here is the corrected one.


LICENCE AND ATTRIBUTION

Code: MIT. Derived data follows the licence of the source benchmark (BBQ: CC-BY-4.0). The controlled
corpus is generated deterministically from a fixed seed and contains no third-party material.
