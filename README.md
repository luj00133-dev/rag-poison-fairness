# Retrieval Fairness under Pairwise Poisoning

Code and data for two companion papers:

- **Paper A** — *Measuring Retrieval Fairness Under Adversarial Poisoning: Why
  the Standard Statistics Are Blind, and What to Measure Instead*
- **Paper B** — *The Fragility of Fair Retrieval Under an Informed Attacker: Why
  Randomized and Composition-Constrained RAG Defenses Do Not Survive Adaptation*

Paper A is framed as a **measurement** paper: its subject is the validity of the
statistics that fairness defenses are selected and validated by, and the defense
failure it reports is a proved consequence of that measurement failure rather
than a separate claim. The framing was changed late, after the experiments were
complete, because the evidence supported it better — the paper's contributions
are three measurement failures with a shared cause, not a defense that fails.

Everything here runs on **CPU in under four minutes**. No GPU, no model
downloads, no generator. The retrieval-layer formulation is deliberate: the
R1/R2 mechanism is measurable without an LLM, which makes the study reproducible
on commodity hardware and isolates the mechanism from generator behaviour.

---

## Findings in one table

| Finding | Corpus | Status |
|---|---|---|
| **Composition statistics are blind** — R1 drift stays at or below legitimate retrieval variance | both | retained |
| **Two of three R2 statistics are blind** — reference-deviation and one-sidedness are flat across clean and fully attacked | controlled | Finding 3 |
| **The right axis is the per-group shift, not the gap between groups** — an absolute difference cancels the joint relocation the attack performs | both | Findings 8-9 |
| The R1-only defense is **inert** — identical to no defense at every ε, every rate, all 6 retrievers; equivalence bound exactly ±0.0000 | both | retained, ceiling effect |
| The projection attack transfers to naturally written text; the text-only attack does not (needs lexical room) | both | Finding 4 |
| Text-attack susceptibility tracks **sparsity**, not "neuralness" — but sparsity is a correlate, not a law | controlled | Finding 7 |
| Susceptibility is **not monotone in encoder size**: GTE-base 0.0625 → GTE-large 0.5000, E5 0.0625 → 0.0000 | controlled | §5.6, Finding 11 |
| The scale effect is **not geometric**: identical anisotropy and effective dimensionality | controlled | Table 12 |
| No defense survives a defense-aware attacker, on any of 6 back-ends | both | Paper B |

Key numbers: 0.1% injection (8 passages) reaches 68.75% adversarial inclusion on
the controlled corpus; R1-only defense gives `poison@k` *identical* to no
defense at every setting; the cross-group stance gap is exactly 0.0000 clean and
0.6250–1.0000 under attack. Text-attack `poison@k` spans 0.0625–0.7500 across six
retrievers, and the two susceptible ones (BM25, SPLADE) are exactly the sparse
ones.

Both manuscripts compile to PDF with **zero LaTeX errors and zero undefined
references** via `paper/compile_papers.py`: Paper A is 51 pp. in the review
format (40 body + 8 appendix + 3 references, measured by
`analysis/page_profile.py`), Paper B 12 pp. That script parses real `pdflatex`
logs; the conversion log from `paper/make_latex.py` is *not* a compile check.

**Citation style.** Paper A's tex uses **author-date** citations, which is what
IP&M prints: verified against two 2026 articles in the journal through Crossref's
deposited reference strings ("Aljundi, R., Babiloni, F., ... (2018). Memory aware
synapses..."). This requires the `authoryear` class option —
`\documentclass[authoryear,review,3p,times]{elsarticle}` — because loading natbib
separately clashes and `\biboptions` afterwards has no effect. The conversion from
the earlier numeric style is scripted
(`analysis/apply_authoryear_conversion.py`) and checked by
`analysis/check_authoryear.py`. The markdown source still uses numbered citations,
since the docx is an internal copy rather than a submission format; the two
therefore differ in citation style by design.

Section 8's limitations are a summary table in the body, with the full statement
of each in Appendix D. Ten repeated result tables live in Appendix C. Both moves
were made to hold the *body* length down while keeping every measurement in the
paper; the appendix is where the page count goes as a result.

### Figures

Paper A carries nine figures: four data figures redrawn from committed results
(`fig_responsiveness`, `fig_r1_inertness`, `fig_encoder_scale`,
`fig_aggregate_vs_pergroup`) and five conceptual figures that illustrate the
paper's own framework — `fig_framework_tikz` (the retrieval → injection →
statistic panel, **drawn in TikZ** so it uses the document font and sets the
paper's own notation for \(\Delta_{R1}\) and \(\Delta_{R2}\) instead of
paraphrasing it), `fig_f_f1` / `fig_f_f2` / `fig_f_f3` (the three failure modes,
composed in the tex with `subcaption` and in the markdown as the pre-composed
`fig_failure_modes.pdf`), and `fig_probe_commitment` (free-form versus
forced-choice probe). The remaining four are generated bitmaps; `fig_framework.png`
is the earlier bitmap of the framework panel, kept only as a spare. The
conceptual figures carry no measured values, so nothing in them can be read as
data; every number they illustrate is in a table or in one of the four data
figures. Figure placement in the tex is checked by
`analysis/verify_pdf_figures.py`, which reads the PDF's own object stream and the
compile log rather than trusting a clean compile.

### Corrections we made to our own results

We record these rather than quietly fixing them, because both were found by
cross-checking papers against committed data:

1. **Paper B Table 1** was built from a scratch run in `results/verify/`, which
   `.gitignore` excludes, instead of the canonical `results/full/`. The static
   `poison@k` for off-manifold filtering is **0.250, not 0.125**. Re-running
   `configs/default.json` reproduces `results/full/adaptive.csv` exactly
   (18/18 cells bit-identical); the scratch values reproduce from no committed
   configuration.
2. **Paper B Finding 1b** claimed the adaptive collapse is "steeper on a real
   encoder", generalising from GTE-base. Adding Contriever, E5-base-v2 and
   SPLADE showed the abruptness does not reduce to one property — GTE-base and
   E5-base-v2 fail in one step (0.000 → 1.000) while Contriever and the
   learned-sparse SPLADE collapse gradually, like our own hashed retriever. The
   claim was replaced with the three statements that hold on all five.
3. **An earlier claim of "zero LaTeX errors"** rested on the pandoc conversion
   log while `pdflatex` was not on `PATH`. `paper/compile_papers.py` now does a
   real two-pass compile and parses `^!` lines.
4. **Injection budget must be a rate, not a count** (see the methodological
   notes below) — a fixed count produced a spurious "attack does not transfer"
   conclusion in an earlier version.
5. **Limitation 5 predicted, and the measurement contradicted it.** An earlier
   draft asserted that larger checkpoints "give no reason to expect agreement"
   with the base-size spread. Measured, the effect is an order of magnitude
   larger than the prediction implied: GTE-base 0.0625 → GTE-large 0.5000 within
   one family and training recipe, while E5 moves the other way. The limitation
   now reports the measurement and the mechanism (Table 12) instead of the
   guess. We also removed a planned `contriever-large` comparison after checking
   that Meta never released a Contriever above BERT-base — `contriever-msmarco`
   is the same size with a different recipe, and labelling it "large" would have
   been a misrepresentation.

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

# six-back-end adaptive sweep (Paper B 5.2b; needs HF_ENDPOINT)
export HF_ENDPOINT=https://hf-mirror.com
python -m src.run_experiment --config configs/align_gte_ad.json
python -m src.run_experiment --config configs/align_e5.json
python -m src.run_experiment --config configs/contriever_ad.json
python -m src.run_experiment --config configs/align_splade.json

# encoder-scale check (Paper A 5.6; large checkpoints take ~12-25 min each on CPU)
python -m src.run_experiment --config configs/align_e5_large.json
python -m src.run_experiment --config configs/align_gte_large.json
python -m src.run_experiment --config configs/align_splade_large.json

# analyses
python analysis/compare_six_backbones.py    # Paper A 5.5
python analysis/compare_scale.py            # Paper A 5.6, from committed CSVs
python analysis/collapse_table.py           # Paper B 5.2b, from committed CSVs
python analysis/stats_paper.py              # Paper A Appendix B: paired tests, equivalence bounds
python analysis/check_refs.py               # validates every §, Table and Finding cross-reference
python analysis/dump_rate.py                # Paper A injection-rate tables
python analysis/compare_corpora.py          # controlled vs BBQ
python analysis/find_table1_source.py       # traces a quoted number back to its run dir

# build the papers and verify they actually compile
python paper/make_docx.py
python paper/make_latex.py --class elsevier
python paper/compile_papers.py              # real pdflatex errors, not the conversion log
```

Outputs land in `results/<run_tag>/`:
`per_query.csv`, `aggregate.csv`, `by_stratum.csv`, `adaptive.csv`, `summary.txt`.

BBQ data (17,792 passages, 4 categories) is fetched from the official
repository — see `data/README.md`.

---

## Building the manuscripts

The manuscripts are written in Markdown, which is the source; `.tex`, `.docx`
and `.pdf` are derived.

```bash
# Word (needs python-docx)
python paper/make_docx.py

# LaTeX source for the two candidate venues
python paper/make_latex.py --class elsevier    # Computers & Security (elsarticle)
python paper/make_latex.py --class ieee        # TDSC / TIFS (IEEEtran)

# compile (any TeX distribution; MiKTeX on Windows)
cd paper/latex
pdflatex -interaction=nonstopmode paperA_R1R2.tex
pdflatex -interaction=nonstopmode paperA_R1R2.tex     # twice, for references
```

Both papers currently compile with **zero LaTeX errors and zero undefined
references** — Paper A 30 pages, Paper B 12 pages, verified by
`paper/compile_papers.py` (a real two-pass `pdflatex` whose `.log` is parsed for
`^!` errors, undefined citations/references and overfull boxes).
`paper/make_latex.py` only converts Markdown to `.tex` and does not compile
anything; its log is not a compile check.

Five conversion problems are handled in `make_latex.py`; each produces a hard
LaTeX error if left alone:

| Problem | Fix |
|---|---|
| Unicode math typed literally in Markdown (`ε`, `λ`, `≈`) | mapped to `$\varepsilon$` etc., outside existing math spans |
| pandoc's `\real{}` column widths | `calc` package |
| pandoc's `\def\LTcaptype{none}` on uncaptioned tables | declare a `none` counter |
| pandoc's syntax-highlighting macros (`\NormalTok` …) | `--no-highlight` |
| **Backticks pandoc leaves literal become LaTeX control sequences** | `_convert_leftover_code_spans` wraps them in `\texttt{}` |

That last one is not cosmetic. Pandoc converts `` `foo` `` to `\texttt{foo}`
inside ordinary paragraphs but leaves backticks literal in text inserted by hand
or inside raw constructs, and LaTeX then reads the following word as a control
sequence: a prose line whose code span began with the word *python* produced
`! Undefined control sequence` on `\python` and failed the whole build.
`postprocess` now converts any surviving backtick pair, escaping `_`, `%`, `#`,
`&`, `{`, `}`, `~` and `^` inside it, since code spans in these papers are
usually filenames.

The reference list is also rewritten into a `thebibliography` block: pandoc
renders `[1] Title` lines as prose with *escaped* brackets (`{[}1{]}`), so the
rewrite matches that form rather than the original.

---

## Layout

| Path | Purpose |
|---|---|
| `src/retrieval/base.py` | `Document`/`Query` schema, vectorised BM25 |
| `src/retrieval/dense.py` | dense retrievers: feature hashing, GTE-base, Contriever, E5-base-v2 |
| `src/retrieval/splade.py` | learned-sparse retriever (SPLADE) |
| `src/data/corpus.py` | controlled corpus: exact known clean reference |
| `src/data/bbq_loader.py` | BBQ loader; stance labels derived from BBQ's own annotations |
| `src/attacks/poisoning.py` | pairwise injection, subspace projection, adaptive attacker |
| `src/defenses/selectors.py` | multi-query, manifold filter, representation-conserving selector |
| `src/eval/metrics.py` | R1 drift, R2 stance gap, attack-success and utility metrics |
| `src/eval/attribution.py` | generation-stage probes: grounded answers, forced choice, judging |
| `src/eval/generation.py` | multi-provider chat client + local NLI scorer (stance, attribution) |
| `src/run_generation.py` | multi-generator generation-stage evaluation with bootstrap CIs and paired tests |
| `src/run_experiment.py` | driver: sweeps injection rate × defense × retriever |
| `analysis/compare_six_backbones.py` | the six-retriever comparison behind §5.5 |
| `analysis/compare_scale.py` | the encoder-scale check behind §5.6 |
| `analysis/stats_paper.py` | paired tests and equivalence bounds (Appendix B) |
| `analysis/check_refs.py` | validates every cross-reference; run it after any restructuring |
| `analysis/calibrate_nli.py` | pins the NLI convention down empirically; do not skip this |
| `analysis/context_control.py` | negative control: does the generator use the context at all? |
| `analysis/compare_corpora.py` | controlled corpus vs BBQ |
| `paper/compile_papers.py` | compiles both papers with MiKTeX and parses **real** LaTeX errors |
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

**3. Text-attack susceptibility tracks sparsity, not "neuralness".** We added
SPLADE specifically to decide between two explanations, and it decides: SPLADE
learns its term weights and is still as susceptible as BM25 (0.6250 vs 0.7500),
because its representation is sparse. The attack raises a passage's score by
appending query-aligned terms, which requires the representation to expose
**per-term contributions**; a sparse retriever does that whether or not its
weights are learned, and a dense encoder absorbs the appended text into one
vector. Two of the three dense encoders resist almost completely (GTE-base,
E5-base-v2 at 0.0625) while Contriever does not (0.5625), so a single-encoder
robustness claim conflates the defense with an unmeasured encoder property.

**4. Compile the paper, do not trust the conversion log.** `make_latex.py`
reports conversion diagnostics, not LaTeX errors, and `pdflatex` is not
necessarily on `PATH`. `paper/compile_papers.py` runs MiKTeX twice per paper and
parses `^!` lines and undefined references out of the real `.log`. This
distinction caught a claim in our own history that had been asserted on the
strength of the conversion log alone.

---

## Reproducibility

Both corpora, all defenses, the injection-rate sweep, and the adaptive
attacker are deterministic given `seed` in the config. The controlled corpus is
generated from a fixed seed with no downloads. BBQ is reconstructed by
`src/data/bbq_loader.py` from the official benchmark files.

Expected wall-clock on a desktop CPU: controlled 25 s, BBQ 180 s.

## License

Code: MIT. Derived data follows the license of the source benchmark (BBQ: CC-BY-4.0).
