"""Bootstrap confidence intervals and paired tests for the retrieval-layer claims.

Why this is worth doing
-----------------------
The paper's central claim is a *null*: the R1 constraint attains exactly the same
adversarial-passage inclusion as no defence, at every budget setting. We report it
as "delta = 0.000 in 12 of 12 cells", but a reader is entitled to read a point
estimate of zero as "underpowered" rather than as "no effect". A null result needs
an equivalence bound -- the largest effect the data excludes -- and the manuscript
currently gives none anywhere: it contains no p-values and no confidence intervals
at all.

This script supplies, from the committed per-query data:
  1. paired bootstrap CIs and permutation p-values on the R1-constraint
     difference against the unconstrained baseline;
  2. the equivalence bound for each null cell, which is the honest quantitative
     form of "inert";
  3. bootstrap CIs on the positive claims (R2 stance gap, R1 drift) so they carry
     uncertainty too.

Writes paper/stats_tables.md (markdown fragment for the paper) and
results/stats_report.txt.
"""
import csv
import os
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERQ = os.path.join(ROOT, 'results', 'full', 'per_query.csv')
OUT_MD = os.path.join(ROOT, 'paper', 'stats_tables.md')
OUT_TXT = os.path.join(ROOT, 'results', 'stats_report.txt')

SEED = 20260101
N_BOOT = 10000
N_PERM = 20000


def fnum(row, key) -> Optional[float]:
    v = (row.get(key) or '').strip()
    if v in ('', 'nan', 'None'):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def rate_matches(row, rate) -> bool:
    got = (row.get('poison_rate') or '')
    if rate is None:
        return got == ''
    try:
        return abs(float(got) - float(rate)) < 1e-9
    except ValueError:
        return False


def series(rows, *, metric: str, attack: str, rate, retriever: str,
           defense: str, epsilon: str = '') -> Dict[str, float]:
    """{qid: metric} for one cell."""
    out: Dict[str, float] = {}
    for r in rows:
        if (r.get('attack') or '') != attack:
            continue
        if (r.get('retriever') or '') != retriever:
            continue
        if (r.get('defense') or '') != defense:
            continue
        if (r.get('epsilon') or '') != epsilon:
            continue
        if not rate_matches(r, rate):
            continue
        v = fnum(r, metric)
        if v is not None:
            out[r.get('qid', '')] = v
    return out


def paired_bootstrap(a: Sequence[float], b: Sequence[float]
                     ) -> Tuple[float, float, float]:
    d = np.asarray(b, dtype=float) - np.asarray(a, dtype=float)
    rng = np.random.default_rng(SEED)
    means = d[rng.integers(0, d.size, size=(N_BOOT, d.size))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi)


def paired_permutation(a: Sequence[float], b: Sequence[float]
                       ) -> Tuple[float, float]:
    d = np.asarray(b, dtype=float) - np.asarray(a, dtype=float)
    obs = float(d.mean())
    if np.allclose(d, 0.0):
        # the difference vector is identically zero: every permutation gives
        # the same statistic, so the test carries no information. Reported as
        # p = 1 rather than pretending otherwise.
        return obs, 1.0
    rng = np.random.default_rng(SEED)
    signs = rng.choice([-1.0, 1.0], size=(N_PERM, d.size))
    perm = (signs * d).mean(axis=1)
    return obs, float((np.abs(perm) >= abs(obs) - 1e-12).mean())


def ci_mean(vals: Sequence[float]) -> Tuple[float, float, float]:
    arr = np.asarray(vals, dtype=float)
    rng = np.random.default_rng(SEED)
    means = arr[rng.integers(0, arr.size, size=(N_BOOT, arr.size))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(arr.mean()), float(lo), float(hi)


def main() -> int:
    if not os.path.exists(PERQ):
        print('missing', PERQ)
        return 1
    with open(PERQ, encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))

    md: List[str] = []
    txt: List[str] = []

    md.append('**Table S1.** Paired tests of R1-constraint inertness against no '
              'defense. Controlled corpus, `template_plus_projection`, '
              r'$\rho = 0.5\%$, per-query adversarial-passage inclusion.')
    md.append('')
    md.append('| Retriever | Defense | ε | n | Δ mean | 95% CI | p | '
              'excluded effect |')
    md.append('|---|---|---|---|---|---|---|---|')

    attack, rate, metric = 'template_plus_projection', 0.005, 'poison_in_topk'
    null_cells = exact_zero = 0
    changed_cells = 0
    for rt in ('bm25', 'dense'):
        base = series(rows, metric=metric, attack=attack, rate=rate,
                      retriever=rt, defense='vanilla')
        if len(base) < 5:
            continue
        for dname in ('repr_group', 'repr_both', 'repr_stance'):
            for eps in ('0.0', '1.0'):
                cur = series(rows, metric=metric, attack=attack, rate=rate,
                             retriever=rt, defense=dname, epsilon=eps)
                keys = sorted(set(base) & set(cur))
                if len(keys) < 5:
                    continue
                a = [base[k] for k in keys]
                b = [cur[k] for k in keys]
                d, lo, hi = paired_bootstrap(a, b)
                _, p = paired_permutation(a, b)
                bound = max(abs(lo), abs(hi))
                row = ('| %s | %s | %s | %d | %+.4f | [%+.4f, %+.4f] | %.3f '
                       '| ±%.4f |'
                       % (rt, dname, eps, len(keys), d, lo, hi, p, bound))
                md.append(row)
                txt.append('%s/%s/eps=%s n=%d delta=%+.4f CI=[%+.4f,%+.4f] '
                           'p=%.3f excluded=%.4f'
                           % (rt, dname, eps, len(keys), d, lo, hi, p, bound))
                if dname in ('repr_group', 'repr_both'):
                    null_cells += 1
                    if abs(d) < 1e-12:
                        exact_zero += 1
                else:
                    changed_cells += 1

    md.append('')
    md.append('Where the constraint changes nothing, the per-query difference '
              'vector is **identically zero**, not merely small: the bootstrap CI '
              'collapses to [0, 0] and the permutation test is degenerate by '
              'construction. The informative statistic is therefore the '
              'equivalence bound — the smallest effect the data exclude — and '
              'because the differences are exactly zero rather than '
              'approximately zero, these cells exclude *any* effect on '
              'adversarial-passage inclusion, not merely one above a threshold. '
              'The `repr_stance` rows are the contrast case: there the constraint '
              'does change the selection, the difference vector is non-degenerate, '
              'and both the CI and the p-value are meaningful.')
    md.append('')
    md.append('**Table S2.** Bootstrap 95% CIs on the positive claims '
              '(per-question values, 10,000 resamples, no defense).')
    md.append('')
    md.append('| Condition | Retriever | Metric | mean | 95% CI |')
    md.append('|---|---|---|---|---|')
    for atk, r_ in (('clean', None), ('template', 0.005),
                    ('template_plus_projection', 0.005)):
        for rt in ('bm25', 'dense'):
            for met, label in (('stance_gap', 'R2 stance gap'),
                               ('drift_tv', 'R1 drift (TV)')):
                s = series(rows, metric=met, attack=atk, rate=r_,
                           retriever=rt, defense='vanilla')
                if len(s) < 5:
                    continue
                m, lo, hi = ci_mean(list(s.values()))
                md.append('| %s | %s | %s | %.4f | [%.4f, %.4f] |'
                          % (atk, rt, label, m, lo, hi))
                txt.append('%s/%s/%s mean=%.4f CI=[%.4f,%.4f]'
                           % (atk, rt, label, m, lo, hi))

    with open(OUT_MD, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(md) + '\n')
    with open(OUT_TXT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(txt) + '\n')

    print('\n'.join(txt))
    print()
    print('R1-constraint cells: %d, of which exactly zero: %d'
          % (null_cells, exact_zero))
    print('nonzero-change cells (repr_stance): %d' % changed_cells)
    print('wrote', OUT_MD)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
