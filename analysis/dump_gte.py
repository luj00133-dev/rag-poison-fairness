"""Dump GTE-base alignment results (retriever name is 'st:gte-base')."""
import csv
import sys

p = sys.argv[1] if len(sys.argv) > 1 else 'results/st_gte/aggregate.csv'
rows = list(csv.DictReader(open(p, encoding='utf-8')))
print(f'file: {p}  rows={len(rows)}')
print('retrievers:', sorted({r['retriever'] for r in rows}))
print('attacks   :', sorted({r['attack'] for r in rows}))
print('defenses  :', sorted({r['defense'] for r in rows}))
print('rates     :', sorted({r['poison_rate'] for r in rows}))
print()


def num(r, k):
    try:
        return float(r[k])
    except (TypeError, ValueError):
        return float('nan')


hdr = ('attack', 'retriever', 'defense', 'eps', 'rate', 'R1', 'R2gap', 'poison@k')
print(' | '.join(hdr))
for r in sorted(rows, key=lambda x: (x['attack'], x['retriever'], x['defense'],
                                     x['epsilon'], x['poison_rate'] or '')):
    if r['defense'] not in ('vanilla', 'multi_query', 'manifold',
                            'repr_group', 'repr_both', 'repr_stance'):
        continue
    if r['epsilon'] not in ('', '0.0', '1.0'):
        continue
    print(' | '.join([
        r['attack'], r['retriever'], r['defense'], r['epsilon'] or '-',
        r['poison_rate'] or '-',
        f"{num(r,'drift_tv'):.4f}", f"{num(r,'stance_gap'):.4f}",
        r['poison_in_topk'],
    ]))
