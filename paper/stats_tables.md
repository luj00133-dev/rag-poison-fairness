**Table S1.** Paired tests of R1-constraint inertness against no defense. Controlled corpus, `template_plus_projection`, $\rho = 0.5\%$, per-query adversarial-passage inclusion.

| Retriever | Defense | ε | n | Δ mean | 95% CI | p | excluded effect |
|---|---|---|---|---|---|---|---|
| bm25 | repr_group | 0.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| bm25 | repr_group | 1.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| bm25 | repr_both | 0.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| bm25 | repr_both | 1.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| bm25 | repr_stance | 0.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| bm25 | repr_stance | 1.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| dense | repr_group | 0.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| dense | repr_group | 1.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| dense | repr_both | 0.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| dense | repr_both | 1.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| dense | repr_stance | 0.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |
| dense | repr_stance | 1.0 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.000 | ±0.0000 |

Where the constraint changes nothing, the per-query difference vector is **identically zero**, not merely small: the bootstrap CI collapses to [0, 0] and the permutation test is degenerate by construction. The informative statistic is therefore the equivalence bound — the smallest effect the data exclude — and because the differences are exactly zero rather than approximately zero, these cells exclude *any* effect on adversarial-passage inclusion, not merely one above a threshold. The `repr_stance` rows are the contrast case: there the constraint does change the selection, the difference vector is non-degenerate, and both the CI and the p-value are meaningful.

**Table S2.** Bootstrap 95% CIs on the positive claims (per-question values, 10,000 resamples, no defense).

| Condition | Retriever | Metric | mean | 95% CI |
|---|---|---|---|---|
| clean | bm25 | R2 stance gap | 0.0000 | [0.0000, 0.0000] |
| clean | bm25 | R1 drift (TV) | 0.0000 | [0.0000, 0.0000] |
| clean | dense | R2 stance gap | 0.0000 | [0.0000, 0.0000] |
| clean | dense | R1 drift (TV) | 0.0000 | [0.0000, 0.0000] |
| template | bm25 | R2 stance gap | 0.7436 | [0.6068, 0.8718] |
| template | bm25 | R1 drift (TV) | 0.1625 | [0.1062, 0.2208] |
| template | dense | R2 stance gap | 0.6167 | [0.4556, 0.7667] |
| template | dense | R1 drift (TV) | 0.0812 | [0.0438, 0.1208] |
| template_plus_projection | bm25 | R2 stance gap | 0.7436 | [0.6068, 0.8718] |
| template_plus_projection | bm25 | R1 drift (TV) | 0.1625 | [0.1062, 0.2208] |
| template_plus_projection | dense | R2 stance gap | 1.0000 | [1.0000, 1.0000] |
| template_plus_projection | dense | R1 drift (TV) | 0.1625 | [0.1187, 0.2083] |
