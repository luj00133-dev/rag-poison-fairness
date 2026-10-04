"""Is there a graded, non-degenerate label for evidence relocation?

The earlier finding was that both candidate labels are unusable: `n_poison_in_context` is the
experimental condition, and `poison_in_topk` is a monotone function of the injected rate, i.e.
attack strength rather than attack effect.

But the retrieval runs also record `poison_share` -- the FRACTION of the retrieved set that is
adversarial, not merely whether one is present. If that varies per query within a fixed attack
rate, it is a genuine graded measure of how far the evidence was relocated: continuous,
observable at retrieval, and not a statistic under test.

This checks the distribution, and whether the same queries appear in the generation runs, since
the validation would need to join the two layers.
"""
import collections
import csv
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')


def main():
    for tag in ('full', 'bbq'):
        rows = list(csv.DictReader(io.open(os.path.join(RESULTS, tag, 'per_query.csv'),
                                           encoding='utf-8')))
        print('=== %s ===' % tag)
        by = collections.defaultdict(list)
        for r in rows:
            if r['retriever'] != 'bm25' or r['defense'] != 'vanilla':
                continue
            try:
                by[(r['attack'], r['poison_rate'])].append(float(r['poison_share']))
            except (ValueError, KeyError):
                pass
        for key in sorted(by, key=str):
            v = by[key]
            n = len(v)
            uniq = sorted(set(round(x, 4) for x in v))
            print('  %-42s n=%-4d mean=%.3f  distinct=%-3d  %s'
                  % (str(key), n, sum(v) / n if n else float('nan'), len(uniq),
                     uniq[:6]))
        print()

    print('=== do the generation queries overlap the retrieval runs? ===')
    gen = list(csv.DictReader(io.open(os.path.join(RESULTS, 'generation_bbq',
                                                   'per_query.csv'), encoding='utf-8')))
    ret = list(csv.DictReader(io.open(os.path.join(RESULTS, 'bbq', 'per_query.csv'),
                                      encoding='utf-8')))
    gq = {(r['qid'], r['stratum']) for r in gen}
    rq = {(r['qid'], r['stratum']) for r in ret}
    print('  generation qids : %d' % len(gq))
    print('  retrieval  qids : %d' % len(rq))
    print('  shared          : %d' % len(gq & rq))
    print('  example shared  : %s' % list(sorted(gq & rq))[:2])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
