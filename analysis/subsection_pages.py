"""Page ranges for the subsections, so the length discussion rests on measurement.

The earlier profile showed section 5 spans pages 10-23 but not how that divides
between the encoder material, the adaptive material and the generation material.
Without that breakdown there is no basis for deciding what further to cut.
"""
import os
import re
import subprocess

LATEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'paper', 'latex')
pdftotext = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                         'Programs', 'MiKTeX', 'miktex', 'bin', 'x64',
                         'pdftotext.exe')
txt = subprocess.run([pdftotext, '-layout',
                      os.path.join(LATEX, 'paperA_R1R2.pdf'), '-'],
                     capture_output=True, timeout=120).stdout.decode(
                         'utf-8', 'replace')
pages = txt.split('\f')

MARKS = [
    (r'5\.1\.\s+Pairwise poisoning', '5.1 R2 attack'),
    (r'5\.2\.\s+The R1-only defense', '5.2 R1 inert'),
    (r'5\.3\.\s+The R2 constraint works', '5.3 R2 constraint'),
    (r'5\.4\.\s+Replication on a natural', '5.4 BBQ replication'),
    (r'5\.5\.\s+Encoder robustness', '5.5 Encoder robustness'),
    (r'5\.6\.\s+Adaptive attacker', '5.6 Adaptive attacker'),
    (r'5\.7\.\s+Generation-stage propagation', '5.7 Generation stage'),
    (r'6\.1\.\s+Setup', '6.1 Setup'),
    (r'6\.4\.\s+Proposition 3', '6.4 Prop 3 trilemma'),
    (r'6\.5\.\s+Proposition 4', '6.5 Prop 4 structural'),
    (r'6\.6\.\s+Dimensionality', '6.6 detection'),
    (r'7\.\s+An Exploratory', '7 Provenance'),
    (r'8\.\s+Discussion', '8 Discussion'),
    (r'9\.\s+Conclusion', '9 Conclusion'),
    (r'Appendix A\. Reproduction', 'App A'),
    (r'Appendix B\. Paired', 'App B'),
    (r'Appendix C\. Secondary', 'App C'),
    (r'References', 'References'),
]

found = {}
for i, pg in enumerate(pages, start=1):
    for pat, label in MARKS:
        if label not in found and re.search(pat, pg):
            found[label] = i

order = [lbl for _, lbl in MARKS]
print('%-26s %6s %6s' % ('subsection', 'page', 'pages'))
for k, lbl in enumerate(order):
    if lbl not in found:
        print('%-26s %6s' % (lbl, '?'))
        continue
    start = found[lbl]
    nxt = next((found[order[j]] for j in range(k + 1, len(order))
                if order[j] in found), 40)
    print('%-26s %6d %6s' % (lbl, start,
                             ('%d' % (nxt - start)) if nxt > start else '-'))
