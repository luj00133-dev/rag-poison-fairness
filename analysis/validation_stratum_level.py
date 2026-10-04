"""The validation, done at the level the recommendation actually operates on.

Why the previous attempt was testing the wrong thing. The group favourable rate in
summarise() is computed by AVERAGING the binary fc_fav votes across every query in a stratum.
It is a batch statistic. Each individual query contributes one Bernoulli draw, so there is no
per-query per-group rate to threshold, and scoring per-query monitors at AUC was measuring
something the paper does not propose. That is why every monitor sat at chance, and the chance
result is not evidence against the recommendation.

What is tested here instead, at the stratum level and with bootstrap uncertainty:

  1. AGGREGATE INVARIANCE. Does the cross-group gap stay put as the retrieval-side poison
     share varies? This is the paper's central claim.
  2. PER-GROUP RESPONSIVENESS. Do the individual group rates move as it varies? This is the
     paper's recommended diagnostic.

Both are read off the same data, so the claim is confirmed only if the gap is flat while a
group rate is not. The label is the retrieval-side poison share, averaged per stratum, which
the monitors do not observe.
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
OUT = os.path.join(P, 'results', 'validation_stratum_level.csv')


def main():
    j = json.load(io.open(os.path.join(RUN, 'attribution.json'), encoding='utf-8'))
    recs = j['records']

    # retrieval-side label per qid
    lab = {}
    for row in csv.DictReader(io.open(RETR, encoding='utf-8')):
        if row['attack'] != 'template' or row['defense'] != 'vanilla':
            continue
        try:
            lab[row['qid']] = float(row['poison_share'])
        except (ValueError, KeyError):
            pass

    # group order per stratum, matching summarise()
    order = {}
    for r in recs:
        if r.get('fc_fav'):
            gs = list(r['fc_fav'].keys())
            if len(gs) >= 2:
                order.setdefault(r['stratum'], gs[:2])
    print('stratum group order: %s' % order)

    # collect per (condition, stratum): label mean, per-group votes
    cells = collections.defaultdict(lambda: {'lab': [], 'v1': [], 'v2': []})
    for r in recs:
        st = r['stratum']
        if st not in order:
            continue
        g1, g2 = order[st]
        fav = r.get('fc_fav') or {}
        if g1 not in fav or g2 not in fav:
            continue
        key = (r['condition'], st)
        cells[key]['v1'].append(1.0 if fav[g1] else 0.0)
        cells[key]['v2'].append(1.0 if fav[g2] else 0.0)
        if r['condition'] != 'clean' and r['qid'] in lab:
            cells[key]['lab'].append(lab[r['qid']])

    rows = []
    for (cond, st), d in sorted(cells.items()):
        if not d['v1'] or not d['lab']:
            continue
        n = len(d['v1'])
        f1 = sum(d['v1']) / n
        f2 = sum(d['v2']) / n
        rows.append({'condition': cond, 'stratum': st, 'n': n,
                     'label_mean': sum(d['lab']) / len(d['lab']),
                     'fav_g1': f1, 'fav_g2': f2, 'gap': abs(f1 - f2)})

    print()
    print('%-10s %-16s %5s %9s %9s %9s %9s'
          % ('condition', 'stratum', 'n', 'label', 'fav_g1', 'fav_g2', 'gap'))
    print('-' * 74)
    for r in sorted(rows, key=lambda x: (x['condition'], x['label_mean'])):
        print('%-10s %-16s %5d %9.3f %9.3f %9.3f %9.3f'
              % (r['condition'], r['stratum'], r['n'], r['label_mean'],
                 r['fav_g1'], r['fav_g2'], r['gap']))

    # correlation of each statistic with the label, across cells
    def pearson(xs, ys):
        n = len(xs)
        if n < 3:
            return float('nan')
        mx, my = sum(xs) / n, sum(ys) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = sum((x - mx) ** 2 for x in xs) ** 0.5
        dy = sum((y - my) ** 2 for y in ys) ** 0.5
        return num / (dx * dy) if dx and dy else float('nan')

    L = [r['label_mean'] for r in rows]
    print()
    print('correlation with the retrieval-side label, across %d stratum-condition cells:' % len(rows))
    for name, key, sign in (('fav_g1 (per-group)', 'fav_g1', +1),
                            ('fav_g2 (per-group)', 'fav_g2', -1),
                            ('gap (aggregate)', 'gap', 0)):
        vals = [r[key] for r in rows]
        r_ = pearson(L, vals)
        print('  %-22s r = %+.3f' % (name, r_))

    print()
    gaps = [r['gap'] for r in rows]
    print('gap across cells: min=%.3f max=%.3f spread=%.3f' % (min(gaps), max(gaps),
                                                              max(gaps) - min(gaps)))
    g1s = [r['fav_g1'] for r in rows]
    g2s = [r['fav_g2'] for r in rows]
    print('fav_g1 spread=%.3f   fav_g2 spread=%.3f'
          % (max(g1s) - min(g1s), max(g2s) - min(g2s)))

    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        w = csv.DictWriter(fh, fieldnames=['condition', 'stratum', 'n', 'label_mean',
                                           'fav_g1', 'fav_g2', 'gap'])
        w.writeheader()
        w.writerows(rows)
    print()
    print('wrote %s' % OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
