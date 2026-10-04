Novelty check against 2024-2026 literature

WHY THIS WAS RUN

The paper's central claim is that aggregate fairness statistics are structurally invariant to a
balanced injection, and that this is predictable from the form of the statistic rather than
measured after the fact. My estimates of the paper's odds rested on an unverified assumption that
nobody had published that specific result. The earlier attempt to check was too broad and returned
noise, so this run used targeted queries and followed the two closest hits.

WHAT WAS FOUND

1. Bagwe et al., "Your RAG is Unfair: Exposing Fairness Vulnerabilities in Retrieval-Augmented
   Generation via Backdoor Attacks", EMNLP 2025 (doi:10.18653/v1/2025.emnlp-main.804).
   Fairness-specific backdoor attacks on RAG, manipulating semantic relations between target groups
   and social biases. This is the closest work in the attack direction, and the manuscript ALREADY
   CITES IT as reference [13]. Its contribution is that the attack exists and persists; it does not
   analyse whether the statistics used to select and validate fairness defenses can see such an
   attack, which is this paper's question.

2. Oliveira et al., "Metamorphic Fairness Testing of Retrieval-Augmented Generation", Journal of
   Software Engineering Research and Development 14(1), 2026 (doi:10.5753/jserd.2026.7713).
   Metamorphic testing of RAG fairness, component-level, three small language models. NOT cited by
   the manuscript. One of its reported implications is that a model-specific regression effect was
   "invisible to aggregate testing" -- the same aggregate-hides-it argument this paper makes, arrived
   at from software testing rather than from an adversarial construction.

3. Tran et al., "Retrieved But Not Reliable: A Survey on Attacks and Defenses in
   Retrieval-Augmented Generation", arXiv 2026 (doi:10.48550/arxiv.2608.24977). A pipeline-aware
   survey that lists fairness violations among RAG risks. Useful as a positioning citation.

NO PRIORITY LOSS FOUND

No work was found that states the paper's specific claim: that the invariance is a property of the
class of per-group-aggregated statistics, that an adversary can preserve the aggregate in exactly
three ways, and that the modes are checkable before any attack is built. The novelty of the central
claim therefore survives this check, and the two closest works are complementary rather than
overlapping: one shows fairness attacks on RAG exist, the other shows aggregate testing can hide a
fairness effect, and neither asks whether the aggregate is structurally incapable of seeing a
balanced injection.

WHAT WAS DONE ABOUT IT

Oliveira et al. is now cited in the related-work discussion of measurement practice, where it
supports the point that aggregate-level reporting can conceal a group-level effect -- an independent
arrival at part of this paper's motivation, from a different literature, which strengthens the
argument rather than competing with it. Tran et al. is cited as the survey positioning fairness
among RAG risks.

The differentiation from Bagwe et al. is now explicit: their contribution is the attack, this
paper's is the measurement question of whether the statistics that select and validate fairness
defenses can detect one.

RESIDUAL UNCERTAINTY

This is a targeted search over OpenAlex, arXiv and Crossref, not an exhaustive systematic review.
Absence of a found match is evidence, not proof. Two limitations worth stating: Semantic Scholar
was rate limited during the run, so its recommendation graph did not contribute; and venue-specific
searches (security venues, IR venues) were not run separately. A reviewer who knows a paper not
indexed in these sources could still produce a priority challenge.
