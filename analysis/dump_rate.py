"""Injection-rate sweep: how poison@k and the R2 metric scale with rate."""
import csv
from collections import defaultdict


def load(p):
    return list(csv.DictReader(open(p, encoding='utf-8')))


for tag in ('full', 'bbq'):
    print('=' * 76)
    print(f'  {tag.upper()}')
    print('=' * 76)
    rows = load(f'results/{tag}/aggregate.csv')

    for retr in ('bm25', 'dense'):
        print(f'--- {retr}: no defense (vanilla) ---')
        print(f"{'attack':>26s} {'rate':>7s} {'R1 drift':>9s} {'R2 gap':>8s} "
              f"{'poison@k':>9s} {'util':>7s}")
        sub = [r for r in rows if r['defense'] == 'vanilla' and r['retriever'] == retr]
        for r in sorted(sub, key=lambda x: (x['attack'], float(x['poison_rate'] or -1))):
            rate = r['poison_rate']
            rate_s = f"{float(rate):.4%}" if rate else '-'
            print(f"{r['attack']:>26s} {rate_s:>7s} {float(r['drift_tv']):>9.4f} "
                  f"{float(r['stance_gap']):>8.4f} {r['poison_in_topk']:>9s} "
                  f"{float(r['in_pool_rate']):>7.4f}")
        print()

    # R1-only vs R2-constraining as a function of rate (dense, strongest attack)
    print('--- defense vs rate (dense, template_plus_projection) ---')
    print(f"{'rate':>7s} {'defense':>12s} {'eps':>5s} {'R1 drift':>9s} "
          f"{'R2 gap':>8s} {'poison@k':>9s}")
    sub = [r for r in rows
           if r['attack'] == 'template_plus_projection'
           and r['retriever'] == 'dense'
           and r['defense'] in ('vanilla', 'repr_group', 'repr_both')
           and r['epsilon'] in ('', '0.0', '1.0')]
    for r in sorted(sub, key=lambda x: (float(x['poison_rate']), x['defense'], x['epsilon'])):
        print(f"{float(r['poison_rate']):>7.4%} {r['defense']:>12s} {r['epsilon']:>5s} "
              f"{float(r['drift_tv']):>9.4f} {float(r['stance_gap']):>8.4f} "
              f"{r['poison_in_topk']:>9s}")
    print()
