"""Verify the E5-base-v2 numbers quoted in Tables 8, 9 and 10."""
import csv


def load(p):
    return list(csv.DictReader(open(p, encoding='utf-8')))


rows = load('results/align_e5/aggregate.csv')


def g(attack, defense, eps, rate):
    for r in rows:
        if (r['attack'] == attack and r['defense'] == defense
                and r['epsilon'] == eps and r['poison_rate'] == rate
                and r['backbone'] == 'e5-base-v2'):
            return r
    return None


v = g('template_plus_projection', 'vanilla', '', '0.005')
print('Table 8 (E5 row):')
print(f"  R1 drift  = {float(v['drift_tv']):.4f}   (paper says 0.4000)")
print(f"  R2 gap    = {float(v['stance_gap']):.4f}   (paper says 1.0000)")
print(f"  poison@k  = {v['poison_in_topk']}         (paper says 1.000)")
print(f"  in_pool   = {float(v['in_pool_rate']):.4f}   (paper says 0.0000)")

print()
print('Table 9 (E5 row):')
for d, e in (('repr_group', '0.0'), ('repr_group', '1.0'), ('repr_both', '0.0')):
    r = g('template_plus_projection', d, e, '0.005')
    delta = float(r['poison_in_topk']) - float(v['poison_in_topk'])
    print(f"  {d:<12s} eps={e:<4s} poison@k={r['poison_in_topk']}  "
          f"delta={delta:.3f}   (paper says 0.000)")

print()
print('Table 10 (E5 row):')
for rate in ('0.005', '0.02'):
    r = g('template', 'vanilla', '', rate)
    print(f"  template @{float(rate):.1%}: poison@k={r['poison_in_topk']}  "
          f"R1 drift={float(r['drift_tv']):.4f}   (paper says 0.0625 / 0.0000)")
