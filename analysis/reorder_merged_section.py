"""Move the merged section 5.8 to after section 5.7, and fix the references to it.

The merge script inserted the new material before section 5.7 "Generation-stage
propagation" because that anchor was convenient, which left the results sections out of
order (5.1 ... 5.6, 5.8, 5.7). This moves the block to the end of the results sections,
where it belongs -- it is retrieval-layer material like 5.1-5.6, and the generation-stage
section stays last.

It also updates the two places that refer to the protocol by number, since the protocol
subsection sits inside the moved block.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

START = '### 5.8 The collapse is not an artefact of one retriever'
NEXT = '### 5.7 Generation-stage propagation'


def main():
    s = io.open(MD, encoding='utf-8').read()
    i = s.find(START)
    j = s.find(NEXT)
    if i < 0 or j < 0:
        print('ANCHOR FAIL i=%d j=%d' % (i, j))
        return 1
    if i > j:
        print('already in order (5.8 follows 5.7)')
        return 0
    # block runs from START to the line before the next "### " heading after it
    nxt = re.search(r'^### (?!5\.8)', s[i + 4:], re.M)
    end = i + 4 + (nxt.start() if nxt else len(s) - i - 4)
    block = s[i:end]
    s = s[:i] + s[end:]                      # remove it
    # re-find 5.7 now that the block is gone, and insert after its section (before "## 6.")
    k = s.find(NEXT)
    sec6 = s.find('\n## 6. ', k)
    if sec6 < 0:
        print('SECTION 6 ANCHOR FAIL')
        return 1
    s = s[:sec6 + 1] + block + s[sec6 + 1:]

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)

    # verify order
    order = [(m.start(), m.group(0).strip()) for m in re.finditer(r'^### 5\.\d.*$', s, re.M)]
    print('order of section 5 subsections:')
    for _, t in order:
        print('   %s' % t[:64])
    proto = s.find('#### 5.8.1')
    print()
    print('protocol subsection present: %s' % (proto > 0))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
