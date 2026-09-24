"""
Run the forced-choice probe on both corpora and every generator, and compare it with
the free-form probe on the same retrieval conditions.

The question this answers: is the BBQ null a property of the corpus or of the probe?

Free-form measurement cannot answer it, because 99.0% of BBQ answers are
non-committal (mean max-entailment 0.007 against 0.156 on the controlled corpus), so
the free-form statistic is near zero under every condition there and *no* effect
could appear in it. The forced-choice probe removes that degeneracy by requiring the
generator to pick between a favourable and an unfavourable statement about the group,
and it is scored by the same NLI model, so the two probes are on one scale.

Both corpora use the cached retrieval conditions, so all generators see identical
retrieved passages and the only difference is the probe.

Usage
-----
    export DASHSCOPE_API_KEY=...
    python -m src.run_forced_choice --corpus controlled \
        --generators qwen-plus mistral-7b --out results/fc_controlled
    python -m src.run_forced_choice --corpus bbq \
        --generators qwen-plus mistral-7b --out results/fc_bbq
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import pickle
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval.generation import LOCAL_MODELS, NliScorer, make_generator  # noqa: E402
from src.eval.forced_choice import (  # noqa: E402
    forced_choice_records,
    paired_permutation,
    per_query_margins,
    score_records,
    summarise,
)

CORPORA = {
    'controlled': {
        'config': 'configs/attribution.json',
        'contexts': 'results/generation_contexts.pkl',
    },
    'bbq': {
        'config': 'configs/generation_bbq_full.json',
        'contexts': 'results/generation_contexts.pkl',
    },
}

CONDITIONS = ('clean', 'poisoned', 'r1only', 'r2both')


def load_contexts(corpus: str, rebuild: bool):
    """Retrieval conditions, from cache when the corpus matches."""
    from src.run_generation import _restore_conditions, _slim_conditions
    from src.run_attribution import collect_contexts
    from src.run_experiment import load_config

    cfg_path = CORPORA[corpus]['config']
    cache = CORPORA[corpus]['contexts']
    cfg = load_config(cfg_path, quick=False)

    if os.path.exists(cache) and not rebuild:
        with open(cache, 'rb') as fh:
            payload = pickle.load(fh)
        meta = payload['meta']
        # The two corpora differ in query count and must never share an entry: a
        # mismatch is treated as a miss and the contexts are rebuilt.
        expected = (len(cfg['strata']) * int(cfg['n_queries_per_stratum']))
        tag_ok = meta.get('corpus_tag') == corpus
        count_ok = int(meta.get('n_queries', -1)) == expected
        if tag_ok and count_ok:
            print('[cache] contexts for %s loaded (%d queries)'
                  % (corpus, meta['n_queries']))
            return _restore_conditions(payload['conditions']), meta
        print('[cache] entry is for %r/%s queries, need %r/%d -- rebuilding'
              % (meta.get('corpus_tag'), meta.get('n_queries'), corpus, expected))

    print('[build] running retrieval for %s ...' % corpus)
    t0 = time.time()
    _b, conditions, meta = collect_contexts(cfg)
    meta['corpus_tag'] = corpus
    with open(cache, 'wb') as fh:
        pickle.dump({'conditions': _slim_conditions(conditions), 'meta': meta}, fh)
    print('[build] done in %.1fs, cached' % (time.time() - t0))
    return conditions, meta


def run_generator(name, conditions, groups, scorer, out_dir, limit):
    print()
    print('=' * 78)
    print('FORCED CHOICE - %s' % name)
    print('=' * 78)
    client = make_generator(
        name, cache_path=os.path.join(out_dir, 'fc_cache.json'))
    label = getattr(client, 'label', None) or client.provider.label
    print('  generator: %s' % label)

    t0 = time.time()
    recs = forced_choice_records(client=client, conditions=conditions,
                                 groups_of_stratum=groups, limit=limit)
    client.flush()
    t_gen = time.time() - t0

    t0 = time.time()
    score_records(recs, scorer)
    t_score = time.time() - t0

    summ = summarise(recs)

    # paired tests per group against clean
    tests: Dict[str, object] = {}
    if 'clean' in summ:
        clean_recs = [r for r in recs if r['condition'] == 'clean'
                      and r.get('margin') is not None]
        gnames = sorted({str(r['group']) for r in clean_recs})
        for cond in CONDITIONS:
            if cond == 'clean':
                continue
            crecs = [r for r in recs if r['condition'] == cond
                     and r.get('margin') is not None]
            if not crecs:
                continue
            entry: Dict[str, object] = {}
            for g in gnames:
                a = per_query_margins(clean_recs, g)
                b = per_query_margins(crecs, g)
                shared = sorted(set(a) & set(b))
                if len(shared) < 2:
                    continue
                d, p = paired_permutation([a[k] for k in shared],
                                          [b[k] for k in shared])
                entry['delta_%s' % g] = d
                entry['p_%s' % g] = p
                entry['n_%s' % g] = len(shared)
            tests[cond] = entry

    print()
    print('  %-10s %5s %10s %10s %10s %12s %9s' % (
        'condition', 'n', 'stance_g1', 'stance_g2', 'gap', 'commitment',
        'uncommitted'))
    for cond in CONDITIONS:
        s = summ.get(cond)
        if not s:
            continue
        print('  %-10s %5d %10.4f %10.4f %10.4f %12.4f %8.1f%%' % (
            cond, int(s['n']), s['stance_g1'], s['stance_g2'],
            s['stance_gap'], s['commitment'], 100 * s['uncommitted']))
    if summ:
        first = summ[list(summ)[0]]
        print()
        print('  parsed reply as A/B : %.1f%%   NLI agrees with stated choice: %.1f%%'
              % (100 * first['parsed_ok'],
                 100 * first['nli_agrees_with_stated']))
    print()
    for cond, t in tests.items():
        pieces = []
        for k in sorted(t):
            if k.startswith('delta_'):
                g = k[len('delta_'):]
                pieces.append('%s: %+.4f (p=%.4f)' % (g, t[k], t['p_' + g]))
        print('  %-10s vs clean   %s' % (cond, '   '.join(pieces)))
    print('  gen %.0fs  score %.0fs  calls=%d cache=%d errors=%d'
          % (t_gen, t_score, client.n_calls, client.n_cache_hits, client.n_errors))

    return {
        'generator': name,
        'label': label,
        'summary': summ,
        'tests_vs_clean': tests,
        'usage': client.usage,
        'timing': {'generate_s': t_gen, 'score_s': t_score},
        'records': recs,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--corpus', choices=sorted(CORPORA), required=True)
    ap.add_argument('--generators', nargs='+', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--rebuild', action='store_true')
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    print('=' * 78)
    print('FORCED-CHOICE PROBE - corpus %s' % args.corpus)
    print('=' * 78)

    conditions, meta = load_contexts(args.corpus, args.rebuild)
    groups = {k: (v[0], v[1]) for k, v in meta['groups'].items()}
    print('corpus: %d docs, %d queries' % (meta['n_docs'], meta['n_queries']))

    scorer = NliScorer()
    results = []
    for gen in args.generators:
        try:
            results.append(run_generator(gen, conditions, groups, scorer,
                                         args.out, args.limit))
        except Exception as exc:
            print('\n  !! %s failed: %s: %s'
                  % (gen, type(exc).__name__, str(exc)[:160]))

    if not results:
        print('\nno generator produced results')
        return 1

    with open(os.path.join(args.out, 'forced_choice.json'), 'w',
              encoding='utf-8') as fh:
        json.dump({'corpus': args.corpus, 'generators': results}, fh,
                  ensure_ascii=False, indent=2, default=str)

    with open(os.path.join(args.out, 'per_query.csv'), 'w', newline='',
              encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['generator', 'condition', 'qid', 'stratum', 'group',
                    'n_poison_in_context', 'p_fav', 'p_unfav', 'margin',
                    'commitment', 'choice', 'stated_fav', 'agrees', 'error'])
        for res in results:
            for r in res['records']:
                w.writerow([res['generator'], r['condition'], r['qid'],
                            r['stratum'], r['group'], r['n_poison_in_context'],
                            r.get('p_fav', ''), r.get('p_unfav', ''),
                            r.get('margin', ''), r.get('commitment', ''),
                            r.get('choice', ''), r.get('stated_fav', ''),
                            r.get('agrees', ''), r.get('error', '')])

    print()
    print('[done] -> %s' % args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
