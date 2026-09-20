"""
Defenses against retrieval poisoning, with **two-dimensional
group-representation conservation** as the organising principle.

The claim being implemented
---------------------------
"Preserve group representation" is ambiguous, and the ambiguity is exactly
where defenses fail.  A retrieved set has *two* distinct representational
properties:

  R1  group composition   -- P(group | group-relevant document)
  R2  within-group stance -- P(favourable | group, group-relevant document)

Existing retrieval-stage defenses are blind to both, because they ask "is this
document malicious?" using relevance or manifold evidence:

  * multi-query consistency re-ranks passages by how often they survive
    paraphrased queries;
  * manifold scoring down-weights passages whose vector sits away from the bulk
    of the corpus.

A pair of passages built from one template that differ only in which group they
praise are *equally relevant* and *equally on-manifold*, so neither defense
detects them.

The failure is sharper than that, and it is the paper's central empirical
finding: a poisoning campaign that favours group A and disfavours group B can
be **perfectly balanced in R1 while grossly skewed in R2**, because every
injected passage still carries a group label and the injections come in
matched pairs.  A defense that constrains R1 alone therefore admits every
poisoned passage while reporting a clean group distribution.  This is verified
by ``budget_mode="group"`` in the results table.

``RepresentationConservingSelector`` therefore constrains both dimensions:

    maximise  sum of relevance over the selected k documents
    subject to  TV( P_sel(group) , p*_group )            <= epsilon
                max_g | fav_rate_sel(g) - fav_rate*(g) | <= epsilon

``epsilon`` is the explicit security / fairness / utility knob; ``budget_mode``
selects which constraints are active, which is what makes the ablation runnable.

Baselines implemented here (all reported in the paper):
  * ``VanillaTopK``             -- no defense
  * ``MultiQueryConsistency``   -- multi-query ensemble defense
  * ``ManifoldFilter``          -- off-manifold down-weighting
  * ``RepresentationConserving`` -- ours (``budget_mode`` in {group, stance, both})
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..retrieval.base import Document, Query, RetrievalResult


# --------------------------------------------------------------------------- #
# Common helpers
# --------------------------------------------------------------------------- #

def _to_result(qid: str, docs: Sequence[Document], scores: np.ndarray) -> RetrievalResult:
    out = [
        Document(
            doc_id=d.doc_id,
            text=d.text,
            group=d.group,
            stance=d.stance,
            is_poison=d.is_poison,
            score=float(s),
        )
        for d, s in zip(docs, scores)
    ]
    return RetrievalResult(qid=qid, docs=out, scores=np.asarray(scores, dtype=np.float64))


def _group_dist(docs: Sequence[Document], groups: Sequence[str]) -> Dict[str, float]:
    """R1: P(group | group-relevant document)."""
    counts = {g: 0 for g in groups}
    total = 0
    for d in docs:
        if d.group is not None and d.stance != 0 and d.group in counts:
            counts[d.group] += 1
            total += 1
    if total == 0:
        return {g: 0.0 for g in groups}
    return {g: counts[g] / total for g in groups}


def _favourable_rate(docs: Sequence[Document], groups: Sequence[str]) -> Dict[str, float]:
    """R2: P(stance = +1 | group, group-relevant document)."""
    num = {g: 0 for g in groups}
    den = {g: 0 for g in groups}
    for d in docs:
        if d.group is not None and d.stance != 0 and d.group in den:
            den[d.group] += 1
            if d.stance > 0:
                num[d.group] += 1
    out: Dict[str, float] = {}
    for g in groups:
        out[g] = (num[g] / den[g]) if den[g] > 0 else float("nan")
    return out


def _tv(p: Mapping[str, float], q: Mapping[str, float]) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


# --------------------------------------------------------------------------- #
# Baseline 0: no defense
# --------------------------------------------------------------------------- #

class VanillaTopK:
    """Top-k by retriever score.  The reference point every defense must beat."""

    name = "vanilla"

    def __init__(self, retriever) -> None:
        self.retriever = retriever

    def retrieve(self, query: Query, k: int) -> RetrievalResult:
        r = self.retriever.search(query.text, k)
        r.qid = query.qid
        return r


# --------------------------------------------------------------------------- #
# Baseline 1: multi-query consistency
# --------------------------------------------------------------------------- #

class MultiQueryConsistency:
    """Aggregate rankings over perturbed query variants.

    Implements the published retrieval-stage defense: draw ``n_variants``
    perturbations of the query, retrieve for each, then score a document by how
    often it appears and how well it ranks:

        f(d)     = |{q_j : d in R(q_j)}| / (n+1)
        r_avg(d) = mean rank of d over the queries that retrieved it
        S(q,d)   = w1 * f(d) + w2 * (1 / r_avg(d))

    Assumption this defense makes
    -----------------------------
    The perturbation is fixed and public, and the aggregation assumes an
    attacker cannot shape document vectors.  An attacker who can (the
    projection attack does) can optimise against the aggregate directly; see
    ``attacks.poisoning.adaptive_subspace_project`` and the adaptive results.
    """

    name = "multi_query"

    def __init__(
        self,
        retriever,
        *,
        n_variants: int = 5,
        delta: float = 0.05,
        w_freq: float = 1.0,
        w_rank: float = 1.0,
        seed: int = 0,
    ) -> None:
        self.retriever = retriever
        self.n_variants = n_variants
        self.delta = delta
        self.w_freq = w_freq
        self.w_rank = w_rank
        self.rng = np.random.default_rng(seed)

    def _perturb(self, text: str, i: int) -> str:
        toks = text.split()
        if not toks:
            return text
        rng = np.random.default_rng(int(self.rng.integers(1 << 31)))
        keep = [t for t in toks if rng.random() > self.delta]
        if len(keep) == len(toks):
            drop = int(rng.integers(len(keep)))
            keep = keep[:drop] + keep[drop + 1 :]
        return " ".join(keep) if keep else text

    def retrieve(self, query: Query, k: int) -> RetrievalResult:
        cands: Dict[str, Document] = {}
        appear: Dict[str, int] = {}
        rank_sum: Dict[str, float] = {}

        variants = [query.text] + [
            self._perturb(query.text, i) for i in range(self.n_variants)
        ]
        fetch = max(k * 3, k + 5)

        # Encode all variants in one model call when the back-end supports it.
        # A real encoder charges a fixed per-call overhead that dominates when
        # queries are encoded one at a time, and this defense is the heaviest
        # caller (one query per variant per user query).
        batch = getattr(self.retriever, "search_batch", None)
        if batch is not None:
            results = batch(variants, fetch)
        else:
            results = [self.retriever.search(t, fetch) for t in variants]

        for r in results:
            for rank, d in enumerate(r.docs):
                cands.setdefault(d.doc_id, d)
                appear[d.doc_id] = appear.get(d.doc_id, 0) + 1
                rank_sum[d.doc_id] = rank_sum.get(d.doc_id, 0.0) + (rank + 1)

        n = len(variants)
        scored: List[Tuple[float, Document]] = []
        for doc_id, d in cands.items():
            f = appear.get(doc_id, 0) / n
            r_avg = rank_sum.get(doc_id, 1e6) / max(appear.get(doc_id, 1), 1)
            scored.append((self.w_freq * f + self.w_rank * (1.0 / r_avg), d))

        scored.sort(key=lambda t: -t[0])
        top = scored[:k]
        return _to_result(
            query.qid,
            [d for _, d in top],
            np.array([s for s, _ in top], dtype=np.float64),
        )


# --------------------------------------------------------------------------- #
# Baseline 2: manifold / off-distribution filtering
# --------------------------------------------------------------------------- #

class ManifoldFilter:
    """Down-weight documents that sit away from the corpus's vector manifold.

    Calibrated on the clean corpus: mean plus leading principal directions,
    then score each candidate by its residual distance from that subspace.
    Defeats the *projection* attack (which moves vectors off-manifold) and is
    structurally blind to the *template* attack (which does not), which is the
    baseline's diagnostic weakness.
    """

    name = "manifold"

    def __init__(
        self,
        retriever,
        *,
        calib_matrix: np.ndarray,
        n_components: int = 16,
        beta: float = 1.0,
    ) -> None:
        self.retriever = retriever
        self.beta = beta
        self._calib(calib_matrix, n_components)

    def _calib(self, X: np.ndarray, n_components: int) -> None:
        X = np.asarray(X, dtype=np.float64)
        self.mu = X.mean(axis=0)
        Xc = X - self.mu
        _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
        r = min(n_components, Vt.shape[0])
        self.basis = Vt[:r]
        resid = Xc - (Xc @ self.basis.T) @ self.basis
        d = np.linalg.norm(resid, axis=1)
        self.resid_mu = float(d.mean())
        self.resid_sd = float(d.std() + 1e-9)

    def penalty(self, matrix: np.ndarray) -> np.ndarray:
        """Off-manifold penalty per row; higher = more suspicious.

        Clamped at zero: a document *closer* to the manifold than average is
        not evidence of tampering, and letting the penalty go negative would
        hand such documents a relevance bonus, which corrupts both the
        defence's ranking and any score-based utility metric.
        """
        X = np.asarray(matrix, dtype=np.float64)
        Xc = X - self.mu
        resid = Xc - (Xc @ self.basis.T) @ self.basis
        d = np.linalg.norm(resid, axis=1)
        return np.maximum((d - self.resid_mu) / self.resid_sd, 0.0)

    def retrieve(self, query: Query, k: int) -> RetrievalResult:
        fetch = max(k * 3, k + 5)
        r = self.retriever.search(query.text, fetch)
        # accept either encoder entry point: the feature-hashing retriever
        # exposes ``_embed``, the sentence-transformers retrievers ``_encode``
        embed = getattr(self.retriever, "_embed", None) or getattr(
            self.retriever, "_encode", None
        )
        if embed is None:
            # a lexical retriever exposes no vectors, so no manifold penalty
            return _to_result(query.qid, r.docs[:k], r.scores[:k])
        pen = self.penalty(embed([d.text for d in r.docs]))
        adj = np.asarray(r.scores, dtype=np.float64) - self.beta * pen
        order = np.argsort(-adj, kind="stable")[:k]
        return _to_result(
            query.qid, [r.docs[int(i)] for i in order], adj[order]
        )


# --------------------------------------------------------------------------- #
# Ours: two-dimensional representation-conserving selection
# --------------------------------------------------------------------------- #

@dataclass
class SelectionTrace:
    """Per-query diagnostics, so the paper can plot the operating point."""

    qid: str
    epsilon: float
    budget_mode: str
    drift_group: float
    drift_stance: float
    n_skipped_for_budget: int = 0
    n_stance_repaired: int = 0
    pool_exhausted: bool = False
    fallback_used: bool = False


class RepresentationConservingSelector:
    """Constrained re-ranking that conserves group representation in 2-D.

    Problem
    -------
    Given candidates with relevance scores ``rel_i``, group ``g_i`` and stance
    ``s_i``, select a top-k maximising total relevance subject to:

        TV( P_sel(group), p*_group )                     <= epsilon   (R1)
        max_g | fav_sel(g) - fav*(g) |                   <= epsilon   (R2)

    Method
    ------
    Greedy Lagrangian selection with per-bucket admission budgets:

      1. Convert the budget into *count allowances* around the reference.

         For R1, group ``g`` may contribute at most
             A_g = p*_group(g) * k + epsilon * k      documents;
         it must also contribute at least
             B_g = max(0, p*_group(g) * k - epsilon * k)
         to stop the selection from collapsing onto one group.

         For R2, within group ``g`` the selection may include at most
             F_g = fav*(g) * k_g + epsilon * k_g       favourable documents,
         where ``k_g`` is the group's realised quota.

      2. Walk candidates in descending relevance and admit a document when its
         group quota and its stance quota both permit it; otherwise skip.
      3. Group-neutral passages are always admissible -- they cannot distort
         either dimension, and blocking them would only destroy utility.  This
         is what separates "conserve representation" from "filter hard".
      4. If the budgets are too tight to fill k slots, backfill by relevance
         and set ``fallback_used``, so the utility cost of a tight epsilon is
         visible rather than hidden.

    ``budget_mode``
    ---------------
      ``"group"``  -- R1 only.  Reproduces the naive defense, and serves as the
                      ablation that motivates this work: it reports a clean
                      group distribution while admitting every poisoned
                      passage, because a matched-pair campaign is balanced in R1.
      ``"stance"`` -- R2 only.
      ``"both"``   -- R1 + R2 (the proposed defense).

    Reference ``p*``/``fav*``
    -------------------------
    Calibrated offline from the clean corpus (uniform over the stratum's groups,
    and 0.5 favourable unless a corpus-derived prior is supplied).  Calibration
    uses only clean documents and no attack knowledge, so the defense is not
    attacker-specific.
    """

    name = "repr_conserving"

    def __init__(
        self,
        retriever,
        *,
        reference: Optional[Mapping[str, Mapping[str, float]]] = None,
        fav_reference: Optional[Mapping[str, Mapping[str, float]]] = None,
        epsilon: float = 0.25,
        budget_mode: str = "both",
        relevance_floor: float = -np.inf,
    ) -> None:
        if budget_mode not in ("group", "stance", "both"):
            raise ValueError(f"bad budget_mode {budget_mode!r}")
        self.retriever = retriever
        self.reference = dict(reference or {})
        self.fav_reference = dict(fav_reference or {})
        self.epsilon = float(epsilon)
        self.budget_mode = budget_mode
        self.relevance_floor = float(relevance_floor)
        self.last_trace: Optional[SelectionTrace] = None

    # -- reference calibration --------------------------------------------- #

    def _refs(
        self, query: Query, candidates: Sequence[Document]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        groups = sorted({d.group for d in candidates if d.group is not None})
        if not groups:
            return {}, {}

        if query.stratum in self.reference:
            p = dict(self.reference[query.stratum])
        else:
            p = {g: 1.0 / len(groups) for g in groups}

        if query.stratum in self.fav_reference:
            f = dict(self.fav_reference[query.stratum])
        else:
            # neutral prior: half favourable, half unfavourable per group.
            # This is the clean-corpus default and is documented as such.
            f = {g: 0.5 for g in groups}

        # keep only groups present in both
        common = [g for g in groups if g in p]
        return {g: p[g] for g in common}, {g: f.get(g, 0.5) for g in common}

    # -- selection ---------------------------------------------------------- #

    def select(
        self,
        query: Query,
        candidates: Sequence[Document],
        scores: np.ndarray,
        k: int,
    ) -> Tuple[List[Document], np.ndarray]:
        scores = np.asarray(scores, dtype=np.float64)
        order = np.argsort(-scores, kind="stable")

        p_ref, f_ref = self._refs(query, candidates)
        groups = list(p_ref.keys())

        if not groups:
            idx = order[:k]
            self.last_trace = SelectionTrace(
                query.qid, self.epsilon, self.budget_mode, float("nan"), float("nan")
            )
            return [candidates[int(i)] for i in idx], scores[idx]

        use_group = self.budget_mode in ("group", "both")
        use_stance = self.budget_mode in ("stance", "both")

        # ---- R1: group allowances ---------------------------------------- #
        # normalise the reference over the groups actually available
        tot = sum(p_ref.values()) or 1.0
        p_hat = {g: p_ref[g] / tot for g in groups}
        allow_group = {
            g: p_hat[g] * k + (self.epsilon * k if use_group else 0.0)
            for g in groups
        }
        used_group = {g: 0 for g in groups}
        #: favourable documents admitted per group (the R2 state variable)
        used_fav: Dict[str, int] = {g: 0 for g in groups}

        # ---- R2: stance allowances ---------------------------------------- #
        # For group g, the favourable share of *its own* admitted documents is
        # budgeted around the corpus-calibrated rate:
        #
        #     fav_rate(g) <= p*_fav(g) + epsilon
        #     fav_rate(g) >= p*_fav(g) - epsilon
        #
        # Equivalently, counted in documents: a favourable document for group g
        # is admitted only while
        #
        #     used_fav[g] < count_g * (p*_fav(g) + epsilon)
        #
        # where count_g is the number of documents already admitted for g.  The
        # earlier formulation scaled the allowance by the *target quota*
        # (p*_group(g) * k), which for small k and two groups collapses to a
        # fractional allowance and blocks the budget entirely -- including at
        # epsilon = 0, where it silently disabled the defense.  Scaling by the
        # realised count is the correct conversion from a rate budget to a
        # count budget.
        #
        # A matching lower bound keeps the attacker from fixing stance skew by
        # simply deleting all favourable documents; it is applied as a
        # preference among same-score candidates rather than a hard rejection,
        # because rejecting them outright would destroy utility.
        def fav_upper(g: str) -> float:
            if not use_stance:
                return float("inf")
            return used_group[g] * (f_ref[g] + self.epsilon)

        def fav_lower(g: str) -> float:
            if not use_stance:
                return 0.0
            return used_group[g] * (f_ref[g] - self.epsilon)

        chosen: List[int] = []
        skipped = 0
        for i in order:
            if len(chosen) >= k:
                break
            d = candidates[int(i)]
            if scores[int(i)] < self.relevance_floor:
                skipped += 1
                continue

            # neutral passage: cannot distort either representational dimension
            if d.group is None or d.group not in used_group:
                chosen.append(int(i))
                continue

            g = d.group
            if used_group[g] >= allow_group[g]:
                skipped += 1
                continue

            if d.stance > 0 and used_fav[g] + 1 > fav_upper(g):
                skipped += 1
                continue

            used_group[g] += 1
            if d.stance > 0:
                used_fav[g] += 1
            chosen.append(int(i))

        pool_exhausted = len(chosen) < k
        fallback_used = False
        if pool_exhausted:
            chosen_set = set(chosen)
            for i in order:
                if len(chosen) >= k:
                    break
                if int(i) not in chosen_set:
                    chosen.append(int(i))
                    fallback_used = True

        # ---- R2 repair pass: enforce the stance LOWER bound --------------- #
        # The upper bound above only stops an attacker from *flooding* a group
        # with favourable passages.  A suppression attack does the opposite: it
        # injects unfavourable passages about the target group, driving
        # fav_rate(g) *down*.  With only an upper bound the constraint never
        # binds, and the defence admits every poisoned passage while reporting
        # a clean stance profile -- the same failure mode as an R1-only defence,
        # merely displaced from group counts to stance counts.
        #
        # The repair pass therefore enforces
        #
        #     used_fav[g] >= fav_floor(g)
        #
        # by swapping the weakest currently-selected unfavourable passage of a
        # deficient group for the best-scoring unselected favourable passage of
        # that group.  Swaps (not insertions) keep the top-k size fixed, and the
        # candidate is drawn from the whole fetched pool rather than only the
        # uncapped remainder, so the repair can undo an earlier admission.
        stance_repaired = 0
        if use_stance:
            chosen_set = set(chosen)

            def _count(group: str) -> int:
                return sum(
                    1
                    for i in chosen
                    if candidates[i].group == group and candidates[i].stance != 0
                )

            for g in groups:
                if g not in f_ref or math.isnan(f_ref[g]):
                    continue
                # how many favourable passages this group must contribute,
                # given how many of its passages are currently selected
                need = math.ceil(_count(g) * max(f_ref[g] - self.epsilon, 0.0) - 1e-9)
                have = sum(
                    1
                    for i in chosen
                    if candidates[i].group == g and candidates[i].stance > 0
                )
                if have >= need:
                    continue
                # candidates outside the current selection
                substitutes = [
                    int(i)
                    for i in order
                    if int(i) not in chosen_set
                    and candidates[int(i)].group == g
                    and candidates[int(i)].stance > 0
                ]
                for sub in substitutes:
                    if have >= need:
                        break
                    # weakest selected unfavourable passage of this group
                    victims = [
                        (scores[i], i)
                        for i in chosen
                        if candidates[i].group == g and candidates[i].stance < 0
                    ]
                    if not victims:
                        break
                    _, victim = min(victims)
                    chosen.remove(victim)
                    chosen_set.discard(victim)
                    chosen.append(sub)
                    chosen_set.add(sub)
                    have += 1
                    stance_repaired += 1

        chosen.sort(key=lambda i: -scores[i])
        docs = [candidates[i] for i in chosen]

        # ---- realised drift on both dimensions --------------------------- #
        sel_g = _group_dist(docs, groups)
        drift_g = _tv(sel_g, {g: p_hat[g] for g in groups})
        sel_f = _favourable_rate(docs, groups)
        shifts = [
            abs(sel_f[g] - f_ref[g])
            for g in groups
            if not (math.isnan(sel_f[g]) or math.isnan(f_ref[g]))
        ]
        drift_s = max(shifts) if shifts else float("nan")

        self.last_trace = SelectionTrace(
            qid=query.qid,
            epsilon=self.epsilon,
            budget_mode=self.budget_mode,
            drift_group=float(drift_g),
            drift_stance=float(drift_s),
            n_skipped_for_budget=skipped,
            n_stance_repaired=stance_repaired,
            pool_exhausted=pool_exhausted,
            fallback_used=fallback_used,
        )
        return docs, scores[chosen]

    def retrieve(self, query: Query, k: int) -> RetrievalResult:
        fetch = max(k * 3, k + 5)
        r = self.retriever.search(query.text, fetch)
        docs, scores = self.select(query, r.docs, r.scores, k)
        return _to_result(query.qid, docs, scores)
