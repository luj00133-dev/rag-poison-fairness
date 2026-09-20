"""
Probe: is "over-generalisation" a usable provenance signal?

Hypothesis
----------
A poisoned passage is engineered to be retrieved for *many* queries at once
(the projection attack pushes it along the mean query direction), whereas a
legitimate passage is relevant to a small, specific set of queries.  If so, the
number of distinct queries that retrieve a passage is anomalously high for
poison -- and that count needs no ground-truth labels at inference time, so it
is deployable.

This script measures the signal.  It does NOT assume the answer; if the
distributions overlap, the hypothesis fails and the paper must say so.

Run
---
    python -m src.probe_overgeneralisation --config configs/default.json --quick
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from typing import Dict, List, Sequence

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.retrieval.base import BM25Retriever, Document  # type: ignore
    from src.data.corpus import load_corpus  # type: ignore
    from src.attacks.poisoning import (  # type: ignore
        DenseRetriever,
        PoisonSpec,
        make_poison_docs,
        subspace_project,
    )
else:
    from .retrieval.base import BM25Retriever, Document
    from .data.corpus import load_corpus
    from .attacks.poisoning import (
        DenseRetriever,
        PoisonSpec,
        make_poison_docs,
        subspace_project,
    )

GROUPS_BY_STRATUM = {
    "bbq-gender": ("woman", "man"),
    "bbq-disability": ("disabled", "nondisabled"),
    "stereoset-age": ("elderly", "young"),
    "stereoset-race": ("asian", "white"),
}


def build_poison(clean_docs: Sequence[Document], n_poison: int, seed: int):
    poison: List[Document] = []
    for i, (stratum, (fav, sup)) in enumerate(GROUPS_BY_STRATUM.items()):
        pool = [d for d in clean_docs if d.group in (fav, sup)]
        if not pool:
            continue
        poison.extend(
            make_poison_docs(
                pool,
                PoisonSpec(fav, sup, n_poison=n_poison, prefix=f"POISON-{stratum}", seed=seed + i),
            )
        )
    return poison


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.json")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--retriever", default="bm25", choices=["bm25", "dense"])
    ap.add_argument("--lam", type=float, default=1.0)
    args = ap.parse_args(argv)

    n_q = 4 if args.quick else 12
    n_poison = 4 if args.quick else 6

    bundle = load_corpus(n_queries_per_stratum=n_q, seed=20260101)
    clean = bundle.docs
    poison = build_poison(clean, n_poison, 20260101)
    all_docs = list(clean) + poison
    poison_ids = {p.doc_id for p in poison}

    if args.retriever == "bm25":
        r = BM25Retriever()
        r.index(all_docs)
    else:
        r = DenseRetriever(dim=512)
        r.index(all_docs)
        qmat = r._embed([q.text for q in bundle.queries])
        m = r.matrix.copy()
        m[len(clean):] = subspace_project(m[len(clean):], qmat, lam=args.lam)
        r.set_matrix(m)

    k = 5
    # how many distinct queries retrieve each document in their top-k
    hits: Counter = Counter()
    for q in bundle.queries:
        for d in r.search(q.text, k).docs:
            hits[d.doc_id] += 1

    n_queries = len(bundle.queries)
    by_group: Dict[str, List[float]] = {"poison": [], "clean": []}
    for d in all_docs:
        key = "poison" if d.doc_id in poison_ids else "clean"
        by_group[key].append(hits.get(d.doc_id, 0) / max(n_queries, 1))

    print("=" * 74)
    print(f"Over-generalisation probe  retriever={args.retriever} lam={args.lam}")
    print("=" * 74)
    print(f"corpus: {len(clean)} clean + {len(poison)} poison | {n_queries} queries | k={k}")
    print()
    print(f"{'set':>8s} {'n':>6s} {'mean':>9s} {'median':>9s} {'p90':>9s} {'max':>9s}")
    stats: Dict[str, Dict[str, float]] = {}
    for key in ("poison", "clean"):
        vals = np.array(by_group[key], dtype=np.float64)
        if vals.size == 0:
            continue
        stats[key] = {
            "mean": float(vals.mean()),
            "median": float(np.median(vals)),
            "p90": float(np.percentile(vals, 90)),
            "max": float(vals.max()),
        }
        print(
            f"{key:>8s} {vals.size:>6d} {vals.mean():>9.4f} "
            f"{np.median(vals):>9.4f} {np.percentile(vals, 90):>9.4f} {vals.max():>9.4f}"
        )

    # discriminability: poison vs clean at the best median split
    if "poison" in stats and "clean" in stats:
        thr = stats["clean"]["p90"]
        p_detected = float(
            np.mean(np.array(by_group["poison"]) > thr)
        ) if by_group["poison"] else float("nan")
        false_pos = float(
            np.mean(np.array(by_group["clean"]) > thr)
        )
        print()
        print(f"threshold = clean p90 = {thr:.4f}")
        print(f"  poison detection rate : {p_detected:.3f}")
        print(f"  clean false-positive  : {false_pos:.3f}")
        print()
        if p_detected > 0.5 and false_pos < 0.2:
            print("VERDICT: signal is usable -> worth including in the paper")
        elif p_detected > stats['clean']['median']:
            print("VERDICT: weak separation -> report as a negative/partial result")
        else:
            print("VERDICT: NO usable signal -> hypothesis FAILS, do not claim it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
