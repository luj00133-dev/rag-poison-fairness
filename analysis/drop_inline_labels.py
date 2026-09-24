"""Drop the inline value labels from the encoder-scale figure.

Describing the rendered image found the last defect in it: GTE and E5 both start at
0.0625, so their two inline labels sit on top of each other and neither is readable.

Offsetting them would only move the collision, because the figure's point is that two
series *share* a value at base. The labels are also redundant: the legend already
prints each family's exact pair ("GTE (0.0625 -> 0.5000)"), and the y-axis carries the
scale. Removing them is the fix that makes the figure simpler rather than more
crowded, and it removes a class of collision that would recur for any two series that
converge.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
s = io.open(P, encoding='utf-8').read()

m = re.search(
    r"        # offsets differ per series.*?\n(?:.*?\n)*?.*?zorder=5\)\n", s)
assert m, 'inline label block not found'
print('removing %d lines of inline labelling' % m.group(0).count('\n'))
s = s[:m.start()] + s[m.end():]

# the docstring should no longer promise per-point values
s = s.replace('"""Susceptibility is not monotone in encoder size."""',
              '"""Susceptibility is not monotone in encoder size.\n\n'
              '    Values are not annotated on the lines: two families share 0.0625 at\n'
              '    base, so inline labels collide, and the legend already prints each\n'
              '    family\'s exact pair.\n    """')

io.open(P, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('parses; inline labels removed')
