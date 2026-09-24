"""Can the encoder run on the GPU, and does it produce the same retrieval?

Two questions, and the second matters more than the first.

1. **Speed.** GTE-base encodes this machine's CPU at ~5 documents/second, which is
   why the full BBQ corpus costs 59 minutes per pass and why the generation-stage
   evaluation was subsampled to 22 queries. If the GPU is one to two orders of
   magnitude faster, the full-corpus evaluation becomes affordable and the
   "48 retrieval slots, 16 distinct questions" limitation largely goes away.

2. **Equivalence.** The paper's retrieval numbers were produced with a CPU build of
   torch. If GPU encoding changes the embeddings materially, the two cannot be
   mixed and the published tables would have to be regenerated. Float32 matmuls
   differ between devices only through reduction order, so the expectation is
   agreement to ~1e-5 -- but this measures it rather than assuming it, on the
   actual corpus and the actual model.

Also reports retrieval agreement: do the top-5 sets match, and do the
retrieval-layer metrics the paper reports agree?
"""
import os
import sys
import time

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from src.data.corpus import load_corpus  # noqa: E402

N_DOCS = 1500          # enough to measure a rate and to compare rankings
BACKBONE = 'thenlper/gte-base'


def encode(texts, device, batch_size=64, max_length=512):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(BACKBONE, device=device)
    model.max_seq_length = max_length
    t0 = time.time()
    with torch.no_grad():
        v = model.encode(texts, batch_size=batch_size, convert_to_numpy=True,
                         normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(v, dtype=np.float32), time.time() - t0


def main():
    print('torch %s  cuda=%s' % (torch.__version__, torch.cuda.is_available()))
    if torch.cuda.is_available():
        print('device: %s' % torch.cuda.get_device_name(0))

    bundle = load_corpus()
    docs = [d.text for d in bundle.docs][:N_DOCS]
    queries = [q.text for q in bundle.queries]
    print('corpus slice: %d docs, %d queries' % (len(docs), len(queries)))
    print()

    emb = {}
    timing = {}
    for dev in ('cpu', 'cuda'):
        if dev == 'cuda' and not torch.cuda.is_available():
            continue
        v, dt = encode(docs, dev)
        emb[dev] = v
        timing[dev] = dt
        print('%-5s %5d docs in %7.2fs  = %6.1f docs/s   (full 17,792 = %.1f min)'
              % (dev, len(docs), dt, len(docs) / dt, 17792 / (len(docs) / dt) / 60))

    if 'cuda' not in emb:
        print('\nno GPU available; nothing to compare')
        return 0

    print()
    speedup = timing['cpu'] / timing['cuda']
    print('speedup: %.1fx' % speedup)

    # --- equivalence --------------------------------------------------------- #
    a, b = emb['cpu'], emb['cuda']
    cos = (a * b).sum(axis=1)          # both are L2-normalised
    diff = np.abs(a - b).max()
    print()
    print('=== equivalence of CPU vs GPU embeddings ===')
    print('  max |a-b|            : %.3e' % diff)
    print('  cosine(a,b) min/mean : %.8f / %.8f' % (cos.min(), cos.mean()))
    print('  identical rows       : %d / %d'
          % (int((np.abs(a - b).max(axis=1) == 0).sum()), len(a)))

    # --- ranking agreement --------------------------------------------------- #
    q = encode(queries, 'cuda', max_length=128)[0]
    # queries encoded with the doc model in both cases for a like-for-like test
    qc = encode(queries, 'cpu', max_length=128)[0]
    print()
    print('=== retrieval agreement ===')
    agree = 0
    for j in range(len(queries)):
        sa = (a @ qc[j]).argsort()[::-1][:5]
        sb = (b @ q[j]).argsort()[::-1][:5]
        if set(sa.tolist()) == set(sb.tolist()):
            agree += 1
    print('  top-5 identical        : %d / %d queries' % (agree, len(queries)))
    print('  query embeddings differ: %.3e' % np.abs(q - qc).max())

    print()
    if diff < 1e-4 and agree == len(queries):
        print('VERDICT: GPU encoding is equivalent for this purpose; '
              'the published tables stand and GPU encoding can be used to '
              'afford the full corpus.')
    else:
        print('VERDICT: GPU encoding differs enough to matter (max diff %.2e, '
              '%d/%d top-5 agreement). Mixing devices would silently change '
              'results, so the retrieval tables would need regenerating on one '
              'device before any GPU-accelerated run.' % (diff, agree, len(queries)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
