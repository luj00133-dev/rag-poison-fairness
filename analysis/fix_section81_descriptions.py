"""Correct two descriptions in section 8.1 that the verification falsified.

verify_section81_numbers.py re-derived every figure in the new subsection from the raw per-query
files. Two descriptions did not survive:

  * BM25 projected was called "monotone in the relocated fraction, from 0.000 to 0.195". The
    measured maximum is 0.2280 (at full relocation) and the series is not monotone -- share 0.8
    reads 0.0000 while shares 0.4 and 0.6 read 0.0667 and 0.2000.
  * SPLADE projected was called "monotone". Measured: 0.0000, 0.2000, 0.4000, 0.2000, 0.2250 --
    it peaks in the middle and falls back.

Both are replaced with what the numbers show. The point the table is making does not depend on
monotonicity, so the fix is to describe the values rather than to defend a trend that is not
there.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

FIXES = [
    ('| BM25 | lexical, projected | monotone in the relocated fraction, from 0.000 to 0.195 |',
     '| BM25 | lexical, projected | 0.0000 at low relocation, rising to 0.2280 at full relocation |'),
    ('| SPLADE | lexical, projected | monotone in the relocated fraction |',
     '| SPLADE | lexical, projected | 0.0000 at zero relocation, 0.2000-0.4000 through the middle, '
     '0.2250 at full relocation |'),
    ('On the other back-ends the retrieved set relocates composition as well, and the aggregate '
     'moves with it.',
     'On the other back-ends the retrieved set relocates composition as well, and the aggregate '
     'moves with it, reaching 0.1750 on dense and 0.2 or above on the projected lexical '
     'back-ends; the dependence is not strictly monotone in the relocated fraction, which is '
     'itself a reason to check the regime rather than assume it.'),
]


def main():
    s = io.open(MD, encoding='utf-8').read()
    for old, new in FIXES:
        n = s.count(old)
        print('%-58s %d match(es)' % (old[:58], n))
        if n == 1:
            s = s.replace(old, new, 1)
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)

    s2 = io.open(MD, encoding='utf-8').read()
    print()
    print('stale "0.195" gone        : %s' % ('0.195' not in s2))
    print('stale "monotone" gone     : %s' % ('monotone in the relocated fraction' not in s2))
    print('0.2280 present            : %s' % ('0.2280' in s2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
