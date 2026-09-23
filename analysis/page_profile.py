"""Accurate page profile of Paper A.

The first version matched section names anywhere in the extracted text, so the
"Appendix A" entry was found on page 10 -- a page that merely *mentions* Appendix
A in a cross-reference -- and the numbers were wrong. This anchors on headings
that appear at the start of a line, which is where a heading lands in a
`pdftotext -layout` extraction, and reports the body/appendix split explicitly
since that is the number that matters for a length judgement.
"""
import os
import re
import subprocess
import sys

LATEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'paper', 'latex')
PDF = os.path.join(LATEX, 'paperA_R1R2.pdf')

pdftotext = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                         'Programs', 'MiKTeX', 'miktex', 'bin', 'x64',
                         'pdftotext.exe')
if not os.path.exists(pdftotext):
    print('pdftotext not found')
    sys.exit(0)

txt = subprocess.run([pdftotext, '-layout', PDF, '-'],
                     capture_output=True, timeout=120).stdout.decode(
                         'utf-8', 'replace')
pages = txt.split('\f')

#: headings, matched only at the start of a line (which is how a real heading is
#: laid out, as opposed to a mid-sentence cross-reference)
HEADINGS = [
    (r'^\s*1\.\s+Introduction', '1 Introduction'),
    (r'^\s*2\.\s+Related Work', '2 Related Work'),
    (r'^\s*3\.\s+Two Dimensions', '3 Two Dimensions'),
    (r'^\s*4\.\s+Attack and Evaluation', '4 Attack and Evaluation'),
    (r'^\s*5\.\s+Results', '5 Results'),
    (r'^\s*6\.\s+Why Distribution-Level', '6 Why Distribution-Level'),
    (r'^\s*7\.\s+An Exploratory', '7 An Exploratory'),
    (r'^\s*8\.\s+Discussion', '8 Discussion'),
    (r'^\s*9\.\s+Conclusion', '9 Conclusion'),
    (r'^\s*Data and Code Availability', 'Data and Code'),
    (r'^\s*Appendix A\.', 'Appendix A'),
    (r'^\s*Appendix B\.', 'Appendix B'),
    (r'^\s*Appendix C\.', 'Appendix C'),
    (r'^\s*References', 'References'),
]

found = {}
for i, p in enumerate(pages, start=1):
    for pat, label in HEADINGS:
        if label in found:
            continue
        if re.search(pat, p, re.M):
            found[label] = i

n_body_pages = 39
print('%-28s %s' % ('section', 'starts on page'))
order = [lbl for _, lbl in HEADINGS]
for lbl in order:
    if lbl in found:
        print('%-28s %d' % (lbl, found[lbl]))

print()
start_appendix = min([found[l] for l in ('Appendix A', 'Appendix B', 'Appendix C')
                      if l in found] or [0])
start_refs = found.get('References', 0)
print('body (1 .. %d)                 : %d pages'
      % (start_appendix - 1 if start_appendix else 39,
         (start_appendix - 1) if start_appendix else 39))
if start_appendix:
    print('appendices (A .. before refs)  : %d pages'
          % ((start_refs - start_appendix) if start_refs else 0))
if start_refs:
    print('references                     : %d pages' % (40 - start_refs))
print()
print('total: %d pages' % n_body_pages)
