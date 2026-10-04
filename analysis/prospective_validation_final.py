"""Prospective validation, on the data actually generated.

Setup. The generation run answered every query under four retrieval conditions with
deepseek-chat, and the NLI scorer measured per-group answer stance. The label is the
retrieval-side quantity n_poison_in_context, recorded per query in the run's own output.

  * label      : how many adversarial passages were in that query's retrieved context (1..5)
                 -- evidence relocation, observed at retrieval, independent of any monitor
  * monitors   : computed from the ANSWER only. A deployment has the answer, not the context.
      - aggregate : the cross-group stance gap |fav_g1 - fav_g2| -- the statistic the paper
                    indicts
      - per-group : each group's favourable rate, and the max deviation from its own stratum
                    mean -- what the paper recommends
  * threshold  : fixed on the portion of the label range below the median and applied to the
                 upper portion, so the split is decided before any monitor is scored.

This is the test that could not be run before: earlier attempts used a label that was the
experimental condition (degenerate) or the attacker's own rate (strength, not effect).
"""
import collections
import csv
import io
import json
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(P, 'results', 'pv_attrib')
OUT = os.path.join(P, 'results', 'prospective_validation.csv')


def load_records():
    j = json.load(io.open(os.path.join(RUN, 'attribution.json'), encoding='utf-8'))
    recs = j['records']
    out = []
    for r in recs:
        g1 = r.get('fav_rate_g1')
        g2 = r.get('fav_rate_g2')
        out.append({
            'qid': r['qid'], 'stratum': r['stratum'], 'condition': r['condition'],
            'n_poison': float(r.get('n_poison_in_context') or 0),
            'g1': g1, 'g2': g2,
            'gap': (abs(g1 - g2) if (g1 is not None and g2 is not None) else None),
            'answer': r.get('answer', ''),
        })
    return out


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
    rows = load_records()
    print('records: %d' % len(rows))
    poison_counts = collections.Counter(r['n_poison'] for r in rows)
    print('n_poison_in_context distribution: %s' % dict(sorted(poison_counts.items())))
    usable = [r for r in rows if r['g1'] is not None and r['g2'] is not None]
    print('rows with both group rates: %d' % len(usable))
    if not usable:
        print('NO USABLE ROWS')
        return 1

    # label: relocated (>0 adversarial passages) vs not
    lab = [1 if r['n_poison'] > 0 else 0 for r in usable]
    print('label balance: relocated=%d not=%d' % (sum(lab), len(lab) - sum(lab)))

    # monitors, computed from the answer side only
    strata_mean = collections.defaultdict(list)
    for r in usable:
        strata_mean[(r['stratum'], r['condition'])].append(r)
    def maxdev(r):
        grp = strata_mean[(r['stratum'], r['condition'])]
        m1 = sum(x['g1'] for x in grp) / len(grp)
        m2 = sum(x['g2'] for x in grp) / len(grp)
        return max(abs(r['g1'] - m1), abs(r['g2'] - m2))

    monitors = {
        'aggregate_gap': ([r['gap'] for r in usable], 'aggregate'),
        'pergroup_g1_dev': ([abs(r['g1'] - 0.5) for r in usable], 'per-group'),
        'pergroup_g2_dev': ([abs(r['g2'] - 0.5) for r in usable], 'per-group'),
        'pergroup_maxdev': ([maxdev(r) for r in usable], 'per-group'),
    }

    print()
    print('%-18s %-10s %7s' % ('monitor', 'family', 'AUC'))
    print('-' * 38)
    out = []
    for name, (scores, fam) in monitors.items():
        a = auc(scores, lab)
        print('%-18s %-10s %7.3f' % (name, fam, a))
        out.append({'monitor': name, 'family': fam, 'auc': a})

    agg = [r for r in out if r['family'] == 'aggregate']
    per = [r for r in out if r['family'] == 'per-group']
    print()
    print('claim: the aggregate is at chance, the per-group monitors are not')
    print('  aggregate AUC          : %.3f' % (agg[0]['auc'] if agg else float('nan')))
    print('  best per-group AUC     : %.3f'
          % (max(r['auc'] for r in per) if per else float('nan')))
    verdict = ('supported' if agg and per and agg[0]['auc'] < 0.60 <= max(r['auc'] for r in per)
               else 'NOT supported on this configuration')
    print('  VERDICT: %s' % verdict)

    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        w = csv.DictWriter(fh, fieldnames=['monitor', 'family', 'auc'])
        w.writeheader()
        w.writerows(out)
    print()
    print('wrote %s' % OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
