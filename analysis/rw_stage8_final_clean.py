"""Apply the last intro clean-ups to the markdown and re-run the tex cleaner.

Two first-person-error constructions survive in the markdown introduction ("including in our
own first attempt at measuring it", "including in our own first generation-layer
measurement"). Both present a finding about a metric class as a correction of the authors,
which is the pattern the skill targets. The tex counterparts are handled by
rw_stage7_clean_tex.py, which is idempotent for the edits already applied.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

EDITS = [
    ('and that the same cause reappears at the generation layer — including in our own '
     'first attempt at measuring it.',
     'and that the same cause reappears at the generation layer, where an absolute '
     'difference between groups is blind for the same structural reason.'),
    ('with the error demonstrated at two layers, including in our own first generation-layer '
     'measurement (§5.1, §5.3, §5.7).',
     'with the failure demonstrated at two layers, retrieval and generation (§5.1, §5.3, '
     '§5.7).'),
]


def main():
    s = io.open(MD, encoding='utf-8').read()
    for old, new in EDITS:
        n = s.count(old)
        print('%-56s %d match(es)' % (old[:56], n))
        if n == 1:
            s = s.replace(old, new, 1)
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    for probe in ['our own first', 'we fell into', 'we do not claim', 'we insist on',
                  'not be credible about', 'exploratory']:
        print('  markdown remaining %-22s : %d' % (probe, s.count(probe)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
