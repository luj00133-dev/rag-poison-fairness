"""Accurate page profile of Paper A.

Two earlier versions of this script were wrong, and both errors are worth recording
because each produced a confidently incorrect number:

 1. Section names were matched anywhere in the extracted text, so "Appendix A" was
    found on a page that merely *mentions* it in a cross-reference. Fixed by
    anchoring on headings at the start of a line.
 2. The appendix patterns had the wrong case ("Appendix A." where pdflatex writes
    "APPENDIX A."), so no appendix was ever found: the script reported an 8-page
    reference section and a negative body length. Fixed by matching case-insensitively
    on a heading that occupies its own line.

The page total is now computed from the extracted text rather than hardcoded, since a
hardcoded total silently goes stale the moment the paper changes length -- which is
exactly what happened here.
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
total_pages = len([p for p in pages if p.strip()])

#: headings, matched only at the start of a line (which is how a real heading is
#: laid out, as opposed to a mid-sentence cross-reference). The appendix patterns are
#: case-insensitive because the generated tex uppercases those headings.
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
    # The appendix headings are extracted as "11. Appendix A. Reproduction" -- numbered
    # section headings -- while in-text cross-references read "Appendix A. Two corpora
    # are used" and also start a line inside a justified paragraph. Requiring the
    # section number is what separates the two; without it the profiler reported the
    # appendix as starting on page 14, where a sentence merely cites it.
    (r'^\s*\d+\.\s*[Aa]ppendix\s+A[\.\s]', 'Appendix A'),
    (r'^\s*\d+\.\s*[Aa]ppendix\s+B[\.\s]', 'Appendix B'),
    (r'^\s*\d+\.\s*[Aa]ppendix\s+C[\.\s]', 'Appendix C'),
    (r'^\s*\d+\.\s*[Aa]ppendix\s+D[\.\s]', 'Appendix D'),
    (r'^\s*(?:References|REFERENCES)\s*$', 'References'),
]

found = {}
for i, p in enumerate(pages, start=1):
    for pat, label in HEADINGS:
        if label in found:
            continue
        if re.search(pat, p, re.M | re.I):
            found[label] = i

print('%-28s %s' % ('section', 'starts on page'))
order = [lbl for _, lbl in HEADINGS]
for lbl in order:
    if lbl in found:
        print('%-28s %d' % (lbl, found[lbl]))

appendix_pages = [found[l] for l in ('Appendix A', 'Appendix B', 'Appendix C',
                                     'Appendix D')
                  if l in found]
start_appendix = min(appendix_pages) if appendix_pages else 0
start_refs = found.get('References', 0)

print()
if start_appendix:
    print('body (1 .. %d)                 : %d pages'
          % (start_appendix - 1, start_appendix - 1))
    if start_refs:
        print('appendices (%d .. %d)          : %d pages'
              % (start_appendix, start_refs - 1, start_refs - start_appendix))
    if start_refs:
        print('references (%d .. %d)          : %d pages'
              % (start_refs, total_pages, total_pages - start_refs + 1))
print()
print('total: %d pages' % total_pages)
