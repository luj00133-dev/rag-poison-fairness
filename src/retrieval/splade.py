"""
SPLADE retriever: learned sparse retrieval.

Why SPLADE matters for this paper
---------------------------------
Our backbone comparison (Findings 6 and 7) currently covers two representation
families: lexical (BM25) and dense semantic (GTE-base, Contriever, E5-base-v2).
Text-only injection splits the dense encoders 2-to-1, which raises an obvious
question the two families cannot answer: is susceptibility a property of
*sparsity* or of *density*? SPLADE is the natural test because it is **learned
sparse** -- it keeps a lexical, term-level representation but learns the term
weights, so it sits between the two families rather than in either.

If SPLADE behaves like BM25, susceptibility tracks sparse representations and the
finding becomes a clean sparse/dense dichotomy. If it behaves like E5/GTE, then
what protects an encoder is something the learned weights capture, and sparse
versus dense is not the right axis. Either outcome sharpens Finding 7; we do not
predict which.

Implementation
--------------
SPLADE scores by the inner product of sparse term-weight vectors::

    w(t, x) = max_i log(1 + ReLU(logit_i(t)))      for t in the input's tokens
    score(q, d) = sum_t  w_q(t) * w_d(t)

The max is taken over the token positions at which term ``t`` occurs. We
implement this directly on top of ``transformers`` rather than pulling in a
retrieval library, because the pipeline needs a retriever that exposes its
vectors for the projection attack, and because reproducing the formula exactly
matters for a cross-paper comparison.

Memory
------
Document vectors are stored as ``(indices, values)`` pairs (a dense vocabulary
vector per document would be 30k floats). Retrieval is then a sparse dot product
per document, vectorised over documents with numpy.

Requires ``transformers`` and ``torch``; the model is ~440 MB.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .base import Document, Query, RetrievalResult

#: SPLADE checkpoints. ``splade_v2_distil`` is the smaller distilled variant;
#: ``splade-cocondenser-ensembledistil`` is the standard DistilBERT ensemble.
#:
#: The published ``efficient-splade-*`` family splits the encoder in two: a
#: query-side model and a document-side model, each fine-tuned separately. Both
#: halves are needed, so entries whose value is a ``(query_id, doc_id)`` pair are
#: handled by :class:`SpladeRetriever` with two loaded models. Two documented
#: hazards of that family are handled explicitly: the checkpoints carry 30522
#: *tokenizer* rows but the model's MLM head is sized to 30000, so the logits
#: must be sliced to the model's own vocab size; and the queries must be encoded
#: with the query half or the retrieval quality collapses.
SPLADE_MODELS: Dict[str, object] = {
    "splade-v2-distil": "naver/splade_v2_distil",
    "splade-cocondenser": "naver/splade-cocondenser-ensembledistil",
    # large-scale, split query/doc encoders (for the scale check)
    "splade-large": (
        "naver/efficient-splade-VI-BT-large-query",
        "naver/efficient-splade-VI-BT-large-doc",
    ),
}


@dataclass
class SparseVector:
    """Sparse term-weight vector, kept as parallel index/value arrays."""

    indices: np.ndarray  # int32 term ids with non-zero weight
    values: np.ndarray   # float32 weights, same length

    def to_dense(self, dim: int) -> np.ndarray:
        v = np.zeros(dim, dtype=np.float32)
        v[self.indices] = self.values
        return v


class SpladeRetriever:
    """Learned sparse retriever (SPLADE) with vectors exposed for perturbation.

    The class deliberately mirrors the interface of the other retrievers --
    ``index``, ``search``, ``matrix``/``set_matrix`` -- so that the defenses, the
    projection attack and the adaptive harness all work unchanged. ``matrix``
    here is a *dense* (n_docs, vocab) float32 array, materialised on demand; it
    is large (n_docs x 30k) so it is only built when a caller actually needs
    per-document vectors.
    """

    name = "splade"

    #: process-wide text -> sparse-vector cache, keyed by (model_id, text).
    #: Each defense variant builds its own retriever and re-indexes the corpus;
    #: without this the same ~2 x 10^3 passages are re-encoded once per variant
    #: (8x on the default sweep) plus once per attack/rate combination, which
    #: made the sweep take tens of minutes.
    _CACHE: Dict[Tuple[str, str], "SparseVector"] = {}
    _CACHE_HITS = 0
    _CACHE_MISSES = 0

    def __init__(
        self,
        backbone: str = "splade-v2-distil",
        *,
        device: Optional[str] = None,
        batch_size: int = 32,
        max_length: int = 256,
        top_k_terms: int = 256,
    ) -> None:
        from .dense import configure_hf_mirror

        configure_hf_mirror()

        try:
            import torch
            from transformers import AutoModelForMaskedLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "SPLADE needs transformers and torch: "
                "python -m pip install transformers torch"
            ) from exc

        self._torch = torch
        spec = SPLADE_MODELS.get(backbone, backbone)
        # a split checkpoint is a (query_id, doc_id) pair; a single checkpoint
        # encodes both sides
        if isinstance(spec, tuple):
            query_id, doc_id = spec
        else:
            query_id = doc_id = spec
        self.model_id = doc_id
        self.query_model_id = query_id
        self.split_encoder = query_id != doc_id
        self.backbone = backbone
        self.name = f"splade:{backbone}"
        self.batch_size = batch_size
        self.max_length = max_length
        self.top_k_terms = top_k_terms

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        self.tokenizer = AutoTokenizer.from_pretrained(doc_id)
        self.model = AutoModelForMaskedLM.from_pretrained(doc_id)
        self.model.eval()
        self.model.to(device)
        # The efficient-splade checkpoints ship a tokenizer with 30522 rows but
        # an MLM head of 30000. Term ids are tokenizer ids, so the vector width
        # must be the tokenizer's; the head is sliced to match at encode time.
        self.model_vocab_size = int(self.model.config.vocab_size)
        self.vocab_size = int(self.tokenizer.vocab_size)

        if self.split_encoder:
            self.query_tokenizer = AutoTokenizer.from_pretrained(query_id)
            self.query_model = AutoModelForMaskedLM.from_pretrained(query_id)
            self.query_model.eval()
            self.query_model.to(device)
            # guard the tokenizer/model vocab mismatch on the query half too
            self.query_model_vocab_size = int(
                self.query_model.config.vocab_size
            )
            self.query_vocab_size = int(self.query_tokenizer.vocab_size)
        else:
            self.query_tokenizer = self.tokenizer
            self.query_model = self.model
            self.query_vocab_size = self.vocab_size
            self.query_model_vocab_size = self.model_vocab_size

        self.docs: List[Document] = []
        #: per-document sparse vectors, so retrieval never re-encodes the corpus
        self._doc_vecs: List[SparseVector] = []
        #: dense matrix is expensive; build lazily and cache
        self._matrix: Optional[np.ndarray] = None

    # -- encoding ---------------------------------------------------------- #

    def _encode_sparse(
        self, texts: Sequence[str], *, side: str = "doc"
    ) -> List[SparseVector]:
        """SPLADE term weights: ``max_i log(1 + ReLU(logit_i))`` per term.

        ``side`` selects which model encodes the batch. It is ignored for a
        single-encoder checkpoint (where both sides are the same model) and is
        essential for the split ``efficient-splade`` checkpoints, whose query
        and document halves were fine-tuned separately: encoding queries with
        the document model, or vice versa, silently degrades retrieval.

        Uses a process-wide content cache: only uncached texts reach the model,
        so re-indexing an already-seen corpus costs a dict lookup per passage
        instead of a forward pass. The cache key includes the side, so the two
        halves never share entries.
        """
        texts = list(texts)
        model_id = self.query_model_id if side == "query" else self.model_id
        keys = [(model_id, t) for t in texts]
        missing = [i for i, k in enumerate(keys) if k not in self._CACHE]
        if missing:
            fresh = self._encode_sparse_uncached(
                [texts[i] for i in missing], side=side
            )
            for slot, i in enumerate(missing):
                self._CACHE[keys[i]] = fresh[slot]
            type(self)._CACHE_MISSES += len(missing)
        type(self)._CACHE_HITS += len(texts) - len(missing)
        return [self._CACHE[k] for k in keys]

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

    def _encode_sparse_uncached(
        self, texts: Sequence[str], *, side: str = "doc"
    ) -> List[SparseVector]:
        torch = self._torch
        if side == "query":
            tokenizer, model = self.query_tokenizer, self.query_model
            keep = min(self.query_vocab_size, self.query_model_vocab_size)
        else:
            tokenizer, model = self.tokenizer, self.model
            keep = min(self.vocab_size, self.model_vocab_size)
        out: List[SparseVector] = []
        with torch.no_grad():
            for start in range(0, len(texts), self.batch_size):
                batch = list(texts[start:start + self.batch_size])
                enc = tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                )
                enc = {k: v.to(self.device) for k, v in enc.items()}
                # pad the head out to the tokenizer width when the head is
                # narrower, so every returned vector is .vocab_size wide
                raw = model(**enc).logits  # (B, T, head_vocab)
                if raw.shape[-1] < self.vocab_size:
                    pad = torch.zeros(
                        *raw.shape[:-1], self.vocab_size - raw.shape[-1],
                        dtype=raw.dtype, device=raw.device,
                    )
                    raw = torch.cat([raw, pad], dim=-1)
                elif raw.shape[-1] > self.vocab_size:
                    raw = raw[..., : self.vocab_size]
                # ReLU then log1p, then max over token positions
                act = torch.log1p(torch.relu(raw))
                # ignore padding positions so they cannot contribute
                mask = enc["attention_mask"].unsqueeze(-1).float()
                act = act * mask
                vec, _ = torch.max(act, dim=1)  # (B, V)
                vec = vec.cpu().numpy()
                for row in vec:
                    nz = np.nonzero(row)[0]
                    if nz.size > self.top_k_terms:
                        # keep the heaviest terms; harmless for scoring, and it
                        # keeps the sparse dot products cheap
                        keep = np.argpartition(-row[nz], self.top_k_terms)[
                            : self.top_k_terms
                        ]
                        nz = nz[keep]
                    out.append(
                        SparseVector(
                            indices=nz.astype(np.int32),
                            values=row[nz].astype(np.float32),
                        )
                    )
        return out

    # -- vector access (for the projection attack) ------------------------- #

    @property
    def matrix(self) -> np.ndarray:
        """Dense (n_docs, vocab) term-weight matrix, materialised on demand.

        The sparse representation is kept for scoring; the projection attack
        needs to perturb document vectors and re-install them, which requires a
        dense array. Building it costs ~n_docs x vocab floats, so it is cached
        and only built when a caller asks for it.
        """
        if self._matrix is None:
            m = np.zeros((len(self._doc_vecs), self.vocab_size), dtype=np.float32)
            for i, sv in enumerate(self._doc_vecs):
                m[i, sv.indices] = sv.values
            self._matrix = m
        return self._matrix

    def set_matrix(self, matrix: np.ndarray) -> None:
        m = np.asarray(matrix, dtype=np.float32)
        if m.shape[0] != len(self.docs):
            raise ValueError(f"matrix rows {m.shape[0]} != n_docs {len(self.docs)}")
        self._matrix = m
        # rebuild the sparse view so scoring sees the perturbed vectors
        self._doc_vecs = []
        for row in m:
            nz = np.nonzero(row)[0]
            self._doc_vecs.append(
                SparseVector(indices=nz.astype(np.int32),
                             values=row[nz].astype(np.float32))
            )

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        """Dense view of encodings, for code paths written against ``_embed``."""
        out = np.zeros((len(texts), self.vocab_size), dtype=np.float32)
        for i, sv in enumerate(self._encode_sparse(list(texts))):
            out[i, sv.indices] = sv.values
        return out

    _encode = _embed

    # -- interface --------------------------------------------------------- #

    def index(self, docs: Sequence[Document]) -> None:
        self.docs = list(docs)
        self._doc_vecs = self._encode_sparse([d.text for d in self.docs])
        self._matrix = None  # invalidate; rebuilt lazily

    def search(self, query: str, k: int) -> RetrievalResult:
        return self.search_batch([query], k)[0]

    def search_batch(self, queries: Sequence[str], k: int) -> List[RetrievalResult]:
        """Score many queries in one encode call, then retrieve for each.

        Scoring is a single ``(n_docs, V) @ (V, n_queries)`` product rather than a
        per-document sparse loop. At ~2 x 10^3 documents and a 30k vocabulary the
        dense document matrix is ~200 MB, which is cheaper in wall-clock than
        thousands of interpreted index intersections -- the loop version made the
        sweep intractable.
        """
        if not queries:
            return []
        qvecs = self._encode_sparse(list(queries))
        qmat = np.zeros((self.vocab_size, len(qvecs)), dtype=np.float32)
        for j, qv in enumerate(qvecs):
            qmat[qv.indices, j] = qv.values
        doc_mat = self._dense_doc_matrix()
        sims_all = doc_mat @ qmat  # (n_docs, n_queries)

        results: List[RetrievalResult] = []
        kk = min(k, len(self.docs))
        for j in range(len(qvecs)):
            sims = sims_all[:, j]
            idx = np.argsort(-sims, kind="stable")[:kk]
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
            results.append(RetrievalResult(qid="", docs=docs, scores=sims[idx]))
        return results

    def _dense_doc_matrix(self) -> np.ndarray:
        """Cached (n_docs, V) term-weight matrix used for scoring.

        ``V`` is the **tokenizer's** vocabulary width, not the MLM head's. The
        split ``efficient-splade`` checkpoints ship a 30522-row tokenizer against
        a 30000-wide head, so the head is sliced to the tokenizer width during
        encoding (see ``_encode_sparse_uncached``): the two must agree or the
        scatter below writes out of bounds or scores misaligned dimensions.
        """
        if self._matrix is None or self._matrix.shape[0] != len(self._doc_vecs):
            m = np.zeros((len(self._doc_vecs), self.vocab_size), dtype=np.float32)
            for i, dv in enumerate(self._doc_vecs):
                m[i, dv.indices] = dv.values
            self._matrix = m
        return self._matrix

    def _sparse_dot(self, a: SparseVector, b: SparseVector) -> float:
        """Inner product of two sparse vectors via index intersection.

        Retained for correctness checks against the matrix path; the retrieval
        hot path does not use it.
        """
        if a.indices.size == 0 or b.indices.size == 0:
            return 0.0
        common, ia, ib = np.intersect1d(a.indices, b.indices, return_indices=True)
        if common.size == 0:
            return 0.0
        return float(np.dot(a.values[ia], b.values[ib]))

    def search_many(self, queries: Sequence[Query], k: int) -> List[RetrievalResult]:
        out = self.search_batch([q.text for q in queries], k)
        for r, q in zip(out, queries):
            r.qid = q.qid
        return out
