"""Final checks after restoring section 8's protocol list.

Confirms the list is inside section 8, has nine enumerated items, that the conclusion's
cross-reference now resolves to a section that actually holds a protocol, and that the
Highlights claims still hold.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')
ITEM = chr(92) + 'item'          # avoid any escaping ambiguity


def main():
    s = io.open(TEX, encoding='utf-8').read()
    d = s.find('\\section{Discussion and Limitations}')
    c = s.find('\\section{Conclusion}')
    p = s.find('We close with the protocol the results imply')
    print('section 8 at %d, protocol at %d, conclusion at %d' % (d, p, c))
    print('protocol inside section 8 : %s' % (d < p < c))

    block = s[p:c]
    print('enumerated items in it    : %d' % len(re.findall(re.escape(ITEM) + r'\b', block)))
    print('has \\begin{enumerate}     : %s' % ('\\begin{enumerate}' in block))
    print('has \\end{enumerate}       : %s' % ('\\end{enumerate}' in block))

    print()
    print('--- cross-reference resolution ---')
    print('conclusion points at      : %s'
          % ('§8 and §5.8.1' if 'set out in §8 and §5.8.1' in s else 'CHECK'))
    # §8 now contains the nine-item list, so the pointer resolves
    print('§8 holds a protocol list  : %s' % (len(re.findall(re.escape(ITEM) + r'\b', block)) == 9))
    p581 = s.find('The evaluation protocol these results imply')
    end581 = s.find('\\end{enumerate}', p581)
    print('§5.8.1 holds %d items     : %s'
          % (len(re.findall(re.escape(ITEM) + r'\b', s[p581:end581])),
             len(re.findall(re.escape(ITEM) + r'\b', s[p581:end581])) == 6))

    print()
    print('--- the three protocol statements ---')
    for label, needle in (('abstract (summary)', 'per-group shifts rather than cross-group '
                           'differences, adversarial inclusion as a function'),
                          ('§5.8.1 (adversarial-eval rules)', 'Sweep to the point of failure'),
                          ('§8 (complete list)', 'Measure per-group shifts')):
        print('  %-34s %s' % (label, 'present' if needle in s else 'ABSENT'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
