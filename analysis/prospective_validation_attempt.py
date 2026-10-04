"""Prospective validation, corrected: paired monitors against held-out ground truth.

Why the first attempt was wrong. It scored each query's absolute per-group LEVEL, and the
per-query dispersion of a level is sd 0.43 on a signal whose mean moves 0.13 -- the topic of
the query dominates the level. Every monitor came out at chance (aggregate AUC 0.484, best
per-group 0.543) and the script correctly reported "NOT supported by this data". The failure
was mine: the paper does not recommend thresholding raw levels, it recommends comparing
per-group quantities against a clean reference for the same queries. The runs are paired by
qid, so that comparison is available.

This version implements the recommendation as stated.

Construction:
  * ground truth is `n_poison_in_context` (0 clean, 5 poisoned), never derived from a metric;
  * each monitor is evaluated as a PAIRED difference: the attacked query's value minus the
    SAME query's value in the clean condition, so the query's topic cancels;
  * thresholds are tuned on the controlled corpus and applied UNCHANGED to the natural BBQ
    corpus, which is the held-out test;
  * every monitor is compared at a matched false-positive rate (5%) on clean queries.

Monitors, grouped by what the paper predicts about them:
  * aggregate  : the cross-group gap (F3) and the R1 drift statistics (F1)
  * per-group  : the change in each group's level -- the paper's recommendation
  * individual : per-passage attribution (§7)

Pre-registered prediction: the aggregate monitors are at chance on the held-out corpus,
the per-group monitors are not.
"""
import collections
import csv
import io
import os
import random

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')
OUT = os.path.join(RESULTS, 'prospective_validation.csv')

AGGREGATE = ['gap', 'stance_shift', 'stance_div', 'stance_onesided', 'drift_tv', 'drift_js']
PERGROUP = ['g1', 'g2']
INDIVIDUAL = ['attrib', 'unattr']


def load_gen(tag):
    rows = list(csv.DictReader(io.open(os.path.join(RESULTS, tag, 'per_query.csv'),
                                       encoding='utf-8')))
    by = {}
    for r in rows:
        key = (r['generator'], r['qid'])
        try:
            rec = {'g1': float(r['stance_g1']), 'g2': float(r['stance_g2']),
                   'gap': float(r['gap']),
                   'attrib': float(r['mean_attribution'] or 'nan'),
                   'unattr': float(r['unattributed_rate'] or 'nan')}
        except ValueError:
            continue
        by.setdefault(key, {})[r['condition']] = rec
    return by


def load_ret(tag):
    rows = list(csv.DictReader(io.open(os.path.join(RESULTS, tag, 'per_query.csv'),
                                       encoding='utf-8')))
    by = {}
    for r in rows:
        if r['retriever'] != 'bm25' or r['defense'] != 'vanilla':
            continue
        try:
            rec = {k: float(r[k]) for k in ('drift_tv', 'drift_js', 'stance_shift',
                                            'stance_div', 'stance_onesided', 'stance_gap')}
        except ValueError:
            continue
        cond = 'clean' if r['attack'] == 'clean' else 'attacked'
        by.setdefault((r['qid'],), {})[cond] = rec
    return by


def auc(scores, labels):
    pairs = sorted(zip(scores, labels), key=lambda t: t[0])
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if not n_pos or not n_neg:
        return float('nan')
    rank_sum, i = 0.0, 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            if pairs[k][1] == 1:
                rank_sum += avg
        i = j + 1
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def permutation_p(diffs_pos):
    """Paired sign-flip test on the paired differences: is the mean shift nonzero?"""
    vals = [d for d in diffs_pos]
    if not vals:
        return float('nan')
    obs = abs(sum(vals) / len(vals))
    rng = random.Random(0)
    n = len(vals)
    hits = 0
    trials = 5000
    for _ in range(trials):
        s = sum(v if rng.random() < 0.5 else -v for v in vals)
        if abs(s / n) >= obs - 1e-15:
            hits += 1
    return hits / trials


def paired(by, metric, attacked_cond='poisoned'):
    """(abs paired difference, is_attacked) for every query present in both conditions."""
    out = []
    for key, conds in by.items():
        if 'clean' not in conds or attacked_cond not in conds:
            continue
        a = conds['clean']
        for cond_name, rec in ((attacked_cond, conds[attacked_cond]),):
            try:
                d = rec[metric] - a[metric]
            except KeyError:
                continue
            if d != d:
                continue
            out.append((abs(d), 1, key))
        # clean queries against themselves: difference zero
        out.append((0.0, 0, key))
    return out


def quantile(values, q):
    v = sorted(values)
    if not v:
        return float('nan')
    return v[min(len(v) - 1, max(0, int(round(q * (len(v) - 1)))))]


def main():
    tune = load_gen('generation')
    test = load_gen('generation_bbq')
    ret = load_ret('full')
    print('tuning (controlled)  : %d query-conditions' % len(tune))
    print('held out (BBQ)       : %d query-conditions' % len(test))
    print('retrieval layer      : %d query-conditions' % len(ret))

    print()
    print('=== generation layer, paired against each query\'s own clean run ===')
    print('%-14s %-9s %9s %9s %8s' % ('metric', 'group', 'AUC(tune)', 'AUC(test)', 'p(test)'))
    print('-' * 56)
    rows_out = []
    for metric in AGGREGATE + PERGROUP + INDIVIDUAL:
        grp = ('aggregate' if metric in AGGREGATE else
               'per-group' if metric in PERGROUP else 'individual')
        s_t = paired(tune, metric)
        s_e = paired(test, metric)
        if not s_t or not s_e:
            print('%-14s %-9s %9s %9s' % (metric, grp, 'n/a', 'n/a'))
            continue
        a_t = auc([x[0] for x in s_t], [x[1] for x in s_t])
        a_e = auc([x[0] for x in s_e], [x[1] for x in s_e])
        diffs = [x[0] for x in s_e if x[1] == 1]
        p = permutation_p(diffs)
        print('%-14s %-9s %9.3f %9.3f %8.4f' % (metric, grp, a_t, a_e, p))
        rows_out.append({'layer': 'generation', 'metric': metric, 'group': grp,
                         'auc_tune': a_t, 'auc_test': a_e, 'p_test': p})

    print()
    print('=== retrieval layer, paired against the same query\'s clean run ===')
    print('%-16s %-9s %9s %8s' % ('metric', 'group', 'AUC', 'p'))
    print('-' * 46)
    for metric in ('stance_shift', 'stance_gap', 'drift_tv', 'drift_js',
                   'stance_div', 'stance_onesided'):
        s = paired(ret, metric, attacked_cond='attacked')
        if not s:
            continue
        a = auc([x[0] for x in s], [x[1] for x in s])
        diffs = [x[0] for x in s if x[1] == 1]
        p = permutation_p(diffs)
        grp = 'per-group' if metric == 'stance_shift' else 'aggregate'
        print('%-16s %-9s %9.3f %8.4f' % (metric, grp, a, p))
        rows_out.append({'layer': 'retrieval', 'metric': metric, 'group': grp,
                         'auc_tune': float('nan'), 'auc_test': a, 'p_test': p})

    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        w = csv.DictWriter(fh, fieldnames=['layer', 'metric', 'group', 'auc_tune',
                                           'auc_test', 'p_test'])
        w.writeheader()
        w.writerows(rows_out)
    print()
    print('wrote %s' % OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
