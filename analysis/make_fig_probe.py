"""Redraw the probe figure as vector, in the house style.

Replaces fig_probe_commitment.png, a ChatGPT-generated 2,085 KB bitmap. Contract from
analysis/figure_contract.md: the figure is a before/after on identical retrieval conditions, and
THE CONTRAST IS THE POINT -- neither panel carries it alone. So the two panels are drawn as mirror
images of each other, sharing one baseline and one axis, and the caption states the contrast rather
than describing each panel separately.

What the panels must show:
    left   a free-form probe, where answers take no position at all, so the statistic reads near
           zero under every condition and no effect of any size could have appeared in it;
    right  a forced-choice probe on the same retrieval conditions, where answers commit, and an
           effect appears.

The claim is about the INSTRUMENT, not the corpus: the same conditions produced nothing under one
probe and something under the other. No measured value is drawn; the caption points at the table
holding the commitment values.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figure_style import Canvas, C                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(os.path.dirname(HERE), 'paper', 'figures')

L = dict(x=0.012, y=0.070, w=0.472, h=0.900)
R = dict(x=0.516, y=0.070, w=0.472, h=0.900)


def panel(cv, g, tag, title, sub):
    cv.card(g)
    cv.text(g['x'] + 0.022, g['y'] + g['h'] - 0.035, tag, g, tag='%s.tag' % tag,
            fontsize=7.6, fontweight='bold', color=C['rule'], ha='left', va='top')
    cv.text(g['x'] + 0.078, g['y'] + g['h'] - 0.038, title, g, tag='%s.t' % tag,
            fontsize=6.2, fontweight='bold', color=C['ink'], ha='left', va='top')
    cv.text(g['x'] + 0.022, g['y'] + g['h'] - 0.098, sub, g, tag='%s.s' % tag,
            fontsize=5.2, color=C['rule'], ha='left', va='top')


def freeform(cv, g):
    """Left: four answer glyphs, none of which takes a position."""
    y = g['y'] + 0.430
    cv.text(g['x'] + 0.022, y + 0.150, 'answers take no position', g, tag='L.a',
            fontsize=5.2, color=C['rule'], ha='left', va='bottom')
    for i in range(4):
        cv.rect(g['x'] + 0.030 + i * 0.102, y, 0.078, 0.098,
                C['rule'], C['lgrey'], z=4)
        cv.text(g['x'] + 0.069 + i * 0.102, y + 0.049, '\u2014', g,
                tag='L.dash%d' % i, fontsize=7.0, color=C['grey'],
                ha='center', va='center')
    # the readout: flat at zero under every condition
    y0 = g['y'] + 0.180
    cv.rect(g['x'] + 0.070, y0, 0.330, 0.130, C['rule'], 'white', lw=0.5, z=2)
    cv.ax.plot([g['x'] + 0.080, g['x'] + 0.390], [y0 + 0.014, y0 + 0.014],
               color=C['grey'], linewidth=1.1, zorder=5,
               transform=cv.ax.transAxes, clip_on=False)
    cv.text(g['x'] + 0.235, y0 + 0.150, 'statistic reads near zero', g, tag='L.r',
            fontsize=5.1, color=C['rule'], ha='center', va='bottom')
    cv.text(g['x'] + 0.235, y0 - 0.020, 'clean        attacked', g, tag='L.x',
            fontsize=5.0, color=C['rule'], ha='center', va='top')
    cv.text(g['x'] + 0.022, g['y'] + 0.075,
            'no effect of any size could have appeared', g, tag='L.v',
            fontsize=5.6, color=C['rule'], fontweight='bold', ha='left', va='bottom')


def forced(cv, g):
    """Right: the same answers made to commit, and the effect appears."""
    y = g['y'] + 0.430
    cv.text(g['x'] + 0.022, y + 0.150, 'answers commit to a side', g, tag='R.a',
            fontsize=5.2, color=C['rule'], ha='left', va='bottom')
    # committed answers are drawn as a filled side-bar plus a short arrow, not as
    # triangle glyphs: Arial has no U+25C0/U+25B6 and matplotlib would silently drop them
    for i, col in enumerate((C['accent'], C['blue'], C['blue'], C['accent'])):
        bx = g['x'] + 0.030 + i * 0.102
        cv.rect(bx, y, 0.078, 0.098, col, 'white', z=4)
        cv.rect(bx, y, 0.020, 0.098, col, col, z=5)
        cv.text(bx + 0.040, y + 0.058, 'fav', g, tag='R.fav%d' % i, fontsize=4.8,
                color=col, ha='center', va='center')
        cv.text(bx + 0.040, y + 0.030, 'A' if i % 2 == 0 else 'B', g,
                tag='R.g%d' % i, fontsize=4.8, color=col, ha='center', va='center')
    # the readout: two conditions separated
    y0 = g['y'] + 0.180
    cv.rect(g['x'] + 0.070, y0, 0.330, 0.130, C['rule'], 'white', lw=0.5, z=2)
    cv.rect(g['x'] + 0.100, y0 + 0.014, 0.070, 0.070, C['grey'], C['grey'], z=4)
    cv.rect(g['x'] + 0.280, y0 + 0.014, 0.070, 0.108, C['accent'], C['accent'], z=4)
    cv.text(g['x'] + 0.135, y0 - 0.006, 'clean', g, tag='R.c', fontsize=5.0,
            color=C['rule'], ha='center', va='top')
    cv.text(g['x'] + 0.315, y0 - 0.006, 'attacked', g, tag='R.k', fontsize=5.0,
            color=C['accent'], ha='center', va='top')
    cv.text(g['x'] + 0.235, y0 + 0.150, 'the effect appears', g, tag='R.r',
            fontsize=5.1, color=C['accent'], ha='center', va='bottom')
    cv.text(g['x'] + 0.022, g['y'] + 0.075,
            'same retrieval conditions as the left panel', g, tag='R.v',
            fontsize=5.6, color=C['accent'], fontweight='bold', ha='left', va='bottom')


def main():
    cv = Canvas(140, 52)
    panel(cv, L, 'A', 'free-form probe', 'the statistic an earlier analysis used')
    panel(cv, R, 'B', 'forced-choice probe', 'identical retrieval conditions')
    freeform(cv, L)
    forced(cv, R)
    ok = cv.save(os.path.join(FIGS, 'fig_probe_commitment_py'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
