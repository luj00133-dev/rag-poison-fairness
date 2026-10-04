"""Add numbered figure citations to the tex and confirm the labels resolve.

The tex has seven \\caption{} and seven fig: labels but zero \\ref{fig:...}, so the figures print
with numbers no sentence points at. This inserts one cross-reference per figure, immediately before
the paragraph that discusses it, and then verifies that every \\ref targets a label that exists.

Written as a file rather than a shell heredoc because the escaping needed for LaTeX backslashes in
a heredoc has defeated me three times in this session.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

# caption opening -> the sentence fragment before which the reference is inserted
ANCHORS = {
    'Pairwise poisoning acts on the second of two dimensions':
        ('fig:framework', 'The paper separates two dimensions of representation.'),
    'The three failure modes, shown on the same retrieval setting':
        ('fig:failure-modes', 'Three single-cause constructions each suffice.'),
    'Responsiveness control.':
        ('fig:responsiveness', 'The indicted statistics are working instruments.'),
    'R1-constraint inertness.':
        ('fig:r1-inertness', 'The constraint is inert rather than weak.'),
    'Text-attack susceptibility at base and large scale':
        ('fig:encoder-scale', 'Susceptibility is a per-checkpoint property.'),
    'The aggregate statistic against the per-group shifts':
        ('fig:aggregate-vs-pergroup', 'The signal is in the per-group shift.'),
    'The instrument, not the corpus, was the reason':
        ('fig:probe-commitment', 'The instrument, not the corpus, suppressed the effect.'),
}


def main():
    tex = io.open(TEX, encoding='utf-8').read()

    labels = re.findall(r'\\label\{(fig:[^}]+)\}', tex)
    print('figure labels present: %d' % len(labels))
    for l in labels:
        print('   %s' % l)

    # every anchor must name a label that exists
    missing = [lab for _cap, (lab, _txt) in ANCHORS.items() if lab not in labels]
    if missing:
        print()
        print('ANCHOR MISMATCH, labels expected but not found: %s' % missing)
        print('Nothing written. The label names must match before a reference can point at them.')
        return 1

    added = 0
    for cap_start, (lab, sentence) in ANCHORS.items():
        ref = 'Figure~\\ref{%s}' % lab
        if ref in tex or ('\\ref{%s}' % lab) in tex:
            continue
        i = tex.find(sentence)
        if i < 0:
            print('  sentence not found, skipped: %s' % sentence[:44])
            continue
        tex = tex[:i] + ref + ' ' + tex[i:]
        added += 1
        print('  cited %-30s' % lab)

    print()
    print('references added: %d of %d' % (added, len(ANCHORS)))

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(tex)

    tex2 = io.open(TEX, encoding='utf-8').read()
    refs = set(re.findall(r'\\ref\{(fig:[^}]+)\}', tex2))
    labs = set(re.findall(r'\\label\{(fig:[^}]+)\}', tex2))
    print('refs: %d   labels: %d' % (len(refs), len(labs)))
    print('dangling refs : %s' % (sorted(refs - labs) or 'none'))
    print('uncited labels: %s' % (sorted(labs - refs) or 'none'))
    for needed in ('\\begin{document}', '\\end{document}'):
        if needed not in tex2:
            print('FAIL: missing %s' % needed)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
