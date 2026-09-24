"""Rebuild every figure environment from scratch, discarding pandoc's version.

Pandoc's LaTeX figure output puts the caption into the `alt` option of
`\\includegraphics` and appends its remainder to the option list, so the rendered
option string contained `width=140mm, \\}792 passages and passages are swapped...`.
Cleaning that in place is guesswork about how pandoc split the text.

Rebuilding is deterministic instead: for each figure environment, take the path from
`\\includegraphics`, take the FIRST `\\caption{...}` found in the block by brace
matching, and emit a fresh environment with a width looked up from the manuscript
order. Everything else pandoc wrote inside the block is discarded.

Widths are assigned by figure order, which the manuscript fixes:
    1 responsiveness  140 mm (double column)
    2 aggregate-vs-per-group 140 mm
    3 r1 inertness  88 mm
    4 encoder scale 88 mm
"""
from __future__ import annotations

import os
import re

WIDTHS = ['140mm', '140mm', '88mm', '88mm']


def _match_braces(s: str, i: int) -> int:
    """Index just past the brace group starting at s[i] == '{'."""
    depth = 0
    while i < len(s):
        if s[i] == '{' and (i == 0 or s[i - 1] != '\\'):
            depth += 1
        elif s[i] == '}' and (i == 0 or s[i - 1] != '\\'):
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(s)


def rebuild_figures(tex: str) -> tuple[str, int]:
    out = []
    pos = 0
    n = 0
    while True:
        b = tex.find('\\begin{figure}', pos)
        if b == -1:
            out.append(tex[pos:])
            break
        e = tex.find('\\end{figure}', b)
        if e == -1:
            out.append(tex[pos:])
            break
        block = tex[b:e]
        out.append(tex[pos:b])

        gi = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}', block)
        path = os.path.basename(gi.group(1).strip()) if gi else ''
        ci = block.find('\\caption{')
        caption = ''
        if ci != -1:
            end = _match_braces(block, ci + len('\\caption'))
            caption = block[ci + len('\\caption{'):end - 1]
        width = WIDTHS[n] if n < len(WIDTHS) else WIDTHS[-1]
        label = 'fig:' + re.sub(r'^fig[_-]?', '',
                                os.path.splitext(path)[0]).replace('_', '-')
        out.append(
            '\\begin{figure}[t]\n\\centering\n'
            '\\includegraphics[width=%s]{%s}\n'
            '\\caption{%s}\n\\label{%s}\n\\end{figure}'
            % (width, path, caption, label))
        n += 1
        pos = e + len('\\end{figure}')
    return ''.join(out), n


def normalise_graphic_includes(tex: str) -> tuple[str, int]:
    """Kept as the entry point make_latex.py already imports."""
    return rebuild_figures(tex)
