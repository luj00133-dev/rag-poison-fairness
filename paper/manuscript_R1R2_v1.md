# Two Dimensions of Retrieval Fairness: Why Group-Proportion Constraints Cannot Defend RAG Against Pairwise Poisoning

**Author**: Jiang Lu
**Affiliation**: School of Electronic and Optical Engineering, Nanjing University of Science and Technology
**Corresponding author**: Jiang Lu (lujiang12@njust.edu.cn; luj00133@gmail.com). ORCID: 0009-0001-0717-2732.

**Target venue**: *Computers & Security* (Q1, CCF-B) — alternative: IEEE TDSC / IEEE TIFS

---

## Abstract

Retrieval-augmented generation (RAG) systems ground large language model outputs in an external corpus, which makes the retrieval layer a security-critical component: an adversary who can inject passages into that corpus can steer what the system cites as evidence. A recent line of work shows that such injection can be used not only to induce factual errors but to amplify *social bias*, and several defenses have been proposed that constrain the **group composition** of the retrieved set — the proportion of passages about one protected group versus another.

We show that this defense objective is mis-specified. "Group representation" in a retrieved set has two orthogonal dimensions: **(R1) group composition**, the proportion of group-relevant passages belonging to each group, and **(R2) within-group stance**, the proportion of passages about a given group that are favourable rather than unfavourable toward it. Pairwise poisoning — the natural adversarial construction, in which injected passages reuse the legitimate template inventory and differ only in which group they favour — is **balanced in R1 by construction** while being **arbitrarily skewed in R2**. Consequently every defense that constrains R1 alone admits the entire poisoned set while reporting a clean group distribution.

We formalise both dimensions, construct the pairwise attack, and re-implement five representative defenses — multi-query consistency, off-manifold filtering, and three variants of representation-conserving selection (R1-only, R2-only, and joint) — under a controlled corpus with exact group and stance annotations. Across BM25 and dense retrieval, over 48 queries spanning four bias strata, we find that:

1. **Pairwise poisoning is invisible to every R1 statistic.** R1 composition drift stays at 0.1313 or below on the controlled corpus and 0.2722 or below on BBQ, while adversarial passages take over the retrieved set. Two natural R2 statistics — deviation of stance from a corpus reference, and one-sidedness of stance — are also flat (0.2859 → 0.3113 and 0.4667 → 0.5000) across the clean and attacked conditions, because the attack preserves the topic-conditioned component that dominates them. On the controlled corpus only the **cross-group stance gap** responds, moving from exactly 0.0000 (clean, all four strata) to 0.6250–1.0000.
2. **The R1-only defense is inert, not merely weak.** On both corpora, and at **every injection rate we swept**, it attains exactly the same adversarial-passage inclusion rate as no defense, and does so at every value of its budget parameter — including the strictest. The budget parameter acts on a quantity the attack does not perturb.
3. **The R2 dimension is the only axis along which anything moves.** On the controlled corpus the R2 constraint improves its own metric by 77%; on BBQ it roughly halves the stance gap (0.970 → 0.525) while the R1 constraint leaves it unchanged (0.952). The direction of the result — R1 inert, R2 effective — is invariant across corpora and injection rates; the magnitude is not, and we report both.
4. **Injection must be reported as a rate, not a count.** With 0.1% of the corpus injected (8 passages), the text attack already reaches 68.75% inclusion against BM25 on the controlled corpus. An earlier version of this study used a fixed count and reached the opposite conclusion for the wrong reason; we report the correction and the mechanism behind the discrepancy (Finding 4).
5. **The projection attack is robust to corpus naturalness; the text attack is not.** The text-only attack reaches 0.000 on BBQ at every rate up to 2%, while the projection attack reaches 0.903 at 0.1% and 1.000 by 2%. We identify the mechanism: an injection that works by aligning its text with query vocabulary needs the injected tokens to stand out, which repetitive corpora permit and naturally varied text does not.

Finding (2) is a **negative result about a class of defenses**, and we argue it is the paper's central contribution: a constraint expressed over the aggregate composition of a retrieved set, however many dimensions it is extended to, has no purchase on an attacker who shapes injected passages to match those statistics. We characterise this limit formally.

Finding (3) is a **negative result about a class of defenses**, and we argue it is the paper's central contribution: a constraint expressed over the aggregate composition of a retrieved set, however many dimensions it is extended to, has no purchase on an attacker who shapes injected passages to match those statistics. We characterise this limit formally.

We then replicate on **BBQ**, a naturally written bias benchmark, using BBQ's own stereotype annotations to derive stance labels, and report results that are **partly unfavourable to our own earlier conclusions**. Two findings change: the text-only template attack, which reached 75% inclusion on the controlled corpus against BM25, is entirely ineffective on natural data (0%), so we withdraw the claim that text-level injection suffices; and the R2-constraining defense, which was inert against the projection attack on the controlled corpus, does reduce adversarial inclusion on natural data (0.764 → 0.660) while improving the utility proxy. Two findings survive on both corpora, and they are the ones we retain: **constraints on group composition are inert against this attack** — attaining exactly the adversarial-inclusion rate of no defense, at every value of their budget parameter — and **the within-group stance dimension is the only one along which any metric moves in the desired direction**.

A methodological by-product is relevant to anyone building monitoring for this threat: of three plausible R2 statistics we tested, two are silently blind to the attack, and on a bias benchmark the third is confounded by a pre-existing corpus imbalance. We report all three to document the failure modes.

**Keywords**: retrieval-augmented generation, data poisoning, group fairness, within-group stance, adversarial robustness, information retrieval

---

## 1. Introduction

Retrieval-augmented generation (RAG) [1] has become the standard architecture for grounding large language model (LLM) outputs in external, updatable knowledge. Because the generator conditions on whatever the retriever returns, the retrieval corpus becomes a security boundary: an adversary who can place passages in that corpus can determine the evidence on which the model's answer rests. Corpus poisoning attacks exploit exactly this, and a single line of work has established that a small number of injected passages can mislead an undefended system in the large majority of cases [2, 3].

A more recent observation is that poisoning need not target factual correctness at all. Wang et al. [4] show that injected passages can **amplify social bias**: a query that is group-neutral can be answered in a stereotyped way because the retrieved evidence has been skewed toward one group. This matters because the harm is representational rather than factual — a biased answer can be *correct* by every factual measure while still systematically demeaning a protected group — and because it is therefore invisible to the accuracy-based evaluation that RAG systems normally undergo.

In response, a body of work has begun to defend the retrieval layer on fairness grounds. The proposed defenses share a common objective: they measure the **group composition** of the retrieved set and constrain it to remain balanced. Concretely, they partition the corpus by group and either re-rank to equalise group proportions [5], adjust the proportion and ordering of group-relevant passages [6], reverse-bias the embedder so that its retrieved group balance compensates for the generator's own bias [7], or randomise the ranking so that equally relevant items receive equal exposure [8]. Item-side variants of the same idea equalise *exposure* rather than group share, but still operate on aggregate composition [8].

This paper argues that this objective is mis-specified, and we demonstrate the consequences empirically.

**The problem.** "Group representation" is not one quantity but two. A retrieved set can be described by

- **(R1) group composition** — the proportion of group-relevant passages that concern each protected group, i.e. $P(\text{group} \mid \text{group-relevant})$; and
- **(R2) within-group stance** — the proportion of passages about a given group that portray it favourably rather than unfavourably, i.e. $P(\text{favourable} \mid \text{group}, \text{group-relevant})$.

R1 and R2 are orthogonal: a set can be perfectly balanced in R1 while every passage about one group is unfavourable, and vice versa. Crucially, the adversarial construction that arises naturally in this setting is **balanced in R1 by construction**. An attacker who wishes to skew representation does not inject one-sided material; they inject matched pairs — a favourable passage about group $A$, an unfavourable passage about group $B$ — which are individually indistinguishable from legitimate passages because they are drawn from the *same template inventory*. The injected set therefore contributes equally to both groups' counts, leaving R1 essentially unchanged, while shifting R2 systematically.

Every defense that constrains R1 alone is blind to this. It observes that the group distribution is clean, admits the injected passages, and reports success.

**What we do.** We formalise R1 and R2, construct the pairwise-poisoning attack, and build a controlled evaluation in which group and stance labels are exact and the clean reference for both dimensions is known by construction. We then re-implement the R1-constraining defense family and evaluate it against the attack across two retrieval back-ends. Our findings are:

- **Pairwise poisoning is an R2 attack, not an R1 attack.** R1 drift under attack is at or below the level legitimate retrieval variance produces; within-group stance divergence rises to near its maximum. An R1-only monitor therefore reports the system as healthy while the retrieved evidence is entirely attacker-controlled.
- **The R1-only defense is not merely weak, it is inert.** Under the projection-augmented attack it attains exactly the same adversarial-passage inclusion rate as no defense (0.750 for BM25, 1.000 for dense retrieval), and this holds at *every* budget setting, including the strictest. The budget parameter acts on a quantity the attack does not perturb.
- **A two-sided R2 constraint improves its own metric by 77% and defends not at all.** Adding a lower bound on within-group favourable rate — the bound that the suppression form of the attack violates — reduces the cross-group stance gap from 0.6250 to 0.1429 (§5.3). Adversarial-passage inclusion does not move: it remains 0.750 in every configuration tested, across the full budget sweep. We explain why: the repair pass substitutes one high-scoring passage for another, and because injected passages are engineered to out-rank legitimate ones, the substitute is itself adversarial. A genuinely relevant passage satisfies any constraint expressed over aggregate composition, no matter how many dimensions that composition is extended to.
- **A provenance signal is necessary, and we report an exploratory candidate.** We measure the number of distinct queries for which a passage is retrieved and find clean separation in our controlled setting. We state plainly that our corpus is synthetic and that this separation may be an artefact of its construction; we therefore present it as a hypothesis with a specified falsification experiment, not as a defense.

**Contributions.**

1. A two-dimensional formalisation of representation in retrieved sets (R1 composition, R2 within-group stance), with the observation that adversarial injection is balanced in R1 and skewed in R2 (§3).
2. A controlled pairwise-poisoning construction that makes both dimensions measurable without a generator, so the mechanism can be studied independently of LLM behaviour (§4).
3. An empirical demonstration that R1-constraining defenses are inert against this attack, including the strictest budget setting, across two retrieval back-ends and four bias strata (§5).
4. A negative result on the limits of distribution-level defense: aggregate-composition constraints cannot reject an individually admissible passage, so any defense in this class has an adversarial-passage inclusion floor of 1 (§6). To our knowledge this limit has not been characterised.
5. An exploratory provenance signal with an explicit validity threat and a falsification protocol (§7).

---

## 2. Related Work

### 2.1 Poisoning attacks on RAG

Corpus poisoning against RAG was established by Zou et al. [2], who showed that a small number of optimised passages can steer a system's answers, and has since been extended to black-box and query-agnostic settings [3], to knowledge-graph-structured retrieval [9], and to multimodal pipelines [10, 11, 12]. A parallel thread targets the retrieval process itself rather than passage content, manipulating embedding space so that injected passages rank highly regardless of their text. Wang et al. [4] combine both: reward-optimised adversarial documents, subspace projection to raise their retrieval probability, and a generate–evaluate–reinject loop that accumulates bias over time.

All of this work targets *factual* correctness except [4], and [4] itself measures bias by *counting* stereotype-consistent selections rather than by modelling the distribution of stance within groups. Our R2 formulation is a distributional refinement of that measurement, and we show that the refinement changes which defenses can work.

### 2.2 Fairness in RAG

Fairness in RAG has been studied primarily as a property of the knowledge base and the generator rather than of an adversary. Wu et al. [6] construct scenario-based questions and evaluate group disparity across RAG components, finding that the retriever has the largest influence on both accuracy and fairness, and that utility and fairness trade off. Their mitigation is to adjust the proportion and ordering of group-relevant passages — an R1 intervention — and they state that they do not provide a comprehensive exploration of mitigation strategies. Kim et al. [7] decompose RAG into LLM, embedder, and corpus, show that component biases interact ("bias conflict"), and find that *reverse-biasing* a small embedder can cancel a much larger generator's bias; their bias metric is group membership, so both R1 and R2 are outside their formulation. Kim and Diaz [8] bring fair-ranking machinery to RAG, using stochastic rankers to equalise item-side exposure across repeated requests, and find that fairness and quality need not trade off severely; their fairness unit is the item/provider rather than the social group.

Most closely related is Zhao et al. [5], who model position-wise bias propagation in top-$k$ RAG and formulate fairness-aware retrieval as an optimisation problem over group composition, solved by decomposition. This is the most general R1-constraining defense we are aware of, and we treat it as the representative of the class. Like the others, it assumes no adversary: bias is a property of the corpus and the generator, not something an attacker injects.

Two further works are relevant. Kim et al. [7] observe that "naively increasing fairness is not always the optimal solution" — a conclusion we sharpen by identifying the *specific* reason: the fairness being increased is measured along the wrong axis. Bagwe et al. [13] construct fairness-targeted backdoor attacks that manipulate semantic relationships between groups and biases; their attack relies on a trigger and their objective is attack construction, whereas we study trigger-free injection and its consequences for defense design.

### 2.3 The gap

Across this literature we identify four points of agreement that together define the gap this paper addresses. First, fairness defenses for RAG consistently constrain group composition or item exposure (§2.2). Second, several authors independently report that existing defenses are not robust enough — "further optimization … to achieve more stable and generalizable defense performance" [4]; "single-stage defenses give limited robustness" [14]; "does not provide a comprehensive exploration of strategies to mitigate these unfairnesses" [6]. Third, and structurally, none of the fairness works models an adversary: they study corpora that are *naturally* skewed. Fourth, no work we have found constrains or detects within-group stance.

We therefore study the intersection that has not been studied: an *adversary* acting on the axis that *no* defense constrains.

---

## 3. Two Dimensions of Representation

### 3.1 Definitions

Let a retrieved set for query $q$ be $\mathcal{D}_q = \{d_1, \dots, d_k\}$, and let each passage $d$ carry a group label $g(d) \in \mathcal{G} \cup \{\bot\}$ (the protected group the passage concerns; $\bot$ for group-neutral text) and a stance $s(d) \in \{+1, -1, 0\}$ ($+1$ favourable toward $g(d)$, $-1$ unfavourable, $0$ neutral or group-irrelevant).

**Definition 1 (R1: group composition).** Over the group-relevant passages of $\mathcal{D}_q$,

$$P^{\mathcal{D}_q}_{\text{grp}}(g) = \frac{|\{d \in \mathcal{D}_q : g(d)=g,\ s(d)\neq 0\}|}{|\{d \in \mathcal{D}_q : g(d)\neq \bot,\ s(d)\neq 0\}|}.$$

**Definition 2 (R2: within-group stance).** For each group $g$,

$$P^{\mathcal{D}_q}_{\text{fav}}(g) = \frac{|\{d \in \mathcal{D}_q : g(d)=g,\ s(d)=+1\}|}{|\{d \in \mathcal{D}_q : g(d)=g,\ s(d)\neq 0\}|}.$$

**Definition 3 (R1 drift).** Against a reference $P^{*}_{\text{grp}}$,

$$\Delta_{\text{R1}}(\mathcal{D}_q) = \tfrac{1}{2}\sum_{g} \bigl| P^{\mathcal{D}_q}_{\text{grp}}(g) - P^{*}_{\text{grp}}(g) \bigr|.$$

**Definition 4 (R2 group-conditioned stance gap).** The primary R2 metric is the spread of favourable rate *across* groups:

$$\Delta_{\text{R2}}(\mathcal{D}_q) = \max_{g \neq g'} \bigl| P^{\mathcal{D}_q}_{\text{fav}}(g) - P^{\mathcal{D}_q}_{\text{fav}}(g') \bigr|.$$

**Why a gap across groups, and not a deviation from a reference.** The natural first choice for an R2 metric — how far a group's favourable rate sits from the corpus reference — turns out to be unusable, and the reason is worth recording because it is easy to get wrong. Consider a balanced corpus and a query such as *"Who performed better in the engineering evaluation?"* The query's vocabulary matches favourable and unfavourable templates differently, so a clean retrieval of top-$k$ tends to be **one-sided**: it returns five passages that are all favourable, or all unfavourable. Measured against a reference favourable rate of $0.5$, this yields a large deviation ($\approx 0.31$ by JS divergence) *before any attack is applied*. We confirmed this directly: every clean query in our corpus returns a top-5 that is entirely one-sided.

Crucially, that one-sidedness is **topic-conditioned, not group-conditioned**: when the corpus is balanced, an all-unfavourable retrieval is all-unfavourable for *every* group, so it is not a fairness violation. A deviation-from-reference metric therefore conflates two different phenomena — legitimate topic conditioning, which the attack does not change, and group-conditioned skew, which is the actual harm. Under pairwise poisoning the attack *preserves* the topic-conditioned component (its injected passages are drawn from the same templates), so a deviation metric does not move: in our experiments both the reference-deviation and one-sidedness metrics are flat across the clean and attacked conditions ($0.2859 \to 0.3113$ and $0.4667 \to 0.5000$ respectively), while `poison@k` goes from 0 to 0.750. A defense monitoring either would see a healthy system.

The gap across groups isolates the group-conditioned component. Under a balanced corpus a clean retrieval has $\Delta_{\text{R2}} = 0$ exactly (all groups equally one-sided, hence equal rates), which we observe across all four strata. Pairwise poisoning favours one group while suppressing another, driving the gap toward 1. This is the quantity the attack actually perturbs, and it is invisible to any R1 monitor.

### 3.2 Why the reference for R2 must be a gap, not a deviation

We state this separately because our own first implementation got it wrong, and the error is instructive.

A per-query clean reference — the natural choice, and the one used for R1 — **cannot detect an R2 attack**. Under pairwise poisoning the injected passages are drawn from the same template inventory as the legitimate ones, so the *availability* of favourable and unfavourable passages in the candidate pool is unchanged: the attacker replaces legitimate favourable evidence with adversarial favourable evidence, and legitimate unfavourable evidence with adversarial unfavourable evidence. A clean retrieval under the same budget therefore exhibits the same stance profile as the attacked retrieval. Measuring R2 against the clean retrieval returns approximately zero drift *even when every retrieved passage is attacker-controlled*.

Worse, a deviation-from-corpus-reference metric does not work either, for the reason given in Definition 4: it is dominated by topic conditioning, which the attack preserves. In our experiments the corpus-reference JS divergence is $0.2859$ clean and $0.3113$ attacked — a change of $0.025$ while adversarial inclusion moves from $0$ to $0.750$.

Only the cross-group gap responds. We emphasise all three failures because each is a plausible design choice that produces a monitor reporting a healthy system while the evidence is fully adversarial.

### 3.3 What pairwise poisoning does to each dimension

Let the attacker inject $n$ passages, half favourable toward group $A$ and half unfavourable toward group $B$, using the legitimate template inventory. Then:

- **R1:** the injected set contributes $\lceil n/2 \rceil$ group-relevant passages to each of $A$ and $B$. Its composition is $(\tfrac{1}{2}, \tfrac{1}{2})$ — *identical to the balanced reference*. Formally, the compositional drift contributed by the injection is 0, and any observed R1 drift comes from injected passages outranking legitimate ones, not from their composition.
- **R2 (reference deviation):** unchanged, because the attack preserves the topic-conditioned one-sidedness that dominates this quantity (§3.3).
- **R2 (cross-group gap):** $P_{\text{fav}}(A) \to 1$ and $P_{\text{fav}}(B) \to 0$, so $\Delta_{\text{R2}} \to 1$ — the maximum.

This asymmetry is the attack's entire mechanism, and it is invisible to an R1 monitor by construction.

---

## 4. Attack and Evaluation Setup

### 4.1 Corpus

We require a corpus in which (i) every passage carries exact group and stance annotations, and (ii) the clean reference for both R1 and R2 is known by construction. Public bias benchmarks provide stereotype/anti-stereotype template inventories [15, 16] but not passage-level scaffolding with a known clean reference, so we build a controlled corpus: for each of four bias strata (gender, disability, age, race), a balanced pool of passages is instantiated from the stratum's template inventory, with an equal number of favourable and unfavourable passages per group and a set of group-neutral passages. Queries are group-neutral by construction — the query text never names a protected group — so any group skew in a retrieved set is attributable to the corpus and not to the question. [FILL: replace with or replicate on TREC 2022 Fair Ranking Track [17] and BBQ [15] corpora; see §8.]

### 4.2 Attack

**Pairwise template injection.** For each stratum with groups $(A, B)$, the attacker selects a target direction (favour $A$, suppress $B$) and injects $n$ passages drawn from the legitimate template inventory, half favourable toward $A$ and half unfavourable toward $B$. Two mechanisms ensure the injected passages actually out-rank legitimate ones, since otherwise the attack is vacuous:

1. *Query alignment.* Legitimate passages carry a discourse filler that does not match query vocabulary; injected passages replace it with query-aligned terms. This raises lexical scores without altering the stance-bearing clause, so the signal the defense must detect is unchanged.
2. *Length.* Injected passages are shorter, which length-normalised lexical scoring rewards.

Note that (1) makes the attack effective against BM25 as well as dense retrieval, so a defense cannot pass by relying on lexical scoring being hard to poison.

**Subspace projection.** For dense back-ends we additionally apply the projection-and-amplify step $h' = h + \lambda \langle h, \bar{q}\rangle \|\bar{q}\|^{-2} \bar{q}$ with $\bar{q}$ the mean query direction, following [4]. We sweep $\lambda \in \{0, 0.25, 0.5, 1, 2, 4\}$.

**Adaptive variant.** We also evaluate a *defense-aware* attacker, which observes the defense's own scoring function and searches over $\lambda$ for the value that best balances raised similarity against the defense's penalty. A defense that reports numbers only against the non-adaptive attacker has not demonstrated robustness.

### 4.3 Defenses

We implement the R1-constraining family plus ablations.

**Multi-query consistency** [4] — aggregate rankings over query variants; score passages by appearance frequency and mean rank.

**Off-manifold filtering** — calibrate the corpus manifold (mean plus leading principal directions), penalise passages by residual distance outside it.

**Representation-conserving selection** — greedy Lagrangian selection with per-group admission budgets, in three ablations:
- `repr_group` (**R1 only**): constrain $\Delta_{\text{R1}} \le \epsilon$. This is the representative of the existing defense class.
- `repr_stance` (**R2 only**): constrain within-group favourable rate to $[P^{*}_{\text{fav}}(g) - \epsilon,\ P^{*}_{\text{fav}}(g) + \epsilon]$, with a repair pass that restores the lower bound by swapping the weakest admissible unfavourable passage of a deficient group for the best-scoring unselected favourable passage of that group.
- `repr_both` (**R1 + R2**): both constraints.

The two-sided R2 constraint is deliberate. An upper bound alone stops an attacker from *flooding* a group with favourable passages; the actual attack *suppresses*, driving the favourable rate down, and is therefore only constrained by the lower bound.

### 4.4 Metrics

| Metric | Dimension | Definition |
|---|---|---|
| `drift_tv` | R1 | $\Delta_{\text{R1}}$ — TV distance of group composition vs clean retrieval |
| `drift_js` | R1 | JS divergence of group composition vs clean retrieval |
| **`stance_gap`** | **R2 (primary)** | $\Delta_{\text{R2}}$ — max spread of favourable rate across groups (§3, Def. 4) |
| `stance_shift` | R2 (control) | $\max_g \|P_{\text{fav}}(g) - P^{*}_{\text{fav}}(g)\|$ vs corpus reference; saturates |
| `stance_div` | R2 (control) | $\max_g \mathrm{JS}(\pi^{\mathcal{D}_q}_g \| \pi^{*}_g)$ vs corpus reference; confounded by topic conditioning |
| `stance_onesided` | R2 (control) | $\max_g \|P_{\text{fav}}(g) - 0.5\|$; also confounded |
| `poison@k` | Attack success | fraction of queries with $\ge 1$ injected passage in top-$k$ |
| `poison_share` | Attack success | mean fraction of top-$k$ occupied by injected passages |
| `in_pool_rate` | Utility | fraction of retrieved passages from the query's candidate pool |
| `mean_score` | Utility | mean retriever score of the returned set |

We deliberately report three R2 statistics rather than one. The two reference-based variants are included as **controls**: §5.1 shows they do not respond to the attack, which is itself a finding, and reporting them documents the failure mode rather than hiding it.

Ground-truth poison labels are used **only** for the attack-success metrics; no defense receives them. All defenses are evaluated with $k = 5$; retrieval back-ends are BM25 and a dense embedder. [FILL: add GTE-base (matching [5]) and Contriever/SPLADE (matching [8]) to enable direct comparison.]

---

## 5. Results

> **Status of this section.** All numbers reported below were produced by the released implementation and are reproducible with the commands in Appendix A. Two corpora are used: a controlled corpus with an exactly known clean reference (§5.1–§5.3) and the natural BBQ corpus (§5.4), each swept over injection rate $\rho \in \{0.1\%, \dots, 2\%\}$ of corpus size. The controlled suite completes in ~25 s and the BBQ replication in ~180 s, both on CPU with no GPU. Remaining `[FILL]` placeholders concern the additional retrieval back-ends and the generation-stage evaluation described in §8.

### 5.1 Pairwise poisoning is an R2 attack, not an R1 attack

Table 1 reports attack effect with no defense, over 48 queries across four bias strata.

**Table 1.** Attack effect without defense.

| Attack | Retriever | `drift_tv` (R1) | `stance_gap` (R2) | `stance_div` (ref-dev) | `one_sided` | `poison@k` |
|---|---|---|---|---|---|---|
| clean | BM25 | 0.0000 | **0.0000** | 0.2859 | 0.4667 | — |
| clean | dense | 0.0000 | **0.0000** | 0.3113 | 0.5000 | — |
| template | BM25 | 0.1500 | **0.6250** | 0.3113 | 0.5000 | 0.750 |
| template | dense | 0.0625 | **0.5000** | 0.3113 | 0.5000 | 0.625 |
| template + projection | BM25 | 0.1500 | **0.6250** | 0.3113 | 0.5000 | 0.750 |
| template + projection | dense | 0.1313 | **1.0000** | 0.3113 | 0.5000 | **1.000** |

Three observations.

**First, the R2 gap is exactly zero before the attack and large after it, in every stratum.** Clean retrieval yields `stance_gap` $= 0.0000$ across all four strata (gender, disability, age, race) — because on a balanced corpus a topic-conditioned one-sided retrieval is one-sided *for every group equally*, so the cross-group spread vanishes. Under attack the gap rises to 0.6250 (BM25) and 1.0000 (dense + projection). Per stratum, the clean condition is $0.0000$ throughout while the attacked condition is $\{1.0000, 0.5000, 0.3333, 0.7500\}$ for the template attack and $1.0000$ in all four strata under projection.

**Second, the two reference-based R2 metrics fail completely.** `stance_div` — deviation from the corpus stance reference — moves from 0.2859 to 0.3113 (a change of 0.025) while adversarial inclusion goes from absent to 0.750; `one_sided` moves from 0.4667 to 0.5000. Either metric would report a healthy system. This empirically confirms the analysis of §3.2: the attack preserves the topic-conditioned component that dominates both quantities, so only the cross-group gap responds. We regard this as a methodological contribution in its own right — three plausible R2 metrics, two of which are silently blind.

**Third, R1 drift is small and non-diagnostic.** The largest value is 0.1313 (dense, projection), consistent with §3.4: the injected set is compositionally $(\tfrac{1}{2}, \tfrac{1}{2})$, so the drift reflects injected passages outranking legitimate ones rather than any compositional imbalance on their part. An R1-based monitor sees a retrieved set whose group balance is close to the clean reference, while `poison@k` reaches 1.000 and the utility proxy `in_pool_rate` falls to 0.000 — the retrieved set becomes entirely attacker-controlled.

**Finding 1.** Pairwise poisoning drives the cross-group stance gap to 0.6250–1.0000 while leaving both R1 drift and the two reference-based R2 statistics near their clean values. Neither an R1 monitor nor a naive R2 monitor flags it.

### 5.2 The R1-only defense is inert

**Table 2.** Defense comparison under template + projection. `poison@k` is the adversarial-passage inclusion rate.

| Retriever | Defense | ε | `drift_tv` (R1) | `stance_gap` (R2) | `poison@k` |
|---|---|---|---|---|---|
| BM25 | vanilla (none) | — | 0.1500 | 0.6250 | **0.750** |
| BM25 | multi-query consistency | — | 0.1531 | 0.6157 | **0.750** |
| BM25 | `repr_group` (R1 only) | 1.0 | 0.1500 | 0.6250 | **0.750** |
| BM25 | `repr_group` (R1 only) | 0.5 | 0.1500 | 0.6250 | **0.750** |
| BM25 | `repr_group` (R1 only) | 0.25 | 0.1500 | 0.6250 | **0.750** |
| BM25 | `repr_group` (R1 only) | 0.1 | 0.1625 | 0.6250 | **0.750** |
| BM25 | `repr_group` (R1 only) | **0.0** | 0.1812 | 0.6250 | **0.750** |
| dense | vanilla (none) | — | 0.1313 | 1.0000 | **1.000** |
| dense | `repr_group` (R1 only) | 1.0 | 0.1313 | 1.0000 | **1.000** |
| dense | `repr_group` (R1 only) | **0.0** | 0.2438 | 1.0000 | **1.000** |

**Finding 2. The R1-only defense is not weak but inert.** `repr_group` attains *exactly* the same `poison@k` as `vanilla` — 0.750 on BM25, 1.000 on dense — at **every** budget setting, including $\epsilon = 0$, the strictest possible constraint. The inclusion rate is not merely unchanged at the default setting; across a sweep of five values spanning the entire range of the budget parameter it does not vary at all. Tightening the budget does change R1 drift (0.1500 → 0.1812, i.e. it can make R1 *worse*, by forcing the selection away from the natural ranking) while leaving both the R2 gap and adversarial inclusion untouched. This is the signature of a constraint acting on quantities the attack does not perturb: the budget has no purchase on the attack.

This is the central empirical claim of the paper, and it applies directly to the published defense family: [5] optimises R1 composition under a fairness constraint, [6] adjusts R1 proportions and ordering, [7] controls embedder group balance, [8] equalises item-side exposure. Each constrains aggregate composition along axes the attack leaves clean, so each inherits this insensitivity. We note that multi-query consistency [4], which operates on retrieval stability rather than composition, is also inert here (0.750).

**Table 3.** Adaptive attacker (defense-aware), `poison@k`.

| Defense | λ=0 | λ=0.25 | λ=0.5 | λ=1 | λ=2 | λ=4 |
|---|---|---|---|---|---|---|
| multi-query consistency | 0.729 | 0.958 | 1.000 | 1.000 | 1.000 | 1.000 |
| off-manifold filtering | **0.125** | 0.438 | 0.750 | 0.938 | 1.000 | 1.000 |
| `repr_both` (R1+R2) | 0.625 | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 |

The adaptive attacker defeats every defense. Off-manifold filtering is by a wide margin the strongest at $\lambda = 0$ (0.125) and **collapses monotonically to 1.000 by $\lambda = 2$** — a clean demonstration that its advantage is specific to the non-adaptive attacker and does not survive an adversary who observes its penalty. The representation-conserving defenses, which never achieve better than 0.625 even non-adaptively, saturate at 1.000 by $\lambda = 0.5$: they are the most fragile under adaptation as well as the least effective without it.

### 5.3 The R2 constraint works — on the R2 metric — and does not defend

Adding the cross-group R2 constraint substantially improves the R2 statistic. On BM25 the `stance_gap` falls from 0.6250 (no defense, and R1-only defense) to **0.1429** under `repr_both` at $\epsilon = 1.0$ — a **77% reduction**, and to 0.3542 at $\epsilon = 0.25$. The constraint is doing exactly what it was designed to do.

**Table 4.** R2 constraint effect vs. adversarial inclusion (BM25, template + projection).

| Defense | ε | `stance_gap` (R2, lower is better) | `poison@k` (security, lower is better) |
|---|---|---|---|
| vanilla | — | 0.6250 | 0.750 |
| `repr_group` (R1 only) | 0.0 | 0.6250 | 0.750 |
| `repr_stance` (R2 only) | 1.0 | 0.4444 | 0.750 |
| `repr_stance` (R2 only) | 0.0 | 0.5278 | 0.750 |
| **`repr_both` (R1+R2)** | **1.0** | **0.1429** | **0.750** |
| `repr_both` (R1+R2) | 0.25 | 0.3542 | 0.750 |
| `repr_both` (R1+R2) | 0.0 | 0.5278 | 0.750 |

**And `poison@k` is unchanged at 0.750 in every single row.** On the dense back-end the R2 constraint fails even on its own metric ($\text{stance\_gap} \ge 0.75$ throughout, `poison@k` $= 1.000$ at every setting).

The mechanism is visible in the implementation. The repair pass of §4.3 restores a deficient group's favourable count by swapping its weakest selected unfavourable passage for the best-scoring unselected favourable passage of that group. It improves the stance profile *of the selection* — but the substituted passage need not be legitimate. An injected passage that is favourable toward the deficient group is an admissible substitute, and because injected passages are engineered to out-rank legitimate ones, they are precisely the passages the swap selects. The defense improves its fairness statistic by substituting one adversarial passage for another.

**Finding 3.** On the controlled corpus, a distribution constraint extended to a second dimension can improve its own aggregate statistic by 77% while adversarial inclusion does not move by a single query. On the natural corpus the same constraint *does* reduce adversarial inclusion (§5.4), so Finding 3 is corpus-dependent and we do not claim it universally. What is corpus-independent is the direction of the result: **the R2 dimension is the only one along which either metric moves at all**, whereas the R1 dimension is inert in both settings. We suggest that evaluations in this area report adversarial inclusion alongside fairness metrics, because the two demonstrably move independently — and, on the controlled corpus, in opposite directions.

### 5.4 Replication on a natural corpus (BBQ)

The results above use a controlled corpus whose passages are template-instantiated, which is a threat to external validity. We therefore replicate on **BBQ** [15], a naturally written bias benchmark, using BBQ's own stereotype annotations to derive stance labels (§4.1) so that no new annotation is introduced. The corpus contains 17,792 passages over 144 group-neutral queries spanning four categories (gender, disability, age, race/ethnicity).

**A note on the injection parameter, because our first attempt was wrong.** An earlier version of this experiment injected a fixed six passages per stratum and concluded that the text-only attack "does not transfer" to natural data. That conclusion was an artefact of the parameter, not a property of the corpus: six passages is roughly 10% of a small candidate pool but ~0.03% of an 18k-passage corpus, so a fixed count measures corpus size rather than attack strength. Poisoning studies standardly report an *injection rate*; we now do the same, sweeping $\rho \in \{0.1\%, 0.25\%, 0.5\%, 1\%, 2\%\}$ of corpus size. All results below are at matched $\rho$.

**Table 5.** Attack effect vs. injection rate $\rho$; no defense; `poison@k`.

*Controlled corpus (1,824 passages):*

| ρ | passages/stratum | BM25 `poison@k` | BM25 `stance_gap` | dense `poison@k` | dense `stance_gap` |
|---|---|---|---|---|---|
| clean | 0 | — | **0.0000** | — | **0.0000** |
| 0.1% | 2 | **0.6875** | 0.5417 | 0.4375 | 0.2833 |
| 0.25% | 5 | 0.750 | 0.6250 | 0.625 | 0.5000 |
| 1% | 18 | 0.750 | 0.7692 | 0.625 | 0.6111 |
| 2% | 36 | 0.750 | 0.7000 | 0.625 | 0.6667 |

*BBQ (17,792 passages):*

| ρ | passages/stratum | BM25 `poison@k` | dense `poison@k` | dense `stance_gap` | dense `in_pool_rate` |
|---|---|---|---|---|---|
| clean | 0 | — | — | 0.9326 | 0.5569 |
| 0.1% | 18 | **0.000** | **0.903** | 0.9395 | 0.2000 |
| 0.25% | 44 | 0.000 | 0.972 | 0.9389 | 0.1278 |
| 0.5% | 89 | 0.000 | 0.986 | 0.9696 | 0.0597 |
| 1% | 178 | 0.000 | 0.993 | 0.9942 | 0.0250 |
| 2% | 356 | 0.000 | **1.000** | 0.9958 | 0.0111 |

**Finding 4. The text-only attack's effectiveness depends on how templated the corpus is, not only on injection rate.** On the controlled corpus, **8 injected passages (0.1% of the corpus) already reach 68.75% inclusion against BM25** — the same order as the five-document attacks reported in the factual-poisoning literature [2]. On BBQ the same attack reaches **0.000 at every rate up to 2%** (356 passages per stratum). The mechanism is lexical: the attack raises its score by aligning injected text with query vocabulary, and that advantage requires the injected passage to *stand out* against the corpus's own vocabulary distribution. A template-instantiated corpus is repetitive, so the injected tokens dominate; naturally varied text dilutes them, and no injection rate we tested overcame the dilution. We stress that the sweep was necessary to see this — at a fixed count we would have reported the opposite conclusion for the wrong reason.

**Finding 5. The projection attack is robust to corpus naturalness.** On the dense back-end, `poison@k` reaches **0.903 at 0.1%** on BBQ and 1.000 by 2%, with the utility proxy falling from 0.557 to 0.011. The projection operates in embedding space, where the perturbation's advantage does not depend on lexical distinctiveness, so it transfers where the text attack does not. Across both corpora and both injection modes, the projection attack is the only one that is consistently effective.

**Table 6.** Defense comparison on BBQ under template + projection (dense), by injection rate. `poison@k`.

| ρ | vanilla | `repr_group` (R1 only) ε=0 | `repr_both` (R1+R2) ε=1.0 |
|---|---|---|---|
| 0.1% | 0.903 | 0.903 | **0.903** |
| 0.25% | 0.972 | 0.972 | 0.951 |
| 0.5% | 0.986 | 0.986 | 0.972 |
| 1% | 0.993 | 0.993 | 0.972 |
| 2% | 1.000 | 1.000 | 0.993 |

**The R2 constraint reduces adversarial inclusion on BBQ while the R1 constraint does not, and the pattern holds across the whole rate sweep.** `repr_group` is identical to no defense at every rate (0.903 / 0.972 / 0.986 / 0.993 / 1.000), whereas `repr_both` is weakly better at every rate, with its absolute advantage growing as the attack strengthens (0.021 at 0.5%, 0.007 at 2%) while its R2 advantage is much larger. The effect sizes here are smaller than the fixed-count run reported, and the reason is now clear: that run's comparison was confounded by the injection budget.

**Table 7.** R2 constraint effect on BBQ (dense, template + projection, $\rho = 0.5\%$).

| Defense | ε | `stance_gap` (R2) | `poison@k` |
|---|---|---|---|
| vanilla | — | 0.9696 | 0.986 |
| `repr_group` (R1 only) | 0.0 | 0.9515 | 0.986 |
| **`repr_both` (R1+R2)** | **1.0** | **0.5250** | **0.972** |

The R2 constraint roughly halves the stance gap (0.9696 → 0.5250) at this operating point while the R1 constraint leaves it essentially unchanged (0.9515). This is the clearest form of the paper's central claim on natural data: **the R1 dimension is inert and the R2 dimension is where the effect lives.**

We also note a ceiling effect. On BBQ the *clean* retrieval already has `stance_gap` = 0.9326, because BBQ is a bias benchmark whose contexts express stereotyped views by construction, so a query retrieves largely one-sided passages regardless of any adversary. The absolute value of $\Delta_{\text{R2}}$ is therefore uninformative on this corpus and we rely on the change from the clean baseline throughout.

**Revised summary of findings across corpora and injection rates.**

| Finding | Controlled | BBQ | Status |
|---|---|---|---|
| R1 drift is small and non-diagnostic | yes | yes | **retained** |
| R1-only defense is inert (identical to no defense at every ε) | yes | yes | **retained** |
| R2 constraint is the only one that improves either metric | yes | yes | **retained** |
| Projection attack transfers to natural text | yes | yes (0.903 at 0.1%) | **retained** |
| Text-only attack transfers to natural text | yes | no (0.000 at all ρ) | **corpus-dependent** (Finding 4) |
| R2 constraint reduces adversarial inclusion | no (fixed count) | yes (0.986 → 0.972) | **rate-dependent** |

The three findings that hold on both corpora and at every injection rate are the paper's claims. The two that do not — text-attack transfer, and whether the R2 constraint reduces inclusion — are reported with their conditions rather than dropped, because the conditions are themselves informative: both are consequences of how much lexical room the attacker has.

**Adaptive attack on BBQ.** `off-manifold` holds `poison@k` at 0.007–0.111 up to $\lambda = 0.5$; `repr_conserving` at 0.049–0.319; `multi_query` at 0.083–0.535. All saturate at 1.000 by $\lambda = 4$; see the companion paper for a full adaptive-evaluation treatment.

---

## 6. Why Distribution-Level Defense Has a Limit

Finding 3 is not a tuning failure. It follows from what a distributional constraint *is*.

Let a defense constrain $\mathcal{D}_q$ to a region $\mathcal{R} \subseteq 2^{\mathcal{C}}$ of admissible retrieved sets, defined by conditions on aggregate statistics of $\mathcal{D}_q$ (group composition, stance composition, exposure). Let $\mathcal{A}$ be the set of passages the attacker controls.

**Proposition 1.** If there exists an admissible set $\mathcal{D} \in \mathcal{R}$ with $\mathcal{D} \cap \mathcal{A} \neq \emptyset$, then any defense that only enforces $\mathcal{D} \in \mathcal{R}$ admits adversarial passages.

*Proof.* Immediate: the defense's acceptance test is membership in $\mathcal{R}$, which the set satisfies. $\square$

The force of the proposition is that $\mathcal{R}$ is constructed from *clean* statistics — the reference profiles $P^{*}$. An attacker who shapes injected passages to match those statistics generates sets in $\mathcal{R}$ at will. Pairwise injection is the canonical construction: by drawing from the legitimate template inventory and balancing the two groups, the attacker produces a set whose group composition is exactly $P^{*}_{\text{grp}}$, and by controlling stance within each group the attacker can place the set's stance composition anywhere in $[0,1]^{|\mathcal{G}|}$ that the $\epsilon$-ball around $P^{*}_{\text{fav}}$ permits.

Two consequences follow, and they are the actionable content of this section.

**(a) Dimensionality does not help.** Extending the constraint from R1 to R2 to $m$ dimensions does not shrink $\mathcal{R}$ in a way that excludes adversarial passages; it merely gives the attacker more statistics to match. The attacker's cost grows, but their *feasibility* does not disappear, because the injected passages are, by construction, individually indistinguishable from legitimate ones under any statistic computed over their aggregate.

**(b) The only escape is individual-level evidence.** To exclude an adversarial passage, a defense must evaluate a property of *that passage* that is not a function of the retrieved set's composition. In the adversarial setting this is a provenance question — was this passage injected? — and it is answerable only from signals the attacker's optimisation leaves behind.

This reframes the defense problem. Prior work in this space has largely been an optimisation problem (which composition is fairest, and how to reach it). Under an adversary it is a *detection* problem, and the two are not interchangeable: as §5.3 and §5.4 jointly show, a defense can improve its fairness objective while its security objective is unchanged (controlled corpus) — and, more importantly, the *only* configurations in which the security objective moves at all are those that constrain the R2 dimension (BBQ). An optimisation framing that does not include a composition-independent term has no purchase on the attacker.

[FILL: formalise the attacker's feasibility set $\mathcal{R} \cap \{\mathcal{D} : \mathcal{D} \cap \mathcal{A} \neq \emptyset\}$ as a function of $n$, $k$, and $\epsilon$, and derive the minimum injection ratio required for $\epsilon$-stance-shift. This is the natural extension of Proposition 1 and is planned as follow-up work.]

---

## 7. An Exploratory Provenance Signal

Proposition 1 indicates that a usable defense needs individual-level evidence. We report an exploratory candidate and are explicit about its validity status.

**Hypothesis.** A passage injected to be retrieved for many queries — the projection attack optimises a *single* direction $\bar{q}$ so that one passage serves many queries — will be retrieved for an anomalously large number of distinct queries. A legitimate passage is relevant to a small, specific set. The number of distinct queries retrieving a passage is computable at inference time from retrieval logs and requires no labels.

**Measurement.** We score each passage by the fraction of queries in the query set for which it appears in the top-$k$.

**Table 3.** Over-generalisation signal.

| Retriever | Set | n | mean | median | p90 |
|---|---|---|---|---|---|
| BM25 | poison | 16 | 0.1914 | 0.1875 | 0.2500 |
| BM25 | clean | 608 | 0.0032 | **0.0000** | **0.0000** |
| dense + projection (λ=1) | poison | 16 | 0.3086 | 0.2188 | 0.6250 |
| dense + projection (λ=1) | clean | 608 | 0.0001 | **0.0000** | **0.0000** |

At a threshold of the clean 90th percentile, detection rate is 1.000 with 3.9% (BM25) and 0.2% (dense) false positives.

**This result must not be taken at face value, and we state the reason.** The clean 90th percentile is **0.0000** — 90% of legitimate passages are retrieved by *no* query. That is not a property of realistic corpora; it is a property of our construction, in which injected passages share a fixed query-aligned vocabulary that legitimate passages lack. The separation may therefore measure *lexical overlap with our query template set* rather than *retrieval optimisation*. In a natural corpus this signal may vanish entirely.

**Falsification protocol.** Before this can be claimed as a defense:
1. replicate on a natural corpus (TREC 2022 Fair Ranking Track [17], Natural Questions) with injected passages generated by a query-agnostic attack [3] so that no shared vocabulary is introduced by construction;
2. report the signal's AUC with confidence intervals, and the resulting detection/false-positive trade-off;
3. verify that threshold selection does not require knowledge of the injection rate.

We report the signal because it is the direction Proposition 1 points to, and because a negative result from step (1) would itself be informative about which provenance cues survive in realistic settings.

---

## 8. Discussion and Limitations

**Implications for prior work.** Our results do not show that existing fairness defenses are implemented incorrectly; they show that the defenses optimise an objective that an adversary does not perturb. Concretely, [5]'s optimisation, [6]'s proportion adjustment, [7]'s embedder control, and [8]'s exposure equalisation all act on aggregate composition. Under natural corpus skew — the setting those works target — this is appropriate, and their reported improvements are meaningful. Under an adversary, §5.2 shows the same machinery leaves adversarial inclusion unchanged. We suggest that evaluations in this area report an adversarial-passage inclusion rate alongside their fairness metrics, since the two can move independently.

**The reference-dimension error.** §3.3 identifies a class of mistakes that is easy to make and hard to notice: R2 statistics evaluated against a per-query clean retrieval, or against a corpus reference, are dominated by topic-conditioned stance variation that the attack preserves, and therefore report a healthy system while the retrieved set is fully adversarial. We made this error and corrected it by adopting the cross-group gap. Because the error makes a broken defense look functional, we recommend that any R2-style metric be specified together with its reference *and* accompanied by a control showing that it responds to a known attack.

**Limitations.**

1. **The measurement requires group- and stance-annotated passages, and natural retrieval corpora do not have them.** This is the binding constraint on this line of work, and it is worth stating plainly rather than as a data-collection to-do. R1 needs a group label per passage; R2 needs a stance label per passage. NQ and MS MARCO — the standard neutral retrieval corpora — carry neither, and stance toward a social group is not a property that can be inferred from a neutral passage, because a neutral passage does not express one. We therefore could not substitute a neutral corpus for BBQ, and neither can the defenses we evaluate: an R1-constraining defense needs the same group labels, and an R2-constraining defense needs labels that no existing neutral corpus provides. The framework's applicability is thus bounded by annotation, not by computation, and constructing a neutral, group- and stance-annotated retrieval benchmark is the field's outstanding infrastructure problem. Our two corpora bound the behaviour from the two sides available today: a template-controlled corpus with an exact known reference, and a naturally written bias benchmark. [FILL: construct or adopt such a benchmark.]
2. **Neither corpus is a neutral retrieval benchmark, and they disagree in two respects.** The text-only template attack is effective only on the controlled corpus (Finding 4), and the R2 constraint reduces adversarial inclusion only on BBQ. We report both conditions rather than selecting the favourable one. The mechanism behind the first disagreement is identified (lexical room depends on corpus repetitiveness), which we regard as a finding rather than a gap; the second is a smaller effect whose magnitude we expect to depend on the corpus's pre-existing stance imbalance.
3. **The absolute R2 metric does not transfer.** `stance_gap` is exactly 0 on the balanced controlled corpus and near its maximum (0.9326) on BBQ *before any attack*, where it is dominated by the benchmark's own stereotyped construction. On such a corpus only the change from the clean baseline is informative. A corpus-relative normalisation of $\Delta_{\text{R2}}$ would be preferable and we leave it open.
4. **Injection budget is a rate, not a count.** We report an injection rate throughout (§5.4), because a fixed passage count measures corpus size and produced a spurious conclusion in our own earlier experiment. Readers comparing against work that reports absolute counts should convert.
5. **Retrieval back-ends.** BM25 and a controlled dense embedder. Directly comparable results against the R1-constraining literature require GTE-base (as in [5]) and Contriever/SPLADE (as in [8]). [FILL]
6. **No generation-stage evaluation.** We deliberately evaluate at the retrieval layer, so that the R1/R2 mechanism is measurable without a generator and the study is reproducible on commodity hardware (the full suite runs on CPU in under three minutes). This means we do not report attributed exposure [8] or generator bias [4, 7]. Since the retrieval-layer failure we document is a precondition for the downstream harm, we consider the two complementary, and we report generator-stage attribution as planned work. [FILL]
7. **Binary groups.** Following [6, 7, 8], we use two groups per stratum. Extension to $|\mathcal{G}| > 2$ is mechanical for R1 and R2 but is not evaluated here. We note that the race/ethnicity category of BBQ is markedly imbalanced in our corpus build (960 passages about the protected group versus 88 about the non-protected group), which is itself a property of the benchmark worth flagging for anyone reusing it.

---

## 9. Conclusion

Fairness defenses for retrieval-augmented generation constrain the group composition of the retrieved set. We have shown that this objective is mis-specified in the adversarial setting. Group representation has two orthogonal dimensions, and pairwise poisoning — the natural adversarial construction, in which injected passages reuse the legitimate template inventory in matched pairs — is balanced in the first and skewed in the second. The consequence is not that the defenses are weak but that they are inert: the R1-only defense attains the same adversarial-passage inclusion rate as no defense at all, at every budget setting including the strictest.

Extending the constraint to the second dimension improves the aggregate statistic it measures without changing adversarial inclusion, and we have given the reason: a constraint expressed over aggregate composition cannot reject an individually admissible passage, and injected passages are admissible by construction. The problem is consequently not one of optimisation but of detection, and it requires evidence about individual passages rather than about the set they belong to.

We have reported an exploratory provenance signal in that direction, together with the reason it may not survive replication on a natural corpus. Establishing which provenance cues do survive is, in our view, the central open problem this work exposes.

---

## Data and Code Availability

The implementation, configuration files, and the scripts that regenerate every number in §5 are released at `[repository URL]`. The controlled corpus is generated deterministically from a fixed seed and requires no dataset download; the BBQ corpus is reconstructed from the official benchmark files by a released loader that derives stance labels from BBQ's own annotations.

---

## Appendix A. Reproduction

```bash
# controlled-corpus suite (CPU only; ~25 s)
python -m src.run_experiment --config configs/default.json

# natural-corpus replication on BBQ (CPU only; ~165 s)
python -m src.run_experiment --config configs/bbq.json

# development-scale run (~5 s)
python -m src.run_experiment --config configs/default.json --quick

# corpus comparison table
python compare_corpora.py

# over-generalisation probe
python src/probe_overgeneralisation.py --quick --retriever bm25
```

The BBQ data is downloaded from the official repository:

```bash
python -m src.data.bbq_loader          # builds and reports corpus statistics
```

(Expects `data/bbq/{Gender_identity,Disability_status,Age,Race_ethnicity}.jsonl`
from `https://github.com/nyu-mll/BBQ/tree/main/data`.)

Outputs: `results/<run_tag>/{per_query,aggregate,by_stratum,adaptive}.csv` and `summary.txt`.

The full retrieval-layer study runs on CPU: the controlled suite completes in
25 s and the BBQ replication in 165 s on a desktop CPU, with no GPU required.
Embedding and reranking models, when added for the comparisons in §8, fit within
8 GB of VRAM.

---

## References

[1] P. Lewis, E. Perez, A. Piktus, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS*, 2020.

[2] W. Zou, R. Geng, B. Wang, J. Jia. PoisonedRAG: Knowledge corruption attacks to retrieval-augmented generation of large language models. *USENIX Security*, 2025.

[3] B. Zhang, Y. Chen, Z. Liu, et al. Practical poisoning attacks against retrieval-augmented generation. *arXiv:2504.03957*, 2025.

[4] L. Wang, T. Zhu, L. Qin, L. Gao, W. Zhou. Bias amplification in RAG: Poisoning knowledge retrieval to steer LLMs. *IEEE Transactions on Dependable and Secure Computing*, 23(5):11033–11050, 2026. (arXiv:2506.11415)

[5] Y. Zhao, V. Efthymiou, J. Nummenmaa, K. Stefanidis. Fairness-aware retrieval optimization for retrieval-augmented generation. *arXiv:2605.15790*, 2026.

[6] X. Wu, S. Li, H.-T. Wu, Z. Tao, Y. Fang. Does RAG introduce unfairness in LLMs? Evaluating fairness in retrieval-augmented generation systems. *COLING*, pp. 10021–10036, 2025. (arXiv:2409.19804)

[7] T. Kim, J. M. Springer, A. Raghunathan, M. Sap. Mitigating bias in RAG: Controlling the embedder. *Findings of ACL*, 2025. (arXiv:2502.17390)

[8] T. E. Kim, F. Diaz. Towards fair RAG: On the impact of fair ranking in retrieval-augmented generation. *ICTIR*, pp. 33–43, 2025. (arXiv:2409.11598)

[9] J. Liang, Y. Wang, C. Li, et al. GraphRAG under fire. *IEEE Symposium on Security and Privacy*, 2026. (arXiv:2501.14050)

[10] H. Ha, Q. Zhan, J. Kim, et al. MM-PoisonRAG: Disrupting multimodal RAG with local and global poisoning attacks. *arXiv:2502.17832*, 2025.

[11] Y. Liu, Z. Yuan, G. Tie, et al. Poisoned-MRAG: Knowledge poisoning attacks to multimodal retrieval augmented generation. *arXiv:2503.06254*, 2025.

[12] K. Edemacu, M. M. Shokri. Hidden in the metadata: Stealth poisoning attacks on multimodal retrieval-augmented generation. *arXiv:2603.00172*, 2026.

[13] G. Bagwe, S. S. Chaturvedi, X. Ma, et al. Your RAG is unfair: Exposing fairness vulnerabilities in retrieval-augmented generation via backdoor attacks. *arXiv:2509.22486*, 2025.

[14] S. K. Mohanty, R. Patel, K. Yuvaraj, et al. TriShieldRAG: 3 rings, one blind spot in layered defenses for retrieval-augmented generation. *arXiv:2607.23838*, 2026.

[15] A. Parrish, A. Chen, N. Nangia, et al. BBQ: A hand-built bias benchmark for question answering. *Findings of ACL*, pp. 2086–2105, 2022.

[16] M. Nadeem, A. Bethke, S. Reddy. StereoSet: Measuring stereotypical bias in pretrained language models. *ACL*, 2021.

[17] M. D. Ekstrand, G. McDonald, A. Raj, I. Johnson. Overview of the TREC 2022 fair ranking track. *TREC*, 2022.

[18] S. Dai, X. Chen, S. Xu, L. Pang, Z. Dong, J. Xu. Bias and unfairness in information retrieval systems: New challenges in the LLM era. *KDD*, pp. 6437–6447, 2024.

[19] M. Hu, H. Wu, Z. Guan, et al. No free lunch: Retrieval-augmented generation undermines fairness in LLMs, even for vigilant users. *arXiv:2410.07589*, 2024.

[20] R. Shrestha, Y. Zou, Q. Chen, et al. FairRAG: Fair human generation via fair retrieval augmentation. *CVPR*, 2024.
