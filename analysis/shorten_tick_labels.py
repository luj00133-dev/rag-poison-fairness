"""Shorten the responsiveness tick labels at the source.

Two rounds of margin and rotation changes failed to stop the leftmost tick label from
being clipped, and the vision description of the second attempt was itself uncertain
("could be 'swap 3000 reversed' with the 'sw' cut off"). Rather than keep tuning
geometry against an uncertain reading, the label is shortened: a rotated label that
needs a paragraph of horizontal room is the wrong label.

    'baseline'           -> 'base'
    'swap 500'           -> '500'
    'swap 1500'          -> '1500'
    'swap 3000'          -> '3000'
    'swap 3000 reversed' -> '3000 rev.'

The meaning is restored where it belongs, in the caption, which now has to say that the
five bars are the five corpus variants and what each swaps. That is a better division of
labour anyway: tick labels name the category, captions explain it.

Edited here rather than in make_figures.py because the labels are data, and
figure_data.py is the file that owns them.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figure_data.py')
s = io.open(P, encoding='utf-8').read()

m = re.search(r"'variant': \[[^\]]*\],", s, re.S)
assert m, 'variant list not found'
print('before: %s' % ' '.join(m.group(0).split()))

new = ("'variant': ['base', '500', '1500', '3000', '3000 rev.'],")
s = s[:m.start()] + new + s[m.end():]
io.open(P, 'w', encoding='utf-8').write(s)

import ast
ast.parse(s)
print('after : %s' % new)
print('figure_data.py parses')
