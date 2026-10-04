"""Make the figure checker derive its expectation from the tex instead of a hardcoded list.

The checker kept reporting the paper as broken after the figures were legitimately redrawn, because
its expected filenames were written into the script. A checker that has to be edited every time the
figures change will eventually be ignored, which is worse than not having it.

This rewrites it to read the actual \\includegraphics list out of the tex and verify that each named
file is present next to the document. Whether a figure is the right figure is a matter for the
contract in analysis/figure_contract.md and for looking at it; whether the file the document asks
for exists is what a script should decide.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = os.path.join(P, 'analysis', 'verify_pdf_figures.py')
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

NEW = '''"""Verify that every figure the tex asks for exists, and that none is a raster placeholder.

Expectation is READ FROM THE TEX rather than hardcoded. An earlier version listed the expected
filenames inline and therefore reported the document as broken every time a figure was legitimately
redrawn -- the kind of checker that gets ignored, which is worse than having none.

Two things are checked, both of which a clean compile does not prove:
  1. every \\includegraphics target exists next to the document (pdftex.def falls back to a draft
     box and still compiles with zero errors when one is missing);
  2. the built PDF contains no raster images, since the concept figures are now vector and a stray
     bitmap would mean one of them silently reverted.
"""
import io
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LATEX_DIR = os.path.join(ROOT, 'paper', 'latex')
TEX = os.path.join(LATEX_DIR, 'paperA_R1R2.tex')
PDF = os.path.join(LATEX_DIR, 'paperA_R1R2.pdf')
PDFIMAGES = r'C:\\Users\\Administrator\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64\\pdfimages.exe'


def main():
    tex = io.open(TEX, encoding='utf-8').read()
    wanted = re.findall(r'\\\\includegraphics(?:\\[[^\\]]*\\])?\\{([^}]+)\\}', tex)
    print('figures the tex asks for: %d' % len(wanted))
    problems = 0
    for name in wanted:
        path = os.path.join(LATEX_DIR, name)
        ok = os.path.exists(path)
        if not ok:
            problems += 1
        size = ('%.0f KB' % (os.path.getsize(path) / 1024.0)) if ok else '-'
        print('   %-4s %-34s %s' % ('OK' if ok else 'MISS', name, size))

    print()
    if os.path.exists(PDF):
        out = subprocess.run([PDFIMAGES, '-list', PDF], capture_output=True, text=True).stdout
        rows = [l for l in out.split('\\n')[2:] if l.strip()]
        print('raster images in the built PDF: %d' % len(rows))
        if rows:
            problems += len(rows)
            for r in rows[:10]:
                print('   ' + ' '.join(r.split()[:8]))
    else:
        print('PDF not built; run compile_papers.py first')
        problems += 1

    print()
    print('RESULT: %s' % ('all figures present and vector' if not problems
                           else '%d problem(s)' % problems))
    return 0 if not problems else 1


if __name__ == '__main__':
    raise SystemExit(main())
'''


def main():
    io.open(OLD, 'w', encoding='utf-8', newline='\n').write(NEW)
    print('rewrote %s' % OLD)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
