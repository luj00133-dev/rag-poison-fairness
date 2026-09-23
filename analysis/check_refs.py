"""Validate every cross-reference in the manuscript against the real structure.

Written after the reframing pass introduced a `§3.4` reference to a section that
does not exist: the paper's subsections end at 3.3. Section references are the
kind of thing a reframing pass silently breaks, so this checks them mechanically
rather than by reading.

Checks:
  * every `§x.y` points at a heading that exists;
  * table caption numbers in the main body are unique and in reading order;
  * every `Table N` reference in prose points at an existing table;
  * every Finding number is unique.

Appendix tables keep their own numbering space and are reported separately rather
than treated as collisions, since "Table 3" in an appendix and "Table 3" in the
body are different objects.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()
lines = s.split('\n')

#: everything from here on is appendix material with its own table numbering
appendix_at = next((i for i, l in enumerate(lines)
                    if re.match(r'^##\s+Appendix', l)), len(lines))

secs, caps, fnd = [], [], []
for i, l in enumerate(lines):
    # NOTE: three anchoring traps here, each of which produced a wrong answer
    # before being caught. `(?:\.\d+)?\.(?:\s|$)` silently failed to match a
    # heading at end-of-line -- `$` inside an alternation does not behave as an
    # end anchor in Python -- reducing the section list to the nine top-level
    # headings. `(\d+(?:\.\d+)*)\.` captures only "5" from "### 5.1 ...", because
    # `*` allows zero repetitions and the dot then matches the decimal point.
    # And requiring the trailing period drops the top-level headings, which
    # write "## 5. Results" with a period but were matched by a different branch.
    # Matching both forms explicitly is what finally worked.
    m = re.match(r'^#{2,3}\s+(\d+(?:\.\d+)*)\.?\s', l)
    if m:
        secs.append(m.group(1))
    m = re.match(r'^\*\*Table (\S+?)\.\*\*', l)
    if m:
        caps.append((i, m.group(1), i >= appendix_at))
    m = re.match(r'^\*\*Finding (\d+[a-z]?)\.', l)
    if m:
        fnd.append(m.group(1))

refs = re.findall(r'\u00a7(\d+(?:\.\d+)?)', s)
bad_refs = sorted(set(r for r in refs if r not in secs),
                  key=lambda x: [int(p) for p in x.split('.')])

print('sections defined  : %s' % ' '.join(secs))
print('DANGLING sections : %s' % (bad_refs if bad_refs else 'none'))

body = [n for _, n, is_app in caps if not is_app and re.fullmatch(r'\d+[a-z]?', n)]
app = [n for _, n, is_app in caps if is_app]
print()
print('body tables       : %s' % ' '.join(n for _, n, a in caps if not a))
print('appendix tables   : %s' % (' '.join(app) if app else '(none)'))


def sort_key(n):
    """Order '15b' after '15' but before '16'."""
    m = re.fullmatch(r'(\d+)([a-z]?)', n)
    return (int(m.group(1)) if m else 0, m.group(2) if m else '')


dupes = sorted(set(n for n in body if body.count(n) > 1), key=sort_key)
print('DUPLICATE body    : %s' % (dupes if dupes else 'none'))
print('body in order     : %s' % ('yes' if body == sorted(body, key=sort_key)
                                  else 'NO -> ' + ' '.join(body)))

known = set(body) | set(app)
intext = set(re.findall(r'[Tt]able (\d+[a-z]?)\b', s))
dangling = sorted([x for x in intext if x not in known],
                  key=lambda x: (int(re.sub(r'\D', '', x) or 0), x))
print('DANGLING table refs: %s' % (dangling if dangling else 'none'))

print()
print('findings in order : %s' % ' '.join(fnd))
dupf = sorted(set(n for n in fnd if fnd.count(n) > 1))
print('DUPLICATE findings: %s' % (dupf if dupf else 'none'))

print()
print('paragraphs: %d  body tables: %d  findings: %d  placeholders: %d'
      % (len([l for l in lines if l.strip()]), len(body), len(fnd),
         s.count('[FILL')))

ok = (not bad_refs and not dupes and not dangling and not dupf
      and body == sorted(body, key=sort_key))
print()
print('RESULT: %s' % ('all cross-references valid' if ok else 'PROBLEMS FOUND'))
