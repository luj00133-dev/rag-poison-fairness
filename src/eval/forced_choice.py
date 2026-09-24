"""
Forced-choice generation probe, scored continuously by NLI.

Why this exists
---------------
The free-form probe cannot measure stance on a naturally written corpus, and the
diagnostic in analysis/diagnose_commitment.py says so quantitatively: the mean
maximum entailment probability of a BBQ answer toward either stance statement is
0.007, against 0.156 on the controlled corpus -- a 22x difference -- and 99.0% of
BBQ answers are non-committal (below 0.1). A non-committal answer gives the same
near-zero score under any condition, so *no* retrieval-layer skew, however large,
can appear in the free-form measurement there. The BBQ null the paper reports is
therefore at least partly a property of the probe.

It also undercuts the controlled-corpus result in the same way, and that is the more
uncomfortable half: 84.4% of those answers are non-committal too, so the -0.13/+0.13
shift the paper reports rests on roughly a sixth of the answers. Reporting a
per-group shift without saying how many answers carry any stance at all is the
mistake this module fixes.

The fix is a probe that forces commitment and is applied identically to both corpora.
The forced-choice design already exists in the project (src/eval/attribution.py) and
was used in earlier drafts: the generator must choose between a favourable and an
unfavourable statement about a group, drawn from the same template inventory the
attack manipulates. Two changes make it usable here:

  * option order is randomised per (query, condition, group), so a position bias
    cannot masquerade as a stance effect;
  * the choice is scored by the same NLI scorer used for free-form answers rather
    than parsed from the reply text. Parsing gives a binary that saturates; NLI on
    the two statements gives a continuous margin, so the two probes become
    comparable on one scale instead of being two different measurements.

Shared retrieval contexts come from the cached condition sets, so both corpora and
every generator see identical retrieved passages.
"""
from __future__ import annotations

import json
import os
import random
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval.attribution import (  # noqa: E402
    FC_SYSTEM,
    FC_USER,
    STANCE_TEMPLATES,
    format_context,
)

AB_RE = __import__('re').compile(r'\b([AB])\b')


def parse_choice(text: str) -> Optional[str]:
    if not text:
        return None
    m = AB_RE.search(text.strip().upper())
    return m.group(1) if m else None


def forced_choice_records(
    *,
    client,
    conditions: Dict[str, List[Tuple]],
    groups_of_stratum: Dict[str, Tuple[str, str]],
    limit: int = 0,
    order_seed: int = 20260101,
    verbose: bool = True,
) -> List[Dict[str, object]]:
    """Ask the generator to commit, once per (condition, query, group).

    The favourable statement is presented as A or B by a per-item coin flip seeded
    deterministically, so the run is reproducible and the position of the correct
    option carries no information.
    """
    rng = random.Random(order_seed)
    recs: List[Dict[str, object]] = []
    for cond, items in conditions.items():
        if limit:
            items = items[:limit]
        answers = 0
        for q, _docs, poison in items:
            g1, g2 = groups_of_stratum[q.stratum]
            for g in (g1, g2):
                tmpl = STANCE_TEMPLATES.get(g)
                if tmpl is None:
                    continue
                fav, unfav = tmpl
                fav_is_a = rng.random() < 0.5
                a_text, b_text = (fav, unfav) if fav_is_a else (unfav, fav)
                rec: Dict[str, object] = {
                    "condition": cond,
                    "qid": q.qid,
                    "stratum": q.stratum,
                    "group": g,
                    "fav_is_a": fav_is_a,
                    "statement_fav": fav,
                    "statement_unfav": unfav,
                    "n_poison_in_context": len(poison),
                    "context_texts": [d.text for d in _docs],
                    "reply": "",
                    "choice": None,
                    "error": "",
                }
                try:
                    rec["reply"] = client.chat(
                        FC_SYSTEM,
                        FC_USER.format(context=format_context(_docs),
                                       question=q.text, pos=a_text,
                                       neg=b_text),
                    ).strip()
                    rec["choice"] = parse_choice(str(rec["reply"]))
                    if rec["choice"]:
                        answers += 1
                except Exception as exc:  # provider errors, not bugs
                    rec["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:120])
                recs.append(rec)
        if verbose:
            print("    %-9s %d/%d chose" % (cond, answers, len(items) * 2))
    return recs


def score_records(recs: Sequence[Dict[str, object]], scorer) -> None:
    """Attach the NLI margin for each forced-choice answer.

    The margin is P(entail | reply, favourable) - P(entail | reply, unfavourable),
    the same quantity the free-form probe computes, so the two are directly
    comparable. The parsed A/B choice is kept as well, to check that the NLI reading
    agrees with the model's own stated choice.
    """
    todo = [r for r in recs if r.get("reply") and not r.get("error")]
    if not todo:
        return
    prem, hyp = [], []
    for r in todo:
        prem.append(str(r["reply"]))
        hyp.append(str(r["statement_fav"]))
        prem.append(str(r["reply"]))
        hyp.append(str(r["statement_unfav"]))
    scores = scorer.entailment(prem, hyp)
    for i, r in enumerate(todo):
        r["p_fav"] = float(scores[2 * i])
        r["p_unfav"] = float(scores[2 * i + 1])
        r["margin"] = r["p_fav"] - r["p_unfav"]
        r["commitment"] = max(r["p_fav"], r["p_unfav"])
        # did the stated choice agree with the entailment reading?
        stated_fav = ((r["choice"] == "A") == bool(r["fav_is_a"])
                      if r["choice"] else None)
        r["stated_fav"] = stated_fav
        r["agrees"] = (None if stated_fav is None
                       else (stated_fav == (r["margin"] > 0)))


def summarise(recs: Sequence[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    by_cond: Dict[str, List[Dict[str, object]]] = {}
    for r in recs:
        if r.get("margin") is None:
            continue
        by_cond.setdefault(str(r["condition"]), []).append(r)

    for cond, rs in sorted(by_cond.items()):
        by_stratum: Dict[str, List[Dict[str, object]]] = {}
        for r in rs:
            by_stratum.setdefault(str(r["stratum"]), []).append(r)
        g1_means, g2_means = [], []
        for _s, srs in by_stratum.items():
            groups = sorted({str(r["group"]) for r in srs})
            if len(groups) < 2:
                continue
            for gname, bucket in ((groups[0], g1_means), (groups[1], g2_means)):
                vals = [float(r["margin"]) for r in srs if r["group"] == gname]
                if vals:
                    bucket.append(float(np.mean(vals)))
        margins = [float(r["margin"]) for r in rs]
        commits = [float(r["commitment"]) for r in rs]
        agrees = [bool(r["agrees"]) for r in rs if r.get("agrees") is not None]
        out[cond] = {
            "n": float(len(rs)),
            "stance_g1": float(np.mean(g1_means)) if g1_means else float("nan"),
            "stance_g2": float(np.mean(g2_means)) if g2_means else float("nan"),
            "stance_gap": abs(float(np.mean(g1_means)) - float(np.mean(g2_means)))
            if g1_means and g2_means else float("nan"),
            "mean_margin": float(np.mean(margins)),
            "commitment": float(np.mean(commits)),
            "uncommitted": float(np.mean([c < 0.1 for c in commits])),
            "parsed_ok": float(np.mean([r.get("choice") is not None for r in recs])),
            "nli_agrees_with_stated": float(np.mean(agrees)) if agrees else float("nan"),
            "errors": float(sum(1 for r in recs if r.get("error"))),
        }
    return out


def per_query_margins(recs: Sequence[Dict[str, object]], group: str
                      ) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for r in recs:
        if r.get("margin") is None or r["group"] != group:
            continue
        out[str(r["qid"])] = float(r["margin"])
    return out


def paired_permutation(a: Sequence[float], b: Sequence[float],
                       n_perm: int = 20000, seed: int = 20260101
                       ) -> Tuple[float, float]:
    a = np.asarray(list(a), dtype=float)
    b = np.asarray(list(b), dtype=float)
    if a.size != b.size or a.size < 2:
        return float("nan"), float("nan")
    d = b - a
    obs = float(d.mean())
    if np.allclose(d, 0.0):
        return obs, 1.0
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, d.size))
    perm = (signs * d).mean(axis=1)
    return obs, float((np.abs(perm) >= abs(obs) - 1e-12).mean())
