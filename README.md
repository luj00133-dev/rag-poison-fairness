# Retrieval Fairness under Pairwise Poisoning

Code and data for two companion papers:

- **Paper A** — *Two Dimensions of Retrieval Fairness: Why Group-Proportion
  Constraints Cannot Defend RAG Against Pairwise Poisoning*
- **Paper B** — *The Fragility of Fair Retrieval Under an Informed Attacker: Why
  Randomized and Composition-Constrained RAG Defenses Do Not Survive Adaptation*

Everything here runs on **CPU in under four minutes**. No GPU, no model
downloads, no generator. The retrieval-layer formulation is deliberate: the
R1/R2 mechanism is measurable without an LLM, which makes the study reproducible
on commodity hardware and isolates the mechanism from generator behaviour.

---

## Findings in one table

| Finding | Corpus | Status |
|---|---|---|
| R1 composition drift is small and non-diagnostic under attack | both | retained |
| The R1-only defense is **inert** — identical to no defense at every ε and every injection rate | both | retained |
| The R2 constraint is the only dimension that moves either metric | both | retained |
| The projection attack transfers to naturally written text | both | retained |
| The text-only attack is **corpus-dependent** (needs lexical room) | controlled only | Finding 4 |
| No defense survives a defense-aware attacker | both | Paper B |

Key numbers: 0.1% injection (8 passages) reaches 68.75% adversarial inclusion on
the controlled corpus; R1-only defense gives `poison@k` *identical* to no
defense at every setting; the cross-group stance gap is exactly 0.0000 clean and
0.6250–1.0000 under attack.

---

## Quick start

```bash
python -m pip install numpy python-docx

# controlled corpus, full suite incl. injection-rate sweep  (~25 s)
python -m src.run_experiment --config configs/default.json

# natural-corpus replication on BBQ                        (~180 s)
python -m src.run_experiment --config configs/bbq.json

# development-scale smoke run                              (~5 s)
python -m src.run_experiment --config configs/default.json --quick

# Paper B's adaptive-attack numbers
python dump_usage.py

# Paper A's injection-rate tables
python dump_rate.py

# side-by-side corpus comparison
python compare_corpora.py
```

Outputs land in `results/<run_tag>/`:
`per_query.csv`, `aggregate.csv`, `by_stratum.csv`, `adaptive.csv`, `summary.txt`.

BBQ data (17,792 passages, 4 categories) is fetched from the official
repository — see `data/README.md`.

---

## Layout

| Path | Purpose |
|---|---|
| `src/retrieval/base.py` | `Document`/`Query` schema, vectorised BM25 |
| `src/data/corpus.py` | controlled corpus: exact known clean reference |
| `src/data/bbq_loader.py` | BBQ loader; stance labels derived from BBQ's own annotations |
| `src/attacks/poisoning.py` | pairwise injection, subspace projection, adaptive attacker |
| `src/defenses/selectors.py` | multi-query, manifold filter, representation-conserving selector |
| `src/eval/metrics.py` | R1 drift, R2 stance gap, attack-success and utility metrics |
| `src/run_experiment.py` | driver: sweeps injection rate × defense × retriever |
| `src/probe_overgeneralisation.py` | exploratory provenance signal (with its validity caveat) |
| `paper/` | manuscripts (Markdown + Word), docx renderer |
| `results/` | all raw results backing the published tables |

---

## Two methodological points worth knowing before you extend this

**1. Injection budget must be a rate, not a count.** An earlier version of this
code injected a fixed six passages per stratum and concluded the text attack
"does not transfer" to natural text. That was wrong: six passages is ~10% of a
small candidate pool but ~0.03% of an 18k-passage corpus, so a fixed count
measures corpus size, not attack strength. `poison_budget: "rate"` in the config
fixes this. If you compare against work reporting absolute counts, convert.

**2. R2 metrics must be a cross-group gap, not a deviation from a reference.**
Two plausible R2 statistics — deviation from a corpus reference, and
one-sidedness — are **silently blind** here: they move 0.286 → 0.311 and
0.467 → 0.500 across clean and fully-attacked conditions. The reason is that a
group-neutral query legitimately retrieves one-sided evidence, so a
deviation-based metric measures topic conditioning rather than group skew, and
pairwise poisoning preserves topic conditioning by construction. `stance_gap`
(the spread of favourable rate *across* groups) is the metric that works, and it
is exactly 0.0000 on a balanced corpus before any attack.

---

## Reproducibility

Both corpora, all defenses, the injection-rate sweep, and the adaptive
attacker are deterministic given `seed` in the config. The controlled corpus is
generated from a fixed seed with no downloads. BBQ is reconstructed by
`src/data/bbq_loader.py` from the official benchmark files.

Expected wall-clock on a desktop CPU: controlled 25 s, BBQ 180 s.

## License

Code: MIT. Derived data follows the license of the source benchmark (BBQ: CC-BY-4.0).
