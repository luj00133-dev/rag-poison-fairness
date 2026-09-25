"""Merge Paper B's genuinely new results into Paper A.

Scoped from measurement, not assumption. A's section 6 already carries four propositions,
including 6.5 on public randomisation, so B's section 4 is already absorbed. B's section 6
reporting protocol overlaps A's section 8 protocol, which is the stronger of the two and
stays. What is left, and what this script inserts:

  1. A NEW subsection 5.8, the six-back-end adaptive sweep: the static advantage is
     LARGEST on the pretrained encoders the compared literature uses (four start at exactly
     0.000), no defense survives beyond one or two perturbation steps on any of the six, and
     the attacker's cost stays at usage >= 0.943 -- which is what rules out the objection
     that the attack destroyed its own passages. A currently reports this for one dense
     retriever with a per-lambda grid in Appendix C.
  2. A paragraph on what retains benefit under adaptation: only the configuration whose
     constraint is over the retrieved SET rather than over individual passages, and only
     until lambda = 2.
  3. Two references A does not have and should: Carlini et al. (2019) and Tramer et al.
     (2020), the canonical adaptive-evaluation works, cited where the adaptive evaluation is
     introduced.

B's citation of "[Companion paper]" is dropped, since after the merge the companion paper is
this one.

The prose is transplanted with B's numeric citations converted to A's author-date keys; B's
"Table 2b" becomes A's Table 15 to avoid colliding with A's numbering. Inserted before A's
section 5.7, which keeps results together and leaves the generation-stage material last.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

ANCHOR = '### 5.7 Generation-stage propagation'

NEW_SECTION = r'''### 5.8 The collapse is not an artefact of one retriever

The sweep above uses our own feature-hashing dense retriever. Because the *shape* of the collapse — not merely its endpoint — could depend on the encoder, we repeated it on four further back-ends: **GTE-base** (the encoder used by the closest prior work on fairness-aware retrieval optimisation \citeyearpar{zhao2026}), **E5-base-v2** (used by the RAG fairness evaluations above), **Contriever**, and **SPLADE**, a learned *sparse* retriever. SPLADE is what makes the comparison diagnostic: it is a trained neural encoder, like GTE and E5, but its representation is sparse, like BM25's.

**Table 15.** `poison@k` under the adaptive attacker for off-manifold filtering, by back-end. Six back-ends; `usage` (the attacker's semantic fidelity) in the last column.

| Back-end | representation | λ=0 | λ=0.25 | λ=0.5 | λ=1 | λ=2 | λ=4 | `usage` at λ=1 |
|---|---|---|---|---|---|---|---|---|
| hash-dense (own) | dense, hashed | 0.250 | 0.562 | 0.812 | 0.938 | 1.000 | 1.000 | 0.945 |
| **GTE-base** | dense semantic | **0.000** | **1.000** | 1.000 | 1.000 | 1.000 | 1.000 | 0.978 |
| **E5-base-v2** | dense semantic | **0.000** | **1.000** | 1.000 | 1.000 | 1.000 | 1.000 | 0.971 |
| **Contriever** | dense semantic | **0.000** | 0.625 | 1.000 | 1.000 | 1.000 | 1.000 | 0.943 |
| **SPLADE** (distil) | sparse, learned | 0.188 | 0.500 | 0.812 | 1.000 | 1.000 | 1.000 | 0.954 |
| **SPLADE large** | sparse, learned | **0.000** | 0.500 | 0.750 | 0.938 | 1.000 | 1.000 | 0.952 |

The picture is not the one we expected when we added these back-ends, and it took all six to see why. Four of the five pretrained encoders (GTE-base, E5-base-v2, Contriever and SPLADE-large) begin at **exactly zero** adversarial inclusion against the static attacker and are effectively defeated after a single perturbation step. But "one step" means a *complete* failure immediately for GTE-base and E5-base-v2 (0.000 → 1.000), whereas Contriever (0.000 → 0.625 → 1.000) and both SPLADE sizes climb gradually and resemble our own hashed retriever (0.188 / 0.500 / 0.812 and 0.000 / 0.500 / 0.750 against 0.250 / 0.562 / 0.812). Scaling SPLADE up even *improves* the defense's static position (0.188 → 0.000 at $\lambda = 0$) while leaving the collapse rate unchanged. Neither "pretrained versus hashed" nor "dense versus sparse" describes the collapse on its own.

**Finding 12.** Three claims are stable across all six back-ends and are what this finding rests on. First, **the static advantage is largest on the pretrained encoders**: all five begin below our hashed retriever's 0.250, and four begin at 0.000 — the reverse of the concern that motivated the experiment, and awkward for the compared literature, because the static numbers one would use to select a defense are most optimistic precisely on the back-ends that literature uses. Second, **no defense retains any measurable benefit beyond $\lambda = 1$** on any of the six, and on four of them none survives $\lambda = 0.25$. Third, **the attacker pays essentially nothing**: `usage` is at least 0.943 at $\lambda = 1$ on every back-end, so the injected material is over 94% semantically intact at the point where the defenses have lost most or all of their advantage.

The honest statement about the *shape* of the collapse is therefore weaker than we first wrote: the abruptness varies by encoder in a way we cannot reduce to a single property, and an earlier framing of ours — that the collapse is steeper on a "real" encoder — was too coarse and is replaced here. The practical consequence is unchanged and, if anything, sharper. A defense selected on its static advantage is defeated comprehensively, and a robustness claim measured on one back-end inherits an unmeasured dependence on which back-end was chosen. This is the same lesson as §5.5, arrived at from the opposite direction: there, the encoder determined whether a *text* attack worked at all; here, it determines whether a defense collapses in one perturbation step or three. **In both cases the encoder is not a nuisance parameter.**

**Finding 13. What survives adaptation, and why.** Only one configuration retains measurable benefit, and only in part of the sweep: the R1+R2 constraint on BBQ holds `poison@k` at 0.049 / 0.111 / 0.319 for $\lambda \le 0.5$ while preserving the utility proxy (`in_pool_rate` 0.442 against 0.363 for no defense), and it beats multi-query consistency throughout (0.319 against 0.535 at $\lambda = 0.5$; 0.764 against 0.847 at $\lambda = 1$). We attribute this to the defense's *objective* rather than to any attack-specific matching. It is the only defense whose constraint is expressed over the composition of the retrieved set rather than over individual passage statistics, so it cannot be satisfied by choosing perturbations — only by changing which passages are mutually compatible. That is a weaker effect than the static evaluation suggested, and it disappears by $\lambda = 2$. The asymmetry is the useful part: **constraints on properties of an individual passage are optimisable-against because the attacker controls that passage; constraints on the set are not, but they are correspondingly weaker.**

#### 5.8.1 The evaluation protocol these results imply

Findings 12 and 13 are not sensitive to our particular attack. They follow from the attacker being informed, which is the standard against which robustness claims are judged in the adversarial literature \citep{carlini2019,tramer2020}. We therefore state the protocol as a requirement rather than a suggestion, and it is the second half of the measurement contribution this paper makes: §3.4 gave the conditions under which a *statistic* is blind, and this gives the conditions under which a *robustness claim* is interpretable.

1. **State the threat model, including whether the attacker knows the defense.** A claim of robustness without this qualifier is uninterpretable, and it is the qualifier that separates the two evaluations in §5.2 and §5.6.
2. **Report adversarial inclusion as a function of attacker strength, not at one operating point.** A single value cannot distinguish a defense that is robust from one evaluated below its failure threshold. In our sweep every defense fails by $\lambda = 2$; a sweep stopping at $\lambda = 0.25$ would have shown three apparently robust defenses.
3. **Sweep to the point of failure and report where it occurs.** The location of the failure is the result; the endpoint alone is not.
4. **Report a utility-preserving baseline**, since a defense trivially achieves low inclusion by returning fewer or worse passages; we report `in_pool_rate` alongside `poison@k` throughout.
5. **For a randomised defense, state the distribution and assume it is known**, and report the attacker's optimal response to its expectation rather than to a sample. By Proposition 4, randomisation bounds the variance of the attacker's utility and not its mean.
6. **For a penalty-based defense, report whether the penalty is computable from public information**, and if it is, treat it as a constraint in the attacker's optimisation rather than as an unknown. This is Corollary 2, and in our experiments it is decisive for the defense that looked strongest statically: publishing a scoring function, which auditability requires, is equivalent to handing the attacker a differentiable objective.

'''

NEW_REFS = [
    'B. Carlini, A. Athalye, N. Papernot, et al. On evaluating adversarial robustness. *arXiv:1902.06705*, 2019.',
    'F. Tramer, N. Carlini, W. Brendel, A. Madry. On adaptive attacks to adversarial example defenses. *NeurIPS*, 2020.',
]


def main():
    s = io.open(MD, encoding='utf-8').read()
    if ANCHOR not in s:
        print('ANCHOR FAIL')
        return 1
    # The markdown source uses NUMERIC citations internally, while the tex uses natbib
    # author-date. The transplanted prose therefore carries numeric refs for the markdown,
    # and the same prose is written for the tex by merge_B_into_A_tex.py with citations as
    # \citeyearpar / \citep. Mixing the two styles here would have put literal LaTeX in the
    # docx and text parentheses in the PDF.
    #
    # The numbers must be A's own: [5] is Zhao et al. (verified), and the two new adaptive
    # references are appended as [23] Carlini et al. and [24] Tramer et al. An earlier draft
    # of this script mapped them to B's numbers [9, 10], which in A are GraphRAG and
    # MM-PoisonRAG -- a silently wrong citation.
    body = NEW_SECTION
    body = body.replace('\\citeyearpar{zhao2026}', '[5]')
    body = body.replace('\\citep{carlini2019,tramer2020}', '[23, 24]')

    s = s.replace(ANCHOR, body + ANCHOR, 1)

    # B's references 9 and 10 become A's 23 and 24
    refs_at = s.rfind('\n[22] ')
    end = s.find('\n', refs_at + 1)
    tail = s[end + 1:]
    add = '\n'.join('\n[%d] %s' % (n, t) for n, t in
                    zip(range(23, 23 + len(NEW_REFS)), NEW_REFS))
    s = s[:end + 1] + add + '\n' + tail

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print('inserted section of %d chars' % len(NEW_SECTION))
    print('added %d references (23-24)' % len(NEW_REFS))
    print('tables in markdown now: %d' % len(re.findall(r'^\*\*Table ', s, re.M)))
    print('cross-references to [9, 10] in the new section: %d'
          % body.count('[9, 10]'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
