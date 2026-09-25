"""Dump every citation site in the tex with its surrounding words.

Converting to author-date is not a find-and-replace: a site has to become \\citet (the
author is part of the sentence: "Wang et al. [4] show") or \\citep (the citation is a
parenthetical aside: "injected passages [2, 3]"). Getting that wrong produces "Wang et
al. (2025) et al. show" or a citation stranded mid-clause.

The surrounding text is therefore printed for every site, so the choice can be made per
site and checked, rather than guessed by a rule.
"""
import io
import re

TEX = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.tex'

s = io.open(TEX, encoding='utf-8').read()
body = s[:s.find('\\begin{thebibliography}')]

# blank out the pieces that are not citations so the contexts read cleanly
sites = []
for m in re.finditer(r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}', body):
    left = body[max(0, m.start() - 95):m.start()]
    right = body[m.end():m.end() + 60]
    # is the site adjacent to an author name already in the text?
    tail = re.sub(r'\s+', ' ', left)[-60:]
    head = re.sub(r'\s+', ' ', right)[:50]
    sites.append((m.group(1), tail, head))

print('citation sites: %d' % len(sites))
print()
for i, (nums, tail, head) in enumerate(sites, 1):
    print('%3d  [%s]' % (i, nums))
    print('     ...%s <<HERE>> %s...' % (tail, head))
