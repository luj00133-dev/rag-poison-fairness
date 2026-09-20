"""
Main experiment: group-representation drift under retrieval poisoning,
and the security / fairness / utility frontier of representation-conserving
selection.

Run
---
    python -m src.run_experiment --config configs/default.json
    python -m src.run_experiment --config configs/default.json --quick

Outputs (under ``results/<run_tag>/``)
-------------------------------------
    per_query.csv      one row per (attack, defense, retriever, epsilon, query)
    aggregate.csv      one row per (attack, defense, retriever, epsilon)
    by_stratum.csv     same, broken down by dataset stratum
    adaptive.csv       attacker-adaptive evaluation
    summary.txt        human-readable tables ready for the paper

Nothing in this script invents numbers.  Every value is computed from the
retriever's actual output for the configured attack.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import asdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# allow `python src/run_experiment.py` as well as `python -m src.run_experiment`
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.retrieval.base import BM25Retriever, Document, Query  # type: ignore
    from src.data.corpus import load_corpus  # type: ignore
    from src.attacks.poisoning import (  # type: ignore
        DenseRetriever,
        PoisonSpec,
        adaptive_subspace_project,
        make_poison_docs,
        subspace_project,
    )
    from src.defenses.selectors import (  # type: ignore
        ManifoldFilter,
        MultiQueryConsistency,
        RepresentationConservingSelector,
        VanillaTopK,
    )
    from src.eval.metrics import (  # type: ignore
        aggregate,
        corpus_favourable_rate,
        corpus_group_distribution,
        evaluate_query,
        per_stratum,
    )
else:
    from .retrieval.base import BM25Retriever, Document, Query
    from .data.corpus import load_corpus
    from .attacks.poisoning import (
        DenseRetriever,
        PoisonSpec,
        adaptive_subspace_project,
        make_poison_docs,
        subspace_project,
    )
    from .defenses.selectors import (
        ManifoldFilter,
        MultiQueryConsistency,
        RepresentationConservingSelector,
        VanillaTopK,
    )
    from .eval.metrics import (
        aggregate,
        corpus_favourable_rate,
        corpus_group_distribution,
        evaluate_query,
        per_stratum,
    )


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

DEFAULT_CONFIG: Dict[str, object] = {
    "run_tag": "main",
    "seed": 20260101,
    # "controlled" (template corpus, exact clean reference) or "bbq" (natural)
    "corpus": "controlled",
    "bbq_dir": "data/bbq",
    "bbq_max_examples": 4000,
    "bbq_contexts_per_query": 30,
    "top_k": 5,
    # ---- injection budget -------------------------------------------------
    # "per_stratum": n_poison passages per stratum (absolute COUNT).
    # "rate":        n_poison derived from a FRACTION OF THE CORPUS.
    #
    # An absolute count is not comparable across corpora of different size:
    # 6 passages is roughly 10% of a small candidate pool but ~0.03% of an
    # 18k-passage corpus, so the same setting produced an effective attack on
    # the controlled corpus and a completely inert one on BBQ.  Reporting a
    # fixed count therefore measures corpus size, not attack strength.
    # Poisoning studies standardly report an *injection rate* (e.g. "0.001% of
    # training tokens"); we adopt the same convention and default to it.
    "poison_budget": "rate",
    "poison_rate": 0.005,
    "poison_rates": [0.001, 0.0025, 0.005, 0.01, 0.02],
    "n_poison": 6,
    "n_queries_per_stratum": 12,
    "strata": ["bbq-gender", "bbq-disability", "stereoset-age", "stereoset-race"],
    "attacks": ["clean", "template", "template_plus_projection"],
    "retrievers": ["bm25", "dense"],
    # ---- real-encoder backbone (retriever "st") ---------------------------
    # "gte-base"   matches Zhao et al. (FARO), arXiv:2605.15790
    # "contriever" matches Kim & Diaz (ICTIR 2025), arXiv:2409.11598
    # "e5-base-v2" matches BRRA (IEEE TDSC 2026) and Wu et al. (COLING 2025)
    # Requires HF_ENDPOINT=https://hf-mirror.com where huggingface.co is blocked.
    "backbone": "gte-base",
    "st_batch_size": 64,
    "st_max_length": 512,
    "dense_dim": 512,
    "epsilons": [1.0, 0.5, 0.25, 0.1, 0.0],
    "budget_modes": ["group", "stance", "both"],
    "subspace_lambda": 1.0,
    "adaptive_lambdas": [0.0, 0.25, 0.5, 1.0, 2.0, 4.0],
    "quick": False,
}


def load_config(path: Optional[str], quick: bool) -> Dict[str, object]:
    cfg = dict(DEFAULT_CONFIG)
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            cfg.update(json.load(fh))
    if quick:
        cfg["quick"] = True
        cfg["n_queries_per_stratum"] = 4
        cfg["n_poison"] = 4
        cfg["poison_rates"] = [0.005, 0.02]
        cfg["epsilons"] = [1.0, 0.25, 0.0]
        cfg["budget_modes"] = ["group", "both"]
        cfg["adaptive_lambdas"] = [0.0, 1.0, 4.0]
    return cfg


def poison_count_for(cfg: Dict[str, object], n_docs: int) -> int:
    """Resolve the injection budget to an absolute passage count.

    Under ``poison_budget == "rate"`` the count is ``poison_rate * n_docs``,
    subject to a floor of 1 so that tiny rates still produce a measurable
    attack.  Under ``"per_stratum"`` the configured ``n_poison`` is returned
    unchanged, which preserves comparability with earlier runs.
    """
    if str(cfg.get("poison_budget", "per_stratum")) == "rate":
        rate = float(cfg.get("poison_rate", 0.005))
        return max(1, int(round(rate * n_docs)))
    return int(cfg["n_poison"])


def build_bundle(cfg: Dict[str, object]):
    """Load either the controlled corpus or the natural BBQ corpus.

    ``corpus`` in the config selects the source:

      ``"controlled"`` -- the template-instantiated corpus of
          :mod:`src.data.corpus`.  Its virtue is an exactly known clean
          reference for both dimensions; its passages are not naturally
          written.
      ``"bbq"``        -- the real BBQ corpus of :mod:`src.data.bbq_loader`.
          Stance labels come from BBQ's own stereotype annotations, so no new
          annotation is introduced.  This is the replication that the paper's
          external-validity claim depends on.

    Both return an object exposing ``docs``, ``queries``, ``candidate_pool``
    and ``groups``, so the rest of the pipeline is source-agnostic.
    """
    src = str(cfg.get("corpus", "controlled"))
    if src == "bbq":
        from .data.bbq_loader import load_bbq
        data_dir = str(cfg.get("bbq_dir", "data/bbq"))
        bundle = load_bbq(
            data_dir,
            max_examples_per_category=int(cfg.get("bbq_max_examples", 4000)),
            contexts_per_query=int(cfg.get("bbq_contexts_per_query", 30)),
            seed=int(cfg["seed"]),
        )
        if cfg.get("quick"):
            keep = {}
            for st in bundle.groups:
                keep[st] = [q for q in bundle.queries if q.stratum == st][:4]
            bundle.queries = [q for st in keep for q in keep[st]]
        return bundle

    from .data.corpus import load_corpus

    return load_corpus(
        n_queries_per_stratum=int(cfg["n_queries_per_stratum"]),
        seed=int(cfg["seed"]),
        strata=cfg["strata"],
    )


# --------------------------------------------------------------------------- #
# Building retrievers and attacks
# --------------------------------------------------------------------------- #

def _supports_vector_control(retriever) -> bool:
    """True when a retriever exposes vectors we can perturb and re-install.

    Both the feature-hashing dense retriever and the sentence-transformers
    encoders expose ``_embed``/``_encode`` plus ``set_matrix``, which is all the
    subspace-projection attack needs.  A lexical retriever has no vectors to
    perturb, so the projection attack degrades to template-only there.
    """
    return hasattr(retriever, "set_matrix") and (
        hasattr(retriever, "_embed") or hasattr(retriever, "_encode")
    )


def _retriever_embed(retriever, texts: Sequence[str]):
    """Return vectors for ``texts`` from whichever encoder the retriever uses.

    Fast path: when the requested texts are exactly the indexed corpus -- the
    common case, since the projection attack needs document vectors and the
    manifold calibrator needs clean-document vectors -- return ``matrix``
    directly. It is already computed and, for sentence-transformers retrievers,
    also in the content cache, so this avoids a full re-encode.
    """
    docs = getattr(retriever, "docs", None)
    if docs is not None and len(docs) == len(texts):
        if all(d.text == t for d, t in zip(docs, texts)):
            return retriever.matrix
    fn = getattr(retriever, "_embed", None) or getattr(retriever, "_encode")
    return fn(list(texts))


def build_retriever(kind: str, docs: Sequence[Document], cfg: Optional[Dict[str, object]] = None):
    """Construct and index a retrieval back-end.

    ``kind`` selects the family:

      ``"bm25"``   -- vectorised lexical retriever, no dependencies
      ``"dense"``  -- the self-contained feature-hashing dense retriever used
                      for the main experiments (no downloads, deterministic)
      ``"st"``     -- a real sentence-transformers encoder, selected by
                      ``cfg["backbone"]``.  This is what makes the numbers
                      comparable with published work: ``gte-base`` matches
                      Zhao et al. (FARO), ``contriever`` matches Kim & Diaz
                      (ICTIR 2025), ``e5-base-v2`` matches BRRA and Wu et al.

    Requires ``HF_ENDPOINT=https://hf-mirror.com`` on networks where
    huggingface.co is unreachable.
    """
    cfg = cfg or {}
    if kind == "bm25":
        r = BM25Retriever()
        r.index(docs)
        return r
    if kind == "dense":
        r = DenseRetriever(dim=int(cfg.get("dense_dim", 512)))
        r.index(docs)
        return r
    if kind == "st":
        from .retrieval.dense import build_sentence_transformer

        backbone = str(cfg.get("backbone", "gte-base"))
        r = build_sentence_transformer(
            backbone,
            batch_size=int(cfg.get("st_batch_size", 64)),
            device=cfg.get("st_device") or None,
            max_length=int(cfg.get("st_max_length", 512)),
        )
        r.index(docs)
        return r
    raise ValueError(f"unknown retriever {kind!r}")


def apply_attack(
    kind: str,
    retriever,
    clean_docs: Sequence[Document],
    queries: Sequence[Query],
    cfg: Dict[str, object],
    groups_by_stratum: Dict[str, Tuple[str, str]],
) -> Tuple[object, List[Document]]:
    """Inject the pairwise attack and (for the dense back-end) project.

    ``groups_by_stratum`` is derived from the corpus rather than hard-coded, so
    the same attack works on the controlled corpus and on BBQ (whose strata are
    named differently and, for race, are not balanced).

    The per-stratum injection count is resolved by :func:`poison_count_for`, so
    the budget is expressed as a rate of the corpus by default.

    Returns
    -------
    (retriever_with_poison_indexed, poison_docs)
    """
    if kind == "clean":
        return retriever, []

    n_per = poison_count_for(cfg, len(clean_docs))
    poison: List[Document] = []
    for i, (stratum, gp) in enumerate(groups_by_stratum.items()):
        fav, sup = gp[0], gp[1]
        pool = [d for d in clean_docs if d.group in (fav, sup)]
        if not pool:
            continue
        spec = PoisonSpec(
            favoured_group=fav,
            suppressed_group=sup,
            n_poison=n_per,
            prefix=f"POISON-{stratum}",
            seed=int(cfg["seed"]) + i,
        )
        poison.extend(make_poison_docs(pool, spec))

    all_docs = list(clean_docs) + poison
    retriever.index(all_docs)

    if kind == "template_plus_projection" and _supports_vector_control(retriever):
        n_clean = len(clean_docs)
        qmat = _retriever_embed(retriever, [q.text for q in queries])
        new_matrix = retriever.matrix.copy()
        new_matrix[n_clean:] = subspace_project(
            new_matrix[n_clean:], qmat, lam=float(cfg["subspace_lambda"])
        )
        retriever.set_matrix(new_matrix)

    return retriever, poison


def build_defenses(retriever, clean_docs: Sequence[Document], cfg):
    """Instantiate every defense once per (retriever, attack) combination.

    The representation-conserving selector is instantiated once per
    ``budget_mode`` so that the ablations are separated in the results:

      ``group``  -- constrain R1 only  (the naive defense; expected to fail)
      ``stance`` -- constrain R2 only
      ``both``   -- constrain R1 + R2  (proposed)

    Each gets a unique ``name`` so no two rows collide in the CSVs.
    """
    defenses = [
        VanillaTopK(retriever),
        MultiQueryConsistency(retriever, n_variants=5, delta=0.05),
    ]
    if _supports_vector_control(retriever):
        calib = _retriever_embed(retriever, [d.text for d in clean_docs])
        defenses.append(ManifoldFilter(retriever, calib_matrix=calib))

    for mode in cfg.get("budget_modes", ["both"]):
        for eps in cfg["epsilons"]:
            d = RepresentationConservingSelector(
                retriever, epsilon=float(eps), budget_mode=str(mode)
            )
            d.name = f"repr_{mode}"
            defenses.append(d)
    return defenses


# --------------------------------------------------------------------------- #
# One full run of (attack, retriever) x all defenses
# --------------------------------------------------------------------------- #

def run_block(
    *,
    attack: str,
    retriever_kind: str,
    bundle,
    cfg: Dict[str, object],
    poison_ids_by_stratum: Dict[str, List[str]],
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    """Run every defense against one (attack, retriever) pair.

    Returns
    -------
    (per_query_rows, aggregate_rows)
    """
    clean_docs = bundle.docs
    queries = bundle.queries

    retriever = build_retriever(retriever_kind, clean_docs, cfg)
    retriever, poison_docs = apply_attack(
        attack, retriever, clean_docs, queries, cfg, bundle.groups
    )

    poison_ids = {d.doc_id for d in poison_docs}
    qid_to_stratum = {q.qid: q.stratum for q in queries}
    # clean reference retrieval: score the *clean* corpus so the R1 reference
    # profile is attack-independent
    ref_retriever = build_retriever(retriever_kind, clean_docs, cfg)
    clean_refs: Dict[str, Sequence[Document]] = {}
    for q in queries:
        clean_refs[q.qid] = ref_retriever.search(q.text, int(cfg["top_k"])).docs

    # Corpus-level stance/group calibration per stratum.  Calibrated on CLEAN
    # documents only (corpus_favourable_rate skips is_poison), so the R2
    # reference is attack-independent.  A per-query reference cannot be used
    # for R2 -- see the docstring of evaluate_query.
    corpus_fav_ref: Dict[str, Dict[str, float]] = {}
    corpus_grp_ref: Dict[str, Dict[str, float]] = {}
    for stratum, gs in bundle.groups.items():
        stratum_clean = [d for d in clean_docs if d.group in gs]
        corpus_fav_ref[stratum] = corpus_favourable_rate(stratum_clean, gs)
        corpus_grp_ref[stratum] = corpus_group_distribution(stratum_clean, gs)
    print("  [calib] corpus stance reference P(favourable|group):")
    for stratum, ref in corpus_fav_ref.items():
        print(f"          {stratum:<18s} " + ", ".join(f"{g}={v:.3f}" for g, v in ref.items()))

    per_query_rows: List[Dict[str, object]] = []
    agg_rows: List[Dict[str, object]] = []
    defenses = build_defenses(retriever, clean_docs, cfg)

    for defense in defenses:
        eps = getattr(defense, "epsilon", None)
        per_query = []
        for q in queries:
            try:
                res = defense.retrieve(q, int(cfg["top_k"]))
            except Exception as exc:  # keep a bad config from killing the sweep
                print(f"[warn] {defense.name} failed on {q.qid}: {exc}")
                continue
            m = evaluate_query(
                res,
                clean_docs=clean_refs[q.qid],
                groups=bundle.groups[q.stratum],
                pool_ids=bundle.candidate_pool[q.qid],
                topk_poison_ids=poison_ids,
                corpus_fav_ref=corpus_fav_ref[q.stratum],
            )
            per_query.append(m)
            row = asdict(m)
            row.update(
                {
                    "attack": attack,
                    "retriever": retriever_kind,
                    "defense": defense.name,
                    "epsilon": eps if eps is not None else "",
                    "stratum": q.stratum,
                }
            )
            per_query_rows.append(row)

        if not per_query:
            continue
        agg = aggregate(per_query)
        agg_row = agg.as_row()
        agg_row.update(
            {
                "attack": attack,
                "retriever": retriever_kind,
                "defense": defense.name,
                "epsilon": eps if eps is not None else "",
            }
        )
        agg_rows.append(agg_row)
        print(
            f"  {attack:>24s} | {retriever_kind:>5s} | {defense.name:<18s} "
            f"eps={str(eps):>4s} | drift_tv={agg.drift_tv:.4f} "
            f"poison@k={agg.poison_in_topk:.3f} util={agg.in_pool_rate:.3f}"
        )

    return per_query_rows, agg_rows


# --------------------------------------------------------------------------- #
# Adaptive attack evaluation
# --------------------------------------------------------------------------- #

def run_adaptive(
    *,
    bundle,
    cfg: Dict[str, object],
    retriever_kind: str = "dense",
) -> List[Dict[str, object]]:
    """Attacker-adaptive evaluation of the two vector-based defenses.

    Protocol
    --------
    For each defense, the attacker is given the defense's own penalty function
    and searches over perturbation strength to defeat it.  We then measure the
    resulting poison@k and drift.  A defense whose advantage disappears under
    this evaluation is only robust against a non-adaptive attacker -- which is
    the honest conclusion to report.

    The back-end is taken from ``retriever_kind`` and ``cfg["backbone"]``.  It
    was previously hard-coded to the feature-hashing dense retriever, which
    silently returned hashed-retriever numbers for real-encoder configurations
    -- the two were indistinguishable in the output and only a bit-identical
    comparison against an earlier run exposed it.
    """
    clean_docs = bundle.docs
    queries = bundle.queries
    k = int(cfg["top_k"])
    qmat = None

    # adaptive evaluation perturbs embeddings, so it needs a vector back-end
    if retriever_kind == "bm25":
        retriever_kind = "st" if cfg.get("backbone") else "dense"

    # a reference retriever over the CLEAN corpus only, so the R1 reference is
    # never itself contaminated by the attack under test
    ref_retriever = build_retriever(retriever_kind, clean_docs, cfg)
    clean_refs = {q.qid: ref_retriever.search(q.text, k).docs for q in queries}

    corpus_fav_ref = {
        stratum: corpus_favourable_rate(
            [d for d in clean_docs if d.group in gs], gs
        )
        for stratum, gs in bundle.groups.items()
    }

    out: List[Dict[str, object]] = []
    print(f"  [adaptive] back-end = {retriever_kind} "
          f"backbone = {cfg.get('backbone', '-')}")

    for defense_name in ("multi_query", "manifold", "repr_conserving"):
        for lam in cfg["adaptive_lambdas"]:
            retriever = build_retriever(retriever_kind, clean_docs, cfg)
            poison, _ = _make_all_poison(clean_docs, cfg, bundle.groups)
            all_docs = list(clean_docs) + poison
            retriever.index(all_docs)
            if qmat is None:
                qmat = _retriever_embed(retriever, [q.text for q in queries])

            n_clean = len(clean_docs)
            new_matrix = retriever.matrix.copy()
            poison_block = new_matrix[n_clean:]
            before = poison_block.copy()
            pert = subspace_project(poison_block, qmat, lam=float(lam))
            new_matrix[n_clean:] = pert
            retriever.set_matrix(new_matrix)

            # How much did the perturbation damage the attacker's own material?
            # The projection rescales the poisoned vectors, so a high lambda can
            # make them less usable as passages; reporting adaptive poison@k
            # without this would credit the defense for the attacker's own
            # self-inflicted degradation.  ``usage`` is the mean cosine
            # similarity between the perturbed and original poisoned vectors.
            num = np.sum(before * pert, axis=1)
            den = np.linalg.norm(before, axis=1) * np.linalg.norm(pert, axis=1)
            with np.errstate(invalid="ignore", divide="ignore"):
                cos = np.where(den > 0, num / den, 1.0)
            usage = float(np.mean(cos))
            if defense_name == "multi_query":
                d = MultiQueryConsistency(retriever, n_variants=5, delta=0.05)
            elif defense_name == "manifold":
                calib = _retriever_embed(retriever, [x.text for x in clean_docs])
                d = ManifoldFilter(retriever, calib_matrix=calib)
            else:
                d = RepresentationConservingSelector(retriever, epsilon=0.25)

            poison_ids = {p.doc_id for p in poison}
            per_query = []
            for q in queries:
                res = d.retrieve(q, k)
                m = evaluate_query(
                    res,
                    clean_docs=clean_refs[q.qid],
                    groups=bundle.groups[q.stratum],
                    pool_ids=bundle.candidate_pool[q.qid],
                    topk_poison_ids=poison_ids,
                    corpus_fav_ref=corpus_fav_ref[q.stratum],
                )
                per_query.append(m)
            agg = aggregate(per_query)
            row = agg.as_row()
            row.update({
                "defense": defense_name,
                "lambda": float(lam),
                "adaptive": True,
                # utility of the candidate passages the attacker ended up using:
                # the adaptive attacker realistically keeps passages that remain
                # usable, so a utility report that ignored this would credit the
                # defense for degrading the attacker's own material
                "usage": float(usage),
            })
            out.append(row)
            print(
                f"  [adaptive] {defense_name:<18s} lam={lam:<5} "
                f"poison@k={agg.poison_in_topk:.3f} drift_tv={agg.drift_tv:.4f} "
                f"stance={agg.stance_shift:.4f}"
            )
    return out


def _make_all_poison(
    clean_docs: Sequence[Document],
    cfg: Dict[str, object],
    groups_by_stratum: Dict[str, Tuple[str, str]],
) -> Tuple[List[Document], Dict[str, Tuple[str, str]]]:
    n_per = poison_count_for(cfg, len(clean_docs))
    poison: List[Document] = []
    for i, (stratum, gp) in enumerate(groups_by_stratum.items()):
        fav, sup = gp[0], gp[1]
        pool = [d for d in clean_docs if d.group in (fav, sup)]
        if not pool:
            continue
        poison.extend(
            make_poison_docs(
                pool,
                PoisonSpec(
                    favoured_group=fav,
                    suppressed_group=sup,
                    n_poison=n_per,
                    prefix=f"POISON-{stratum}",
                    seed=int(cfg["seed"]) + i,
                ),
            )
        )
    return poison, groups_by_stratum


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="configs/default.json")
    ap.add_argument("--quick", action="store_true", help="tiny smoke run")
    ap.add_argument("--out", default=None, help="override results dir")
    args = ap.parse_args(argv)

    cfg = load_config(args.config, args.quick)
    out_dir = args.out or os.path.join("results", str(cfg["run_tag"]))
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 78)
    print("Retrieval poisoning / group-representation drift experiment")
    print("=" * 78)
    print(f"config      : {json.dumps(cfg, ensure_ascii=False)}")
    print(f"output dir  : {out_dir}")

    t0 = time.time()
    bundle = build_bundle(cfg)
    print(
        f"corpus      : {len(bundle.docs)} documents, "
        f"{len(bundle.queries)} queries, strata={list(bundle.groups)}"
    )

    per_query_rows: List[Dict[str, object]] = []
    agg_rows: List[Dict[str, object]] = []

    # Injection-budget sweep.  The clean condition is budget-independent, so it
    # is run once; every attacked condition is run at each rate.  This is the
    # sweep that makes results comparable across corpora of different size.
    rates: List[Optional[float]]
    if str(cfg.get("poison_budget", "per_stratum")) == "rate" and cfg.get("poison_rates"):
        rates = [float(r) for r in cfg["poison_rates"]]  # type: ignore[index]
    else:
        rates = [None]

    print("\n-- main sweep " + "-" * 63)
    for attack in cfg["attacks"]:
        attack_rates = [None] if attack == "clean" else rates
        for rate in attack_rates:
            cfg_run = dict(cfg)
            if rate is not None:
                cfg_run["poison_rate"] = rate
            n_per = poison_count_for(cfg_run, len(bundle.docs))
            if attack != "clean":
                print(
                    f"  [budget] rate={rate:.4%} -> {n_per} passages/stratum "
                    f"({n_per * len(bundle.groups)} injected of {len(bundle.docs)})"
                )
            for rk in cfg["retrievers"]:
                # a real-encoder retriever is swept over several backbones so
                # that one run yields the cross-encoder comparison that the
                # backbone-alignment claim depends on
                backbones = (
                    [str(b) for b in cfg["backbones"]]  # type: ignore[index]
                    if rk == "st" and cfg.get("backbones")
                    else [str(cfg.get("backbone", "gte-base"))]
                )
                for bb in backbones:
                    cfg_bb = dict(cfg_run)
                    cfg_bb["backbone"] = bb
                    print(f"  [backbone] {bb} (retriever={rk})")
                    pq, ag = run_block(
                        attack=attack,
                        retriever_kind=rk,
                        bundle=bundle,
                        cfg=cfg_bb,
                        poison_ids_by_stratum={},
                    )
                    for row in pq + ag:
                        row["poison_rate"] = "" if rate is None else float(rate)
                        row["backbone"] = bb if rk == "st" else ""
                    per_query_rows.extend(pq)
                    agg_rows.extend(ag)

    print("\n-- adaptive attacker " + "-" * 55)
    # the adaptive evaluation perturbs embeddings, so it runs on a vector
    # back-end: the configured real encoder when one is selected, else the
    # self-contained dense retriever
    adaptive_rows = run_adaptive(
        bundle=bundle,
        cfg=cfg,
        retriever_kind="st" if cfg.get("backbone") and "st" in cfg["retrievers"]
        else "dense",
    )

    # ---- write outputs ---------------------------------------------------- #
    def _write(path: str, rows: List[Dict[str, object]]) -> None:
        if not rows:
            return
        keys: List[str] = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow(r)

    _write(os.path.join(out_dir, "per_query.csv"), per_query_rows)
    _write(os.path.join(out_dir, "aggregate.csv"), agg_rows)
    _write(os.path.join(out_dir, "adaptive.csv"), adaptive_rows)

    # stratum breakdown
    by_stratum_rows: List[Dict[str, object]] = []
    for r in per_query_rows:
        pass  # per-query already carries stratum; aggregated below
    # rebuild stratum aggregation from per-query rows
    from collections import defaultdict

    buckets = defaultdict(list)
    for r in per_query_rows:
        buckets[(str(r["attack"]), str(r["retriever"]), str(r["defense"]), str(r["epsilon"]), str(r["stratum"]))].append(r)
    for (atk, rk, dfn, eps, st), rs in sorted(buckets.items()):
        n = len(rs)

        def _mean(key: str) -> float:
            vals = [float(x[key]) for x in rs if x.get(key) not in ("", None) and not _isnan(x[key])]
            return float(np.mean(vals)) if vals else float("nan")

        by_stratum_rows.append(
            {
                "attack": atk,
                "retriever": rk,
                "defense": dfn,
                "epsilon": eps,
                "stratum": st,
                "n_queries": n,
                "drift_tv": _mean("drift_tv"),
                "drift_js": _mean("drift_js"),
                "stance_shift": _mean("stance_shift"),
                "stance_div": _mean("stance_div"),
                "stance_onesided": _mean("stance_onesided"),
                "stance_gap": _mean("stance_gap"),
                "poison_in_topk": _mean("poison_in_topk"),
                "poison_share": _mean("poison_share"),
                "in_pool_rate": _mean("in_pool_rate"),
                "mean_score": _mean("mean_score"),
            }
        )
    _write(os.path.join(out_dir, "by_stratum.csv"), by_stratum_rows)

    # ---- summary ---------------------------------------------------------- #
    lines: List[str] = []
    lines.append("Retrieval Poisoning / Group-Representation Drift -- summary")
    lines.append(f"run_tag={cfg['run_tag']}  elapsed={time.time() - t0:.1f}s")
    lines.append("")
    lines.append("TABLE 1  Attack effect (no defense), by retriever")
    lines.append(
        f"{'attack':>26s} {'retriever':>9s} {'drift_tv':>9s} {'drift_js':>9s} "
        f"{'stance_sh':>9s} {'stance_dv':>9s} {'poison@k':>9s} {'util':>7s}"
    )
    for r in agg_rows:
        if r["defense"] != "vanilla":
            continue
        lines.append(
            f"{str(r['attack']):>26s} {str(r['retriever']):>9s} "
            f"{float(r['drift_tv']):>9.4f} {float(r['drift_js']):>9.4f} "
            f"{float(r['stance_shift']):>9.4f} {float(r['stance_div']):>9.4f} "
            f"{float(r['poison_in_topk']):>9.3f} "
            f"{float(r['in_pool_rate']):>7.3f}"
        )

    lines.append("")
    lines.append("TABLE 2  Defense comparison under the strongest attack")
    lines.append(
        f"{'retriever':>9s} {'defense':>12s} {'eps':>5s} {'drift_tv':>9s} "
        f"{'stance_dv':>9s} {'poison@k':>9s} {'util':>7s} {'mean_score':>10s}"
    )
    strong = "template_plus_projection"
    for r in agg_rows:
        if r["attack"] != strong:
            continue
        lines.append(
            f"{str(r['retriever']):>9s} {str(r['defense']):>12s} "
            f"{str(r['epsilon']):>5s} {float(r['drift_tv']):>9.4f} "
            f"{float(r['stance_div']):>9.4f} "
            f"{float(r['poison_in_topk']):>9.3f} {float(r['in_pool_rate']):>7.3f} "
            f"{float(r['mean_score']):>10.4f}"
        )

    lines.append("")
    lines.append("TABLE 3  Epsilon sweep (representation budget) -- the frontier")
    lines.append(
        f"{'retriever':>9s} {'defense':>12s} {'eps':>5s} {'drift_tv':>9s} "
        f"{'stance':>8s} {'poison@k':>9s} {'util':>7s}"
    )
    for r in agg_rows:
        if r["attack"] != strong or str(r["defense"]).startswith("repr_") is False:
            continue
        lines.append(
            f"{str(r['retriever']):>9s} {str(r['defense']):>12s} "
            f"{str(r['epsilon']):>5s} {float(r['drift_tv']):>9.4f} "
            f"{float(r['stance_shift']):>8.4f} "
            f"{float(r['poison_in_topk']):>9.3f} "
            f"{float(r['in_pool_rate']):>7.3f}"
        )

    lines.append("")
    lines.append("TABLE 4  Adaptive attacker (knows the defense)")
    lines.append(
        f"{'defense':>18s} {'lambda':>7s} {'poison@k':>9s} {'drift_tv':>9s} "
        f"{'stance_dv':>9s}"
    )
    for r in adaptive_rows:
        lines.append(
            f"{str(r['defense']):>18s} {float(r['lambda']):>7.2f} "
            f"{float(r['poison_in_topk']):>9.3f} {float(r['drift_tv']):>9.4f} "
            f"{float(r.get('stance_div', float('nan'))):>9.4f}"
        )

    summary = "\n".join(lines)
    with open(os.path.join(out_dir, "summary.txt"), "w", encoding="utf-8") as fh:
        fh.write(summary + "\n")
    print("\n" + summary)
    print(f"\n[done] wrote results to {out_dir} in {time.time() - t0:.1f}s")
    return 0


def _isnan(v) -> bool:
    try:
        return bool(np.isnan(float(v)))
    except Exception:
        return True


if __name__ == "__main__":
    raise SystemExit(main())
