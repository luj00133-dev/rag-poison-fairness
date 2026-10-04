"""Build the supplementary package for submission.

WHAT A SUPPLEMENTARY FILE IS FOR HERE

The paper already deposits the implementation, configurations and regeneration scripts in a
repository. So the supplementary is not a second copy of the code: it is the thing a reviewer needs
in order to CHECK THE CLAIMS WITHOUT EXECUTING ANYTHING AND WITHOUT AN API KEY. That is (a) the
analysis-ready per-query data behind every table and figure, and (b) the generation-stage model
outputs, which could not be recreated by a reviewer at all, because producing them costs API calls
against a paid endpoint.

WHAT WAS EXCLUDED, AND WHY

  * every developmental smoke run (smoke*, chk*, reg*, verify, rate_chk, *_smoke, pv_dry,
    pv_gen_smoke): superseded scratch output, not sources of any reported number;
  * the pv_* prospective-validation runs, which belong to a line of work that did NOT reach the
    paper. Their negative result is recorded in results/*_NOTE.md in the repository, and shipping
    the raw runs would imply a role they do not have;
  * logs, caches, .pkl artifacts and the contaminated-cache backup: build residue;
  * the generation reply cache, which contains raw API traffic and is not needed to check a number.

Each included run keeps ONLY its per-query CSV plus its small summary files, because the per-query
file is what regenerates a table and the logs are not data.
"""
import csv
import io
import os
import shutil

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')
OUT = os.path.join(P, 'supplementary')

# directory -> (new name, what it supports in the manuscript)
INCLUDE = {
    'full':            ('S1_retrieval_controlled', 'Tables 2, 3, 4; Figures 3, 4; Fig. 6 source'),
    'bbq':             ('S2_retrieval_bbq', 'Table 6; the natural-corpus replication in §5.4'),
    'align_gte_ad':    ('S3_encoder_gte', 'Tables 8, 9; Figure 5; §5.5 six-back-end sweep'),
    'align_e5':        ('S4_encoder_e5', 'Tables 8, 9; Figure 5; §5.5'),
    'align_splade':    ('S5_encoder_splade', 'Tables 8, 9; Figure 5; §5.5'),
    'contriever_ad':   ('S6_encoder_contriever', 'Tables 8, 9; §5.5'),
    'align_multi':     ('S7_encoder_multi', 'Table 15; §5.8 adaptive sweep, six back-ends'),
    'align_gte_large': ('S8_scale_gte_large', 'Table 15; Figure 5; §5.6 encoder-scale check'),
    'align_e5_large':  ('S9_scale_e5_large', 'Figure 5; §5.6'),
    'align_splade_large': ('S10_scale_splade_large', 'Figure 5; §5.6'),
    'generation':      ('S11_generation_controlled', 'Tables 12, 13; §5.7 propagation'),
    'generation_bbq':  ('S12_generation_bbq', 'Table 12 (BBQ rows); §5.7'),
    'fc_controlled':   ('S13_forcedchoice_controlled', 'Table 13; Figure 7'),
    'fc_bbq':          ('S14_forcedchoice_bbq', 'Table 14; Figure 7'),
}

KEEP_EXTRA = ['summary.txt', 'aggregate.csv', 'by_stratum.csv', 'adaptive.csv',
              # the generation-stage RESULTS: the model outputs themselves. These are the
              # data a reader cannot recreate, since producing them costs API calls, so
              # the archive must carry them rather than the code that would re-buy them.
              'generation.json', 'forced_choice.json', 'attribution.json']
# _cache.json files hold raw API traffic for resumption and are build residue, not data
SKIP_SUFFIX = ('_cache.json',)
SKIP_EXT = {'.log', '.pkl', '.aux', '.out', '.spl'}

MANIFEST = '''Supplementary material for

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


HOW TO READ A PER-QUERY FILE

Every directory contains `per_query.csv`, one row per (query, condition) with the metrics computed
for that query. The columns, in the order they appear:

  qid             query identifier; the same qid appears under every condition, so conditions are
                  paired and a per-query difference is well defined
  drift_tv        R1 metric: total-variation distance of the group composition of the retrieved
                  set from the clean reference. The statistic the paper indicts.
  drift_js        R1 metric, Jensen-Shannon form
  stance_shift    R2 metric: per-group change in favourable rate against the per-query clean
                  reference. This is the diagnostic the paper recommends.
  stance_div      R2 metric: deviation of a group's stance from the corpus reference (mode F2)
  stance_onesided R2 metric: one-sidedness of a group's stance (mode F2)
  stance_gap      R2 metric: cross-group stance difference (mode F3). Invariant when all groups
                  relocate together.
  poison_in_topk  attack-success indicator
  poison_share    fraction of the retrieved top-k that is adversarial. Used as the graded
                  evidence-relocation label in the scope analysis.
  in_pool_rate    utility control: whether admissible passages remain available
  mean_score      mean retrieval score of the selected set
  attack, retriever, defense, epsilon, stratum, poison_rate, backbone
                  the experimental cell

`summary.txt` in each directory restates the tables printed by the run. `aggregate.csv`,
`by_stratum.csv` and `adaptive.csv` carry the aggregate and per-stratum reductions.


DIRECTORY INDEX

{index}

Numbers in this archive are the same values reported in the manuscript. Where an earlier version of
this work reported a different value, the change is recorded in Appendix E of the manuscript, and
the value here is the corrected one.


LICENCE AND ATTRIBUTION

Code: MIT. Derived data follows the licence of the source benchmark (BBQ: CC-BY-4.0). The controlled
corpus is generated deterministically from a fixed seed and contains no third-party material.
'''


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    rows = []
    total = 0
    for src, (dst, role) in INCLUDE.items():
        sdir = os.path.join(RESULTS, src)
        if not os.path.isdir(sdir):
            print('MISSING source: %s' % src)
            continue
        ddir = os.path.join(OUT, dst)
        os.makedirs(ddir, exist_ok=True)
        kept = []
        for f in sorted(os.listdir(sdir)):
            p = os.path.join(sdir, f)
            if not os.path.isfile(p):
                continue
            if os.path.splitext(f)[1].lower() in SKIP_EXT:
                continue
            if f.endswith(SKIP_SUFFIX):
                continue
            if f == 'per_query.csv' or f in KEEP_EXTRA:
                shutil.copy2(p, os.path.join(ddir, f))
                kept.append(f)
        size = sum(os.path.getsize(os.path.join(ddir, f)) for f in kept)
        total += size
        rows.append((dst, role, kept, size))
        print('%-30s %-34s %2d file(s) %7d KB' % (dst, kept[0] if kept else '-',
                                                  len(kept), round(size / 1024)))

    index = '\n'.join('  %-30s %s' % (d, r) for d, r, _k, _s in rows)
    io.open(os.path.join(OUT, 'README_SUPPLEMENTARY.txt'), 'w',
            encoding='utf-8', newline='\n').write(MANIFEST.format(index=index))
    print()
    print('directories: %d   total: %.1f MB' % (len(rows), total / 1024 / 1024))
    print('wrote %s' % os.path.join(OUT, 'README_SUPPLEMENTARY.txt'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
