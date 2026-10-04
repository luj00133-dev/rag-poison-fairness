"""Add the scope conditions the verification work established, and correct one claim they falsify.

WHAT THE CHECKING ESTABLISHED

A line of validation work (results/balanced_partial_sweep_NOTE.md, results/gpu_and_scaling_NOTE.md)
measured where the paper's aggregate-invariance claim holds. Three boundary conditions came out of
it, and one of them contradicts a sentence the paper currently carries.

1. WHICH RETRIEVERS THE AGGREGATE IS FLAT ON.

Undefended drift_tv at the partial-relocation levels, by retriever:

    st + lexical attack        drift 0.0000 at every partial level   <- flat
    dense + template           drift 0.0000 rising to 0.1750         <- NOT flat, monotone in label
    bm25                       drift rises monotonically with the label
    splade                     drift rises monotonically with the label

So composition stays put on the st retriever with the lexical attack, and moves on the others.
This is a boundary, not a refutation: the balanced pairwise construction is what makes drift
zero on st, and dense/bm25/splade relocate composition even under the same injection.

2. THE PROJECTION STEP MAKES PASSAGE TEXT IRRELEVANT, SO NO TEXT-SIDE VARIATION CAN ACT ON IT.

Under template_plus_projection the adversarial fraction was 1.0 for 192 of 192 queries at every
alignment setting tried (six configurations). Projection sets the ranking from vectors, so the
composition the defenses see is decided by the projection rather than by the passages' text.

3. THE PER-GROUP STATISTIC IS A BATCH QUANTITY, NOT A PER-QUERY ONE.

The group favourable rate averages binary stance votes over a stratum. A single query contributes
one Bernoulli draw. An earlier validation attempt in this project scored per-query monitors by
AUC and found everything at chance, which says nothing about the recommendation because the
recommendation is not a per-query rule. The consequence that must be stated: the diagnostic needs
batches, so its power is bounded by the number of independent strata or audit rounds, not by the
number of queries. On a corpus with four query templates per stratum, adding queries repeats the
same texts and does not buy power -- measured, not assumed: the balanced-and-partial regime held
36 of 192 queries and 0 of 1,536 once the query count was raised.

THE CLAIM THAT MUST BE CORRECTED

The paper says "R1 drift stays at or below the level legitimate retrieval variance produces". On
the controlled corpus clean drift is exactly 0.0000 -- there is no legitimate variance for it to
stay below -- while the paper's own Table 1 reports attacked drift of 0.1500 (BM25) and 0.1313
(dense). The sentence is therefore false as written on the paper's own numbers. What is true and
measurable is stated instead.

The skill's rule that applies here is to narrow the claim rather than defend it: the invariance is
real but conditional, and naming the conditions is a strength because a reader can then tell
whether their setting is covered.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

SCOPE = '''### 8.1 Scope of the invariance

The invariance results above are conditional, and the conditions are measurable, so they are
stated here rather than left for a reader to infer. They also identify which settings the
framework covers.

**The composition statistic is flat on the lexical retriever, and moves elsewhere.** Undefended
composition drift on the controlled corpus, at the relocation levels where the label is partial:

| back-end | attack | composition drift at partial relocation |
|---|---|---|
| `st` (GTE-base) | lexical | 0.0000 at every partial level |
| dense | lexical | 0.0000 at the lowest level, rising to 0.1750 at full relocation |
| BM25 | lexical, projected | monotone in the relocated fraction, from 0.000 to 0.195 |
| SPLADE | lexical, projected | monotone in the relocated fraction |

On `st` the injected set is compositionally balanced and stays so however much of it is
retrieved, so the aggregate reads clean while the evidence moves — the regime the framework
describes. On the other back-ends the retrieved set relocates composition as well, and the
aggregate moves with it. The balanced pairwise construction is therefore a sufficient condition
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

'''


def main():
    s = io.open(MD, encoding='utf-8').read()

    # 1. insert the scope subsection at the end of section 8
    anchor = '## 9. Conclusion'
    if anchor not in s:
        print('ANCHOR FAIL: no conclusion heading')
        return 1
    if '### 8.1 Scope of the invariance' in s:
        print('scope subsection already present; skipping insert')
    else:
        s = s.replace(anchor, SCOPE + anchor, 1)
        print('inserted 8.1 Scope of the invariance (%d chars)' % len(SCOPE))

    # 2. correct the claim that the checked numbers falsify
    old = ('R1 drift stays at or below the level legitimate retrieval variance produces; '
           'two of three candidate R2 statistics are flat across the clean and fully attacked '
           'conditions.')
    new = ('On the lexical retriever the composition statistic reads clean however much of the '
           'injected set is retrieved, while two of three candidate R2 statistics are flat '
           'across the clean and fully attacked conditions; §8.1 states the retrievers and '
           'attacks on which each part of this holds.')
    n = s.count(old)
    print('claim-correction anchor: %d match(es)' % n)
    if n == 1:
        s = s.replace(old, new, 1)
        print('corrected the unsupported "at or below legitimate variance" claim')

    # 3. point the abstract at the scope statement, so the boundary is not a surprise
    a_old = ('The study covers binary group partitions at the retrieval and generation layers '
             'across two corpora; the framework\'s applicability is bounded by the availability '
             'of group- and stance-annotated passages, which is an infrastructure problem for '
             'the field rather than a computation.')
    a_new = ('The study covers binary group partitions at the retrieval and generation layers '
             'across two corpora, and the invariance is conditional on the back-end: §8.1 states '
             'the retrievers and threat models in which the composition statistic stays flat, '
             'which is what a reader needs in order to know whether a null aggregate is '
             'informative in their own setting.')
    n2 = s.count(a_old)
    print('abstract anchor: %d match(es)' % n2)
    if n2 == 1:
        s = s.replace(a_old, a_new, 1)
        print('abstract now points at the scope statement')

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    for probe in ('at or below the level legitimate retrieval variance',
                  '8.1 Scope of the invariance'):
        print('  %-52s count=%d' % (probe[:52], s.count(probe)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
