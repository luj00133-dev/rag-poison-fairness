"""Empirical check of the formal analysis.

Predictions under test
----------------------
P1 (Prop. 1): an injection whose composition matches the reference is admissible
   at every epsilon, so the R1 constraint is inert -> poison@k identical to no
   defense, at all epsilon.

P2 (Prop. 2): the injection budget needed to violate a stance constraint for a
   group scales with that group's representation in the selection, is bounded by
   k+1, and is INDEPENDENT of corpus size. Test: does poison@k, at a fixed
   absolute injection count, change when the corpus grows?

P3 (Prop. 3, trilemma horn 2): tightening the budget to gain soundness costs
   utility -> a tight-epsilon constraint that blocks anything must also reduce
   in_pool_rate; if it blocks nothing it is inert.

Also reported: whether a tight budget ever buys a security improvement.
"""
import csv
from collections import defaultdict


def load(p):
    try:
        return list(csv.DictReader(open(p, encoding='utf-8')))
    except FileNotFoundError:
        return []


def num(r, k, d=float('nan')):
    try:
        return float(r[k])
    except (TypeError, ValueError):
        return d


print('=' * 88)
print('P1: is the R1 constraint inert at every epsilon?')
print('=' * 88)
print(f"{'corpus/backbone':>26s} {'eps':>5s} {'poison@k':>9s} {'vanilla':>9s} "
      f"{'delta':>7s} {'util':>8s} {'delta_util':>11s}")

sources = [
    ('controlled / BM25', 'results/full/aggregate.csv', 'bm25'),
    ('controlled / hash-dense', 'results/full/aggregate.csv', 'dense'),
    ('BBQ / BM25', 'results/bbq/aggregate.csv', 'bm25'),
    ('BBQ / hash-dense', 'results/bbq/aggregate.csv', 'dense'),
    ('controlled / GTE-base', 'results/align_ctl/aggregate.csv', 'st'),
    ('controlled / Contriever', 'results/align_multi/aggregate.csv', 'st'),
]

for label, path, retr in sources:
    rows = load(path)
    # pick the strongest available attack and mid injection rate
    cands = [r for r in rows if r['defense'] == 'vanilla' and r['retriever'] == retr]
    if not cands:
        continue
    attacks = sorted({r['attack'] for r in cands})
    attack = 'template_plus_projection' if 'template_plus_projection' in attacks else attacks[-1]
    rates = sorted({r['poison_rate'] for r in cands if r['poison_rate']})
    rate = rates[-1] if rates else ''

    def find(defense, eps):
        for r in rows:
            if (r['defense'] == defense and r['epsilon'] == eps
                    and r['retriever'] == retr and r['attack'] == attack
                    and r['poison_rate'] == rate):
                if defense == 'vanilla' or r.get('backbone', '') in ('', label.split('/ ')[-1]
                        .replace('GTE-base', 'gte-base').replace('Contriever', 'contriever')):
                    return r
        return None

    van = find('vanilla', '')
    if not van:
        continue
    for eps in ('1.0', '0.5', '0.25', '0.1', '0.0'):
        r = None
        for x in rows:
            bb = x.get('backbone', '')
            want = 'gte-base' if 'GTE' in label else ('contriever' if 'Contriever' in label else '')
            if (x['defense'] == 'repr_group' and x['epsilon'] == eps
                    and x['retriever'] == retr and x['attack'] == attack
                    and x['poison_rate'] == rate and (not want or bb == want)):
                r = x
                break
        if not r:
            continue
        d_pk = num(r, 'poison_in_topk') - num(van, 'poison_in_topk')
        d_ut = num(r, 'in_pool_rate') - num(van, 'in_pool_rate')
        print(f"{label:>26s} {eps:>5s} {num(r,'poison_in_topk'):>9.3f} "
              f"{num(van,'poison_in_topk'):>9.3f} {d_pk:>7.3f} "
              f"{num(r,'in_pool_rate'):>8.4f} {d_ut:>11.4f}")
    print()

print('=' * 88)
print('P2: does the injection budget depend on corpus size?')
print('=' * 88)
print('Fixed ABSOLUTE injection count vs corpus size, and the resulting poison@k.')
print('Prop. 2 predicts the required count is bounded by k+1 and independent of')
print('corpus size; a dependence would falsify it.')
print()
print(f"{'corpus':>22s} {'n_docs':>8s} {'count/stratum':>14s} {'poison@k':>9s} {'rate':>8s}")
for label, path, retr, ndocs in (
    ('controlled / BM25', 'results/full/aggregate.csv', 'bm25', 1824),
    ('BBQ / BM25', 'results/bbq/aggregate.csv', 'bm25', 17792),
):
    for r in load(path):
        if (r['defense'] == 'vanilla' and r['retriever'] == retr
                and r['attack'] == 'template' and r['poison_rate']):
            rate = float(r['poison_rate'])
            cnt = round(rate * ndocs)
            print(f"{label:>22s} {ndocs:>8d} {cnt:>14d} {num(r,'poison_in_topk'):>9.3f} "
                  f"{rate:>8.2%}")

print()
print('=' * 88)
print('P3: does a tight budget ever buy a security gain?  (trilemma horn 2)')
print('=' * 88)
print(f"{'corpus/backbone':>26s} {'eps=1.0 pk':>11s} {'eps=0.0 pk':>11s} "
      f"{'gain':>8s} {'util 1.0':>9s} {'util 0.0':>9s}")
for label, path, retr in sources:
    rows = load(path)
    attack = 'template_plus_projection'
    rates = sorted({r['poison_rate'] for r in rows if r['poison_rate'] and r['retriever'] == retr})
    if not rates:
        continue
    rate = rates[-1]
    want = 'gte-base' if 'GTE' in label else ('contriever' if 'Contriever' in label else '')
    out = {}
    for eps in ('1.0', '0.0'):
        for r in rows:
            bb = r.get('backbone', '')
            if (r['defense'] == 'repr_group' and r['epsilon'] == eps
                    and r['retriever'] == retr and r['attack'] == attack
                    and r['poison_rate'] == rate and (not want or bb == want)):
                out[eps] = r
    if '1.0' in out and '0.0' in out:
        a, b = out['1.0'], out['0.0']
        gain = num(a, 'poison_in_topk') - num(b, 'poison_in_topk')
        print(f"{label:>26s} {num(a,'poison_in_topk'):>11.3f} "
              f"{num(b,'poison_in_topk'):>11.3f} {gain:>8.3f} "
              f"{num(a,'in_pool_rate'):>9.4f} {num(b,'in_pool_rate'):>9.4f}")
