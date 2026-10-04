"""Where did evidence relocation take a PARTIAL value, and under what configuration?

The graded label has to come from somewhere, so this finds every (attack, retriever, defense,
rate) cell in the committed runs whose poison_share takes an intermediate value, and reports
what distinguishes the partial cells. If no cell is partial anywhere, the label cannot be
built by any reanalysis and the conclusion is a design one.
"""
import collections
import csv
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')


def main():
    tags = ['full', 'bbq', 'pv_gradient', 'pv_smoke', 'reg', 'reg2', 'reg3', 'verify',
            'chk', 'chk2']
    found = collections.Counter()
    examples = {}
    for tag in tags:
        p = os.path.join(RESULTS, tag, 'per_query.csv')
        if not os.path.exists(p):
            continue
        rows = list(csv.DictReader(io.open(p, encoding='utf-8')))
        by = collections.defaultdict(list)
        for r in rows:
            if 'poison_share' not in r:
                continue
            try:
                v = float(r['poison_share'])
            except (ValueError, TypeError):
                continue
            by[(r['attack'], r['retriever'], r['defense'], r.get('epsilon', ''),
                r.get('poison_rate', ''))].append(v)
        for key, vals in by.items():
            uniq = sorted(set(round(x, 4) for x in vals))
            if len(uniq) > 1:
                found[(tag, key[0], key[1])] += 1
                examples.setdefault((tag, key[0], key[1]),
                                    (key, len(vals), uniq[:8]))
    print('cells whose poison_share takes more than one value: %d' % len(examples))
    for k in sorted(examples, key=str):
        key, n, uniq = examples[k]
        print('  %-14s attack=%-26s retriever=%-8s n=%-4d values=%s'
              % (k[0], k[1], k[2], n, uniq))

    print()
    print('--- all distinct poison_share values seen, across every run ---')
    allv = set()
    for tag in tags:
        p = os.path.join(RESULTS, tag, 'per_query.csv')
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(io.open(p, encoding='utf-8')):
            try:
                allv.add(round(float(r['poison_share']), 4))
            except (ValueError, TypeError, KeyError):
                pass
    print('  %s' % sorted(allv))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
