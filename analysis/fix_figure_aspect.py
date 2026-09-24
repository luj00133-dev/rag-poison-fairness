"""Make the rendered PNG dimensions match the declared figure size exactly.

Because the output used `bbox_inches='tight'`, any artist extending past the axes --
rotated tick labels, a legend placed outside, an annotation with an offset -- was
included in the bounding box and stretched the image. The results were 2.4:1 and
2.6:1 against an intended 2:1, and the declared sizes were therefore not the sizes
anyone would get.

The fix is to stop cropping: render the full canvas and lay the axes out inside it
with explicit margins big enough for the rotated labels. Then 140 x 48 mm really is
140 x 48 mm, the aspect ratio is what the layout says it is, and a figure placed at
1:1 in LaTeX is exactly the width intended.

Applied by rewriting the save helper and the subplot margins in make_figures.py.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
s = io.open(P, encoding='utf-8').read()

# 1. no cropping, and no pad
s = s.replace("    'savefig.bbox': 'tight',\n    'savefig.pad_inches': 0.02,\n",
              "    # no crop: a tight bbox lets rotated tick labels stretch the image,\n"
              "    # so the declared figure size would not be the delivered size\n"
              "    'savefig.bbox': None,\n")
if "savefig.pad_inches" in s:
    s = re.sub(r"\n\s*'savefig\.pad_inches':[^\n]*", '', s)

# 2. explicit margins so rotated labels fit inside the canvas
s = s.replace(
    "def save(fig, name):\n    os.makedirs(FIGS, exist_ok=True)",
    "def save(fig, name, *, bottom=0.20, left=0.13, right=0.97, top=0.86,\n"
    "         wspace=0.28):\n"
    "    \"\"\"Lay out inside the canvas, then save without cropping.\"\"\"\n"
    "    fig.subplots_adjust(bottom=bottom, left=left, right=right, top=top,\n"
    "                        wspace=wspace)\n"
    "    os.makedirs(FIGS, exist_ok=True)")

io.open(P, 'w', encoding='utf-8').write(s)
print('save() now lays out explicitly and does not crop')
print('savefig.bbox tight present:', "bbox': 'tight'" in s)
print('pad_inches present:', 'pad_inches' in s)
