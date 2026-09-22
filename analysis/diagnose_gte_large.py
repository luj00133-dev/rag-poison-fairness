"""Why does GTE-large become susceptible when GTE-base does not?

Reporting the 0.0625 -> 0.5000 jump is a number; a reviewer will ask for the
mechanism. The attack works by appending query-aligned vocabulary to the injected
text, which raises its cosine similarity to the query. Whether that is enough to
enter the top-k depends on the *margin* between the injected passage and the
legitimate competition, so two candidate explanations are testable:

  (H1) representation geometry -- GTE-large's embedding space is more
       anisotropic (vectors concentrated in a narrow cone), which compresses
       cosine differences between relevant and irrelevant passages, so a fixed
       textual nudge buys a larger rank change;

  (H2) the attack's raw gain -- GTE-large simply scores the poisoned passages
       higher relative to clean ones for the same appended text.

This measures the similarity of poisoned vs clean passages to the query, and the
anisotropy (mean pairwise cosine) of each encoder's document matrix.
"""
import os
import sys

import numpy as np

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.corpus import load_corpus
from src.retrieval.dense import SentenceTransformerRetriever


def load_docs():
    bundle = load_corpus()
    return bundle.docs, bundle.queries


def main():
    docs, queries = load_docs()
    print('corpus: %d docs, %d queries' % (len(docs), len(queries)))
    print()

    for backbone in ('gte-base', 'gte-large', 'e5-base-v2', 'e5-large-v2'):
        r = SentenceTransformerRetriever(backbone=backbone, batch_size=16)
        r.index(docs)
        M = r.matrix.astype(np.float64)
        n = M / np.maximum(np.linalg.norm(M, axis=1, keepdims=True), 1e-12)

        # anisotropy: mean pairwise cosine over a sample of documents
        rng = np.random.default_rng(0)
        idx = rng.choice(len(n), size=min(400, len(n)), replace=False)
        S = n[idx] @ n[idx].T
        off = S[~np.eye(len(idx), dtype=bool)]
        aniso = float(off.mean())

        # effective dimensionality of the document cloud
        cov = np.cov(n[idx].T)
        ev = np.linalg.eigvalsh(cov)[::-1]
        ev = ev / ev.sum()
        eff_dim = float(np.exp(-(ev * np.log(ev + 1e-12)).sum()))

        # cosines: every clean doc vs. the first query
        q = r._encode([queries[0].text], r.query_prefix)[0]
        q = q / max(np.linalg.norm(q), 1e-12)
        cos = n @ q
        print('%-14s dim=%4d  anisotropy=%.4f  eff_dim=%6.1f  '
              'cos min/med/max = %.3f / %.3f / %.3f'
              % (backbone, M.shape[1], aniso, eff_dim,
                 cos.min(), np.median(cos), cos.max()))

        # spread of query similarity: a compressed spread means a fixed textual
        # nudge moves rank more easily
        p90, p10 = np.percentile(cos, 90), np.percentile(cos, 10)
        print('%-14s top-decile spread (p90-p10) = %.4f'
              % ('', p90 - p10))
        print()


if __name__ == '__main__':
    main()
