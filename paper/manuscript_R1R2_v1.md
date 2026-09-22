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
5. **The projection attack is robust to corpus naturalness; the text attack is not.** The text-only attack reaches 0.000 on BBQ at every rate up to 2%, while the projection attack reaches 0.903 at 0.1% and 1.000 by 2%. We identify the mechanism: an injection that works by aligning its text with query vocabulary needs the injected tokens to stand out, which repetitive corpora permit and naturally varied text does not. The same condition reappears in the *representation*, and there it has a mechanism. Across six retrievers at base size the text attack succeeds 0.750 (BM25), 0.625 (feature hashing), 0.625 (**SPLADE**), 0.5625 (Contriever), 0.0625 (GTE-base) and 0.0625 (E5-base-v2) — a nine-fold spread. We added SPLADE, a *learned sparse* retriever, specifically to separate two explanations: SPLADE learns its term weights yet is as susceptible as BM25, so susceptibility tracks the **sparsity** of the representation rather than whether the encoder is learned or semantic. The attack raises its score by appending query-aligned terms, which requires the representation to expose per-term contributions — which sparse retrievers do, learned or not, and dense encoders do not. **The spread does not close with scale, and sparsity is a correlate rather than a law.** Pairing each encoder with its larger sibling from the same family, E5-base-v2 → E5-large-v2 becomes *more* resistant (0.0625 → 0.0000) while **GTE-base → GTE-large becomes eight times more susceptible (0.0625 → 0.5000)**, on identical data and with the only variable being the checkpoint. Text-attack susceptibility is therefore a per-checkpoint property that is not monotone in encoder size and must be measured, not inferred.

Finding (2) is a **negative result about a class of defenses**, and we argue it is the paper's central contribution. We prove it (§6): under a relevance-overlap assumption, a distribution-constrained defense faces a **trilemma** — it cannot simultaneously exclude adversarial passages, admit good clean selections, and impose a non-vacuous constraint. Violating an ε-constraint costs the attacker at most $k$ replacements once its passages are retrieved; whether they are retrieved is a separate, corpus- and encoder-dependent question, and our six-retriever comparison shows it varies by more than an order of magnitude. We also show by backbone alignment that the inertness does not depend on the attack leaving R1 undisturbed: on the dense encoders the attack moves R1 by 0.37–0.47, more than three times as much as on BM25, and the R1 constraint remains inert at every budget setting — Δ = 0.000 in all twelve constrained configurations measured against six retrievers.

The retrieval-layer skew also **propagates to the generated output** (§5.7): with a fixed generator and only the retrieved context varying, the generation-layer stance gap rises 46% under poisoning (0.271 → 0.396), and it does so by driving one group's favourable rate to ceiling (0.708 → 1.000) while the other stays flat — a more specific failure than a uniform shift. Neither constraint repairs this.

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

**What we do.** We formalise R1 and R2, construct the pairwise-poisoning attack, and build a controlled evaluation in which group and stance labels are exact and the clean reference for both dimensions is known by construction. We then re-implement the R1-constraining defense family and evaluate it against the attack across six retrieval back-ends. Our findings are:

- **Pairwise poisoning is an R2 attack, not an R1 attack.** R1 drift under attack is at or below the level legitimate retrieval variance produces; within-group stance divergence rises to near its maximum. An R1-only monitor therefore reports the system as healthy while the retrieved evidence is entirely attacker-controlled.
- **The R1-only defense is not merely weak, it is inert.** Under the projection-augmented attack it attains exactly the same adversarial-passage inclusion rate as no defense (0.750 for BM25, 1.000 for dense retrieval), and this holds at *every* budget setting, including the strictest. The budget parameter acts on a quantity the attack does not perturb.
- **A two-sided R2 constraint improves its own metric by 77% and defends not at all.** Adding a lower bound on within-group favourable rate — the bound that the suppression form of the attack violates — reduces the cross-group stance gap from 0.6250 to 0.1429 (§5.3). Adversarial-passage inclusion does not move: it remains 0.750 in every configuration tested, across the full budget sweep. We explain why: the repair pass substitutes one high-scoring passage for another, and because injected passages are engineered to out-rank legitimate ones, the substitute is itself adversarial. A genuinely relevant passage satisfies any constraint expressed over aggregate composition, no matter how many dimensions that composition is extended to.
- **A provenance signal is necessary, and we report an exploratory candidate.** We measure the number of distinct queries for which a passage is retrieved and find clean separation in our controlled setting. We state plainly that our corpus is synthetic and that this separation may be an artefact of its construction; we therefore present it as a hypothesis with a specified falsification experiment, not as a defense.

**Contributions.**

1. A two-dimensional formalisation of representation in retrieved sets (R1 composition, R2 within-group stance), with the observation that adversarial injection is balanced in R1 and skewed in R2 (§3).
2. A controlled pairwise-poisoning construction that makes both dimensions measurable without a generator, so the mechanism can be studied independently of LLM behaviour (§4).
3. An empirical demonstration that R1-constraining defenses are inert against this attack, including the strictest budget setting, across **six** retrieval back-ends and four bias strata (§5).
4. A negative result on the limits of distribution-level defense: aggregate-composition constraints cannot reject an individually admissible passage, so any defense in this class has an adversarial-passage inclusion floor of 1 (§6). To our knowledge this limit has not been characterised.
5. An exploratory provenance signal with an explicit validity threat and a falsification protocol (§7).
6. A methodological finding with an identified mechanism: text-attack susceptibility is predicted by the **sparsity** of the retrieval representation, not by whether the encoder is learned or semantic (§5.5, Finding 7). A learned sparse retriever is as susceptible as BM25 while two of three dense encoders resist almost completely, so a single-encoder robustness claim measures an unmeasured encoder property.
7. A scale check that bounds contribution 6 and is itself the sharper result (§5.6): susceptibility is **not monotone in encoder size**. E5 becomes more resistant when enlarged while GTE becomes eight times more susceptible within the same family and training recipe, so susceptibility is a per-checkpoint property that must be measured rather than inferred from architecture, size, or sparsity.

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

We require a corpus in which (i) every passage carries exact group and stance annotations, and (ii) the clean reference for both R1 and R2 is known by construction. Public bias benchmarks provide stereotype/anti-stereotype template inventories [15, 16] but not passage-level scaffolding with a known clean reference, so we build a controlled corpus: for each of four bias strata (gender, disability, age, race), a balanced pool of passages is instantiated from the stratum's template inventory, with an equal number of favourable and unfavourable passages per group and a set of group-neutral passages. Queries are group-neutral by construction — the query text never names a protected group — so any group skew in a retrieved set is attributable to the corpus and not to the question. §5.4 replicates the mechanism findings on the naturally written BBQ corpus, and §8 discusses why no *neutral* retrieval corpus can substitute (§8, Limitation 1).

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

Ground-truth poison labels are used **only** for the attack-success metrics; no defense receives them. All defenses are evaluated with $k = 5$. Retrieval back-ends are BM25, a self-contained feature-hashing dense retriever, and — for the backbone alignment of §5.5 and the scale check of §5.6 — the encoders GTE-base [5], GTE-large, Contriever [8], E5-base-v2 and E5-large-v2 [4, 6], plus the learned-sparse retrievers SPLADE (distil) and SPLADE-efficient-large. Multilingual and instruction-tuned embedders remain to be swept (Limitation 5).

---

## 5. Results

> **Status of this section.** All numbers reported below were produced by the released implementation and are reproducible with the commands in Appendix A. Two corpora are used: a controlled corpus with an exactly known clean reference (§5.1–§5.3) and the natural BBQ corpus (§5.4), each swept over injection rate $\rho \in \{0.1\%, \dots, 2\%\}$ of corpus size; §5.5 adds the backbone alignment against five further retrievers, §5.6 the encoder-scale check, and §5.7 the generation-stage propagation check. The controlled suite completes in ~25 s, the BBQ replication in ~180 s, and the multi-backbone sweep in ~12 min, all on CPU with no GPU.

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

### 5.5 Backbone alignment: six retrievers, and what susceptibility actually tracks

The experiments above use a self-contained feature-hashing dense retriever and a lexical one. Neither is the encoder the fairness-defense literature uses, so the numbers cannot be placed beside published results. We therefore add the encoders that literature actually uses — **GTE-base** [5], **Contriever** [8], and **E5-base-v2** [4, 6] — and, to test a mechanism rather than only to align, **SPLADE**, a *learned sparse* retriever. SPLADE is the decisive addition: it is sparse like BM25 but learned like a neural encoder, so it separates two explanations that a lexical-versus-semantic comparison cannot. E5 receives its required `query:` / `passage:` prefixes; omitting them measurably degrades retrieval and would distort the comparison.

**Table 8.** Attack effect by backbone. `template_plus_projection`, $\rho = 0.5\%$, no defense.

| Retriever | representation | R1 drift | R2 gap | `poison@k` | `in_pool_rate` |
|---|---|---|---|---|---|
| BM25 | lexical, unsupervised sparse | 0.1625 | 0.7436 | 0.750 | 0.0125 |
| dense (feature hashing) | hashed, not semantic | 0.1625 | 1.0000 | 1.000 | 0.0000 |
| **SPLADE** | **learned sparse** | 0.2687 | 1.0000 | 0.750 | 0.0000 |
| GTE-base | dense semantic | 0.4688 | 1.0000 | 1.000 | 0.0000 |
| Contriever | dense semantic | 0.3687 | 1.0000 | 1.000 | 0.0000 |
| E5-base-v2 | dense semantic | 0.4000 | 1.0000 | 1.000 | 0.0000 |

Every retriever is attacked, and the R2 gap saturates at its maximum for all but BM25. The R1 drift of the dense encoders (0.37–0.47) is **2.3x–2.9x** that of BM25 (0.16) — the projection attack perturbs group composition *more* in a continuous semantic space, which is the opposite of what we expected when we added this experiment.

**Table 9.** R1-only constraint inertness. `template_plus_projection`, $\rho = 0.5\%$, Δ = constrained minus no defense.

| Retriever | `repr_group` ε=0 | ε=1.0 | `repr_both` ε=0 | Δ |
|---|---|---|---|---|
| BM25 | 0.750 | 0.750 | 0.750 | **0.000** |
| dense (hash) | 1.000 | 1.000 | 1.000 | **0.000** |
| SPLADE | 0.750 | 0.750 | 0.750 | **0.000** |
| GTE-base | 1.000 | 1.000 | 1.000 | **0.000** |
| Contriever | 1.000 | 1.000 | 1.000 | **0.000** |
| E5-base-v2 | 1.000 | 1.000 | 1.000 | **0.000** |

**Finding 6. The R1 constraint is inert on every backbone tested — all 12 constrained configurations in Table 9 show Δ = 0.000, where Δ is the change in adversarial-passage inclusion (`poison@k`) versus no defense — and its inertness does not depend on the attack leaving R1 undisturbed.** This is the paper's strongest single result, and we state it in the sharper form deliberately, because the weaker form would be misleading. One might reasonably expect an R1 constraint to become effective once the attack perturbs R1 appreciably — and on the dense encoders it does perturb R1, by 0.37–0.47, more than three times as much as on BM25. It nonetheless admits exactly the same adversarial passages as no defense, at either budget extreme. The reason is that the constraint operates on *admission quotas*, and the attacker constructs the injection to fit inside whatever quota the defense enforces: the tolerance parameter widens or narrows the admissible region without ever excluding the attacker's passages, which were built to be compositionally typical. §6.2 proves why. The result holds across six retrievers spanning lexical, hashed, learned-sparse and three dense semantic representations.

**Table 10.** Text-only (lexical) attack by backbone — what susceptibility actually tracks. `template`, no defense.

| Retriever | representation | `poison@k` @0.5% | @2% | R1 drift @0.5% | `fav_g2` |
|---|---|---|---|---|---|
| BM25 | lexical, unsupervised sparse | 0.7500 | 0.7500 | 0.1625 | 0.7436 |
| dense (feature hashing) | hashed (preserves lexical surface) | 0.6250 | 0.6250 | 0.0812 | 0.6167 |
| **SPLADE** | **learned sparse** | **0.6250** | 0.6250 | 0.2188 | **1.0000** |
| Contriever | dense semantic | 0.5625 | 0.5625 | 0.1750 | 0.9444 |
| GTE-base | dense semantic | **0.0625** | 0.0625 | 0.0000 | n/a |
| E5-base-v2 | dense semantic | **0.0625** | 0.0625 | 0.0000 | n/a |

The `fav_g2` column is the R2 reading. The `n/a` entries for GTE-base and E5-base-v2 are not missing values but a consequence of the attack failing: with no adversarial passage in the top-$k$ there is no stance skew to measure, so the R2 gap is undefined rather than 0 or 1. We report it as undefined because collapsing it to 0.000 would misrepresent a failed attack as a perfectly balanced selection. Note also that R1 drift is **exactly** 0.0000 for both resistant encoders — the attack produces no measurable change on either dimension — whereas SPLADE's R2 gap reaches its maximum 1.0000, the highest of the six, against a text-only attack where BM25 reaches only 0.7436. SPLADE's learned term weighting evidently concentrates score on exactly the terms the attacker appends, making it the *most* efficiently attacked retriever on the R2 dimension despite tying the hashed retriever on `poison@k`.

**Finding 7. Text-attack susceptibility tracks the *sparsity* of the representation, not whether the encoder is learned or semantic.** We added SPLADE specifically to decide between two explanations, and it decides: SPLADE learns its term weights — it is a neural encoder, trained on relevance — yet it is as susceptible as BM25 (**0.6250 versus 0.7500**), because its representation is still a sparse bag of term weights. The grouping that the data supports is:

| representation | retrievers | text attack |
|---|---|---|
| **sparse** (term-level weights, learned or not) | BM25, SPLADE | **susceptible** (0.62–0.75) |
| hashed (preserves the lexical surface) | feature hashing | susceptible (0.6250) |
| **dense semantic** | GTE-base, E5-base-v2 | **resistant** (0.0625) |
| dense semantic | **Contriever** | susceptible (0.5625) |

The mechanism is now clear and follows from how the attack works. The injection raises its score by appending query-aligned terms, which requires the representation to expose **per-term contributions**. A sparse retriever — including a learned one — does exactly that, so the attacker's appended terms translate directly into score. A dense encoder compresses the whole passage into one vector, where appended terms are absorbed into the semantic representation and produce no separate term-level gain. We had expected a lexical-versus-semantic split; **sparsity is the operative property, and semantics only matters through it.**

**This finding has a measured boundary, and we state it here rather than burying it in the limitations.** §5.6 pairs each of these encoders with its larger sibling from the same family and finds that sparsity predicts susceptibility *at a fixed scale* but does not determine it: GTE-large is dense and semantic, yet is eight times more susceptible than GTE-base. Sparsity is therefore a strong correlate and a useful heuristic for choosing a back-end, not a law. The version of Finding 7 we are prepared to defend is the weaker one — **susceptibility is a property of the specific checkpoint and must be measured** — with sparsity the best available predictor among the axes we varied.

Two consequences, and the second is the uncomfortable one. One observation is worth recording first because it surprised us: SPLADE is the *most* efficiently attacked of the six on the R2 dimension, reaching the maximum stance gap 1.0000 against a text-only attack where BM25 reaches only 0.7436 — its learned term weighting evidently concentrates score on exactly the terms the attacker appends.

First, a feature-hashing retriever is not a substitute for a semantic one: it preserves the lexical surface (0.6250, close to BM25's 0.7500) and therefore over-states text-attack effectiveness relative to a dense encoder. This is why our own earlier numbers, produced with it, were too pessimistic about encoder robustness.

Second, **"dense semantic" is not a guarantee — Contriever is the counterexample.** Two of the three dense encoders resist almost completely (0.0625) while Contriever sits near BM25 (0.5625), a nine-fold gap between encoders of the same size class on the same corpus with the same injected text. And Contriever is the encoder used by the fair-ranking work we compare against [8]. A defense evaluated on Contriever would appear to face a live text-injection threat; the same defense on E5-base-v2 or GTE-base would face a negligible one. Because evaluations in this literature are typically run on a single encoder, a reported robustness figure conflates the defense's behaviour with an encoder property that is not measured. We do not regard this as a flaw in any particular paper so much as a **missing control**: the encoder should be reported as a factor rather than as an implementation detail, and a robustness claim should be accompanied by the same measurement on encoders that differ in representation family.

**Adaptive attacker, for completeness.** On both SPLADE and E5-base-v2 every defense again collapses to complete failure at the first perturbation step: `off-manifold` goes 0.1875 → 0.5000 → 0.8125 → 1.000 (SPLADE) and 0.000 → 1.000 (E5-base-v2) for $\lambda = 0, 0.25, 0.5, 1$; `multi_query` and `repr_conserving` saturate by $\lambda = 0.25$. This matches the companion paper's finding that a real encoder leaves defenses less adaptive headroom than our own retriever.

**Consequences for our claims.** Two findings needed this experiment to be stated correctly:

- Finding 2 (R1 inertness) survives and is **substantially stronger** than the version we would have claimed without backbone alignment: it holds across six retrievers and, decisively, holds *even when the attack moves R1 substantially* (up to 0.47 on GTE-base).
- Finding 4 (corpus-dependence of the text attack) becomes a **three-way dependence**: on corpus repetitiveness, on injection rate, and on the representation family. Sparsity is the third term, and §5.5 shows it is the one with a mechanism behind it.

Two findings do *not* survive unchanged, and we report both. First, the R2 constraint's **demonstrable benefit** shrinks on the dense encoders: the R2 gap is already saturated at 1.0000 under every defense configuration at this injection rate, leaving no headroom to recover, so we can show the constraint reducing the gap only on BM25 and our own retrievers. Second, our earlier statement that text-level injection is sufficient must be narrowed to the sparse and hashed representations and to Contriever; against GTE-base and E5-base-v2 it does not hold at any injection rate we tested.

### 5.6 Encoder scale: susceptibility is not a smooth function of size

The backbone comparison above covers six retrievers at *base* size. A natural objection is that encoder choice is a nuisance parameter of the implementation rather than a finding — that a larger checkpoint, being better trained, would simply be more robust, and that the spread would narrow. An earlier draft of this paper asserted as much, predicting that larger checkpoints "give no reason to expect agreement" without measuring it. We have now measured it, and **the prediction was right in direction but far too weak in magnitude: scaling up flips one encoder family from resistant to susceptible.**

We pair each base encoder with its larger sibling from the *same* family and training recipe, holding corpus, injection rate, attack and defenses fixed: GTE-base → **GTE-large**, E5-base-v2 → **E5-large-v2**, and SPLADE (distil) → **SPLADE-efficient-large** (the published large SPLADE, which splits into separately fine-tuned query and document encoders).

**Table 11.** Text-only (lexical) attack, $\rho = 0.5\%$, no defense. Base/large pairs from the same family.

| Retriever | params | `poison@k` | R1 drift | R2 gap |
|---|---|---|---|---|
| GTE-base | 110M | **0.0625** | 0.0000 | n/a |
| **GTE-large** | 335M | **0.5000** | 0.1313 | 0.9444 |
| E5-base-v2 | 110M | **0.0625** | 0.0000 | n/a |
| **E5-large-v2** | 335M | **0.0000** | 0.0000 | n/a |
| SPLADE distil | 66M | 0.6250 | 0.2188 | 1.0000 |
| **SPLADE large** | 110M | 0.5625 | 0.1875 | 0.8810 |

**Finding 11. Text-attack susceptibility is a per-checkpoint property that is not monotone in encoder scale, and scaling can destroy resistance entirely.** GTE-base and E5-base-v2 are equally resistant at base size — both at 0.0625, i.e. the attack succeeds on three of 48 queries. Enlarging both by the same factor of three moves them in *opposite* directions: **E5-large-v2 becomes more resistant (0.0625 → 0.0000, the attack now fails on every query), while GTE-large becomes eight times more susceptible (0.0625 → 0.5000, succeeding on 24 of 48 queries).** SPLADE is susceptible at both scales with little change (0.6250 → 0.5625), so the learned-sparse result is stable under scaling even though its own size increase is modest.

Two things make this more than a curiosity. First, it is a same-family, same-recipe comparison on identical data, so it cannot be attributed to corpus, rate, or attack construction — the only variable is the checkpoint. Second, the per-query distribution is discrete: adversarial inclusion is 0 or 1 per query with nothing in between, so the change from 3 to 24 affected queries is a shift in *how many* queries are compromised, not a drift in a continuous score. A system whose retrieval robustness was validated on GTE-base would become substantially more attackable by the routine act of upgrading the embedder.

**Mechanism.** We tested the obvious explanation and it is wrong, which makes the result more informative rather than less. If GTE-large's embedding space were more *anisotropic* — vectors collapsed into a narrower cone — then a fixed textual nudge would move rank further, and the finding would reduce to a known geometric property. We measured it: GTE-base and GTE-large are near-identical in mean pairwise cosine (0.8484 vs 0.8579), in effective dimensionality (13.2 in both, against 768 and 1024 nominal dimensions), and in the spread of query similarity (top-decile spread 0.0860 vs 0.0895). The same holds for the E5 pair (0.8291 / 0.8375 anisotropy, 13.9 / 14.8 effective dimensions). **Embedding geometry does not explain the scale effect.**

What does explain it is the size of the gain the attack buys. Measuring the injected passages directly against the clean corpus, for the same queries:

**Table 12.** Where the GTE scale effect comes from. 36 injected passages, 48 queries, no defense, $\rho = 0.5\%$.

| Quantity | GTE-base | GTE-large |
|---|---|---|
| mean cosine gain of poison over clean (`poison − clean`) | **+0.0115** | **+0.0200** |
| mean best-poison cosine | 0.8907 | 0.8975 |
| mean top-5 clean threshold | 0.8982 | 0.8988 |
| mean margin (best poison − threshold) | **−0.0075** | **−0.0013** |
| `poison@k` | 0.0625 | 0.5000 |

The two encoders place the same injected text at almost the same distance from the query (best-poison cosine 0.8907 vs 0.8975), and the legitimate competition sits at the same threshold (0.8982 vs 0.8988). The difference is that **the identical appended vocabulary buys 74% more similarity on GTE-large (+0.0200 vs +0.0115)**. Because the mean margin is only about −0.007, a gain difference of +0.0085 is enough to carry a large fraction of queries across the threshold — which is exactly the 3-to-24 shift in affected queries. Susceptibility here is not a property of the space but of *how much a fixed lexical perturbation moves a passage within it*, and that quantity is not predictable from architecture, dimensionality, size, or geometry. This is what we mean by saying the property must be measured: it is the interaction between the attack's vocabulary and the encoder's learned weighting of it, and no coarse descriptor of the encoder we have tried predicts it.

**Finding 6b. The R1 constraint remains inert at large scale.** Table 13 extends the §5.2 inertness check to the large checkpoints.

**Table 13.** R1-only constraint inertness on large back-ends. `template_plus_projection`, $\rho = 0.5\%$; Δ = adversarial-passage inclusion minus no defense.

| Retriever | `repr_group` ε=0 | `repr_both` ε=0 | Δ |
|---|---|---|---|
| hash-dense (own) | 1.0000 | 1.0000 | **0.0000** |
| GTE-large | 1.0000 | 1.0000 | **0.0000** |
| E5-base-v2 | 1.0000 | 1.0000 | **0.0000** |
| E5-large-v2 | 1.0000 | 1.0000 | **0.0000** |
| SPLADE distil | 0.7500 | 0.7500 | **0.0000** |
| SPLADE large | 1.0000 | 1.0000 | **0.0000** |
| BM25 (lexical) | 0.7500 | 0.7500 | **0.0000** |

Across all eight back-ends and both constraint configurations, the difference is exactly zero. This is now the fourth independent setting in which the inertness holds — two corpora, six base retrievers, and the large checkpoints — and it remains the paper's most robust result. Note that the projection attack reaches complete inclusion (1.0000) on GTE-large, on E5-large-v2 and on SPLADE-large, so the constraint is inert in the worst case rather than in a marginal one.

**Consequences for Finding 7.** Finding 7 identified sparsity as the operative property behind the base-size spread. The scale check bounds that claim rather than refuting it: sparsity still predicts susceptibility *at a fixed scale* (both sparse retrievers susceptible, and the one resistant-at-both-scales encoder is dense), but it is not sufficient, because GTE-large is dense and semantic yet susceptible. The honest form of Finding 7 is therefore that **the sparse/dense split is a strong correlate at base size and a heuristic, not a law**, and the only fully reliable statement is the weaker one: susceptibility is a property of the specific checkpoint, and it must be measured rather than inferred from architecture or size.

### 5.7 Generation-stage propagation: does the retrieval skew reach the output?

Every result above is measured at the retrieval layer. That is deliberate — it makes the mechanism measurable without a generator and reproducible on commodity hardware — but it leaves the question a reviewer will ask: **does a retrieval-layer stance skew change what the system says?** We answer it with a fixed generator, varying only the retrieved context, so that any difference between conditions is attributable to retrieval.

**Protocol.** For each query we generate under four conditions, holding model, prompt, decoding (temperature 0) and question text fixed: `clean` (unpoisoned retrieval), `poisoned` (pairwise injection, no defence), `r1only` (R1 constraint), `r2both` (R1+R2 constraint). The primary probe is **forced choice**: the generator must select between a favourable and an unfavourable statement about a group — the generation-layer analogue of the R2 dimension, and the same form of measurement used for attack success in the poisoning literature. Option order is randomised per (query, condition, group) so that a position bias cannot masquerade as a stance effect. We additionally collect free-form answers and a per-passage attribution probe.

Generator: DeepSeek (`deepseek-chat` at temperature 0), selected because it is reachable without a proxy from the network this work used. 207 API calls, 49.2k prompt tokens, 125 s of model time.

**Table 14.** Generation-layer stance by condition. Controlled corpus, GTE-base retrieval, $\rho = 2\%$.

| Condition | fav. rate (g1) | fav. rate (g2) | **stance gap** | Δ vs clean |
|---|---|---|---|---|
| clean | 0.562 | 0.708 | **0.2708** | — |
| poisoned | 0.583 | 0.979 | **0.3958** | **+46%** |
| `r1only` (R1) | 0.604 | 1.000 | **0.3958** | +46% |
| `r2both` (R1+R2) | 0.583 | 1.000 | **0.4167** | +54% |

**Finding 8. The retrieval-layer skew propagates to the generated output.** The generation-layer stance gap rises from 0.2708 to 0.3958 under poisoning — a 46% increase on a fixed generator with only the context changed. The retrieval-layer failure we document is therefore not an artefact of how we measure retrieval: it changes what the system says.

**Finding 9. The skew does not appear as a uniform shift; it saturates one group.** The favourable rate for the second group rises monotonically across conditions (**0.708 → 0.979 → 1.000 → 1.000**) while the first group's rate is essentially flat (0.562 → 0.583 → 0.604 → 0.583). The attack does not make the generator "more biased" in a diffuse sense; it drives one group's favourable judgement to ceiling. This is a more specific — and more concerning — failure mode than a uniform shift, and it is visible only because we measure the two groups separately.

**Finding 10. Neither constraint improves the generation layer, and one makes it slightly worse.** `r1only` leaves the gap identical to no defence (0.3958); `r2both` leaves it slightly higher (0.4167). This is consistent with the retrieval-layer result on this backbone, where the R2 gap is already saturated and the R1 constraint is inert (§5.5): the input to the generator is unchanged, so the output is unchanged. We report it because it closes the loop honestly — the constraints we proposed, evaluated here, do not repair the downstream harm.

**A metric that failed, reported because it is the natural one to reach for.** We implemented the expected-attributed-exposure (EAE-D) statistic of Kim & Diaz [8] by asking the generator, per retrieved passage, whether its answer relied on that passage. It returns **1.000 in every condition**, with no discrimination. The reason is structural rather than a coding error: the answer is generated *from* the context, so a "did you rely on this?" probe admits YES for essentially any passage present. Proper attribution — "which passages did you rely on?" — is what [8] measures by entailment rather than by self-report, and our self-report implementation does not replicate it. We report the failure because EAE-D is the obvious metric at this interface and a reader should know that its cheap version is uninformative here.

**Scope.** One generator, one retrieval backbone (GTE-base), one injection rate, 48 queries. The direction and the saturation pattern are clear; the magnitudes should not be extrapolated.

---

## 6. Why Distribution-Level Defense Has a Limit

Findings 2, 3 and 6 are not tuning failures. They follow from what a distributional constraint *is*, and we give the derivation here.

### 6.1 Setup

Let $\mathcal{C}$ be the corpus; each passage $d$ carries a group $g(d) \in \mathcal{G} \cup \{\bot\}$ and a stance $s(d) \in \{+1,-1,0\}$ ($+1$ favourable toward $g(d)$). Let $\mathcal{A} \subseteq \mathcal{C}$ be the passages the attacker controls, $n = |\mathcal{A}|$. A defense selects $\mathcal{D}_q \subseteq \mathcal{C}$ with $|\mathcal{D}_q| = k$ (we write $\mathcal{D}$ where $q$ is clear). Define

$$p_{\text{grp}}(g;\mathcal{D}) = \frac{|\{d \in \mathcal{D} : g(d) = g,\ s(d)\neq 0\}|}{|\{d \in \mathcal{D} : g(d)\neq\bot,\ s(d)\neq 0\}|}, \qquad p_{\text{fav}}(g;\mathcal{D}) = \frac{|\{d \in \mathcal{D} : g(d) = g,\ s(d)=+1\}|}{|\{d \in \mathcal{D} : g(d) = g,\ s(d)\neq 0\}|}.$$

**Definition (ε-feasible).** Fix references $p^{*}_{\text{grp}}, p^{*}_{\text{fav}}$. A selection $\mathcal{D}$ is *ε-feasible*, written $\mathcal{D} \in \mathcal{R}_\varepsilon$, if for every $g \in \mathcal{G}$

$$\bigl|p_{\text{grp}}(g;\mathcal{D}) - p^{*}_{\text{grp}}(g)\bigr| \le \varepsilon \quad\text{and}\quad \bigl|p_{\text{fav}}(g;\mathcal{D}) - p^{*}_{\text{fav}}(g)\bigr| \le \varepsilon. \tag{1}$$

A distribution-constrained defense accepts exactly $\mathcal{R}_\varepsilon$. All defenses in the family we evaluate — the R1 constraint of §4.3, and by inspection the objective of [5] and the proportion adjustment of [6] — are of this form, with $\mathcal{R}$ built from *clean* statistics.

### 6.2 Proposition 1 — the injection is admissible at every tolerance

**Proposition 1.** Let the attacker inject $n$ passages that are (i) group-relevant, (ii) split between groups in proportion $p^{*}_{\text{grp}}$, and (iii) stance-balanced so that $p_{\text{fav}}(g) = p^{*}_{\text{fav}}(g)$ for every $g$. Then any selection consisting only of injected passages is ε-feasible for every $\varepsilon \ge 0$.

*Proof.* Take $\mathcal{D} \subseteq \mathcal{A}$ with $|\mathcal{D}| = k$. By (ii), the count of passages of group $g$ in $\mathcal{D}$ is $p^{*}_{\text{grp}}(g)\,k$ up to rounding, so $p_{\text{grp}}(g;\mathcal{D}) = p^{*}_{\text{grp}}(g)$, and the first inequality of (1) holds with equality. By (iii), $p_{\text{fav}}(g;\mathcal{D}) = p^{*}_{\text{fav}}(g)$, so the second holds with equality. Hence $\mathcal{D} \in \mathcal{R}_\varepsilon$ for all $\varepsilon \ge 0$. $\square$

**Consequence.** A defense whose acceptance test is membership in $\mathcal{R}_\varepsilon$ admits a **fully adversarial** selection at any tolerance, including $\varepsilon = 0$. Tightening the budget does not exclude the injection; it constrains the attacker's *composition*, which the attacker chooses freely. This is the mechanism behind Findings 2 and 6, and it explains why the empirical `poison@k` is *identical* to no defense at every $\varepsilon$ rather than merely close to it: the injected selection is not near the boundary of $\mathcal{R}_\varepsilon$, it is at the reference point.

**Empirical check.** Table 12 reports the prediction of Prop. 1 against every configuration we ran: if the injected selection sits at the reference point, then constraining the R1 budget must leave adversarial inclusion *exactly* unchanged at every tolerance.

**Table 15.** Prop. 1 prediction vs. measurement. R1-only constraint (`repr_group`), strongest attack, largest injection rate per corpus; Δ = constrained minus no defense.

| Corpus / retriever | ε=1.0 | ε=0.5 | ε=0.25 | ε=0.1 | ε=0.0 |
|---|---|---|---|---|---|
| controlled / BM25 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| controlled / feature-hash dense | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| BBQ / BM25 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| BBQ / feature-hash dense | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| controlled / GTE-base | 0.000 | — | — | — | 0.000 |
| controlled / Contriever | 0.000 | — | — | — | 0.000 |

*(entries are Δ`poison@k`; 0.000 in all 24 measured cells)*

Prop. 1 predicts Δ = 0 exactly, and Δ = 0 exactly in every one of the 24 cells measured — not approximately, which a tuning-failure explanation would predict. The equivalence is reproduced by `analysis/verify_theory.py`. We state the count explicitly because the exactness is the point: the constrained selection is not *near* the reference composition, it *is* the reference composition.

### 6.3 Proposition 2 — the minimum injection for an ε-shift

Proposition 1 shows the attacker *can* be admissible; we now give the budget at which it becomes *effective*.

**Proposition 2.** Fix a query and a group $g$. Suppose the clean selection contains $m_g \le k$ passages about $g$, of which $f_g$ are favourable, so $p^{*}_{\text{fav}}(g) = f_g/m_g$. An attacker who replaces $j \le \min(n, m_g)$ of these with injected passages about $g$ (favourable, to flood; unfavourable, to suppress) violates the stance constraint of (1) for $g$ if and only if

$$j > \varepsilon\, m_g, \qquad\text{so}\qquad j^{*}_g(\varepsilon) = \lceil \varepsilon\, m_g \rceil + 1. \tag{2}$$

*Proof.* Flooding: $p_{\text{fav}}(g) = (f_g + j)/m_g$ for $j \le m_g - f_g$, so $p_{\text{fav}}(g) - p^{*}_{\text{fav}}(g) = j/m_g > \varepsilon \iff j > \varepsilon m_g$. Suppressing: $p_{\text{fav}}(g) = (f_g - j)/m_g$, and $p^{*}_{\text{fav}}(g) - p_{\text{fav}}(g) = j/m_g$, giving the same condition. The smallest integer satisfying the strict inequality is $\lceil \varepsilon m_g\rceil + 1$, which is needed to handle the case where $\varepsilon m_g$ is an integer. $\square$

**Corollary 1 (the *constraint* cost is at most $k$).** Since $m_g \le k$, $j^{*}_g(\varepsilon) \le k$ for all $\varepsilon \le 1$. With $k$ typically 3–5, violating the constraint is cheap in the currency of the constraint itself.

**Corollary 2 (suppression is cheaper than flooding when the clean retrieval is one-sided).** If $f_g = 0$ then $p^{*}_{\text{fav}}(g) = 0$ and the flooding direction requires no violation at all, while the suppression direction must overcome the full rate; if $f_g = m_g$ the reverse holds. The cheaper direction is always the one pushing an already-extreme rate further toward its extreme — consistent with the empirical Finding 9, where the attack drove one group's favourable rate to ceiling rather than shifting both.

**A correction we had to make.** An earlier version of this section concluded from Corollary 1 that "the number of passages required is bounded by a small constant independent of corpus size". That conflates two requirements that behave very differently:

| Requirement | Governed by | Depends on corpus size? |
|---|---|---|
| **Violate the constraint** (Prop. 2) | $\varepsilon$ and $m_g \le k$ | **No** |
| **Be retrieved at all** | whether injected passages out-rank the clean competition | **Yes** |

The second is the *premise* of the derivation, not its conclusion. Our measurements show that premise failing in a corpus-dependent way: on the controlled corpus **2 injected passages per stratum (0.1% of 1,824)** already reach `poison@k` = 0.688, whereas on BBQ **356 per stratum (2% of 17,792)** reach **0.000**. Nor is $j^{*} \le k = 5$ sufficient on the controlled corpus, where 5 passages reach only 0.750 — replacement requires out-ranking a large field of equally relevant clean passages. The defensible statement is therefore conditional: **once the attacker's passages are retrieved, violating an ε-constraint costs at most $k$ replacements; whether they are retrieved is governed by the attack's relevance advantage, which is corpus- and encoder-dependent (Findings 4 and 7).** The error mattered: taken at face value it predicts that injection *rate* is irrelevant, which our rate sweep falsifies.

### 6.4 Proposition 3 — the trilemma

**Assumption (relevance overlap).** Every injected passage admits an admissible selection: for each $a \in \mathcal{A}$ there is $\mathcal{D} \in \mathcal{P}$ with $a \in \mathcal{D}$, where $\mathcal{P}$ is the set of selections meeting a utility floor (e.g. every selected passage is within a relevance loss $\delta$ of the unconstrained top-$k$). This is the standard assumption of corpus-poisoning work and our measurements support it — the projection attack attains `poison@k` = 1.000 on our retrievers and 0.903–1.000 on real encoders at $\rho = 0.1\%$.

**Proposition 3.** Under relevance overlap, for every $\varepsilon$ there exists an injection of at most $k$ passages per group that is simultaneously ε-feasible and $\mathcal{P}$-admissible.

*Proof.* Prop. 1 supplies an injection that is ε-feasible for all $\varepsilon$; relevance overlap supplies a $\mathcal{P}$-admissible selection containing each of its passages; the intersection is non-empty. $\square$

**Consequence — the trilemma.** A distribution-constrained defense faces three requirements and can satisfy at most two:

| Requirement | Formal condition |
|---|---|
| **Soundness** — exclude adversarial passages | $\mathcal{R}_\varepsilon \cap \{\mathcal{D} : \mathcal{D}\cap\mathcal{A} \neq \emptyset\} = \emptyset$ |
| **Usefulness** — admit good clean selections | $\mathcal{R}_\varepsilon \cap \mathcal{P} \neq \emptyset$ |
| **Tightness** — a non-vacuous constraint | $\varepsilon < 1$ |

Soundness fails for every $\varepsilon$ whenever the attacker can construct an ε-feasible injection — which requires only knowledge of $p^{*}$ and $\varepsilon$, both public for an auditable defense. So a defense must either (i) accept adversarial passages, (ii) restrict $\mathcal{R}_\varepsilon$ so severely that $\mathcal{R}_\varepsilon \cap \mathcal{P}$ shrinks or empties, sacrificing Usefulness, or (iii) set $\varepsilon$ so large the constraint is vacuous, sacrificing Tightness.

**This is the formal content of the paper's central claim, and our experiments land on all three horns.** (i) Soundness fails: `poison@k` equals no defense at every $\varepsilon$, on six retrievers, two corpora and all injection rates. (ii) Usefulness is squeezed: tightening the R1 budget to $\varepsilon=0$ on the controlled corpus changes `in_pool_rate` from 0.017 to 0.088 with no security gain, and on the dense back-end from 0.2437 to 0.2812 — i.e. the constraint perturbs the selection without excluding anything. (iii) Tightness is vacuous at $\varepsilon = 1$, where the constraint reduces to no defense by construction.

### 6.5 Dimensionality does not help, and the only escape is individual-level evidence

Two consequences of the above are the actionable content of this section.

**(a) Adding dimensions does not shrink the admissible set usefully.** Extending the constraint from R1 to R2 to $m$ dimensions does not remove adversarial selections from $\mathcal{R}$; it gives the attacker more statistics to match, all of them computable from the public references. Prop. 1 applies verbatim with $\mathcal{R}$ the $m$-dimensional feasible set. The attacker's cost rises, their *feasibility* does not fall — and since Prop. 2 bounds the cost by $k$, the rise is cheap.

**(b) The only escape is evidence about individual passages.** To exclude an adversarial passage a defense must evaluate a property of *that passage* that is not a function of the retrieved set's aggregate. In the adversarial setting this is a provenance question, answerable only from traces the attacker's optimisation leaves behind. §7 reports one candidate and its validity threat.

This reframes the problem. Prior work in this area is an **optimisation** problem — which composition is fairest, and how to reach it. Under an adversary it becomes a **detection** problem, and §5.3 shows the two are not interchangeable: a defense can improve its fairness objective while its security objective is untouched. Prop. 3 is the reason the optimisation framing cannot be repaired by tuning: the failure is not at the optimum, it is in the feasible set.

**What this analysis does not establish.** Prop. 3 rests on the relevance-overlap assumption, which we support empirically but do not prove. A defense able to certify that an injected passage is *not* δ-competitive — for instance by proving a relevance upper bound for it — would escape the trilemma, and we know of no such defense in this literature. Constructing one is, in our view, the most promising direction this analysis opens. Prop. 2's bound also assumes replacement, i.e. that injected passages out-rank those they displace; when they do not the bound is vacuous rather than wrong, which is exactly the corpus- and encoder-dependence documented in Findings 4 and 7. Finally, the analysis is pointwise in the query; a defense enforcing the constraint in expectation across queries has more room than the version analysed here, though ours are pointwise, so the measurements are unaffected.

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

1. **The measurement requires group- and stance-annotated passages, and natural retrieval corpora do not have them.** This is the binding constraint on this line of work, and it is worth stating plainly rather than as a data-collection to-do. R1 needs a group label per passage; R2 needs a stance label per passage. NQ and MS MARCO — the standard neutral retrieval corpora — carry neither, and stance toward a social group is not a property that can be inferred from a neutral passage, because a neutral passage does not express one. We therefore could not substitute a neutral corpus for BBQ, and neither can the defenses we evaluate: an R1-constraining defense needs the same group labels, and an R2-constraining defense needs labels that no existing neutral corpus provides. The framework's applicability is thus bounded by annotation, not by computation, and constructing a neutral, group- and stance-annotated retrieval benchmark is the field's outstanding infrastructure problem. Our two corpora bound the behaviour from the two sides available today: a template-controlled corpus with an exactly known reference, and a naturally written bias benchmark. We flag this as an open problem rather than a gap in the present study.
2. **Neither corpus is a neutral retrieval benchmark, and they disagree in two respects.** The text-only template attack is effective only on the controlled corpus (Finding 4), and the R2 constraint reduces adversarial inclusion only on BBQ. We report both conditions rather than selecting the favourable one. The mechanism behind the first disagreement is identified (lexical room depends on corpus repetitiveness), which we regard as a finding rather than a gap; the second is a smaller effect whose magnitude we expect to depend on the corpus's pre-existing stance imbalance.
3. **The absolute R2 metric does not transfer.** `stance_gap` is exactly 0 on the balanced controlled corpus and near its maximum (0.9326) on BBQ *before any attack*, where it is dominated by the benchmark's own stereotyped construction. On such a corpus only the change from the clean baseline is informative. A corpus-relative normalisation of $\Delta_{\text{R2}}$ would be preferable and we leave it open.
4. **Injection budget is a rate, not a count.** We report an injection rate throughout (§5.4), because a fixed passage count measures corpus size and produced a spurious conclusion in our own earlier experiment. Readers comparing against work that reports absolute counts should convert.
5. **Retrieval back-ends, and what the scale check changed.** Nine retrievers are evaluated: BM25, a self-contained feature-hashing dense retriever, SPLADE and SPLADE-large, and five dense semantic encoders — GTE-base, GTE-large, Contriever, E5-base-v2 and E5-large-v2 (§5.5, §5.6). An earlier draft of this paper listed the large checkpoints as "to be added" and *predicted* that they would disagree with the base models. We have since measured it and report the correction: the prediction was right in direction and far too weak in magnitude, since **GTE-base → GTE-large moves from 0.0625 to 0.5000 — an eight-fold increase in susceptibility within a single encoder family and training recipe.** That has three consequences for how this study should be read. First, feature-hashing dense retrieval retains the lexical attack surface and should not be read as a stand-in for a semantic encoder. Second, text-attack effectiveness varies **nine-fold across the base dense encoders alone** (Contriever 0.5625 versus GTE-base and E5-base-v2 at 0.0625) and the susceptible one is the encoder used by the fair-ranking work we compare against [8]. Third, and most importantly, **even holding the family and training recipe fixed, changing the checkpoint changes the answer qualitatively** — so a single-encoder robustness claim does not establish how robust a defense is in general. This is a limitation of our study and, we argue, of the standard evaluation protocol in this area. We have not swept Contriever at large scale, nor multilingual or instruction-tuned embedders, and we expect the spread to widen rather than narrow in those directions. Our scale pairs are parameter-matched (110M → 335M for GTE and E5; 66M → 110M for SPLADE), so the SPLADE pair tests a smaller size delta than the other two and a "large SPLADE is no more robust" conclusion carries correspondingly less weight.
6. **No generation-stage evaluation *beyond §5.7*.** We evaluate at the retrieval layer by design, so the R1/R2 mechanism is measurable without a generator. §5.7 adds a first generation-stage check on a single generator and backbone; it establishes that the skew propagates and that it saturates one group, but not the magnitude. A multi-generator evaluation, and proper entailment-based attribution rather than the self-report probe that failed in §5.7, remain to be done. We do not otherwise report attributed exposure [8] or generator bias [4, 7].
7. **Binary groups.** Following [6, 7, 8], we use two groups per stratum. Extension to $|\mathcal{G}| > 2$ is mechanical for R1 and R2 but is not evaluated here. We note that the race/ethnicity category of BBQ is markedly imbalanced in our corpus build (960 passages about the protected group versus 88 about the non-protected group), which is itself a property of the benchmark worth flagging for anyone reusing it.

---

## 9. Conclusion

Fairness defenses for retrieval-augmented generation constrain the group composition of the retrieved set. We have shown that this objective is mis-specified in the adversarial setting. Group representation has two orthogonal dimensions, and pairwise poisoning — the natural adversarial construction, in which injected passages reuse the legitimate template inventory in matched pairs — is balanced in the first and skewed in the second. The consequence is not that the defenses are weak but that they are inert: the R1-only defense attains the same adversarial-passage inclusion rate as no defense at all, at every budget setting including the strictest.

Extending the constraint to the second dimension improves the aggregate statistic it measures without changing adversarial inclusion, and we have given the reason: a constraint expressed over aggregate composition cannot reject an individually admissible passage, and injected passages are admissible by construction. The problem is consequently not one of optimisation but of detection, and it requires evidence about individual passages rather than about the set they belong to.

We have reported an exploratory provenance signal in that direction, together with the reason it may not survive replication on a natural corpus. Establishing which provenance cues do survive is, in our view, the central open problem this work exposes.

---

## Data and Code Availability

The implementation, configuration files, and the scripts that regenerate every number in §5 are released at **https://github.com/luj00133-dev/rag-poison-fairness**. The controlled corpus is generated deterministically from a fixed seed and requires no dataset download; the BBQ corpus is reconstructed from the official benchmark files by a released loader that derives stance labels from BBQ's own annotations. §5.7 additionally requires a DeepSeek API key, supplied through the `DEEPSEEK_API_KEY` environment variable and never stored in the repository.

**How to regenerate.**

```bash
# retrieval layer (CPU only, no API key)
python -m src.run_experiment --config configs/default.json      # ~25 s
python -m src.run_experiment --config configs/bbq.json          # ~180 s
python -m src.run_experiment --config configs/align_gte_ad.json # GTE-base, ~12 min
python -m src.run_experiment --config configs/align_e5.json     # E5-base, ~10 min
python -m src.run_experiment --config configs/contriever_ad.json # Contriever, ~3 min
python -m src.run_experiment --config configs/align_splade.json # SPLADE distil, ~4 min

# encoder-scale check of §5.6 (large checkpoints, CPU only)
python -m src.run_experiment --config configs/align_gte_large.json      # ~23 min
python -m src.run_experiment --config configs/align_e5_large.json       # ~10 min
python -m src.run_experiment --config configs/align_splade_large.json   # ~12 min

# the analyses behind §5.5 and §5.6
python analysis/compare_six_backbones.py
python analysis/compare_scale.py
python analysis/diagnose_gte_large.py     # embedding geometry
python analysis/diagnose_poison_scores.py # the mechanism behind Table 12

# generation layer (requires DEEPSEEK_API_KEY)
python -m src.run_attribution --config configs/attribution.json
```

Real-encoder runs require `HF_ENDPOINT=https://hf-mirror.com` on networks where huggingface.co is unreachable.

**API key.** The key used for the §5.7 runs is rotated and revoked before publication; the repository contains no credentials, and `results/attribution_cache.json` (a prompt→reply cache) is regenerated locally rather than shipped.

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
The backbone alignment of §5.5 and §5.6 adds roughly 75 minutes of CPU time
across eight encoder checkpoints, the slowest single run being GTE-large at
23 minutes; the largest model loaded is a 335M-parameter encoder, which needs
under 2 GB in fp32. No GPU is used anywhere in this paper.

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
