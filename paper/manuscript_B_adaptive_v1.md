# The Fragility of Fair Retrieval Under an Informed Attacker: Why Randomized and Composition-Constrained RAG Defenses Do Not Survive Adaptation

**Author**: Jiang Lu
**Affiliation**: School of Electronic and Optical Engineering, Nanjing University of Science and Technology
**Corresponding author**: Jiang Lu (lujiang12@njust.edu.cn; luj00133@gmail.com). ORCID: 0009-0001-0717-2732.

**Target venue**: IEEE Transactions on Dependable and Secure Computing / IEEE Transactions on Information Forensics and Security

---

## Abstract

Defenses that protect the retrieval layer of retrieval-augmented generation (RAG) against fairness-targeted poisoning are evaluated almost exclusively against attackers who do not know the defense. In the security literature this is a well-understood insufficiency: a defense whose robustness is demonstrated only against a static adversary has not been shown to be robust. We provide the first systematic adaptive-attack evaluation of this defense family, in which the attacker observes the defense's own scoring function and optimises the poisoning perturbation against it.

We study three representative defenses — multi-query consistency (query randomization with ensemble aggregation), off-manifold filtering (calibrated density estimation in embedding space), and representation-conserving selection (a constrained re-ranker over group composition and within-group stance) — against an adaptive attacker that perturbs injected-passage embeddings along a query-derived direction and searches over perturbation strength to defeat each defense's penalty. The evaluation is run on two corpora: a controlled corpus with an exact clean reference, and BBQ, a naturally written bias benchmark.

Our findings are:

1. **Every defense is defeated, and the ordering of defenses changes completely under adaptation.** On the controlled corpus, off-manifold filtering reduces adversarial-passage inclusion from 0.750 to 0.125 against the non-adaptive attacker — a factor of six, and by far the best result in the static evaluation — but rises monotonically to 1.000 by perturbation strength $\lambda = 2$. The representation-conserving defenses, worse than off-manifold filtering at $\lambda = 0$ (0.625), saturate at 1.000 by $\lambda = 0.5$. A ranking derived from the static evaluation would recommend the wrong defense.

2. **Randomization-based defense has a structural limit, not a tuning limit.** Multi-query consistency defends by drawing query variants from a fixed, public distribution; the attacker optimises against the *expectation* of that distribution rather than any realisation. A defense whose mechanism is a fixed distribution over retrievals can therefore be defeated in expectation, and its robustness is non-adaptive by construction. We state this as a proposition and confirm it empirically (0.729 → 1.000).

3. **The strongest defense is strong for a reason unrelated to the attack.** Off-manifold filtering's static advantage comes from penalising vectors that leave the corpus manifold — precisely where the projection perturbation places them. Once the attacker trades perturbation strength against penalty, the defense's own penalty function becomes the attacker's constraint, and the advantage disappears. We show that the defense's penalty is *informative to the attacker*: making a defense's suspicion score observable is equivalent to handing over a differentiable objective.

4. **A partial exception, and its limits.** Only the R2 (within-group stance) constraint retains measurable benefit under adaptation, and only at low perturbation strength: on BBQ it holds adversarial inclusion at 0.049–0.319 up to $\lambda = 0.5$, versus 0.007–0.111 for off-manifold filtering, and it does so while preserving utility. Above $\lambda = 2$ every defense saturates at 1.000.

The practical implication is that adaptive evaluation changes the conclusion of this literature: static rankings of defense strength are not merely optimistic but *inverted*. We propose a minimal reporting protocol — an adaptive attacker with a strength sweep — and argue it should be mandatory for any retrieval-fairness defense claim.

**Keywords**: adaptive attacks, retrieval-augmented generation, data poisoning, fairness defenses, robustness evaluation, threat modelling

---

## 1. Introduction

Retrieval-augmented generation (RAG) [1] grounds language model outputs in an external corpus, which makes the corpus a security boundary. A poisoned corpus can steer not only factual accuracy [2, 3] but the *fairness* of the system's output: injected passages can amplify social bias in group-neutral queries [4]. A defense literature has accordingly emerged, proposing to constrain the group composition of the retrieved set [4, 5, 6, 7] or to equalise item-side exposure through randomized ranking [8].

These defenses are evaluated against **non-adaptive** attackers: the adversary injects passages and the defense responds, but the adversary does not model the defense. In cryptography and systems security, robustness claims made under this threat model are not accepted [9, 10]. An adversary who knows the defense will optimise against it, and a defense whose mechanism is public — which it must be, for auditability — provides that knowledge at no cost.

Fairness defenses for RAG have an additional exposure that makes adaptation unusually cheap. Several of them defend by **randomising** the retrieval (query perturbation [4], stochastic ranking [8]) and then aggregating. Randomisation is a legitimate defense against a fixed attack, but its security argument is probabilistic: it assumes the attacker cannot predict the realised randomisation. When the randomisation *distribution* is public and fixed, the attacker can instead optimise against its expectation, which is deterministic and known. We make this precise in §4.

We therefore conduct an adaptive-attack evaluation of three representative defenses from this family, in which the attacker is given the defense's scoring function and searches over perturbation strength to defeat it. We run the evaluation on two corpora — a controlled corpus with an exact clean reference, and BBQ [11] — and report where the static evaluation's conclusions survive and where they invert.

**Contributions.**

1. The first adaptive-attack evaluation of RAG fairness defenses: three defense families, two corpora, a defense-aware attacker with a perturbation-strength sweep (§5).
2. The demonstration that **the static ranking of these defenses inverts under adaptation** (§5.2): the best static defense (off-manifold filtering) and the weakest static defenses (composition constraints) converge to the same failure point once the attacker optimises.
3. A structural argument for why randomization-based defense cannot be robust here (§4): a defense whose mechanism is a fixed distribution over retrievals is defeated in expectation by an attacker who knows the distribution, independently of how much randomness is used.
4. Evidence that a defense's *penalty function is an attack surface*: making the suspicion score observable converts it from a filter into a constraint the attacker can optimise against (§5.3).
5. A concrete reporting protocol for the evaluation of retrieval-fairness defenses (§6).

---

## 2. Related Work

### 2.1 Poisoning and fairness attacks on RAG

Corpus poisoning against RAG was established by [2] and extended to query-agnostic and black-box settings [3], knowledge-graph retrieval [12], and multimodal pipelines [13, 14, 15]. The fairness-targeted variant injects passages that specifically alter the representation of protected groups rather than factual content [4], and fairness-targeted backdoors manipulate the semantic relationship between groups and stereotypes [16]. Our work does not propose a new attack; it asks whether the defenses proposed against these attacks hold under adaptation.

### 2.2 Fairness defenses for RAG

Existing defenses constrain the retrieved set. Wu et al. [6] adjust the proportion and ordering of group-relevant passages. Kim et al. [7] reverse-bias the embedder so its group balance compensates for the generator's own bias. Kim and Diaz [8] convert a deterministic ranker into a stochastic one so that equally relevant items receive equal expected exposure, controlled by a sharpness parameter. Zhao et al. [5] formulate fairness-aware retrieval as a constrained optimisation over position-wise group composition. Wang et al. [4] propose query perturbation with ensemble aggregation. All are evaluated against attackers that do not model the defense. Several authors note that their defenses are not robust enough — "further optimization … to achieve more stable and generalizable defense performance" [4]; "single-stage defenses give limited robustness" [17] — but the insufficiency is characterised as a tuning problem. We show it is structural.

### 2.3 Adaptive attacks

The principle that a defense must be evaluated against an adversary who knows it is standard in security [9, 10], and adaptive evaluation has repeatedly shown defenses designed against static attackers to be ineffective once the attacker accounts for the defense's mechanism. Retrieval-specific adaptive evaluation exists for factual poisoning [17, 18] but not, to our knowledge, for fairness-targeted poisoning or for the fairness-defense family. This paper fills that gap, and shows that the gap matters: the conclusion changes, and not only in magnitude.

---

## 3. Preliminaries

We use the retrieval-layer formulation and notation of our companion work [19]: a retrieved set $\mathcal{D}_q$ for query $q$ is characterised by **R1** group composition $P_{\text{grp}}(g)$ and **R2** within-group stance $P_{\text{fav}}(g)$; a defense is a map from the candidate set to a selected set $\mathcal{D}_q \subseteq \mathcal{C}$ of size $k$. R1 drift is the total-variation distance from a clean reference; the R2 metric is the cross-group spread $\max_{g \neq g'}|P_{\text{fav}}(g) - P_{\text{fav}}(g')|$; attack success is `poison@k`, the fraction of queries whose retrieved set contains at least one injected passage.

**Threat model.** The attacker can insert $n$ passages into the corpus and can perturb the embedding of each inserted passage by a vector $\delta$ with $\|\delta\| \le \eta$. The attacker **knows the defense**, including its scoring function, its hyperparameters, and (for randomized defenses) its distribution. It does not know the queries at injection time in the query-agnostic setting; where it does, we say so. This is the standard informed-adversary model.

---

## 4. Why Randomised Defense Cannot Be Robust Here

**Proposition 1.** Let a defense's selection mechanism be a fixed distribution $\pi(\mathcal{D} \mid q, \mathcal{C})$ over retrieved sets, public to the attacker. Let $U(\mathcal{D})$ be the attacker's utility (e.g. the indicator that $\mathcal{D}$ contains an injected passage). Then the attacker can achieve $\mathbb{E}_{\pi}[U] \to 1$ whenever there exists a set in the support of $\pi$ with $U = 1$, by choosing an injection configuration that places injected passages in every set with positive probability mass above a threshold.

*Proof sketch.* Since $\pi$ is fixed and known, the attacker computes $\mathbb{E}_\pi[U]$ explicitly as a function of the injection and maximises it by search or gradient. Randomisation does not bound $\mathbb{E}_\pi[U]$; it bounds the variance of $U$ across realisations. An attacker who does not care about variance — which is the usual case, since success is measured in expectation over queries — is unaffected by it. $\square$

The proposition is elementary, and that is the point: **randomisation is a defense against unpredictability, not against knowledge.** Two consequences specific to this literature follow.

**Corollary 1 (fixed-distribution defenses).** Multi-query consistency [4] perturbs the query by token dropout at rate $\delta$ and aggregates over $n_v$ variants. The perturbation is random but its *rate* and *number* are public constants. The expected aggregate score of a passage is therefore a deterministic, differentiable function of the injected embedding, which the attacker can maximise directly. Adding variants does not change this: the attacker optimises the expectation, and the expectation is exact in the limit of many variants.

**Corollary 2 (penalty-observable defenses).** A defense that down-weights passages by a penalty $f(d)$ and whose penalty is computable from public information gives the attacker the constraint "stay inside the low-penalty region". If the attacker can satisfy that constraint while raising similarity — which is possible whenever the penalty is a continuous function of a perturbation the attacker controls — the defense imposes a cost rather than a barrier. Off-manifold filtering is exactly this case (§5.3).

We do not claim these observations are novel in general; they are the standard reason adaptive evaluation is required. Our claim is that this defense family is *structurally* exposed to them, because its two dominant mechanisms — public randomisation and an observable penalty — are precisely the two cases the propositions cover, and that the published evaluations therefore overstate robustness in a way that inverts the ranking of defenses.

---

## 5. Experiments

### 5.1 Setup

**Corpora.** (i) A **controlled corpus** with an exactly known clean reference for both R1 and R2, built from stereotype/anti-stereotype template inventories; 48 group-neutral queries over four strata, 1,824 passages. (ii) **BBQ** [11], a naturally written bias benchmark: 17,792 passages over 144 group-neutral queries in four categories, with stance labels derived from BBQ's own stereotype annotations so that no new annotation is introduced.

**Attack.** Pairwise injection: the attacker injects $n$ passages drawn from the legitimate template/context inventory, half favourable toward group $A$ and half unfavourable toward $B$, so that the injected set's R1 composition is balanced by construction. Two injection modes: **template only** (text-level, no embedding control) and **template + projection**, where injected embeddings are perturbed as
$$h' = h + \lambda \, \langle h, \bar{q} \rangle \|\bar{q}\|^{-2} \bar{q},$$
with $\bar{q}$ the mean query direction. The attacker sweeps $\lambda \in \{0, 0.25, 0.5, 1, 2, 4\}$.

**Defenses.** `multi_query` — token-dropout query variants with frequency/rank aggregation [4]. `manifold` — calibrate the corpus manifold by PCA, down-weight passages by residual distance outside it. `repr_conserving` — greedy constrained selection over group composition (R1) and within-group stance (R2) with a per-group budget $\epsilon$ [19].

**Adaptive evaluation.** For each defense the attacker is given the defense's penalty function $f(\cdot)$ and, for each $\lambda$ in the sweep, evaluates the objective $\mathrm{sim}(d, \bar{q}) - f(d)$ over the candidate injected passages, retaining the $\lambda$ that maximises it. Robustness is reported as `poison@k` as a function of $\lambda$; a defense is robust to the extent that this curve stays low as $\lambda$ grows.

### 5.2 Static ranking inverts under adaptation

**Table 1.** `poison@k` under the adaptive attacker. Best (lowest) value per column in bold.

*Controlled corpus:*

| Defense | λ=0 | λ=0.25 | λ=0.5 | λ=1 | λ=2 | λ=4 | Static rank |
|---|---|---|---|---|---|---|---|
| off-manifold filtering | **0.125** | **0.438** | **0.750** | 0.938 | 1.000 | 1.000 | 1st |
| `repr_conserving` (R1+R2) | 0.625 | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | 2nd |
| multi-query consistency | 0.729 | 0.958 | 1.000 | 1.000 | 1.000 | 1.000 | 3rd |

*BBQ (natural corpus):*

| Defense | λ=0 | λ=0.25 | λ=0.5 | λ=1 | λ=2 | λ=4 | Static rank |
|---|---|---|---|---|---|---|---|
| off-manifold filtering | **0.007** | **0.021** | **0.111** | 0.403 | 0.917 | 1.000 | 1st |
| `repr_conserving` (R1+R2) | 0.049 | 0.111 | 0.319 | 0.764 | 0.979 | 1.000 | 2nd |
| multi-query consistency | 0.083 | 0.299 | 0.535 | 0.847 | 0.993 | 1.000 | 3rd |

On the controlled corpus, off-manifold filtering reduces adversarial inclusion from 0.750 (no defense) to **0.125** against the static attacker — a factor of six, and the best result anywhere in our study. It is the defense one would recommend from a static evaluation. Under adaptation it rises monotonically — 0.125 → 0.438 → 0.750 → 0.938 → 1.000 — and is defeated by $\lambda = 2$. The composition-constrained defenses, which are *five times worse* statically (0.625), saturate at 1.000 by $\lambda = 0.5$; they fail sooner but were never credible. **Above $\lambda = 2$ every defense is at 1.000: complete adversarial inclusion.**

The natural corpus shows the same pattern at lower magnitude, and here the comparison is more interesting because the defenses are closer statically. Off-manifold filtering holds 0.007–0.111 out to $\lambda = 0.5$ versus 0.049–0.319 for `repr_conserving`, i.e. a 2–4x gap, which persists further into the sweep (at $\lambda = 1$: 0.403 vs 0.764). The *ordering* is stable but the *magnitudes* are not, and the crossover to complete failure occurs within the sweep in both corpora.

**The attacker does not pay for this in passage quality.** A natural objection is that a large perturbation degrades the injected passages, so their inclusion becomes harmless and the defense is being credited for the attacker's own self-inflicted damage. We measured this directly: `usage` is the mean cosine similarity between each injected passage's perturbed embedding and its original. It remains **0.945–0.957 at $\lambda = 1$**, 0.883–0.884 at $\lambda = 2$, and 0.755–0.810 at $\lambda = 4$ (controlled / BBQ respectively). At the point where the strongest defense is already at 0.938–0.403 inclusion, the injected material is more than 94% intact semantically. **The defenses fail while the attack retains essentially full strength**, so the failure cannot be attributed to self-degradation.

**Finding 1.** No defense in this family survives an informed attacker. Under adaptation the failure point is reached within $\lambda \le 2$ in every case, and the defenses converge to identical (complete) failure. Static evaluation overstates robustness by up to a factor of eight, and a defense selected on static performance (off-manifold filtering) is defeated as comprehensively as one selected on structural grounds, merely later in the sweep.

### 5.3 The defense's penalty is the attacker's constraint

Off-manifold filtering's static advantage is not accidental and not a property of fairness defense: it penalises vectors that leave the corpus manifold, and the projection perturbation places them exactly there. In the static and mildly-adaptive regime the defense is therefore well-matched to the attack.

The mechanism by which it fails is instructive. The attacker's problem is
$$\max_{\delta}\ \ \mathrm{sim}(h + \delta, \bar{q}) \quad \text{s.t.} \quad f(h + \delta) \le \tau,$$
where $f$ is the defense's penalty. Because $f$ is a continuous, publicly computable function of $\delta$, this is not a barrier but a constraint set: the attacker selects the largest $\lambda$ whose induced residual still falls within the tolerated band, then pushes $\lambda$ until the low-penalty region is exhausted. The observed monotone rise of `poison@k` with $\lambda$ is the signature of an attacker expanding along this constraint until it binds.

This generalises beyond manifold filtering. Any defense whose suspicion score is (i) computable from public information and (ii) continuous in a perturbation the attacker controls is exposed to the same treatment: the score stops being a filter and becomes a feasibility constraint. **Publishing the scoring function, which auditability requires, is equivalent to giving the attacker a differentiable objective.**

### 5.4 What retains benefit, and for how long

Only one configuration retains measurable benefit under adaptation, and only in part of the sweep: `repr_conserving` on BBQ, which holds `poison@k` at 0.049 / 0.111 / 0.319 for $\lambda \le 0.5$ while preserving the utility proxy (`in_pool_rate` 0.442 versus 0.363 for no defense). Its advantage over multi-query consistency is present throughout the sweep (0.319 vs 0.535 at $\lambda = 0.5$; 0.764 vs 0.847 at $\lambda = 1$).

We attribute this to the defense's objective rather than to any attack-specific matching: it is the only defense whose constraint is expressed over the *composition* of the retrieved set rather than over individual passage statistics, so it cannot be satisfied by choosing perturbations but only by changing which passages are mutually compatible. That is a weaker effect than the static evaluation suggested, and it disappears by $\lambda = 2$.

**Finding 2.** Under adaptation, the only defense retaining any measurable benefit is the one whose constraint acts on the retrieved set rather than on individual passages — and its benefit is bounded, disappearing within the sweep. This is consistent with the structural argument of §4: constraints on passage-level statistics are optimisable-against because they are properties of a passage the attacker controls; constraints on set composition are not, but they are correspondingly weaker.

---

## 6. A Reporting Protocol

The results above are not sensitive to our particular attack; they follow from the attacker being informed. We therefore propose a minimal protocol, which we suggest should be required for any claim of robustness for a retrieval-fairness defense:

1. **State the threat model explicitly**, including whether the attacker knows the defense. A claim of robustness without this qualifier is uninterpretable.
2. **Report `poison@k` as a function of attacker strength**, not at a single operating point. A single value cannot distinguish a defense that is robust from one that has been evaluated below its failure threshold.
3. **Sweep perturbation strength to the point of failure** and report where it occurs. In our study every defense fails by $\lambda \le 2$; a sweep stopping at $\lambda = 0.25$ would have shown three apparently robust defenses.
4. **Report a utility-preserving baseline**, since a defense can trivially achieve low `poison@k` by returning fewer or worse passages.
5. **For randomized defenses, state the distribution and assume it is known.** Report the attacker's optimal response to the expectation, not to a sample.
6. **For penalty-based defenses, report whether the penalty is computable from public information**, and if so treat the penalty as a constraint in the attacker's optimisation rather than as an unknown.

Point 6 is the one most likely to be overlooked, and in our experiments it is decisive for the defense that looked strongest.

---

## 7. Limitations

1. **Attacker strength.** Our adaptive attacker sweeps a single scalar perturbation direction derived from the mean query. A full bilevel optimisation over the perturbation vector would be at least as strong; our results are therefore a lower bound on adaptive attack effectiveness, not an upper bound. We consider this the conservative direction for our claims but it means the reported failure points are optimistic for the defenses. [FILL: full bilevel optimisation.]
2. **Perturbation budget.** We vary $\lambda$ without an explicit norm budget $\eta$; the two are related but not identical, and a reader wishing to compare against the literal constraint in [4] should note the difference.
3. **Corpora.** A controlled corpus and BBQ. BBQ is a bias benchmark rather than a retrieval benchmark, and its large pre-existing stance imbalance dominates absolute fairness metrics (see [19] for a fuller treatment). A neutral retrieval corpus is needed to place the magnitudes on a representative footing. [FILL]
4. **Defense coverage.** Three defenses from two mechanism families. Coverage of the embedder-control [7] and constrained-optimisation [5] families would strengthen the generality of Finding 1; we argue the structural argument of §4 applies to both, since embedder control is also a fixed public map and constrained optimisation has a public objective.
5. **No generation-stage evaluation.** As in [19], we evaluate at the retrieval layer for reproducibility on commodity hardware.

---

## 8. Conclusion

Defenses for retrieval fairness in RAG are evaluated against attackers who do not know the defense, and this is not a conservative simplification — it changes the conclusion. We conducted the first adaptive-attack evaluation of this defense family, giving the attacker the defense's own scoring function and a perturbation-strength sweep, on a controlled corpus and on a naturally written bias benchmark.

Every defense is defeated. The defense that looks strongest statically — off-manifold filtering, reducing adversarial inclusion sixfold against a static attacker — rises monotonically to complete failure by perturbation strength $\lambda = 2$. The randomized defense is defeated by the elementary observation that its distribution is public, so the attacker optimises its expectation. The penalty-based defense is defeated because its penalty is a continuous public function of the perturbation, which converts a filter into a constraint the attacker expands against until it binds.

The practical consequence is that static rankings of defense strength in this literature are not merely optimistic but inverted: the defense recommended by a static evaluation fails earliest relative to its static margin, and all defenses converge to identical failure. We propose a six-point reporting protocol, of which the least intuitive and most decisive item is that a defense's penalty function should be treated as part of the attacker's constraint set rather than as an unknown quantity the attacker must work around.

---

## References

[1] P. Lewis, E. Perez, A. Piktus, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS*, 2020.

[2] W. Zou, R. Geng, B. Wang, J. Jia. PoisonedRAG: Knowledge corruption attacks to retrieval-augmented generation of large language models. *USENIX Security*, 2025.

[3] B. Zhang, Y. Chen, Z. Liu, et al. Practical poisoning attacks against retrieval-augmented generation. *arXiv:2504.03957*, 2025.

[4] L. Wang, T. Zhu, L. Qin, L. Gao, W. Zhou. Bias amplification in RAG: Poisoning knowledge retrieval to steer LLMs. *IEEE TDSC*, 23(5):11033–11050, 2026.

[5] Y. Zhao, V. Efthymiou, J. Nummenmaa, K. Stefanidis. Fairness-aware retrieval optimization for retrieval-augmented generation. *arXiv:2605.15790*, 2026.

[6] X. Wu, S. Li, H.-T. Wu, Z. Tao, Y. Fang. Does RAG introduce unfairness in LLMs? *COLING*, 2025.

[7] T. Kim, J. M. Springer, A. Raghunathan, M. Sap. Mitigating bias in RAG: Controlling the embedder. *Findings of ACL*, 2025.

[8] T. E. Kim, F. Diaz. Towards fair RAG: On the impact of fair ranking in retrieval-augmented generation. *ICTIR*, 2025.

[9] N. Carlini, A. Athalye, N. Papernot, et al. On evaluating adversarial robustness. *arXiv:1902.06705*, 2019.

[10] F. Tramèr, N. Carlini, W. Brendel, A. Madry. On adaptive attacks to adversarial example defenses. *NeurIPS*, 2020.

[11] A. Parrish, A. Chen, N. Nangia, et al. BBQ: A hand-built bias benchmark for question answering. *Findings of ACL*, 2022.

[12] J. Liang, Y. Wang, C. Li, et al. GraphRAG under fire. *IEEE S&P*, 2026.

[13] H. Ha, Q. Zhan, J. Kim, et al. MM-PoisonRAG. *arXiv:2502.17832*, 2025.

[14] Y. Liu, Z. Yuan, G. Tie, et al. Poisoned-MRAG. *arXiv:2503.06254*, 2025.

[15] K. Edemacu, M. M. Shokri. Hidden in the metadata. *arXiv:2603.00172*, 2026.

[16] G. Bagwe, S. S. Chaturvedi, X. Ma, et al. Your RAG is unfair. *arXiv:2509.22486*, 2025.

[17] S. K. Mohanty, R. Patel, K. Yuvaraj, et al. TriShieldRAG: 3 rings, one blind spot in layered defenses for RAG. *arXiv:2607.23838*, 2026.

[18] P. Pathmanathan, M.-A. Panaitescu-Liess, C.-Y. J. Chiang, et al. RAGPart & RAGMask: Retrieval-stage defenses against corpus poisoning. *arXiv:2512.24268*, 2025.

[19] [Companion paper]. Two dimensions of retrieval fairness: Why group-proportion constraints cannot defend RAG against pairwise poisoning. *Under review*, 2026.

---

## Appendix A. Reproduction

```bash
# controlled corpus, all defenses, adaptive sweep (~25 s, CPU)
python -m src.run_experiment --config configs/default.json

# natural corpus (BBQ) replication (~165 s, CPU)
python -m src.run_experiment --config configs/bbq.json

# adaptive results are written to results/<tag>/adaptive.csv
```

The adaptive sweep is produced by `src.attacks.poisoning.subspace_project` driven
over $\lambda$ together with the per-defense penalty functions in
`src.defenses.selectors`; `run_adaptive` in `src/run_experiment.py` assembles the
objective $\mathrm{sim} - f$ and reports `poison@k` per $\lambda$.

No GPU is required; both corpora complete on CPU in under three minutes.
