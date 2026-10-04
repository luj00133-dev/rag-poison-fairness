"""Verify the Word submission materials read correctly.

Opening a .docx proves nothing beyond the file being a zip with the right parts, so this checks
what a reader would see: the text actually present in each document, and whether the manuscript
lost anything when the submission block was removed.
"""
import io
import os

import docx

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = os.path.join(P, 'paper')


def text_of(path):
    d = docx.Document(path)
    return [p.text.strip() for p in d.paragraphs if p.text.strip()]


def main():
    for name in ('cover_letter.docx', 'highlights.docx', 'title_page.docx'):
        path = os.path.join(PAPER, name)
        if not os.path.exists(path):
            print('%s MISSING' % name)
            continue
        lines = text_of(path)
        print('=' * 70)
        print('%s -- %d non-empty paragraphs' % (name, len(lines)))
        print('=' * 70)
        for l in lines[:10]:
            print('   %s' % l[:100])
        if len(lines) > 10:
            print('   ... (%d more)' % (len(lines) - 10))
        print()

    # the manuscript must still carry its title, abstract, declaration and availability
    md = text_of(os.path.join(PAPER, 'manuscript_R1R2_v1.docx'))
    joined = '\n'.join(md)
    print('=' * 70)
    print('manuscript_R1R2_v1.docx -- integrity after removing the submission block')
    print('=' * 70)
    checks = [
        ('title present', 'Adversarially Invariant Fairness Statistics' in joined),
        ('author present', 'Lu Jiang' in joined),
        ('abstract present', 'Abstract' in joined),
        ('highlights block removed', 'SUBMISSION ARTIFACT' not in joined),
        ('no leftover comment', '<!--' not in joined),
        ('AI declaration present', 'Declaration of generative AI' in joined),
        ('data availability present', 'Data and Code Availability' in joined),
        ('references present', 'References' in joined),
        ('a known table caption present', 'Table 1' in joined),
        ('a known figure caption present', 'Figure 1' in joined),
    ]
    bad = 0
    for label, ok in checks:
        if not ok:
            bad += 1
        print('   %-34s %s' % (label, 'ok' if ok else 'MISSING'))
    print()
    print('paragraphs: %d' % len(md))
    print('RESULT: %s' % ('manuscript intact' if bad == 0 else '%d problem(s)' % bad))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
