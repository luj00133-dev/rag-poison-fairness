"""Apply the third section 8.1 correction, which the previous script missed.

The markdown source wraps lines, so the sentence spans a newline and the single-line pattern did
not match. The correction adds the measured magnitudes and the non-monotonicity, which the first
two fixes already reflected in the table rows.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

OLD = ('On the other back-ends the retrieved set relocates composition as well, and the\n'
       'aggregate moves with it.')
NEW = ('On the other back-ends the retrieved set relocates composition as well, and the\n'
       'aggregate moves with it, reaching 0.1750 on dense and 0.2 or above on the projected\n'
       'lexical back-ends. The dependence is not strictly monotone in the relocated fraction,\n'
       'which is itself a reason to measure the regime rather than assume it.')


def main():
    s = io.open(MD, encoding='utf-8').read()
    n = s.count(OLD)
    print('anchor matches: %d' % n)
    if n != 1:
        print('ABORT')
        return 1
    s = s.replace(OLD, NEW, 1)
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    s2 = io.open(MD, encoding='utf-8').read()
    print('magnitudes present     : %s' % ('reaching 0.1750 on dense' in s2))
    print('non-monotone note      : %s' % ('not strictly monotone' in s2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
