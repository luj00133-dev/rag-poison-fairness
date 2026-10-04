"""Print the six protocol items in 5.8.1 and find the dangling section pointer.

The conclusion says the reporting requirements are "set out in §8", but section 8's list was
removed by my own conclusion replacement; the protocol now lives in §5.8.1. That is a
dangling cross-reference and has to be fixed, together with anything else that points at a
protocol section which no longer holds one.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')
ITEM = '\\' + 'item'


def main():
    s = io.open(TEX, encoding='utf-8').read()

    i = s.find('The evaluation protocol these results imply')
    j = s.find('\\end{enumerate}', i)
    seg = s[i:j]
    print('--- 5.8.1 protocol items (%d chars) ---' % len(seg))
    for m in re.finditer(re.escape(ITEM) + r'\s*\n?\s*\\textbf\{([^}]*)\}', seg):
        print('   * %s' % m.group(1)[:100])
    print('   item count: %d' % len(re.findall(re.escape(ITEM) + r'\b', seg)))

    print()
    print('--- references to a protocol section anywhere in the tex ---')
    for m in re.finditer(r'.{70}(?:set out in|protocol in|the protocol the results imply).{50}', s, re.S):
        print('   ...%s...' % ' '.join(m.group(0).split()))

    print()
    print('--- which sections still contain a list of reporting rules? ---')
    for marker, label in ((r'\section{Discussion and Limitations}', 'section 8'),
                          (r'The evaluation protocol these results imply', '5.8.1')):
        k = s.find(marker)
        if k < 0:
            print('   %-10s marker absent' % label)
            continue
        window = s[k:k + 14000]
        end = window.find('\\end{enumerate}')
        n = len(re.findall(re.escape(ITEM) + r'\b', window[:end])) if end > 0 else 0
        print('   %-10s enumerate items: %d' % (label, n))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
