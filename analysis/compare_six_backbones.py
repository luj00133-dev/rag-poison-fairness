"""Six-way backbone comparison: is susceptibility about sparsity or semantics?"""
import csv


def load(p):
    try:
        return list(csv.DictReader(open(p, encoding='utf-8')))
    except FileNotFoundError:
        return []


rows = (load('results/full/aggregate.csv')
        + load('results/align_multi/aggregate.csv')
        + load('results/align_e5/aggregate.csv')
        + load('results/align_splade/aggregate.csv'))

KIND = {
    ('bm25', ''): ('BM25', 'lexical, unsupervised sparse'),
    ('dense', ''): ('hash-dense', 'hashed (not semantic)'),
    ('splade', ''): ('SPLADE', 'LEARNED sparse'),
    ('st', 'gte-base'): ('GTE-base', 'dense semantic'),
    ('st', 'contriever'): ('Contriever', 'dense semantic'),
    ('st', 'e5-base-v2'): ('E5-base-v2', 'dense semantic'),
}
ORDER = [('bm25', ''), ('dense', ''), ('splade', ''),
         ('st', 'gte-base'), ('st', 'contriever'), ('st', 'e5-base-v2')]
RATE = '0.005'


def get(attack, defense, eps, rate, retr, bb):
    for r in rows:
        if (r['attack'] == attack and r['defense'] == defense
                and r['epsilon'] == eps and r['poison_rate'] == rate
                and r['retriever'] == retr and r.get('backbone', '') == bb):
            return r
    return None


def num(r, k):
    try:
        return float(r[k])
    except (TypeError, ValueError):
        return float('nan')


print('=' * 92)
print('A. text-only (lexical) attack: does susceptibility track SPARSITY or SEMANTICS?')
print('=' * 92)
print(f"{'retriever':>13s} {'family':<26s} {'poison@k':>10s} {'R1 drift':>9s} {'R2 gap':>8s}")
for k in ORDER:
    r = get('template', 'vanilla', '', RATE, *k)
    if not r:
        print(f"{KIND[k][0]:>13s} {'(missing)':<26s}")
        continue
    print(f"{KIND[k][0]:>13s} {KIND[k][1]:<26s} {num(r,'poison_in_topk'):>10.4f} "
          f"{num(r,'drift_tv'):>9.4f} {num(r,'stance_gap'):>8.4f}")

print()
print('=' * 92)
print('B. projection attack + R1-only constraint inertness')
print('=' * 92)
print(f"{'retriever':>13s} {'R1 drift':>9s} {'R2 gap':>8s} {'vanilla pk':>11s} "
      f"{'R1only e0':>10s} {'delta':>7s} {'R1+R2 e0':>9s} {'delta':>7s}")
nz = ncell = 0
for k in ORDER:
    van = get('template_plus_projection', 'vanilla', '', RATE, *k)
    if not van:
        continue
    vpk = num(van, 'poison_in_topk')
    out = {}
    for d, e in (('repr_group', '0.0'), ('repr_both', '0.0')):
        r = get('template_plus_projection', d, e, RATE, *k)
        out[d] = r
        if r:
            ncell += 1
            if abs(num(r, 'poison_in_topk') - vpk) < 1e-9:
                nz += 1
    g = out.get('repr_group')
    b = out.get('repr_both')
    gd = (num(g, 'poison_in_topk') - vpk) if g else float('nan')
    bd = (num(b, 'poison_in_topk') - vpk) if b else float('nan')
    print(f"{KIND[k][0]:>13s} {num(van,'drift_tv'):>9.4f} {num(van,'stance_gap'):>8.4f} "
          f"{vpk:>11.4f} {num(g,'poison_in_topk') if g else float('nan'):>10.4f} "
          f"{gd:>7.3f} {num(b,'poison_in_topk') if b else float('nan'):>9.4f} {bd:>7.3f}")
print(f"\n  R1-constrained cells with delta = 0.000 : {nz} / {ncell}")

print()
print('=' * 92)
print('C. adaptive attacker, poison@k by lambda')
print('=' * 92)
for tag, label in (('align_splade', 'SPLADE'), ('align_e5', 'E5-base-v2')):
    ad = load(f'results/{tag}/adaptive.csv')
    if not ad:
        continue
    lams = sorted({float(r['lambda']) for r in ad})
    print(f'--- {label} ---')
    print(f"{'defense':>16s} " + ' '.join(f'{l:>8.2f}' for l in lams))
    for d in sorted({r['defense'] for r in ad}):
        sub = {float(r['lambda']): r for r in ad if r['defense'] == d}
        print(f"{d:>16s} " + ' '.join(
            f"{sub[l]['poison_in_topk']:>8s}" if l in sub else f"{'-':>8s}"
            for l in lams))
    print()
