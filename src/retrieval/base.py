"""
Base interfaces for the retrieval layer.

Design notes
------------
Everything in this package is deliberately dependency-light: the *core*
experiment (group-representation drift under retrieval poisoning) is a
distribution-distance computation over a retrieved document set, so it needs
no GPU and no 7B generator.  Retrieval back-ends are pluggable so that the
same defense code can be evaluated with BM25 (pure python fallback), a dense
bi-encoder, or a hybrid retriever.

This keeps the security claim testable on commodity hardware, which matters
because the attack we defend against (subspace projection) was reported to
reach 100% adversarial retrieval success across BM25 and E5 retrievers alike.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

import numpy as np


# --------------------------------------------------------------------------- #
# Document schema
# --------------------------------------------------------------------------- #

@dataclass
class Document:
    """One retrievable unit in the knowledge base.

    Attributes
    ----------
    doc_id:
        Stable identifier.  Poisoned documents use the ``POISON-`` prefix so
        that attack-success metrics can be computed without an oracle.
    text:
        Raw passage text.
    group:
        Protected-group label this passage *speaks about* (e.g. ``"woman"``,
        ``"man"``, ``"elderly"``).  ``None`` for group-neutral passages.
    stance:
        ``+1`` = counter-stereotypical / favourable framing of ``group``,
        ``-1`` = stereotypical / unfavourable framing,
        ``0``  = neutral or no group content.
        This mirrors the (s_j, a_j) stereotype / anti-stereotype template pair
        used by the bias-amplification attack literature, because that pair is
        exactly what makes poisoned passages semantically indistinguishable
        from legitimate ones under a relevance-only view.
    is_poison:
        Ground-truth attack label.  Used ONLY for reporting attack-success
        metrics, never as an input to any defense.
    """

    doc_id: str
    text: str
    group: Optional[str] = None
    stance: int = 0
    is_poison: bool = False

    # populated by the retriever
    score: float = field(default=0.0, compare=False)


@dataclass
class Query:
    """A retrieval query, optionally carrying group-balance bookkeeping."""

    qid: str
    text: str
    #: groups that a *clean* retrieval is expected to represent
    target_groups: Tuple[str, ...] = ()
    #: dataset provenance (e.g. "bbq-gender", "stereoset-age")
    stratum: str = ""


@dataclass
class RetrievalResult:
    """Output of a retriever for a single query."""

    qid: str
    docs: List[Document]
    scores: np.ndarray

    def ids(self) -> List[str]:
        return [d.doc_id for d in self.docs]


# --------------------------------------------------------------------------- #
# Retriever protocol
# --------------------------------------------------------------------------- #

class Retriever(Protocol):
    """Minimal interface every back-end must satisfy."""

    name: str

    def index(self, docs: Sequence[Document]) -> None:
        ...

    def search(self, query: str, k: int) -> RetrievalResult:
        ...

    def search_many(self, queries: Sequence[Query], k: int) -> List[RetrievalResult]:
        ...


# --------------------------------------------------------------------------- #
# Pure-python BM25 (Okapi) -- no external dependency, deterministic
# --------------------------------------------------------------------------- #

_TOKEN_RE = None


def _tokenize(text: str) -> List[str]:
    """Lowercase word tokenizer.

    Kept intentionally simple and dependency-free (no nltk/spacy) so the
    pipeline is reproducible on a bare Python install.
    """
    global _TOKEN_RE
    if _TOKEN_RE is None:
        import re

        _TOKEN_RE = re.compile(r"[a-z0-9]+")
    return _TOKEN_RE.findall(text.lower())


class BM25Retriever:
    """Okapi BM25 with an in-memory inverted index.

    Parameters
    ----------
    k1, b:
        Standard BM25 saturation and length-normalisation constants.
    """

    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs: List[Document] = []
        self._df: Dict[str, int] = {}
        self._len: np.ndarray = np.zeros(0, dtype=np.float64)
        self._avg_len: float = 0.0
        # inverted index: term -> (document ids, term frequencies) as numpy
        # arrays so scoring is vectorised rather than a Python double loop
        self._term_docs: Dict[str, List[int]] = {}
        self._term_tf: Dict[str, np.ndarray] = {}

    # -- indexing ---------------------------------------------------------- #

    def index(self, docs: Sequence[Document]) -> None:
        self.docs = list(docs)
        self._df = {}
        self._term_docs = {}
        tmp: Dict[str, List[int]] = {}
        tmp_tf: Dict[str, List[int]] = {}
        lengths = np.zeros(len(self.docs), dtype=np.float64)

        for i, d in enumerate(self.docs):
            toks = _tokenize(d.text)
            lengths[i] = len(toks)
            tf: Dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            for t, c in tf.items():
                tmp.setdefault(t, []).append(i)
                tmp_tf.setdefault(t, []).append(c)
                self._df[t] = self._df.get(t, 0) + 1

        for t, ids in tmp.items():
            self._term_docs[t] = ids
            self._term_tf[t] = np.asarray(tmp_tf[t], dtype=np.float64)

        self._len = lengths
        self._avg_len = float(self._len.mean()) if len(self._len) else 0.0

    # -- scoring ----------------------------------------------------------- #

    def _score_one(self, query: str) -> np.ndarray:
        """Vectorised BM25 scoring.

        The naive formulation evaluates every (term, document) pair in Python,
        which is O(|query terms| x |corpus|) interpreted iterations -- on the
        order of 10^8 for a corpus of ~2 x 10^4 passages, and repeated for
        every defense variant.  We instead store the term-frequency matrix in
        CSR form and compute each term's contribution as a single vectorised
        operation, which reduces the cost to O(nnz) with numpy doing the inner
        loop.
        """
        n = len(self.docs)
        if n == 0:
            return np.zeros(0, dtype=np.float64)

        scores = np.zeros(n, dtype=np.float64)
        # precomputed per-document length normalisation denominator
        denom_base = 1.0 - self.b + self.b * self._len / max(self._avg_len, 1e-9)

        for term in set(_tokenize(query)):
            df = self._df.get(term, 0)
            if df == 0:
                continue
            idf = float(np.log(1.0 + (n - df + 0.5) / (df + 0.5)))
            rows = self._term_docs.get(term)
            if not rows:
                continue
            idx = np.fromiter(rows, dtype=np.int64, count=len(rows))
            f = self._term_tf[term].astype(np.float64)
            scores[idx] += idf * (f * (self.k1 + 1.0)) / (f + self.k1 * denom_base[idx])
        return scores

    def search(self, query: str, k: int) -> RetrievalResult:
        scores = self._score_one(query)
        k = min(k, len(self.docs))
        # stable sort so ties are resolved by index (keeps runs reproducible)
        idx = np.argsort(-scores, kind="stable")[:k]
        docs = []
        for i in idx:
            d = self.docs[int(i)]
            docs.append(
                Document(
                    doc_id=d.doc_id,
                    text=d.text,
                    group=d.group,
                    stance=d.stance,
                    is_poison=d.is_poison,
                    score=float(scores[int(i)]),
                )
            )
        return RetrievalResult(qid="", docs=docs, scores=scores[idx])

    def search_many(self, queries: Sequence[Query], k: int) -> List[RetrievalResult]:
        out = []
        for q in queries:
            r = self.search(q.text, k)
            r.qid = q.qid
            out.append(r)
        return out
