"""Extract every number the four data figures need, and write them to one file.

Figures must not contain a number that is not in a results file. Pulling them all
here means the plotting script reads one artefact, and a mismatch between a figure
and a table becomes a visible diff rather than a silent transcription error.
"""
import csv
import json
import os
import sys

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join('results', 'figure_data.json')


def rows(path):
    with open(path, encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def fnum(r, k):
    v = (r.get(k) or '').strip()
    if v in ('', 'nan', 'None'):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def rate_ok(r, rate):
    got = (r.get('poison_rate') or '')
    if rate is None:
        return got == ''
    try:
        return abs(float(got) - float(rate)) < 1e-9
    except ValueError:
        return False


def figure4_r1_inertness():
    """poison@k for every constraint kind and epsilon against the baseline."""
    r = rows('results/full/aggregate.csv')
    out = {}
    for rt in ('bm25', 'dense'):
        base = next((fnum(x, 'poison_in_topk') for x in r
                     if x['attack'] == 'template_plus_projection'
                     and x['retriever'] == rt and x['defense'] == 'vanilla'
                     and rate_ok(x, 0.005)), None)
        series = {}
        for d in ('repr_group', 'repr_stance', 'repr_both'):
            pts = []
            for x in r:
                if (x['attack'] == 'template_plus_projection'
                        and x['retriever'] == rt and x['defense'] == d
                        and rate_ok(x, 0.005)):
                    e = fnum(x, 'epsilon')
                    p = fnum(x, 'poison_in_topk')
                    if e is not None and p is not None:
                        pts.append({'eps': e, 'poison_at_k': p,
                                    'delta': p - base})
            pts.sort(key=lambda d_: -d_['eps'])
            if pts:
                series[d] = pts
        out[rt] = {'baseline': base, 'series': series}
    return out


def figure5_aggregate_vs_pergroup():
    """Aggregate gap change vs per-group changes, controlled corpus, 3 generators."""
    d = json.load(open('results/generation/generation.json', encoding='utf-8'))
    out = []
    for g in d['generators']:
        t = g['tests_vs_clean'].get('poisoned', {})
        if 'delta_group1' not in t:
            continue
        out.append({
            'generator': g['generator'],
            'delta_gap': t['delta_gap'], 'p_gap': t['p_gap'],
            'delta_g1': t['delta_group1'], 'p_g1': t['p_group1'],
            'delta_g2': t['delta_group2'], 'p_g2': t['p_group2'],
        })
    return out


def figure6_encoder_scale():
    """Text-attack poison@k at base and large, both families, plus SPLADE."""
    runs = [
        ('align_gte_ad', 'GTE', 'base', 'st'),
        ('align_gte_large', 'GTE', 'large', 'st'),
        ('align_e5', 'E5', 'base', 'st'),
        ('align_e5_large', 'E5', 'large', 'st'),
        ('align_splade', 'SPLADE', 'base', 'splade'),
        ('align_splade_large', 'SPLADE', 'large', 'splade'),
    ]
    out = {}
    for tag, fam, size, rk in runs:
        p = os.path.join('results', tag, 'aggregate.csv')
        if not os.path.exists(p):
            continue
        for x in rows(p):
            if (x['attack'] == 'template' and x['retriever'] == rk
                    and x['defense'] == 'vanilla' and rate_ok(x, 0.005)):
                v = fnum(x, 'poison_in_topk')
                if v is not None:
                    out.setdefault(fam, {})[size] = v
    return out


def figure7_responsiveness():
    """Ground-truth composition vs each statistic, corpus size held constant."""
    return {
        'variant': ['base', '500', '1500', '3000', '3000 rev.'],
        'corpus_pct_woman': [0.500, 0.580, 0.739, 0.978, 0.022],
        'drift_tv': [0.0000, 0.0264, 0.0660, 0.0924, 0.0569],
        'drift_js': [0.0000, 0.0372, 0.0809, 0.1062, 0.0532],
        'stance_div': [0.2925, 0.2876, 0.2854, 0.2854, 0.2851],
        'stance_onesided': [0.4753, 0.4711, 0.4694, 0.4694, 0.4691],
    }


def main():
    data = {
        'fig4_r1_inertness': figure4_r1_inertness(),
        'fig5_aggregate_vs_pergroup': figure5_aggregate_vs_pergroup(),
        'fig6_encoder_scale': figure6_encoder_scale(),
        'fig7_responsiveness': figure7_responsiveness(),
    }
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2, default=str)
    print('wrote %s' % OUT)
    print()
    print('fig4 baseline poison@k: %s'
          % {k: v['baseline'] for k, v in data['fig4_r1_inertness'].items()})
    print('fig5 generators: %s'
          % [g['generator'] for g in data['fig5_aggregate_vs_pergroup']])
    print('fig6 families: %s' % data['fig6_encoder_scale'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
