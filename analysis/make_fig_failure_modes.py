"""Redraw the failure-modes figure (F1/F2/F3) as vector, in the house style.

Replaces the bitmap composite fig_failure_modes.pdf, which was assembled from ChatGPT-generated
PNGs and therefore carries a different palette, typeface and resolution from the four data figures.

Contract, from analysis/figure_contract.md: three panels of deliberately EQUAL weight, because F1,
F2 and F3 are alternative mechanisms rather than stages of one process. Giving any of them a hero
panel would present them as a sequence, which is the opposite of what the paper claims -- the point
is that three independent single-cause constructions each suffice.

What each panel must show is not "a small number" but WHY the number is small, since that is the
mechanism:
    F1  the statistic counts a quantity the injection keeps equal, so the count is clean;
    F2  the statistic is anchored to a reference the attack does not move, so it reports the
        query-varying component instead of the attack-varying one;
    F3  every group moves together, so a difference between groups is unchanged.

No measured value appears; the caption says the panels are conceptual and names the sections
holding the measurements.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figure_style import Canvas, C                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(os.path.dirname(HERE), 'paper', 'figures')

P = [
    dict(x=0.010, y=0.055, w=0.320, h=0.925),
    dict(x=0.340, y=0.055, w=0.320, h=0.925),
    dict(x=0.670, y=0.055, w=0.320, h=0.925),
]


def head(cv, g, code, title):
    cv.text(g['x'] + 0.020, g['y'] + g['h'] - 0.030, code, g, tag='%s.code' % code,
            fontsize=8.0, fontweight='bold', color=C['accent'], ha='left', va='top')
    cv.text(g['x'] + 0.072, g['y'] + g['h'] - 0.032, title, g, tag='%s.t' % code,
            fontsize=6.0, fontweight='bold', color=C['ink'], ha='left', va='top')


def axis_frame(cv, g, x0, y0, w, h, ylab):
    """A small schematic plotting frame with a direct y label."""
    cv.rect(x0, y0, w, h, C['rule'], 'white', lw=0.5, z=2)
    cv.text(x0 - 0.014, y0 + h / 2, ylab, g, tag='%s.yl' % ylab[:6], fontsize=5.1,
            color=C['rule'], ha='right', va='center', rotation=90)


def f1(cv, g):
    head(cv, g, 'F1', 'balanced count')
    x0, y0, w, h = g['x'] + 0.085, g['y'] + 0.455, 0.238, 0.290
    axis_frame(cv, g, x0, y0, w, h, 'group count')
    # two clean bars and two attacked bars, all equal
    for i, (dx, col, lab) in enumerate((
            (0.020, C['grey'], 'clean'), (0.075, C['grey'], ''),
            (0.130, C['blue'], 'attacked'), (0.185, C['blue'], ''))):
        cv.rect(x0 + dx, y0 + 0.012, 0.038, 0.235, col, col, z=4)
    cv.text(x0 + 0.100, y0 - 0.016, 'A            B', g, tag='F1.xl', fontsize=5.1,
            color=C['rule'], ha='center', va='top')
    cv.text(x0 + w / 2, y0 + h + 0.020, 'the injection adds equally to both groups',
            g, tag='F1.cap', fontsize=5.0, color=C['rule'], ha='center', va='bottom')
    cv.text(g['x'] + 0.020, g['y'] + 0.400,
            'A statistic over group counts\nreturns its clean value, because the\n'
            'quantity it counts is unchanged.',
            g, tag='F1.body', fontsize=5.2, color=C['ink'], ha='left', va='top',
            linespacing=1.45)
    cv.text(g['x'] + 0.020, g['y'] + 0.090, 'aggregate reads clean', g, tag='F1.verdict',
            fontsize=5.6, color=C['blue'], fontweight='bold', ha='left', va='bottom')


def f2(cv, g):
    head(cv, g, 'F2', 'preserved nuisance')
    x0, y0, w, h = g['x'] + 0.100, g['y'] + 0.455, 0.195, 0.290
    axis_frame(cv, g, x0, y0, w, h, 'deviation')
    # the measured quantity varies WITH THE QUERY, and the reference is flat
    pts = [0.05, 0.16, 0.10, 0.24, 0.14, 0.22]
    for i, v in enumerate(pts):
        cv.rect(x0 + 0.018 + i * 0.028, y0 + 0.012, 0.016, v * 1.05,
                C['rule'], C['lgrey'], z=4)
    cv.text(x0 + 0.014, y0 + 0.300, 'reference the attack cannot move', g,
            tag='F2.ref', fontsize=5.0, color=C['orange'], ha='left', va='bottom')
    cv.ax.plot([x0 + 0.010, x0 + w - 0.010], [y0 + 0.012, y0 + 0.012],
               color=C['orange'], linewidth=1.1, zorder=5,
               transform=cv.ax.transAxes, clip_on=False)
    cv.text(x0 + w / 2, y0 - 0.020, 'queries', g, tag='F2.xl', fontsize=5.1,
            color=C['rule'], ha='center', va='top')
    cv.text(g['x'] + 0.020, g['y'] + 0.400,
            'The statistic is anchored to a reference\nthe attack does not change, so it\n'
            'reports the query-varying component\ninstead of the attack-varying one.',
            g, tag='F2.body', fontsize=5.2, color=C['ink'], ha='left', va='top',
            linespacing=1.45)
    cv.text(g['x'] + 0.020, g['y'] + 0.090, 'aggregate reads clean', g, tag='F2.verdict',
            fontsize=5.6, color=C['orange'], fontweight='bold', ha='left', va='bottom')


def f3(cv, g):
    head(cv, g, 'F3', 'cancelled shift')
    x0, y0, w, h = g['x'] + 0.090, g['y'] + 0.440, 0.222, 0.300
    axis_frame(cv, g, x0, y0, w, h, 'stance')
    # both groups relocate in the same direction: the difference is unchanged
    cv.rect(x0 + 0.030, y0 + 0.020, 0.030, 0.110, C['grey'], C['grey'], z=4)
    cv.rect(x0 + 0.080, y0 + 0.020, 0.030, 0.150, C['grey'], C['grey'], z=4)
    cv.rect(x0 + 0.135, y0 + 0.135, 0.030, 0.110, C['accent'], C['fillaccent'], z=4)
    cv.rect(x0 + 0.170, y0 + 0.135, 0.030, 0.150, C['accent'], C['fillaccent'], z=4)
    # the invariant difference, drawn as a bracket
    for (bx, yb) in ((x0 + 0.030, y0 + 0.130), (x0 + 0.135, y0 + 0.245)):
        cv.ax.plot([bx, bx + 0.080], [yb, yb], color=C['blue'], linewidth=0.9,
                   zorder=6, transform=cv.ax.transAxes, clip_on=False)
    cv.text(x0 + 0.145, y0 + h + 0.020, 'both groups move by the same amount', g,
            tag='F3.cap', fontsize=5.0, color=C['rule'], ha='center', va='bottom')
    cv.text(x0 + w / 2, y0 - 0.020, 'clean      attacked', g, tag='F3.xl', fontsize=5.1,
            color=C['rule'], ha='center', va='top')
    cv.text(g['x'] + 0.020, g['y'] + 0.380,
            'Every group is relocated together, so a\ndifference between groups is unchanged\n'
            'however far the groups move.',
            g, tag='F3.body', fontsize=5.2, color=C['ink'], ha='left', va='top',
            linespacing=1.45)
    cv.text(g['x'] + 0.020, g['y'] + 0.090, 'aggregate reads clean', g, tag='F3.verdict',
            fontsize=5.6, color=C['accent'], fontweight='bold', ha='left', va='bottom')


def main():
    cv = Canvas(190, 50)          # double-column width: three panels side by side
    for g in P:
        cv.card(g)
    f1(cv, P[0])
    f2(cv, P[1])
    f3(cv, P[2])
    ok = cv.save(os.path.join(FIGS, 'fig_failure_modes_py'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
