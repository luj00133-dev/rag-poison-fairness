"""Final whole-paper check: numbers resolve in the built PDF, and nothing is left stale.

The point of checking the PDF rather than the source is that LaTeX resolves \\ref at typeset time;
a reference to a missing label prints as "??" and the source looks perfectly fine. So every claim
below is read out of the delivered document.
"""
import io
import os
import re
import subprocess

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.pdf')
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
TXT = os.path.join(os.environ['TEMP'], 'pa_final.txt')
PDFTOTEXT = r'C:\Users\Administrator\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdftotext.exe'


def main():
    subprocess.run([PDFTOTEXT, '-layout', PDF, TXT], check=True, capture_output=True)
    text = io.open(TXT, encoding='utf-8', errors='ignore').read()
    pages = text.split('\f')
    print('pages: %d' % (len(pages) - 1))

    print()
    print('--- unresolved references (would print as ??) ---')
    qq = len(re.findall(r'\?\?', text))
    print('   "??" occurrences: %d' % qq)

    print()
    print('--- do Figure 1..7 and Table 1..11 each appear? ---')
    missing = []
    for n in range(1, 8):
        if not re.search(r'Figure\s*%d\b' % n, text):
            missing.append('Figure %d' % n)
    for n in range(1, 12):
        if not re.search(r'Table\s*%d\b' % n, text):
            missing.append('Table %d' % n)
    print('   missing from the PDF: %s' % (missing or 'none'))

    print()
    print('--- numbered captions in the markdown ---')
    md = io.open(MD, encoding='utf-8').read()
    print('   tables : %s' % re.findall(r'\*\*Table ([A-Z]?\d+)\.', md))
    print('   figures: %s' % re.findall(r'!\[Figure (\d)\.', md))

    print()
    print('--- raster images in the PDF (should be 0) ---')
    PDFIMAGES = r'C:\Users\Administrator\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdfimages.exe'
    out = subprocess.run([PDFIMAGES, '-list', PDF], capture_output=True, text=True).stdout
    rows = [l for l in out.split('\n')[2:] if l.strip()]
    print('   raster images: %d' % len(rows))

    ok = (qq == 0 and not missing and len(rows) == 0)
    print()
    print('VERDICT: %s' % ('clean' if ok else 'PROBLEMS ABOVE'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
