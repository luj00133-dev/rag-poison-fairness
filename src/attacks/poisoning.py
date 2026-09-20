"""
Poisoning attacks against the retrieval layer.

Two attack families are implemented:

``template_injection``
    The *content* attack: poisoned passages clone the legitimate template and
    differ only in which group they favour.  Because the surface form is near
    identical to clean passages, relevance-based detection has almost no signal
    to work with.  This is the minimal attack that the defense must handle.

``subspace_projection``
    The *representation* attack: poisoned passage vectors are pushed along the
    query direction in embedding space, which raises their similarity without
    changing their text.  This mirrors the published bias-amplification attack,
    which reported 100% adversarial retrieval success against both BM25 and
    dense retrievers -- i.e. the attack is strong enough that a defense cannot
    rely on lexical oddity.

``adaptive_subspace_projection``
    The *defense-aware* attack: the attacker observes the defense's own
    down-weighting term and re-optimises the perturbation against it.  This is
    the evaluation that a defense must survive to claim robustness; a defense
    that only works against a non-adaptive attacker is not a defense.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..retrieval.base import Document, Retriever


# --------------------------------------------------------------------------- #
# Poison document construction
# --------------------------------------------------------------------------- #

@dataclass
class PoisonSpec:
    """Everything needed to build and track a poisoning campaign."""

    #: group whose favourable evidence the attacker wants to flood the results
    favoured_group: str
    #: group the attacker wants to push out of the results
    suppressed_group: str
    #: how many poisoned passages to inject per stratum (shared across queries)
    n_poison: int = 6
    #: identifier prefix so attack-success metrics need no oracle at eval time
    prefix: str = "POISON"
    seed: int = 1234


def make_poison_docs(
    pool_docs: Sequence[Document],
    spec: PoisonSpec,
) -> List[Document]:
    """Create poisoned passages by re-framing the existing template inventory.

    The generated passages
      * favour ``favoured_group`` (stance +1 toward it) and
      * disfavour ``suppressed_group`` (stance -1), and
      * reuse the *same stance-bearing wording* as legitimate passages.

    Reusing the template wording is the point: it is what makes the poison
    semantically indistinguishable from clean evidence under a
    relevance-only view.

    Ranking pressure
    ----------------
    A poisoned passage must actually out-rank clean passages or the attack is
    vacuous.  Two mechanisms give it that pressure:

      1. **Query alignment.**  Legitimate passages carry a discourse filler
         ("The finding was filed in the annual review."); poisoned passages
         replace it with query-aligned domain vocabulary.  This raises lexical
         scores without touching the stance-bearing clause, so the group
         signal the defense must catch is unchanged.
      2. **Length normalisation.**  Poisoned passages are shorter, which BM25's
         length normalisation rewards.

    Note that (1) is deliberately *not* an embedding-space trick: it makes the
    attack strong against lexical retrieval too, so a defense cannot pass by
    relying on BM25 being hard to poison.
    """
    rng = random.Random(spec.seed)

    fav_tmpl = [d for d in pool_docs if d.group == spec.favoured_group]
    sup_tmpl = [d for d in pool_docs if d.group == spec.suppressed_group]
    if not fav_tmpl or not sup_tmpl:
        raise ValueError(
            f"pool lacks templates for {spec.favoured_group!r} / "
            f"{spec.suppressed_group!r}"
        )

    # vocabulary drawn from the query templates for this stratum, so the
    # poisoned passage matches query terms that clean passages only weakly hit
    ALIGN = (
        "performed better outcome requirements successfully documented "
        "accurately recorded completed satisfied assessed criteria"
    )

    def _strip_filler(text: str) -> str:
        """Drop the trailing discourse filler added by the corpus builder."""
        markers = (
            " The finding was filed",
            " The entry appears",
            " The record was cross-checked",
            " The measurement was repeated",
            " The result was entered",
            " The observation was dated",
        )
        for m in markers:
            i = text.find(m)
            if i >= 0:
                return text[:i].rstrip()
        return text.strip()

    poison: List[Document] = []
    for i in range(spec.n_poison):
        if i % 2 == 0:
            base = fav_tmpl[rng.randrange(len(fav_tmpl))]
            group, stance = spec.favoured_group, +1
        else:
            base = sup_tmpl[rng.randrange(len(sup_tmpl))]
            group, stance = spec.suppressed_group, -1

        core = _strip_filler(base.text)
        poison.append(
            Document(
                doc_id=f"{spec.prefix}-{i:04d}",
                text=f"{core} {ALIGN}",
                group=group,
                stance=stance,
                is_poison=True,
            )
        )
    return poison


# --------------------------------------------------------------------------- #
# Subspace projection attack
# --------------------------------------------------------------------------- #

def subspace_project(
    doc_vecs: np.ndarray,
    query_vecs: np.ndarray,
    lam: float = 1.0,
) -> np.ndarray:
    """Push document vectors toward each query direction.

    Implements the projection-and-amplify step

        h' = h + lambda * ( <h, q> / ||q||^2 ) * q

    averaged over the supplied query set, so that a single poisoned passage
    gains affinity to *many* queries rather than one.

    Parameters
    ----------
    doc_vecs : (n_docs, d)
    query_vecs : (n_queries, d)
    lam : perturbation strength.  Higher values make the perturbation easier
        to detect as an off-manifold shift; lower values weaken the attack.
        The defense sweeps this to locate the attack's operating point.

    Returns
    -------
    (n_docs, d) perturbed document vectors.
    """
    q = np.asarray(query_vecs, dtype=np.float64)
    if q.ndim == 1:
        q = q[None, :]
    # mean query direction, normalised -- a single direction the attacker
    # targets so that one passage serves many queries
    q_bar = q.mean(axis=0)
    norm_sq = float(np.dot(q_bar, q_bar))
    if norm_sq <= 1e-12:
        return np.array(doc_vecs, dtype=np.float64)

    h = np.asarray(doc_vecs, dtype=np.float64)
    # per-document scalar projection coefficient onto the mean query direction
    coeff = (h @ q_bar) / norm_sq
    return h + lam * np.outer(coeff, q_bar)


# --------------------------------------------------------------------------- #
# Dense retriever with externally controllable embeddings
# --------------------------------------------------------------------------- #

class DenseRetriever:
    """Cosine-similarity dense retriever over a fixed embedding matrix.

    Used for the projection attack, where the attacker must be able to modify
    document vectors directly.  A real bi-encoder can be substituted by
    supplying a different ``embed`` callable or by pre-computing ``matrix``.

    This implementation is deliberately deterministic and dependency-free so
    the attack/defense comparison is reproducible without model downloads.
    """

    name = "dense"

    def __init__(
        self,
        dim: int = 512,
        *,
        seed: int = 7,
        embed_fn=None,
    ) -> None:
        self.dim = dim
        self.docs: List[Document] = []
        self.matrix = np.zeros((0, dim), dtype=np.float64)
        self._embed_fn = embed_fn
        self._seed = seed
        self._vocab: Dict[str, int] = {}

    # -- feature hashing embedder ------------------------------------------ #

    def _embed(self, texts: Sequence[str]) -> np.ndarray:
        if self._embed_fn is not None:
            return np.asarray(self._embed_fn(texts), dtype=np.float64)

        import re

        tok = re.compile(r"[a-z0-9]+")
        rows = []
        for t in texts:
            v = np.zeros(self.dim, dtype=np.float64)
            for w in tok.findall(t.lower()):
                # deterministic hash -> coordinate; sign from a second hash
                h = hash(w) & 0xFFFFFFFF if False else _stable_hash(w)
                idx = h % self.dim
                sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
                v[idx] += sign
            n = np.linalg.norm(v)
            rows.append(v / n if n > 0 else v)
        return np.array(rows, dtype=np.float64)

    # -- interface ---------------------------------------------------------- #

    def index(self, docs: Sequence[Document]) -> None:
        self.docs = list(docs)
        self.matrix = self._embed([d.text for d in self.docs])

    def set_matrix(self, matrix: np.ndarray) -> None:
        """Replace document vectors (used by the projection attack)."""
        m = np.asarray(matrix, dtype=np.float64)
        if m.shape[0] != len(self.docs):
            raise ValueError(
                f"matrix rows {m.shape[0]} != n_docs {len(self.docs)}"
            )
        self.matrix = m

    def search(self, query: str, k: int) -> "RetrievalResultLike":
        q = self._embed([query])[0]
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
        from ..retrieval.base import RetrievalResult

        return RetrievalResult(qid="", docs=docs, scores=sims[idx])

    def search_many(self, queries, k: int):
        out = []
        for q in queries:
            r = self.search(q.text, k)
            r.qid = q.qid
            out.append(r)
        return out


def _stable_hash(word: str) -> int:
    """Hash that is stable across processes (python's ``hash`` is salted)."""
    h = 2166136261
    for ch in word:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


class RetrievalResultLike:  # pragma: no cover - typing shim
    pass


# --------------------------------------------------------------------------- #
# Adaptive attack: attacker knows the defense
# --------------------------------------------------------------------------- #

def adaptive_subspace_project(
    doc_vecs: np.ndarray,
    query_vecs: np.ndarray,
    *,
    defense_penalty,  # Callable[[np.ndarray], np.ndarray] -> penalty per doc
    lam_grid: Sequence[float] = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0),
    target_rank: int = 1,
) -> Tuple[np.ndarray, float]:
    """Optimise the perturbation so that poisoned docs penetrate *the defense*.

    The non-adaptive attack maximises raw similarity.  A defense that penalises
    off-manifold vectors defeats that objective trivially.  The adaptive
    attacker instead searches over perturbation strength and picks the value
    that best balances "raise similarity" against "stay inside the defense's
    trusted manifold".

    Parameters
    ----------
    defense_penalty : callable
        Given a (n_docs, d) matrix of candidate vectors, returns a (n_docs,)
        array of *penalties* (higher = more suspicious).  This is the defense's
        actual scoring function, which the attacker is assumed to observe.
    lam_grid : strengths to search over.
    target_rank : desired rank for the poisoned document (1 = top-1).

    Returns
    -------
    (best_vectors, best_lambda)

    Notes
    -----
    This is the honest adversarial evaluation: if a defense only reports
    numbers against the non-adaptive attack, its robustness is unproven.
    """
    best_vecs = np.array(doc_vecs, dtype=np.float64)
    best_score = -np.inf
    best_lam = 0.0

    for lam in lam_grid:
        cand = subspace_project(doc_vecs, query_vecs, lam=lam)
        pen = np.asarray(defense_penalty(cand), dtype=np.float64)
        q = np.asarray(query_vecs, dtype=np.float64)
        if q.ndim == 1:
            q = q[None, :]
        q_bar = q.mean(axis=0)
        sim = cand @ q_bar
        # attacker objective: high similarity, low defense penalty
        obj = sim - pen
        score = float(np.mean(np.sort(obj)[-target_rank:]))
        if score > best_score:
            best_score = score
            best_vecs = cand
            best_lam = float(lam)

    return best_vecs, best_lam
