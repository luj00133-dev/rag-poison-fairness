"""Extract the adaptive-attacker collapse table across every backbone we have,
to check whether the collapse is abrupt only on real encoders (Paper B, 5.2b)."""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = [
    ('full', 'hash-dense (own)'),
    ('align_gte_ad', 'GTE-base'),
    ('align_e5', 'E5-base-v2'),
    ('align_splade', 'SPLADE'),
    ('bbq', 'BBQ / hash-dense'),
]
LAMS = ['0.0', '0.25', '0.5', '1.0', '2.0', '4.0']

for tag, label in DIRS:
    p = os.path.join(ROOT, 'results', tag, 'adaptive.csv')
    if not os.path.exists(p):
        print('%-20s (no adaptive.csv)' % label)
        continue
    rows = list(csv.DictReader(open(p, encoding='utf-8')))
    if not rows:
        print('%-20s (empty)' % label)
        continue
    lam_col = next((c for c in rows[0] if 'lambda' in c.lower()), None)
    def_col = next((c for c in rows[0] if 'defense' in c.lower()), None)
    pk_col = next((c for c in rows[0] if 'poison' in c.lower()), None)
    if not (lam_col and def_col and pk_col):
        print('%-20s columns=%s' % (label, list(rows[0])))
        continue
    print('=' * 72)
    print(label, ' lambda col=%r' % lam_col)
    defs = []
    for r in rows:
        if r[def_col] not in defs:
            defs.append(r[def_col])
    for d in defs:
        vals = {}
        for r in rows:
            if r[def_col] != d:
                continue
            key = str(float(r[lam_col]))
            vals[key] = float(r[pk_col])
        seq = []
        for L in LAMS:
            k = str(float(L))
            seq.append('%6.3f' % vals[k] if k in vals else '     -')
        print('  %-18s %s' % (d[:18], ' '.join(seq)))

print()
print('lambda order:', LAMS)
