"""Give the graded injection an explicit strength profile so the label spans 0..5.

The probe (analysis/probe_align_strength2.py) established that the alignment gradient makes
partial contamination reachable -- at align_strength 0.15 the retrieved poison count becomes
{0:132, 1:36, 2:24}, i.e. three levels where the original construction gave two. But the
schedule is fractions 1/6..6/6 scaled by strength, so at low strength even the strongest
passage is only moderately aligned, and the count never exceeds 2 of 5. A graded label wants
the whole range: some passages that clearly win, some that clearly lose, and some on the
boundary, so that different queries land on different counts.

This adds align_min_frac (default 1/n_poison, the original spacing) so the profile can run
from a weak floor to full strength. Defaults leave every existing configuration untouched.
"""
import io
import os
import py_compile

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(P, 'src', 'attacks', 'poisoning.py')

SPEC_OLD = '''    #: Scale on the alignment vocabulary when align_graded is set. 1.0 spreads passages
    #: across the full ALIGN string; smaller values compress them toward the weak end.
    align_strength: float = 1.0'''
SPEC_NEW = '''    #: Scale on the alignment vocabulary when align_graded is set. 1.0 spreads passages
    #: across the full ALIGN string; smaller values compress them toward the weak end.
    align_strength: float = 1.0
    #: Weakest fraction of the alignment vocabulary, as a share of align_strength. The
    #: default reproduces even spacing across the passage set (1/n, 2/n, ... 1). Lowering it
    #: pushes the weakest passages below clean evidence so that some queries retrieve few or
    #: no adversarial passages, widening the range of the graded label.
    align_min_frac: float = 0.0'''

HELPER_OLD = '''        if n <= 1:
            frac = 1.0
        else:
            # spread idx across (0, 1]: weakest first, strongest last
            frac = (idx + 1) / float(n)
        frac *= max(0.0, min(1.0, float(spec.align_strength)))'''
HELPER_NEW = '''        if n <= 1:
            frac = 1.0
        else:
            # spread idx across [floor, 1]: weakest first, strongest last
            lo = float(spec.align_min_frac) if spec.align_min_frac > 0 else 1.0 / n
            lo = max(0.0, min(1.0, lo))
            frac = lo + (1.0 - lo) * (idx / float(n - 1))
        frac *= max(0.0, min(1.0, float(spec.align_strength)))'''


def main():
    s = io.open(SRC, encoding='utf-8').read()
    for old, new, label in ((SPEC_OLD, SPEC_NEW, 'align_min_frac field'),
                            (HELPER_OLD, HELPER_NEW, 'schedule')):
        n = s.count(old)
        print('%-22s %d match(es)' % (label, n))
        if n != 1:
            print('  ABORT')
            return 1
        s = s.replace(old, new, 1)
    io.open(SRC, 'w', encoding='utf-8', newline='\n').write(s)
    py_compile.compile(SRC, doraise=True)
    print('compiles: True')

    s2 = io.open(SRC, encoding='utf-8').read()
    print('default align_min_frac 0.0 keeps 1/n spacing: %s'
          % ('if spec.align_min_frac > 0 else 1.0 / n' in s2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
