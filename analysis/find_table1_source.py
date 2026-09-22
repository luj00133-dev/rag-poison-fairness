"""Locate which results directory backs Paper B's Table 1 numbers, since the
obvious candidate (results/full/adaptive.csv) does not match them.

Paper B Table 1, off-manifold filtering, controlled corpus:
    0.125 0.438 0.750 0.938 1.000 1.000
"""
import csv
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = [0.125, 0.438, 0.750, 0.938, 1.000, 1.000]
LAMS = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0]


def close(a, b):
    return abs(a - b) < 0.006


for path in sorted(glob.glob(os.path.join(ROOT, 'results', '*', 'adaptive.csv'))):
    tag = os.path.basename(os.path.dirname(path))
    rows = list(csv.DictReader(open(path, encoding='utf-8')))
    if not rows:
        continue
    by_def = {}
    for r in rows:
        by_def.setdefault(r['defense'], {})[round(float(r['lambda']), 2)] = r
    for dname, d in by_def.items():
        series = []
        for L in LAMS:
            r = d.get(L)
            series.append(float(r['poison_in_topk']) if r else None)
        if None in series:
            continue
        hits = sum(1 for a, b in zip(series, TARGET) if close(a, b))
        flag = '  <== MATCH (rounding-level)' if hits == 6 else ''
        if hits >= 4:
            print('%-22s %-18s %s  hits=%d/6%s'
                  % (tag, dname, ' '.join('%.3f' % v for v in series), hits, flag))

print()
print('--- all adaptive.csv files and their manifold series ---')
for path in sorted(glob.glob(os.path.join(ROOT, 'results', '*', 'adaptive.csv'))):
    tag = os.path.basename(os.path.dirname(path))
    rows = list(csv.DictReader(open(path, encoding='utf-8')))
    if not rows:
        continue
    by_def = {}
    for r in rows:
        if r['defense'] == 'manifold':
            by_def[round(float(r['lambda']), 2)] = float(r['poison_in_topk'])
    if not by_def:
        continue
    series = ['%.3f' % by_def[L] if L in by_def else '   - ' for L in LAMS]
    print('%-22s %s' % (tag, ' '.join(series)))
