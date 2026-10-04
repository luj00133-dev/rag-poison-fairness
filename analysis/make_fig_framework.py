"""Framework figure, third attempt: text width is measured, not assumed.

Two attempts produced three collisions, all with one cause: captions were placed at fixed offsets
without checking how wide they would be, so a 52-character subtitle ran past its card and a
left-column caption crashed into the right column's heading. The TikZ version of this figure
carries the same warning in its header, and it is the defect that survived into that figure's
first PDF too.

So the layout is now checked rather than eyeballed. Every text block is registered as it is
placed, and before saving the figure each block's rendered bounding box is compared against the
card it belongs to; a block that leaves its card, or overlaps a previously placed block, is
reported and the drawing fails instead of shipping the defect. That check is the part worth
keeping -- the coordinates are disposable, the guard is not.
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(os.path.dirname(HERE), 'paper', 'figures')
MM = 1 / 25.4

C = {
    'ink': '#1a1a1a', 'rule': '#5f5f5f', 'grey': '#8c8c8c',
    'fill': '#e9e9e9', 'blue': '#0072B2', 'accent': '#B23C34', 'fillaccent': '#ECD1CE',
}

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 6,
    'pdf.fonttype': 42,
    'svg.fonttype': 'none',
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.012,
})

PLACED = []          # (label, bbox_in_axes_coords)


def place(fig, ax, x, y, s, card_box=None, tag='', **kw):
    """Draw text and record its measured extent so overlaps can be detected."""
    kw.setdefault('zorder', 6)
    t = ax.text(x, y, s, transform=ax.transAxes, **kw)
    fig.canvas.draw()
    bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
    inv = ax.transAxes.inverted()
    (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
    PLACED.append((tag or s[:24], (x0, y0, x1, y1), card_box))
    return t


def audit():
    """Report text outside its card, or text overlapping text."""
    problems = []
    for name, bb, cardb in PLACED:
        if cardb:
            cx, cy, cw, ch = cardb['x'], cardb['y'], cardb['w'], cardb['h']
            if bb[0] < cx - 0.002 or bb[2] > cx + cw + 0.002 \
               or bb[1] < cy - 0.002 or bb[3] > cy + ch + 0.002:
                problems.append('OUTSIDE CARD: %-28s text=(%.3f,%.3f,%.3f,%.3f) '
                                'card=(%.3f,%.3f,%.3f,%.3f)'
                                % (name, bb[0], bb[1], bb[2], bb[3], cx, cy, cw, ch))
    for i in range(len(PLACED)):
        for j in range(i + 1, len(PLACED)):
            a, b = PLACED[i][1], PLACED[j][1]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 0.004 and oy > 0.004:
                problems.append('OVERLAP: %-24s <-> %-24s (%.3f x %.3f)'
                                % (PLACED[i][0], PLACED[j][0], ox, oy))
    return problems


A = dict(x=0.014, y=0.560, w=0.440, h=0.428)
B = dict(x=0.548, y=0.560, w=0.440, h=0.428)
Cc = dict(x=0.014, y=0.028, w=0.974, h=0.470)


def card(ax, g, label, accent=False):
    ax.add_patch(FancyBboxPatch(
        (g['x'], g['y']), g['w'], g['h'],
        boxstyle='round,pad=0,rounding_size=0.006', linewidth=0.9,
        edgecolor=(C['accent'] if accent else C['ink']), facecolor='white',
        zorder=1, transform=ax.transAxes))


def glyphrow(ax, x, y, n, pitch, w, accent=(), h=0.058):
    for i in range(n):
        acc = i in accent
        ax.add_patch(Rectangle(
            (x + i * pitch, y), w, h, linewidth=0.5,
            edgecolor=(C['accent'] if acc else C['rule']),
            facecolor=(C['fillaccent'] if acc else C['fill']),
            zorder=3, transform=ax.transAxes))


def main():
    fig = plt.figure(figsize=(88 * MM, 60 * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()

    # ------------------------------------------------------------------ panel A
    card(ax, A, 'A')
    place(fig, ax, A['x'] + 0.018, A['y'] + A['h'] - 0.022, 'A   Retrieval',
          A, tag='A.head', fontsize=6.4, fontweight='bold', color=C['ink'],
          ha='left', va='top')
    place(fig, ax, A['x'] + 0.018, A['y'] + A['h'] - 0.075, 'group-neutral query',
          A, tag='A.q', fontsize=5.2, color=C['rule'], ha='left', va='top')
    ax.add_patch(FancyBboxPatch(
        (A['x'] + 0.018, A['y'] + A['h'] - 0.158), 0.290, 0.048,
        boxstyle='round,pad=0,rounding_size=0.004', linewidth=0.5,
        edgecolor=C['rule'], facecolor='white', zorder=3, transform=ax.transAxes))
    place(fig, ax, A['x'] + 0.028, A['y'] + A['h'] - 0.134, 'Who performed better?',
          A, tag='A.qbox', fontsize=5.4, color=C['ink'], ha='left', va='center')
    ax.add_patch(FancyArrowPatch(
        (A['x'] + 0.062, A['y'] + A['h'] - 0.158), (A['x'] + 0.062, A['y'] + A['h'] - 0.200),
        arrowstyle='-|>', mutation_scale=5, linewidth=0.6, color=C['ink'],
        shrinkA=0, shrinkB=0, zorder=4, transform=ax.transAxes))
    place(fig, ax, A['x'] + 0.018, A['y'] + A['h'] - 0.212, 'top-$k$ retrieved set',
          A, tag='A.topk', fontsize=5.2, color=C['rule'], ha='left', va='top')
    glyphrow(ax, A['x'] + 0.018, A['y'] + 0.075, 5, 0.060, 0.050)
    place(fig, ax, A['x'] + 0.018, A['y'] + 0.048, 'any skew comes from the corpus',
          A, tag='A.note', fontsize=5.2, color=C['rule'], ha='left', va='top')

    # ------------------------------------------------------------------ panel B
    card(ax, B, 'B')
    place(fig, ax, B['x'] + 0.018, B['y'] + B['h'] - 0.022, 'B   Injection',
          B, tag='B.head', fontsize=6.4, fontweight='bold', color=C['ink'],
          ha='left', va='top')
    place(fig, ax, B['x'] + 0.018, B['y'] + B['h'] - 0.082, 'matched pairs from the inventory',
          B, tag='B.sub', fontsize=5.2, color=C['rule'], ha='left', va='top')
    glyphrow(ax, B['x'] + 0.018, B['y'] + B['h'] - 0.180, 6, 0.062, 0.052,
             accent=(0, 2, 4))
    place(fig, ax, B['x'] + 0.018, B['y'] + B['h'] - 0.216, 'favours A',
          B, tag='B.fa', fontsize=5.2, color=C['accent'], ha='left', va='top')
    place(fig, ax, B['x'] + 0.250, B['y'] + B['h'] - 0.216, 'disfavours B',
          B, tag='B.fb', fontsize=5.2, color=C['accent'], ha='left', va='top')
    place(fig, ax, B['x'] + 0.018, B['y'] + 0.080,
          'balanced across groups,\nindistinguishable from clean text',
          B, tag='B.note', fontsize=5.2, color=C['rule'], ha='left', va='top',
          linespacing=1.35)

    # ------------------------------------------------------------------ panel C (hero)
    card(ax, Cc, 'C', accent=True)
    place(fig, ax, Cc['x'] + 0.018, Cc['y'] + Cc['h'] - 0.022,
          'C   What a statistic then sees   \u2014   same attacked set',
          Cc, tag='C.head', fontsize=6.6, fontweight='bold', color=C['accent'],
          ha='left', va='top')
    place(fig, ax, Cc['x'] + 0.018, Cc['y'] + Cc['h'] - 0.078,
          'the attack moves one dimension and leaves the other at its clean value',
          Cc, tag='C.sub', fontsize=5.2, color=C['rule'], ha='left', va='top')

    # left column: R1
    ytop = Cc['y'] + 0.250
    place(fig, ax, Cc['x'] + 0.018, ytop + 0.048, 'R1   group composition',
          Cc, tag='C.r1h', fontsize=5.8, color=C['ink'], ha='left', va='bottom')
    glyphrow(ax, Cc['x'] + 0.018, ytop, 2, 0.056, 0.046, h=0.052)
    place(fig, ax, Cc['x'] + 0.145, ytop + 0.026, 'unchanged',
          Cc, tag='C.r1v', fontsize=5.8, color=C['blue'], fontweight='bold',
          ha='left', va='center')
    place(fig, ax, Cc['x'] + 0.018, ytop - 0.024,
          'the count is balanced,\nso a composition statistic reads clean',
          Cc, tag='C.r1n', fontsize=5.2, color=C['rule'], ha='left', va='top',
          linespacing=1.35)

    # right column: R2
    ybot = Cc['y'] + 0.110
    x0, x1 = Cc['x'] + 0.520, Cc['x'] + 0.700
    place(fig, ax, x0, ybot + 0.092, 'R2   within-group stance',
          Cc, tag='C.r2h', fontsize=5.8, color=C['accent'], ha='left', va='bottom')
    place(fig, ax, x0, ybot + 0.058, 'clean', Cc, tag='C.c1', fontsize=5.2,
          color=C['rule'], ha='left', va='bottom')
    place(fig, ax, x1, ybot + 0.058, 'attacked', Cc, tag='C.c2', fontsize=5.2,
          color=C['accent'], ha='left', va='bottom')
    for dy, lab in ((0.024, 'A'), (-0.006, 'B')):
        ax.add_patch(Rectangle((x0, ybot + dy), 0.048, 0.024, linewidth=0.5,
                               edgecolor=C['grey'], facecolor=C['grey'], zorder=3,
                               transform=ax.transAxes))
        place(fig, ax, x0 + 0.054, ybot + dy + 0.012, lab, Cc, tag='C.lab%s' % lab,
              fontsize=5.2, color=C['rule'], ha='left', va='center')
    for dy, w, lab in ((0.024, 0.014, 'A down'), (-0.006, 0.080, 'B up')):
        ax.add_patch(Rectangle((x1, ybot + dy), w, 0.024, linewidth=0.5,
                               edgecolor=C['accent'], facecolor=C['accent'], zorder=3,
                               transform=ax.transAxes))
        place(fig, ax, x1 + 0.086, ybot + dy + 0.012, lab, Cc,
              tag='C.d%s' % lab[:1], fontsize=5.2, color=C['accent'],
              ha='left', va='center')
    place(fig, ax, x0, ybot - 0.006,
          'the stance is relocated,\nso a difference between groups cancels',
          Cc, tag='C.r2n', fontsize=5.2, color=C['rule'], ha='left', va='top',
          linespacing=1.35)

    problems = audit()
    print('layout audit: %d problem(s)' % len(problems))
    for p in problems:
        print('   ' + p)
    if problems:
        print('NOT SAVED: fix the layout rather than shipping the defect')
        plt.close(fig)
        return 1

    for ext in ('pdf', 'png'):
        out = os.path.join(FIGS, 'fig_framework_py.' + ext)
        fig.savefig(out, dpi=600 if ext == 'png' else None)
        print('wrote %s' % out)
    plt.close(fig)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
