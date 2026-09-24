"""Remove the orphaned title-argument lines left by the previous regex pass.

`fix_figure_defects.py` stripped `ax.set_title(...)` with a single-line regex, but
several calls span two lines, so the second line survived as a bare argument list and
the module no longer parsed (IndentationError at line 104). The video-check that found
the original clipped-title defect could not have caught this: it operates on rendered
images, and the script no longer renders.

This removes any line that is nothing but continuation arguments for a title call that
no longer exists, identified precisely: a line whose stripped form begins with
`fontsize=` or `pad=` and is not preceded by an unclosed call.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_figures.py')
lines = io.open(P, encoding='utf-8').read().split('\n')

out = []
removed = 0
for i, line in enumerate(lines):
    st = line.strip()
    orphan = (st.startswith('fontsize=') or st.startswith('pad=')) and \
        (not out or not out[-1].rstrip().endswith(','))
    if orphan:
        removed += 1
        continue
    out.append(line)

io.open(P, 'w', encoding='utf-8').write('\n'.join(out))
print('removed %d orphaned argument line(s)' % removed)

# compile-check, since the whole point of this script is that the file parses
import ast
try:
    ast.parse('\n'.join(out))
    print('make_figures.py parses')
except SyntaxError as e:
    print('STILL BROKEN at line %s: %s' % (e.lineno, e.msg))
    for k in range(max(0, e.lineno - 4), min(len(out), e.lineno + 2)):
        print('  %4d: %s' % (k + 1, out[k]))
