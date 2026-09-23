"""Repair one corrupted line and one stale reference in Appendix B.

Line 765 lost a pair of backticks and gained a stray backslash at some point
during the table-renumbering passes: the code span `repr_stance` became
`epr_stance\`. The rest of the manuscript is intact (checked: every fenced block
is balanced and no other line has an odd backtick count), so this is a single-site
repair rather than a general one.

The same line also still carries a "§Table 16" reference from before the
renumbering; Table 16 no longer exists, and the paired-tests table is now B1.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

OLD = ('The point of \u00a7Table 16 is the last column. For the R1-only and joint '
       'constraints the difference is zero per query, so the CI is [0, 0] and the '
       'equivalence bound is \u00b10.0000: the data exclude any effect on '
       'adversarial inclusion, not merely an effect above some threshold. The '
       'epr_stance\\ rows are included as a contrast, since there the constraint '
       'genuinely changes the selection.')

NEW = ('The point of Table B1 is the last column. For the R1-only and joint '
       'constraints the difference is zero per query, so the CI is [0, 0] and the '
       'equivalence bound is \u00b10.0000: the data exclude any effect on '
       'adversarial inclusion, not merely an effect above some threshold. The '
       '`repr_stance` rows are included as a contrast, since there the constraint '
       'genuinely changes the selection.')

assert s.count(OLD) == 1, s.count(OLD)
s = s.replace(OLD, NEW)
io.open(P, 'w', encoding='utf-8').write(s)

lines = s.split('\n')
print('backticks: %d (even: %s)' % (s.count('`'), s.count('`') % 2 == 0))
odd = [i + 1 for i, l in enumerate(lines)
       if l.count('`') % 2 == 1 and '```' not in l]
print('lines with an odd backtick count (excluding fences): %s'
      % (odd if odd else 'none'))
print('stray backslashes before a letter: %d'
      % len([m for m in __import__('re').finditer(r'\\[a-z_]', s)]))
