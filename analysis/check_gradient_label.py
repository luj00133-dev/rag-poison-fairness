"""Is the poison-share label graded, and does the per-group signal decouple from the aggregate?

Two things must hold for the prospective validation to be possible at all:

  1. the label must vary PER QUERY at a fixed attack rate. If it is again a monotone function
     of the rate, it is attack strength and the earlier objection stands;
  2. the per-group statistic and the aggregate must not be the same number. If they move
     together perfectly, there is nothing to compare.
"""
import collections
import csv
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(P, 'results', 'pv_gradient', 'per_query.csv')


def main():
    rows = list(csv.DictReader(io.open(RUN, encoding='utf-8')))
    print('rows: %d' % len(rows))
    print('attacks: %s' % sorted({r['attack'] for r in rows}))
    print('defenses: %s' % sorted({r['defense'] for r in rows}))
    print('poison_rates: %s' % sorted({r['poison_rate'] for r in rows}, key=str))
    print()

    # restrict to the undefended configuration, which is what the label describes
    base = [r for r in rows if r['defense'] == 'vanilla' and r['retriever'] == 'st']
    print('--- label by (attack, poison_rate), vanilla/st ---')
    by = collections.defaultdict(list)
    for r in base:
        try:
            by[(r['attack'], r['poison_rate'])].append(float(r['poison_share']))
        except ValueError:
            pass
    for key in sorted(by, key=str):
        v = by[key]
        uniq = sorted(set(round(x, 4) for x in v))
        print('  %-34s n=%-4d mean=%.3f distinct=%-3d %s'
              % (str(key), len(v), sum(v) / len(v), len(uniq), uniq[:8]))

    print()
    print('--- do the per-group and aggregate statistics differ? ---')
    def num(r, k):
        try:
            return float(r[k])
        except (ValueError, KeyError):
            return float('nan')
    pairs = [(num(r, 'stance_shift'), num(r, 'stance_gap'), num(r, 'stance_div'))
             for r in base if r['attack'] != 'clean']
    pairs = [p for p in pairs if p[0] == p[0]]
    print('  attacked rows with a per-group shift: %d' % len(pairs))
    if pairs:
        same_gap = sum(1 for a, b, c in pairs if abs(a - b) < 1e-9)
        same_div = sum(1 for a, b, c in pairs if abs(a - c) < 1e-9)
        print('  stance_shift == stance_gap : %d / %d' % (same_gap, len(pairs)))
        print('  stance_shift == stance_div : %d / %d' % (same_div, len(pairs)))
        vals = sorted({round(a, 4) for a, _, _ in pairs})
        print('  distinct stance_shift values: %s' % vals[:10])
        gvals = sorted({round(b, 4) for _, b, _ in pairs})
        print('  distinct stance_gap values  : %s' % gvals[:10])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
