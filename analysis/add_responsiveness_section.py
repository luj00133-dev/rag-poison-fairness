"""Add the responsiveness control to section 3.4.

This is the evidence the framework needs to be a contribution rather than a
complaint. Without it a reviewer can read the paper as "these statistics are
unreliable"; with it the claim is specifically "these statistics are immune to an
adversary who balances what they count, and here is proof that they do respond when
the ground truth moves".

The control holds the corpus size fixed at 17,792 passages and swaps passages
between two well-populated groups, so the retrieval pool and the score threshold do
not move and composition is the only thing that changes -- by a known number of
passages, in a known direction, and reversed in the last row.

    variant                    corpus%woman  drift_tv  drift_js  stance_div  onesided
    baseline                          0.500    0.0000    0.0000      0.2925    0.4753
    swap 500  man->woman              0.580    0.0264    0.0372      0.2876    0.4711
    swap 1500 man->woman              0.739    0.0660    0.0809      0.2854    0.4694
    swap 3000 man->woman              0.978    0.0924    0.1062      0.2854    0.4694
    swap 3000 woman->man              0.022    0.0569    0.0532      0.2851    0.4691

drift_tv and drift_js track the composition change monotonically and move in the
right direction; the two reference-based stance statistics barely move, which is
independent confirmation of F2 on data where the ground truth is known by
construction.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

ANCHOR = ('**What the taxonomy does not claim.** It is not a claim that no fairness '
          'metric can be robust.')
assert s.count(ANCHOR) == 1, s.count(ANCHOR)

NEW = r'''**The taxonomy is testable against known ground truth, and we ran that test.** A taxonomy of failure modes is only worth stating if the statistics it indicts are otherwise sound: if they did not respond to a real composition change either, the finding would be that the measurement apparatus is broken, not that an adversary defeats it. We therefore ran a positive control on the naturally written corpus, where the true composition is known by construction.

The control holds the corpus size fixed at 17,792 passages and **swaps** passages between the two groups of a balanced stratum, so the retrieval pool and the score threshold do not move and composition is the only variable. It changes by a known number of passages, in a known direction, and is reversed in the last row.

**Table 2.** Responsiveness control. Corpus size constant; only group composition changes. `corpus%woman` is the true share after the swap; the remaining columns are the statistics under test.

| Variant | `corpus%woman` | `drift_tv` | `drift_js` | `stance_div` | `stance_onesided` |
|---|---|---|---|---|---|
| baseline (balanced) | 0.500 | 0.0000 | 0.0000 | 0.2925 | 0.4753 |
| swap 500 man→woman | 0.580 | 0.0264 | 0.0372 | 0.2876 | 0.4711 |
| swap 1500 man→woman | 0.739 | 0.0660 | 0.0809 | 0.2854 | 0.4694 |
| swap 3000 man→woman | 0.978 | 0.0924 | 0.1062 | 0.2854 | 0.4694 |
| **swap 3000 woman→man** | **0.022** | **0.0569** | 0.0532 | 0.2851 | 0.4691 |

Two conclusions, and they are what make the negative results interpretable rather than merely negative. First, **`drift_tv` and `drift_js` are working instruments**: they rise monotonically with a real composition change and respond to its direction. The R1 statistic is not broken; it is *specifically* invariant to an injection that balances group counts, which is exactly what F1 predicts and what §5.2 measures. Second, **the two reference-based stance statistics barely move even here** — `stance_div` changes by 0.007 across a composition swing from 0.022 to 0.978 — which is independent confirmation of F2 on data whose ground truth is known by construction rather than inferred from an attack.

The contrast is the paper's central claim in one table: the same statistics that detect a 3000-passage composition change with $p \to 0$ detect a fully adversarial injection not at all.

**What the taxonomy does not claim.** It is not a claim that no fairness metric can be robust.'''

s = s.replace(ANCHOR, NEW)
io.open(P, 'w', encoding='utf-8').write(s)

print('responsiveness control added to 3.4')
print('paper length: %d chars' % len(s))
