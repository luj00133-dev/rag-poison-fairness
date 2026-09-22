# Formal Analysis of Distribution-Constrained Selection under Injection

**Purpose**: replace the informal Proposition 1 in the manuscript with a
derived result — a closed-form injection budget that suffices to violate an
R1 (or R2) constraint, and the corollary that no budget tight enough to block it
preserves utility.

Notation follows §3 of the manuscript.

---

## Setup

Let $\mathcal{C}$ be a corpus of passages. Each passage $d$ carries a group
$g(d) \in \mathcal{G} \cup \{\bot\}$ and a stance $s(d) \in \{+1,-1,0\}$, where
$+1$ is favourable toward $g(d)$. Let $\mathcal{A} \subseteq \mathcal{C}$ be the
passages the attacker controls, $n = |\mathcal{A}|$.

A **defense** is a map that, for a query $q$, selects $\mathcal{D}_q \subseteq
\mathcal{C}$ with $|\mathcal{D}_q| = k$. Write

$$
p_{\text{grp}}(g; \mathcal{D}) = \frac{|\{d \in \mathcal{D} : g(d)=g,\ s(d)\neq 0\}|}{|\{d \in \mathcal{D} : g(d)\neq\bot,\ s(d)\neq 0\}|},
\qquad
p_{\text{fav}}(g; \mathcal{D}) = \frac{|\{d \in \mathcal{D} : g(d)=g,\ s(d)=+1\}|}{|\{d \in \mathcal{D} : g(d)=g,\ s(d)\neq 0\}|}.
$$

**Definition (ε-feasible selection).** Fix references $p^\ast_{\text{grp}}$ and
$p^\ast_{\text{fav}}$. A selection $\mathcal{D}$ is *ε-feasible* if

$$
\bigl|p_{\text{grp}}(g;\mathcal{D}) - p^\ast_{\text{grp}}(g)\bigr| \le \varepsilon
\quad\text{and}\quad
\bigl|p_{\text{fav}}(g;\mathcal{D}) - p^\ast_{\text{fav}}(g)\bigr| \le \varepsilon
\qquad \forall g \in \mathcal{G}.
\tag{1}
$$

Let $\mathcal{R}_\varepsilon$ denote the set of ε-feasible selections. A
distribution-constrained defense accepts exactly $\mathcal{R}_\varepsilon$.

---

## Proposition 1 (admissibility of the injection)

**Statement.** If the attacker injects $n$ passages that are (i) group-relevant,
(ii) split between the groups in proportion $p^\ast_{\text{grp}}$, and (iii)
stance-balanced so that $p_{\text{fav}}(g) = p^\ast_{\text{fav}}(g)$ for every
$g$, then every selection containing only injected passages is ε-feasible for
every $\varepsilon \ge 0$.

**Proof.** Consider $\mathcal{D} = \mathcal{A}'$ for any $\mathcal{A}' \subseteq
\mathcal{A}$ with $|\mathcal{A}'| = k$. By (ii), the number of passages of each
group in $\mathcal{A}'$ is $p^\ast_{\text{grp}}(g)\,k$ up to rounding, so
$p_{\text{grp}}(g;\mathcal{A}') = p^\ast_{\text{grp}}(g)$ and the first
inequality of (1) holds with equality. By (iii), $p_{\text{fav}}(g;\mathcal{A}')
= p^\ast_{\text{fav}}(g)$, so the second holds with equality. Hence
$\mathcal{A}' \in \mathcal{R}_\varepsilon$ for every $\varepsilon \ge 0$. $\square$

**Consequence.** A defense whose acceptance test is membership in
$\mathcal{R}_\varepsilon$ admits a fully adversarial selection at *any*
tolerance, including $\varepsilon = 0$. Tightening the budget does not exclude
the injection; it constrains the attacker's *composition*, which the attacker
chooses freely. This is the mechanism behind the empirical Finding 2/6: the
budget has no operating point at which it bites.

---

## Proposition 2 (minimum injection for an ε-stance-shift)

Proposition 1 shows the attacker *can* be admissible. We now give the budget at
which it becomes *effective*: how many passages must be injected to move a
group's stance rate by more than the defense tolerates.

**Setup.** Fix a query $q$ and a group $g$. Let the clean selection contain
$m_g$ passages about $g$, with $f_g$ favourable, so $p^\ast_{\text{fav}}(g) =
f_g/m_g$. The attacker replaces $j \le \min(n, m_g)$ of these with favourable
passages about $g$ (the flooding direction) or sets them unfavourable (the
suppression direction). Assume the injected passages out-rank the ones they
displace so that replacement, not addition, is the operative effect.

**Statement.** The minimum number of *displaced* passages needed to violate the
stance constraint for group $g$ is

$$
\boxed{\;j^\ast_g(\varepsilon) \;=\; \bigl\lceil \varepsilon\, m_g \bigr\rceil + 1\;}
\tag{2}
$$

and the corresponding minimum injection budget is
$n^\ast(\varepsilon) = \sum_{g \in \mathcal{G}} j^\ast_g(\varepsilon)$.

**Proof.** Suppose the attacker floods $g$ with favourable passages, replacing
$j$ unfavourable ones. The new favourable count is $\min(f_g + j,\ m_g)$, and
the rate becomes

$$
p_{\text{fav}}(g) = \frac{f_g + j}{m_g}\quad\text{for } j \le m_g - f_g .
$$

The constraint $p_{\text{fav}}(g) - p^\ast_{\text{fav}}(g) > \varepsilon$ is

$$
\frac{f_g + j}{m_g} - \frac{f_g}{m_g} > \varepsilon
\;\iff\; \frac{j}{m_g} > \varepsilon
\;\iff\; j > \varepsilon\, m_g .
$$

The smallest integer satisfying this is $\lceil \varepsilon m_g\rceil + 1$
(the $+1$ handles the strictness when $\varepsilon m_g$ is an integer). The
suppression direction is symmetric: replacing favourable with unfavourable gives
$p_{\text{fav}}(g) = (f_g - j)/m_g$, and $(f_g - j)/m_g < p^\ast_{\text{fav}}(g)
- \varepsilon$ yields the same bound. Taking the maximum over groups gives the
budget. $\square$

**Reading.** $j^\ast_g$ is *linear* in both the tolerance and the group's clean
representation: raising $\varepsilon$ from 0 to 1 costs the attacker at most
$m_g$ displaced passages, and $m_g \le k$, so

$$
j^\ast_g(\varepsilon) \;\le\; k \quad\text{for all } \varepsilon \le 1 .
$$

**This bound is on the *constraint*, not on retrievability — a distinction we
initially got wrong.** An earlier draft concluded that "the number of passages
required is bounded by a small constant independent of corpus size". That
conflates two requirements that behave very differently:

| Requirement | Governed by | Depends on corpus size? |
|---|---|---|
| **Violate the constraint** (Prop. 2) | $\varepsilon$ and $m_g \le k$ | **No** |
| **Be retrieved at all** | whether injected passages out-rank the clean competition | **Yes** |

The second is not modelled above; it is the *premise* of the derivation ("assume
the injected passages out-rank the ones they displace"). Our own measurements
show that premise failing in a corpus-dependent way: on the controlled corpus
**2 injected passages per stratum (0.1% of 1,824)** already reach `poison@k` =
0.688, whereas on BBQ **356 passages per stratum (2% of 17,792)** reach
**0.000**. The bound $j^\ast \le k = 5$ is not even sufficient on the controlled
corpus, where 5 passages reach only 0.750 — because replacement requires the
injected passages to out-rank a large field of equally relevant clean passages.

The defensible statement is therefore conditional, and we state it as such:
**once the attacker's passages are retrieved, violating an ε-constraint costs at
most $k$ replacements; whether they are retrieved is a separate question governed
by the attack's relevance advantage, which is corpus- and encoder-dependent
(Findings 4 and 7).** Conflating the two would predict that injection rate is
irrelevant — a prediction our rate sweep falsifies.

**Corollary 1 (the constraint is cheap to violate, once retrieved).** For any
tolerance in the admissible range, an attacker who can place at most $k$
passages per group into the selection violates the stance constraint for that
group. Since $k$ is the retrieval depth — typically 3–5 — the *constraint* cost
is a small constant, while the *retrieval* cost is not.

**Corollary 2 (suppression is cheaper than flooding).** If the clean selection
is one-sided for group $g$ — say $f_g = 0$, which we observe empirically on
group-neutral queries (§3.2: every clean query returns a top-$k$ that is entirely
favourable or entirely unfavourable) — then $p^\ast_{\text{fav}}(g) = 0$ and the
attacker's flood direction is free in terms of constraint violation, while the
suppression direction must overcome the full rate. Conversely, if $f_g = m_g$ the
suppression direction is free. **The cheaper direction is always the one that
pushes an already-extreme rate further toward its extreme**, consistent with the
empirical Finding 9 (the attack drives one group's favourable rate to ceiling
rather than shifting both).

---

## Proposition 3 (the utility constraint on blocking)

Proposition 2 gives the attacker's budget. We now ask whether the defense can
set $\varepsilon$ low enough to block it while still being useful. Let the
defense additionally require $\mathcal{D} \in \mathcal{P}$, where $\mathcal{P}$
is the set of selections satisfying some utility floor (e.g. that every selected
passage has relevance above a threshold, or that the selection is within a
relevance loss $\delta$ of the unconstrained top-$k$).

**Assumption (relevance overlap).** Assume the attacker can make injected
passages $\delta$-competitive, i.e. for each injected $a$ there is an admissible
$\mathcal{D} \in \mathcal{P}$ containing $a$. This is the standard assumption in
corpus-poisoning work: passages are optimised to rank highly, and the empirical
results confirm it (projection attack: `poison@k` = 1.000 on our retrievers and
0.90–1.00 on real encoders).

**Statement.** Under the relevance-overlap assumption, for every $\varepsilon$
there exists an injection of size $\le k+1$ per group that is both
$\varepsilon$-feasible (Prop. 1) and $\mathcal{P}$-admissible.

**Proof.** By Prop. 1 the attacker can construct an injection that is
ε-feasible for all $\varepsilon$. By the relevance-overlap assumption each
injected passage admits a selection in $\mathcal{P}$ containing it. Combining,
there is a selection satisfying both. $\square$

**Consequence — the trilemma.** A distribution-constrained defense faces three
requirements and can satisfy at most two:

| Requirement | Formal condition |
|---|---|
| **Soundness** — exclude adversarial passages | $\mathcal{R}_\varepsilon \cap \{\mathcal{D} : \mathcal{D} \cap \mathcal{A} \neq \emptyset\} = \emptyset$ |
| **Usefulness** — admit a good clean selection | $\mathcal{R}_\varepsilon \cap \mathcal{P} \neq \emptyset$ |
| **Tightness** — a non-trivial constraint | $\varepsilon < 1$ |

Prop. 1 shows Soundness fails for every $\varepsilon$ whenever the attacker can
construct an ε-feasible injection, which requires only that the attacker knows
$p^\ast$ and $\varepsilon$ — both public for an auditable defense. So the
defense must either accept adversarial passages, or restrict $\mathcal{R}_\varepsilon$
so severely that $\mathcal{R}_\varepsilon \cap \mathcal{P}$ is small or empty
(i.e. sacrifice Usefulness), or set $\varepsilon$ so large that the constraint
is vacuous (sacrifice Tightness).

**This is the formal content of the paper's central claim.** Empirically we
observe the first horn (Soundness fails; Findings 2, 6); the second is ruled out
by the utility measurements (`in_pool_rate` collapses when the budget is tight —
e.g. the R1-only defense at $\varepsilon=0$ drives `in_pool_rate` from 0.017 to
0.088 with no security gain); the third is the $\varepsilon = 1$ column, which
reduces to no defense.

---

## What this does *not* establish

We state the limits of the analysis, since overclaiming here would be the
easiest way to make the paper wrong.

1. **Prop. 1 assumes the attacker can choose composition freely.** It cannot, if
   the corpus supplies only certain passage types. In our controlled corpus the
   template inventory is rich enough; on a restricted corpus the feasibility set
   may shrink. The empirical Finding 7 (attack success varying nine-fold between
   two real encoders) is evidence that feasibility is encoder-dependent in ways
   this analysis does not model.

2. **Prop. 2 assumes replacement, i.e. that injected passages out-rank the ones
   they displace.** If they do not, they are simply not retrieved and the bound
   is vacuous. This is why injection *rate* still matters for the text attack on
   large corpora (Finding 4): the arithmetic bound is on validity, not on
   retrievability.

3. **Prop. 3 rests on the relevance-overlap assumption**, which we support
   empirically but do not prove. A defense that could certify that an injected
   passage is not δ-competitive — for instance by proving a relevance upper
   bound — would escape the trilemma. We know of no such defense in this
   literature, and constructing one is, in our view, the most promising
   direction this analysis opens.

4. **The analysis is per-group and per-query.** It does not model the
   dataset-level aggregation that R1 constraints are usually stated over; a
   defense enforcing the constraint in expectation across queries has more room
   than the pointwise version analysed here. Since our empirical defenses are
   pointwise, the mismatch does not affect our measurements, but it does mean
   the trilemma is stated for the pointwise case.
