"""Check whether the new R2 metric (stance_gap) responds to the attack."""
import csv
from collections import defaultdict

with open('results/full/aggregate.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print('=== R2 metrics, attack effect (no defense) ===')
print(f"{'attack':>26s} {'retr':>6s} {'R1 drift_tv':>12s} {'stance_gap':>11s} "
      f"{'one_sided':>10s} {'stance_div':>11s} {'poison@k':>9s}")
for r in rows:
    if r['defense'] != 'vanilla':
        continue
    print(f"{r['attack']:>26s} {r['retriever']:>6s} "
          f"{float(r['drift_tv']):>12.4f} {float(r['stance_gap']):>11.4f} "
          f"{float(r['stance_onesided']):>10.4f} {float(r['stance_div']):>11.4f} "
          f"{r['poison_in_topk']:>9s}")

print()
print('=== stance_gap by defense (attack = template_plus_projection) ===')
print(f"{'retr':>6s} {'defense':>12s} {'eps':>5s} {'stance_gap':>11s} {'poison@k':>9s}")
for r in rows:
    if r['attack'] != 'template_plus_projection':
        continue
    print(f"{r['retriever']:>6s} {r['defense']:>12s} {r['epsilon']:>5s} "
          f"{float(r['stance_gap']):>11.4f} {r['poison_in_topk']:>9s}")

print()
print('=== stance_gap by stratum, vanilla ===')
with open('results/full/by_stratum.csv', encoding='utf-8') as f:
    sr = list(csv.DictReader(f))
print(f"{'attack':>26s} {'stratum':>18s} {'R1 drift_tv':>12s} {'stance_gap':>11s}")
for r in sr:
    if r['defense'] != 'vanilla':
        continue
    print(f"{r['attack']:>26s} {r['stratum']:>18s} "
          f"{float(r['drift_tv']):>12.4f} {float(r['stance_gap']):>11.4f}")
