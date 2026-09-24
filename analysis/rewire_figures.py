"""Repoint make_latex.py at the correct figure handling.

The previous wiring called a markdown-stage converter from `postprocess`, which runs
*after* pandoc. That produced a worked example of the confusion: the convert_figures
call found nothing to do because pandoc had already replaced the image markdown, while
pandoc's own output carried `alt={...}`, `height=\\textheight` and a mangled path, and
the manuscript failed to compile with four "file not found" errors.

This switches the wiring to `normalise_graphic_includes`, which is designed for the
stage it actually runs in, and drops the earlier call.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.join(os.path.dirname(HERE), 'paper')
MAKE = os.path.join(PAPER, 'make_latex.py')

s = io.open(MAKE, encoding='utf-8').read()

# 1. import the right function
s = s.replace('from figure_env import convert_figures',
              'from figure_env import normalise_graphic_includes')
s = s.replace('from .figure_env import convert_figures',
              'from .figure_env import normalise_graphic_includes')

# 2. remove the wrong-stage call
s = re.sub(
    r"    # figures first: the replacement inserts a figure environment and a\n"
    r"    # caption, and later passes rewrite text that could sit inside one\n"
    r"    tex, n_figs = convert_figures\(tex\)\n"
    r"    if n_figs:\n"
    r'        print\("  converted %d figure\(s\)" % n_figs\)\n\n',
    '', s)

# 3. add the correct call, at the END of postprocess so nothing can disturb it
if 'normalise_graphic_includes(tex)' not in s:
    m = re.search(r'\ndef _convert_bibliography', s)
    assert m, 'could not find the function after postprocess'
    # find the last return inside postprocess, i.e. the one before this def
    head = s[:m.start()]
    last_ret = head.rfind('    return tex')
    assert last_ret != -1, 'postprocess has no return tex'
    s = (head[:last_ret]
         + '    # figures last: pandoc emits alt={...}, height=\\textheight and a\n'
           '    # path with directories, none of which the venue classes accept\n'
           '    tex, n_figs = normalise_graphic_includes(tex)\n'
           '    if n_figs:\n'
           '        print("  normalised %d figure include(s)" % n_figs)\n'
         + head[last_ret:]
         + s[m.start():])
    print('call added at the end of postprocess')

io.open(MAKE, 'w', encoding='utf-8').write(s)
print('import:', 'normalise_graphic_includes' in s)
print('stale convert_figures call present:', 'convert_figures(tex)' in s)
