"""Move explanatory notes out of the figure images and into the LaTeX captions.

The figures were rendered with a `fig.text(...)` note under the axes. Because the
output uses `bbox_inches='tight'`, that note was included in the bounding box and
stretched the images horizontally: fig_responsiveness came out 5338 x 1263, an aspect
ratio of 4.2:1 against an intended 2:1, and the same effect inflated the two-panel
aggregate figure to 2.6:1.

Two problems with that, beyond the aspect ratio. Text baked into an image cannot be
edited, cannot be restyled by the journal's template, and does not appear in the
document's text layer -- so a reader searching the PDF cannot find it and a
translation or accessibility pass will miss it. Explanatory prose belongs in the
caption, where the venue class controls its font and position.

This rewrites the two figures to draw only the plot, and the notes are carried in the
captions added to the manuscript.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
s = io.open(P, encoding='utf-8').read()

# --- fig2: drop the fig.text note -------------------------------------------- #
OLD2 = """    fig.text(0.5, -0.06,
             'Asterisk marks $p<0.05$ (paired permutation against clean). '
             'Note the different y-scales: the aggregate moves by $<0.002$, the '
             'groups by $\\\\approx 0.13$.',
             ha='center', fontsize=6.2, wrap=True)
    save(fig, 'fig_aggregate_vs_pergroup')"""
NEW2 = """    save(fig, 'fig_aggregate_vs_pergroup')"""
if s.count(OLD2) == 1:
    s = s.replace(OLD2, NEW2)
    print('fig2 note removed')
else:
    # fall back to a slice between the marker lines
    i = s.find("    fig.text(0.5, -0.06,")
    j = s.find("    save(fig, 'fig_aggregate_vs_pergroup')", i)
    if i != -1 and j > i:
        s = s[:i] + s[j:]
        print('fig2 note removed (by slice)')
    else:
        print('fig2 note NOT found')

# --- fig4: drop the fig.text note -------------------------------------------- #
i = s.find("    fig.text(0.5, -0.10,")
j = s.find("    save(fig, 'fig_responsiveness')", i)
if i != -1 and j > i:
    s = s[:i] + s[j:]
    print('fig4 note removed')

io.open(P, 'w', encoding='utf-8').write(s)

# report any remaining fig.text
import re
left = re.findall(r'fig\.text\([^)]*', s)
print('remaining fig.text calls: %d' % len(left))
for t in left:
    print('   %s' % t[:70])
