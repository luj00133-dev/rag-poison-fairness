"""Three-way backbone comparison: BM25 vs feature-hashing dense vs GTE-base.

All on the controlled corpus so that only the retriever varies. This is the
table that decides whether the paper's "R1 is inert" claim survives a real
semantic encoder.
"""
import csv


def load(p):
    try:
        return list(csv.DictReader(open(p, encoding='utf-8')))
    except FileNotFoundError:
        return []


def num(r, k):
    try:
        return float(r[k])
    except (TypeError, ValueError):
        return float('nan')


full = load('results/full/aggregate.csv')          # bm25 + hash-dense
gte = load('results/align_ctl/aggregate.csv')      # bm25 + st:gte-base

# pick the strongest attack and a matched injection rate
ATTACK = 'template_plus_projection'
RATE = '0.005'

print('=' * 96)
print(f'  A. attack effect under {ATTACK} at rate {RATE}, no defense')
print('=' * 96)
print(f"{'retriever':>16s} {'R1 drift':>9s} {'R2 gap':>9s} {'poison@k':>10s} {'util':>8s}")
seen = {}
for rows in (full, gte):
    for r in rows:
        if r['attack'] != ATTACK or r['defense'] != 'vanilla':
            continue
        if r['poison_rate'] != RATE:
            continue
        seen[r['retriever']] = r
for k in ('bm25', 'dense', 'st'):
    r = seen.get(k)
    if not r:
        continue
    label = {'bm25': 'BM25', 'dense': 'dense (hash)', 'st': 'GTE-base'}[k]
    print(f"{label:>16s} {num(r,'drift_tv'):>9.4f} {num(r,'stance_gap'):>9.4f} "
          f"{r['poison_in_topk']:>10s} {num(r,'in_pool_rate'):>8.4f}")

print()
print('=' * 96)
print(f'  B. does the R1-only constraint stay inert?  ({ATTACK}, rate {RATE})')
print('=' * 96)
print(f"{'retriever':>16s} {'defense':>12s} {'eps':>5s} {'poison@k':>10s} "
      f"{'vs vanilla':>12s} {'R2 gap':>9s}")
for k, label in (('bm25', 'BM25'), ('dense', 'dense (hash)'), ('st', 'GTE-base')):
    van = seen.get(k)
    if not van:
        continue
    van_pk = van['poison_in_topk']
    for rows in (full, gte):
        for r in rows:
            if (r['retriever'] != k or r['attack'] != ATTACK
                    or r['poison_rate'] != RATE):
                continue
            if r['defense'] not in ('repr_group', 'repr_both'):
                continue
            if r['epsilon'] not in ('0.0', '1.0'):
                continue
            pk = r['poison_in_topk']
            delta = 'same' if pk == van_pk else f'{pk} vs {van_pk}'
            print(f"{label:>16s} {r['defense']:>12s} {r['epsilon']:>5s} "
                  f"{pk:>10s} {delta:>12s} {num(r,'stance_gap'):>9.4f}")
    print()

print('=' * 96)
print('  C. template-only attack: does lexical poisoning survive a real encoder?')
print('=' * 96)
print(f"{'retriever':>16s} {'rate':>8s} {'poison@k':>10s} {'R1 drift':>9s} {'R2 gap':>9s}")
for rows, keys in ((full, ('bm25', 'dense')), (gte, ('bm25', 'st'))):
    for r in rows:
        if r['attack'] != 'template' or r['defense'] != 'vanilla':
            continue
        if r['retriever'] not in keys:
            continue
        label = {'bm25': 'BM25', 'dense': 'dense (hash)', 'st': 'GTE-base'}[r['retriever']]
        print(f"{label:>16s} {float(r['poison_rate']):>8.2%} {r['poison_in_topk']:>10s} "
              f"{num(r,'drift_tv'):>9.4f} {num(r,'stance_gap'):>9.4f}")
    print()
