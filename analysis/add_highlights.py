"""Add the Highlights as a submission artifact, in both sources.

IP&M requires 3-5 highlights of at most 85 characters each. They are entered in the
submission system's own field, not typeset into the manuscript -- so they are written to
paper/highlights.txt rather than into the paper body, and the markdown gets a clearly
labelled block at the top so the docx carrying them is self-describing.

Each highlight is a claim, so each is checked against the manuscript by
verify_highlights.py before being written. None of them is a number the paper does not
contain:

  1 the statistics are adversarially invariant        -> abstract, taxonomy (F1-F3)
  2 three modes defeat the three metric families      -> §3.4
  3 per-group shifts 0.13 against a gap under 0.002   -> §5.7, Table 12
  4 static advantage largest on the pretrained encoders -> §5.8, Table 15
  5 a six-point protocol                              -> §5.8.1 (6 items)

Highlight 5 says "six-point" and refers to the protocol in 5.8.1, which is the one with six
items. Section 8 carries a longer nine-point list; the highlight names the six-point one so
the count is not ambiguous.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
TXT = os.path.join(P, 'paper', 'highlights.txt')

HIGHLIGHTS = [
    'Aggregate fairness statistics are adversarially invariant by structure',
    'Three predictable modes defeat composition, reference and difference metrics',
    'Per-group shifts move 0.13 where the cross-group gap moves under 0.002',
    'Static defense advantage is largest on the encoders the field uses',
    'A six-point protocol makes retrieval robustness claims interpretable',
]
LIMIT = 85

BLOCK_HEAD = ('<!-- SUBMISSION ARTIFACT — entered in the journal submission system, not '
              'typeset into the manuscript.\n')
BLOCK_TAIL = '-->\n\n'


def main():
    over = [(h, len(h)) for h in HIGHLIGHTS if len(h) > LIMIT]
    if over:
        print('FAIL: %d highlight(s) over %d characters: %s' % (len(over), LIMIT, over))
        return 1
    if not (3 <= len(HIGHLIGHTS) <= 5):
        print('FAIL: IP&M requires 3-5 highlights, have %d' % len(HIGHLIGHTS))
        return 1
    print('lengths: %s (limit %d)' % ([len(h) for h in HIGHLIGHTS], LIMIT))

    # 1. the plain-text artifact for the submission form
    io.open(TXT, 'w', encoding='utf-8', newline='\n').write(
        '\n'.join(HIGHLIGHTS) + '\n')
    print('wrote %s' % TXT)

    # 2. a labelled block at the top of the markdown
    s = io.open(MD, encoding='utf-8').read()
    if 'SUBMISSION ARTIFACT — entered in the journal' in s:
        print('markdown already carries the block; skipped')
        return 0
    block = (BLOCK_HEAD
             + 'Highlights (3-5 items, each <= 85 characters):\n\n'
             + '\n'.join('* %s' % h for h in HIGHLIGHTS)
             + '\n\n' + BLOCK_TAIL)
    i = s.find('\n---\n')
    if i < 0:
        print('MARKDOWN ANCHOR FAIL')
        return 1
    s = s[:i + 1] + block + s[i + 1:]
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print('inserted the labelled block into the markdown')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
