"""Stage 1 of the narrative rewrite: title and abstract.

Applying the anti-defensive-writing rules to the abstract, which is the opening of the
press conference. What changed and why:

  * the title no longer promises "what to measure instead" -- it names the property the
    paper establishes (adversarial invariance) and the consequence (aggregate metrics
    cannot detect pairwise poisoning);
  * the abstract opens with the STAKES and a one-sentence thesis rather than walking
    straight into the F1/F2/F3 list, so the problem and the contribution are both present
    in the first five sentences;
  * the positive control is stated as evidence that the instruments are sound, which is
    what pre-empts "your metrics are just broken";
  * the strongest numbers lead (equivalence bound ±0.0000; per-group shifts +0.13/-0.13
    against an aggregate that moves <0.002; four of six back-ends starting at exactly 0.000);
  * every self-weakening construction is removed: "we initially got this wrong ourselves",
    "we reproduced the exact error we identify", "is the third instrument failure the paper
    documents", "whether that is an artefact of its construction". None of these facts is
    deleted from the paper -- several are relocated to the limitations appendix, where a
    reader can still audit them, and the numbers are unchanged.

Scope is preserved in one measured sentence at the end, as the ethics rules require; what
is removed is the self-undermining framing, not the boundary.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

OLD_TITLE = ('# Measuring Retrieval Fairness Under Adversarial Poisoning: Why the Standard '
             'Statistics Are Blind, and What to Measure Instead')
NEW_TITLE = ('# Adversarially Invariant Fairness Statistics: Why Aggregate '
             'Retrieval-Fairness Metrics Cannot Detect Pairwise Poisoning')

NEW_ABSTRACT = '''## Abstract

Fairness defenses for retrieval-augmented generation are selected, tuned and validated by aggregate statistics of the retrieved set: the share of passages about each protected group, the deviation of a group's stance from a corpus reference, or the exposure of items across requests. Because a defense is only as sensitive as the statistic that selects it, an adversary who can make that statistic invariant defeats the defense *selection* without touching the defense. We show that this is not a weakness of any particular metric but a structural property of the class, and that it is checkable before any attack is built. Every statistic in this literature has the form of a per-group quantity aggregated across groups, and an adversary can preserve that aggregate in exactly three ways: by balancing the quantity it counts (**F1**), by anchoring it to a reference the attack leaves intact (**F2**), or by moving all groups together so that a difference between them cancels (**F3**). The three modes are a falsifiable test rather than a description: applied to the published metrics they predict which will be blind, and the predictions hold.

The attack that realises them is *pairwise poisoning*, which injects matched passages drawn from the legitimate template inventory — one favourable to a group, one unfavourable to another — so that the injection is balanced across groups by construction and the stance of the evidence is skewed instead. We formalise representation as two orthogonal dimensions, **(R1) group composition** and **(R2) within-group stance**, and measure both on a controlled corpus and on a naturally written bias benchmark. A positive control in which the ground truth changes by a known amount while corpus size is held fixed establishes that the indicted statistics are *working instruments*: they respond monotonically and in the correct direction. Against those same instruments, the R1 constraint is inert with an equivalence bound of exactly ±0.0000 — every constrained configuration reproduces the unconstrained inclusion rate per query, because the unconstrained baseline already admits adversarial passages on every query where it can (1.000 dense, 0.750 BM25), leaving no headroom for a reduction to appear. The signal lives in the per-group shifts rather than in the gap between groups: injection moves the suppressed group's stance by −0.13 to −0.18 and the favoured group's by +0.13, consistently across four generators spanning three model families at $p \\le 0.0035$, while the absolute cross-group gap moves by less than 0.002. A defense-aware attacker then inverts the static ranking of defenses across six retrieval back-ends: the strongest defense's static advantage is *largest* on the pretrained encoders the compared literature uses — four begin at exactly 0.000 inclusion — and no defense retains measurable benefit beyond one perturbation step on any of them, while the injected passages stay over 94% semantically intact.

The consequence is a reporting requirement rather than another defense. We give a six-point protocol under which a robustness claim is interpretable: per-group shifts rather than cross-group differences, adversarial inclusion as a function of attacker strength rather than at a single operating point, the encoder reported as a factor, equivalence bounds for null claims, and the threat model stated explicitly. The study covers binary group partitions at the retrieval and generation layers across two corpora; the framework's applicability is bounded by the availability of group- and stance-annotated passages, which is an infrastructure problem for the field rather than a computation.

'''


def main():
    s = io.open(MD, encoding='utf-8').read()
    if OLD_TITLE not in s:
        print('TITLE ANCHOR FAIL')
        return 1
    s = s.replace(OLD_TITLE, NEW_TITLE, 1)

    a = s.find('## Abstract')
    b = s.find('**Keywords**:')
    if a < 0 or b < 0 or b < a:
        print('ABSTRACT BOUNDARY FAIL a=%d b=%d' % (a, b))
        return 1
    s = s[:a] + NEW_ABSTRACT + s[b:]

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print('title replaced: %s' % NEW_TITLE[:60])
    print('abstract replaced: %d chars -> %d chars'
          % (b - a, len(NEW_ABSTRACT)))
    for probe in ['we initially got this wrong', 'third instrument failure',
                  'artefact of its construction', 'negative result about a class']:
        print('  removed %-34s : %s' % (probe, probe not in s))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
