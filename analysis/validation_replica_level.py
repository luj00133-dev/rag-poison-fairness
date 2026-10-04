"""The prospective validation, at replica level, with the attack that satisfies both properties.

Why this design. Three earlier attempts failed for reasons that are now all understood:

  * the label was the experimental condition (degenerate);
  * the label was binary because the injection was uniform, so there was no ROC to compute;
  * scoring per-query monitors tested a per-query quantity, whereas the paper's group
    favourable rate is an AVERAGE of binary votes over a stratum -- a batch statistic. A
    single query contributes one Bernoulli draw, so per-query monitoring at chance is
    uninformative about the recommendation.

This version fixes all three. The label is the retrieval-side adversarial fraction, graded by
the new injection; the monitors are computed as batch averages; and power comes from replicating
each stratum into 24 independent sub-batches, since only four BBQ categories exist and the
batch statistic needs many batches, not many categories.

The configuration is the one where balance and partial success co-occur: `template` on the st
retriever, where drift_tv is 0.0000 at every partial label level (analysis/
test_balance_vs_partial.py). Prediction under test, from the paper:

  * the cross-group gap is INVARIANT to how much evidence was relocated;
  * the per-group rates move monotonically with it.

If the gap tracks the label as strongly as the per-group rates do, the paper's asymmetry is not
supported on this data.
"""
import collections
import csv
import io
import json
import os
import random

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(P, 'results', 'pv_validate', 'attribution.json')
RETR = os.path.join(P, 'results', 'pv_graded3', 'per_query.csv')
OUT = os.path.join(P, 'results', 'validation_replica_level.csv')

N_REPLICAS = 12


def main():
    recs = json.load(io.open(GEN, encoding='utf-8'))['records']
    lab = {}
    for row in csv.DictReader(io.open(RETR, encoding='utf-8')):
        if row['attack'] == 'template' and row['defense'] == 'vanilla':
            try:
                lab[row['qid']] = float(row['poison_share'])
            except (ValueError, KeyError):
                pass

    order = {}
    for r in recs:
        if r.get('fc_fav'):
            gs = list(r['fc_fav'].keys())
            if len(gs) >= 2:
                order.setdefault(r['stratum'], gs[:2])
    print('group order: %s' % order)

    # replica assignment: within each (condition, stratum), split queries by qid order into
    # N_REPLICAS batches of near-equal size
    cells = collections.defaultdict(list)
    for r in recs:
        st = r['stratum']
        if st not in order:
            continue
        cells[(r['condition'], st)].append(r)
    for k in cells:
        cells[k].sort(key=lambda r: r['qid'])

    reps = collections.defaultdict(lambda: {'v1': [], 'v2': [], 'lab': []})
    for (cond, st), rs in cells.items():
        n = len(rs)
        if n == 0:
            continue
        size = max(1, n // N_REPLICAS)
        for i in range(0, n, size):
            chunk = rs[i:i + size]
            if not chunk:
                continue
            g1, g2 = order[st]
            v1 = [1.0 if (r.get('fc_fav') or {}).get(g1) else 0.0 for r in chunk]
            v2 = [1.0 if (r.get('fc_fav') or {}).get(g2) else 0.0 for r in chunk]
            key = (cond, st, i // size)
            reps[key]['v1'].extend(v1)
            reps[key]['v2'].extend(v2)
            for r in chunk:
                if cond != 'clean' and r['qid'] in lab:
                    reps[key]['lab'].append(lab[r['qid']])

    rows = []
    for (cond, st, idx), d in reps.items():
        if len(d['v1']) < 3:
            continue
        f1 = sum(d['v1']) / len(d['v1'])
        f2 = sum(d['v2']) / len(d['v2'])
        rows.append({'condition': cond, 'stratum': st, 'replica': idx,
                     'n': len(d['v1']),
                     'label': (sum(d['lab']) / len(d['lab'])) if d['lab'] else None,
                     'fav_g1': f1, 'fav_g2': f2, 'gap': abs(f1 - f2)})
    print('replica-level units: %d' % len(rows))

    # aggregate by condition
    print()
    print('%-10s %5s %9s %9s %9s %9s'
          % ('condition', 'units', 'label', 'fav_g1', 'fav_g2', 'gap'))
    print('-' * 60)
    by_cond = collections.defaultdict(list)
    for r in rows:
        by_cond[r['condition']].append(r)
    for cond in ('clean', 'poisoned'):
        v = by_cond.get(cond, [])
        if not v:
            continue
        labs = [r['label'] for r in v if r['label'] is not None]
        print('%-10s %5d %9s %9.4f %9.4f %9.4f'
              % (cond, len(v),
                 ('%.3f' % (sum(labs) / len(labs))) if labs else '-',
                 sum(r['fav_g1'] for r in v) / len(v),
                 sum(r['fav_g2'] for r in v) / len(v),
                 sum(r['gap'] for r in v) / len(v)))

    # attacked replicas binned by label level
    print()
    print('attacked replicas binned by retrieval-side label level:')
    print('%-9s %5s %9s %9s %9s' % ('label', 'units', 'fav_g1', 'fav_g2', 'gap'))
    print('-' * 48)
    binned = collections.defaultdict(list)
    for r in rows:
        if r['condition'] != 'clean' and r['label'] is not None:
            binned[round(r['label'], 1)].append(r)
    for lev in sorted(binned):
        v = binned[lev]
        print('%-9.1f %5d %9.4f %9.4f %9.4f'
              % (lev, len(v), sum(r['fav_g1'] for r in v) / len(v),
                 sum(r['fav_g2'] for r in v) / len(v),
                 sum(r['gap'] for r in v) / len(v)))

    # spread across label levels: flat vs moving
    print()
    print('spread across label levels (max - min):')
    for key, name in (('gap', 'gap (aggregate)'), ('fav_g1', 'fav_g1 (per-group)'),
                      ('fav_g2', 'fav_g2 (per-group)')):
        vals = [sum(r[key] for r in v) / len(v) for v in binned.values()]
        if len(vals) >= 2:
            print('  %-20s %.4f' % (name, max(vals) - min(vals)))

    # bootstrap CI on the clean-vs-full contrast for each statistic
    print()
    print('bootstrap 95%% CI, attacked(label=1.0) minus clean:')
    rng = random.Random(0)
    full = binned.get(1.0, [])
    cleanv = by_cond.get('clean', [])
    for key, name in (('gap', 'gap (aggregate)'), ('fav_g1', 'fav_g1 (per-group)'),
                      ('fav_g2', 'fav_g2 (per-group)')):
        if not full or not cleanv:
            continue
        obs = (sum(r[key] for r in full) / len(full)
               - sum(r[key] for r in cleanv) / len(cleanv))
        diffs = []
        for _ in range(2000):
            a = [rng.choice(full)[key] for _ in full]
            b = [rng.choice(cleanv)[key] for _ in cleanv]
            diffs.append(sum(a) / len(a) - sum(b) / len(b))
        diffs.sort()
        lo, hi = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs))]
        sig = 'SIGNIFICANT' if (lo > 0) == (hi > 0) else 'not distinguishable from 0'
        print('  %-20s %+.4f  [%+.4f, %+.4f]  %s' % (name, obs, lo, hi, sig))

    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        w = csv.DictWriter(fh, fieldnames=['condition', 'stratum', 'replica', 'n',
                                           'label', 'fav_g1', 'fav_g2', 'gap'])
        w.writeheader()
        w.writerows(rows)
    print()
    print('wrote %s' % OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
