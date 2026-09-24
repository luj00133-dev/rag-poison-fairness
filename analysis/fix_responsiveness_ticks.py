"""Give the leftmost rotated tick label room inside the canvas.

The responsiveness figure's longest tick label, "swap 3000 reversed", sits at x = 0.
Rotated and right-aligned, it extends to the left of the axes, and the vision check
reports its head being cut ("... 3000 reversed" visible). The fix is to widen the
x-limits so there is axes space to the left of the first bar for the label to occupy;
enlarging the left margin instead would shrink the plot without moving the label.

Applied to both panels, since they share the tick set.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
s = io.open(P, encoding='utf-8').read()
before = s

# replace the two identical tick-setting blocks with one that also widens x-limits
OLD = """    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=38, ha='right',
                       fontsize=6.2)"""
NEW = """    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=6.0)
    # "swap 3000 reversed" sits at x = 0 and, rotated and right-aligned, reaches
    # left of the axes. Widening the limits creates axes space for it; widening
    # the left margin would shrink the plot without moving the label.
    ax.set_xlim(-0.62, len(comp_s) - 0.38)"""
n = s.count(OLD)
s = s.replace(OLD, NEW)
print('replaced %d tick block(s)' % n)

if n == 0:
    # the two panels were edited separately at some point; patch each form
    for pat in (r"ax\.set_xticklabels\(labels, rotation=\d+, ha='right',\n"
                r"\s*fontsize=[\d.]+\)",
                r"ax\.set_xticklabels\(labels, rotation=\d+, ha='right'\)"):
        s2 = re.sub(pat,
                    "ax.set_xticklabels(labels, rotation=30, ha='right', "
                    "fontsize=6.0)\n"
                    "    ax.set_xlim(-0.62, len(comp_s) - 0.38)", s)
        if s2 != s:
            s = s2
            print('patched via fallback pattern')

assert s != before, 'nothing changed'
io.open(P, 'w', encoding='utf-8').write(s)

import ast
ast.parse(s)
print('parses; x-limits widened in the responsiveness figure')
