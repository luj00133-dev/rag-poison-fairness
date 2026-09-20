"""Smoke test: can we download and run a real encoder through the HF mirror?"""
import os
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
print("HF_ENDPOINT =", os.environ["HF_ENDPOINT"])

t0 = time.time()
try:
    from sentence_transformers import SentenceTransformer
    print(f"[{time.time()-t0:.1f}s] sentence_transformers imported")
except Exception as e:
    print("IMPORT FAIL:", e)
    raise SystemExit(1)

for name in ("thenlper/gte-base",):
    t = time.time()
    try:
        m = SentenceTransformer(name, device="cpu")
        print(f"[{time.time()-t:.1f}s] loaded {name}")
        dim = m.get_sentence_embedding_dimension()
        print(f"           embedding dim = {dim}")
    except Exception as e:
        print(f"LOAD FAIL {name}: {type(e).__name__}: {str(e)[:300]}")
        raise SystemExit(1)

    t = time.time()
    vecs = m.encode(
        ["Who performed better in the engineering evaluation?",
         "The woman engineer produced the highest measured accuracy."],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    print(f"[{time.time()-t:.1f}s] encoded 2 sentences")
    import numpy as np
    v = np.asarray(vecs)
    print(f"           shape={v.shape}  cosine={float(v[0] @ v[1]):.4f}")
    print("ENCODER OK")
