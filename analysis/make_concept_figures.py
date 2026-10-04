"""Draw the three concept figures in Python, in the manuscript's existing figure style.

Why this exists. The three concept figures placed in the manuscript are ChatGPT-generated
bitmaps (or a bitmap composed from them), while the four data figures are vector PDFs drawn with
the house style. The mismatch is visible in palette, in typeface and in resolution, and a bitmap
schematic cannot carry the manuscript's own notation or be edited when a symbol changes.

House style is copied from analysis/make_figures.py rather than invented, so the concept figures
sit next to the data figures without a seam:

    palette   Okabe-Ito geometric
    type      Arial, base 7 pt, axis labels 7.5, legend 6.5
    widths    88 mm single column, 140 mm wide, 190 mm double
    output    vector PDF with pdf.fonttype 42 (text stays editable) plus 600-dpi PNG

Figure 1 of 3: the framework. See analysis/figure_contract.md for the contract this implements --
core conclusion, panel jobs, archetype, hero panel. No measured number appears in this figure;
the captions state that the panels are conceptual, and a schematic carrying hand-typed values is
the easiest way to publish a figure that contradicts its own text.
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                     # noqa: E402
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(os.path.dirname(HERE), 'paper', 'figures')
MM = 1 / 25.4

C = {
    'ink': '#1a1a1a',
    'rule': '#5f5f5f',
    'grey': '#8c8c8c',
    'lgrey': '#d9d9d9',
    'fill': '#e9e9e9',
    'blue': '#0072B2',
    'orange': '#E69F00',
    'green': '#009E73',
    'purple': '#CC79A7',
    'accent': '#B23C34',
    'fillaccent': '#ECD1CE',
}

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 7,
    'axes.linewidth': 0.6,
    'pdf.fonttype': 42,
    'svg.fonttype': 'none',
    'savefig.bbox': None,
})


def card(ax, x, y, w, h, label=None, accent=False):
    """A panel card with an optional corner label."""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle='round,pad=0,rounding_size=1.2',
        linewidth=0.9, edgecolor=(C['accent'] if accent else C['ink']),
        facecolor='white', zorder=1))
    if label:
        ax.text(x + 1.6, y + h - 1.8, label, fontsize=7.5, fontweight='bold',
                color=(C['accent'] if accent else C['ink']),
                ha='left', va='top', zorder=4)


def box(ax, x, y, w, h, fc='white', ec=None, lw=0.5, r=0.7):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle='round,pad=0,rounding_size=%s' % r,
        linewidth=lw, edgecolor=(ec or C['rule']), facecolor=fc, zorder=2))


def glyphs(ax, x, y, n, pitch, w, gcol, ylab=None, accent_rows=()):
    """A row of passage glyphs; accent_rows marks attacker-supplied passages."""
    gcol = C['rule']
    for i in range(n):
        acc = i in accent_rows
        ax.add_patch(Rectangle(
            (x + i * pitch, y), w, 4.6, linewidth=0.5,
            edgecolor=(C['accent'] if acc else gcol),
            facecolor=(C['fillaccent'] if acc else C['fill']), zorder=3))
    if ylab:
        ax.text(x - 1.4, y + 2.3, ylab, fontsize=6.2, color=C['rule'],
                ha='right', va='center', zorder=4)


def arrow(ax, p0, p1, color=None, lw=0.7, style='-|>'):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=6.5, linewidth=lw,
        color=(color or C['ink']), shrinkA=0, shrinkB=0, zorder=5))


def build():
    fig = plt.figure(figsize=(88 * MM, 62 * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 88)
    ax.set_ylim(0, 62)
    ax.axis('off')

    # ------------------------------------------------ panel A : retrieval (top left)
    card(ax, 1.0, 34.0, 40.0, 27.0, 'A  Retrieval')
    ax.text(3.0, 56.4, 'group-neutral query', fontsize=6.2, color=C['rule'], va='top')
    box(ax, 3.0, 51.4, 25.0, 4.4, fc='white', ec=C['rule'])
    ax.text(15.5, 53.6, 'Who performed better?', fontsize=6.4, color=C['ink'],
            ha='center', va='center')
    arrow(ax, (15.5, 51.0), (15.5, 48.6))

    ax.text(3.0, 47.6, 'top-$k$ retrieved set', fontsize=6.2, color=C['rule'],
            va='top', ha='left')
    glyphs(ax, 3.0, 41.4, 5, 5.0, 4.2, C['rule'], None)
    ax.text(3.0, 38.6, 'no group is named in the query,\nso any skew comes from the corpus',
            fontsize=6.0, color=C['rule'], va='top', ha='left', linespacing=1.35)

    # ------------------------------------------------ panel B : injection (top right)
    card(ax, 45.0, 34.0, 42.0, 27.0, 'B  Injection')
    ax.text(47.2, 56.4, 'matched pairs, legitimate template inventory',
            fontsize=6.2, color=C['rule'], va='top')
    glyphs(ax, 47.2, 49.4, 6, 6.2, 5.2, C['rule'], None,
           accent_rows=(0, 1, 2, 3, 4, 5))
    ax.text(47.2, 47.6, 'favours A', fontsize=6.0, color=C['accent'], va='top')
    ax.text(72.0, 47.6, 'disfavours B', fontsize=6.0, color=C['accent'], va='top')
    ax.text(47.2, 43.0, 'balanced across groups by construction,\n'
                        'indistinguishable from clean passages',
            fontsize=6.0, color=C['rule'], va='top', ha='left', linespacing=1.35)

    # ------------------------------------------------ panel C : what a statistic sees (HEST)
    card(ax, 1.0, 1.0, 86.0, 30.0, 'C  What a statistic then sees   \u2014   same attacked set',
         accent=True)
    ax.text(3.0, 27.4,
            'the paper separates two dimensions of representation, and the attack moves only one',
            fontsize=6.2, color=C['rule'], va='top')

    # R1 row
    y0 = 17.4
    ax.text(3.0, y0 + 3.6, 'R1  group composition', fontsize=6.8, color=C['ink'],
            va='bottom', ha='left')
    glyphs(ax, 3.0, y0, 2, 5.4, 4.6, C['rule'], 'clean')
    glyphs(ax, 3.0, y0 - 6.2, 2, 5.4, 4.6, C['rule'], 'attacked')
    ax.text(15.0, y0 + 2.3, 'unchanged', fontsize=6.6, color=C['blue'],
            va='center', ha='left', fontweight='bold')
    ax.text(15.0, y0 - 3.9, 'count balanced \u2192 statistic reads its clean value',
            fontsize=6.0, color=C['rule'], va='center', ha='left')

    # R2 row
    y1 = 7.0
    ax.text(46.0, y1 + 6.4, 'R2  within-group stance', fontsize=6.8, color=C['accent'],
            va='bottom', ha='left')

    def levelbar(x, y, w, h, col, lab):
        """One group's stance level, as a short bar with a direct label."""
        ax.add_patch(Rectangle((x, y), w, h, linewidth=0.5, edgecolor=col,
                               facecolor=col, alpha=0.85, zorder=3))
        ax.text(x + w + 1.2, y + h / 2, lab, fontsize=6.0, color=C['rule'],
                va='center', ha='left')

    ax.text(46.0, y1 + 5.6, 'clean', fontsize=6.0, color=C['rule'], va='bottom')
    levelbar(46.0, y1 + 2.6, 4.0, 2.0, C['grey'], 'A')
    levelbar(46.0, y1 - 0.6, 4.0, 2.0, C['grey'], 'B')
    ax.text(60.0, y1 + 5.6, 'attacked', fontsize=6.0, color=C['accent'], va='bottom')
    levelbar(60.0, y1 + 2.6, 1.2, 2.0, C['accent'], 'A down')
    levelbar(60.0, y1 - 0.6, 6.8, 2.0, C['accent'], 'B up')
    ax.text(60.0, y1 - 3.4, 'stance relocated \u2192 statistic moves', fontsize=6.0,
            color=C['accent'], va='top', ha='left')

    return fig


def main():
    os.makedirs(FIGS, exist_ok=True)
    fig = build()
    stem = os.path.join(FIGS, 'fig_framework_py')
    fig.savefig(stem + '.pdf')
    fig.savefig(stem + '.png', dpi=600)
    plt.close(fig)
    print('wrote %s.pdf and .png' % stem)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
