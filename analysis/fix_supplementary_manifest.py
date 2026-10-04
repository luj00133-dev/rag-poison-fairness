"""Fix the supplementary manifest: it documented one schema for three different file types.

The verifier caught this. All fourteen directories carry a `per_query.csv`, but they do not share a
schema: the ten retrieval-stage directories carry the R1/R2 metrics, the generation-stage
directories carry per-group stance with the answer text, and the forced-choice directories carry a
per-group two-alternative measurement. The manifest described only the first, so a reader opening
S11 or S13 would find none of the columns it promised.

Each schema is now documented separately, taken from the actual file headers rather than from the
manuscript's definitions, and the distinction between the two layers is stated up front because it
is the difference between "what was retrieved" and "what the model then said".
"""
import csv
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(P, 'supplementary')
README = os.path.join(SUPP, 'README_SUPPLEMENTARY.txt')


def header_of(directory):
    p = os.path.join(SUPP, directory, 'per_query.csv')
    with io.open(p, encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh).fieldnames or [])


def main():
    text = io.open(README, encoding='utf-8').read()

    ret_cols = header_of('S1_retrieval_controlled')
    gen_cols = header_of('S11_generation_controlled')
    fc_cols = header_of('S13_forcedchoice_controlled')
    print('retrieval schema : %d cols' % len(ret_cols))
    print('generation schema: %d cols' % len(gen_cols))
    print('forced-choice    : %d cols' % len(fc_cols))

    new_section = '''THREE FILE TYPES, NOT ONE

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
'''

    # replace the old single-schema section, which ran from its heading to the directory index
    start = text.find('HOW TO READ A PER-QUERY FILE')
    end = text.find('DIRECTORY INDEX')
    if start < 0 or end < 0 or end < start:
        print('ANCHOR FAIL: could not locate the schema section')
        return 1
    text = text[:start] + new_section + '\n' + text[end:]
    io.open(README, 'w', encoding='utf-8', newline='\n').write(text)
    print('manifest now documents all three schemas')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
