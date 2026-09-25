"""Insert the five concept figures into the markdown source, matching the tex.

The tex was edited first; if the markdown is left alone the two sources disagree
about how many figures the paper has, and the next conversion pass from markdown
(pandoc -> docx, or make_latex.py) would silently drop all five. So the same five
insertions are made here, at the same anchors, with the same captions.

Anchors are the neighbouring prose, not the section numbers, so a renumbering pass
cannot silently misplace a figure.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

FRAMEWORK = (
    '![The paper\'s framework in one panel. **(A)** A group-neutral query is answered '
    'from the top-$k$ retrieved set. **(B)** The attacker injects passages drawn from the '
    'legitimate template inventory in matched pairs --- one favourable to group A, one '
    'unfavourable to group B --- so the injection is balanced across groups by construction. '
    '**(C)** What a statistic then sees: an R1 (group-composition) statistic is left at its '
    'clean value because the attack balances the count, whereas an R2 (within-group stance) '
    'statistic is skewed because the attack changes the stance the evidence supports. The '
    'figure states the two dimensions the paper separates; the three failure modes below are '
    'the ways an aggregate over such statistics loses that signal.]'
    '(figures/fig_framework.png){width=88mm}\n\n'
)

FAILURE_MODES = (
    '![The three failure modes, shown on the same retrieval setting. **(a) F1:** the injection '
    'contributes equally to every group, so a counting or composition statistic returns its '
    'clean value --- the attack is invisible to it (measured in §5.1 and §5.2). **(b) F2:** the '
    'statistic is anchored to a reference the attack does not move, so it reports the component '
    'that varies with the query rather than the one that varies with the attack (`stance_div` '
    'and `stance_onesided`, §3.2 and §5.1). **(c) F3:** all groups are relocated together, so '
    'any difference between groups is unchanged however far the groups move (`stance_gap` and '
    'its generation-layer twin, §5.1 and §5.7). The three panels are conceptual and carry no '
    'measured values; the corresponding measurements are in the sections named in the table '
    'above and in the responsiveness figure.](figures/fig_failure_modes.pdf){width=140mm}\n\n'
)

PROBE = (
    '![The instrument, not the corpus, was the reason the natural corpus appeared to show '
    'nothing. **Left:** with a free-form probe most answers take no position at all --- on the '
    'full BBQ corpus 99.0% of them, against 84.4% on the controlled corpus --- so the statistic '
    'reads near zero under every condition and no effect of any size could have appeared in it. '
    '**Right:** a forced-choice probe makes the same answers commit to a side, and on identical '
    'retrieval conditions it reads an effect, with five per-group shifts at $p < 0.05$ for one '
    'generator (Table 14). The panels are conceptual and carry no measured values; the commitment '
    'values they illustrate are in Table 13.](figures/fig_probe_commitment.png){width=140mm}\n\n'
)

INSERTS = [
    # (anchor, block, position)
    (
        '**The taxonomy is a test, not a description.** For a candidate statistic $M$, the '
        'three failure modes correspond to three questions that can be asked before any attack '
        'is built:',
        FRAMEWORK,
        'before',
    ),
    (
        'A statistic that survives all three is, in our setting, one that reports '
        '**per-group levels** rather than a difference between them,',
        FAILURE_MODES,
        'before',
    ),
    (
        'The gap is 22×, and it means the free-form statistic on BBQ is near zero under '
        '*every* condition:',
        PROBE,
        'before',
    ),
]

placed = 0
for anchor, block, pos in INSERTS:
    if s.count(anchor) != 1:
        print('ANCHOR PROBLEM (%d matches): %r' % (s.count(anchor), anchor[:60]))
        continue
    s = s.replace(anchor, block + anchor, 1)
    placed += 1
    print('inserted before %r' % anchor[:58])

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print()
print('%d of %d figures placed; images in manuscript: %d'
      % (placed, len(INSERTS), s.count('![')))
