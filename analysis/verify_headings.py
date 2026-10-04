"""Verify that each renamed Results subsection heading matches what its section contains.

I already mislabeled these once (mapping "composition statistics" onto the R2-constraint
section), so the headings are now checked against the text rather than against my memory of
the order. For each subsection this prints the heading, the size, and the key terms that
actually occur in it -- the words that would have to be there for the heading to be honest.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

# term -> must be present for the heading to be defensible
EXPECT = {
    1: ['R1', 'R2', 'orthogonal', 'composition', 'stance'],
    2: ['positive control', 'corpus size', 'responsive', 'working instrument'],
    3: ['inert', 'equivalence', 'poison@k', 'headroom'],
    4: ['BBQ', 'injection rate', 'natural'],
    5: ['shift', 'gap', 'per-group', 'generator'],
    6: ['encoder', 'scale', 'GTE', 'E5', 'checkpoint'],
    7: ['generation', 'forced-choice', 'commitment'],
    8: ['adaptive', 'back-end', 'static', 'collapse'],
}


def main():
    s = io.open(MD, encoding='utf-8').read()
    marks = [(m.start(), m.group(0)) for m in re.finditer(r'^### 5\.\d.*$', s, re.M)]
    marks.append((s.find('\n## 6. '), 'EOF'))
    for idx, ((i, head), (j, _)) in enumerate(zip(marks, marks[1:]), start=1):
        body = s[i:j]
        low = body.lower()
        want = EXPECT.get(idx, [])
        missing = [w for w in want if w.lower() not in low]
        verdict = 'OK' if not missing else 'MISSING %s' % missing
        print('%s' % head[:78])
        print('    %5d chars   %s' % (len(body), verdict))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
