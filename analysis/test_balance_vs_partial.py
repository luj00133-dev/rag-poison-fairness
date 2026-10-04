"""Test whether ANY balanced attack in this repository is blind AND partially successful.

The design question was whether an attack can be balanced across groups while only partially
succeeding per query. Rather than reason about the construction, this measures the relation
between the two quantities directly wherever both are recorded: the R1 composition statistic
(drift_tv) and the retrieved adversarial fraction (poison_share).

The finding to check, from run `bbq` dense/vanilla: drift_tv is monotone in poison_share --
0.0000 at share 0.0, 0.0900 at 0.2, 0.1750 at 0.4, 0.2435 at 0.6, 0.2438 at 0.8, 0.2476 at
1.0 -- against a clean baseline of exactly 0.0000. If that pattern holds generally, then the
R1 statistic is flat only at FULL saturation, and partial success necessarily moves it. That
would mean the two requirements are in tension by construction, not by tuning.

The paper's own blindness result lives in runs where the attack saturates, so this also reports
drift in those runs to confirm the claim holds exactly where the paper says it does.
"""
import collections
import csv
import glob
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')


def fnum(x):
    try:
        v = float(x)
        return v if v == v else None
    except (ValueError, TypeError):
        return None


def main():
    print('Relation between the R1 statistic and the retrieved adversarial fraction,')
    print('undefended (vanilla) cells only, per retriever.')
    print()
    print('%-16s %-9s %-26s %6s %9s %9s  %s'
          % ('run', 'retriever', 'attack', 'n', 'clean', 'atk drift', 'drift by share level'))
    print('-' * 122)
    flat_at_partial = []
    for path in sorted(glob.glob(os.path.join(RESULTS, '*', 'per_query.csv'))):
        tag = os.path.basename(os.path.dirname(path))
        try:
            rows = list(csv.DictReader(io.open(path, encoding='utf-8')))
        except Exception:
            continue
        if not rows or 'poison_share' not in rows[0]:
            continue
        for retriever in sorted({r['retriever'] for r in rows}):
            for attack in ('template', 'template_plus_projection'):
                sel = [r for r in rows if r['retriever'] == retriever
                       and r['defense'] == 'vanilla' and r['attack'] in ('clean', attack)]
                clean = [fnum(r['drift_tv']) for r in sel if r['attack'] == 'clean']
                atk = [(fnum(r['poison_share']), fnum(r['drift_tv']))
                       for r in sel if r['attack'] == attack]
                atk = [(s, d) for s, d in atk if s is not None and d is not None]
                if len(atk) < 32 or not clean:
                    continue
                cl = [x for x in clean if x is not None]
                if not cl:
                    continue
                by = collections.defaultdict(list)
                for s, d in atk:
                    by[round(s, 1)].append(d)
                # partial levels only: is drift at those levels flat?
                part_drift = [d for lev, ds in by.items() if 0 < lev < 1.0 for d in ds]
                if not part_drift:
                    continue
                mean_part = sum(part_drift) / len(part_drift)
                clean_mean = sum(cl) / len(cl)
                if mean_part <= clean_mean + 1e-9:
                    flat_at_partial.append((tag, retriever, attack))
                summary = ' '.join('%s:%.3f' % (lev, sum(ds) / len(ds))
                                   for lev, ds in sorted(by.items()))
                print('%-16s %-9s %-26s %6d %9.4f %9.4f  %s'
                      % (tag, retriever, attack[:26], len(atk), clean_mean,
                         sum(d for _, d in atk) / len(atk), summary[:46]))

    print()
    print('cells where drift at PARTIAL levels is no higher than clean: %d'
          % len(flat_at_partial))
    if flat_at_partial:
        for t in flat_at_partial:
            print('   %s' % (t,))
    else:
        print('   none -- every partial level carries more composition drift than clean,')
        print('   so balance and partial success do not co-occur in this repository.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
