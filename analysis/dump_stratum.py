import csv
from collections import defaultdict

with open('results/full/by_stratum.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print('=== stance_div by stratum, attack=template_plus_projection, defense=vanilla ===')
print(f"{'stratum':>18s} {'drift_tv':>9s} {'stance_div':>11s} {'poison@k':>9s} {'n':>5s}")
for r in rows:
    if r['attack'] == 'template_plus_projection' and r['defense'] == 'vanilla':
        print(f"{r['stratum']:>18s} {float(r['drift_tv']):>9.4f} "
              f"{float(r['stance_div']):>11.4f} {r['poison_in_topk']:>9s} {r['n_queries']:>5s}")

print()
print('=== stance_shift (rate form) vs stance_div (divergence form), vanilla ===')
print(f"{'attack':>26s} {'stratum':>18s} {'stance_shift':>13s} {'stance_div':>11s}")
for r in rows:
    if r['defense'] != 'vanilla':
        continue
    print(f"{r['attack']:>26s} {r['stratum']:>18s} "
          f"{float(r['stance_shift']):>13.4f} {float(r['stance_div']):>11.4f}")

print()
print('=== repr_stance vs vanilla, stance_div by stratum ===')
d = defaultdict(dict)
for r in rows:
    if r['attack'] != 'template_plus_projection':
        continue
    if r['defense'] == 'vanilla':
        d[r['stratum']]['vanilla'] = float(r['stance_div'])
    if r['defense'] == 'repr_stance' and r['epsilon'] == '0.0':
        d[r['stratum']]['repr_stance_eps0'] = float(r['stance_div'])
    if r['defense'] == 'repr_group' and r['epsilon'] == '0.0':
        d[r['stratum']]['repr_group_eps0'] = float(r['stance_div'])
print(f"{'stratum':>18s} {'vanilla':>9s} {'R1only':>9s} {'R2only':>9s}")
for st in sorted(d):
    print(f"{st:>18s} {d[st].get('vanilla', float('nan')):>9.4f} "
          f"{d[st].get('repr_group_eps0', float('nan')):>9.4f} "
          f"{d[st].get('repr_stance_eps0', float('nan')):>9.4f}")
