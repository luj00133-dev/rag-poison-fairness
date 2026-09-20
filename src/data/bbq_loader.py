"""
Natural-corpus loader: BBQ (Parrish et al., 2022).

Purpose
-------
The controlled synthetic corpus of ``data.corpus`` makes the R1/R2 mechanism
measurable with an exactly known clean reference, but its passages are
template-instantiated, which is a threat to validity for any claim about
magnitude.  This loader rebuilds the same experimental object — a corpus of
passages with group and stance labels, probed by group-neutral queries — from
real BBQ data, so that the §5 findings can be replicated on naturally written
text.

How stance is labelled without new annotation
---------------------------------------------
BBQ ships two annotations that jointly determine whether a passage expresses a
stereotypical or a counter-stereotypical view:

  * ``additional_metadata.stereotyped_groups`` — which group the example's
    stereotype targets (e.g. ``["F"]`` for women), and
  * ``question_polarity`` — whether the stereotype-consistent answer is the
    negative (``neg``) or the non-negative (``nonneg``) option.

A passage whose answer names the stereotyped group, under a ``neg``-polarity
question, is a **stereotypical** (unfavourable) statement about that group.
A passage whose answer names the non-stereotyped group is
**counter-stereotypical** (favourable) for that group and, symmetrically,
unfavourable for the other.  We therefore derive stance directly from BBQ's own
labels rather than by re-annotating, which avoids injecting our own judgement
into the ground truth.

Known limitation
----------------
BBQ questions repeat across examples ("Who was the secretary?"), so a single
query retrieves passages from many examples.  This is *intended*: it is what
makes the pool large enough for top-k selection to be non-trivial, and it
mirrors the realistic case in which one user question is answered from many
corpus passages.  It does mean that the queries are not unique, so we treat the
distinct question strings as the query set.

Usage
-----
    python -m src.data.bbq_loader            # build and report statistics
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..retrieval.base import Document, Query


# --------------------------------------------------------------------------- #
# Category -> (protected group, non-protected group, BBQ group tokens)
# --------------------------------------------------------------------------- #
# BBQ encodes group membership in ``answer_info`` as [display, canonical].
CATEGORIES: Dict[str, Dict[str, object]] = {
    "Gender_identity": {
        "protected": "woman",
        "nonprotected": "man",
        "protected_tokens": {"F", "female", "woman", "women", "girl", "girls"},
        "nonprotected_tokens": {"M", "male", "man", "men", "boy", "boys"},
        "stratum": "bbq-gender",
    },
    "Disability_status": {
        "protected": "disabled",
        "nonprotected": "nondisabled",
        "protected_tokens": {"disabled", "D", "disability"},
        "nonprotected_tokens": {"nonDisabled", "non-disabled", "N", "not disabled"},
        "stratum": "bbq-disability",
    },
    "Age": {
        "protected": "elderly",
        "nonprotected": "young",
        "protected_tokens": {"old", "O", "elderly", "older"},
        "nonprotected_tokens": {"nonOld", "young", "Y", "non-old"},
        "stratum": "age",
    },
    "Race_ethnicity": {
        "protected": "african_american",
        "nonprotected": "european_american",
        "protected_tokens": {"Black", "African American", "African_American"},
        "nonprotected_tokens": {"White", "European American", "European_American"},
        "stratum": "race",
    },
}


@dataclass
class BBQCorpus:
    """Real-data counterpart of ``data.corpus.CorpusBundle``."""

    docs: List[Document]
    queries: List[Query]
    candidate_pool: Dict[str, Tuple[str, ...]]
    groups: Dict[str, Tuple[str, ...]]
    #: per-doc provenance: which (category, question) it came from
    provenance: Dict[str, Dict[str, object]]


def _group_of(answer_info_entry: Sequence[str], spec: Dict[str, object]) -> Optional[str]:
    """Map a BBQ answer-info pair to our protected/non-protected label."""
    toks = {str(t) for t in answer_info_entry}
    if toks & set(spec["protected_tokens"]):  # type: ignore[arg-type]
        return str(spec["protected"])
    if toks & set(spec["nonprotected_tokens"]):  # type: ignore[arg-type]
        return str(spec["nonprotected"])
    return None


def load_bbq(
    data_dir: str,
    *,
    categories: Optional[Sequence[str]] = None,
    max_examples_per_category: int = 4000,
    contexts_per_query: int = 30,
    seed: int = 20260101,
) -> BBQCorpus:
    """Build a passage corpus and query set from BBQ JSONL files.

    For each category we collect passages of the form
    ``"<context> Question: <question> Answer: <answer>"``.  The stance of a
    passage is derived as described in the module docstring:

      * answer names the stereotype-targeted group under a ``neg`` question
        -> stance ``-1`` (stereotypical / unfavourable toward that group)
      * answer names the other group -> stance ``+1`` (favourable toward it,
        and unfavourable toward the stereotype-targeted group)

    Queries are the distinct question strings, which are group-neutral by
    construction (BBQ questions never name the group).
    """
    import random

    rng = random.Random(seed)
    cats = list(categories) if categories else list(CATEGORIES.keys())

    docs: List[Document] = []
    provenance: Dict[str, Dict[str, object]] = {}
    by_question: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    groups: Dict[str, Tuple[str, ...]] = {}
    counter = 0

    for cat in cats:
        spec = CATEGORIES[cat]
        path = os.path.join(data_dir, f"{cat}.jsonl")
        if not os.path.exists(path):
            print(f"[warn] missing {path}, skipping {cat}")
            continue

        stratum = str(spec["stratum"])
        groups[stratum] = (str(spec["protected"]), str(spec["nonprotected"]))

        n_read = 0
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if n_read >= max_examples_per_category:
                    break
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                n_read += 1

                polarity = rec.get("question_polarity")
                stereo = set(
                    rec.get("additional_metadata", {}).get("stereotyped_groups", [])
                )
                if not stereo:
                    continue

                # which of the two groups does this example's stereotype target?
                if stereo & set(spec["protected_tokens"]):  # type: ignore[arg-type]
                    stereo_group = str(spec["protected"])
                    other_group = str(spec["nonprotected"])
                elif stereo & set(spec["nonprotected_tokens"]):  # type: ignore[arg-type]
                    stereo_group = str(spec["nonprotected"])
                    other_group = str(spec["protected"])
                else:
                    continue

                question = rec["question"]
                context = rec["context"]

                # one passage per answer option that names a group
                for key in ("ans0", "ans1", "ans2"):
                    ans_text = rec.get(key)
                    info = rec.get("answer_info", {}).get(key)
                    if ans_text is None or info is None:
                        continue
                    g = _group_of(info, spec)
                    if g is None:
                        continue  # "unknown" option

                    # stance: does this passage portray g favourably?
                    # A passage naming the stereotype-targeted group under a
                    # negatively-polarised question is unfavourable toward it;
                    # naming the non-targeted group is favourable toward it.
                    if g == stereo_group:
                        stance = -1 if polarity == "neg" else 1
                    else:
                        stance = 1 if polarity == "neg" else -1

                    doc_id = f"BBQ-{cat[:4]}-{counter:06d}"
                    counter += 1
                    text = f"{context} Question: {question} Answer: {ans_text}."
                    docs.append(
                        Document(
                            doc_id=doc_id,
                            text=text,
                            group=g,
                            stance=stance,
                            is_poison=False,
                        )
                    )
                    provenance[doc_id] = {
                        "category": cat,
                        "stratum": stratum,
                        "question": question,
                        "polarity": polarity,
                        "stereo_group": stereo_group,
                        "group": g,
                    }
                    by_question[(stratum, question)].append(doc_id)

    # ---- queries: distinct question strings with enough candidate passages -- #
    queries: List[Query] = []
    candidate_pool: Dict[str, Tuple[str, ...]] = {}
    for (stratum, question), ids in sorted(by_question.items()):
        if len(ids) < contexts_per_query:
            continue
        qid = f"{stratum}-q{len(queries):04d}"
        gs = groups[stratum]
        queries.append(
            Query(qid=qid, text=question, target_groups=gs, stratum=stratum)
        )
        # a query's candidate pool is the passages carrying that question
        candidate_pool[qid] = tuple(ids)

    return BBQCorpus(
        docs=docs,
        queries=queries,
        candidate_pool=candidate_pool,
        groups=groups,
        provenance=provenance,
    )


def report(corpus: BBQCorpus) -> None:
    print(f"passages : {len(corpus.docs)}")
    print(f"queries  : {len(corpus.queries)}")
    print()
    for stratum, gs in corpus.groups.items():
        sub = [d for d in corpus.docs if d.group in gs]
        print(f"--- {stratum} (groups {gs}) ---")
        print(f"  passages with group : {len(sub)}")
        for g in gs:
            gd = [d for d in sub if d.group == g]
            c = Counter(d.stance for d in gd)
            print(f"  {g:<20s} n={len(gd):<6d} stance={dict(sorted(c.items()))}")
        qs = [q for q in corpus.queries if q.stratum == stratum]
        print(f"  distinct queries    : {len(qs)}")
        if qs:
            sizes = [len(corpus.candidate_pool[q.qid]) for q in qs]
            print(
                f"  pool sizes          : min={min(sizes)} "
                f"median={sorted(sizes)[len(sizes)//2]} max={max(sizes)}"
            )
            print(f"  example query       : {qs[0].text!r}")
        print()


if __name__ == "__main__":
    import sys

    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ddir = os.path.join(here, "data", "bbq")
    c = load_bbq(ddir)
    report(c)
