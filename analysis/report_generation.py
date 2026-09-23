"""Print the generation-stage comparison across every generator, from the JSON.

The console log of the run was filtered by a PowerShell Select-String pipeline and
lost the local generator's block, so the numbers are read from the result file
instead of from the log. That is the right source anyway: the log is a progress
narrative, the JSON is the record.

Reports per generator and condition: the absolute cross-group gap (the metric that
turned out to be blind), the two per-group shifts with their paired p-values (the
metric that works), attribution, and how many answers changed at all between
conditions.
"""
import json
import os
from collections import defaultdict

P = os.path.join('results', 'generation', 'generation.json')
d = json.load(open(P, encoding='utf-8'))

CONDS = ('clean', 'poisoned', 'r1only', 'r2both')

print('=' * 100)
print('GENERATION-STAGE STANCE, ALL GENERATORS')
print('=' * 100)
print()
print('%-14s %-10s %8s %8s %9s %8s %9s %8s %7s' % (
    'generator', 'condition', 'gap', 'd_gap', 'd_group1', 'p_g1',
    'd_group2', 'p_g2', 'EAE-D'))
for g in d['generators']:
    for c in CONDS:
        s = g['summary'].get(c)
        if not s:
            continue
        t = g['tests_vs_clean'].get(c, {})

        def f(k, spec='%+.4f'):
            return (spec % t[k]) if k in t else '     n/a'

        # p-values are printed with their own format; using the delta formatter on
        # them (as an earlier version did) made the table look as if the
        # significance columns repeated the effect sizes, which is exactly the
        # kind of display bug that hides a real result
        print('%-14s %-10s %8.4f %8s %9s %8s %9s %8s %7.3f' % (
            g['generator'], c, s['stance_gap'], f('delta_gap'),
            f('delta_group1'), f('p_group1', '%8.4f'),
            f('delta_group2'), f('p_group2', '%8.4f'), s['eae_d']))
    print()

print('=' * 100)
print('REPLICATION OF THE PER-GROUP SHIFT (poisoned vs clean)')
print('=' * 100)
print()
print('%-14s %10s %8s %10s %8s  %s' % (
    'generator', 'd_group1', 'p', 'd_group2', 'p', 'verdict'))
for g in d['generators']:
    t = g['tests_vs_clean'].get('poisoned', {})
    if 'delta_group1' not in t:
        continue
    sig = (t['p_group1'] < 0.05 and t['p_group2'] < 0.05
           and t['delta_group1'] < 0 and t['delta_group2'] > 0)
    print('%-14s %+10.4f %8.4f %+10.4f %8.4f  %s' % (
        g['generator'], t['delta_group1'], t['p_group1'],
        t['delta_group2'], t['p_group2'],
        'replicates (g1 down, g2 up, both p<0.05)' if sig
        else 'DOES NOT REPLICATE'))
print()

# how often the answer text actually changes between conditions
print('=' * 100)
print('DOES THE ANSWER TEXT CHANGE AT ALL?')
print('=' * 100)
print()
for g in d['generators']:
    by_q = defaultdict(dict)
    for r in g['records']:
        by_q[r['qid']][r['condition']] = (r.get('answer') or '').strip()
    tot = len(by_q)
    identical = sum(1 for cs in by_q.values() if len(set(cs.values())) == 1)
    changed = tot - identical
    print('%-14s answers identical across all 4 conditions: %2d/%2d   '
          'changed: %2d' % (g['generator'], identical, tot, changed))

print()
print('=' * 100)
print('ATTRIBUTION (EAE-D): clean -> poisoned')
print('=' * 100)
print()
for g in d['generators']:
    a = g['summary'].get('clean', {}).get('eae_d')
    b = g['summary'].get('poisoned', {}).get('eae_d')
    if a is None or b is None:
        continue
    print('%-14s %.3f -> %.3f   (%+.3f)' % (g['generator'], a, b, b - a))
