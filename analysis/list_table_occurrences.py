"""Show every "Table N" occurrence so the renumbering can be reasoned about exactly.

The previous two attempts aborted on a citation-count mismatch, and the reason is that a caption
("Table 5. ...") matches the same pattern as a citation ("see Table 5"). Rather than guess at the
distinction, this prints every occurrence with enough context to classify it, so the renumbering
rule can be checked against the actual text instead of against an assumption about it.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')


def main():
    for path, style in ((MD, 'md'), (TEX, 'tex')):
        s = io.open(path, encoding='utf-8').read()
        print('=' * 74)
        print(os.path.basename(path))
        print('=' * 74)
        caps = 0
        cites = 0
        for m in re.finditer(r'Table\s?([A-Z]?\d+)', s):
            tail = s[m.end():m.end() + 2]
            lead = s[max(0, m.start() - 46):m.start()].replace('\n', ' ')
            is_cap = tail.startswith('.') or tail.startswith('\\')
            if is_cap:
                caps += 1
            else:
                cites += 1
            kind = 'CAPTION' if is_cap else 'cite   '
            print('  %s Table %-4s ...%s' % (kind, m.group(1), ' '.join(lead.split())[-44:]))
        print()
        print('  captions: %d   in-text citations: %d' % (caps, cites))
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
