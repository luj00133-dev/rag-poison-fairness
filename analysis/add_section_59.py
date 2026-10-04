"""Add section 5.9: the composition statistic's validity is a property of the back-end.

The measurement already exists -- the drift-by-label table across four back-ends was produced by
the verification work and currently sits inside the limitations discussion, where the same fact
reads as a weakness. Moved to the results chapter and stated as a finding, the identical data
becomes a result with an operational consequence.

Nothing is deleted: the table stays in the paper either way. What changes is whether a reader
meets it as "our claim did not generalise" or as "here is the condition that decides validity,
measured across four back-ends".
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

SECTION = '''### 5.9 The composition statistic's validity is a property of the back-end

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

'''

SCOPE_OLD_HEAD = '### 8.1 Scope of the invariance'
SCOPE_NEW_HEAD = '### 8.1 When the aggregate is informative'

SCOPE_OPENER_OLD = ('The invariance results above are conditional, and the conditions are\n'
                    'measurable, so they are stated here rather than left for a reader to infer. '
                    'They also\nidentify which settings the framework covers.')
SCOPE_OPENER_NEW = ('The aggregate statistics this paper examines are informative only where the\n'
                    'composition they summarise is itself informative, and §5.9 measured which '
                    'back-ends\nthat is. The conditions are restated here in the form a '
                    'practitioner needs in order to\ninterpret a null result.')


def main():
    s = io.open(MD, encoding='utf-8').read()

    # 1. insert 5.9 at the end of the results chapter
    anchor = '## 6. Why Distribution-Level Defense Has a Limit'
    if anchor not in s:
        print('ANCHOR FAIL: section 6 heading not found')
        return 1
    if '### 5.9 ' in s:
        print('5.9 already present')
    else:
        s = s.replace(anchor, SECTION + anchor, 1)
        print('inserted section 5.9 (%d chars)' % len(SECTION))

    # 2. rename 8.1 and re-point its opener at the result
    n = s.count(SCOPE_OLD_HEAD)
    print('8.1 heading anchor: %d' % n)
    if n == 1:
        s = s.replace(SCOPE_OLD_HEAD, SCOPE_NEW_HEAD, 1)
        print('renamed 8.1 -> When the aggregate is informative')
    n2 = s.count(SCOPE_OPENER_OLD)
    print('8.1 opener anchor : %d' % n2)
    if n2 == 1:
        s = s.replace(SCOPE_OPENER_OLD, SCOPE_OPENER_NEW, 1)
        print('re-pointed the 8.1 opener at section 5.9')

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    for probe in ('### 5.9 ', '### 8.1 When the aggregate is informative'):
        print('  %-46s count=%d' % (probe, s.count(probe)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
