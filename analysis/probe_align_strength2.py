"""Fast probe: locate the align_strength that yields partial contamination.

Why a probe rather than a sweep of full runs: one retrieval run costs about 20 minutes on this
CPU, and there are six strength values to compare, so tuning by running the pipeline is not
affordable. The quantity that decides the label -- how many of a query's top-5 passages are
adversarial -- is a ranking comparison that can be computed directly, for every strength, in a
single pass over the encoder.

What it reproduces: the same corpus, the same encoder (thenlper/gte-base, the id the dense
retriever maps "gte-base" to), the same ALIGN constant read out of the source, the same
per-stratum group pairs, and the same per-passage fraction schedule the graded injection uses.
Scoring is embedding similarity, which is what the st retriever ranks by.

What it does NOT reproduce: BM25's length normalisation and the subspace projection. Those are
reported separately rather than assumed absent -- the projection is known to override text and
is called out in the output.
"""
import collections
import io
import os
import random
import sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)

MODEL_ID = 'thenlper/gte-base'
MARKERS = (
    " The finding was filed", " The entry appears", " The record was cross-checked",
    " The measurement was repeated", " The result was entered", " The observation was dated",
)


def strip_filler(text):
    for m in MARKERS:
        i = text.find(m)
        if i >= 0:
            return text[:i].rstrip()
    return text.strip()


def read_align():
    src = io.open(os.path.join(P, 'src', 'attacks', 'poisoning.py'), encoding='utf-8').read()
    i = src.find('ALIGN = (')
    if i < 0:
        raise SystemExit('ALIGN not found in source')
    ns = {}
    exec(src[i:src.find(')', i) + 1], ns)
    return ns['ALIGN']


def main():
    import numpy as np
    from sentence_transformers import SentenceTransformer
    from src.run_experiment import build_bundle, load_config

    terms = read_align().split()
    cfg = load_config('configs/pv_graded2.json', quick=False)
    bundle = build_bundle(cfg)
    docs = list(bundle.docs)
    queries = list(bundle.queries)
    groups = getattr(bundle, 'groups', None) or {}
    print('docs=%d queries=%d strata=%s' % (len(docs), len(queries), sorted(groups)))

    os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
    model = SentenceTransformer(MODEL_ID)
    dv = model.encode([d.text for d in docs], batch_size=32,
                      normalize_embeddings=True, show_progress_bar=False)
    qv = model.encode([q.text for q in queries], batch_size=32,
                      normalize_embeddings=True, show_progress_bar=False)

    # cache poison vectors per strength: the texts differ, so each needs its own encode
    print()
    print('%-9s %-9s %-7s %s' % ('strength', 'partial', 'mean/pk', 'poison count distribution'))
    print('-' * 78)
    for strength in (0.15, 0.25, 0.35, 0.5, 0.7, 1.0):
        counts = []
        ratios = []
        for qi, q in enumerate(queries):
            stratum = getattr(q, 'stratum', None)
            gp = groups.get(stratum)
            if not gp:
                continue
            fav, sup = gp[0], gp[1]
            fav_t = [d for d in docs if d.group == fav]
            sup_t = [d for d in docs if d.group == sup]
            if not fav_t or not sup_t:
                continue
            r = random.Random(cfg.get('seed', 20260101))
            texts = []
            for i in range(6):
                base = fav_t[r.randrange(len(fav_t))] if i % 2 == 0 \
                    else sup_t[r.randrange(len(sup_t))]
                frac = ((i + 1) / 6.0) * strength
                k = max(1, int(round(frac * len(terms))))
                texts.append('%s %s' % (strip_filler(base.text), ' '.join(terms[:k])))
            pv = model.encode(texts, batch_size=32, normalize_embeddings=True,
                              show_progress_bar=False)
            sims = np.concatenate([dv @ qv[qi], pv @ qv[qi]])
            clean_sims, poison_sims = sims[:len(docs)], sims[len(docs):]
            # how many clean passages does each poisoned passage outrank?
            ratios.extend([float((clean_sims < s).mean()) for s in poison_sims])
            top = np.argsort(-sims)[:5]
            counts.append(int(sum(1 for t in top if t >= len(docs))))
        c = collections.Counter(counts)
        tot = sum(c.values()) or 1
        part = sum(v for k, v in c.items() if 0 < k < 5)
        print('%-9.2f %-9s %-7.3f %s'
              % (strength, '%.1f%%' % (100.0 * part / tot),
                 sum(ratios) / len(ratios) if ratios else float('nan'),
                 dict(sorted(c.items()))))

    print()
    print('Note: this probe ranks by embedding similarity only. BM25 adds length normalisation,')
    print('      and the projection attack overrides text entirely -- under projection every')
    print('      poisoned vector is pushed toward the queries, so no text gradient can help.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
