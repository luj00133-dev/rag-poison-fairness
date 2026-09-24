"""Third layout pass: shorten labels and give rotated text room.

The vision check reports three remaining defects, and they share one cause -- text too
long for the space allocated to it.

  * fig_encoder_scale: the rotated y-axis label ("text-attack adversarial inclusion
    (poison@k)", 44 characters) does not fit the figure height, so its leading
    characters are clipped. Rotated text consumes the figure's *height*, not its
    width, which is why widening the left margin did nothing.
  * fig_r1_inertness: the same problem on the same kind of label.
  * fig_responsiveness: the rotated x tick label "swap 3000 reversed" loses its head
    at the left edge, because the rotated label needs horizontal room below the axis
    that the bottom margin did not provide.

The fix is to stop putting full sentences on axes. Axis labels become the short form
("poison@k", "injection budget"), and the full description moves into the LaTeX
caption, where it is typeset at the venue's own size and cannot be clipped by a margin
fraction. Tick labels are shortened to two lines so their rotated extent fits.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
s = io.open(P, encoding='utf-8').read()
before = s

# --- shortened axis labels ---------------------------------------------------- #
s = s.replace("axes[0].set_ylabel('adversarial inclusion (poison@k)')",
              "axes[0].set_ylabel('poison@k')")
s = s.replace("ax.set_ylabel(r'text-attack adversarial inclusion (poison@k)')",
              "ax.set_ylabel('poison@k')")
s = s.replace("ax.set_xlabel(r'injection budget $\\varepsilon$')",
              "ax.set_xlabel(r'budget $\\varepsilon$')")

# --- shorter tick labels, rotated further, with room -------------------------- #
s = s.replace(
    """        'variant': ['baseline', 'swap 500', 'swap 1500', 'swap 3000',
                    'swap 3000\\nreversed'],""",
    """        'variant': ['baseline', 'swap\\n500', 'swap\\n1500', 'swap\\n3000',
                    'swap 3000\\nreversed'],""")

s = s.replace("ax.set_xticklabels(labels, rotation=22, ha='right')",
              "ax.set_xticklabels(labels, rotation=38, ha='right',\n"
              "                   fontsize=6.2)")
s = s.replace("save(fig, 'fig_responsiveness', bottom=0.32, left=0.13,\n"
              "         right=0.98, top=0.97, wspace=0.30)",
              "save(fig, 'fig_responsiveness', bottom=0.38, left=0.13,\n"
              "         right=0.98, top=0.96, wspace=0.30)")

# the encoder figure gained height already; give the taller label its room
s = s.replace("save(fig, 'fig_encoder_scale', bottom=0.22, left=0.30,\n"
              "         right=0.97, top=0.96)",
              "save(fig, 'fig_encoder_scale', bottom=0.22, left=0.20,\n"
              "         right=0.97, top=0.96)")

assert s != before, 'no substitution applied'
io.open(P, 'w', encoding='utf-8').write(s)

import ast
ast.parse(s)
print('labels shortened, rotation increased, margins retuned')
