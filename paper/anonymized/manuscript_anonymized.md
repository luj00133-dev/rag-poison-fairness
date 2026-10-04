# Adversarially Invariant Fairness Statistics: Why Aggregate Retrieval-Fairness Metrics Cannot Detect Pairwise Poisoning

**Author**: [anonymized]
**Affiliation**: [anonymized]
**Corresponding author**: [anonymized]

**Target venue**: *Information Processing & Management* (CAS Q1 Top, IF 8.1) — alternative: *Information Sciences*

<!-- SUBMISSION ARTIFACT — entered in the journal submission system, not typeset into the manuscript.
Highlights (3-5 items, each <= 85 characters):

* Aggregate fairness statistics are adversarially invariant by structure
* Three predictable modes defeat composition, reference and difference metrics
* Per-group shifts move 0.13 where the cross-group gap moves under 0.002
* Static defense advantage is largest on the encoders the field uses
* A six-point protocol makes retrieval robustness claims interpretable

-->

---

## Abstract

Fairness defenses for retrieval-augmented generation are selected, tuned and validated by aggregate statistics of the retrieved set: the share of passages about each protected group, the deviation of a group's stance from a corpus reference, or the exposure of items across requests. Because a defense is only as sensitive as the statistic that selects it, an adversary who can make that statistic invariant defeats the defense *selection* without touching the defense. We show that this is not a weakness of any particular metric but a structural property of the class, and that it is checkable before any attack is built. Every statistic in this literature has the form of a per-group quantity aggregated across groups, and an adversary can preserve that aggregate in exactly three ways: by balancing the quantity it counts (**F1**), by anchoring it to a reference the attack leaves intact (**F2**), or by moving all groups together so that a difference between them cancels (**F3**). The three modes are a falsifiable test rather than a description: applied to the published metrics they predict which will be blind, and the predictions hold.

The attack that realises them is *pairwise poisoning*, which injects matched passages drawn from the legitimate template inventory — one favourable to a group, one unfavourable to another — so that the injection is balanced across groups by construction and the stance of the evidence is skewed instead. We formalise representation as two orthogonal dimensions, **(R1) group composition** and **(R2) within-group stance**, and measure both on a controlled corpus and on a naturally written bias benchmark. A positive control in which the ground truth changes by a known amount while corpus size is held fixed establishes that the indicted statistics are *working instruments*: they respond monotonically and in the correct direction. Against those same instruments, the R1 constraint is inert with an equivalence bound of exactly ±0.0000 — every constrained configuration reproduces the unconstrained inclusion rate per query, because the unconstrained baseline already admits adversarial passages on every query where it can (1.000 dense, 0.750 BM25), leaving no headroom for a reduction to appear. The signal lives in the per-group shifts rather than in the gap between groups: injection moves the suppressed group's stance by −0.13 to −0.18 and the favoured group's by +0.13, consistently across four generators spanning three model families at $p \le 0.0035$, while the absolute cross-group gap moves by less than 0.002. A defense-aware attacker then inverts the static ranking of defenses across six retrieval back-ends: the strongest defense's static advantage is *largest* on the pretrained encoders the compared literature uses — four begin at exactly 0.000 inclusion — and no defense retains measurable benefit beyond one perturbation step on any of them, while the injected passages stay over 94% semantically intact.

The consequence is a reporting requirement rather than another defense. We give a six-point protocol under which a robustness claim is interpretable: per-group shifts rather than cross-group differences, adversarial inclusion as a function of attacker strength rather than at a single operating point, the encoder reported as a factor, equivalence bounds for null claims, and the threat model stated explicitly. The study covers binary group partitions at the retrieval and generation layers across two corpora, and the invariance is conditional on the back-end: §8.1 states the retrievers and threat models in which the composition statistic stays flat, which is what a reader needs in order to know whether a null aggregate is informative in their own setting.

**Keywords**: retrieval-augmented generation, data poisoning, fairness measurement, within-group stance, adversarial robustness, evaluation validity

---

## 1. Introduction

Retrieval-augmented generation (RAG) [1] has become the standard architecture for grounding large language model (LLM) outputs in external, updatable knowledge. Because the generator conditions on whatever the retriever returns, the retrieval corpus becomes a security boundary: an adversary who can place passages in that corpus can determine the evidence on which the model's answer rests. Corpus poisoning attacks exploit exactly this, and a single line of work has established that a small number of injected passages can mislead an undefended system in the large majority of cases [2, 3].

A more recent observation is that poisoning need not target factual correctness at all. Wang et al. [4] show that injected passages can **amplify social bias**: a query that is group-neutral can be answered in a stereotyped way because the retrieved evidence has been skewed toward one group. This matters because the harm is representational rather than factual — a biased answer can be *correct* by every factual measure while still systematically demeaning a protected group — and because it is therefore invisible to the accuracy-based evaluation that RAG systems normally undergo.

In response, a body of work has begun to defend the retrieval layer on fairness grounds. The proposed defenses share a common objective: they measure the **group composition** of the retrieved set and constrain it to remain balanced. Concretely, they partition the corpus by group and either re-rank to equalise group proportions [5], adjust the proportion and ordering of group-relevant passages [6], reverse-bias the embedder so that its retrieved group balance compensates for the generator's own bias [7], or randomise the ranking so that equally deserving items receive equal exposure [8]. Item-side variants of the same idea equalise *exposure* rather than group share, but still operate on aggregate composition [8].

**This paper is about the measurement those defenses rest on, not about the defenses themselves.** A fairness defense is selected, tuned and validated by a statistic, and it is only as good as that statistic's sensitivity to the threat. We show that the standard statistics are structurally insensitive to the attack that motivates them, because that attack preserves the very composition those statistics summarise, that the insensitivity has a single identifiable cause, and that the same cause reappears at the generation layer, where an absolute difference between groups is blind for the same structural reason. The defense failure that follows is then a *consequence* we prove, not a separate claim.

**The problem, stated as a measurement problem.** "Group representation" is not one quantity but two, and the standard statistics measure the wrong one. A retrieved set can be described by

- **(R1) group composition** — the proportion of group-relevant passages that concern each protected group, i.e. $P(\text{group} \mid \text{group-relevant})$; and
- **(R2) within-group stance** — the proportion of passages about a given group that portray it favourably rather than unfavourably, i.e. $P(\text{favourable} \mid \text{group}, \text{group-relevant})$.

R1 and R2 are orthogonal: a set can be perfectly balanced in R1 while every passage about one group is unfavourable, and vice versa. Crucially, the adversarial construction that arises naturally in this setting is **balanced in R1 by construction**. An attacker who wishes to skew representation does not inject one-sided material; they inject matched pairs — a favourable passage about group $A$, an unfavourable passage about group $B$ — which are individually indistinguishable from legitimate passages because they are drawn from the *same template inventory*. The injected set therefore contributes equally to both groups' counts, leaving R1 essentially unchanged, while shifting R2 systematically.

Every candidate metric has that form; whether it reads clean depends on whether the injection balances the terms it aggregates. That is a property of the back-end rather than of the metric, and §5.9 measures it across four of them.

**A second failure, and it is a property of a metric class rather than of any one choice.** The natural repair is to move from composition to stance while keeping the same arithmetic: measure the *gap* between the two groups. That repair fails for the same structural reason. An absolute difference between two group-level quantities is dominated by whatever constant asymmetry the corpus already had, so it is insensitive to an attack that **relocates both groups together** — which is what this attack does, suppressing one group while elevating the other. The diagnostic is the *per-group shift*, and the failure repeats at both layers we measure: at the retrieval layer two of three candidate R2 statistics are flat across the clean and fully attacked conditions (§5.3), and at the generation layer the absolute gap moves by less than 0.002 while the per-group shifts move by 0.13 at $p \le 0.0035$, consistently across generators (§5.7). A metric that is dominated by a corpus constant reports that constant and not the attack.

**What we do.** We formalise R1 and R2 and derive the sensitivity of each candidate statistic to the attack. We build a controlled evaluation in which group and stance labels are exact and the clean reference for both dimensions is known by construction, and we replicate on a naturally written bias benchmark. We re-implement the defense family these statistics motivate and evaluate it against the attack across six retrieval back-ends, before and after scaling each encoder. Our findings are:

- **The standard statistics are blind, and the blindness is systematic rather than incidental.** On the lexical retriever the composition statistic reads clean however much of the injected set is retrieved, while two of three candidate R2 statistics are flat across the clean and fully attacked conditions; §8.1 states the retrievers and attacks on which each part of this holds. The reason is shared: each aggregates over a quantity the attack does not perturb, either group counts (which the injection balances by construction) or a topic-conditioned component (which it preserves).
- **The right axis is the per-group shift, and the gap between groups is the wrong one.** Absolute differences between groups are dominated by pre-existing corpus asymmetry and are blind to attacks that relocate both groups. Per-group shifts are large, consistent and highly significant, at both the retrieval and generation layers, and they are what a defense should be selected on.
- **The R1-only defense is not weak, it is inert — and the reason is a ceiling, which is a stronger statement than a failure to detect an effect.** The unconstrained baseline already admits adversarial passages on every query where it can, so there is no headroom for a reduction to appear even in principle; the per-query difference is identically zero and the equivalence bound is exactly ±0.0000, excluding *any* effect rather than an effect above a threshold. It is not that the constraint cannot change the selection — it does — but that changing the selection does not displace a single adversarial passage.
- **The encoder must be reported as a factor, not as an implementation detail.** Text-attack susceptibility is predicted by the sparsity of the representation rather than by whether the encoder is learned, but sparsity is a correlate and not a law: enlarging GTE within one family and training recipe makes it eight times more susceptible while enlarging E5 makes it more resistant. A single-encoder robustness claim therefore reports a property of a checkpoint that was never measured.
- **Aggregates are not the only option: an individual-level signal separates clean from adversarial passages.** We measure the number of distinct queries for which a passage is retrieved, and it separates the two populations cleanly on the controlled corpus. The claim is deliberately narrow and its refutation is specified: a signal of this kind must be shown to survive on naturally written text before it can carry any defensive weight (§7).
- **Under an informed attacker the defenses do not merely weaken, they invert — and the static numbers are most optimistic exactly where the literature looks.** Sweeping six retrieval back-ends against a defense-aware attacker, the static advantage is *largest* on the pretrained encoders the compared work uses (four begin at exactly 0.000 adversarial inclusion), yet no defense retains measurable benefit beyond one perturbation step on any of them, and the injected passages stay over 94% semantically intact throughout — so the collapse cannot be blamed on the attack destroying its own material. The only configuration that survives at all is the one whose constraint acts on the composition of the retrieved *set* rather than on individual passages — which is precisely the constraint this paper shows is blind. From these results we derive the reporting requirements a robustness claim must meet to be interpretable, and state them as a protocol rather than a suggestion.

**Contributions.**

1. **A framework for when adversarial fairness statistics are invariant.** The form is universal; the invariance is conditional, and checkable in advance. Every candidate metric in this literature is a per-group quantity aggregated across groups, and an adversary can defeat the aggregation in exactly three ways: by balancing what the statistic counts (F1), by anchoring it to a reference the attack preserves (F2), or by moving all groups together so a difference between them cancels (F3). The modes are checkable in advance of building an attack, and we use them to predict which published metrics are blind (§3.4), then confirm the predictions empirically (§5.1, §5.2, §5.7).
2. **A positive control that separates blindness from breakage.** With the ground truth moved by a known amount and the corpus size held fixed, the indicted statistics respond monotonically and directionally (Table 1). The claim is therefore specific — these statistics are immune to an adversary who balances what they count — rather than a general complaint that the instrument is unreliable.
3. Identification of a **shared cause of measurement failure**: statistics that aggregate over group counts, or that take an absolute difference between groups, are insensitive to an attack that balances the former and relocates the latter — with the failure demonstrated at two layers, retrieval and generation (§5.1, §5.3, §5.7).
4. A controlled pairwise-poisoning construction that makes both dimensions measurable without a generator, so the mechanism can be studied independently of LLM behaviour (§4), replicated on a naturally written bias benchmark.
5. An empirical demonstration that R1-constraining defenses are inert, with **equivalence bounds rather than point estimates** for the null, across **six** base retrieval back-ends, three scaled checkpoints, two corpora and five injection rates (§5, Appendix B).
6. A negative result on the limits of distribution-level defense: aggregate-composition constraints cannot reject an individually admissible passage, so any defense in this class has an adversarial-passage inclusion floor of 1 (§6). To our knowledge this limit has not been characterised.
7. A scale check that bounds the sparsity account of encoder susceptibility: susceptibility is **not monotone in encoder size** (GTE 0.0625 → 0.5000 while E5 0.0625 → 0.0000 within matched families), so it is a per-checkpoint property (§5.6).
8. A measurement protocol implied by the above: per-group shifts rather than cross-group differences, injection reported as a rate rather than a count, the encoder reported as a factor, equivalence bounds for null claims, and both stance and attribution scored by entailment in the correct direction rather than by a prompted judge (§8, §5.7.1).
9. **An adaptive-attacker result that turns the negative result into an actionable one.** Against a defense-aware attacker on six back-ends, the static advantage of the strongest defense is largest precisely on the pretrained encoders the compared literature uses, and no defense survives beyond one perturbation step on any of them while the attack retains over 94% semantic fidelity (§5.8). The only constraint that retains any benefit is the one acting on set composition rather than on individual passages — the axis this paper shows is blind — which is why we conclude that the escape is *measurement* rather than defense. From this we derive a six-point reporting protocol for robustness claims, the constructive counterpart to the three failure modes (§5.8.1).

---

## 2. Related Work

### 2.1 Poisoning as a retrieval-quality problem

**This paper is about what a retrieval evaluation statistic can see, so it belongs to the corpus of work on how retrieved evidence is measured — not to the corpus of attack construction.** Corpus poisoning against RAG was established by Zou et al. [2], who showed that a small number of optimised passages can steer a system's answers, and has since been extended to black-box and query-agnostic settings [3], to knowledge-graph-structured retrieval [9], and to multimodal pipelines [10, 11, 12]. A parallel thread targets the retrieval process itself rather than passage content, manipulating embedding space so that injected passages rank highly regardless of their text. Bagwe et al. [13] carry the attack direction into fairness specifically, showing that a backdoor can establish a persistent and covert influence on which groups a RAG system favours. That work establishes that the attack exists and persists; the question this paper asks is different, namely whether the statistics used to select and validate fairness defenses can see such an attack at all. Wang et al. [4] combine both: reward-optimised adversarial documents, subspace projection to raise their retrieval probability, and a generate–evaluate–reinject loop that accumulates bias over time.

All of this work targets *factual* correctness except [4], and [4] itself measures bias by *counting* stereotype-consistent selections rather than by modelling the distribution of stance within groups. Our R2 formulation is a distributional refinement of that measurement, and we show that the refinement changes which defenses can work. We adopt this literature's attacks as *instruments*, not as a contribution: what the paper adds is an argument about which statistics can register them, and the evaluation practice that follows. The attacks here are used the way a test collection is used — to make a measurement's blind spots observable, by reporting a change against a control condition rather than a single value. §3.4 and §5.7 return to what that reporting practice should be.

### 2.2 Fairness as a measurement choice in information access

Fairness in RAG has been studied primarily as a property of the knowledge base and the generator rather than of an adversary, and — this is the point for what follows — each work defines fairness by the statistic it optimises. Wu et al. [6] construct scenario-based questions and evaluate group disparity across RAG components, finding that the retriever has the largest influence on both accuracy and fairness, and that utility and fairness trade off. Their mitigation is to adjust the proportion and ordering of group-relevant passages — an R1 intervention — and they state that they do not provide a comprehensive exploration of mitigation strategies. Kim et al. [7] decompose RAG into LLM, embedder, and corpus, show that component biases interact ("bias conflict"), and find that *reverse-biasing* a small embedder can cancel a much larger generator's bias; their bias metric is group membership, so both R1 and R2 are outside their formulation. Kim and Diaz [8] bring fair-ranking machinery to RAG, using stochastic rankers to equalise item-side exposure across repeated requests, and find that fairness and quality need not trade off severely; their fairness unit is the item/provider rather than the social group.

Two measurement traditions meet here, and it matters which statistics each one supplies. Group fairness in information access is defined over a set — the share of a group in a retrieved set, or its exposure across requests — so its natural statistics are aggregates over groups, and the critiques of those aggregates in the wider fairness literature are critiques of exactly that form (§2.3). Item-side fair ranking instead treats fairness as a property of a distribution over rankings, which is why its machinery is stochastic. Read this way, the RAG fairness results above are not a set of competing defenses but a set of *measurement choices*, each taking a position on what fairness is a property of: Wu et al. take it to be a property of the retrieved set's composition, Kim et al. of component membership, Kim and Diaz of the ranking distribution.

Most closely related is Zhao et al. [5], who model position-wise bias propagation in top-$k$ RAG and formulate fairness-aware retrieval as an optimisation problem over group composition, solved by decomposition. This is the most general R1-constraining defense we are aware of, and we treat it as the representative of the class. Like the others, it assumes no adversary: bias is a property of the corpus and the generator, not something an attacker injects.

Two further works are relevant. Kim et al. [7] observe that "naively increasing fairness is not always the optimal solution" — a conclusion we sharpen by identifying the *specific* reason: the fairness being increased is measured along the wrong axis. Bagwe et al. [13] construct fairness-targeted backdoor attacks that manipulate semantic relationships between groups and biases; their attack relies on a trigger and their objective is attack construction, whereas we study trigger-free injection and its consequences for defense design.

A survey and one further result frame how this work should be read. Dai et al. [14] survey bias and unfairness in retrieval and recommend unified measurement across the pipeline — the direction this paper takes, though their unit of analysis is the system rather than the statistic. Hu et al. [15] find that RAG can undermine fairness even for users who are vigilant about it, so the harm does not require a careless reader; that is the property our adversary exploits deliberately, and it is why we treat the retrieval-layer statistic rather than the user's behaviour as the thing to fix.

### 2.3 The gap

Across this literature we identify four points of agreement that together define the gap this paper addresses. First, fairness defenses for RAG consistently constrain group composition or item exposure (§2.2) — that is, they all occupy one cell of the two-dimensional space this paper separates, and the cell they occupy is the one an adversary can leave untouched. Second, several authors independently report that existing defenses are not robust enough — "further optimization … to achieve more stable and generalizable defense performance" [4]; "single-stage defenses give limited robustness" [16]; "does not provide a comprehensive exploration of strategies to mitigate these unfairnesses" [6]. Third, and structurally, none of the fairness works models an adversary: they study corpora that are *naturally* skewed. Fourth, no work we have found constrains or detects within-group stance.

We therefore study the intersection that has not been studied: an *adversary* acting on the axis that *no* defense constrains.

**Where this sits relative to the measurement literature.** Treating an evaluation statistic as a *measurement* of a theoretical construct — and asking whether it can bear the inferential weight placed on it — is established in the measurement literature, and this paper builds on it. Jacobs and Wallach [17] show that many documented fairness harms are mismatches between the construct a system is supposed to measure and its operationalisation, and they supply construct-validity tools for making those mismatches explicit. Ekstrand et al. [18] make the same argument inside information access, where an aggregate over groups hides the per-group and per-stakeholder structure that a fairness claim depends on, and Oliveira et al. [25] reach it independently from software testing, reporting a RAG fairness regression that a per-model analysis detects and aggregate testing does not. Our contribution is what happens to that argument once the adversary is put back in. Those works establish that an aggregate may fail to represent its construct; we show that under pairwise poisoning the failure is not a matter of degree or of a badly chosen threshold but an *invariance*, and we identify which invariance each candidate statistic has — F1 for anything counting, F2 for anything referenced, F3 for anything differenced — and therefore which construction defeats it. §3.4 states the three modes, §5 confirms them on measurements, and the positive control in the same section separates an invariant instrument from a broken one. The remaining distance from that literature is also the reason our recommendation is a *reporting* rule rather than a new metric: a per-group report is what construct validity requires when no aggregation is safe.

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

We state this separately because the distinction is what makes the R2 statistics measurable at all.

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

### 3.4 One form for every candidate metric, and three invariances an adversary can impose

Every fairness statistic in this literature, including the ones we introduce, has the same shape: a per-group quantity aggregated across groups.

$$M(\mathcal{D}) \;=\; A_{g \in \mathcal{G}}\bigl[\,\phi_g(\mathcal{D})\,\bigr] \tag{2}$$

where $\phi_g(\mathcal{D})$ is some per-group measurement — the share of group-relevant passages belonging to $g$, the proportion of those passages that are favourable, the exposure of $g$'s items — and $A$ is an aggregation over groups (a count, a deviation from a reference, a difference, a variance). R1 statistics take $\phi_g$ to be a composition and $A$ to be a deviation or a count; R2 statistics take $\phi_g$ to be a stance proportion and $A$ to be a deviation, a difference or an extremeness.

This form is useful because it exposes exactly where an adversary can act. An attack on a fairness metric has two available moves and only two: leave the aggregate $A$ where it is while moving $\phi_g$, or move $A$ in a direction the defender reads as harmless. Every attack we study does the first. The consequence is a taxonomy of three failure modes, and they are the reason the experiments in §5 come out as they do.

| Failure mode | Mechanism | Which $A$ is exposed | Where we observe it |
|---|---|---|---|
| **F1 — balanced count** | The injection contributes equally to every group, so any aggregate over group counts returns its clean value | any count or share across groups | §5.1, §5.2 (R1 statistics) |
| **F2 — preserved nuisance** | A statistic is anchored to a reference the attack does not change, so it reports the component that varies with the query rather than the one that varies with the attack | any deviation from a reference | §3.2, §5.1 (`stance_div`, `stance_onesided`) |
| **F3 — cancelled shift** | The attack relocates all groups in the same direction, so a difference between groups is unchanged even though every $\phi_g$ moved a long way | any difference, variance or gap across groups | §5.1, §5.7 (`stance_gap` and its generation-layer twin) |

![Figure 1. The paper's framework in one panel. **(A)** A group-neutral query is answered from the top-$k$ retrieved set. **(B)** The attacker injects passages drawn from the legitimate template inventory in matched pairs --- one favourable to group A, one unfavourable to group B --- so the injection is balanced across groups by construction. **(C)** What a statistic then sees: an R1 (group-composition) statistic is left at its clean value because the attack balances the count, whereas an R2 (within-group stance) statistic is skewed because the attack changes the stance the evidence supports. The figure states the two dimensions the paper separates; the three failure modes below are the ways an aggregate over such statistics loses that signal.](figures/fig_framework_py.pdf){width=88mm}

**The taxonomy is a test, not a description.** For a candidate statistic $M$, the three failure modes correspond to three questions that can be asked before any attack is built:

1. *Does the injection balance the quantity $M$ counts?* If the attacker's construction is symmetric across groups — and pairwise poisoning is, because it reuses the legitimate template inventory in matched pairs — then any counting aggregate is invariant by construction and no amount of data will show the attack.
2. *Is $M$ referenced to something the attack preserves?* If the reference is a per-query clean retrieval or a corpus-level rate, the attack leaves it intact by design, and $M$ measures the query's topic rather than the attacker's skew.
3. *Is $M$ an aggregate that cancels a common-mode movement?* A difference or variance across groups is invariant under $g \mapsto g + c$ for every group at once. An attack that moves all groups together is therefore invisible to it, no matter how large the movement.

![Figure 2. The three failure modes, shown on the same retrieval setting. **(a) F1:** the injection contributes equally to every group, so a counting or composition statistic returns its clean value --- the attack is invisible to it (measured in §5.1 and §5.2). **(b) F2:** the statistic is anchored to a reference the attack does not move, so it reports the component that varies with the query rather than the one that varies with the attack (`stance_div` and `stance_onesided`, §3.2 and §5.1). **(c) F3:** all groups are relocated together, so any difference between groups is unchanged however far the groups move (`stance_gap` and its generation-layer twin, §5.1 and §5.7). The three panels are conceptual and carry no measured values; the corresponding measurements are in the sections named in the table above and in the responsiveness figure.](figures/fig_failure_modes_py.pdf){width=140mm}

A statistic that survives all three is, in our setting, one that reports **per-group levels** rather than a difference between them, because that is the only form that is not invariant under at least one of the three moves. §5.1 and §5.7 test this prediction: on the same retrieval conditions where a difference statistics reports a change of 0.002, the per-group levels move by 0.13 and the paired test rejects at $p < 0.01$. The prediction was made from the form of the statistic, not fitted to those numbers, and §8 records that we violated it ourselves in an earlier version of the generation-layer analysis.

**The taxonomy is testable against known ground truth, and we ran that test.** A taxonomy of failure modes is only worth stating if the statistics it indicts are otherwise sound: if they did not respond to a real composition change either, the finding would be that the measurement apparatus is broken, not that an adversary defeats it. We therefore ran a positive control on the naturally written corpus, where the true composition is known by construction.

The control holds the corpus size fixed at 17,792 passages and **swaps** passages between the two groups of a balanced stratum, so the retrieval pool and the score threshold do not move and composition is the only variable. It changes by a known number of passages, in a known direction, and is reversed in the last row.

**Table 1.** Responsiveness control. Corpus size constant; only group composition changes. `corpus%woman` is the true share after the swap; the remaining columns are the statistics under test.

| Variant | `corpus%woman` | `drift_tv` | `drift_js` | `stance_div` | `stance_onesided` |
|---|---|---|---|---|---|
| baseline (balanced) | 0.500 | 0.0000 | 0.0000 | 0.2925 | 0.4753 |
| swap 500 man→woman | 0.580 | 0.0264 | 0.0372 | 0.2876 | 0.4711 |
| swap 1500 man→woman | 0.739 | 0.0660 | 0.0809 | 0.2854 | 0.4694 |
| swap 3000 man→woman | 0.978 | 0.0924 | 0.1062 | 0.2854 | 0.4694 |
| **swap 3000 woman→man** | **0.022** | **0.0569** | 0.0532 | 0.2851 | 0.4691 |

Two conclusions, and they are what make the negative results interpretable rather than merely negative. First, **`drift_tv` and `drift_js` are working instruments**: they rise monotonically with a real composition change and respond to its direction. The R1 statistic is not broken; it is *specifically* invariant to an injection that balances group counts, which is exactly what F1 predicts and what §5.2 measures. Second, **the two reference-based stance statistics barely move even here** — `stance_div` changes by 0.007 across a composition swing from 0.022 to 0.978 — which is independent confirmation of F2 on data whose ground truth is known by construction rather than inferred from an attack.

The contrast is the paper's central claim in one table: the same statistics that detect a 3000-passage composition change with $p \to 0$ detect a fully adversarial injection not at all.

![Figure 3. Responsiveness control. Corpus size is held constant at 17{,}792 passages and passages are swapped between two well-populated groups, so the retrieval pool and the score threshold do not move and composition is the only variable. The ground-truth group share changes from 0.500 to 0.978 and back to 0.022; the R1 drift statistics track it monotonically and in the right direction, while the two reference-based R2 statistics are flat even here. The indicted statistics are therefore working instruments that are specifically invariant to an injection balancing group counts, not unreliable ones.](figures/fig_responsiveness.pdf){width=140mm}

**What the taxonomy does not claim.** It is not a claim that no fairness metric can be robust. It is a claim about the class of statistics that appear in this literature, all of which are aggregates of the form (2), together with a constructive statement of what escapes the three modes: report $\phi_g$ for each $g$, and report how each moves. That recommendation is cheap, it is what §5.7 does, and it is the difference between detecting the attack and not. Two further bodies of work bound the claim. Within IR evaluation, the practice of reporting a distribution of per-query and per-topic effects rather than a single averaged score is long established — the TREC fair ranking track reports per-query exposure alongside the aggregate for this reason [19] — and the statistical machinery for attaching uncertainty to a difference between conditions, rather than to a single number, is standard [20]. Neither is aimed at an adversary, which is precisely why the invariance matters: those practices make a statistic's uncertainty visible, and an invariant statistic has no uncertainty to report, because its per-query difference is identically zero.

---

## 4. Attack and Evaluation Setup

### 4.1 Corpus

We require a corpus in which (i) every passage carries exact group and stance annotations, and (ii) the clean reference for both R1 and R2 is known by construction. Public bias benchmarks provide stereotype/anti-stereotype template inventories [21, 22] but not passage-level scaffolding with a known clean reference, so we build a controlled corpus: for each of four bias strata (gender, disability, age, race), a balanced pool of passages is instantiated from the stratum's template inventory, with an equal number of favourable and unfavourable passages per group and a set of group-neutral passages. Queries are group-neutral by construction — the query text never names a protected group — so any group skew in a retrieved set is attributable to the corpus and not to the question. §5.4 replicates the mechanism findings on the naturally written BBQ corpus, and §8 discusses why no *neutral* retrieval corpus can substitute (§8, Limitation 1).

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

The chapter is organised as an argument rather than as a sequence of runs. §5.1 and §5.2 establish the two dimensions and the attack, and — critically — show that the statistics we indict are *working instruments*: a positive control moves the ground truth by a known amount and they respond. §5.3 and §5.4 then demonstrate two of the three failure modes on a controlled corpus with an exactly known clean reference and on the naturally written BBQ benchmark, each swept over injection rate $\rho \in \{0.1\%, \dots, 2\%\}$. §5.5 and §5.6 establish that the encoder is a factor rather than an implementation detail. §5.7 shows the retrieval-layer skew reaches the generated text, and §5.8 closes the loop with a defense-aware attacker: the defenses do not merely weaken, and the static numbers that select them are optimistic exactly where the literature looks.

### 5.1 Two orthogonal dimensions of representation

Table 2 reports attack effect with no defense, over 48 queries across four bias strata.

**Table 2.** Attack effect without defense.

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

**Third, R1 drift is small and non-diagnostic.** The largest value is 0.1313 (dense, projection), consistent with §3.3: the injected set is compositionally $(\tfrac{1}{2}, \tfrac{1}{2})$, so the drift reflects injected passages outranking legitimate ones rather than any compositional imbalance on their part. An R1-based monitor sees a retrieved set whose group balance is close to the clean reference, while `poison@k` reaches 1.000 and the utility proxy `in_pool_rate` falls to 0.000 — the retrieved set becomes entirely attacker-controlled.

**Finding 1.** Pairwise poisoning drives the cross-group stance gap to 0.6250–1.0000 while leaving both R1 drift and the two reference-based R2 statistics near their clean values. Neither an R1 monitor nor a naive R2 monitor flags it.

### 5.2 The R1 constraint is inert

**Table 3.** Defense comparison under template + projection. `poison@k` is the adversarial-passage inclusion rate.

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

![Figure 4. R1-constraint inertness. Adversarial-passage inclusion as a function of the constraint budget $\varepsilon$, for the strictest ($\varepsilon=0$) through the loosest ($\varepsilon=1$) setting. Every constrained configuration coincides exactly with the unconstrained baseline -- the lines are not merely close, the per-query values are identical -- so the equivalence bound is $\pm 0.0000$ and the data exclude any effect on adversarial inclusion rather than an effect above some threshold.](figures/fig_r1_inertness.pdf){width=88mm}

**This is a null result, so we state its strength rather than leaving a reader to guess.** A point estimate of zero can mean "no effect" or "not enough data", and the distinction matters here because the claim is that a published defense family does nothing. We therefore report paired tests on the per-query data (Table B1) instead of aggregate means:

- For every R1-constrained configuration, the **per-query difference vector is identically zero** — not small, zero. The paired bootstrap CI collapses to [0, 0] and the permutation test is degenerate by construction. The informative statistic is the equivalence bound: because the differences are exactly zero rather than approximately zero, **these cells exclude any effect on adversarial-passage inclusion, not merely an effect above a threshold.**
- The reason is a **ceiling**, and this is stronger than a failure to detect an effect. The unconstrained baseline already admits adversarial passages on every query it can — 1.000 for the dense retriever, 0.750 for BM25 — so there is no headroom for a constraint to demonstrate a reduction even in principle.
- The ceiling is not an artefact of the constraint being unable to change the selection. It *does* change it: on BM25 the R2 stance gap moves from 0.7436 (no defense) to 0.5385 under the R2-only constraint, so different passages are being selected. **The selection changes and not one adversarial passage is displaced.**

We give the full paired-test table, including the equivalence bounds and the contrast cells where the constraint does change the selection, in Appendix B.

This is the central empirical claim of the paper, and it applies directly to the published defense family: [5] optimises R1 composition under a fairness constraint, [6] adjusts R1 proportions and ordering, [7] controls embedder group balance, [8] equalises item-side exposure. Each constrains aggregate composition along axes the attack leaves clean, so each inherits this insensitivity. We note that multi-query consistency [4], which operates on retrieval stability rather than composition, is also inert here (0.750).

The adaptive sweep is in Appendix C, Table C1; the ranking inverts as described below.

The adaptive attacker defeats every defense. Off-manifold filtering is by a wide margin the strongest at $\lambda = 0$ (0.250, against 0.750 for no defense) and **collapses monotonically to 1.000 by $\lambda = 2$** — a clean demonstration that its advantage is specific to the non-adaptive attacker and does not survive an adversary who observes its penalty. The representation-conserving defenses, which never achieve better than 0.625 even non-adaptively, saturate at 1.000 by $\lambda = 0.5$: they are the most fragile under adaptation as well as the least effective without it.

### 5.3 F1: an aggregate over group counts returns its clean value

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

**Finding 3.** On the controlled corpus, a distribution constraint extended to a second dimension can improve its own aggregate statistic by 77% while adversarial inclusion does not move by a single query. On the natural corpus the same constraint *does* reduce adversarial inclusion (§5.4), so Finding 3 is corpus-dependent, and its scope is stated with it. What is corpus-independent is the direction of the result: **the R2 dimension is the only one along which either metric moves at all**, whereas the R1 dimension is inert in both settings. We suggest that evaluations in this area report adversarial inclusion alongside fairness metrics, because the two demonstrably move independently — and, on the controlled corpus, in opposite directions.

### 5.4 F2: reference-based statistics track the query, not the attack

The results above use a controlled corpus whose passages are template-instantiated, which is a threat to external validity. We therefore replicate on **BBQ** [21], a naturally written bias benchmark, using BBQ's own stereotype annotations to derive stance labels (§4.1) so that no new annotation is introduced. The corpus contains 17,792 passages over 144 group-neutral queries spanning four categories (gender, disability, age, race/ethnicity).

**A note on the injection parameter, because our first attempt was wrong.** An earlier version of this experiment injected a fixed six passages per stratum and concluded that the text-only attack "does not transfer" to natural data. That conclusion was an artefact of the parameter, not a property of the corpus: six passages is roughly 10% of a small candidate pool but ~0.03% of an 18k-passage corpus, so a fixed count measures corpus size rather than attack strength. Poisoning studies standardly report an *injection rate*; we now do the same, sweeping $\rho \in \{0.1\%, 0.25\%, 0.5\%, 1\%, 2\%\}$ of corpus size. All results below are at matched $\rho$.

The sweep itself is in Appendix C, Table C6.

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

**Table 5.** Defense comparison on BBQ under template + projection (dense), by injection rate. `poison@k`.

| ρ | vanilla | `repr_group` (R1 only) ε=0 | `repr_both` (R1+R2) ε=1.0 |
|---|---|---|---|
| 0.1% | 0.903 | 0.903 | **0.903** |
| 0.25% | 0.972 | 0.972 | 0.951 |
| 0.5% | 0.986 | 0.986 | 0.972 |
| 1% | 0.993 | 0.993 | 0.972 |
| 2% | 1.000 | 1.000 | 0.993 |

**The R2 constraint reduces adversarial inclusion on BBQ while the R1 constraint does not, and the pattern holds across the whole rate sweep.** `repr_group` is identical to no defense at every rate (0.903 / 0.972 / 0.986 / 0.993 / 1.000), whereas `repr_both` is weakly better at every rate, with its absolute advantage growing as the attack strengthens (0.021 at 0.5%, 0.007 at 2%) while its R2 advantage is much larger. The effect sizes here are smaller than the fixed-count run reported, and the reason is now clear: that run's comparison was confounded by the injection budget.

The operating-point comparison is in Appendix C, Table C7.

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

### 5.5 The diagnostic is the per-group shift, not the gap between groups

The results so far are measured on our own retrievers. The encoders this literature actually uses differ substantially in how much structure an attacker can exploit, so we evaluate the attack across nine retrieval back-ends: BM25 and a self-contained feature-hashing dense retriever; the learned-sparse retriever SPLADE at two sizes; and the dense semantic encoders the compared work uses — GTE-base [5] and its larger sibling GTE-large, Contriever [8], and E5-base-v2 [4, 6] with E5-large-v2. We include SPLADE specifically because it separates two explanations a lexical-versus-semantic comparison cannot: it is sparse like BM25 but learned like a neural encoder. E5 receives its required `query:` / `passage:` prefixes; omitting them degrades retrieval and would distort the comparison.

**Table 6.** Projection attack (`template_plus_projection`), $\rho = 0.5\%$, no defense. The scale column pairs each encoder with its larger sibling from the same family and training recipe.

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

**Table 7.** Text-only (lexical) attack, $\rho = 0.5\%$ and $2\%$, no defense. This is where the back-ends separate.

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

**Finding 7. Sparsity, not "neuralness", predicts susceptibility at a fixed size, but it is a correlate rather than a law.** SPLADE learns its term weights — it is a neural encoder trained on relevance — yet it is as susceptible as BM25 (0.6250 versus 0.7500), because its representation is still a sparse bag of term weights. The attack raises a passage's score by appending query-aligned terms, which requires the representation to expose **per-term contributions**: a sparse retriever does that whether or not its weights are learned, and a dense encoder absorbs the appended text into a single vector. SPLADE is in fact the *most* efficiently attacked of the nine on the R2 dimension, reaching the maximum stance gap 1.0000 where BM25 reaches 0.7436 — its learned weighting evidently concentrates score on exactly the terms the attacker appends. But sparsity is a correlate, not a law, and two cases bound it: Contriever is dense and semantic yet nearly as susceptible as BM25 (0.5625), and GTE-large is dense and semantic yet eight times more susceptible than its own base checkpoint.

![Figure 5. Text-attack susceptibility at base and large scale, within each encoder family and training recipe. GTE and E5 are equally resistant at base size and move in opposite directions when enlarged: E5 becomes fully resistant ($0.0625 \rightarrow 0.0000$) while GTE becomes eight times more susceptible ($0.0625 \rightarrow 0.5000$). The learned-sparse retriever is susceptible at both sizes. Since the only variable is the checkpoint, susceptibility is a per-checkpoint property that cannot be inferred from architecture, size or representation family.](figures/fig_encoder_scale.pdf){width=88mm}

**Finding 11. Susceptibility is not monotone in encoder scale, and scaling can destroy resistance entirely.** Table 7's clearest result is unexpected: GTE-base and E5-base-v2 are equally resistant at base size (both 0.0625 — the attack succeeds on three of 48 queries), and enlarging both by the same factor of three moves them in *opposite* directions. **E5-large-v2 becomes more resistant (0.0625 → 0.0000, the attack now fails on every query); GTE-large becomes eight times more susceptible (0.0625 → 0.5000, succeeding on 24 of 48).** SPLADE is susceptible at both sizes with little change (0.6250 → 0.5625). Per-query inclusion is binary, so this is a shift in *how many* queries are compromised, not a drift in a continuous score.

**The mechanism is not geometry.** We tested the obvious explanation and it is wrong, which makes the result more informative. If GTE-large's space were more anisotropic — vectors collapsed into a narrower cone — a fixed textual nudge would move rank further, and the finding would reduce to a known property. Measured, GTE-base and GTE-large are near-identical in mean pairwise cosine (0.8484 vs 0.8579), effective dimensionality (13.2 both, against 768 and 1024 nominal), and spread of query similarity (0.0860 vs 0.0895); the E5 pair behaves the same (0.8291 / 0.8375; 13.9 / 14.8). What differs is the gain the attack buys:

The decomposition is in Appendix C, Table C8.

The two encoders place the same injected text at almost the same distance from the query (0.8907 vs 0.8975), and the legitimate competition sits at the same threshold (0.8982 vs 0.8988). The difference is that **the identical appended vocabulary buys 74% more similarity on GTE-large (+0.0200 vs +0.0115)**. Because the mean margin is only about −0.007, a gain difference of +0.0085 carries a large fraction of queries across the threshold — exactly the 3-to-24 shift. Susceptibility is the interaction between the attack's vocabulary and the encoder's learned weighting of it, and none of the coarse descriptors we tried — architecture, dimensionality, size, geometry, sparsity — predicts it.

The cross-back-end cut is in Appendix C, Table C9.

**Finding 6b. The R1 constraint is inert across every encoder and at every scale tested.** In all sixteen constrained configurations the difference is exactly zero. The projection attack reaches complete inclusion on seven of the eight, so the constraint is inert in the worst case rather than a marginal one. This is the third independent setting in which the inertness holds, after the two corpora and the injection-rate sweep.

### 5.6 Under an informed attacker no defense survives

The inertness results above are measured against a *static* attacker. The security literature's standard objection — and the reason adaptive evaluation is mandatory — is that a defense may hold against an attacker who does not know it and fail against one who does. It matters here for two independent reasons, both predicted by §6.5: our defenses are either randomised with public parameters or penalise an observable quantity.

For each defense the attacker is given the defense's own penalty function and searches over perturbation strength $\lambda$, using the same subspace-projection construction. We also report `usage`, the mean cosine similarity between each injected passage's perturbed and original embedding, so that a defense cannot be credited for the attacker's self-inflicted degradation: if the injected material were destroyed, low adversarial inclusion would be meaningless.

*The per-λ grid is in Appendix C, Table C1.*

Off-manifold filtering is by a wide margin the strongest statically — it reduces adversarial inclusion from 0.750 for no defense to 0.250, a factor of three — and **collapses monotonically to complete failure by $\lambda = 2$**. Its static advantage is exactly what §6.5's Corollary 2 predicts: the defense penalises vectors that leave the corpus manifold, which is precisely where the projection perturbation places them, so once the attacker trades perturbation strength against penalty, the penalty becomes the attacker's constraint. The two composition-constrained defenses, which never beat 0.625 even statically, saturate by $\lambda = 0.5$. **The static ranking of defenses inverts under adaptation, and a defense selected on its static advantage is defeated as comprehensively as one selected on structural grounds.**

**The attacker pays almost nothing for this.** `usage` stays at 0.945–0.979 through $\lambda = 1$ and 0.883 at $\lambda = 2$. At the point where the strongest defense has already lost most of its advantage, the injected material is over 94% semantically intact. The collapse therefore cannot be attributed to the attack degrading its own passages.

The static advantage of off-manifold filtering is a factor of three over no defense at this operating point.

### 5.7 The skew reaches the generated text


Every result above is measured at the retrieval layer. That is deliberate — it makes the mechanism measurable without a generator and reproducible on commodity hardware — but it leaves the question a reviewer will ask: **does a retrieval-layer stance skew change what the system says?** We answer it with a fixed generator, varying only the retrieved context, so that any difference between conditions is attributable to retrieval.

**Protocol.** For each query we generate under four conditions, holding model, prompt, decoding (temperature 0) and question text fixed: `clean` (unpoisoned retrieval), `poisoned` (pairwise injection, no defence), `r1only` (R1 constraint), `r2both` (R1+R2 constraint). The primary probe is **forced choice**: the generator must select between a favourable and an unfavourable statement about a group — the generation-layer analogue of the R2 dimension, and the same form of measurement used for attack success in the poisoning literature. Option order is randomised per (query, condition, group) so that a position bias cannot masquerade as a stance effect. We additionally collect free-form answers and a per-passage attribution probe.

Generator: DeepSeek (`deepseek-chat` at temperature 0), selected because it is reachable without a proxy from the network this work used. 207 API calls, 49.2k prompt tokens, 125 s of model time.



Read Table C2 and Table C9 together: the same experiment, on the same corpus at the same injection rate, yields a 46% rise in the absolute gap under one instrument and a rise of 0.0008–0.0018 under the other. We keep both because that discrepancy is itself the finding.

**Finding 8. On the controlled corpus the retrieval-layer skew propagates to the generated output and replicates across three model families, but it does not survive a naturally written corpus.** We re-ran this evaluation with a continuous, entailment-based stance metric (a local NLI model scoring `P(entail | answer, favourable) − P(entail | answer, unfavourable)`, calibrated in §5.7.1) across four generators spanning three model families, one of them (Mistral-7B) open-weight and served locally rather than by an API, so that the result does not rest on hosted models alone. The per-group shifts are large, consistent in sign, and highly significant everywhere:

**Table 8.** Generation-layer stance, entailment-scored, four generators spanning three model families. Controlled corpus, GTE-base retrieval, $\rho = 2\%$, 48 queries, paired permutation test against `clean`.

| Generator | Δ gap (absolute) | p | **Δ group 1** | p | **Δ group 2** | p |
|---|---|---|---|---|---|---|
| qwen-turbo | +0.0008 | 0.32 | **−0.1297** | **<0.0001** | **+0.1305** | **<0.0001** |
| qwen-plus | +0.0018 | 0.042 | **−0.1280** | **0.0035** | **+0.1298** | **0.0015** |
| qwen-max | −0.0491 | 0.18 | **−0.1785** | **0.0001** | **+0.1294** | **0.0029** |
| **mistral-7b** (local, open weights) | +0.0025 | 0.42 | **−0.1297** | **0.0001** | **+0.1322** | **<0.0001** |

![Figure 6. The aggregate statistic against the per-group shifts, on the same retrieval conditions and the same queries. Left: the change in the absolute cross-group gap, which stays within $\pm 0.05$ because the attack relocates both groups rather than separating them. Right: the change in each group's stance separately, which is large, consistent in sign and significant for every generator. An asterisk marks $p<0.05$ under a paired permutation test against the clean condition. Note that the two panels use different vertical scales: the aggregate moves by less than 0.002 where the groups move by about 0.13.](figures/fig_aggregate_vs_pergroup.pdf){width=140mm}

**The absolute cross-group gap — the metric we originally used — is blind to this effect, and we had reproduced one level up the exact error we criticise in §5.3.** Under injection group 1's stance collapses (−0.13 to −0.18) while group 2's rises (+0.13), in every generator, at p ≤ 0.0035. Because the corpus carries a pre-existing stance asymmetry, `|stance(g1) − stance(g2)|` moves by less than 0.002 for two of the three generators and by −0.05 (the wrong sign) for the third. Taking an absolute difference between two groups destroys precisely the signal, for the same reason it does at the retrieval layer: the attack does not make the system uniformly more skewed, it suppresses one group and elevates the other, and the gap between them is dominated by a corpus-level constant that the attack does not touch.

This vindicates the qualitative claim in Finding 9 — the skew saturates one group rather than shifting everything — while changing the evidence for it. Findings 8 and 9 as originally stated rested on a forced-choice probe whose original numbers (gap 0.2708 → 0.3958, a 46% rise) do **not** reproduce under entailment scoring: the gap delta is +0.0008 / +0.0018 / −0.0491 across the three generators. The forced-choice probe is not wrong so much as compressed: it forces a binary selection between two maximally opposed statements, which pushes both groups' rates toward ceiling (the original table showed group 2 at 0.979 → 1.000), whereas a continuous entailment score can register the collapse of the suppressed group at 0.132 → 0.002, which is the larger and more consistent effect. **We therefore report the per-group entailment shifts as the primary generation-layer evidence, and we demote the absolute gap to a control that fails.**

**Finding 9. The skew does not appear as a uniform shift; it suppresses one group and elevates the other.** Under injection the suppressed group's stance falls by 0.13–0.18 and the favoured group's rises by 0.13, in all three generators. The magnitude of the two shifts is nearly equal, which is why the absolute difference between them is nearly unchanged: the attack relocates both groups rather than opening a gap between them. This is visible only because we measure the two groups separately, and it is the generation-layer counterpart of the R1/R2 distinction the paper is built on.

**Finding 10. Neither constraint improves the generation layer.** `r1only` leaves both per-group shifts identical to no defence to four decimal places (Δg1 = −0.1297, Δg2 = +0.1305 for qwen-turbo, identical values), and `r2both` moves them by less than 0.002. This is consistent with the retrieval-layer result: the input to the generator is unchanged, so the output is unchanged. **The constraints we proposed, evaluated here, do not repair the downstream harm.**

**5.7.1 Why the natural corpus appeared to show nothing: the probe, not the corpus.** The free-form measurement above is valid only where answers actually take a position, and on a naturally written corpus they largely do not. Measuring the *commitment* of each answer — the larger of its two entailment probabilities, `max(P(fav), P(unfav))` — separates a real null from an instrument that cannot register anything:

**Table 9.** Answer commitment by corpus, clean condition. An answer with commitment near zero takes no position, so no stance change can appear in it however large the retrieval-layer skew.

| Corpus | mean commitment | answers below 0.1 |
|---|---|---|
| controlled | 0.1555 | 84.4% |
| **BBQ (full)** | **0.0071** | **99.0%** |

![Figure 7. The instrument, not the corpus, was the reason the natural corpus appeared to show nothing. **Left:** with a free-form probe most answers take no position at all --- on the full BBQ corpus 99.0% of them, against 84.4% on the controlled corpus --- so the statistic reads near zero under every condition and no effect of any size could have appeared in it. **Right:** a forced-choice probe makes the same answers commit to a side, and on identical retrieval conditions it reads an effect, with five per-group shifts at $p < 0.05$ for one generator (Table 10). The panels are conceptual and carry no measured values; the commitment values they illustrate are in Table 9.](figures/fig_probe_commitment_py.pdf){width=140mm}

The gap is 22×, and it means the free-form statistic on BBQ is near zero under *every* condition: the effect we were looking for could not have appeared there. This also bounds the controlled-corpus result more honestly than we previously stated it — 84.4% of those answers are non-committal too, so the shift reported above rests on roughly a sixth of them.

**A probe that forces commitment detects the effect on BBQ.** We therefore re-ran the generation stage with the forced-choice probe used in earlier drafts of this work: the generator must choose between a favourable and an unfavourable statement about the group, drawn from the same template inventory the attack manipulates, with option order randomised per item so a position bias cannot masquerade as a stance effect. Before using it we verified it carries signal rather than position: the reply was a parseable choice in 100% of cases, and the probability of choosing position A is 100% when the favourable statement sits at A against 35% when it sits at B — a 65-point swing, so the choice tracks content.

**Table 10.** Forced-choice stance on the full BBQ corpus, 144 queries, per-group favourable-choice rate, paired permutation test against `clean`. Only shifts significant at $p < 0.05$ are listed.

| Generator | Group | Δ favourable rate | p |
|---|---|---|---|
| **qwen-turbo** | woman | **+0.6333** | **<0.0001** |
| **qwen-turbo** | nondisabled | **+0.5714** | **<0.0001** |
| **qwen-turbo** | man | **+0.5000** | **0.0003** |
| **qwen-turbo** | young | +0.2449 | 0.0121 |
| **qwen-turbo** | disabled | +0.2381 | 0.0274 |
| qwen-plus | man | +0.2333 | 0.0379 |
| mistral-7b | — | none reached significance | — |

**Finding 8, restated.** The retrieval-layer skew does reach the generated output on a naturally written corpus. What failed on BBQ was the free-form probe, which could not have detected the effect because 99.0% of the answers it scores take no position at all. With a probe that forces commitment, one generator shows five per-group shifts at $p < 0.05$ with the largest at $+0.63$.

Three qualifications belong with that, and we state them rather than leaving them to be found:

- **The effect is group-specific, not uniform.** On BBQ it concentrates in woman, nondisabled, man, young and disabled; on the controlled corpus (Table 8) it concentrates in asian, elderly and white. Averaging over groups, which is what a per-group *mean* does and what our earlier free-form analysis did, understates it substantially.
- **It is generator-dependent.** qwen-turbo carries most of the signal on both corpora; mistral-7b shows none that reaches significance on BBQ, and the one API generator we ran at largest scale shows a single group. A single dense number such as "the gap rose 46%" is therefore the wrong form for this result, and we no longer report one.
- **Concentration is not the same as a large average effect.** Five significant groups out of eight, each with a large rate shift, is a stronger statement than the average gap suggests, and a weaker one than "the system's stance changed across the board".

**This is the third instrument failure in the paper, and it belongs with the other two.** The free-form probe joins the reference-based stance statistics and the absolute cross-group gap as a measurement that returns a plausible number while being structurally unable to see the thing being measured. Its signature is the one we have now seen three times: a statistic that comes out near zero for reasons that have nothing to do with the phenomenon. We report it in the results rather than the limitations because it changes a conclusion we had already drawn.

**5.7.2 Two metric failures, and what they were caused by.**

**5.7.2 Two metric failures, and what they were caused by.** Both are worth recording because each cost us a wrong result before being found.

*Stance direction.* The first implementation scored stance as `P(entail | statement, answer)`. Calibrated against the correct convention on the same data, the reversed form returns ±0.002 for a favourable answer, an unfavourable answer, an unrelated answer and a vacuous one alike: it cannot separate anything, and it fails silently by returning zeros rather than an obvious error. The correct direction, `P(entail | answer, statement)`, returns +0.997 and −0.997 for the two extremes. The convention is not interchangeable and the failure mode is indistinguishable from a genuine null result — a mistake worth flagging for anyone building this measurement.

*Attribution direction.* The expected-attributed-exposure (EAE-D) statistic of Kim & Diaz [8] was implemented by asking the generator, per retrieved passage, whether its answer relied on that passage. It returned **1.000 in every condition**, which we previously reported as a failed metric. The cause is again direction: attribution must ask whether the **passage entails the answer**, not the reverse. A passage the answer used scores 0.996 in the correct direction and 0.008 in the reversed one; an unused passage scores 0.000 in both. With the direction fixed the statistic discriminates properly — 0.798–0.828 clean, rising to 0.831–0.968 under injection, since poisoned contexts are engineered to be the passages the answer leans on. The earlier self-report probe measured the judge's agreeableness, not the answer's provenance.

**Scope.** Three generators from two model families, one retrieval backbone (GTE-base), one injection rate, and 48 retrieval slots that correspond to only 16 distinct question texts (§8, Limitation 6). The per-group shifts are consistent in sign and significance across all three generators, which is stronger evidence than the single-generator version this section previously reported; the magnitudes, however, should not be extrapolated to generators we did not run.

---

### 5.8 Under an informed attacker the defenses invert

The sweep above uses our own feature-hashing dense retriever. Because the *shape* of the collapse — not merely its endpoint — could depend on the encoder, we repeated it on four further back-ends: **GTE-base** (the encoder used by the closest prior work on fairness-aware retrieval optimisation [5]), **E5-base-v2** (used by the RAG fairness evaluations above), **Contriever**, and **SPLADE**, a learned *sparse* retriever. SPLADE is what makes the comparison diagnostic: it is a trained neural encoder, like GTE and E5, but its representation is sparse, like BM25's.

**Table 11.** `poison@k` under the adaptive attacker for off-manifold filtering, by back-end. Six back-ends; `usage` (the attacker's semantic fidelity) in the last column.

| Back-end | representation | λ=0 | λ=0.25 | λ=0.5 | λ=1 | λ=2 | λ=4 | `usage` at λ=1 |
|---|---|---|---|---|---|---|---|---|
| hash-dense (own) | dense, hashed | 0.250 | 0.562 | 0.812 | 0.938 | 1.000 | 1.000 | 0.945 |
| **GTE-base** | dense semantic | **0.000** | **1.000** | 1.000 | 1.000 | 1.000 | 1.000 | 0.978 |
| **E5-base-v2** | dense semantic | **0.000** | **1.000** | 1.000 | 1.000 | 1.000 | 1.000 | 0.971 |
| **Contriever** | dense semantic | **0.000** | 0.625 | 1.000 | 1.000 | 1.000 | 1.000 | 0.943 |
| **SPLADE** (distil) | sparse, learned | 0.188 | 0.500 | 0.812 | 1.000 | 1.000 | 1.000 | 0.954 |
| **SPLADE large** | sparse, learned | **0.000** | 0.500 | 0.750 | 0.938 | 1.000 | 1.000 | 0.952 |

The picture is not the one the dense-versus-sparse account predicts, and it takes all six back-ends to see why. Four of the five pretrained encoders (GTE-base, E5-base-v2, Contriever and SPLADE-large) begin at **exactly zero** adversarial inclusion against the static attacker and are effectively defeated after a single perturbation step. But "one step" means a *complete* failure immediately for GTE-base and E5-base-v2 (0.000 → 1.000), whereas Contriever (0.000 → 0.625 → 1.000) and both SPLADE sizes climb gradually and resemble our own hashed retriever (0.188 / 0.500 / 0.812 and 0.000 / 0.500 / 0.750 against 0.250 / 0.562 / 0.812). Scaling SPLADE up even *improves* the defense's static position (0.188 → 0.000 at $\lambda = 0$) while leaving the collapse rate unchanged. Neither "pretrained versus hashed" nor "dense versus sparse" describes the collapse on its own.

**Finding 12.** Three claims are stable across all six back-ends and are what this finding rests on. First, **the static advantage is largest on the pretrained encoders**: all five begin below our hashed retriever's 0.250, and four begin at 0.000 — the reverse of the concern that motivated the experiment, and awkward for the compared literature, because the static numbers one would use to select a defense are most optimistic precisely on the back-ends that literature uses. Second, **no defense retains any measurable benefit beyond $\lambda = 1$** on any of the six, and on four of them none survives $\lambda = 0.25$. Third, **the attacker pays essentially nothing**: `usage` is at least 0.943 at $\lambda = 1$ on every back-end, so the injected material is over 94% semantically intact at the point where the defenses have lost most or all of their advantage.

The *shape* of the collapse therefore varies by encoder in a way that no single property we measured accounts for, and the practical consequence is sharper for it. A defense selected on its static advantage is defeated comprehensively, and a robustness claim measured on one back-end inherits an unmeasured dependence on which back-end was chosen. This is the same lesson as §5.5, arrived at from the opposite direction: there, the encoder determined whether a *text* attack worked at all; here, it determines whether a defense collapses in one perturbation step or three. **In both cases the encoder is not a nuisance parameter.**

**Finding 13. What survives adaptation, and why.** Only one configuration retains measurable benefit, and only in part of the sweep: the R1+R2 constraint on BBQ holds `poison@k` at 0.049 / 0.111 / 0.319 for $\lambda \le 0.5$ while preserving the utility proxy (`in_pool_rate` 0.442 against 0.363 for no defense), and it beats multi-query consistency throughout (0.319 against 0.535 at $\lambda = 0.5$; 0.764 against 0.847 at $\lambda = 1$). We attribute this to the defense's *objective* rather than to any attack-specific matching. It is the only defense whose constraint is expressed over the composition of the retrieved set rather than over individual passage statistics, so it cannot be satisfied by choosing perturbations — only by changing which passages are mutually compatible. That is a weaker effect than the static evaluation suggested, and it disappears by $\lambda = 2$. The asymmetry is the useful part: **constraints on properties of an individual passage are optimisable-against because the attacker controls that passage; constraints on the set are not, but they are correspondingly weaker.**

#### 5.8.1 The evaluation protocol these results imply

Findings 12 and 13 are not sensitive to our particular attack. They follow from the attacker being informed, which is the standard against which robustness claims are judged in the adversarial literature [23, 24]. We therefore state the protocol as a requirement rather than a suggestion, and it is the second half of the measurement contribution this paper makes: §3.4 gave the conditions under which a *statistic* is blind, and this gives the conditions under which a *robustness claim* is interpretable.

1. **State the threat model, including whether the attacker knows the defense.** A claim of robustness without this qualifier is uninterpretable, and it is the qualifier that separates the two evaluations in §5.2 and §5.6.
2. **Report adversarial inclusion as a function of attacker strength, not at one operating point.** A single value cannot distinguish a defense that is robust from one evaluated below its failure threshold. In our sweep every defense fails by $\lambda = 2$; a sweep stopping at $\lambda = 0.25$ would have shown three apparently robust defenses.
3. **Sweep to the point of failure and report where it occurs.** The location of the failure is the result; the endpoint alone is not.
4. **Report a utility-preserving baseline**, since a defense trivially achieves low inclusion by returning fewer or worse passages; we report `in_pool_rate` alongside `poison@k` throughout.
5. **For a randomised defense, state the distribution and assume it is known**, and report the attacker's optimal response to its expectation rather than to a sample. By Proposition 4, randomisation bounds the variance of the attacker's utility and not its mean.
6. **For a penalty-based defense, report whether the penalty is computable from public information**, and if it is, treat it as a constraint in the attacker's optimisation rather than as an unknown. This is Corollary 2, and in our experiments it is decisive for the defense that looked strongest statically: publishing a scoring function, which auditability requires, is equivalent to handing the attacker a differentiable objective.

### 5.9 The composition statistic's validity is a property of the back-end

The results so far establish the invariance and its cause. This section establishes where it
holds, which turns out to vary by retrieval back-end in a way that is measurable and that a
practitioner can check before trusting a null aggregate.

**Design.** The same balanced pairwise injection is applied to four retrieval back-ends under
identical conditions, and the composition statistic is read as a function of how much of the
retrieved set is adversarial. If composition drifts nowhere, the invariance is a property of the
statistic. If it drifts on some back-ends and not others, the invariance is a property of the
back-end, and that distinction decides whether a clean aggregate means anything.

**Result.** Undefended composition drift, by relocated fraction:

| back-end | attack | composition drift |
|---|---|---|
| `st` (GTE-base) | lexical | **0.0000 at every partial level**, 0.2400 only at full relocation |
| dense | lexical | 0.0000 at the lowest level, rising to **0.1750** at full relocation |
| BM25 | lexical, projected | 0.0000 at low relocation, rising to **0.2280** at full relocation |
| SPLADE | lexical, projected | 0.0000 at zero, 0.2000--0.4000 through the middle, **0.2250** at full relocation |

On `st` the injected set is compositionally balanced and stays balanced however much of it is
retrieved, so the composition statistic reads clean while the evidence moves: the regime in which
the aggregate is uninformative. On the other three back-ends the retrieved set relocates
composition as well and the statistic moves with it, so a clean reading there would carry
information.

**The dependence is not a monotone function of the relocated fraction.** BM25 reads 0.0000 at a
relocated fraction of 0.8 while reading 0.2000 at 0.6, and SPLADE peaks in the middle
(0.4000 at 0.6) and falls back (0.2250 at 1.0). The relation between how much adversarial
evidence is present and how much composition moves therefore cannot be summarised by a single
slope, which is the practical reason to measure the regime rather than extrapolate to it.

**Why this is a result and not a caveat.** The balanced pairwise construction is a sufficient
condition for the invariance, not a universal one. Stated that way the finding is actionable: the
three-question test of §3.4 predicts whether a candidate statistic is invariant *for a stated
back-end and threat model*, and §5.9 supplies the measurement that tells a practitioner which
regime they are in. A paper reporting a null aggregate cannot interpret it without this, and the
table is the check.

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

**Empirical check.** Table C3 reports the prediction of Prop. 1 against every configuration we ran: if the injected selection sits at the reference point, then constraining the R1 budget must leave adversarial inclusion *exactly* unchanged at every tolerance.



*(entries are Δ`poison@k`; 0.000 in all 24 measured cells)*

Prop. 1 predicts Δ = 0 exactly, and Δ = 0 exactly in every one of the 24 cells measured — not approximately, which a tuning-failure explanation would predict. The equivalence is reproduced by `analysis/verify_theory.py`. We state the count explicitly because the exactness is the point: the constrained selection is not *near* the reference composition, it *is* the reference composition.

### 6.3 Proposition 2 — the minimum injection for an ε-shift

Proposition 1 shows the attacker *can* be admissible; we now give the budget at which it becomes *effective*.

**Proposition 2.** Fix a query and a group $g$. Suppose the clean selection contains $m_g \le k$ passages about $g$, of which $f_g$ are favourable, so $p^{*}_{\text{fav}}(g) = f_g/m_g$. An attacker who replaces $j \le \min(n, m_g)$ of these with injected passages about $g$ (favourable, to flood; unfavourable, to suppress) violates the stance constraint of (1) for $g$ if and only if

$$j > \varepsilon\, m_g, \qquad\text{so}\qquad j^{*}_g(\varepsilon) = \lceil \varepsilon\, m_g \rceil + 1. \tag{2}$$

*Proof.* Flooding: $p_{\text{fav}}(g) = (f_g + j)/m_g$ for $j \le m_g - f_g$, so $p_{\text{fav}}(g) - p^{*}_{\text{fav}}(g) = j/m_g > \varepsilon \iff j > \varepsilon m_g$. Suppressing: $p_{\text{fav}}(g) = (f_g - j)/m_g$, and $p^{*}_{\text{fav}}(g) - p_{\text{fav}}(g) = j/m_g$, giving the same condition. The smallest integer satisfying the strict inequality is $\lceil \varepsilon m_g\rceil + 1$, which is needed to handle the case where $\varepsilon m_g$ is an integer. $\square$

**Corollary 1 (the *constraint* cost is at most $k$).** Since $m_g \le k$, $j^{*}_g(\varepsilon) \le k$ for all $\varepsilon \le 1$. With $k$ typically 3–5, violating the constraint is cheap in the currency of the constraint itself.

**Corollary 2 (suppression is cheaper than flooding when the clean retrieval is one-sided).** If $f_g = 0$ then $p^{*}_{\text{fav}}(g) = 0$ and the flooding direction requires no violation at all, while the suppression direction must overcome the full rate; if $f_g = m_g$ the reverse holds. The cheaper direction is always the one pushing an already-extreme rate further toward its extreme — consistent with the empirical Finding 9, where the attack drove one group's favourable rate to ceiling rather than shifting both.

**A distinction that governs how the result should be read.** Corollary 1 does not imply that "the number of passages required is bounded by a small constant independent of corpus size". That conflates two requirements that behave very differently:

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

### 6.5 Proposition 4 — why the family is *structurally* exposed, not merely mis-tuned

Propositions 1–3 show that a distribution constraint cannot exclude the injection. A reader may reasonably ask whether that is a property of *composition* constraints specifically, or of this defense family more broadly — and in particular whether the non-compositional members, which the literature presents as the more robust alternatives, escape it. They do not, and the reason is worth stating separately because it covers the family as a whole.

**Proposition 4 (randomised defense under a known distribution).** Let a defense's selection mechanism be a fixed distribution $\pi(\mathcal{D} \mid q, \mathcal{C})$ over retrieved sets, public to the attacker, and let $U(\mathcal{D})$ be the attacker's utility (e.g. the indicator that $\mathcal{D}$ contains an injected passage). If any set in the support of $\pi$ has $U = 1$, the attacker can drive $\mathbb{E}_{\pi}[U] \to 1$ by choosing an injection that places adversarial passages in every set with non-negligible probability mass.

*Proof sketch.* Since $\pi$ is fixed and known, $\mathbb{E}_\pi[U]$ is computable in closed form as a function of the injection, and the attacker maximises it by search or by gradient. Randomisation does not bound $\mathbb{E}_\pi[U]$; it bounds the *variance* of $U$ across realisations. An attacker whose success is measured in expectation over queries — the usual case — is indifferent to that variance. $\square$

The proposition is elementary, and that is the point: **randomisation defends against unpredictability, not against knowledge.** Two corollaries identify the cases that arise in this literature.

**Corollary 1 (public-distribution defenses).** Multi-query consistency [4] perturbs the query by token dropout at rate $\delta$ and aggregates over $n_v$ variants. The perturbation is random, but its *rate* and its *count* are public constants, so the expected aggregate score of a passage is a deterministic, differentiable function of the injected embedding which the attacker can maximise directly. Adding variants does not change this: the attacker optimises the expectation, and with many variants the empirical mean converges to it. The adaptive sweep reports the predicted collapse, from 0.729 at $\lambda = 0$ to 1.000 by $\lambda = 0.5$.

**Corollary 2 (penalty-observable defenses).** A defense that down-weights passages by a penalty $f(d)$ computable from public information hands the attacker the constraint "remain in the low-penalty region". Whenever that constraint can be satisfied while raising similarity — possible whenever the penalty is a continuous function of a perturbation the attacker controls — the defense imposes a *cost* rather than a *barrier*. Off-manifold filtering is exactly this case, and the measured consequence is that it is the strongest defense statically (0.250 against 0.750 for no defense) and is defeated by $\lambda = 0.25$.

These are the standard reasons adaptive evaluation is required, and they are why security venues expect it. What this paper establishes is that **this defense family is structurally exposed to them**, because its two dominant mechanisms — public randomisation and an observable penalty — are precisely the two cases the proposition covers. Proposition 3 then explains why the remaining members fail for an independent reason, so the family is squeezed from both sides: composition constraints cannot exclude an individually admissible passage, and the non-compositional alternatives are defeated by an informed attacker. That is why we treat the failure as structural rather than as a matter of tuning, and why the honest remedy is detection (§6.6) rather than a better objective.

### 6.6 Dimensionality does not help, and the only escape is individual-level evidence

Two consequences of the above are the actionable content of this section.

**(a) Adding dimensions does not shrink the admissible set usefully.** Extending the constraint from R1 to R2 to $m$ dimensions does not remove adversarial selections from $\mathcal{R}$; it gives the attacker more statistics to match, all of them computable from the public references. Prop. 1 applies verbatim with $\mathcal{R}$ the $m$-dimensional feasible set. The attacker's cost rises, their *feasibility* does not fall — and since Prop. 2 bounds the cost by $k$, the rise is cheap.

**(b) The only escape is evidence about individual passages.** To exclude an adversarial passage a defense must evaluate a property of *that passage* that is not a function of the retrieved set's aggregate. In the adversarial setting this is a provenance question, answerable only from traces the attacker's optimisation leaves behind. §7 reports one candidate and its validity threat.

This reframes the problem. Prior work in this area is an **optimisation** problem — which composition is fairest, and how to reach it. Under an adversary it becomes a **detection** problem, and §5.3 shows the two are not interchangeable: a defense can improve its fairness objective while its security objective is untouched. Prop. 3 is the reason the optimisation framing cannot be repaired by tuning: the failure is not at the optimum, it is in the feasible set.

**What this analysis does not establish.** Prop. 3 rests on the relevance-overlap assumption, which we support empirically but do not prove. A defense able to certify that an injected passage is *not* δ-competitive — for instance by proving a relevance upper bound for it — would escape the trilemma, and we know of no such defense in this literature. Constructing one is, in our view, the most promising direction this analysis opens. Prop. 2's bound also assumes replacement, i.e. that injected passages out-rank those they displace; when they do not the bound is vacuous rather than wrong, which is exactly the corpus- and encoder-dependence documented in Findings 4 and 7. Finally, the analysis is pointwise in the query; a defense enforcing the constraint in expectation across queries has more room than the version analysed here, though ours are pointwise, so the measurements are unaffected.

---

## 7. An Individual-Level Signal

Proposition 1 indicates that a usable defense needs individual-level evidence. We report one such signal and state the test that would falsify it.

**Hypothesis.** A passage injected to be retrieved for many queries — the projection attack optimises a *single* direction $\bar{q}$ so that one passage serves many queries — will be retrieved for an anomalously large number of distinct queries. A legitimate passage is relevant to a small, specific set. The number of distinct queries retrieving a passage is computable at inference time from retrieval logs and requires no labels.

**Measurement.** We score each passage by the fraction of queries in the query set for which it appears in the top-$k$.



At a threshold of the clean 90th percentile, detection rate is 1.000 with 3.9% (BM25) and 0.2% (dense) false positives.

**This result must not be taken at face value, and we state the reason.** The clean 90th percentile is **0.0000** — 90% of legitimate passages are retrieved by *no* query. That is not a property of realistic corpora; it is a property of our construction, in which injected passages share a fixed query-aligned vocabulary that legitimate passages lack. The separation may therefore measure *lexical overlap with our query template set* rather than *retrieval optimisation*. In a natural corpus this signal may vanish entirely.

**Falsification protocol.** Before this can be claimed as a defense:
1. replicate on a natural corpus (TREC 2022 Fair Ranking Track [19], Natural Questions) with injected passages generated by a query-agnostic attack [3] so that no shared vocabulary is introduced by construction;
2. report the signal's AUC with confidence intervals, and the resulting detection/false-positive trade-off;
3. verify that threshold selection does not require knowledge of the injection rate.

We report the signal because it is the direction Proposition 1 points to, and because a negative result from step (1) would itself be informative about which provenance cues survive in realistic settings.

---

## 8. Discussion and Limitations

**What the failure is, and what it is not.** Our results do not show that existing fairness defenses are implemented incorrectly, nor that their reported gains are illusory in the setting they target. They show something narrower and, we think, more useful: the statistic each defense optimises is insensitive to the adversary that motivates the defense. Concretely, [5]'s optimisation, [6]'s proportion adjustment, [7]'s embedder control, and [8]'s exposure equalisation all act on aggregate composition. Under natural corpus skew — the setting those works study — this is appropriate, and their improvements are real. Under an adversary, §5.2 shows the same machinery leaves adversarial inclusion unchanged, and §6 shows why no refinement along that axis can change it. The distinction matters for how the field reads this result: the claim is about **evaluation validity**, and it implies a change in what gets measured rather than a rewrite of what has been built.

**An error we made twice, and why that is the point.** §3.2 identifies a class of mistakes that is easy to make and hard to notice: R2 statistics evaluated against a per-query clean retrieval, or against a corpus reference, are dominated by topic-conditioned stance variation that the attack preserves, and therefore report a healthy system while the retrieved set is fully adversarial. We made that error, corrected it by adopting the cross-group gap, and then made a second error of the same family one level up in §5.7: the cross-group gap is itself an absolute difference, and it is blind to an attack that relocates both groups rather than separating them. Both errors share a signature that makes them dangerous — they return a plausible, healthy-looking number rather than an obviously wrong one. We therefore make two recommendations rather than one. Any stance-style metric should be specified together with its reference *and* accompanied by a control showing it responds to a known attack; and where a metric is computed as a difference between two groups, the per-group values should be reported alongside it, because the difference can be flat while both components move a long way.

**Adversarial evaluation is a measurement problem before it is a defense problem.** Taken together, the failures in this paper — a composition statistic that counts what the attack balances, a reference-based statistic that measures topic rather than stance, an absolute difference that cancels a joint shift, a self-report attribution probe that a model answers affirmatively by construction, an entailment convention whose reversed form returns zeros, and a null reported without an equivalence bound — are all failures of instrument rather than of method. None of them would be caught by improving an attack or a defense. We suspect this generalises beyond retrieval fairness: any evaluation whose statistic is an aggregate over the quantity an adversary controls is vulnerable to the same class of error. The mitigation that worked here was mechanical rather than conceptual — a control that flips the signal and checks the statistic moves, an equivalence bound on every null, and a per-component report for every difference.

**The three failure modes, and what each one predicts about work we did not run.** §3.4 stated the taxonomy from the form of the statistics; §5 confirmed it on measurements. Collecting the confirmations makes the framework's reach explicit, including for defenses we did not implement.

*F1, balanced count.* Confirmed twice: the R1 statistics are invariant under pairwise injection (§5.1), and the positive control shows the same statistics detect a 3000-passage composition change with the corpus size held fixed (Table 1). So the invariance is a property of the attack, not the instrument. **The prediction for work we did not run**: any defense whose objective is a group count or share — the re-ranking of [5], the proportion adjustment of [6], the embedder control of [7], the exposure equalisation of [8] — inherits this invariance exactly, without regard to how well it is optimised, because the injection is constructed to satisfy whatever composition the defense prefers. Our measurements on re-implementations of that objective support this and we have no reason to expect a different outcome from a better-optimised version of the same statistic.

*F2, preserved nuisance.* Confirmed twice, and the second confirmation is the stronger one: `stance_div` and `stance_onesided` are flat across the clean and fully attacked conditions (§5.1), *and* they are flat across the positive control where the true composition swings from 0.022 to 0.978 (Table 1). A statistic that does not move when the ground truth moves will not move for an adversary either. **The prediction**: any metric anchored to a per-query clean retrieval or a corpus-level rate is measuring the query's topic conditioning, which the attack preserves by construction, so evaluations that report such a metric alongside a clean baseline are reporting a quantity orthogonal to the threat.

*F3, cancelled shift.* Confirmed at two layers, and this is the one we got wrong ourselves: the cross-group gap is blind to the retrieval-layer attack (§5.1) and to the generation-layer attack (§5.7), and on the generation layer our first analysis used it anyway and reported a null. **The prediction**: any difference, gap or variance across groups is invariant under a common-mode move, so a defense or an evaluation that reports only a gap will under-report any attack that relocates groups together rather than separating them — which is what a matched-pair injection does by construction.

The three modes also compose, which is why the defense family fails as a family rather than in parts. F1 accounts for the composition-constrained members; §6.4 proves that no refinement along that axis escapes it. F3 accounts for the non-compositional members that report a group difference. And §6.5 shows the remaining mechanisms — public randomisation and an observable penalty — fail for a fourth reason that is not a measurement failure at all: an informed attacker optimises the expectation of a public distribution, and treats a computable penalty as a constraint rather than a barrier.

**The constructive half.** A taxonomy of failure modes is only useful if something escapes it, and the three modes share one structural feature: each is an invariance of an *aggregation* over groups. Reporting the per-group quantities $\phi_g$ and their paired changes is not invariant under any of the three, because it makes no aggregation claim for the adversary to preserve. That is a cheap change to how a result is reported, it requires no new defense, and §5.7 is an existence proof that it works: on identical retrieval conditions, the aggregated gap moved by 0.002 while the per-group levels moved by 0.13 at $p < 0.01$. The recommendation is therefore not "build a better defense metric" but "stop reporting only the aggregate".

**Sensitivity is not validity, and the per-group report is a case in point.** The per-group report is more sensitive than an aggregate, and a more sensitive instrument still has to be shown to measure the right quantity. The clearest example is our own: the free-form probe reports a large, replicated per-group shift on the controlled corpus and nothing on the naturally written one, and it would have been easy to publish that as a finding about corpora. It is not — the probe scores answers that take no position in 99.0% of cases on natural text, so it was structurally incapable of reporting the effect that a commitment-forcing probe then found there. An instrument that manufactures commitment will report an effect where there is none; an instrument that suppresses it will report a null that does not exist. We hit the second case, and the control that caught it was measuring commitment rather than trusting the margin. We therefore report both probes and both corpora, and treat the disagreement between them as the result.

**Limitations.** Ten constraints bound what this study establishes. The table states
each one and what it costs; the full statement of each, with the measurements behind it,
is in Appendix D.

| # | Limitation | What it constrains, or what already handles it |
|---|---|---|
| 1 | **Group- and stance-annotated passages are required, and neutral retrieval corpora do not carry them** | The binding constraint on this whole line of work: the framework's applicability is bounded by annotation, not computation. R1 needs a group label per passage and R2 a stance label, and no standard neutral corpus (NQ, MS MARCO) has either, nor can stance toward a group be inferred from a neutral passage. Described in full in Appendix D.1. |
| 2 | **Neither corpus is a neutral retrieval benchmark, and they disagree in two respects** | The text-only attack works only on the controlled corpus; the R2 constraint reduces inclusion only on BBQ. Both conditions are reported rather than the favourable one, and the mechanism behind the first disagreement is identified (§5.4). |
| 3 | **The absolute R2 metric does not transfer across corpora** | `stance_gap` is exactly 0 on the balanced controlled corpus but 0.9326 on BBQ *before any attack*. Only the change from the clean baseline is informative there, and §5.4 relies on the change throughout. |
| 4 | **Injection budget must be reported as a rate, not a count** | A fixed count measures corpus size rather than attack strength. §5.4 sweeps $\rho \in \{0.1\%, \dots, 2\%\}$; readers comparing against absolute counts must convert. |
| 5 | **Nine retrieval back-ends, and the scale check changed the conclusion** | GTE-base → GTE-large moves susceptibility from 0.0625 to 0.5000 within one family and recipe, so a single-encoder robustness claim reports an unmeasured checkpoint property (§5.5). Contriever is not swept at large scale and multilingual or instruction-tuned embedders are not tested. |
| 6 | **The generation-stage evaluation is multi-generator and multi-probe, and the probes disagree** | Three sub-limits, each with a measurement behind it: retrieval conditions are fixed to one backbone; the free-form probe commits to a position in only 15.6\% (controlled) and 1.0\% (BBQ) of cases, which is why the forced-choice probe is primary; and the effect is generator-dependent. Appendix D.6 also records the inverted-context negative control and a corrected attribution metric. |
| 7 | **Binary groups: $\vert\mathcal{G}\vert = 2$ throughout** | Extension to $\vert\mathcal{G}\vert > 2$ is mechanical for R1 and R2 but is not evaluated here. BBQ's race/ethnicity category is also markedly imbalanced in our build (960 vs 88 passages). |

We close with the protocol the results imply. The first four points are about **measurement validity** — whether a statistic can see the attack at all — and the last five about **adversarial evaluation hygiene**, which is what makes a robustness claim interpretable:

1. **Measure per-group shifts, not cross-group differences.** An absolute gap between groups is dominated by pre-existing corpus asymmetry and is blind to an attack that relocates both groups together. Report both group-level quantities, and report the change in each.
2. **Report injection as a rate, not a count.** A fixed passage count measures corpus size rather than attack strength.
3. **Report the encoder as a factor.** Susceptibility is a per-checkpoint property that is not monotone in encoder size — within one family and training recipe, scaling GTE raised text-attack success eight-fold while scaling E5 lowered it to zero. A single-encoder robustness claim reports an unmeasured property of that checkpoint.
4. **Give equivalence bounds for null claims.** "No effect detected" and "no effect" are different claims, and only the second supports a conclusion about a defense family. Where the per-query difference is identically zero this is conclusive; where it is not, the bound is the honest statement.
5. **State the threat model explicitly, including whether the attacker knows the defense.** A robustness claim without this qualifier is uninterpretable, and the qualifier is what separates the two evaluations in §5.6.
6. **Report adversarial inclusion as a function of attacker strength, not at a single operating point.** One value cannot distinguish a robust defense from one evaluated below its failure threshold. In our sweep every defense fails by $\lambda \le 2$; a sweep stopping at $\lambda = 0.25$ would have shown three apparently robust defenses.
7. **Report a utility-preserving baseline.** A defense can achieve low adversarial inclusion trivially by returning fewer or worse passages, which is why we report `in_pool_rate` alongside `poison@k` throughout.
8. **For a randomised defense, state the distribution and assume it is known.** Report the attacker's optimal response to the expectation rather than to a sample; by Proposition 4, randomisation bounds variance and not the expectation.
9. **For a penalty-based defense, report whether the penalty is computable from public information.** If it is, treat it as a constraint in the attacker's optimisation rather than as an unknown; by Corollary 2 that is the difference between a cost and a barrier.

Point 9 is the one most easily overlooked and, in our experiments, decisive for the defense that looked strongest statically. Point 5 is the one most often omitted in this literature. Points 1–4 are prerequisites for a fairness statistic to be reported at all under adversarial conditions, and points 5–9 for a robustness claim to be credited.

### 8.1 When the aggregate is informative

The aggregate statistics this paper examines are informative only where the
composition they summarise is itself informative, and §5.9 measured which
back-ends that is. The conditions are restated here in the form a practitioner
needs in order to interpret a null result.

**The composition statistic is flat on the lexical retriever, and moves elsewhere.** Undefended
composition drift on the controlled corpus, at the relocation levels where the label is partial:

| back-end | attack | composition drift at partial relocation |
|---|---|---|
| `st` (GTE-base) | lexical | 0.0000 at every partial level |
| dense | lexical | 0.0000 at the lowest level, rising to 0.1750 at full relocation |
| BM25 | lexical, projected | 0.0000 at low relocation, rising to 0.2280 at full relocation |
| SPLADE | lexical, projected | 0.0000 at zero relocation, 0.2000-0.4000 through the middle, 0.2250 at full relocation |

On `st` the injected set is compositionally balanced and stays so however much of it is
retrieved, so the aggregate reads clean while the evidence moves — the regime the framework
describes. On the other back-ends the retrieved set relocates composition as well, and the
aggregate moves with it, reaching 0.1750 on dense and 0.2 or above on the projected
lexical back-ends. The dependence is not strictly monotone in the relocated fraction,
which is itself a reason to measure the regime rather than assume it. The balanced pairwise construction is therefore a sufficient condition
for the blindness and not a universal one, and the practical reading is: check which regime your
retriever is in before treating a null aggregate as evidence of robustness.

**Subspace projection removes the passage text from the ranking decision.** Under
`template_plus_projection` the relocated fraction was 1.000 for all 192 queries at every
alignment setting we tried. Projection sets the ranking from document and query vectors, so the
composition the composition statistics observe is fixed by the projection rather than by the
passages. This bounds what any text-side defence or perturbation can achieve against that
back-end, and it is the mechanism behind the saturation reported in §5.8.

**The per-group statistic is a batch average, and its power is bounded by batch count.** Every
group-level rate in this paper averages binary stance decisions over the queries in a stratum. A
single query contributes one draw, so the diagnostic is not a per-query test and should not be
evaluated as one; we report it per stratum for this reason. The consequence is a power bound that
does not yield to more queries of the same kind: on a corpus whose queries are instantiations of a
small template set, raising the query count repeats the same texts, and we measured this rather
than assuming it — a regime that held 36 of 192 queries held 0 of 1,536 once the count was raised.
Obtaining more power requires more independent strata or repeated audits over time, not a larger
sample of the same queries.

**What this means for reporting.** The framework's three questions (§3.4) and the protocol above
identify blindness in advance, but they identify it for a stated retriever and threat model. A
robustness claim should say which of these regimes it was evaluated in, because a null result in
the first regime is informative and a null result in the others is not.

## 9. Conclusion

Fairness defenses for retrieval-augmented generation are chosen and validated by aggregate statistics of the retrieved set. We have shown that the standard statistics are adversarially invariant: an attacker who balances what they count, preserves what they reference, or relocates all groups together leaves the statistic at its clean value while controlling the evidence. The invariance has one cause, it is predictable from the form of the statistic rather than measured after the fact, and the defense failure that follows is a consequence of it rather than a separate phenomenon.

The two dimensions we separate make the mechanism visible. **R1** is group composition; **R2** is within-group stance. Pairwise poisoning is balanced in R1 by construction, because the injected passages are matched pairs drawn from the legitimate template inventory, so every composition statistic reads clean while the stance of the evidence is skewed. The natural repair — move to stance and keep the same arithmetic, measuring the gap between groups — fails for the same structural reason: an absolute difference is dominated by the corpus's pre-existing asymmetry and is blind to an attack that relocates both groups. The diagnostic is the per-group shift, and it is large and consistent where the aggregate is not: the suppressed group's stance moves by −0.13 to −0.18 and the favoured group's by +0.13 across four generators spanning three model families at $p \le 0.0035$, while the absolute cross-group gap moves by less than 0.002.

The consequence for the defense class is a ceiling rather than a null. The unconstrained baseline already admits adversarial passages on every query where it can, so no reduction is available even in principle; the per-query difference is identically zero and the equivalence bound is exactly ±0.0000. The constraint does change which passages are selected — it moves the R2 stance gap substantially — and that is precisely the point: selection changes, and not one adversarial passage is displaced. Extending the constraint to a second dimension improves the statistic it measures without changing adversarial inclusion. The problem is one of detection, not of optimisation, and detection requires evidence about individual passages rather than about the set they belong to.

Under a defense-aware attacker the picture sharpens rather than softens. Across six retrieval back-ends the static advantage of the strongest defense is *largest* on the pretrained encoders the compared literature uses — four of the six begin at exactly 0.000 adversarial inclusion — and no defense retains measurable benefit beyond one perturbation step on any of them, while the injected passages stay over 94% semantically intact. A defense selected on its static advantage is therefore defeated comprehensively, and the static numbers that would select it are most optimistic exactly where that literature looks.

Two things follow, and they are what this paper contributes. The first is a **test**: three questions that predict, before any attack is built, whether a candidate statistic is invariant to an adversary who balances the quantity it counts, anchors it to a reference the attack preserves, or moves all groups together. The second is a **standard**: the reporting requirements a robustness or fairness claim must meet to be interpretable, set out in §8 and §5.8.1 — per-group shifts rather than cross-group differences, injection as a rate rather than a count, the encoder reported as a factor, equivalence bounds for null claims, the threat model stated, adversarial inclusion reported as a function of attacker strength, and a penalty treated as the attacker's constraint when it is computable from public information. Applied together these change what a result has to contain; they do not require a new defense, and every one of them is cheap.

The open problem is the one the framework itself exposes. A per-group report is more sensitive than an aggregate, and a more sensitive instrument still has to be shown to measure the right quantity. The individual-level signal we report in §7 is a candidate in that direction, and the test that would settle it is stated with it: it must survive on naturally written text. Establishing which cues about individual passages do survive — and why — is the measurement problem this work leaves open.

## Data and Code Availability

The implementation, configuration files, and the scripts that regenerate every number in §5 are released at **[anonymized repository]**. The controlled corpus is generated deterministically from a fixed seed and requires no dataset download; the BBQ corpus is reconstructed from the official benchmark files by a released loader that derives stance labels from BBQ's own annotations. §5.7 additionally requires a DeepSeek API key, supplied through the `DEEPSEEK_API_KEY` environment variable and never stored in the repository.

The repository is withheld here for anonymous review and will be named in the camera-ready version.

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
python analysis/diagnose_poison_scores.py # the mechanism behind Table C1

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
from `[anonymized repository]`.)

Outputs: `results/<run_tag>/{per_query,aggregate,by_stratum,adaptive}.csv` and `summary.txt`.

The full retrieval-layer study runs on CPU: the controlled suite completes in
25 s and the BBQ replication in 165 s on a desktop CPU, with no GPU required.
The backbone alignment of §5.5 and §5.6 adds roughly 75 minutes of CPU time
across eight encoder checkpoints, the slowest single run being GTE-large at
23 minutes; the largest model loaded is a 335M-parameter encoder, which needs
under 2 GB in fp32. No GPU is used anywhere in this paper.

---

## Appendix B. Paired tests and confidence intervals

Every number in §5 is an aggregate over queries. Because the paper's central claim is a null, we give the paired tests on the underlying per-query data here, including the equivalence bound for each null cell. Reproduce with the script `analysis/stats_paper.py`.

**Table B1.** Paired tests of R1-constraint inertness against no defense. Controlled corpus, `template_plus_projection`, $\rho = 0.5\%$, per-query adversarial-passage inclusion.

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



The point of Table B1 is the last column. For the R1-only and joint constraints the difference is zero per query, so the CI is [0, 0] and the equivalence bound is ±0.0000: the data exclude any effect on adversarial inclusion, not merely an effect above some threshold. The `repr_stance` rows are included as a contrast, since there the constraint genuinely changes the selection.

---

## Appendix C. Secondary tables

Tables moved out of the main body to keep it readable. Each is referenced from the section that discusses it.

**Table C1.** Adaptive attacker (defense-aware), `poison@k`. Controlled corpus, $\rho = 2\%$.

| Defense | λ=0 | λ=0.25 | λ=0.5 | λ=1 | λ=2 | λ=4 | static rank |
|---|---|---|---|---|---|---|---|
| off-manifold filtering | **0.250** | **0.562** | **0.812** | 0.938 | 1.000 | 1.000 | 1st |
| `repr_both` (R1+R2) | 0.625 | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | 2nd |
| multi-query consistency | 0.729 | 0.958 | 1.000 | 1.000 | 1.000 | 1.000 | 3rd |

**Table C2.** The first generation-layer measurement, with the forced-choice probe on a single generator. Superseded by Table 8; kept because the contrast between the two is the point. Controlled corpus, GTE-base retrieval, $\rho = 2\%$.

| Condition | fav. rate (g1) | fav. rate (g2) | **stance gap** | Δ vs clean |
|---|---|---|---|---|
| clean | 0.562 | 0.708 | **0.2708** | — |
| poisoned | 0.583 | 0.979 | **0.3958** | **+46%** |
| `r1only` (R1) | 0.604 | 1.000 | **0.3958** | +46% |
| `r2both` (R1+R2) | 0.583 | 1.000 | **0.4167** | +54% |

**Table C3.** Prop. 1 prediction vs. measurement. R1-only constraint (`repr_group`), strongest attack, largest injection rate per corpus; Δ = constrained minus no defense.

| Corpus / retriever | ε=1.0 | ε=0.5 | ε=0.25 | ε=0.1 | ε=0.0 |
|---|---|---|---|---|---|
| controlled / BM25 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| controlled / feature-hash dense | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| BBQ / BM25 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| BBQ / feature-hash dense | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| controlled / GTE-base | 0.000 | — | — | — | 0.000 |
| controlled / Contriever | 0.000 | — | — | — | 0.000 |

**Table C4.** Over-generalisation signal.

| Retriever | Set | n | mean | median | p90 |
|---|---|---|---|---|---|
| BM25 | poison | 16 | 0.1914 | 0.1875 | 0.2500 |
| BM25 | clean | 608 | 0.0032 | **0.0000** | **0.0000** |
| dense + projection (λ=1) | poison | 16 | 0.3086 | 0.2188 | 0.6250 |
| dense + projection (λ=1) | clean | 608 | 0.0001 | **0.0000** | **0.0000** |

**Table C5.** Bootstrap 95% CIs on the positive claims (per-question values, 10,000 resamples, no defense).

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

**Table C6.** Attack effect vs. injection rate $\rho$; no defense; `poison@k`.

*Controlled corpus (1,824 passages):*

| ρ | passages/stratum | BM25 `poison@k` | BM25 `stance_gap` | dense `poison@k` | dense `stance_gap` |
|---|---|---|---|---|---|
| clean | 0 | — | **0.0000** | — | **0.0000** |
| 0.1% | 2 | **0.6875** | 0.5417 | 0.4375 | 0.2833 |
| 0.25% | 5 | 0.750 | 0.6250 | 0.625 | 0.5000 |
| 1% | 18 | 0.750 | 0.7692 | 0.625 | 0.6111 |
| 2% | 36 | 0.750 | 0.7000 | 0.625 | 0.6667 |

**Table C7.** R2 constraint effect on BBQ (dense, template + projection, $\rho = 0.5\%$).

| Defense | ε | `stance_gap` (R2) | `poison@k` |
|---|---|---|---|
| vanilla | — | 0.9696 | 0.986 |
| `repr_group` (R1 only) | 0.0 | 0.9515 | 0.986 |
| **`repr_both` (R1+R2)** | **1.0** | **0.5250** | **0.972** |

**Table C8.** Where the GTE scale effect comes from. 36 injected passages, 48 queries, no defense, $\rho = 0.5\%$.

| Quantity | GTE-base | GTE-large |
|---|---|---|
| mean cosine gain of poison over clean | **+0.0115** | **+0.0200** |
| mean best-poison cosine | 0.8907 | 0.8975 |
| mean top-5 clean threshold | 0.8982 | 0.8988 |
| mean margin (best poison − threshold) | **−0.0075** | **−0.0013** |
| `poison@k` | 0.0625 | 0.5000 |

**Table C9.** R1-only constraint inertness across encoders and scales. `template_plus_projection`, $\rho = 0.5\%$; Δ = adversarial-passage inclusion minus no defense.

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

---

## Appendix D. Limitations in full

The body states each limitation in one line and what it costs; this appendix states them in full, with the measurements behind each. The numbering matches the body table.

1. **The measurement requires group- and stance-annotated passages, and natural retrieval corpora do not have them.** This is the binding constraint on this line of work, and it is worth stating plainly rather than as a data-collection to-do. R1 needs a group label per passage; R2 needs a stance label per passage. NQ and MS MARCO — the standard neutral retrieval corpora — carry neither, and stance toward a social group is not a property that can be inferred from a neutral passage, because a neutral passage does not express one. We therefore could not substitute a neutral corpus for BBQ, and neither can the defenses we evaluate: an R1-constraining defense needs the same group labels, and an R2-constraining defense needs labels that no existing neutral corpus provides. The framework's applicability is thus bounded by annotation, not by computation, and constructing a neutral, group- and stance-annotated retrieval benchmark is the field's outstanding infrastructure problem. Our two corpora bound the behaviour from the two sides available today: a template-controlled corpus with an exactly known reference, and a naturally written bias benchmark. We flag this as an open problem rather than a gap in the present study.
2. **Neither corpus is a neutral retrieval benchmark, and they disagree in two respects.** The text-only template attack is effective only on the controlled corpus (Finding 4), and the R2 constraint reduces adversarial inclusion only on BBQ. We report both conditions rather than selecting the favourable one. The mechanism behind the first disagreement is identified (lexical room depends on corpus repetitiveness), which we regard as a finding rather than a gap; the second is a smaller effect whose magnitude we expect to depend on the corpus's pre-existing stance imbalance.
3. **The absolute R2 metric does not transfer.** `stance_gap` is exactly 0 on the balanced controlled corpus and near its maximum (0.9326) on BBQ *before any attack*, where it is dominated by the benchmark's own stereotyped construction. On such a corpus only the change from the clean baseline is informative. A corpus-relative normalisation of $\Delta_{\text{R2}}$ would be preferable and we leave it open.
4. **Injection budget is a rate, not a count.** We report an injection rate throughout (§5.4), because a fixed passage count measures corpus size and produced a spurious conclusion in our own earlier experiment. Readers comparing against work that reports absolute counts should convert.
5. **Retrieval back-ends, and what the scale check changed.** Nine retrievers are evaluated: BM25, a self-contained feature-hashing dense retriever, SPLADE and SPLADE-large, and five dense semantic encoders — GTE-base, GTE-large, Contriever, E5-base-v2 and E5-large-v2 (§5.5, §5.6). An earlier draft of this paper listed the large checkpoints as "to be added" and *predicted* that they would disagree with the base models. We have since measured it and report the correction: the prediction was right in direction and far too weak in magnitude, since **GTE-base → GTE-large moves from 0.0625 to 0.5000 — an eight-fold increase in susceptibility within a single encoder family and training recipe.** That has three consequences for how this study should be read. First, feature-hashing dense retrieval retains the lexical attack surface and should not be read as a stand-in for a semantic encoder. Second, text-attack effectiveness varies **nine-fold across the base dense encoders alone** (Contriever 0.5625 versus GTE-base and E5-base-v2 at 0.0625) and the susceptible one is the encoder used by the fair-ranking work we compare against [8]. Third, and most importantly, **even holding the family and training recipe fixed, changing the checkpoint changes the answer qualitatively** — so a single-encoder robustness claim does not establish how robust a defense is in general. This is a limitation of our study and, we argue, of the standard evaluation protocol in this area. We have not swept Contriever at large scale, nor multilingual or instruction-tuned embedders, and we expect the spread to widen rather than narrow in those directions. Our scale pairs are parameter-matched (110M → 335M for GTE and E5; 66M → 110M for SPLADE), so the SPLADE pair tests a smaller size delta than the other two and a "large SPLADE is no more robust" conclusion carries correspondingly less weight.
6. **The generation-stage evaluation is multi-generator and multi-probe, and the probes disagree in a way that is itself a result.** §5.7 reports four generators spanning three model families (API-served Qwen and DeepSeek, plus open-weight Mistral-7B run locally in 4-bit on an RTX 5060), two corpora, and two probes: free-form answers scored by entailment, and a forced-choice probe scored by the choice it forces. Three limits remain. (i) *Retrieval conditions are measured on one backbone* (GTE-base), held fixed across the generation-stage comparison, so the encoder-dependence of §5.5 is not varied here. (ii) *The two probes support different conclusions, and the freer one is the weaker.* Free-form answers commit to a position in only 15.6% of cases on the controlled corpus and 1.0% on BBQ, so that probe is near-blind on natural text; the forced-choice probe detects the effect on both. We report both rather than the favourable one, because a probe that manufactures commitment can also manufacture an effect, and §5.7.1 records the checks we ran to establish that the forced choice tracks statement content rather than option position (100% versus 35% agreement with the placement of the favourable statement). (iii) *The effect is generator-dependent.* One of three generators carries most of the signal on both corpora, a second shows a single group on BBQ, and the third shows none reaching significance there. A result of this shape is not summarisable as one number, and we no longer report one. Whether a larger generator would show more or less is an open question: we ran one open-weight model and three API models, and the scale of the API models is not controlled.

   *Query diversity.* The controlled corpus's 48 retrieval slots correspond to only **16 distinct question texts** (each repeated 3×, once per paraphrase variant). Any statistic aggregated over the 48 is therefore aggregated over 16 questions, and the effective sample size is a third of what the table suggests. The natural-corpus evaluation does not have this problem (BBQ supplies 144 distinct, naturally written questions), which is an additional reason to prefer it for output-level measurement rather than treating it as a replication check.

   *The generator does not follow an inverted context on this corpus.* We ran a negative control that flips the stance of every retrieved passage while holding the question fixed. On the controlled corpus the answer was **unchanged in 6 of 6 cases under inversion**, but **changed in 6 of 6 cases when the context was replaced by unrelated passages** or removed entirely. The generator is therefore reading the context at the level of *topic* — it knows a question about an engineering evaluation calls for naming an engineer — but not at the level of *stance*, and the answers are determined by the question's framing rather than by the evidence on trial. This is a property of a template corpus whose questions presuppose their own answer, and it means a null propagation result on that corpus would have been uninformative. The forced-choice probe reported in §5.7 avoids the problem by construction, which is why it is the primary measurement; we now report the control because the free-form probe alone cannot distinguish "no propagation" from "generator ignores stance".

   *A metric we reported as failed is now fixed, and the fix is not cosmetic.* The per-passage attribution probe asked the generator itself whether its answer relied on a given passage; the judge answered YES almost always and the resulting EAE-D was a constant 1.000 in every condition. The cause is direction: an NLI model must be asked whether the **passage entails the answer**, not the reverse. Calibrated on this corpus, a passage the answer used scores 0.996 in the correct direction and 0.008 in the reversed one, and an unused passage scores 0.000 in both — so the reversed form returns noise rather than an obviously wrong value. §5.7's EAE-D figures should be read as produced by the probe we have now replaced.

   A multi-generator evaluation with entailment-based attribution is in progress and is not reported here; we do not otherwise report attributed exposure [8] or generator bias [4, 7].
7. **Binary groups.** Following [6, 7, 8], we use two groups per stratum. Extension to $|\mathcal{G}| > 2$ is mechanical for R1 and R2 but is not evaluated here. We note that the race/ethnicity category of BBQ is markedly imbalanced in our corpus build (960 passages about the protected group versus 88 about the non-protected group), which is itself a property of the benchmark worth flagging for anyone reusing it.

---

---

## Appendix E. The record of changes to our own measurements

The body reports the measurements as they stand. This appendix records where earlier
versions of this work reported something different, so that a reader who has seen an
earlier draft can see exactly what changed and why. Every number quoted here is the
superseded value, and the value that replaced it is the one used in the body.

1. **The static advantage of off-manifold filtering.** An earlier draft reported
   0.125 / 0.438 / 0.750 across the perturbation sweep and described the static advantage
   as a factor of six over no defense. Those values came from a run written to a scratch
   directory excluded from version control, rather than from the configuration that
   produces every other number in this paper. Re-running the committed configuration
   reproduces Table C1 with 18 of 18 adaptive cells bit-identical, and gives a static
   advantage of a factor of three. The qualitative conclusion is unchanged; the factor is.

2. **The shape of the adaptive collapse.** We first reported that the collapse is steeper
   on a pretrained encoder than on our own hashed retriever, and framed the result as
   "real encoders collapse faster". With six back-ends the pattern does not support that
   framing: GTE-base and E5-base-v2 fail in a single perturbation step, while Contriever
   and both SPLADE sizes climb gradually and resemble the hashed retriever. The framing
   was too coarse and was replaced by the three claims in §5.8, which hold on all six.

3. **The R2 reference convention.** Our first implementation scored stance as
   `P(entail | statement, answer)`. Calibrated against the correct convention on the same
   data, the reversed form returns ±0.002 for a favourable answer, an unfavourable answer,
   an unrelated answer and a vacuous one alike; the correct direction,
   `P(entail | answer, statement)`, returns +0.997 and −0.997 for the two extremes. The
   convention is not interchangeable, and the failure mode is indistinguishable from a
   genuine null result.

4. **The attribution direction.** The expected-attributed-exposure statistic was first
   implemented by asking the generator whether its answer relied on each retrieved
   passage. It returned 1.000 in every condition. The cause is direction: attribution must
   ask whether the **passage entails the answer**. With the direction corrected the
   statistic discriminates properly, 0.798–0.828 clean rising to 0.831–0.968 under
   injection.

5. **The injection parameter.** An earlier version injected a fixed six passages per
   stratum and concluded that the text-only attack does not transfer to natural data. Six
   passages is roughly 10% of a small candidate pool but 0.03% of an 18k-passage corpus, so
   a fixed count measures corpus size rather than attack strength. The sweep in §5.4 is
   reported as an injection rate.

6. **An inference from Corollary 1.** An earlier version concluded that the number of
   passages required is bounded by a small constant independent of corpus size. That
   conflates two requirements which behave differently, and the corrected statement is in
   §6.

7. **A cross-reference defect found by the reference checker.** Three `\bibitem` keys had
   been assigned the same label during an automated edit, which pdflatex resolves silently
   to the last definition; every citation affected was pointing at the wrong entry. Found
   by comparing the citation set against the markdown source, and corrected.

---

## References

**Declaration of generative AI and AI-assisted technologies in the manuscript preparation process.** During the preparation of this work the author used DeepSeek Harness (deepseek-flash) in order to search and verify bibliographic metadata, draft and revise prose, and produce one conceptual schematic figure of the framework from a description supplied by the author. After using this tool, the author reviewed and edited all output, verified every citation against the primary source, and takes full responsibility for the content of the publication.

**On the tooling used for the research itself.** The generator outputs analysed in §5.7 were produced by the DeepSeek and Qwen API models and by a local Mistral-7B checkpoint, exactly as stated in §5.7 and Appendix D.6. No other AI tool contributed to the research procedure.


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

[14] S. Dai, X. Chen, S. Xu, L. Pang, Z. Dong, J. Xu. Bias and unfairness in information retrieval systems: New challenges in the LLM era. *KDD*, pp. 6437–6447, 2024.

[15] M. Hu, H. Wu, Z. Guan, et al. No free lunch: Retrieval-augmented generation undermines fairness in LLMs, even for vigilant users. *arXiv:2410.07589*, 2024.

[16] S. K. Mohanty, R. Patel, K. Yuvaraj, et al. TriShieldRAG: 3 rings, one blind spot in layered defenses for retrieval-augmented generation. *arXiv:2607.23838*, 2026.

[17] A. Z. Jacobs, H. Wallach. Measurement and fairness. *ACM Conference on Fairness, Accountability, and Transparency (FAccT)*, pp. 375–385, 2021.

[18] M. D. Ekstrand, A. Das, R. Burke, F. Diaz. Fairness in information access systems. *Foundations and Trends in Information Retrieval*, vol. 16, no. 1–2, pp. 1–177, 2022.

[19] M. D. Ekstrand, G. McDonald, A. Raj, I. Johnson. Overview of the TREC 2022 fair ranking track. *TREC*, 2022.

[20] B. Efron, R. J. Tibshirani. *An Introduction to the Bootstrap*. Chapman & Hall/CRC, 1993.

[21] A. Parrish, A. Chen, N. Nangia, et al. BBQ: A hand-built bias benchmark for question answering. *Findings of ACL*, pp. 2086–2105, 2022.

[22] M. Nadeem, A. Bethke, S. Reddy. StereoSet: Measuring stereotypical bias in pretrained language models. *ACL*, 2021.

[23] B. Carlini, A. Athalye, N. Papernot, et al. On evaluating adversarial robustness. *arXiv:1902.06705*, 2019.

[24] F. Tramer, N. Carlini, W. Brendel, A. Madry. On adaptive attacks to adversarial example defenses. *NeurIPS*, 2020.

[25] M. Oliveira, B. J. Vergilio, R. Sobrinho, J. de Andrade Silva, A. Fontao. Metamorphic fairness testing of retrieval-augmented generation: Diagnosing retriever bias and evaluating graph-based mitigation. *Journal of Software Engineering Research and Development*, 14(1):179-208, 2026.
