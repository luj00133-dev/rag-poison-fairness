"""Render the four data figures for Paper A.

Design rules applied to all four, because a figure that misleads is worse than no
figure:

  * numbers come only from results/figure_data.json, which is extracted from the
    committed result files by analysis/figure_data.py. Nothing is typed by hand.
  * a muted, colour-blind-safe palette (Okabe-Ito derivations); no red/green pair.
  * fonts sized for a final width of 88 mm (single column) or 190 mm (double), so
    the PDF is placed at 1:1 and stays legible.
  * vector output (PDF) plus a 600 dpi PNG for inspection.
  * every axis labelled with units, and zero lines drawn explicitly where a claim is
    about a null.

Outputs land in paper/figures/.
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIGS = os.path.join(ROOT, 'paper', 'figures')
DATA = json.load(open(os.path.join(ROOT, 'results', 'figure_data.json'),
                      encoding='utf-8'))

#: Okabe-Ito derived, colour-blind safe
C = {
    'black': '#000000',
    'grey': '#8c8c8c',
    'lgrey': '#d9d9d9',
    'blue': '#0072B2',
    'orange': '#E69F00',
    'purple': '#CC79A7',
    'green': '#009E73',
}
MM = 1 / 25.4
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 7,
    'axes.linewidth': 0.6,
    'axes.labelsize': 7.5,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'legend.fontsize': 6.5,
    'legend.frameon': False,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'xtick.major.size': 2.5,
    'ytick.major.size': 2.5,
    'figure.dpi': 150,
    # no crop: a tight bbox lets rotated tick labels stretch the image,
    # so the declared figure size would not be the delivered size
    'savefig.bbox': None,
})


def save(fig, name, *, bottom=0.24, left=0.17, right=0.97, top=0.95,
         wspace=0.30):
    """Lay out inside the canvas, then save without cropping.

    Margins are deliberately generous. A vision description of the first render caught
    a clipped y-axis label and a clipped suptitle, both caused by margins that were
    right for the axes but not for the text around them; ink-coverage checks cannot
    see that. Titles now live in the LaTeX caption, so `top` only has to clear the
    axes frame.
    """
    fig.subplots_adjust(bottom=bottom, left=left, right=right, top=top,
                        wspace=wspace)
    os.makedirs(FIGS, exist_ok=True)
    # The file-writing loop lives here and nowhere else. An earlier round of edits
    # replaced this function wholesale and silently dropped it, so the script still
    # ran and printed "done" while writing nothing -- which is why a later tick-label
    # change had no effect on the images even though the JSON behind them had changed,
    # and why a vision description kept reporting the old label.
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(FIGS, '%s.%s' % (name, ext)), dpi=600)
    plt.close(fig)
    print('   wrote %s.pdf / .png' % name)


def stat_ok(p):
    return '*' if (p is not None and p < 0.05) else ''


# --------------------------------------------------------------------------- #
def fig1_r1_inertness():
    """The R1 constraint's effect on adversarial inclusion is exactly zero."""
    d = DATA['fig4_r1_inertness']
    fig, axes = plt.subplots(1, 2, figsize=(88 * MM, 50 * MM), sharey=True)
    kinds = [('repr_group', 'R1 only', C['blue'], 'o', '-'),
             ('repr_stance', 'R2 only', C['orange'], 's', '--'),
             ('repr_both', 'R1+R2', C['purple'], '^', ':')]

    for ax, rt in zip(axes, ('bm25', 'dense')):
        base = d[rt]['baseline']
        ax.axhline(base, color=C['black'], lw=0.9, zorder=1,
                   label='no defense (%.3f)' % base)
        for key, label, col, mk, ls in kinds:
            pts = d[rt]['series'].get(key)
            if not pts:
                continue
            eps = [p['eps'] for p in pts]
            y = [p['poison_at_k'] for p in pts]
            ax.plot(eps, y, color=col, marker=mk, ms=3.0, lw=0.9,
                    ls=ls, zorder=2, label=label, clip_on=False)
        ax.set_xlabel(r'budget $\varepsilon$')
        ax.set_xlim(1.08, -0.08)
        ax.set_ylim(-0.05, 1.08)
        ax.grid(axis='y', color=C['lgrey'], lw=0.4, zorder=0)

    axes[0].set_ylabel('poison@k')
    axes[0].legend(loc='lower left', ncol=1, handlelength=1.6,
                   borderpad=0.1, labelspacing=0.25)
    save(fig, 'fig_r1_inertness', bottom=0.24, left=0.20,
         right=0.98, top=0.93, wspace=0.34)


# --------------------------------------------------------------------------- #
def fig2_aggregate_vs_pergroup():
    """The aggregate gap is flat; the per-group shifts are large."""
    rows = DATA['fig5_aggregate_vs_pergroup']
    gens = [r['generator'] for r in rows]
    x = np.arange(len(gens))
    w = 0.26

    fig, axes = plt.subplots(1, 2, figsize=(140 * MM, 50 * MM),
                             gridspec_kw={'width_ratios': [1, 1.25]})

    # left: the aggregate gap
    ax = axes[0]
    vals = [r['delta_gap'] for r in rows]
    ax.bar(x, vals, w * 2.2, color=C['grey'], edgecolor=C['black'],
           linewidth=0.5, zorder=2)
    for xi, r in zip(x, rows):
        ax.annotate(stat_ok(r['p_gap']), (xi, r['delta_gap']),
                    ha='center', va='bottom' if r['delta_gap'] >= 0 else 'top',
                    fontsize=8, zorder=3)
    ax.axhline(0, color=C['black'], lw=0.7, zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels(gens, rotation=18, ha='right')
    ax.set_ylabel(r'$\Delta$ absolute cross-group gap')
    ax.set_ylim(-0.07, 0.07)
    ax.grid(axis='y', color=C['lgrey'], lw=0.4, zorder=0)

    # right: the per-group shifts
    ax = axes[1]
    ax.bar(x - w / 1.6, [r['delta_g1'] for r in rows], w,
           color=C['blue'], edgecolor=C['black'], linewidth=0.5,
           label='group 1 (suppressed)', zorder=2)
    ax.bar(x + w / 1.6, [r['delta_g2'] for r in rows], w,
           color=C['orange'], edgecolor=C['black'], linewidth=0.5,
           label='group 2 (favoured)', zorder=2)
    for xi, r in zip(x, rows):
        ax.annotate(stat_ok(r['p_g1']), (xi - w / 1.6, r['delta_g1']),
                    ha='center', va='top', fontsize=8, zorder=3)
        ax.annotate(stat_ok(r['p_g2']), (xi + w / 1.6, r['delta_g2']),
                    ha='center', va='bottom', fontsize=8, zorder=3)
    ax.axhline(0, color=C['black'], lw=0.7, zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels(gens, rotation=18, ha='right')
    ax.set_ylabel(r'$\Delta$ per-group stance')
    ax.set_ylim(-0.22, 0.22)
    ax.legend(loc='lower left', ncol=2, handlelength=1.2, columnspacing=1.0,
              borderpad=0.1)
    ax.grid(axis='y', color=C['lgrey'], lw=0.4, zorder=0)

    save(fig, 'fig_aggregate_vs_pergroup', bottom=0.30, left=0.13,
         right=0.98, top=0.97, wspace=0.30)


# --------------------------------------------------------------------------- #
def fig3_encoder_scale():
    """Susceptibility is not monotone in encoder size.

    Values are not annotated on the lines: two families share 0.0625 at
    base, so inline labels collide, and the legend already prints each
    family's exact pair.
    """
    d = DATA['fig6_encoder_scale']
    fams = [f for f in ('GTE', 'E5', 'SPLADE') if f in d]
    style = {'GTE': (C['blue'], 'o'), 'E5': (C['green'], 's'),
             'SPLADE': (C['orange'], '^')}

    fig, ax = plt.subplots(figsize=(88 * MM, 62 * MM))
    for fam in fams:
        col, mk = style[fam]
        sizes = d[fam]
        if 'base' not in sizes or 'large' not in sizes:
            continue
        y = [sizes['base'], sizes['large']]
        ax.plot([0, 1], y, color=col, marker=mk, ms=4.5, lw=1.2,
                label='%s (%.4f $\\rightarrow$ %.4f)' % (fam, y[0], y[1]),
                clip_on=False)
    ax.axhline(0, color=C['black'], lw=0.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['base\n(110M / 66M)', 'large\n(335M / 110M)'])
    ax.set_xlim(-0.25, 1.25)
    # The range comes from the data, not from a constant. A hard-coded 0.60 put the
    # SPLADE base value (0.6250) outside the axes, so its marker and label were cut
    # off by the canvas -- a reader would have seen that series starting at its
    # second point.
    vals = [v for fam in fams for v in d[fam].values()]
    hi = max(vals) * 1.35 + 0.03
    ax.set_ylim(-0.06, hi)
    ax.set_ylabel('poison@k')
    ax.legend(loc='upper left', handlelength=1.6, borderpad=0.1,
              labelspacing=0.3)
    ax.grid(axis='y', color=C['lgrey'], lw=0.4, zorder=0)
    save(fig, 'fig_encoder_scale', bottom=0.22, left=0.20,
         right=0.97, top=0.96)


# --------------------------------------------------------------------------- #
def fig4_responsiveness():
    """The statistics respond to ground truth, so their attack-blindness is specific."""
    d = DATA['fig7_responsiveness']
    comp = np.array(d['corpus_pct_woman'])
    order = np.argsort(comp)
    labels = [d['variant'][i].replace('\n', ' ') for i in order]
    comp_s = comp[order]

    fig, axes = plt.subplots(1, 2, figsize=(140 * MM, 48 * MM),
                             gridspec_kw={'width_ratios': [1, 1.15]})
    x = np.arange(len(comp_s))

    ax = axes[0]
    ax.bar(x, comp_s, 0.6, color=C['grey'], edgecolor=C['black'],
           linewidth=0.5, zorder=2)
    ax.axhline(0.5, color=C['blue'], lw=0.8, ls='--', zorder=3,
               label='balanced (0.500)')
    for xi, v in zip(x, comp_s):
        ax.annotate('%.3f' % v, (xi, v), ha='center',
                    va='bottom' if v > 0.05 else 'top', fontsize=6.2,
                    zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=6.0)
    ax.set_xlim(-0.62, len(comp_s) - 0.38)
    ax.set_ylabel('group share in corpus')
    ax.set_ylim(-0.10, 1.12)
    ax.legend(loc='upper left', handlelength=1.4, borderpad=0.1)
    ax.grid(axis='y', color=C['lgrey'], lw=0.4, zorder=0)

    ax = axes[1]
    series = [
        ('drift_tv', r'R1 drift ($\mathrm{TV}$)', C['blue'], 'o', '-'),
        ('drift_js', r'R1 drift ($\mathrm{JS}$)', C['green'], 's', '--'),
        ('stance_div', 'R2 deviation from reference', C['orange'], '^', '-.'),
        ('stance_onesided', 'R2 one-sidedness', C['purple'], 'v', ':'),
    ]
    for key, label, col, mk, ls in series:
        v = np.array(d[key])[order]
        ax.plot(x, v, color=col, marker=mk, ms=3.4, lw=1.0, ls=ls,
                label=label, clip_on=False)
    ax.axhline(0, color=C['black'], lw=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=6.0)
    ax.set_xlim(-0.62, len(comp_s) - 0.38)
    ax.set_ylabel('statistic value')
    ax.set_ylim(-0.03, 0.52)
    ax.legend(loc='upper left', handlelength=1.8, borderpad=0.1,
              labelspacing=0.22)
    ax.grid(axis='y', color=C['lgrey'], lw=0.4, zorder=0)

    save(fig, 'fig_responsiveness', bottom=0.38, left=0.13,
         right=0.98, top=0.96, wspace=0.30)


if __name__ == '__main__':
    print('rendering figures to %s' % FIGS)
    fig1_r1_inertness()
    fig2_aggregate_vs_pergroup()
    fig3_encoder_scale()
    fig4_responsiveness()
    print('done')
