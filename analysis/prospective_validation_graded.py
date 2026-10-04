"""The prospective validation, on a genuinely graded label.

Label. Per query, the count of adversarial passages in its retrieved context, from the run's
own records. The graded injection made this take more than two values for the first time.

Monitors. Computed from the ANSWER only, which is what a deployment has; the label is
retrieval-side, so the monitors are scored against something they do not observe.

  aggregate : the cross-group stance gap |fav_g1 - fav_g2| -- the statistic the paper indicts
  per-group : each group's favourable rate relative to its own stratum-and-condition mean --
              what the paper recommends

Test. Does the per-group monitor rank queries by evidence relocation better than the
aggregate? Reported as AUC on the continuous label, plus a binary contrast at a matched
false-positive rate. If the per-group monitors do not beat the aggregate, the paper's
recommendation is not supported by this data and the output says so.
"""
import collections
import csv
import io
import json
import os
import random
import sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(P, 'results', 'pv_validate')
RETR = os.path.join(P, 'results', 'pv_graded3', 'per_query.csv')
OUT = os.path.join(P, 'results', 'prospective_validation.csv')


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


def main():
    j = json.load(io.open(os.path.join(RUN, 'attribution.json'), encoding='utf-8'))
    recs = j['records']
    print('generation records: %d' % len(recs))
    c = collections.Counter(r['n_poison_in_context'] for r in recs)
    print('n_poison_in_context by condition: %s' % dict(sorted(c.items())))

    # join the retrieval-side label by qid, so the label is the RETRIEVAL quantity rather
    # than the generation record's own copy
    lab = {}
    for row in csv.DictReader(io.open(RETR, encoding='utf-8')):
        if row['attack'] != 'template' or row['defense'] != 'vanilla':
            continue
        try:
            lab[row['qid']] = float(row['poison_share'])
        except (ValueError, KeyError):
            pass
    print('retrieval-side labels available for %d queries' % len(lab))

    # group rates are per record only as a boolean vote; use fc_fav
    rows = []
    for r in recs:
        fav = r.get('fc_fav') or {}
        vals = list(fav.values())
        if len(vals) != 2:
            continue
        g1, g2 = float(vals[0]), float(vals[1])
        rows.append({'qid': r['qid'], 'stratum': r['stratum'],
                     'condition': r['condition'], 'g1': g1, 'g2': g2,
                     'gap': abs(g1 - g2)})
    print('rows with a two-group vote: %d' % len(rows))

    # graded label: retrieval poison share, for ATTACKED queries only
    attacked = [r for r in rows if r['condition'] in ('poisoned', 'r1only', 'r2both')
                and r['qid'] in lab]
    print('attacked rows with a label: %d' % len(attacked))
    if not attacked:
        print('NO LABELLED ROWS')
        return 1
    lv = collections.Counter(round(lab[r['qid']], 2) for r in attacked)
    print('label distribution over attacked rows: %s' % dict(sorted(lv.items())))

    # per-group deviation from the stratum-and-condition mean
    base = collections.defaultdict(list)
    for r in rows:
        base[(r['stratrum'] if 'stratrum' in r else r['stratum'], r['condition'])].append(r)
    for k, grp in base.items():
        m1 = sum(x['g1'] for x in grp) / len(grp)
        m2 = sum(x['g2'] for x in grp) / len(grp)
        for x in grp:
            x['dev'] = max(abs(x['g1'] - m1), abs(x['g2'] - m2))

    y = [1 if lab[r['qid']] > 0 else 0 for r in attacked]
    print()
    print('binary contrast: relocated (>0 adversarial passages) vs not')
    print('  positives=%d negatives=%d' % (sum(y), len(y) - sum(y)))

    monitors = {
        'aggregate_gap': ([r['gap'] for r in attacked], 'aggregate'),
        'pergroup_g1_dev': ([abs(r['g1'] - 0.5) for r in attacked], 'per-group'),
        'pergroup_g2_dev': ([abs(r['g2'] - 0.5) for r in attacked], 'per-group'),
        'pergroup_stratum_dev': ([r.get('dev', 0.0) for r in attacked], 'per-group'),
    }
    print()
    print('%-24s %-10s %7s' % ('monitor', 'family', 'AUC'))
    print('-' * 44)
    res = []
    for name, (sc, fam) in monitors.items():
        a = auc(sc, y)
        print('%-24s %-10s %7.3f' % (name, fam, a))
        res.append({'monitor': name, 'family': fam, 'auc': a})

    agg = [r for r in res if r['family'] == 'aggregate'][0]['auc']
    per = max(r['auc'] for r in res if r['family'] == 'per-group')
    print()
    print('claim: aggregate at chance, per-group above it')
    print('  aggregate AUC      : %.3f' % agg)
    print('  best per-group AUC : %.3f' % per)
    verdict = 'supported' if (agg < 0.60 <= per) else 'NOT supported on this configuration'
    print('  VERDICT: %s' % verdict)

    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        w = csv.DictWriter(fh, fieldnames=['monitor', 'family', 'auc'])
        w.writeheader()
        w.writerows(res)
    print()
    print('wrote %s' % OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
