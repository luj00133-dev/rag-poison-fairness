"""Build the anonymized manuscript, which the checklist promises for double-anonymized review.

The Data and Code Availability section names a repository URL containing the author's username, and
the submitting author's email shares that username, so the URL alone identifies the author. The
manuscript's own note already says to replace it for double-anonymized venues; this produces the
file rather than leaving the instruction for someone to carry out by hand under time pressure.

What is removed: the repository URL from the availability statement, and the name, email and ORCID
from the front matter. What is kept: everything a reviewer needs, including the software
description and the regeneration commands, because anonymising a paper is not a reason to make it
uncheckable.
"""
import io
import os
import re
import sys

from docx import Document
from docx.shared import Pt, Inches

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAPER = os.path.join(ROOT, 'paper')
OUTDIR = os.path.join(PAPER, 'anonymized')
sys.path.insert(0, PAPER)

import make_docx  # noqa: E402  the project's own renderer, so the build matches the main DOCX


def make_anonymized_markdown():
    src = os.path.join(PAPER, 'manuscript_R1R2_v1.md')
    text = io.open(src, encoding='utf-8').read()

    before = text

    # 1. the repository URL, which carries the username
    text = re.sub(r'\*\*https://github\.com/[^*]+\*\*', '**[anonymized repository]**', text)
    text = re.sub(r'https://github\.com/[A-Za-z0-9_./-]+', '[anonymized repository]', text)

    # 2. identifying front matter
    text = re.sub(r'^\*\*Author\*\*:.*$', '**Author**: [anonymized]', text, flags=re.M)
    text = re.sub(r'^\*\*Affiliation\*\*:.*$', '**Affiliation**: [anonymized]', text, flags=re.M)
    text = re.sub(r'^\*\*Corresponding author\*\*:.*$',
                  '**Corresponding author**: [anonymized]', text, flags=re.M)

    # 3. the note that instructed a human to do this is no longer needed in the anonymized file,
    #    but the software-availability content must survive
    text = re.sub(r'\*\*Note for double-anonymized submission\.\*\*.*?(?=\n\n)',
                  'The repository is withheld here for anonymous review and will be named in the '
                  'camera-ready version.', text, flags=re.S)

    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, 'manuscript_anonymized.md')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(text)

    # report what changed, so the edit is auditable rather than trusted
    checks = [
        ('github URL gone', 'github.com' not in text),
        ('username gone', 'luj00133' not in text),
        ('email gone', 'lujiang12@njust.edu.cn' not in text),
        ('ORCID gone', '0009-0001-0717-2732' not in text),
        ('name gone', 'Lu Jiang' not in text),
        ('availability section kept', 'Data and Code Availability' in text),
        ('regeneration commands kept', 'run_experiment' in text),
        ('title kept', 'Adversarially Invariant Fairness Statistics' in text),
        ('unchanged in length within 5%',
         abs(len(text) - len(before)) < 0.05 * len(before)),
    ]
    print('anonymization checks:')
    for label, ok in checks:
        print('   %-34s %s' % (label, 'ok' if ok else 'FAIL'))
    return all(ok for _, ok in checks), out


def main():
    ok, md = make_anonymized_markdown()
    if not ok:
        print('NOT built: anonymization incomplete, so the file would still identify the author')
        return 1

    out = os.path.join(OUTDIR, 'manuscript_anonymized.docx')
    make_docx.render_markdown(
        md, out,
        'Adversarially Invariant Fairness Statistics',
        'Why Aggregate Retrieval-Fairness Metrics Cannot Detect Pairwise Poisoning')
    print('wrote %s (%d bytes)' % (out, os.path.getsize(out)))

    # confirm the DOCX itself is clean, not just the markdown it came from
    d = Document(out)
    joined = '\n'.join(p.text for p in d.paragraphs)
    for label, bad in (('github URL', 'github.com'), ('username', 'luj00133'),
                       ('email', 'lujiang12'), ('ORCID', '0009-0001-0717-2732'),
                       ('author name', 'Lu Jiang')):
        present = bad in joined
        print('   docx contains %-14s %s' % (label, 'STILL PRESENT' if present else 'no'))
        if present:
            return 1
    print('anonymized DOCX verified clean')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
