"""Second round of layout fixes, driven by a second vision description.

The first round removed the in-image titles and widened margins, which fixed
fig_encoder_scale's title-on-marker collision. Two problems survived:

  * fig_encoder_scale still clips its y-axis label ("...inclusion (poison@" with the
    "k)" outside the canvas). The cause is not the margin fraction but the figure
    being too short: at 88 mm wide and 52 mm tall there is not enough vertical room
    beside the axes for a rotated label of that length, so `left` cannot be increased
    far enough without squeezing the plot. The fix is a taller canvas.
  * fig_r1_inertness reported a clipped line at the top, which is the suptitle that
    the previous pass intended to delete. It is now confirmed gone from the source, so
    the taller canvas and a slightly lower `top` are what remain to change.

Both changes are size adjustments rather than content changes, so no number moves.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
s = io.open(P, encoding='utf-8').read()

before = s

# taller canvases, so a long rotated axis label has room beside the axes
s = s.replace("figsize=(88 * MM, 52 * MM)", "figsize=(88 * MM, 62 * MM)")
s = s.replace("figsize=(88 * MM, 42 * MM)", "figsize=(88 * MM, 50 * MM)")

# and margins that use the extra room
s = s.replace("save(fig, 'fig_encoder_scale', bottom=0.26, left=0.26,\n"
              "         right=0.97, top=0.97)",
              "save(fig, 'fig_encoder_scale', bottom=0.22, left=0.30,\n"
              "         right=0.97, top=0.96)")
s = s.replace("save(fig, 'fig_r1_inertness', bottom=0.26, left=0.19,\n"
              "         right=0.98, top=0.97, wspace=0.34)",
              "save(fig, 'fig_r1_inertness', bottom=0.24, left=0.20,\n"
              "         right=0.98, top=0.93, wspace=0.34)")

assert s != before, 'no substitution applied'
io.open(P, 'w', encoding='utf-8').write(s)

import ast
ast.parse(s)
print('make_figures.py parses; canvases raised and margins retuned')
for m in re.finditer(r'figsize=\(([^)]+)\)', s):
    print('   figsize: %s' % m.group(1))
