"""Compress Paper A sections 5.5 and 5.6 into a single section.

Why: the encoder material grew to 17,793 characters, 33 paragraphs and six tables
across two sections, because each experiment was appended as its own section.
Both sections answer one question -- "can retrieval robustness be predicted from
the encoder, or must it be measured?" -- so two sections and six tables overstate
how much distinct content there is. The compression keeps every finding, the
mechanism, and the tables that carry the claim, and drops the duplication between
the two sections' framing paragraphs.

The merged table set replaces Tables 8, 9, 10 (backbone) and 11, 12, 13 (scale)
with:
    Table 8   projection attack by encoder family and size  (was 8 + 11)
    Table 9   text attack, base and large                   (was 10 + 11)
    Table 10  the scale mechanism                           (was 12)
    Table 11  R1 inertness at both scales                   (was 9 + 13)
    Table 12  adaptive attacker                             (was 3, now kept here)
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

start = s.find('### 5.5 ')
end = s.find('### 5.7 ')
assert start != -1 and end > start, (start, end)

NEW = r'''### 5.5 Encoder robustness: a per-checkpoint property, not a family property

The results so far are measured on our own retrievers. The encoders this literature actually uses differ substantially in how much structure an attacker can exploit, so we evaluate the attack across nine retrieval back-ends: BM25 and a self-contained feature-hashing dense retriever; the learned-sparse retriever SPLADE at two sizes; and the dense semantic encoders the compared work uses — GTE-base [5] and its larger sibling GTE-large, Contriever [8], and E5-base-v2 [4, 6] with E5-large-v2. We include SPLADE specifically because it separates two explanations a lexical-versus-semantic comparison cannot: it is sparse like BM25 but learned like a neural encoder. E5 receives its required `query:` / `passage:` prefixes; omitting them degrades retrieval and would distort the comparison.

**Table 8.** Projection attack (`template_plus_projection`), $\rho = 0.5\%$, no defense. The scale column pairs each encoder with its larger sibling from the same family and training recipe.

| Retriever | representation | size | R1 drift | R2 gap | `poison@k` |
|---|---|---|---|---|---|
| BM25 | lexical, unsupervised sparse | — | 0.1625 | 0.7436 | 0.750 |
| dense (feature hashing) | hashed, not semantic | — | 0.1625 | 1.0000 | 1.000 |
| SPLADE | learned sparse | 66M | 0.2687 | 1.0000 | 0.750 |
| SPLADE large | learned sparse | 110M | 0.2687 | 1.0000 | 1.000 |
| GTE-base | dense semantic | 110M | 0.4688 | 1.0000 | 1.000 |
| **GTE-large** | dense semantic | 335M | 0.4188 | 1.0000 | 1.000 |
| Contriever | dense semantic | 110M | 0.3687 | 1.0000 | 1.000 |
| E5-base-v2 | dense semantic | 110M | 0.4000 | 1.0000 | 1.000 |
| **E5-large-v2** | dense semantic | 335M | 0.3750 | 1.0000 | 1.000 |

Every back-end is attacked, and the R2 gap saturates at its maximum for all but BM25. The dense encoders' R1 drift (0.37–0.47) is **2.3×–2.9×** that of BM25 (0.16): the projection attack perturbs group composition *more* in a continuous semantic space, the opposite of what we expected when adding this experiment.

**Table 9.** Text-only (lexical) attack, $\rho = 0.5\%$ and $2\%$, no defense. This is where the back-ends separate.

| Retriever | representation | `poison@k` @0.5% | @2% | R1 drift | `fav_g2` |
|---|---|---|---|---|---|
| BM25 | lexical, unsupervised sparse | 0.7500 | 0.7500 | 0.1625 | 0.7436 |
| dense (feature hashing) | hashed (keeps lexical surface) | 0.6250 | 0.6250 | 0.0812 | 0.6167 |
| **SPLADE** | **learned sparse** | **0.6250** | 0.6250 | 0.2188 | **1.0000** |
| **SPLADE large** | learned sparse | **0.5625** | 0.5625 | 0.1875 | 0.8810 |
| Contriever | dense semantic | 0.5625 | 0.5625 | 0.1750 | 0.9444 |
| GTE-base | dense semantic | **0.0625** | 0.0625 | 0.0000 | n/a |
| **GTE-large** | dense semantic | **0.5000** | 0.5000 | 0.1313 | 0.9444 |
| E5-base-v2 | dense semantic | **0.0625** | 0.0625 | 0.0000 | n/a |
| **E5-large-v2** | dense semantic | **0.0000** | 0.0000 | 0.0000 | n/a |

Three observations, and they are the finding.

**Sparsity, not "neuralness", predicts susceptibility at a fixed size.** SPLADE learns its term weights — it is a neural encoder trained on relevance — yet it is as susceptible as BM25 (0.6250 versus 0.7500), because its representation is still a sparse bag of term weights. The attack raises a passage's score by appending query-aligned terms, which requires the representation to expose **per-term contributions**: a sparse retriever does that whether or not its weights are learned, and a dense encoder absorbs the appended text into a single vector. SPLADE is in fact the *most* efficiently attacked of the nine on the R2 dimension, reaching the maximum stance gap 1.0000 where BM25 reaches 0.7436 — its learned weighting evidently concentrates score on exactly the terms the attacker appends. But sparsity is a correlate, not a law, and two cases bound it: Contriever is dense and semantic yet nearly as susceptible as BM25 (0.5625), and GTE-large is dense and semantic yet eight times more susceptible than its own base checkpoint.

**Scaling does not close the spread, and it is not monotone.** Table 9's clearest result is unexpected: GTE-base and E5-base-v2 are equally resistant at base size (both 0.0625 — the attack succeeds on three of 48 queries), and enlarging both by the same factor of three moves them in *opposite* directions. **E5-large-v2 becomes more resistant (0.0625 → 0.0000, the attack now fails on every query); GTE-large becomes eight times more susceptible (0.0625 → 0.5000, succeeding on 24 of 48).** SPLADE is susceptible at both sizes with little change (0.6250 → 0.5625). Per-query inclusion is binary, so this is a shift in *how many* queries are compromised, not a drift in a continuous score.

**The mechanism is not geometry.** We tested the obvious explanation and it is wrong, which makes the result more informative. If GTE-large's space were more anisotropic — vectors collapsed into a narrower cone — a fixed textual nudge would move rank further, and the finding would reduce to a known property. Measured, GTE-base and GTE-large are near-identical in mean pairwise cosine (0.8484 vs 0.8579), effective dimensionality (13.2 both, against 768 and 1024 nominal), and spread of query similarity (0.0860 vs 0.0895); the E5 pair behaves the same (0.8291 / 0.8375; 13.9 / 14.8). What differs is the gain the attack buys:

**Table 10.** Where the GTE scale effect comes from. 36 injected passages, 48 queries, no defense, $\rho = 0.5\%$.

| Quantity | GTE-base | GTE-large |
|---|---|---|
| mean cosine gain of poison over clean | **+0.0115** | **+0.0200** |
| mean best-poison cosine | 0.8907 | 0.8975 |
| mean top-5 clean threshold | 0.8982 | 0.8988 |
| mean margin (best poison − threshold) | **−0.0075** | **−0.0013** |
| `poison@k` | 0.0625 | 0.5000 |

The two encoders place the same injected text at almost the same distance from the query (0.8907 vs 0.8975), and the legitimate competition sits at the same threshold (0.8982 vs 0.8988). The difference is that **the identical appended vocabulary buys 74% more similarity on GTE-large (+0.0200 vs +0.0115)**. Because the mean margin is only about −0.007, a gain difference of +0.0085 carries a large fraction of queries across the threshold — exactly the 3-to-24 shift. Susceptibility is the interaction between the attack's vocabulary and the encoder's learned weighting of it, and none of the coarse descriptors we tried — architecture, dimensionality, size, geometry, sparsity — predicts it.

**Table 11.** R1-only constraint inertness across encoders and scales. `template_plus_projection`, $\rho = 0.5\%$; Δ = adversarial-passage inclusion minus no defense.

| Retriever | `repr_group` ε=0 | `repr_both` ε=0 | Δ |
|---|---|---|---|
| BM25 | 0.7500 | 0.7500 | **0.0000** |
| dense (hash) | 1.0000 | 1.0000 | **0.0000** |
| SPLADE distil | 0.7500 | 0.7500 | **0.0000** |
| SPLADE large | 1.0000 | 1.0000 | **0.0000** |
| GTE-base | 1.0000 | 1.0000 | **0.0000** |
| GTE-large | 1.0000 | 1.0000 | **0.0000** |
| E5-base-v2 | 1.0000 | 1.0000 | **0.0000** |
| E5-large-v2 | 1.0000 | 1.0000 | **0.0000** |

In all sixteen constrained configurations the difference is exactly zero. The projection attack reaches complete inclusion on seven of the eight, so the constraint is inert in the worst case rather than a marginal one. This is the third independent setting in which the inertness holds, after the two corpora and the injection-rate sweep.

### 5.6 Adaptive attacker: no defense survives an informed adversary

The inertness results above are measured against a *static* attacker. The security literature's standard objection — and the reason adaptive evaluation is mandatory — is that a defense may hold against an attacker who does not know it and fail against one who does. It matters here for two independent reasons, both predicted by §6.5: our defenses are either randomised with public parameters or penalise an observable quantity.

For each defense the attacker is given the defense's own penalty function and searches over perturbation strength $\lambda$, using the same subspace-projection construction. We also report `usage`, the mean cosine similarity between each injected passage's perturbed and original embedding, so that a defense cannot be credited for the attacker's self-inflicted degradation: if the injected material were destroyed, low adversarial inclusion would be meaningless.

**Table 12.** Adaptive attacker (defense-aware), `poison@k`. Controlled corpus, $\rho = 2\%$.

| Defense | λ=0 | λ=0.25 | λ=0.5 | λ=1 | λ=2 | λ=4 | static rank |
|---|---|---|---|---|---|---|---|
| off-manifold filtering | **0.250** | **0.562** | **0.812** | 0.938 | 1.000 | 1.000 | 1st |
| `repr_both` (R1+R2) | 0.625 | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | 2nd |
| multi-query consistency | 0.729 | 0.958 | 1.000 | 1.000 | 1.000 | 1.000 | 3rd |

Off-manifold filtering is by a wide margin the strongest statically — it reduces adversarial inclusion from 0.750 for no defense to 0.250, a factor of three — and **collapses monotonically to complete failure by $\lambda = 2$**. Its static advantage is exactly what §6.5's Corollary 2 predicts: the defense penalises vectors that leave the corpus manifold, which is precisely where the projection perturbation places them, so once the attacker trades perturbation strength against penalty, the penalty becomes the attacker's constraint. The two composition-constrained defenses, which never beat 0.625 even statically, saturate by $\lambda = 0.5$. **The static ranking of defenses inverts under adaptation, and a defense selected on its static advantage is defeated as comprehensively as one selected on structural grounds.**

**The attacker pays almost nothing for this.** `usage` stays at 0.945–0.979 through $\lambda = 1$ and 0.883 at $\lambda = 2$. At the point where the strongest defense has already lost most of its advantage, the injected material is over 94% semantically intact. The collapse therefore cannot be attributed to the attack degrading its own passages.

**Correction.** An earlier draft reported 0.125 / 0.438 / 0.750 for off-manifold filtering and described its static advantage as a factor of six over no defense. Those values came from an exploratory run written to a scratch directory excluded from version control, not from the run that produces every other number in this paper; re-running the committed configuration reproduces Table 12 with 18 of 18 adaptive cells bit-identical. The qualitative conclusion is unchanged, but the static advantage is a factor of three, not six. We record it rather than silently overwriting, because a robustness factor is the kind of number a reader may quote.

### 5.7 Generation-stage propagation: does the retrieval skew reach the output?'''

s = s[:start] + NEW + '\n\n' + s[end:]
io.open(P, 'w', encoding='utf-8').write(s)

print('paper length now: %d chars' % len(s))
print('sections:')
for m in re.finditer(r'^### (5\.\d+ .+)$', s, re.M):
    print('  ' + m.group(1)[:74])
