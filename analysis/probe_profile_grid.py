"""Locate the (align_min_frac, align_strength) pair that spans the full 0..5 label range.

The previous probe showed the gradient works but the count topped out at 2 of 5, because the
weakest passage still used 1/n of the alignment vocabulary. align_min_frac now lets the
profile start below that, so a run can contain passages that clearly lose, passages on the
boundary, and passages that clearly win -- which is what makes different queries land on
different counts.

Ranking is by embedding similarity, the same quantity the st retriever uses, with BM25's
length term absent; that caveat is stated in the output rather than left implicit.
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

    os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
    model = SentenceTransformer(MODEL_ID)
    dv = model.encode([d.text for d in docs], batch_size=32,
                      normalize_embeddings=True, show_progress_bar=False)
    qv = model.encode([q.text for q in queries], batch_size=32,
                      normalize_embeddings=True, show_progress_bar=False)

    # pre-compute the per-query clean ranking once; it does not depend on the profile
    clean_top = {}
    for qi, q in enumerate(queries):
        clean_top[qi] = float(np.sort(dv @ qv[qi])[-1])

    print()
    print('%-8s %-8s %-9s %-8s %s'
          % ('min_frac', 'strength', 'partial', 'levels', 'poison count distribution'))
    print('-' * 84)
    best = None
    for min_frac in (0.02, 0.05, 0.10):
        for strength in (0.15, 0.25, 0.4):
            counts = []
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
                    frac = min_frac + (1.0 - min_frac) * (i / 5.0)
                    frac *= strength
                    k = max(1, int(round(frac * len(terms))))
                    texts.append('%s %s' % (strip_filler(base.text), ' '.join(terms[:k])))
                pv = model.encode(texts, batch_size=32, normalize_embeddings=True,
                                  show_progress_bar=False)
                sims = np.concatenate([dv @ qv[qi], pv @ qv[qi]])
                top = np.argsort(-sims)[:5]
                counts.append(int(sum(1 for t in top if t >= len(docs))))
            c = collections.Counter(counts)
            tot = sum(c.values()) or 1
            part = sum(v for k, v in c.items() if 0 < k < 5)
            nlev = len([k for k in c if k > 0])
            frac_part = part / tot
            print('%-8.2f %-8.2f %-9s %-8d %s'
                  % (min_frac, strength, '%.1f%%' % (100 * frac_part), nlev,
                     dict(sorted(c.items()))))
            if best is None or frac_part > best[0]:
                best = (frac_part, min_frac, strength, dict(sorted(c.items())))
    print()
    print('best by partial fraction: min_frac=%.2f strength=%.2f -> %.1f%%  %s'
          % (best[1], best[2], 100 * best[0], best[3]))
    print()
    print('Note: ranks by embedding similarity only; BM25 adds a length term and the')
    print('      projection attack overrides text entirely.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
