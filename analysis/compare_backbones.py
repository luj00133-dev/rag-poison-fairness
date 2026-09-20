"""Compare the feature-hashing dense retriever against real GTE-base."""
import csv
from collections import defaultdict


def load(p):
    try:
        return list(csv.DictReader(open(p, encoding='utf-8')))
    except FileNotFoundError:
        return []


def _rate(r):
    """Rate as a float, or -1 for the clean condition (which has no injection)."""
    v = r.get('poison_rate', '')
    try:
        return float(v)
    except (TypeError, ValueError):
        return -1.0


def _rate_s(r):
    v = _rate(r)
    return '    -  ' if v < 0 else f'{v:>7.2%}'


def tbl(rows, retr, title, attack='template_plus_projection'):
    print(f'--- {title}  (retriever = {retr}) ---')
    print(f"{'defense':>12s} {'eps':>5s} {'rate':>7s} {'R1 drift':>9s} "
          f"{'R2 gap':>8s} {'poison@k':>9s} {'util':>7s}")
    sub = [r for r in rows
           if r.get('defense') in ('vanilla', 'multi_query', 'manifold', 'repr_group', 'repr_both')
           and r.get('retriever') == retr]
    for r in sorted(sub, key=lambda x: (x['attack'], _rate(x), x['defense'], x['epsilon'])):
        if r['attack'] != attack:
            continue
        print(f"{r['defense']:>12s} {r['epsilon'] or '-':>5s} "
              f"{_rate_s(r)} {float(r['drift_tv']):>9.4f} "
              f"{float(r['stance_gap']):>8.4f} {r['poison_in_topk']:>9s} "
              f"{float(r['in_pool_rate']):>7.4f}")
    print()


print('#' * 78)
print('#  BASELINE (feature-hashing dense)  vs  ALIGNED (GTE-base)')
print('#' * 78)
base = load('results/full/aggregate.csv')
gte = load('results/align_ctl/aggregate.csv')

print()
print('=' * 78)
print('  A. attack effect, no defense, controlled corpus')
print('=' * 78)
for tag, rows, retr in (('hash-dense', base, 'dense'), ('GTE-base', gte, 'st')):
    print(f'--- {tag} ---')
    print(f"{'attack':>26s} {'rate':>7s} {'R1 drift':>9s} {'R2 gap':>8s} "
          f"{'poison@k':>9s} {'util':>7s}")
    sub = [r for r in rows if r['defense'] == 'vanilla' and r['retriever'] == retr]
    for r in sorted(sub, key=lambda x: (x['attack'], _rate(x))):
        print(f"{r['attack']:>26s} {_rate_s(r)} "
              f"{float(r['drift_tv']):>9.4f} {float(r['stance_gap']):>8.4f} "
              f"{r['poison_in_topk']:>9s} {float(r['in_pool_rate']):>7.4f}")
    print()

print('=' * 78)
print('  B. defense comparison under template_plus_projection')
print('=' * 78)
tbl(base, 'dense', 'hash-dense')
tbl(gte, 'st', 'GTE-base')
