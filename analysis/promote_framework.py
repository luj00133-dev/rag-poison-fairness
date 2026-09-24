"""Put the framework at the front of the paper, where a reader decides what it is.

Section 3.4 now states that every candidate metric has one form and fails in one of
three ways, and section 3.4 also carries the positive control showing the indicted
statistics are otherwise sound. Neither is visible from the abstract or the
contribution list, which still lead with the individual failures. A reviewer forms a
view in the first page, and at the moment that view is "a list of case studies"
rather than "a framework plus evidence".

This rewrites the abstract's opening and the contribution list so the paper declares
its shape: one form, three failure modes, a test that predicts them, and a control
that separates "blind to this adversary" from "broken".
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

# --- abstract: state the framework up front ---------------------------------- #
OLD_ABS = ('Fairness defenses for retrieval-augmented generation (RAG) are selected '
           'and validated using aggregate statistics of the retrieved set: the '
           'proportion of passages about each protected group, the deviation of a '
           "group's stance from a corpus reference, or the exposure of items across "
           'repeated requests. We show that these statistics are **blind to the '
           'attack they are meant to detect**, and we identify the property they '
           'all share that makes them blind.')

NEW_ABS = ('Fairness defenses for retrieval-augmented generation (RAG) are selected '
           'and validated using aggregate statistics of the retrieved set: the '
           'proportion of passages about each protected group, the deviation of a '
           "group's stance from a corpus reference, or the exposure of items across "
           'repeated requests. Every such statistic has the same form — a per-group '
           'quantity aggregated across groups — and we show that an adversary who '
           'knows this can defeat the aggregation in exactly **three ways**, which '
           'together explain why the defenses built on these statistics fail:\n\n'
           '- **F1, balanced count.** The injection contributes equally to every '
           'group, so any statistic over group counts returns its clean value.\n'
           '- **F2, preserved nuisance.** The statistic is anchored to a reference '
           'the attack does not change, so it reports the component that varies with '
           'the query rather than the one that varies with the attack.\n'
           '- **F3, cancelled shift.** The attack moves all groups together, so any '
           'difference between groups is unchanged however far the groups move.\n\n'
           'The three modes are not a description but a **test**: each can be checked '
           'against a candidate statistic before any attack is built, and we use them '
           'to predict which existing metrics will be blind. To separate *blind to '
           'this adversary* from *broken instrument*, we add a positive control in '
           'which the ground truth changes by a known amount and the same statistics '
           'must respond: they do, monotonically and in the right direction.')

assert s.count(OLD_ABS) == 1, s.count(OLD_ABS)
s = s.replace(OLD_ABS, NEW_ABS)
print('abstract rewritten to lead with the framework')

# --- contributions: promote the framework to first ---------------------------- #
OLD_C1 = ('1. A two-dimensional formalisation of representation in retrieved sets '
          '(R1 composition, R2 within-group stance), with the observation that '
          'adversarial injection is balanced in R1 and skewed in R2, and an analysis '
          'of which aggregate statistics are sensitive to it (\u00a73, \u00a75.1).')

NEW_C1 = ('1. **A framework for why adversarial fairness statistics fail.** Every '
          'candidate metric in this literature is a per-group quantity aggregated '
          'across groups, and an adversary can defeat the aggregation in exactly '
          'three ways: by balancing what the statistic counts (F1), by anchoring it '
          'to a reference the attack preserves (F2), or by moving all groups '
          'together so a difference between them cancels (F3). The modes are '
          'checkable in advance of building an attack, and we use them to predict '
          'which published metrics are blind (\u00a73.4), then confirm the '
          'predictions empirically (\u00a75.1, \u00a75.2, \u00a75.7).\n'
          '2. **A positive control that separates blindness from breakage.** With '
          'the ground truth moved by a known amount and the corpus size held fixed, '
          'the indicted statistics respond monotonically and directionally '
          '(Table 1). The claim is therefore specific — these statistics are immune '
          'to an adversary who balances what they count — rather than a general '
          'complaint that the instrument is unreliable.')

assert s.count(OLD_C1) == 1, s.count(OLD_C1)
s = s.replace(OLD_C1, NEW_C1)

# renumber the remaining contributions
for old, new in (
    ('2. Identification of a **shared cause of measurement failure**:',
     '3. Identification of a **shared cause of measurement failure**:'),
    ('3. A controlled pairwise-poisoning construction that makes both dimensions',
     '4. A controlled pairwise-poisoning construction that makes both dimensions'),
    ('4. An empirical demonstration that R1-constraining defenses are inert, with',
     '5. An empirical demonstration that R1-constraining defenses are inert, with'),
    ('5. A negative result on the limits of distribution-level defense:',
     '6. A negative result on the limits of distribution-level defense:'),
    ('6. A scale check that bounds the sparsity account of encoder susceptibility:',
     '7. A scale check that bounds the sparsity account of encoder susceptibility:'),
    ('7. A measurement protocol implied by the above:',
     '8. A measurement protocol implied by the above:'),
):
    if s.count(old) == 1:
        s = s.replace(old, new)

io.open(P, 'w', encoding='utf-8').write(s)

import re
print()
print('contributions now:')
for m in re.finditer(r'^(\d+)\. \*\*(.{0,62})', s, re.M):
    print('  %s. %s' % (m.group(1), m.group(2)))
print()
print('paper length: %d chars' % len(s))
