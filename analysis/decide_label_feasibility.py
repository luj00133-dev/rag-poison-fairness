"""Decide whether a graded relocation label is usable, from the full committed record.

This is the measurement that settles the experiment's feasibility. Across every retrieval run
in the repository, how often does the label take an intermediate value -- something strictly
between "no adversarial passage retrieved" and "the whole top-k is adversarial"? A graded
label is only usable if intermediates are a substantial fraction; if the pipeline only ever
produces 0 or 1, every configuration is degenerate and the prospective validation cannot be
built by reconfiguration.
"""
import collections
import csv
import glob
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')


def main():
    per_run = collections.defaultdict(collections.Counter)
    for p in glob.glob(os.path.join(RESULTS, '*', 'per_query.csv')):
        tag = os.path.basename(os.path.dirname(p))
        try:
            rows = list(csv.DictReader(io.open(p, encoding='utf-8')))
        except Exception:
            continue
        if not rows or 'poison_share' not in rows[0]:
            continue
        for r in rows:
            if r['attack'] == 'clean':
                continue
            try:
                v = float(r['poison_share'])
            except (ValueError, TypeError):
                continue
            if v != v:
                continue
            per_run[tag][round(v, 2)] += 1

    print('%-18s %6s %8s %8s %9s' % ('run', 'attacked', 'zero', 'partial', 'full'))
    print('-' * 54)
    tot = collections.Counter()
    for tag in sorted(per_run):
        c = per_run[tag]
        n = sum(c.values())
        zero = c.get(0.0, 0)
        full = c.get(1.0, 0)
        part = n - zero - full
        tot['n'] += n
        tot['zero'] += zero
        tot['full'] += full
        tot['part'] += part
        if n >= 32:
            print('%-18s %6d %8d %8d %9d' % (tag, n, zero, part, full))

    print()
    print('ALL RUNS: attacked=%d  zero=%d (%.1f%%)  partial=%d (%.1f%%)  full=%d (%.1f%%)'
          % (tot['n'], tot['zero'], 100.0 * tot['zero'] / max(1, tot['n']),
             tot['part'], 100.0 * tot['part'] / max(1, tot['n']),
             tot['full'], 100.0 * tot['full'] / max(1, tot['n'])))
    print()
    if tot['part'] / max(1, tot['n']) < 0.10:
        print('VERDICT: intermediates are under 10%% of attacked queries. The pipeline is')
        print('         effectively binary on the retrieval side, so a graded label cannot')
        print('         be obtained by reconfiguration. A prospective detector validation')
        print('         needs a different INJECTION DESIGN, not a different config.')
    else:
        print('VERDICT: intermediates are frequent enough to supervise on.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
