"""
Driver: retrieval conditions -> generation -> stance judging -> attribution.

Builds the retrieved context for each condition by actually running the
retrievers and defenses (so the contexts are the same ones the retrieval-layer
tables report), then asks the generator to answer from each context and has the
same model judge the stance of its answer.

Run
---
    # offline validation of the whole pipeline, no API calls
    python -m src.run_attribution --config configs/attribution.json --dry-run

    # real run (needs DEEPSEEK_API_KEY)
    python -m src.run_attribution --config configs/attribution.json

Environment
-----------
    DEEPSEEK_API_KEY   required unless --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.run_experiment import (  # type: ignore
        build_bundle,
        build_defenses,
        build_retriever,
        apply_attack,
        load_config,
        poison_count_for,
        _make_all_poison,
        _retriever_embed,
    )
    from src.eval.attribution import (  # type: ignore
        DeepSeekClient,
        run_attribution,
        save,
    )
    from src.retrieval.base import Document, Query  # type: ignore
else:
    from .run_experiment import (
        build_bundle,
        build_defenses,
        build_retriever,
        apply_attack,
        load_config,
        poison_count_for,
        _make_all_poison,
        _retriever_embed,
    )
    from .eval.attribution import DeepSeekClient, run_attribution, save
    from .retrieval.base import Document, Query


DEFENSE_FOR_CONDITION = {
    "clean": None,
    "poisoned": None,
    "r1only": "repr_group",
    "r2both": "repr_both",
}

CONDITIONS = ("clean", "poisoned", "r1only", "r2both")


def collect_contexts(cfg: Dict[str, object]):
    """Return {condition: [(query, docs, poison_ids)]} for one configuration.

    The retrieval is performed for real, and the *same* query set is used in
    every condition, so the only thing that differs between conditions is the
    retrieved context.
    """
    bundle = build_bundle(cfg)
    k = int(cfg["top_k"])
    queries = bundle.queries
    rk = str(cfg.get("retriever", "st"))
    caps = _caps(cfg)

    # --- clean: unpoisoned corpus, no defense ----------------------------- #
    clean_retriever = build_retriever(rk, bundle.docs, cfg)
    clean_docs_map: Dict[str, List[Document]] = {}
    for q in queries:
        clean_docs_map[q.qid] = clean_retriever.search(q.text, k).docs

    # --- poisoned: same corpus plus the injection ------------------------- #
    atk_retriever = build_retriever(rk, bundle.docs, cfg)
    atk_retriever, poison_docs = apply_attack(
        "template_plus_projection", atk_retriever, bundle.docs, queries, cfg,
        bundle.groups,
    )
    poison_ids = {d.doc_id for d in poison_docs}

    out: Dict[str, List[Tuple[Query, List[Document], List[str]]]] = {
        c: [] for c in CONDITIONS
    }
    defenses = {d.name: d for d in build_defenses(atk_retriever, bundle.docs, cfg)}

    for q in queries:
        # clean
        docs = clean_docs_map[q.qid]
        out["clean"].append((q, docs, []))
        # poisoned (no defense)
        docs = atk_retriever.search(q.text, k).docs
        out["poisoned"].append(
            (q, docs, [d.doc_id for d in docs if d.doc_id in poison_ids])
        )
        # constrained variants
        for cond, dname in (("r1only", "repr_group"), ("r2both", "repr_both")):
            d = defenses.get(dname)
            if d is None:
                continue
            docs = d.retrieve(q, k).docs
            out[cond].append(
                (q, docs, [x.doc_id for x in docs if x.doc_id in poison_ids])
            )

    meta = {
        "n_docs": len(bundle.docs),
        "n_queries": len(queries),
        "n_poison": len(poison_docs),
        "groups": {k2: list(v) for k2, v in bundle.groups.items()},
        "stratum_of_qid": {q.qid: q.stratum for q in queries},
    }
    return bundle, out, meta


def _caps(cfg):
    """budget_modes must include the two constrained variants we compare."""
    c = dict(cfg)
    c["budget_modes"] = ["group", "both"]
    if not c.get("epsilons"):
        c["epsilons"] = [1.0]
    return c


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="configs/attribution.json")
    ap.add_argument("--out", default="results/attribution")
    ap.add_argument("--dry-run", action="store_true",
                    help="exercise the pipeline without API calls")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap queries per condition (0 = all)")
    args = ap.parse_args(argv)

    cfg = load_config(args.config, quick=False)
    if args.dry_run:
        cfg["quick"] = False

    os.makedirs(args.out, exist_ok=True)
    print("=" * 78)
    print("Generation-stage attribution")
    print("=" * 78)
    print(f"config : {args.config}")
    print(f"corpus : {cfg.get('corpus')}   retriever: {cfg.get('retriever')} "
          f"/ {cfg.get('backbone', '-')}")

    t0 = time.time()
    bundle, conditions, meta = collect_contexts(cfg)

    if args.limit:
        for c in conditions:
            conditions[c] = conditions[c][: args.limit]

    print(f"corpus    : {meta['n_docs']} docs, {meta['n_queries']} queries, "
          f"{meta['n_poison']} injected")
    for c in CONDITIONS:
        n = len(conditions.get(c, []))
        pk = np.mean([len(p) for _, _, p in conditions[c]]) if n else float("nan")
        print(f"  {c:<9s} n={n:<4d} mean poison in context = {pk:.2f}")

    client = DeepSeekClient(dry_run=args.dry_run)
    print(f"generator : {client.model} @ {client.base_url}"
          f"{'  [DRY RUN]' if args.dry_run else ''}")

    res = run_attribution(
        conditions=conditions,
        client=client,
        groups_of_stratum={k: (v[0], v[1]) for k, v in meta["groups"].items()},
    )

    save(res, os.path.join(args.out, "attribution.json"))

    # flat CSV of answers, for inspection and for the paper's appendix
    with open(os.path.join(args.out, "answers.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["qid", "stratum", "condition", "n_poison_in_context",
                    "leaning", "answer", "error"])
        for r in res.records:
            w.writerow([r.qid, r.stratum, r.condition, r.n_poison_in_context,
                        r.leaning, r.answer.replace("\n", " ")[:400], r.error])

    print("\n-- summary " + "-" * 66)
    print(f"{'condition':>10s} {'n':>4s} {'strata':>7s} {'fav_g1':>8s} "
          f"{'fav_g2':>8s} {'STANCE GAP':>11s} {'EAE-D':>7s} "
          f"{'poison@ctx':>11s} {'err':>4s}")
    from .eval.attribution import summarise  # local import to avoid cycle noise

    summ = summarise(res)
    for cond in CONDITIONS:
        s = summ.get(cond)
        if not s:
            continue
        print(f"{cond:>10s} {int(s['n']):>4d} {int(s['n_strata']):>7d} "
              f"{s['fav_rate_g1']:>8.3f} {s['fav_rate_g2']:>8.3f} "
              f"{s['stance_gap']:>11.4f} {s['eae_d']:>7.3f} "
              f"{s['poison_in_context']:>11.2f} {int(s['errors']):>4d}")
    print("\nNote: STANCE GAP is the generation-layer analogue of the retrieval R2")
    print("      metric. Compare its movement across conditions with the R2 gap")
    print("      reported at the retrieval layer: if the retrieval skew is")
    print("      consequential, poisoned > clean.")
    print("\nusage:", json.dumps(res.usage))
    print(f"[done] {time.time()-t0:.1f}s  ->  {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
