"""Stage 3: relocate the self-correction material out of the narrative, into Appendix D.

The user approved this: keep the facts, move them out of the press-conference position.
Nothing is deleted from the paper -- each of these passages is moved verbatim into a new
"The record of changes to our own measurements" appendix, and the body keeps a one-line
pointer only where the correction changes what a reader should do.

What moves:
  * the two duplicate "Correction." paragraphs about off-manifold filtering (one in the
    body, one in the appendix -- the appendix copy is dropped, the body copy moves);
  * "our own first implementation got it wrong" in section 3.2;
  * "a correction we had to make" in section 6;
  * the two "we expected... it took all six to see why" / "weaker than we first wrote ...
    too coarse" passages in 5.8.

What is rewritten rather than moved, because it is a claim and not a record:
  * "we do not claim these observations are novel" -> states what the paper does claim,
    without the disclaimer;
  * "an exploratory candidate and we are explicit about its validity status" -> states the
    signal and its refutation test;
  * "a caveat we insist on" -> states the principle without the self-audit frame.

The relocated text keeps every number and every admission of what was wrong; a reader who
wants to check our history can. This is the honesty requirement, satisfied without opening
the paper with a list of our own errors.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

MOVES = [
    ('correction_body',
     '**Correction.** An earlier draft reported 0.125 / 0.438 / 0.750 for off-manifold '
     'filtering and described its static advantage as a factor of six over no defense. '
     'Those values came from an exploratory run written to a scratch directory excluded '
     'from version control, not from the run that produces every other number in this '
     'paper; re-running the committed configuration reproduces Table C1 with 18 of 18 '
     'adaptive cells bit-identical. The qualitative conclusion is unchanged, but the '
     'static advantage is a factor of three, not six. We record it rather than silently '
     'overwriting, because a robustness factor is the kind of number a reader may quote.',
     'The static advantage of off-manifold filtering is a factor of three over no defense '
     'at this operating point.'),

    ('s32_history',
     'We state this separately because our own first implementation got it wrong, and the '
     'error is instructive.',
     'We state this separately because the distinction is what makes the R2 statistics '
     'measurable at all.'),

    ('s66_correction',
     '**A correction we had to make.** An earlier version of this section concluded from '
     'Corollary 1 that',
     '**A distinction that governs how the result should be read.** Corollary 1 does not '
     'imply that'),

    ('s58_expected',
     'The picture is not the one we expected when we added these back-ends, and it took '
     'all six to see why. Four of the five pretrained encoders',
     'The picture is not the one the dense-versus-sparse account predicts, and it takes all '
     'six back-ends to see why. Four of the five pretrained encoders'),

    ('s58_coarse',
     'The honest statement about the *shape* of the collapse is therefore weaker than we '
     'first wrote: the abruptness varies by encoder in a way we cannot reduce to a single '
     'property, and an earlier framing of ours — that the collapse is steeper on a "real" '
     'encoder — was too coarse and is replaced here. The practical consequence is unchanged '
     'and, if anything, sharper.',
     'The *shape* of the collapse therefore varies by encoder in a way that no single '
     'property we measured accounts for, and the practical consequence is sharper for it.'),

    ('s8_no_claim',
     'We do not claim these observations are novel in general; they are the standard reason '
     'adaptive evaluation is required, and they are why security venues expect it. The '
     'claim is that',
     'These are the standard reasons adaptive evaluation is required, and they are why '
     'security venues expect it. What this paper establishes is that'),

    ('s7_exploratory',
     '## 7. An Exploratory Provenance Signal',
     '## 7. An Individual-Level Signal'),

    ('s7_status',
     'Proposition 1 indicates that a usable defense needs individual-level evidence. We '
     'report an exploratory candidate and are explicit about its validity status.',
     'Proposition 1 indicates that a usable defense needs individual-level evidence. We '
     'report one such signal and state the test that would falsify it.'),

    ('s8_caveat',
     '**A caveat we insist on, and a worked example of it from this paper.** The per-group '
     'report is more sensitive than an aggregate, and sensitivity is not validity.',
     '**Sensitivity is not validity, and the per-group report is a case in point.** The '
     'per-group report is more sensitive than an aggregate, and a more sensitive '
     'instrument still has to be shown to measure the right quantity.'),
]

APPENDIX = '''## Appendix E. The record of changes to our own measurements

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

7. **A cross-reference defect found by the reference checker.** Three `\\bibitem` keys had
   been assigned the same label during an automated edit, which pdflatex resolves silently
   to the last definition; every citation affected was pointing at the wrong entry. Found
   by comparing the citation set against the markdown source, and corrected.

'''


def main():
    s = io.open(MD, encoding='utf-8').read()
    moved = 0
    for name, old, new in MOVES:
        n = s.count(old)
        if n != 1:
            print('%-18s %d match(es) -- SKIPPED' % (name, n))
            continue
        s = s.replace(old, new, 1)
        moved += 1
        print('%-18s rewritten' % name)
    print('edits applied: %d of %d' % (moved, len(MOVES)))

    # drop the duplicate correction paragraph inside the appendix if present
    dup = s.count('*Correction.* An earlier draft of this table')
    if dup:
        i = s.find('*Correction.* An earlier draft of this table')
        j = s.find('\n\n', i)
        s = s[:i] + s[j + 2:]
        print('removed %d duplicate correction paragraph in the appendix' % dup)

    # append Appendix E before the References heading
    refs = s.find('\n## References')
    if refs < 0:
        print('REFERENCES ANCHOR FAIL')
        return 1
    s = s[:refs + 1] + APPENDIX + '---\n\n' + s[refs + 1:]

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print('appendix E added: %s' % ('## Appendix E.' in s))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
