import csv

with open('results/full/aggregate.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print('=== NO-DEFENSE ROWS (vanilla) ===')
hdr = ('attack', 'retriever', 'drift_tv', 'drift_js', 'stance_div',
       'poison@k', 'util', 'mean_score')
print(' | '.join(hdr))
for r in rows:
    if r['defense'] != 'vanilla':
        continue
    print(' | '.join([
        r['attack'], r['retriever'],
        f"{float(r['drift_tv']):.4f}", f"{float(r['drift_js']):.4f}",
        f"{float(r['stance_div']):.4f}", r['poison_in_topk'],
        f"{float(r['in_pool_rate']):.4f}", f"{float(r['mean_score']):.4f}",
    ]))

print()
print('=== OTHER DEFENSES under template_plus_projection ===')
for r in rows:
    if r['attack'] != 'template_plus_projection' or r['defense'] == 'vanilla':
        continue
    print(' | '.join([
        r['retriever'], r['defense'], r['epsilon'],
        f"{float(r['drift_tv']):.4f}", f"{float(r['stance_div']):.4f}",
        r['poison_in_topk'], f"{float(r['in_pool_rate']):.4f}",
        f"{float(r['mean_score']):.4f}",
    ]))

print()
print('=== ADAPTIVE (poison@k) ===')
with open('results/full/adaptive.csv', encoding='utf-8') as f:
    ad = list(csv.DictReader(f))
for r in ad:
    print(' | '.join([
        r['defense'], r['lambda'], r['poison_in_topk'],
        f"{float(r['drift_tv']):.4f}", f"{float(r.get('stance_div','nan')):.4f}",
    ]))
