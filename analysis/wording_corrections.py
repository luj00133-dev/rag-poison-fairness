"""Fix the 8.1 opener and apply the four wording corrections.

The wording corrections all fix the same underlying error: the paper has been conflating a
UNIVERSAL statement about the form of the statistics with a CONDITIONAL one about their
blindness. The form is universal -- every candidate metric is a per-group quantity aggregated
across groups -- but whether that aggregate reads clean depends on whether the injection
balances the terms it aggregates, which section 5.9 now measures per back-end. Statements that
assert the blindness universally are therefore stronger than the evidence and are corrected to
say which of the two claims is being made.

None of these changes weakens or removes a finding. They make each claim match its evidence,
which is what stops a reviewer from falsifying the paper's own headline sentence with the
paper's own table.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')


def main():
    s = io.open(MD, encoding='utf-8').read()
    lines = s.split('\n')

    # ---- locate the 8.1 opener by its first words rather than by exact wrapping
    for i, line in enumerate(lines):
        if line.startswith('The invariance results above are conditional'):
            j = i
            while j < len(lines) and lines[j].strip():
                j += 1
            new = [
                'The aggregate statistics this paper examines are informative only where the',
                'composition they summarise is itself informative, and §5.9 measured which',
                'back-ends that is. The conditions are restated here in the form a practitioner',
                'needs in order to interpret a null result.',
            ]
            lines[i:j] = new
            print('8.1 opener re-pointed at section 5.9 (replaced %d lines)' % (j - i))
            break
    else:
        print('8.1 opener NOT FOUND')

    s = '\n'.join(lines)

    # ---- wording corrections, matched on stable fragments
    edits = [
        # 1. the universal blindness claim: separate form (universal) from blindness (conditional)
        ('Every statistic that aggregates over group composition is blind to this. It reports '
         'the group distribution as clean, admits the injected passages, and returns success.',
         'Every candidate metric has that form; whether it reads clean depends on whether the '
         'injection balances the terms it aggregates. That is a property of the back-end rather '
         'than of the metric, and §5.9 measures it across four of them.'),

        # 2. contribution 1: "fail" is not a property of the metric
        ('1. **A framework for why adversarial fairness statistics fail.**',
         '1. **A framework for when adversarial fairness statistics are invariant.** The form is '
         'universal; the invariance is conditional, and checkable in advance.'),

        # 3. section 3.4 heading: the signal is not lost by the metric, it is preserved by the attack
        ('### 3.4 One form for every candidate metric, and three ways it loses the signal',
         '### 3.4 One form for every candidate metric, and three invariances an adversary can impose'),

        # 4. the introduction's "structurally insensitive" needs its condition
        ('We show that the standard statistics are structurally insensitive to the attack that '
         'motivates them',
         'We show that the standard statistics are structurally insensitive to the attack that '
         'motivates them, because that attack preserves the very composition those statistics '
         'summarise'),
    ]

    for old, new in edits:
        n = s.count(old)
        print('%-64s %d match(es)' % (old[:64].replace('\n', ' '), n))
        if n == 1:
            s = s.replace(old, new, 1)
        elif n == 0:
            print('    ^ NOT FOUND')

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)

    s2 = io.open(MD, encoding='utf-8').read()
    print()
    checks = [
        ('universal blindness claim removed',
         'Every statistic that aggregates over group composition is blind to this.' not in s2),
        ('"why ... fail" reframed', 'why adversarial fairness statistics fail' not in s2),
        ('3.4 heading reframed', 'three ways it loses the signal' not in s2),
        ('intro condition added', 'preserves the very composition' in s2),
        ('8.1 opener points at 5.9', '§5.9 measured which' in s2),
    ]
    for label, ok in checks:
        print('  %-38s %s' % (label, ok))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
