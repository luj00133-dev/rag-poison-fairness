"""The last two disclaimers, in the markdown, matching what the tex already says.

1. "Treating an evaluation statistic as a measurement ... is not a new idea, and we do not
   claim it as ours." The literature attribution belongs in the paper, but phrasing it as a
   renunciation invites the reviewer to ask what is left. It becomes an attribution: the
   framing is established, and this paper extends it to the adversarial case.

2. "Finding 3 is corpus-dependent and we do not claim it universally." This is a scope
   statement wearing a disclaimer. The scope stays; the wording states it.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

EDITS = [
    ('is not a new idea, and we do not claim it as ours.',
     'is established in the measurement literature, and this paper builds on it.'),
    ('so Finding 3 is corpus-dependent and we do not claim it universally.',
     'so Finding 3 is corpus-dependent, and its scope is stated with it.'),
]


def main():
    s = io.open(MD, encoding='utf-8').read()
    for old, new in EDITS:
        n = s.count(old)
        print('%-52s %d match(es)' % (old[:52], n))
        if n == 1:
            s = s.replace(old, new, 1)
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print('remaining "we do not claim": %d' % s.count('we do not claim'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
