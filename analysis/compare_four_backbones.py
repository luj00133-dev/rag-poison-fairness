"""Four-way backbone comparison: BM25 / feature-hashing / GTE-base / Contriever.

Uses results/align_multi (which sweeps both real encoders) plus results/full for
the lexical and hashed retrievers, all on the controlled corpus so only the
retriever varies.
"""
import csv

ATTACK = 'template_plus_projection'
RATE = '0.005'

LABEL = {
    ('bm25', ''): 'BM25 (lexical)',
    ('dense', ''): 'dense (hash)',
    ('st', 'gte-base'): 'GTE-base',
    ('st', 'contriever'): 'Contriever',
}


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


full = load('results/full/aggregate.csv')
multi = load('results/align_multi/aggregate.csv')
rows = full + multi


def key(r):
    return (r['retriever'], r.get('backbone', ''))


def pick(attack, defense, eps, rate, retr, bb):
    for r in rows:
        if (r['attack'] == attack and r['defense'] == defense
                and r['epsilon'] == eps and r['poison_rate'] == rate
                and r['retriever'] == retr and r.get('backbone', '') == bb):
            return r
    return None


order = [('bm25', ''), ('dense', ''), ('st', 'gte-base'), ('st', 'contriever')]

print('=' * 92)
print(f'A. attack effect, {ATTACK}, rate {RATE}, no defense')
print('=' * 92)
print(f"{'retriever':>18s} {'R1 drift':>9s} {'R2 gap':>9s} {'poison@k':>10s} {'util':>8s}")
base_pk = {}
for k in order:
    r = pick(ATTACK, 'vanilla', '', RATE, *k)
    if not r:
        print(f"{LABEL[k]:>18s}   (missing)")
        continue
    base_pk[k] = r['poison_in_topk']
    print(f"{LABEL[k]:>18s} {num(r,'drift_tv'):>9.4f} {num(r,'stance_gap'):>9.4f} "
          f"{r['poison_in_topk']:>10s} {num(r,'in_pool_rate'):>8.4f}")

print()
print('=' * 92)
print(f'B. R1-only vs R1+R2 constraint, {ATTACK}, rate {RATE}')
print('=' * 92)
print(f"{'retriever':>18s} {'defense':>12s} {'eps':>5s} {'poison@k':>10s} "
      f"{'vs vanilla':>11s} {'R2 gap':>9s}")
for k in order:
    van = pick(ATTACK, 'vanilla', '', RATE, *k)
    if not van:
        continue
    for defense in ('repr_group', 'repr_both'):
        for eps in ('0.0', '1.0'):
            r = pick(ATTACK, defense, eps, RATE, *k)
            if not r:
                continue
            pk = r['poison_in_topk']
            delta = 'same' if pk == van['poison_in_topk'] else f"{pk} vs {van['poison_in_topk']}"
            print(f"{LABEL[k]:>18s} {defense:>12s} {eps:>5s} {pk:>10s} "
                  f"{delta:>11s} {num(r,'stance_gap'):>9.4f}")
    print()

print('=' * 92)
print(f'C. template-only attack (lexical surface), by rate, no defense')
print('=' * 92)
print(f"{'retriever':>18s} {'rate':>8s} {'poison@k':>10s} {'R1 drift':>9s} {'R2 gap':>9s}")
for k in order:
    seen_any = False
    for r in sorted([x for x in rows if x['attack'] == 'template'
                     and x['defense'] == 'vanilla' and key(x) == k],
                    key=lambda x: x['poison_rate'] or ''):
        seen_any = True
        print(f"{LABEL[k]:>18s} {float(r['poison_rate']):>8.2%} {r['poison_in_topk']:>10s} "
              f"{num(r,'drift_tv'):>9.4f} {num(r,'stance_gap'):>9.4f}")
    if not seen_any:
        print(f"{LABEL[k]:>18s}   (missing)")
    print()

print('=' * 92)
print('D. adaptive attacker, poison@k by lambda (Contriever vs GTE-base)')
print('=' * 92)
ad = load('results/align_multi/adaptive.csv')
lams = sorted({float(r['lambda']) for r in ad}) if ad else []
print(f"{'defense':>16s} " + ' '.join(f'{l:>8.2f}' for l in lams))
for d in sorted({r['defense'] for r in ad}):
    sub = {float(r['lambda']): r for r in ad if r['defense'] == d}
    print(f"{d:>16s} " + ' '.join(
        f"{sub[l]['poison_in_topk']:>8s}" if l in sub else f"{'-':>8s}" for l in lams))
