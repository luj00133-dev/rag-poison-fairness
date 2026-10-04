"""Shared house style and layout guard for the concept figures.

Extracted so all three concept figures use one style and one guard rather than three copies that
drift apart. The guard exists because two of the three defects in the first framework attempt were
text blocks leaving their card, which I could not see by reasoning about coordinates and did not
notice by looking at the render.

Style is copied from analysis/make_figures.py, the script that already draws the four data figures,
so the concept figures match them by construction: Okabe-Ito palette, Arial at 7 pt base, 88 mm and
140 mm widths, vector output with editable text.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch  # noqa: E402

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
    'fillblue': '#D6E6F2',
}

STYLE = {
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 6,
    'pdf.fonttype': 42,
    'svg.fonttype': 'none',
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.012,
}


class Canvas:
    """A figure with one full-bleed axes and a register of placed text."""

    def __init__(self, width_mm, height_mm):
        plt.rcParams.update(STYLE)
        self.fig = plt.figure(figsize=(width_mm * MM, height_mm * MM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_axis_off()
        self.placed = []

    # -- primitives ------------------------------------------------------- #

    def card(self, g, accent=False, lw=0.9):
        self.ax.add_patch(FancyBboxPatch(
            (g['x'], g['y']), g['w'], g['h'],
            boxstyle='round,pad=0,rounding_size=0.008', linewidth=lw,
            edgecolor=(C['accent'] if accent else C['ink']), facecolor='white',
            zorder=1, transform=self.ax.transAxes))

    def box(self, x, y, w, h, ec=None, fc='white', lw=0.5, z=3, r=0.008):
        self.ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle='round,pad=0,rounding_size=%s' % r,
            linewidth=lw, edgecolor=(ec or C['rule']), facecolor=fc, zorder=z,
            transform=self.ax.transAxes))

    def rect(self, x, y, w, h, ec, fc, lw=0.5, z=3):
        self.ax.add_patch(Rectangle((x, y), w, h, linewidth=lw, edgecolor=ec,
                                    facecolor=fc, zorder=z, transform=self.ax.transAxes))

    def arrow(self, p0, p1, color=None, lw=0.6, ms=6.0, z=5):
        self.ax.add_patch(FancyArrowPatch(
            p0, p1, arrowstyle='-|>', mutation_scale=ms, linewidth=lw,
            color=(color or C['ink']), shrinkA=0, shrinkB=0, zorder=z,
            transform=self.ax.transAxes))

    def glyphs(self, x, y, n, pitch, w, h=0.055, accent=(), z=3):
        for i in range(n):
            acc = i in accent
            self.rect(x + i * pitch, y, w, h,
                      C['accent'] if acc else C['rule'],
                      C['fillaccent'] if acc else C['fill'], z=z)

    # -- text with measurement -------------------------------------------- #

    def text(self, x, y, s, card=None, tag=None, **kw):
        kw.setdefault('zorder', 6)
        t = self.ax.text(x, y, s, transform=self.ax.transAxes, **kw)
        self.fig.canvas.draw()
        bb = t.get_window_extent(renderer=self.fig.canvas.get_renderer())
        inv = self.ax.transAxes.inverted()
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        self.placed.append((tag or s[:22], (x0, y0, x1, y1), card))
        return t

    # -- the guard -------------------------------------------------------- #

    def audit(self, quiet=False):
        problems = []
        for name, bb, cardb in self.placed:
            if cardb:
                cx, cy, cw, ch = cardb['x'], cardb['y'], cardb['w'], cardb['h']
                out = []
                if bb[0] < cx - 0.003:
                    out.append('left')
                if bb[2] > cx + cw + 0.003:
                    out.append('right')
                if bb[1] < cy - 0.003:
                    out.append('bottom')
                if bb[3] > cy + ch + 0.003:
                    out.append('top')
                if out:
                    problems.append('OUTSIDE CARD (%s): %-26s text=(%.3f,%.3f,%.3f,%.3f) '
                                    'card=(%.3f,%.3f,%.3f,%.3f)'
                                    % (','.join(out), name, bb[0], bb[1], bb[2], bb[3],
                                       cx, cy, cw, ch))
        for i in range(len(self.placed)):
            for j in range(i + 1, len(self.placed)):
                a, b = self.placed[i][1], self.placed[j][1]
                ox = min(a[2], b[2]) - max(a[0], b[0])
                oy = min(a[3], b[3]) - max(a[1], b[1])
                if ox > 0.004 and oy > 0.004:
                    problems.append('OVERLAP (%.3f x %.3f): %-24s <-> %-24s'
                                    % (ox, oy, self.placed[i][0], self.placed[j][0]))
        if not quiet:
            print('layout audit: %d problem(s)' % len(problems))
            for p in problems:
                print('   ' + p)
        return problems

    def save(self, stem, dpi=600):
        """Save only if the layout is clean; a defective figure is not written."""
        if self.audit():
            print('NOT SAVED: fix the layout rather than shipping the defect')
            plt.close(self.fig)
            return False
        for ext in ('pdf', 'png'):
            self.fig.savefig('%s.%s' % (stem, ext), dpi=dpi if ext == 'png' else None)
            print('wrote %s.%s' % (stem, ext))
        plt.close(self.fig)
        return True
