"""Five-way backbone comparison: BM25 / hash / GTE-base / Contriever / E5-base."""
import csv
import os

ATTACKS = ('template', 'template_plus_projection')
RATE = '0.005'
K = 5

LABEL = {
    ('bm25', ''): 'BM25 (lexical)',
    ('dense', ''): 'dense (hash)',
    ('st', 'gte-base'): 'GTE-base',
    ('st', 'contriever'): 'Contriever',
    ('st', 'e5-base-v2'): 'E5-base-v2',
}
ORDER = [('bm25', ''), ('dense', ''), ('st', 'gte-base'),
         ('st', 'contriever'), ('st', 'e5-base-v2')]


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


rows = (load('results/full/aggregate.csv')
        + load('results/align_multi/aggregate.csv')
        + load('results/align_e5/aggregate.csv'))


def get(attack, defense, eps, rate, retr, bb):
    for r in rows:
        if (r['attack'] == attack and r['defense'] == defense
                and r['epsilon'] == eps and r['poison_rate'] == rate
                and r['retriever'] == retr and r.get('backbone', '') == bb):
            return r
    return None


print('=' * 94)
print(f'A. attack effect, {ATTACKS[1]}, rate {RATE}, no defense')
print('=' * 94)
print(f"{'retriever':>18s} {'R1 drift':>9s} {'R2 gap':>9s} {'poison@k':>10s} {'util':>8s}")
for k in ORDER:
    r = get(ATTACKS[1], 'vanilla', '', RATE, *k)
    if not r:
        print(f"{LABEL[k]:>18s}   (missing)")
        continue
    print(f"{LABEL[k]:>18s} {num(r,'drift_tv'):>9.4f} {num(r,'stance_gap'):>9.4f} "
          f"{r['poison_in_topk']:>10s} {num(r,'in_pool_rate'):>8.4f}")

print()
print('=' * 94)
print(f'B. R1-only constraint inertness: Delta poison@k vs no defense')
print('=' * 94)
print(f"{'retriever':>18s} {'eps=0.0':>10s} {'eps=1.0':>10s} {'R1+R2 eps=0':>13s} "
      f"{'vanilla pk':>11s}")
n_zero = 0
n_cells = 0
for k in ORDER:
    van = get(ATTACKS[1], 'vanilla', '', RATE, *k)
    if not van:
        continue
    vpk = num(van, 'poison_in_topk')
    cells = []
    for defense, eps in (('repr_group', '0.0'), ('repr_group', '1.0'),
                         ('repr_both', '0.0')):
        r = get(ATTACKS[1], defense, eps, RATE, *k)
        if r is None:
            cells.append('   -   ')
            continue
        d = num(r, 'poison_in_topk') - vpk
        n_cells += 1
        if abs(d) < 1e-9:
            n_zero += 1
        cells.append(f'{d:>10.3f}')
    print(f"{LABEL[k]:>18s} {cells[0]:>10s} {cells[1]:>10s} {cells[2]:>13s} "
          f"{vpk:>11.3f}")
print(f"\n  cells with Delta = 0.000 : {n_zero} / {n_cells}")

print()
print('=' * 94)
print('C. text-only (lexical) attack by backbone -- the encoder-sensitivity result')
print('=' * 94)
print(f"{'retriever':>18s} {'@0.5%':>9s} {'@2%':>9s} {'R1 drift @0.5%':>16s} {'R2 gap @0.5%':>14s}")
vals = {}
for k in ORDER:
    out = []
    for rate in ('0.005', '0.02'):
        r = get('template', 'vanilla', '', rate, *k)
        out.append(num(r, 'poison_in_topk') if r else float('nan'))
    r5 = get('template', 'vanilla', '', '0.005', *k)
    vals[k] = out[0]
    print(f"{LABEL[k]:>18s} {out[0]:>9.4f} {out[1]:>9.4f} "
          f"{(num(r5,'drift_tv') if r5 else float('nan')):>16.4f} "
          f"{(num(r5,'stance_gap') if r5 else float('nan')):>14.4f}")

enc = [v for kk, v in vals.items() if kk[0] == 'st' and v == v]
if len(enc) >= 2:
    print(f"\n  spread across the {len(enc)} real encoders: "
          f"min={min(enc):.4f}  max={max(enc):.4f}  ratio={max(enc)/max(min(enc),1e-9):.1f}x")

print()
print('=' * 94)
print('D. adaptive attacker on E5-base (poison@k by lambda)')
print('=' * 94)
ad = load('results/align_e5/adaptive.csv')
if ad:
    lams = sorted({float(r['lambda']) for r in ad})
    print(f"{'defense':>16s} " + ' '.join(f'{l:>8.2f}' for l in lams))
    for d in sorted({r['defense'] for r in ad}):
        sub = {float(r['lambda']): r for r in ad if r['defense'] == d}
        print(f"{d:>16s} " + ' '.join(
            f"{sub[l]['poison_in_topk']:>8s}" if l in sub else f"{'-':>8s}" for l in lams))
