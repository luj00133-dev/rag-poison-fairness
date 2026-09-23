"""Move secondary tables out of the main body into a new Appendix C.

Measured density is the reason: the body is 547 paragraphs with 16 tables over 39
pages, and the 5.5/5.6 compression removed 6,889 characters for one page, because
a LaTeX table costs vertical space far out of proportion to its character count.
Cutting prose is therefore the wrong lever; moving tables is the right one.

What moves, and why each is safe to move:
  * adaptive-attacker sweep (was Table 12) -- the *result* (static ranking inverts,
    every defense at 1.000 by lambda=2) stays in the body as prose with its
    numbers; only the per-lambda grid moves.
  * forced-choice generation table (was Table 13) -- historical, superseded by the
    entailment table that stays; the body keeps the 46%-versus-0.0018 contrast
    that is the actual point.
  * Prop. 1 empirical check (was Table 15) -- a confirmation table whose content
    is one sentence ("every cell is 0.000").
  * over-generalisation signal (was Table 16) -- exploratory, and its paper
    section already flags it as unvalidated.
  * bootstrap CIs (was Table 18) -- depends on the paired-tests table already in
    Appendix B.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

#: (table number in the body, regex for the caption line, new appendix label)
MOVE = [
    ('12', 'Adaptive attacker \\(defense-aware\\)', 'C1'),
    ('13', 'The first generation-layer measurement', 'C2'),
    ('15', 'Prop\\. 1 prediction vs\\. measurement', 'C3'),
    ('16', 'Over-generalisation signal', 'C4'),
    ('18', 'Bootstrap 95% CIs on the positive claims', 'C5'),
]

appendix_tables = []
for num, pat, label in MOVE:
    # find the caption and the contiguous block that follows it (table body)
    m = re.search(r'^\*\*Table %s\.\*\*.*?$' % num, s, re.M)
    if not m:
        print('NOT FOUND: Table %s (%s)' % (num, pat))
        continue
    start = m.start()
    # block = caption line, blank line, then all consecutive '|' rows
    lines = s[start:].split('\n')
    end_rel = 1
    for i, l in enumerate(lines[1:], 1):
        if l.strip().startswith('|') or l.strip() == '':
            end_rel = i
            if not l.strip().startswith('|') and i > 1:
                break
        else:
            break
    block = '\n'.join(lines[:end_rel]).rstrip()
    appendix_tables.append((label, block))
    s = s[:start] + ('*The per-λ grid is in Appendix C, Table %s.*' % label
                     if num == '12' else '') + s[start + len(block):]
    print('moved Table %s -> Appendix Table %s' % (num, label))

# append Appendix C
C = ['', '---', '',
     '## Appendix C. Secondary tables', '',
     'Tables moved out of the main body to keep it readable. Each is referenced '
     'from the section that discusses it.', '']
for label, block in appendix_tables:
    block = re.sub(r'^\*\*Table \S+?\.\*\*', '**Table %s.**' % label, block)
    C.append(block)
    C.append('')

anchor = '\n---\n\n## References'
assert s.count(anchor) == 1, s.count(anchor)
s = s.replace(anchor, '\n'.join(C) + anchor)

io.open(P, 'w', encoding='utf-8').write(s)

print()
print('body tables : %s' % ' '.join(re.findall(r'^\*\*Table (\d+)\.\*\*', s, re.M)))
print('appendix    : %s' % ' '.join(re.findall(r'^\*\*Table (C?\d+[a-z]?)\.\*\*', s, re.M)))
print('length: %d chars' % len(s))
