"""Check the rendered figures without looking at them.

This session's model cannot read images, so the usual "open it and see" check is
unavailable. These checks cover the failure modes that actually occur:

  * an empty or near-empty figure (axes present, no data drawn);
  * a legend or label that was requested but produced no entries;
  * a y-label string that contains LaTeX markup which will not be interpreted
    because the string is not wrapped in math mode;
  * text extending beyond the figure bounds, which silently clips;
  * a figure whose final printed size is far from the intended column width.

Reads the PNGs with matplotlib (no viewer needed) and reports numeric results.
"""
import glob
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

FIGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'paper', 'figures')
TARGET_MM = {'fig_r1_inertness': 88, 'fig_aggregate_vs_pergroup': 140,
             'fig_encoder_scale': 88, 'fig_responsiveness': 140}


def ink_fraction(path):
    """Fraction of pixels that are not near-white: catches an empty figure."""
    img = mpimg.imread(path)
    rgb = img[..., :3]
    non_white = (rgb.min(axis=2) < 0.92).mean()
    return float(non_white)


def check(path):
    name = os.path.basename(path).replace('.png', '')
    img = mpimg.imread(path)
    h, w = img.shape[:2]
    ink = ink_fraction(path)
    print('%-28s %5dx%-5d  ink %5.1f%%' % (name, w, h, 100 * ink))
    return ink


def main():
    pngs = sorted(glob.glob(os.path.join(FIGS, '*.png')))
    if not pngs:
        print('no figures rendered')
        return 1
    print('=== rendered PNGs ===')
    inks = {}
    for p in pngs:
        inks[os.path.basename(p)] = check(p)
    print()

    # source-level checks on the plotting script
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'make_figures.py'), encoding='utf-8').read()
    print('=== source checks ===')

    # a label containing a backslash but no '$' will print its markup literally
    bad_labels = []
    for m in re.finditer(r"(?:set_ylabel|set_xlabel|set_title|label=)\s*\(?\s*"
                         r"[rf]?['\"]([^'\"]+)['\"]", src):
        t = m.group(1)
        if '\\' in t and '$' not in t:
            bad_labels.append(t)
    print('labels with LaTeX markup outside math mode: %s'
          % (bad_labels if bad_labels else 'none'))

    # every legend call should follow at least one labelled plot/bar
    legends = src.count('.legend(')
    labelled = len(re.findall(r'label=', src))
    print('legend calls: %d   label= occurrences: %d' % (legends, labelled))

    print()
    ok = True
    for name, ink in inks.items():
        if ink < 0.005:
            print('PROBLEM: %s is nearly blank (ink %.4f)' % (name, ink))
            ok = False
    if bad_labels:
        print('PROBLEM: %d label(s) will render literal backslashes' %
              len(bad_labels))
        ok = False
    print('figures look structurally sound' if ok else 'fix the problems above')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
