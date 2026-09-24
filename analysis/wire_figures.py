"""Wire figure conversion into make_latex.py and copy the figure PDFs beside the .tex.

Two changes:

1. `postprocess` gains a call to `figure_env.convert_figures`, so markdown images
   become `figure` environments with the width each was given. Without this pandoc
   emits `\\pandocbounded{\\includegraphics...}`, undefined in elsarticle.

2. The figures are copied from `paper/figures/` into `paper/latex/` next to the .tex,
   because LaTeX resolves `\\includegraphics{fig_x.pdf}` relative to the compiling
   directory. Copying rather than referencing keeps the .tex portable: the whole
   `latex/` folder can be zipped and uploaded to the venue without path changes.
"""
import io
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAPER = os.path.join(ROOT, 'paper')
LATEX = os.path.join(PAPER, 'latex')
FIGS = os.path.join(PAPER, 'figures')
MAKE = os.path.join(PAPER, 'make_latex.py')

# --- 1. call the converter from postprocess ---------------------------------- #
s = io.open(MAKE, encoding='utf-8').read()

IMPORT = ("try:\n"
          "    from figure_env import convert_figures\n"
          "except ImportError:  # when run from another directory\n"
          "    from .figure_env import convert_figures\n")

if 'convert_figures' not in s:
    # insert the import after the stdlib imports
    m = re.search(r'^(import [^\n]+\n)+', s, re.M)
    assert m, 'could not find the import block'
    s = s[:m.end()] + '\n' + IMPORT + s[m.end():]
    print('import added')

    # call it as the first thing postprocess does, before any other rewrite, so
    # the figure blocks cannot be touched by the later textual replacements
    anchor = '    # 5 first: it is the pass that can still see the raw backticks'
    assert anchor in s, 'postprocess anchor not found'
    s = s.replace(
        anchor,
        '    # figures first: the replacement inserts a figure environment and a\n'
        '    # caption, and later passes rewrite text that could sit inside one\n'
        '    tex, n_figs = convert_figures(tex)\n'
        '    if n_figs:\n'
        '        print("  converted %d figure(s)" % n_figs)\n\n' + anchor,
        1)
    print('postprocess wired')
else:
    print('already wired')

io.open(MAKE, 'w', encoding='utf-8').write(s)

# --- 2. copy the figure PDFs ------------------------------------------------ #
os.makedirs(LATEX, exist_ok=True)
copied = 0
for f in sorted(os.listdir(FIGS)):
    if f.endswith('.pdf'):
        shutil.copy2(os.path.join(FIGS, f), os.path.join(LATEX, f))
        copied += 1
print('copied %d figure PDF(s) to %s' % (copied, LATEX))
