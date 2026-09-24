"""Diagnose the forced-choice probe before drawing any conclusion from it.

The first forced-choice result looked meaningless in a specific way: the favourable
rate for the first group was exactly 1.0000 in every condition while the second
group's rate moved. That pattern is what a *positional* response produces. The probe
puts the favourable statement at position A or B by a seeded coin flip; if the model
answers "A" regardless of content, then the recorded stance is determined by the flip,
and a run of coin flips that happened to favour one group looks like a stance effect.

So before the probe is used on either corpus, this measures whether its answers carry
statement information at all:

  * `P(A)` -- how often the model picks position A. Near 1.0 or near 0.0 means the
    answer is positional and the probe is measuring nothing.
  * `P(favourable)` -- how often the favourable statement is chosen, and whether it
    departs from `P(A)` in the way content-driven answering would require.
  * the same quantities conditioned on the group, which is what the metric needs.
  * the NLI margin, already known to be uninformative for one-letter replies, kept as
    a recorded failure rather than dropped silently.

A probe passes if `P(A)` is not extreme AND the favourable rate is driven by content
rather than by position, which shows up as `P(favourable)` differing between the
favourable-at-A and favourable-at-B halves.
"""
import json
import os
import sys
from collections import defaultdict

import numpy as np


def pct(x):
    return '%.1f%%' % (100 * x)


def main():
    dirs = sys.argv[1:] or ['results/fc_smoke']
    for out_dir in dirs:
        path = os.path.join(out_dir, 'forced_choice.json')
        if not os.path.exists(path):
            print('%s: missing' % out_dir)
            continue
        d = json.load(open(path, encoding='utf-8'))
        print('=' * 88)
        print('FORCED-CHOICE PROBE DIAGNOSTIC - corpus %s' % d.get('corpus'))
        print('=' * 88)
        for g in d['generators']:
            recs = [r for r in g['records'] if r.get('choice') in ('A', 'B')]
            if not recs:
                print('\n--- %s: no parsed choices ---' % g['label'])
                continue
            print('\n--- %s   n=%d ---' % (g['label'], len(recs)))

            p_a = float(np.mean([r['choice'] == 'A' for r in recs]))
            fav = float(np.mean([(r['choice'] == 'A') == bool(r['fav_is_a'])
                                 for r in recs]))
            print('  P(choose A)        = %s   <- positional bias if extreme' % pct(p_a))
            print('  P(choose fav)      = %s   <- content signal' % pct(fav))

            # split by where the favourable statement sat; a content-driven model
            # must answer differently in the two halves
            at_a = [r for r in recs if r['fav_is_a']]
            at_b = [r for r in recs if not r['fav_is_a']]
            if at_a and at_b:
                fa = float(np.mean([r['choice'] == 'A' for r in at_a]))
                fb = float(np.mean([r['choice'] == 'A' for r in at_b]))
                print('  P(A | fav at A)    = %s' % pct(fa))
                print('  P(A | fav at B)    = %s' % pct(fb))
                swing = abs(fa - fb)
                print('  swing              = %s   <- must be large for the probe to'
                      ' carry signal' % pct(swing))

            by_group = defaultdict(list)
            for r in recs:
                by_group[str(r['group'])].append(
                    (r['choice'] == 'A') == bool(r['fav_is_a']))
            print('  per-group P(fav):  %s' % '  '.join(
                '%s=%s' % (k, pct(float(np.mean(v))))
                for k, v in sorted(by_group.items())))

            margins = [r['margin'] for r in recs if r.get('margin') is not None]
            if margins:
                print('  NLI margin mean    = %+.4f   (known to be uninformative for'
                      ' one-letter replies)' % float(np.mean(margins)))

            print()
            if p_a > 0.9 or p_a < 0.1:
                print('  FAILS: answers are positional. The recorded stance is a')
                print('  function of where the statements were placed, not of what')
                print('  the context supports, so any group difference it shows is an')
                print('  artefact of the coin flips.')
            elif at_a and at_b and abs(fa - fb) < 0.2:
                print('  FAILS: the choice does not depend on which statement is')
                print('  favourable, so the probe is not reading stance.')
            else:
                print('  PASSES: the choice tracks statement content, so the')
                print('  favourable rate is a measurement.')
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
