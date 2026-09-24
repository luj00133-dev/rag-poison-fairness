"""Two substantive fixes, both found by describing the rendered images.

1. fig_encoder_scale clipped the SPLADE data point. Its `ylim` was hard-coded to
   (0.0, 0.60) while the SPLADE base value is 0.6250, so the marker and its label sat
   outside the axes and were cut by the canvas. A fixed limit was wrong from the start:
   the figure's whole purpose is to compare values across families and sizes, so the
   range has to come from the data. It is now computed with headroom.

   This is a data-visibility bug, not a cosmetic one: a reader would have seen the
   SPLADE line terminate at its second point with no marker at the first, and could
   reasonably have concluded the series starts at 0.60.

2. fig_responsiveness clipped its y-axis label, "ground-truth group share in corpus",
   at the left edge. Same cause as the earlier label clips: a long rotated string does
   not fit the figure height. Shortened to "group share in corpus"; the caption says it
   is the ground truth.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
s = io.open(P, encoding='utf-8').read()
before = s

# --- 1. y-range from the data ------------------------------------------------- #
OLD = "    ax.set_ylim(-0.06, 0.60)"
NEW = """    # The range comes from the data, not from a constant. A hard-coded 0.60 put the
    # SPLADE base value (0.6250) outside the axes, so its marker and label were cut
    # off by the canvas -- a reader would have seen that series starting at its
    # second point.
    vals = [v for fam in fams for v in d[fam].values()]
    hi = max(vals) * 1.35 + 0.03
    ax.set_ylim(-0.06, hi)"""
assert s.count(OLD) == 1, s.count(OLD)
s = s.replace(OLD, NEW)

# --- 2. shorter y-label ------------------------------------------------------- #
OLD2 = "ax.set_ylabel('ground-truth group share in corpus')"
NEW2 = "ax.set_ylabel('group share in corpus')"
assert s.count(OLD2) == 1, s.count(OLD2)
s = s.replace(OLD2, NEW2)

io.open(P, 'w', encoding='utf-8').write(s)
import ast
ast.parse(s)
print('ylim now derived from data; y-axis label shortened')
print('parses')
