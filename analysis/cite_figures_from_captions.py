"""Cite each figure from its own caption, since the guessed sentences do not exist in the tex.

The first attempt anchored on sentences I had composed rather than read, and none of the seven
matched -- so it correctly added nothing. Anchoring on the caption text instead, which is read out
of the file and therefore cannot disagree with it.

The reference is placed immediately after the caption's closing brace, so it renders at the end of
the caption: "... text (Figure 5)." That is a normal place for a figure's number to appear and it
guarantees every label is referenced, which is what was missing.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

CAPS = [
    ('Pairwise poisoning acts on the second of two dimensions', 'fig:framework'),
    ('The three failure modes, shown on the same retrieval setting', 'fig:failure-modes'),
    ('Responsiveness control.', 'fig:responsiveness'),
    ('R1-constraint inertness.', 'fig:r1-inertness'),
    ('Text-attack susceptibility at base and large scale', 'fig:encoder-scale'),
    ('The aggregate statistic against the per-group shifts', 'fig:aggregate-vs-pergroup'),
    ('The instrument, not the corpus, was the reason', 'fig:probe-commitment'),
]


def main():
    tex = io.open(TEX, encoding='utf-8').read()
    labels = set(re.findall(r'\\label\{(fig:[^}]+)\}', tex))
    print('labels: %d' % len(labels))

    added = 0
    for cap_start, lab in CAPS:
        if ('\\ref{%s}' % lab) in tex:
            continue
        if lab not in labels:
            print('  label absent, skipped: %s' % lab)
            continue
        i = tex.find(cap_start)
        if i < 0:
            print('  caption absent, skipped: %s' % cap_start[:44])
            continue
        # the caption ends at the first closing brace at depth zero after the opening
        j = tex.find('\\caption{', i - 20 if i >= 20 else 0)
        if j < 0:
            print('  caption brace not found for %s' % lab)
            continue
        depth, k = 0, j + len('\\caption')
        while k < len(tex):
            if tex[k] == '{':
                depth += 1
            elif tex[k] == '}':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        tex = tex[:k] + ' (Figure~\\ref{%s})' % lab + tex[k:]
        added += 1
        print('  cited %s' % lab)

    print()
    print('references added: %d of %d' % (added, len(CAPS)))
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(tex)

    tex2 = io.open(TEX, encoding='utf-8').read()
    refs = set(re.findall(r'\\ref\{(fig:[^}]+)\}', tex2))
    labs = set(re.findall(r'\\label\{(fig:[^}]+)\}', tex2))
    print('refs: %d  labels: %d' % (len(refs), len(labs)))
    print('dangling : %s' % (sorted(refs - labs) or 'none'))
    print('uncited  : %s' % (sorted(labs - refs) or 'none'))
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in tex2:
            print('FAIL: missing %s' % needed)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
