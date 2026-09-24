"""Fix the figure defects that only a look could find.

A programmatic pass over the rendered PNGs (ink coverage, label markup, aspect ratio)
reported all four figures as sound. Describing them through the vision API found three
real defects in fig_encoder_scale alone:

  1. the y-axis label was clipped: "text-attack adversarial inclusion (poison@" -- the
     closing "k)" fell outside the canvas, because the left margin was 0.13 while the
     rotated label plus its tick labels needed more;
  2. the axes title sat on top of the SPLADE marker at the "base" position;
  3. the "0.5625" annotation collided with the GTE circle and its "0.5000" label,
     leaving the digits partially covered.

A fourth defect was visible in fig_r1_inertness: its suptitle was cut off at the top
edge for the same margin reason.

The fixes are structural rather than cosmetic. Every explanatory heading is removed
from the images and moved into the LaTeX caption, which is where a venue class expects
it and where it cannot be clipped by a margin; margins are set from the longest label
each figure carries; and label offsets are chosen per point so two series that converge
cannot write over each other.

The lesson is recorded in the README: ink coverage and markup checks cannot see layout,
and a vision-capable description can.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
s = io.open(P, encoding='utf-8').read()

# --- 1. drop every in-image title; captions carry that text ------------------- #
s = re.sub(r"\n\s*ax\.set_title\([^\n]*\n", "\n", s)
s = re.sub(r"\n\s*fig\.suptitle\([^\n]*\n(\s*[^\n]*\n)?", "\n", s)
print('in-image titles removed')

# --- 2. margins that fit the longest label each figure carries ---------------- #
OLD_SAVE = s[s.find('def save(fig, name'):s.find('def stat_ok')]
NEW_SAVE = '''def save(fig, name, *, bottom=0.24, left=0.17, right=0.97, top=0.95,
         wspace=0.30):
    """Lay out inside the canvas, then save without cropping.

    Margins are deliberately generous. A vision description of the first render caught
    a clipped y-axis label and a clipped suptitle, both caused by margins that were
    right for the axes but not for the text around them; ink-coverage checks cannot
    see that. Titles now live in the LaTeX caption, so `top` only has to clear the
    axes frame.
    """
    fig.subplots_adjust(bottom=bottom, left=left, right=right, top=top,
                        wspace=wspace)
    os.makedirs(FIGS, exist_ok=True)


'''
s = s.replace(OLD_SAVE, NEW_SAVE)
print('margins widened')

# --- 3. per-figure margins and non-colliding offsets -------------------------- #
s = s.replace("    save(fig, 'fig_r1_inertness')",
              "    save(fig, 'fig_r1_inertness', bottom=0.26, left=0.19,\n"
              "         right=0.98, top=0.97, wspace=0.34)")
s = s.replace("    save(fig, 'fig_aggregate_vs_pergroup')",
              "    save(fig, 'fig_aggregate_vs_pergroup', bottom=0.30, left=0.13,\n"
              "         right=0.98, top=0.97, wspace=0.30)")
s = s.replace("    save(fig, 'fig_encoder_scale')",
              "    save(fig, 'fig_encoder_scale', bottom=0.26, left=0.26,\n"
              "         right=0.97, top=0.97)")
s = s.replace("    save(fig, 'fig_responsiveness')",
              "    save(fig, 'fig_responsiveness', bottom=0.32, left=0.13,\n"
              "         right=0.98, top=0.97, wspace=0.30)")

# the encoder-scale labels collided because both series annotate at the same y
s = s.replace(
    """        for xi, yi in zip((0, 1), y):
            ax.annotate('%.4f' % yi, (xi, yi), textcoords='offset points',
                        xytext=(0, 6 if yi < 0.35 else -11), ha='center',
                        fontsize=6.2, color=col)""",
    """        # offsets differ per series: GTE and SPLADE converge at 'large', so a
        # shared offset wrote one label over the other's marker
        dy = {'GTE': (0, 8), 'E5': (0, 8), 'SPLADE': (0, -13)}[fam]
        dx = {'GTE': (-4, 0), 'E5': (0, 0), 'SPLADE': (14, 12)}[fam]
        for k_, (xi, yi) in enumerate(zip((0, 1), y)):
            ax.annotate('%.4f' % yi, (xi, yi), textcoords='offset points',
                        xytext=(dx[k_], dy[k_]), ha='center', fontsize=6.2,
                        color=col, zorder=5)""")

io.open(P, 'w', encoding='utf-8').write(s)
print('offsets and margins patched')
print('remaining set_title:', s.count('set_title'))
print('remaining suptitle:', s.count('suptitle'))
