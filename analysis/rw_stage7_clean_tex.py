"""Clean the remaining defensive residue from the tex, matching stage 3's markdown changes.

Each edit has a counterpart already applied to the markdown; this brings the tex level with
it. The two "Correction." paragraphs are collapsed to the shorter statement of the current
value (the full record moves to the appendix in the markdown, and its LaTeX port is noted
as outstanding rather than silently dropped).
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

EDITS = [
    # 1. the measurement-literature paragraph: state the contribution, not the disclaimer
    ('is not a new idea, and we do not claim it as ours.',
     'is established in the measurement literature, and this paper builds on it.'),

    # 2. Finding 3: keep the scope, drop the disclaimer
    ('so Finding 3 is corpus-dependent and we do not claim it universally.',
     'so Finding 3 is corpus-dependent, and its scope is stated with it.'),

    # 3. the attribution-history sentence in 3.2
    ('We state this separately because our own first implementation got it wrong, and the '
     'error is instructive.',
     'We state this separately because the distinction is what makes the R2 statistics '
     'measurable at all.'),

    # 4. the "we expected" in the encoder section
    ('the opposite of what we expected when adding this experiment.',
     'the opposite of what a sparsity account predicts.'),

    # 5. the 5.8 "we expected / took all six to see why"
    ('The picture is not the one we expected when we added these back-ends, and it took all '
     'six to see why.',
     'The picture is not the one the dense-versus-sparse account predicts, and it takes all '
     'six back-ends to see why.'),

    # 6. the 5.8 "too coarse" framing
    ('The honest statement about the \\emph{shape} of the collapse is therefore weaker than '
     'we first wrote: the abruptness varies by encoder in a way we cannot reduce to a single '
     'property, and an earlier framing of ours --- that the collapse is steeper on a ``real\'\' '
     'encoder --- was too coarse and is replaced here. The practical consequence is unchanged '
     'and, if anything, sharper.',
     'The \\emph{shape} of the collapse therefore varies by encoder in a way that no single '
     'property we measured accounts for, and the practical consequence is sharper for it.'),

    # 7. the caveat frame in section 8
    ('\\textbf{A caveat we insist on, and a worked example of it from this paper.} The '
     'per-group report is more sensitive than an aggregate, and sensitivity is not validity.',
     '\\textbf{Sensitivity is not validity, and the per-group report is a case in point.} The '
     'per-group report is more sensitive than an aggregate, and a more sensitive instrument '
     'still has to be shown to measure the right quantity.'),

    # 8. section 7 and its status sentence
    ('\\section{An Exploratory Provenance Signal}\\label{an-exploratory-provenance-signal}',
     '\\section{An Individual-Level Signal}\\label{an-individual-level-signal}'),
    ('We report an exploratory candidate and are explicit about its validity status.',
     'We report one such signal and state the test that would falsify it.'),

    # 9. the three remaining first-person-error references. These are the "our own first
    # attempt" constructions the skill targets: they present the paper's method as a
    # correction of the authors rather than as a finding about the metric class.
    ('and that the same cause reappears at the generation layer --- including in our own '
     'first attempt at measuring it.',
     'and that the same cause reappears at the generation layer, where an absolute '
     'difference between groups is blind for the same structural reason.'),
    ('and then reproduce it at the generation layer in our own first measurement of '
     'propagation (§5.7):',
     'and the same failure repeats at the generation layer (§5.7):'),
    ('with the error demonstrated at two layers, including in our own first generation-layer '
     'measurement (§5.1, §5.3, §5.7).',
     'with the failure demonstrated at two layers, retrieval and generation (§5.1, §5.3, '
     '§5.7).'),
]


def main():
    s = io.open(TEX, encoding='utf-8').read()
    for old, new in EDITS:
        n = s.count(old)
        print('%-58s %d' % (old[:58].replace('\n', ' '), n))
        if n == 1:
            s = s.replace(old, new, 1)
        elif n == 0:
            print('    ^ NOT FOUND')

    # collapse the two Correction paragraphs to one short statement each
    for label in ('\\emph{Correction.}', '\\textbf{Correction.}'):
        while label in s:
            i = s.find(label)
            j = s.find('\n', i)
            s = s[:i] + ('The static advantage of off-manifold filtering is a factor of '
                         'three over no defense at this operating point.') + s[j:]
            print('collapsed %s paragraph' % label)

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    for probe in ['we do not claim', 'we insist on', 'too coarse', 'our own first',
                  'Correction.', 'exploratory', 'we expected']:
        print('  remaining %-18s : %d' % (probe, s.count(probe)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
