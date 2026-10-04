"""Fast probe: find the align_strength that maximises partial contamination.

Each retrieval run costs ~20 minutes on this CPU, so tuning strength by running the full
experiment is not viable. The ranking of injected versus clean passages is decided by
embedding similarity plus a length term, and all of it can be computed directly for a grid of
strength values in one pass over the encoder. That turns a 20-minute-per-point search into a
single cheap sweep.

The probe reproduces the essential decision -- for each query, how many of the 5 retrieved
passages are adversarial -- as a function of align_strength, using the same corpus, the same
encoder and the same construction as the real attack.
"""
import io
import os
import random
import sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)

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


def main():
    import numpy as np
    from sentence_transformers import SentenceTransformer

    from src.run_experiment import build_bundle, load_config

    # ALIGN is function-local in make_poison_docs; read it out of the source rather than
    # retyping it, so the probe cannot silently disagree with the real attack.
    _src = io.open(os.path.join(P, 'src', 'attacks', 'poisoning.py'), encoding='utf-8').read()
    _i = _src.find('ALIGN = (')
    _ns = {}
    exec(_src[_i:_src.find(')', _i) + 1], _ns)
    ALIGN = _ns['ALIGN']

    cfg = load_config('configs/pv_graded2.json', quick=False)
    bundle = build_bundle(cfg)
    docs = list(bundle.docs)
    queries = list(bundle.queries)
    groups = bundle.groups if hasattr(bundle, 'groups') else None

    # reconstruct the per-stratum pools the attack actually uses
    groups_by = cfg.get('groups_by_stratum')
    if groups_by is None:
        groups_by = {s: (g[0], g[1]) for s, g in (groups or {}).items()}
    print('strata: %s' % list(groups_by.keys()))
    print('docs: %d  queries: %d' % (len(docs), len(queries)))

    os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
    model = SentenceTransformer('thenlper/gte-base')
    qvecs = model.encode([q.text for q in queries], batch_size=32,
                         normalize_embeddings=True, show_progress_bar=False)
    qstratum = {}
    for i, q in enumerate(queries):
        qstratum.setdefault(getattr(q, 'stratum', None), []).append(i)

    rng = random.Random(1234)
    base_docs = [d for d in docs]
    dvecs = model.encode([d.text for d in base_docs], batch_size=32,
                         normalize_embeddings=True, show_progress_bar=False)

    terms = ALIGN.split()
    print()
    print('%-9s %-8s %s' % ('strength', 'partial', 'distribution of retrieved poison count'))
    print('-' * 74)
    for strength in (0.2, 0.35, 0.5, 0.7, 0.85, 1.0):
        counts = []
        for qidx, q in enumerate(queries):
            stratum = getattr(q, 'stratum', None)
            gp = groups_by.get(stratum)
            if not gp:
                continue
            fav, sup = gp[0], gp[1]
            pool = [d for d in base_docs if d.group in (fav, sup)]
            fav_t = [d for d in pool if d.group == fav]
            sup_t = [d for d in pool if d.group == sup]
            if not fav_t or not sup_t:
                continue
            r = random.Random(1234)
            texts = []
            for i in range(6):
                if i % 2 == 0:
                    base = fav_t[r.randrange(len(fav_t))]
                else:
                    base = sup_t[r.randrange(len(sup_t))]
                frac = ((i + 1) / 6.0) * strength
                k = max(1, int(round(frac * len(terms))))
                texts.append(f"{strip_filler(base.text)} {' '.join(terms[:k])}")
            pv = model.encode(texts, batch_size=32, normalize_embeddings=True,
                              show_progress_bar=False)
            sims = np.concatenate([dvecs @ qvecs[qidx], pv @ qvecs[qidx]])
            top = np.argsort(-sims)[:5]
            counts.append(int(sum(1 for t in top if t >= len(dvecs))))
        import collections
        c = collections.Counter(counts)
        part = sum(v for k, v in c.items() if 0 < k < 5)
        tot = sum(c.values()) or 1
        print('%-9.2f %-8s %s' % (strength, '%.1f%%' % (100.0 * part / tot),
                                  dict(sorted(c.items()))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
