"""
Real-encoder dense retrievers, for backbone alignment with the fairness-defense
literature.

Why this module exists
---------------------
The main experiments use a self-contained feature-hashing dense retriever. That
makes the study dependency-free and fully reproducible, but it means our numbers
cannot be placed next to published results that use standard encoders. This
module closes that gap by providing the exact backbones used by the work we
compare against:

  ``gte-base``     -- as used by Zhao et al. (FARO), arXiv:2605.15790
  ``contriever``   -- as used by Kim & Diaz (ICTIR 2025), arXiv:2409.11598
  ``e5-base-v2``   -- as used by Wang et al. (BRRA, IEEE TDSC 2026) and
                      Wu et al. (COLING 2025)
  ``bge-m3``       -- a stronger multilingual option for replication

Downloading
-----------
HuggingFace is often unreachable from mainland China. Set the mirror before
importing this module:

    set HF_ENDPOINT=https://hf-mirror.com          (Windows)
    export HF_ENDPOINT=https://hf-mirror.com       (bash)

``hf-mirror.com`` is a public read-only mirror of the Hub and serves the same
model files. The helper :func:`configure_hf_mirror` sets it programmatically.

Memory
------
``gte-base`` and ``contriever`` are ~110M parameters (~440 MB in fp32), so
inference fits comfortably in CPU RAM and trivially in the 8 GB of a consumer
GPU. This is the reason the retrieval-layer study needs no large-model hardware:
the encoders that matter for retrieval fairness are two orders of magnitude
smaller than the generators usually blamed for bias.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Sequence

import numpy as np

from .base import Document, Query, RetrievalResult

#: Encoder registry: name -> HuggingFace model id.
BACKBONES: Dict[str, str] = {
    # FARO baseline encoder
    "gte-base": "thenlper/gte-base",
    # Kim & Diaz (ICTIR 2025) baseline encoder
    "contriever": "facebook/contriever",
    # BRRA / Wu et al. baseline encoder
    "e5-base-v2": "intfloat/e5-base-v2",
    # stronger multilingual option
    "bge-m3": "BAAI/bge-m3",
}


def configure_hf_mirror(endpoint: str = "https://hf-mirror.com") -> None:
    """Point huggingface_hub at a mirror.

    Must be called before transformers/huggingface_hub are imported, or before
    the first model download. Harmless if HuggingFace is directly reachable.
    """
    os.environ.setdefault("HF_ENDPOINT", endpoint)


class SentenceTransformerRetriever:
    """Dense retriever over a sentence-transformers encoder.

    Parameters
    ----------
    backbone:
        A key of :data:`BACKBONES`, or any HuggingFace model id.
    query_prefix, doc_prefix:
        Some encoders require task prefixes (E5 uses ``"query: "`` /
        ``"passage: "``; GTE and Contriever do not). Providing them matters:
        omitting an E5 prefix measurably degrades retrieval, which would show up
        as a spurious difference against published numbers.
    batch_size:
        Encoding batch size. 64 is safe on CPU; raise it on a GPU.
    device:
        ``None`` selects CUDA when available, else CPU.
    """

    name = "st"

    #: process-wide (model_id, prefix, text) -> vector cache, shared across
    #: instances.  Essential for this pipeline: every defense variant builds
    #: its own retriever and re-indexes the corpus, so without a cache the same
    #: passages are encoded once per defense (8x on the default sweep) plus once
    #: per attack/rate combination.  With a real encoder that is the difference
    #: between seconds and tens of minutes.
    _CACHE: Dict[tuple, np.ndarray] = {}
    _CACHE_HITS = 0
    _CACHE_MISSES = 0

    def __init__(
        self,
        backbone: str = "gte-base",
        *,
        batch_size: int = 64,
        device: Optional[str] = None,
        query_prefix: str = "",
        doc_prefix: str = "",
        normalize: bool = True,
        max_length: int = 512,
        use_cache: bool = True,
    ) -> None:
        configure_hf_mirror()
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "sentence-transformers is required for real encoders. "
                "Install with: python -m pip install sentence-transformers"
            ) from exc

        model_id = BACKBONES.get(backbone, backbone)
        self.model_id = model_id
        self.backbone = backbone
        self.name = f"st:{backbone}"
        self.batch_size = batch_size
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix
        self.normalize = normalize
        self.use_cache = use_cache

        if device is None:
            try:
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"
        self.device = device

        self.model = SentenceTransformer(model_id, device=device)
        if max_length:
            self.model.max_seq_length = max_length
        self.docs: List[Document] = []
        self.matrix = np.zeros((0, 1), dtype=np.float32)

    # -- encoding ---------------------------------------------------------- #

    def _encode_uncached(self, texts: Sequence[str], prefix: str) -> np.ndarray:
        vecs = self.model.encode(
            [prefix + t for t in texts],
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype=np.float32)

    def _encode(self, texts: Sequence[str], prefix: str = "") -> np.ndarray:
        """Encode with a process-wide content cache.

        Only uncached texts reach the model, so re-indexing an already-seen
        corpus costs a dict lookup per passage instead of a forward pass.
        """
        texts = list(texts)
        if not self.use_cache:
            return self._encode_uncached(texts, prefix)

        keys = [(self.model_id, prefix, t) for t in texts]
        missing = [i for i, k in enumerate(keys) if k not in self._CACHE]
        if missing:
            fresh = self._encode_uncached([texts[i] for i in missing], prefix)
            for slot, i in enumerate(missing):
                self._CACHE[keys[i]] = fresh[slot]
            type(self)._CACHE_MISSES += len(missing)
        type(self)._CACHE_HITS += len(texts) - len(missing)
        return np.stack([self._CACHE[k] for k in keys]).astype(np.float32)

    @classmethod
    def cache_stats(cls) -> Dict[str, object]:
        total = cls._CACHE_HITS + cls._CACHE_MISSES
        return {
            "entries": len(cls._CACHE),
            "hits": cls._CACHE_HITS,
            "misses": cls._CACHE_MISSES,
            "hit_rate": (cls._CACHE_HITS / total) if total else 0.0,
        }

    @classmethod
    def clear_cache(cls) -> None:
        cls._CACHE.clear()
        cls._CACHE_HITS = 0
        cls._CACHE_MISSES = 0

    # -- interface --------------------------------------------------------- #

    def index(self, docs: Sequence[Document]) -> None:
        self.docs = list(docs)
        self.matrix = self._encode([d.text for d in self.docs], self.doc_prefix)

    def set_matrix(self, matrix: np.ndarray) -> None:
        m = np.asarray(matrix, dtype=np.float32)
        if m.shape[0] != len(self.docs):
            raise ValueError(f"matrix rows {m.shape[0]} != n_docs {len(self.docs)}")
        self.matrix = m

    def search(self, query: str, k: int) -> RetrievalResult:
        q = self._encode([query], self.query_prefix)[0]
        return self._search_with_vector(q, k, qid="")

    def search_batch(
        self, queries: Sequence[str], k: int
    ) -> List[RetrievalResult]:
        """Encode many queries in one model call, then retrieve for each.

        A single ``encode`` call on a batch amortises the per-call overhead of
        the transformer stack, which dominates when queries are encoded one at a
        time. The multi-query defense issues one query per paraphrase variant, so
        per-call overhead was the binding cost in the sweep; batching removes it.
        """
        if not queries:
            return []
        qmat = self._encode(list(queries), self.query_prefix)
        return [self._search_with_vector(qmat[i], k, qid="") for i in range(len(queries))]

    def _search_with_vector(self, q: np.ndarray, k: int, qid: str) -> RetrievalResult:
        sims = self.matrix @ q
        k = min(k, len(self.docs))
        idx = np.argsort(-sims, kind="stable")[:k]
        docs = [
            Document(
                doc_id=self.docs[int(i)].doc_id,
                text=self.docs[int(i)].text,
                group=self.docs[int(i)].group,
                stance=self.docs[int(i)].stance,
                is_poison=self.docs[int(i)].is_poison,
                score=float(sims[int(i)]),
            )
            for i in idx
        ]
        return RetrievalResult(qid=qid, docs=docs, scores=sims[idx])

    def search_many(self, queries: Sequence[Query], k: int) -> List[RetrievalResult]:
        out = []
        for q in queries:
            r = self.search(q.text, k)
            r.qid = q.qid
            out.append(r)
        return out


def build_sentence_transformer(backbone: str, **kwargs) -> SentenceTransformerRetriever:
    """Construct a retriever with the correct task prefixes for the backbone."""
    if backbone.startswith("e5"):
        # E5 was trained with explicit task prefixes; omitting them degrades
        # retrieval enough to distort cross-paper comparisons.
        kwargs.setdefault("query_prefix", "query: ")
        kwargs.setdefault("doc_prefix", "passage: ")
    return SentenceTransformerRetriever(backbone, **kwargs)
