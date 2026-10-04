"""Verify the new subsection numbers and titles as they print in the PDF.

The section text changed, so the numbering has to be checked in the built document rather than
inferred from the source order. Confirms that the new subsection lands inside the results chapter
and that section 8's subsection still lands inside the discussion.
"""
import os
import re
import subprocess

PDFTOTEXT = r'C:\Users\Administrator\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdftotext.exe'
PDF = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.pdf'
OUT = os.path.join(os.environ['TEMP'], 'pa_verify.txt')

TARGETS = [
    'validity is a property of the back-end',
    'When the aggregate is informative',
    'invariances an adversary can impose',
]


def main():
    subprocess.run([PDFTOTEXT, '-layout', PDF, OUT], check=True, capture_output=True)
    text = open(OUT, encoding='utf-8', errors='ignore').read()
    pages = text.split('\f')
    print('pages in PDF: %d' % (len(pages) - 1))
    found = 0
    for i, page in enumerate(pages, 1):
        for line in page.split('\n'):
            s = line.strip()
            if len(s) > 110 or not s:
                continue
            for t in TARGETS:
                if t in s:
                    print('  page %-3d  %s' % (i, s[:104]))
                    found += 1
    print()
    print('matched %d of %d targets' % (found, len(TARGETS)))
    if found < len(TARGETS):
        print('MISSING: check numbering or a dropped subsection')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
