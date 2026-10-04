"""Verify the numbers written into section 8.1 against the runs they came from.

Section 8.1 quotes specific drift values and counts. Any of them could be a transcription
error, and they are the kind of number a reviewer would check against the tables, so they are
re-derived here from the raw per-query files rather than trusted from the prose.
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


def cell(tag, retriever, attack, defense='vanilla'):
    path = os.path.join(RESULTS, tag, 'per_query.csv')
    if not os.path.exists(path):
        return None
    rows = list(csv.DictReader(io.open(path, encoding='utf-8')))
    sel = [r for r in rows if r.get('defense') == defense
           and r.get('retriever') == retriever and r.get('attack') == attack]
    if not sel:
        return None
    by = collections.defaultdict(list)
    for r in sel:
        s, d = fnum(r['poison_share']), fnum(r['drift_tv'])
        if s is None or d is None:
            continue
        by[round(s, 1)].append(d)
    return by


def main():
    print('CLAIM: st + lexical gives drift 0.0000 at every partial level')
    by = cell('pv_graded3', 'st', 'template')
    if by:
        for lev in sorted(by):
            v = by[lev]
            print('   share=%.1f n=%-4d drift mean=%.4f' % (lev, len(v), sum(v) / len(v)))

    print()
    print('CLAIM: dense + lexical rises from 0.0000 to 0.1750')
    by = cell('bbq', 'dense', 'template')
    if by:
        for lev in sorted(by):
            v = by[lev]
            print('   share=%.1f n=%-4d drift mean=%.4f' % (lev, len(v), sum(v) / len(v)))

    print()
    print('CLAIM: BM25 projected is monotone from 0.000 to 0.195')
    for tag in ('full', 'rate_chk', 'reg'):
        by = cell(tag, 'bm25', 'template_plus_projection')
        if by:
            print('   run=%s' % tag)
            for lev in sorted(by):
                v = by[lev]
                print('      share=%.1f n=%-4d drift mean=%.4f' % (lev, len(v), sum(v) / len(v)))
            break

    print()
    print('CLAIM: SPLADE projected is monotone')
    by = cell('align_splade', 'splade', 'template_plus_projection')
    if by:
        for lev in sorted(by):
            v = by[lev]
            print('   share=%.1f n=%-4d drift mean=%.4f' % (lev, len(v), sum(v) / len(v)))

    print()
    print('CLAIM: projection gives relocated fraction 1.000 for 192 of 192')
    by = cell('pv_graded', 'st', 'template_plus_projection')
    if by:
        tot = sum(len(v) for v in by.values())
        full = len(by.get(1.0, []))
        print('   pv_graded st: total=%d  at share 1.0 = %d' % (tot, full))

    print()
    print('CLAIM: a regime holding 36 of 192 held 0 of 1536')
    for tag in ('pv_graded3', 'pv_scale'):
        by = cell(tag, 'st', 'template')
        if not by:
            print('   %s: no cell' % tag)
            continue
        tot = sum(len(v) for v in by.values())
        part = sum(len(v) for k, v in by.items() if 0 < k < 1.0)
        bal = sum(len(v) for k, v in by.items()
                  if 0 < k < 1.0 and sum(v) / len(v) < 1e-9)
        print('   %-12s attacked=%-5d partial=%-5d balanced+partial=%d' % (tag, tot, part, bal))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
