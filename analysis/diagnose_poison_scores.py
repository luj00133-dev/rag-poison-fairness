"""Direct test: do the *injected passages themselves* score differently on
GTE-base and GTE-large?

The geometry diagnostic ruled out the representation-geometry explanation (H1):
GTE-base and GTE-large are near-identical in anisotropy (0.848 vs 0.858), in
effective dimensionality (13.2 both) and in the spread of query similarity
(0.086 vs 0.082). So the 8x difference in text-attack success must come from
where the poisoned passages *land*, not from the shape of the space.

This script builds the actual poison set with the same code the experiment uses,
then compares, for the same queries:
  * the poisoned passages' cosine to the query, vs. clean passages';
  * the best poisoned rank and its margin to the k-th clean score;
  * the number of queries where a poisoned passage enters the top-k.
"""
import os
import sys

import numpy as np

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.attacks.poisoning import PoisonSpec, make_poison_docs
from src.data.corpus import load_corpus
from src.retrieval.dense import SentenceTransformerRetriever

K = 5


def build_poison(bundle, n_per=9, seed=20260101):
    """Same construction the experiment driver uses (run_experiment._make_all_poison)."""
    poison = []
    for i, (stratum, gp) in enumerate(bundle.groups.items()):
        fav, sup = gp[0], gp[1]
        pool = [d for d in bundle.docs if d.group in (fav, sup)]
        if not pool:
            continue
        poison.extend(make_poison_docs(pool, PoisonSpec(
            favoured_group=fav, suppressed_group=sup, n_poison=n_per,
            prefix='POISON-%s' % stratum, seed=seed + i)))
    return poison


def run(backbone, bundle):
    r = SentenceTransformerRetriever(backbone=backbone, batch_size=16)
    r.index(bundle.docs)
    clean = r.matrix.astype(np.float64)

    poison = build_poison(bundle)
    pm = r._encode([d.text for d in poison], r.doc_prefix).astype(np.float64)
    qmat = r._encode([q.text for q in bundle.queries], r.query_prefix).astype(np.float64)

    def norm(M):
        return M / np.maximum(np.linalg.norm(M, axis=1, keepdims=True), 1e-12)

    cn, pn, qn = norm(clean), norm(pm), norm(qmat)
    hits = 0
    gains, margins, best_poison_cos, thresholds = [], [], [], []
    for j in range(len(qn)):
        cs = cn @ qn[j]
        ps = pn @ qn[j]
        threshold = np.sort(cs)[::-1][K - 1]
        best = ps.max()
        hits += int(best >= threshold)
        margins.append(best - threshold)
        gains.append(ps.mean() - cs.mean())
        best_poison_cos.append(best)
        thresholds.append(threshold)
    hits /= len(qn)

    print('%-14s  n_poison=%d' % (backbone, len(poison)))
    print('%-14s  poison@k (clean corpus, no defense) = %.4f' % ('', hits))
    print('%-14s  mean(poison cos - clean cos)          = %+.4f'
          % ('', float(np.mean(gains))))
    print('%-14s  mean best-poison cos                 = %.4f' % ('', float(np.mean(best_poison_cos))))
    print('%-14s  mean top-5 clean threshold           = %.4f' % ('', float(np.mean(thresholds))))
    print('%-14s  mean margin (best poison - threshold)= %+.4f'
          % ('', float(np.mean(margins))))
    print()
    return hits


def main():
    bundle = load_corpus()
    for backbone in ('gte-base', 'gte-large'):
        run(backbone, bundle)


if __name__ == '__main__':
    main()
