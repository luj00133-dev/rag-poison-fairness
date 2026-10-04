"""Find existing runs where a BALANCED attack already yields a partial label.

Before building a new attack construction, check whether the repository already contains one
that satisfies both requirements at once:

  1. balanced across groups (so the R1 composition statistics stay at their clean value), and
  2. partially successful per query (so the retrieval-side label is graded).

The label histogram shows intermediates (0.2/0.4/0.6/0.8) in roughly 14% of attacked rows, so
this asks specifically which attack and defense produced them, and whether R1 drift stayed
flat in the same cells. If such a cell exists, the validation can be run on data already in
hand rather than on a new construction.
"""
import collections
import csv
import glob
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')

# attacks that are balanced across groups by construction
BALANCED = ('template_plus_projection', 'template_balanced', 'balanced')


def main():
    found = []
    for path in glob.glob(os.path.join(RESULTS, '*', 'per_query.csv')):
        tag = os.path.basename(os.path.dirname(path))
        try:
            rows = list(csv.DictReader(io.open(path, encoding='utf-8')))
        except Exception:
            continue
        if not rows or 'poison_share' not in rows[0]:
            continue
        cells = collections.defaultdict(lambda: {'share': [], 'drift': []})
        for r in rows:
            if r['attack'] == 'clean':
                continue
            try:
                s = float(r['poison_share'])
            except (ValueError, TypeError):
                continue
            if s != s:
                continue
            k = (r['attack'], r['retriever'], r['defense'])
            cells[k]['share'].append(s)
            try:
                cells[k]['drift'].append(float(r['drift_tv']))
            except (ValueError, TypeError):
                pass
        for (atk, ret, dfn), d in cells.items():
            if not any(b in atk for b in BALANCED):
                continue
            n = len(d['share'])
            if n < 32:
                continue
            part = sum(1 for x in d['share'] if 0 < x < 1.0)
            if part == 0:
                continue
            uniq = sorted(set(round(x, 2) for x in d['share']))
            drift = [x for x in d['drift'] if x == x]
            found.append({
                'run': tag, 'attack': atk, 'retriever': ret, 'defense': dfn,
                'n': n, 'partial': part, 'partial_pct': 100.0 * part / n,
                'levels': uniq,
                'drift_mean': sum(drift) / len(drift) if drift else float('nan'),
            })

    found.sort(key=lambda x: -x['partial_pct'])
    print('%-14s %-26s %-9s %-12s %5s %8s %9s  %s'
          % ('run', 'attack', 'retriever', 'defense', 'n', 'partial',
             'drift_tv', 'levels'))
    print('-' * 116)
    for f in found[:24]:
        print('%-14s %-26s %-9s %-12s %5d %7.1f%% %9.4f  %s'
              % (f['run'], f['attack'][:26], f['retriever'], f['defense'],
                 f['n'], f['partial_pct'], f['drift_mean'], f['levels']))

    print()
    print('%d balanced-attack cells carry a partial label' % len(found))
    if not found:
        print('-> none; a new construction is required')
    else:
        best = found[0]
        print('-> best: run=%s attack=%s defense=%s partial=%.1f%%'
              % (best['run'], best['attack'], best['defense'], best['partial_pct']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
