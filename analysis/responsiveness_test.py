"""Positive control: does drift_tv track a known, directional composition change?

Third attempt, and the first two were wrong in ways their own output revealed:

  v1  applied the R1 constraint under natural skew expecting drift_tv to fall. It
      rose (0.0000 -> 0.10-0.12): the constraint changes *which* group-relevant
      passages are selected rather than moving the corpus toward its reference.
      Not a responsiveness test at all.

  v2  duplicated one group's passages and compared drift before and after.
      Duplication grew the corpus (17,792 -> 18,419), which moves the retrieval pool
      and the score threshold, and both directions raised drift by a similar amount,
      so the direction of the composition change could not be read off the result.

  v3  swapped passages to hold the size fixed, but ran it on the race stratum, whose
      minority group has only 88 passages, so a 2000-passage swap was impossible and
      only one variant ran.

This version holds the corpus size fixed *and* works on a stratum that can support
large swaps: the gender stratum is perfectly balanced (3136 passages per group), so
replacements up to 2000 are available. Only composition changes, in a known
direction and by a known number of passages.

If drift_tv grows with the swap size and returns to zero when the swap is reversed,
the statistic is responsive to real composition change. That is what makes the
paper's claim specific -- these statistics are not broken, they are immune to an
adversary who balances what they count -- rather than a general complaint that the
instrument is unreliable.
"""
import os
import sys
from collections import Counter

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from src.retrieval.base import Document  # noqa: E402

STRATUM = 'bbq-gender'          # balanced: 3136 passages per group
G_A, G_B = 'man', 'woman'


def swap(docs, g_from, g_to, n, tag):
    """Replace n passages of g_from with n new passages of g_to. Size preserved."""
    src = [d for d in docs if d.group == g_from]
    dst = [d for d in docs if d.group == g_to]
    if len(src) < n or not dst:
        return None
    drop = set(id(d) for d in src[:n])
    out = [d for d in docs if id(d) not in drop]
    for i in range(n):
        t = dst[i % len(dst)]
        out.append(Document(doc_id='%s-%d' % (tag, i), text=t.text,
                            group=g_to, stance=t.stance, is_poison=False))
    return out


def main():
    from src.eval.metrics import corpus_favourable_rate, evaluate_query
    from src.run_experiment import build_bundle, build_retriever, load_config

    cfg = load_config('configs/bbq.json', quick=False)
    bundle = build_bundle(cfg)
    k = int(cfg['top_k'])
    gs = bundle.groups[STRATUM]

    base_counts = Counter(d.group for d in bundle.docs if d.group in gs)
    print('stratum %s composition: %s' % (STRATUM, dict(base_counts)))
    print('swapping between %s and %s, corpus size held at %d'
          % (G_A, G_B, len(bundle.docs)))
    print()

    base = build_retriever('dense', bundle.docs, cfg)
    clean = {q.qid: base.search(q.text, k) for q in bundle.queries}

    plan = [
        ('baseline', None),
        ('swap 500  %s->%s' % (G_A, G_B), (G_A, G_B, 500)),
        ('swap 1500 %s->%s' % (G_A, G_B), (G_A, G_B, 1500)),
        ('swap 3000 %s->%s' % (G_A, G_B), (G_A, G_B, 3000)),
        ('swap 3000 %s->%s' % (G_B, G_A), (G_B, G_A, 3000)),
    ]

    print('%-26s %8s %9s %9s %9s %10s %9s' % (
        'variant', 'docs', 'drift_tv', 'drift_js', 'stance_div', 'onesided',
        'corpus%'+G_B))
    for name, spec in plan:
        docs = bundle.docs if spec is None else swap(bundle.docs, *spec, 'sw')
        if docs is None:
            print('%-26s (unavailable)' % name)
            continue
        own = Counter(d.group for d in docs if d.group in gs)
        own_share = own[G_B] / max(1, sum(own.values()))

        r = build_retriever('dense', docs, cfg)
        ref = {s: corpus_favourable_rate([d for d in docs if d.group in g], g)
               for s, g in bundle.groups.items()}
        rows, seen = [], []
        for q in bundle.queries:
            res = r.search(q.text, k)
            rows.append(evaluate_query(
                res, clean_docs=clean[q.qid].docs,
                groups=bundle.groups[q.stratum],
                pool_ids=bundle.candidate_pool[q.qid],
                topk_poison_ids=set(), corpus_fav_ref=ref[q.stratum]))
            if q.stratum == STRATUM:
                got = Counter(d.group for d in res.docs if d.group in gs)
                t = sum(got.values())
                if t:
                    seen.append(got[G_B] / t)
        print('%-26s %8d %9.4f %9.4f %9.4f %10.4f %8.3f' % (
            name, len(docs),
            float(np.nanmean([m.drift_tv for m in rows])),
            float(np.nanmean([m.drift_js for m in rows])),
            float(np.nanmean([m.stance_div for m in rows])),
            float(np.nanmean([m.stance_onesided for m in rows])),
            own_share))

    print()
    print('=' * 88)
    print('READING')
    print('=' * 88)
    print()
    print('Corpus size is constant, so pool and threshold do not move; only the')
    print('composition changes, by a known number of passages, in a known')
    print('direction, and reversed in the last row. drift_tv should grow with the')
    print('swap size and come back down when the direction flips. A statistic that')
    print('did not do that would be unresponsive, and the paper would have to say')
    print('so instead of attributing the failure to the adversary.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
