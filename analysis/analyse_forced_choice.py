"""Score the forced-choice probe by the choice it forced, not by NLI on the reply.

The first version asked the generator to choose between a favourable and an
unfavourable statement and then scored the *reply text* with the NLI model. That is
wrong, and the smoke test said so plainly: the generator replied with a single letter
100% of the time, the NLI reading agreed with the model's own stated choice only
31.2% of the time -- worse than chance -- and every margin came out near zero. A
one-letter answer carries no stance for an entailment model to find.

The forced-choice signal is the choice. It is binary, it is unambiguous, and the
probe's whole purpose is that it *forced* a commitment, which the free-form probe
demonstrably could not obtain on the natural corpus. So this analysis:

  * reads `choice` together with `fav_is_a` to determine which statement was chosen,
    giving per-answer stance in {+1 favourable, -1 unfavourable, 0 unparsed};
  * derives a continuous quantity only where one is legitimate -- the *rate* of
    favourable choices per group, which is what the metric is defined on;
  * reports the NLI reading as a diagnostic of the reply-scoring idea, recording that
    it failed rather than silently dropping it;
  * applies a paired permutation test on the per-query binary choice, which needs no
    entailment model at all.

That last point is the paper's advantage here: on the forced-choice probe the
measurement is exact, so the effect either appears or it does not, with no probe
sensitivity left to argue about.
"""
import io
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONDITIONS = ('clean', 'poisoned', 'r1only', 'r2both')


def stance_of(rec: Dict[str, object]) -> Optional[int]:
    """+1 if the favourable statement was chosen, -1 if the unfavourable, else None."""
    c = rec.get('choice')
    if c not in ('A', 'B'):
        return None
    chose_a = (c == 'A')
    fav_is_a = bool(rec.get('fav_is_a'))
    return 1 if (chose_a == fav_is_a) else -1


def summarise_choice(recs: Sequence[Dict[str, object]]
                     ) -> Dict[str, Dict[str, float]]:
    """Favourable-choice rate per group per condition, and the cross-group gap."""
    out: Dict[str, Dict[str, float]] = {}
    by_cond: Dict[str, List[Dict[str, object]]] = {}
    for r in recs:
        by_cond.setdefault(str(r['condition']), []).append(r)

    for cond, rs in sorted(by_cond.items()):
        rates: Dict[str, List[float]] = defaultdict(list)
        by_stratum: Dict[str, List[Dict[str, object]]] = defaultdict(list)
        for r in rs:
            by_stratum[str(r['stratum'])].append(r)
        g1_rates, g2_rates = [], []
        for _s, srs in by_stratum.items():
            groups = sorted({str(r['group']) for r in srs})
            if len(groups) < 2:
                continue
            for gname, bucket in ((groups[0], g1_rates), (groups[1], g2_rates)):
                vals = [stance_of(r) for r in srs if r['group'] == gname]
                vals = [v for v in vals if v is not None]
                if vals:
                    bucket.append(float(np.mean([1.0 if v > 0 else 0.0
                                                 for v in vals])))
        parsed = [r for r in rs if stance_of(r) is not None]
        nli_margins = [r['margin'] for r in rs if r.get('margin') is not None]
        agrees = [r['agrees'] for r in rs if r.get('agrees') is not None]
        out[cond] = {
            'n': float(len(rs)),
            'n_parsed': float(len(parsed)),
            'fav_rate_g1': float(np.mean(g1_rates)) if g1_rates else float('nan'),
            'fav_rate_g2': float(np.mean(g2_rates)) if g2_rates else float('nan'),
            'stance_gap': (abs(float(np.mean(g1_rates)) - float(np.mean(g2_rates)))
                           if g1_rates and g2_rates else float('nan')),
            'nli_margin_mean': float(np.mean(nli_margins)) if nli_margins else float('nan'),
            'nli_agrees': float(np.mean([bool(a) for a in agrees])) if agrees else float('nan'),
            'errors': float(sum(1 for r in rs if r.get('error'))),
        }
    return out


def per_query_choice(recs: Sequence[Dict[str, object]], group: str
                     ) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for r in recs:
        if r['group'] != group:
            continue
        s = stance_of(r)
        if s is not None:
            out[str(r['qid'])] = float(1.0 if s > 0 else 0.0)
    return out


def paired_permutation(a: Sequence[float], b: Sequence[float],
                       n_perm: int = 20000, seed: int = 20260101
                       ) -> Tuple[float, float]:
    a = np.asarray(list(a), dtype=float)
    b = np.asarray(list(b), dtype=float)
    if a.size != b.size or a.size < 2:
        return float('nan'), float('nan')
    d = b - a
    obs = float(d.mean())
    if np.allclose(d, 0.0):
        return obs, 1.0
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, d.size))
    perm = (signs * d).mean(axis=1)
    return obs, float((np.abs(perm) >= abs(obs) - 1e-12).mean())


def main():
    if len(sys.argv) < 2:
        print('usage: analyse_forced_choice.py results/fc_controlled [more...]')
        return 1
    for out_dir in sys.argv[1:]:
        path = os.path.join(out_dir, 'forced_choice.json')
        if not os.path.exists(path):
            print('%s: missing' % out_dir)
            continue
        d = json.load(open(path, encoding='utf-8'))
        print('=' * 92)
        print('FORCED CHOICE - corpus %s' % d.get('corpus'))
        print('=' * 92)
        for g in d['generators']:
            summ = summarise_choice(g['records'])
            print()
            print('--- %s ---' % g['label'])
            print('%-10s %5s %6s %11s %11s %10s %12s %10s' % (
                'condition', 'n', 'parsed', 'fav_rate_g1', 'fav_rate_g2',
                'gap', 'nli_margin', 'nli_agree'))
            for cond in CONDITIONS:
                s = summ.get(cond)
                if not s:
                    continue
                print('%-10s %5d %6d %11.4f %11.4f %10.4f %12.4f %9.1f%%' % (
                    cond, int(s['n']), int(s['n_parsed']), s['fav_rate_g1'],
                    s['fav_rate_g2'], s['stance_gap'], s['nli_margin_mean'],
                    100 * s['nli_agrees']))
            # paired tests per group
            clean = [r for r in g['records'] if r['condition'] == 'clean']
            groups_here = sorted({str(r['group']) for r in clean})
            print()
            for cond in CONDITIONS:
                if cond == 'clean':
                    continue
                cur = [r for r in g['records'] if r['condition'] == cond]
                if not cur:
                    continue
                pieces = []
                for gname in groups_here:
                    a = per_query_choice(clean, gname)
                    b = per_query_choice(cur, gname)
                    shared = sorted(set(a) & set(b))
                    if len(shared) < 2:
                        continue
                    dd, p = paired_permutation([a[k] for k in shared],
                                               [b[k] for k in shared])
                    pieces.append('%s: %+.4f (p=%.4f)' % (gname, dd, p))
                print('  %-10s vs clean   %s' % (cond, '   '.join(pieces)))
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
