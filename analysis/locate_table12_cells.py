"""Locate every Table 12 cell across the whole PDF, page by page.

The table floats: the caption lands at the top of one page and the rows on another (or the
rows are split), so a check against a single page produces a misleading mix of present and
missing. This reports, for each cell value, which page(s) contain it -- and whether any
value appears nowhere at all, which is the only outcome that indicates a real problem.
"""
import os
import re
import subprocess

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.pdf')
pdftotext = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                         'Programs', 'MiKTeX', 'miktex', 'bin', 'x64', 'pdftotext.exe')

txt = subprocess.run([pdftotext, '-raw', PDF, '-'], capture_output=True,
                     timeout=120).stdout.decode('utf-8', 'replace')
pages = txt.split('\f')

# Candidate pages: those mentioning qwen or the table caption
cand = [i for i, p in enumerate(pages, 1)
        if 'qwen-turbo' in p or 'Generation-layer stance' in p]
print('pages mentioning the table or its generators: %s' % cand)
print()

cells = ['0.0008', '0.32', '0.1297', '0.1280', '0.0035', '0.1305', '0.0001',
         '0.0018', '0.042', '0.1298', '0.0015', '0.0491', '0.18', '0.1785',
         '0.0029', '0.0025', '0.42', '0.1322', '0.1294',
         'qwen-turbo', 'qwen-plus', 'qwen-max', 'mistral-7b']
missing = []
for c in cells:
    where = [i for i in cand if c in pages[i - 1]]
    if not where:
        missing.append(c)
    print('   %-12s %s' % (c, where or 'NOWHERE'))

print()
print('cells found nowhere in the PDF: %s' % (missing or 'none'))

# print the actual table rows, wherever they are
for i in cand:
    p = pages[i - 1]
    if 'qwen-turbo' in p and '0.0008' in p:
        j = p.find('qwen-turbo')
        print()
        print('--- candidate table rows, page %d ---' % i)
        print(p[max(0, j - 260):j + 600])
        break
