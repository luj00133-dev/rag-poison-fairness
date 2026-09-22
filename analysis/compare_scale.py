"""Scale check for Paper A Limitation 5: does the spread in text-attack
susceptibility among *base* encoders persist when the encoder is scaled up?

Limitation 5 asserted that the larger checkpoints "give no reason to expect
agreement". That was a prediction, not a measurement. This script measures it by
pairing each base encoder with its larger sibling:

    GTE-base      -> GTE-large
    E5-base-v2    -> E5-large-v2
    SPLADE distil -> SPLADE efficient-large (split query/doc encoders)

Filtering matters here: a run's ``aggregate.csv`` holds the lexical back-end and
the neural back-end side by side, with ``backbone`` empty for the lexical rows.
Matching only on (attack, rate, defense) silently returns whichever row comes
first -- BM25's -- and reports the lexical numbers as if they were the encoder's.
Every selector below therefore matches on ``retriever`` and ``backbone`` too.
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: (results dir, label, family, size, retriever, backbone-as-stored)
#:
#: ``backbone`` is only populated for ``st`` rows in the committed results;
#: SPLADE and hashed rows leave it blank. They are not ambiguous within their own
#: run, because ``retriever`` already separates them from that run's BM25 rows
#: (``splade`` and ``dense`` respectively). Both keys are matched together so a
#: cell can never silently fall back to the lexical row.
RUNS = [
    ('full', 'hash-dense (own)', 'hashed', '-', 'dense', ''),
    ('align_gte_ad', 'GTE-base', 'dense semantic', 'base', 'st', 'gte-base'),
    ('align_gte_large', 'GTE-large', 'dense semantic', 'large', 'st', 'gte-large'),
    ('align_e5', 'E5-base-v2', 'dense semantic', 'base', 'st', 'e5-base-v2'),
    ('align_e5_large', 'E5-large-v2', 'dense semantic', 'large', 'st', 'e5-large-v2'),
    ('align_splade', 'SPLADE distil', 'learned sparse', 'base', 'splade', ''),
    ('align_splade_large', 'SPLADE large', 'learned sparse', 'large', 'splade', ''),
    ('full', 'BM25 (lexical)', 'lexical sparse', '-', 'bm25', ''),
]


def load(tag):
    p = os.path.join(ROOT, 'results', tag, 'aggregate.csv')
    if not os.path.exists(p):
        return None
    return list(csv.DictReader(open(p, encoding='utf-8')))


def cell(rows, *, attack, rate, retriever, backbone, defense='vanilla',
         epsilon='', budget_mode=None):
    """One aggregate cell. Returns None rather than a wrong-row fallback."""
    for r in rows:
        if r.get('attack') != attack:
            continue
        if r.get('retriever') != retriever:
            continue
        if (r.get('backbone') or '') != (backbone or ''):
            continue
        if r.get('defense') != defense:
            continue
        if (r.get('epsilon') or '') != (epsilon or ''):
            continue
        if budget_mode is not None and r.get('defense') != budget_mode:
            continue
        got = r.get('poison_rate') or ''
        if rate is None:
            if got != '':
                continue
        else:
            try:
                if abs(float(got) - rate) > 1e-9:
                    continue
            except ValueError:
                continue
        return r
    return None


def num(r, key):
    if r is None:
        return None
    v = (r.get(key) or '').strip()
    if v in ('', 'nan', 'None'):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def f(v, nd=4, width=9):
    return ('%.' + str(nd) + 'f') % v if v is not None else 'n/a'.rjust(width)


def table(title, attack, rate):
    print(title)
    print()
    print('%-18s %-16s %-6s %10s %10s %10s' % (
        'backbone', 'family', 'size', 'poison@k', 'R1 drift', 'R2 gap'))
    got = {}
    for tag, label, family, size, rk, bb in RUNS:
        rows = data.get(tag)
        if rows is None:
            print('%-18s %-16s %-6s %10s' % (label, family, size, '(no data)'))
            continue
        r = cell(rows, attack=attack, rate=rate, retriever=rk, backbone=bb)
        got[label] = r
        print('%-18s %-16s %-6s %10s %10s %10s' % (
            label, family, size,
            f(num(r, 'poison_in_topk')), f(num(r, 'drift_tv')),
            f(num(r, 'stance_gap'))))
    print()
    return got


def inertness(attack, rate):
    print('R1-only constraint inertness at scale (%s, rho=%.1f%%)'
          % (attack, rate * 100))
    print()
    print('%-18s %10s %10s %10s %12s' % (
        'backbone', 'vanilla', 'R1 e=0', 'R1+R2 e=0', 'max |delta|'))
    rowsout = []
    for tag, label, family, size, rk, bb in RUNS:
        rows = data.get(tag)
        if rows is None:
            continue
        van = cell(rows, attack=attack, rate=rate, retriever=rk, backbone=bb)
        base = num(van, 'poison_in_topk')
        if base is None:
            print('%-18s %10s   (no vanilla cell)' % (label, 'n/a'))
            continue
        constrained = []
        for r in rows:
            if r.get('attack') != attack or r.get('retriever') != rk:
                continue
            if (r.get('backbone') or '') != (bb or ''):
                continue
            if r.get('defense') not in ('repr_group', 'repr_both'):
                continue
            if (r.get('epsilon') or '') not in ('0.0', '0'):
                continue
            try:
                if abs(float(r.get('poison_rate') or 0) - rate) > 1e-9:
                    continue
            except ValueError:
                continue
            pk = num(r, 'poison_in_topk')
            if pk is not None:
                constrained.append((r['defense'], pk))
        if not constrained:
            print('%-18s %10s   (no constrained cells)' % (label, f(base)))
            continue
        deltas = [abs(pk - base) for _, pk in constrained]
        g = [pk for d, pk in constrained if d == 'repr_group']
        b = [pk for d, pk in constrained if d == 'repr_both']
        rowsout.append((label, base, g, b, max(deltas)))
        print('%-18s %10s %10s %10s %12.4f' % (
            label, f(base), f(g[0]) if g else 'n/a',
            f(b[0]) if b else 'n/a', max(deltas)))
    print()
    return rowsout


data = {}
for tag, label, family, size, rk, bb in RUNS:
    if tag not in data:
        data[tag] = load(tag)

print('=' * 80)
print('SCALE CHECK -- Paper A Limitation 5')
print('Does the encoder split in text-attack susceptibility survive scaling?')
print('=' * 80)
print()

text_rows = table('A. TEXT-ONLY (lexical) attack, rho=0.5%, no defense',
                  'template', 0.005)
proj_rows = table('B. Projection attack, rho=0.5%, no defense',
                  'template_plus_projection', 0.005)
inert_ctl = inertness('template_plus_projection', 0.005)

print('=' * 80)
print('C. VERDICT per base/large pair (text attack, poison@k)')
print('=' * 80)
print()
PAIRS = [
    ('GTE', 'GTE-base', 'GTE-large'),
    ('E5', 'E5-base-v2', 'E5-large-v2'),
    ('SPLADE', 'SPLADE distil', 'SPLADE large'),
]
for name, bl, ll in PAIRS:
    b = num(text_rows.get(bl), 'poison_in_topk')
    l = num(text_rows.get(ll), 'poison_in_topk')
    if b is None or l is None:
        print('  %-7s : base=%-9s large=%-9s  (incomplete)' % (
            name, f(b), f(l)))
        continue
    if max(b, l) < 0.15:
        verdict = 'RESISTANT at both scales -- split persists'
    elif min(b, l) > 0.3:
        verdict = 'SUSCEPTIBLE at both scales -- split persists'
    else:
        verdict = '** SUSCEPTIBILITY CHANGES WITH SCALE **'
    print('  %-7s : base %-9s -> large %-9s  %s' % (name, f(b), f(l), verdict))

print()
print('  Reference: the claim under test is that base-size encoders differ')
print('  nine-fold (Contriever 0.5625 vs GTE-base / E5-base-v2 at 0.0625).')
