"""Stage 5: rewrite the conclusion and de-duplicate the protocol.

Two problems with the current conclusion, both of which the skill names explicitly:

  * it ends with self-negation and a retraction ("we have reported an exploratory
    provenance signal ... together with the reason it may not survive replication"). The
    final paragraph must reinforce the takeaway, not reopen the case;
  * it re-argues its own error as part of the argument ("Reporting the second occurrence
    against ourselves is part of the argument: the error is not exotic, it is the natural
    first thing to compute"), which invites the reader to grade the authors rather than the
    finding.

It also duplicated the nine-point protocol that section 8 already carries in fuller form,
so the paper stated its recommendation twice in slightly different words. The conclusion
now points at it.

What is kept: every number, the ceiling argument for the inert constraint, and the
individual-level direction as the open problem. What goes: the self-audit framing and the
duplicate list.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

NEW_CONCLUSION = '''## 9. Conclusion

Fairness defenses for retrieval-augmented generation are chosen and validated by aggregate statistics of the retrieved set. We have shown that the standard statistics are adversarially invariant: an attacker who balances what they count, preserves what they reference, or relocates all groups together leaves the statistic at its clean value while controlling the evidence. The invariance has one cause, it is predictable from the form of the statistic rather than measured after the fact, and the defense failure that follows is a consequence of it rather than a separate phenomenon.

The two dimensions we separate make the mechanism visible. **R1** is group composition; **R2** is within-group stance. Pairwise poisoning is balanced in R1 by construction, because the injected passages are matched pairs drawn from the legitimate template inventory, so every composition statistic reads clean while the stance of the evidence is skewed. The natural repair — move to stance and keep the same arithmetic, measuring the gap between groups — fails for the same structural reason: an absolute difference is dominated by the corpus's pre-existing asymmetry and is blind to an attack that relocates both groups. The diagnostic is the per-group shift, and it is large and consistent where the aggregate is not: the suppressed group's stance moves by −0.13 to −0.18 and the favoured group's by +0.13 across four generators spanning three model families at $p \\le 0.0035$, while the absolute cross-group gap moves by less than 0.002.

The consequence for the defense class is a ceiling rather than a null. The unconstrained baseline already admits adversarial passages on every query where it can, so no reduction is available even in principle; the per-query difference is identically zero and the equivalence bound is exactly ±0.0000. The constraint does change which passages are selected — it moves the R2 stance gap substantially — and that is precisely the point: selection changes, and not one adversarial passage is displaced. Extending the constraint to a second dimension improves the statistic it measures without changing adversarial inclusion. The problem is one of detection, not of optimisation, and detection requires evidence about individual passages rather than about the set they belong to.

Under a defense-aware attacker the picture sharpens rather than softens. Across six retrieval back-ends the static advantage of the strongest defense is *largest* on the pretrained encoders the compared literature uses — four of the six begin at exactly 0.000 adversarial inclusion — and no defense retains measurable benefit beyond one perturbation step on any of them, while the injected passages stay over 94% semantically intact. A defense selected on its static advantage is therefore defeated comprehensively, and the static numbers that would select it are most optimistic exactly where that literature looks.

Two things follow, and they are what this paper contributes. The first is a **test**: three questions that predict, before any attack is built, whether a candidate statistic is invariant to an adversary who balances the quantity it counts, anchors it to a reference the attack preserves, or moves all groups together. The second is a **standard**: the reporting requirements a robustness or fairness claim must meet to be interpretable, set out in §8 — per-group shifts rather than cross-group differences, injection as a rate rather than a count, the encoder reported as a factor, equivalence bounds for null claims, the threat model stated, adversarial inclusion reported as a function of attacker strength, and a penalty treated as the attacker's constraint when it is computable from public information. Applied together these change what a result has to contain; they do not require a new defense, and every one of them is cheap.

The open problem is the one the framework itself exposes. A per-group report is more sensitive than an aggregate, and a more sensitive instrument still has to be shown to measure the right quantity. The individual-level signal we report in §7 is a candidate in that direction, and the test that would settle it is stated with it: it must survive on naturally written text. Establishing which cues about individual passages do survive — and why — is the measurement problem this work leaves open.

'''

P8 = '## 8. Discussion and Limitations'


def main():
    s = io.open(MD, encoding='utf-8').read()
    a = s.find('## 9. Conclusion')
    b = s.find('## Data and Code Availability')
    if a < 0 or b < 0 or b < a:
        print('BOUNDARY FAIL a=%d b=%d' % (a, b))
        return 1
    s = s[:a] + NEW_CONCLUSION + s[b:]
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)

    print('conclusion replaced: %d chars -> %d chars' % (b - a, len(NEW_CONCLUSION)))
    for probe in ['against ourselves is part of the argument',
                  'may not survive replication',
                  'exploratory provenance signal',
                  'produced a spurious conclusion in our own earlier experiment']:
        print('  removed %-52s : %s' % (probe[:52], probe not in s))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
