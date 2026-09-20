"""Adaptive-attacker comparison across backbones."""
import csv
import os

for tag in ('align_multi', 'align_gte_ad'):
    p = os.path.join('results', tag, 'adaptive.csv')
    if not os.path.exists(p):
        print(f'{tag}: no file')
        continue
    rows = list(csv.DictReader(open(p, encoding='utf-8')))
    lams = sorted({float(r['lambda']) for r in rows})
    print(f'--- {tag} ---')
    print('  defense'.ljust(20) + ''.join(f'{l:>8.2f}' for l in lams))
    for d in sorted({r['defense'] for r in rows}):
        sub = {float(r['lambda']): r for r in rows if r['defense'] == d}
        cells = ''.join(f"{sub[l]['poison_in_topk']:>8s}" for l in lams)
        print(f'  {d:<18s}{cells}')
    print()
