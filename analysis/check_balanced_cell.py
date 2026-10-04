"""Is the partial label in the large balanced cells accompanied by a flat R1 statistic?

The search found 29 undefended cells where the balanced (template_plus_projection) attack
yields a graded poison_share, and one of them is large enough to work with: run `bbq`,
retriever `dense`, 720 attacked queries, 11.8% partial, six label levels. That would satisfy
both requirements the validation needs.

But drift_tv in those cells averages 0.23, which is not small, and the paper's claim is that
the R1 composition statistic is essentially unmoved. Either the attack is not balanced as
assumed, or drift_tv is being driven by something other than group composition. This measures
the clean baseline for the same run and compares, and reports the drift distribution by label
level, because a mean alone cannot distinguish "flat" from "moves only where the label is
high".
"""
import collections
import csv
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')


def load(tag):
    return list(csv.DictReader(io.open(os.path.join(RESULTS, tag, 'per_query.csv'),
                                       encoding='utf-8')))


def fnum(x):
    try:
        v = float(x)
        return v if v == v else None
    except (ValueError, TypeError):
        return None


def main():
    rows = load('bbq')
    for retriever in ('dense', 'bm25'):
        sel = [r for r in rows if r['retriever'] == retriever and r['defense'] == 'vanilla']
        clean = [r for r in sel if r['attack'] == 'clean']
        atk = [r for r in sel if r['attack'] == 'template_plus_projection']
        cd = [fnum(r['drift_tv']) for r in clean]
        cd = [x for x in cd if x is not None]
        print('=== retriever=%s defense=vanilla ===' % retriever)
        print('  clean queries      : %d' % len(clean))
        print('  attacked queries   : %d' % len(atk))
        if cd:
            print('  clean drift_tv     : mean=%.4f  max=%.4f  sd=%.4f'
                  % (sum(cd) / len(cd), max(cd),
                     (sum((x - sum(cd) / len(cd)) ** 2 for x in cd) / len(cd)) ** 0.5))

        # drift by label level
        by = collections.defaultdict(list)
        for r in atk:
            s = fnum(r['poison_share'])
            d = fnum(r['drift_tv'])
            if s is None or d is None:
                continue
            by[round(s, 1)].append(d)
        print('  attacked drift_tv by poison_share level:')
        for lev in sorted(by):
            v = by[lev]
            print('     share=%.1f  n=%-4d drift mean=%.4f  max=%.4f'
                  % (lev, len(v), sum(v) / len(v), max(v)))

        # is the label itself graded here?
        shares = [fnum(r['poison_share']) for r in atk]
        shares = [x for x in shares if x is not None]
        c = collections.Counter(round(x, 2) for x in shares)
        part = sum(n for k, n in c.items() if 0 < k < 1.0)
        print('  label distribution : %s' % dict(sorted(c.items())))
        print('  partial            : %d / %d = %.1f%%'
              % (part, len(shares), 100.0 * part / max(1, len(shares))))
        print()

    print('Reading: if drift_tv on attacked queries sits at the clean level for the levels')
    print('where the label is partial, the attack is balanced AND partially successful, which')
    print('is exactly the configuration the validation needs.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
