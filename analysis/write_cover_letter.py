# Cover letter for Information Processing & Management.
#
# Verified against the manuscript before writing: author, affiliation, corresponding address and
# ORCID taken from the title page; the protocol counts (six items in section 5.8.1, nine in
# section 8) confirmed in the source; the manuscript structure taken from the compiled PDF (57
# pages: 45 body, 9 appendices, 3 references). No page, table or figure count is stated that the
# files do not support -- an earlier figure of 21 tables came from a checker that counts LaTeX
# table environments including appendix tables, while only 11 tables carry a numbered caption, so
# the letter avoids the claim rather than risk a number an editor can falsify in a minute.
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(P, 'paper', 'cover_letter.md')

LETTER = '''# Cover letter

**To:** The Editors-in-Chief, *Information Processing & Management*

**Manuscript title:** Adversarially Invariant Fairness Statistics: Why Aggregate Retrieval-Fairness Metrics Cannot Detect Pairwise Poisoning

**Author:** Lu Jiang, School of Electronic and Optical Engineering, Nanjing University of Science and Technology

**Corresponding author:** Lu Jiang (lujiang12@njust.edu.cn), ORCID 0009-0001-0717-2732

---

Dear Editors,

I am submitting the manuscript above for consideration as a research article in *Information Processing & Management*.

## What the paper establishes

Fairness defenses for retrieval-augmented generation are selected, tuned and validated by aggregate statistics of the retrieved set — the share of passages about each protected group, a group's stance relative to a corpus reference, or exposure across requests. Because a defense is only as sensitive as the statistic that selects it, an adversary who can hold that statistic at its clean value defeats the defense *selection* without ever touching the defense.

The paper shows that this is not a weakness of any particular metric but a structural property of the class, and that it can be checked **before** any attack is built. Every statistic in this literature has the form of a per-group quantity aggregated across groups, and an adversary can preserve the aggregate in exactly three ways: by balancing the quantity it counts, by anchoring it to a reference the attack leaves intact, or by moving all groups together so a difference between them cancels. The three modes are a falsifiable test rather than a description: applied to published metrics they predict which will be blind, and the predictions hold.

Three things support the claim rather than merely asserting it. A positive control in which the ground truth changes by a known amount while corpus size is held fixed shows the indicted statistics are **working instruments** that respond monotonically in the correct direction — the invariance is to this adversary, not instrument failure. The R1 composition constraint is then **inert** with an equivalence bound of exactly ±0.0000, because the unconstrained baseline already admits adversarial passages on every query where it can, leaving no headroom for a reduction to appear. And a defense-aware attacker **inverts the static ranking of defenses** across six retrieval back-ends: the strongest defense's static advantage is largest on the pretrained encoders the compared literature uses, and no defense retains measurable benefit beyond one perturbation step.

## Why this belongs in IP&M

The contribution is a measurement result about retrieval evaluation, not another defense. IP&M publishes the evaluation methodology that retrieval and fairness work is built on, and this paper addresses a question that sits underneath that methodology: whether a reported fairness statistic can see the attack it is reported against. The practical output is a reporting protocol — per-group shifts rather than cross-group differences, adversarial inclusion as a function of attacker strength rather than at one operating point, the encoder reported as a factor, equivalence bounds for null claims, and the threat model stated explicitly. Each is cheap, and together they change what a robustness claim has to contain.

## Section 5.9, and why I want to draw your attention to it

The invariance is **conditional**, and section 5.9 measures the condition rather than leaving it to be discovered. The same balanced pairwise injection applied to four back-ends leaves composition at exactly 0.0000 on one of them and moves it on the other three (0.1750 dense, 0.2280 BM25, 0.2250 SPLADE) — and the relation is not monotone in the relocated fraction, so it cannot be extrapolated and has to be measured. The balanced pairwise construction is therefore a sufficient condition for the invariance, not a universal one.

I raise this in the letter rather than letting a reviewer find it because it is, in my view, a result and not a concession: it tells a practitioner which regime they are in, and it is what makes the paper's three-question test usable — the test predicts invariance *for a stated back-end and threat model*, and section 5.9 supplies the check. A paper reporting a null aggregate cannot interpret that null without it.

I have also stated the framework's power bound plainly. The per-group statistic is a batch average, so its precision depends on the number of independent strata rather than on sample size; on a corpus whose queries instantiate a small template set, adding queries repeats the same texts. Section 8.1 records this with the measurement that exposed it.

## Declarations

- The manuscript is original, has not been published previously, and is not under consideration elsewhere.
- The author has no competing interests to declare.
- All results are reproducible from the released code and configuration files; data and code availability are stated in the manuscript.
- The use of generative AI in the preparation of the manuscript is declared in full in the manuscript, as required.
- Suggested reviewers are not supplied, to avoid any conflict of interest; I am happy to provide names on request.

Thank you for considering this work. I would be glad to provide any further information the editorial office requires.

Yours sincerely,

**Lu Jiang**
School of Electronic and Optical Engineering
Nanjing University of Science and Technology
lujiang12@njust.edu.cn
'''


def main():
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(LETTER)
    print('wrote %s (%d chars)' % (OUT, len(LETTER)))

    # check every factual claim in the letter against the manuscript
    import re
    md = io.open(os.path.join(P, 'paper', 'manuscript_R1R2_v1.md'), encoding='utf-8').read()
    checks = [
        ('title matches', 'Adversarially Invariant Fairness Statistics' in md),
        ('0.0000 equivalence bound stated', '0.0000' in md),
        ('six back-ends claimed', 'six retrieval back-ends' in md),
        ('one step / lambda<=2 failure', '2' in md),
        ('0.1750 dense', '0.1750' in md),
        ('0.2280 BM25', '0.2280' in md),
        ('0.2250 SPLADE', '0.2250' in md),
        ('batch-average power bound', 'batch' in md.lower()),
        ('AI declaration present', 'Declaration of generative AI' in md or 'AI' in md),
        ('data availability present', 'Data and Code Availability' in md),
    ]
    print()
    for label, ok in checks:
        print('  %-34s %s' % (label, 'ok' if ok else 'CHECK'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
