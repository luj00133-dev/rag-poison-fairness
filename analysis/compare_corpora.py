"""Compare controlled vs natural (BBQ) results."""
import csv
from collections import defaultdict


def load(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def show(rows, title, attack='template_plus_projection'):
    print(f'--- {title} ---')
    print(f"{'retr':>6s} {'defense':>12s} {'eps':>5s} {'R1 drift':>9s} "
          f"{'R2 gap':>8s} {'poison@k':>9s} {'util':>7s}")
    for r in rows:
        if r['attack'] != attack:
            continue
        if r['defense'] not in ('vanilla', 'multi_query', 'manifold') and \
           r['epsilon'] not in ('1.0', '0.0', ''):
            continue
        print(f"{r['retriever']:>6s} {r['defense']:>12s} {r['epsilon']:>5s} "
              f"{float(r['drift_tv']):>9.4f} {float(r['stance_gap']):>8.4f} "
              f"{r['poison_in_topk']:>9s} {float(r['in_pool_rate']):>7.4f}")


for tag, path in (('CONTROLLED', 'results/full/aggregate.csv'),
                  ('BBQ (natural)', 'results/bbq/aggregate.csv')):
    print('=' * 78)
    print(f'  {tag}')
    print('=' * 78)
    rows = load(path)
    print(f"{'attack':>26s} {'retr':>6s} {'R1 drift':>9s} {'R2 gap':>8s} "
          f"{'poison@k':>9s} {'util':>7s}")
    for r in rows:
        if r['defense'] != 'vanilla':
            continue
        print(f"{r['attack']:>26s} {r['retriever']:>6s} "
              f"{float(r['drift_tv']):>9.4f} {float(r['stance_gap']):>8.4f} "
              f"{r['poison_in_topk']:>9s} {float(r['in_pool_rate']):>7.4f}")
    print()
    show(rows, f'{tag}: defense comparison')
    print()

# adaptive comparison
print('=' * 78)
print('  ADAPTIVE: poison@k vs lambda')
print('=' * 78)
for tag, path in (('CONTROLLED', 'results/full/adaptive.csv'),
                  ('BBQ', 'results/bbq/adaptive.csv')):
    print(f'--- {tag} ---')
    rows = load(path)
    by = defaultdict(dict)
    for r in rows:
        by[r['defense']][float(r['lambda'])] = float(r['poison_in_topk'])
    lams = sorted({float(r['lambda']) for r in rows})
    print(f"{'defense':>16s} " + ' '.join(f'{l:>7.2f}' for l in lams))
    for d in sorted(by):
        print(f"{d:>16s} " + ' '.join(f"{by[d].get(l, float('nan')):>7.3f}" for l in lams))
    print()
