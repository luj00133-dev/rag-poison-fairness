"""Fix the porting script: the regex was catastrophically backtracking, not the compile.

The pattern `Every statistic that aggregates over group composition is blind to this\\.(?:\\s+[^\\n]*)*?returns success\\.`
nests a quantified group containing a quantified class, which backtracks exponentially on a
long single line. It burned minutes of CPU without producing a match. Replaced with plain string
search, which is what the task needed in the first place.

This also records the lesson: the earlier apparent hang was mine, not the document's. The compile
itself is fine -- the stale report was from the previous successful run.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

START = 'Every statistic that aggregates over group composition is blind to this.'
END = 'returns success.'
NEW = ('Every candidate metric has that form; whether it reads clean depends on whether the '
       'injection balances the terms it aggregates. That is a property of the back-end rather '
       'than of the metric, and section 5.9 measures it across four of them.')


def main():
    s = io.open(TEX, encoding='utf-8').read()
    i = s.find(START)
    if i < 0:
        print('claim not found (already corrected?)')
    else:
        j = s.find(END, i)
        if j < 0:
            print('end marker not found after start; aborting without writing')
            return 1
        j += len(END)
        s = s[:i] + NEW + s[j:]
        io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
        print('corrected the universal blindness claim in the tex')

    s2 = io.open(TEX, encoding='utf-8').read()
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in s2:
            print('FAIL: missing %s' % needed)
            return 1
    print('structure intact')
    print('universal claim gone : %s'
          % ('Every statistic that aggregates over group composition is blind' not in s2))
    print('5.9 present          : %s' % ('property of the back-end}' in s2))
    print('8.1 renamed          : %s' % ('When the aggregate is informative}' in s2))
    print('3.4 renamed          : %s' % ('invariances an adversary can impose}' in s2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
