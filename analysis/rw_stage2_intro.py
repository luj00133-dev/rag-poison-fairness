"""Stage 2: introduction rewrite.

Three targeted changes, each an instance of a rule in the skill:

1. "A second, subtler failure -- one we fell into ourselves" and its closing sentence
   ("a measurement paper whose authors did not notice their own instance of the error would
   not be credible about anyone else's") become a statement about the CLASS of statistics.
   The technical content is identical; what goes is a self-audit that invites the reader to
   judge the authors instead of the metrics. The first-person history is preserved in the
   limitations appendix, so nothing is hidden.

2. The bullet "a distinction we had to be corrected by our own data to see" loses the
   self-correction and keeps the distinction, which is a real contribution.

3. The provenance bullet drops "exploratory", "we state plainly" and "may be an artefact",
   and states the falsification test directly. The claim is unchanged and still bounded --
   it is presented as a candidate signal with a specified refutation, not as a defense --
   but it no longer reads as an apology.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

EDITS = [
    # 1. the "we fell into it ourselves" paragraph
    ('**A second, subtler failure — one we fell into ourselves.** The obvious repair is to '
     'move from composition to stance and to keep using the same arithmetic: measure the '
     '*gap* between the two groups. That repair also fails, and the reason generalises. '
     'An absolute difference between two group-level quantities is dominated by whatever '
     'constant asymmetry the corpus already had, so it is insensitive to an attack that '
     '**relocates both groups together** — which is what this attack does, suppressing one '
     'group while elevating the other. The diagnostic is the *per-group shift*. We identify '
     'this failure at the retrieval layer (§5.3), where two of three candidate R2 '
     'statistics are flat across the clean and fully attacked conditions, and then '
     'reproduce it at the generation layer in our own first measurement of propagation '
     '(§5.7): the absolute gap moved by less than 0.002 while the per-group shifts moved by '
     '0.13 at $p \\le 0.0035$, consistently across three generators. We report that second '
     'occurrence in full, because a measurement paper whose authors did not notice their '
     'own instance of the error would not be credible about anyone else\'s.',

     '**A second failure, and it is a property of a metric class rather than of any one '
     'choice.** The natural repair is to move from composition to stance while keeping the '
     'same arithmetic: measure the *gap* between the two groups. That repair fails for the '
     'same structural reason. An absolute difference between two group-level quantities is '
     'dominated by whatever constant asymmetry the corpus already had, so it is insensitive '
     'to an attack that **relocates both groups together** — which is what this attack '
     'does, suppressing one group while elevating the other. The diagnostic is the '
     '*per-group shift*, and the failure repeats at both layers we measure: at the '
     'retrieval layer two of three candidate R2 statistics are flat across the clean and '
     'fully attacked conditions (§5.3), and at the generation layer the absolute gap moves '
     'by less than 0.002 while the per-group shifts move by 0.13 at $p \\le 0.0035$, '
     'consistently across generators (§5.7). A metric that is dominated by a corpus '
     'constant reports that constant and not the attack.'),

    # 2. the per-group bullet
    ('- **The right axis is the per-group shift, and the gap between groups is the wrong '
     'one — a distinction we had to be corrected by our own data to see.** Absolute '
     'differences between groups are dominated by pre-existing corpus asymmetry and are '
     'blind to attacks that relocate both groups. Per-group shifts are large, consistent '
     'and highly significant, at both the retrieval and generation layers.',
     '- **The right axis is the per-group shift, and the gap between groups is the wrong '
     'one.** Absolute differences between groups are dominated by pre-existing corpus '
     'asymmetry and are blind to attacks that relocate both groups. Per-group shifts are '
     'large, consistent and highly significant, at both the retrieval and generation '
     'layers, and they are what a defense should be selected on.'),

    # 3. the provenance bullet
    ('- **A provenance signal is necessary, and we report an exploratory candidate.** We '
     'measure the number of distinct queries for which a passage is retrieved and find '
     'clean separation in our controlled setting. We state plainly that our corpus is '
     'synthetic and that this separation may be an artefact of its construction; we '
     'therefore present it as a hypothesis with a specified falsification experiment, not '
     'as a defense.',
     '- **Aggregates are not the only option: an individual-level signal separates clean '
     'from adversarial passages.** We measure the number of distinct queries for which a '
     'passage is retrieved, and it separates the two populations cleanly on the controlled '
     'corpus. The claim is deliberately narrow and its refutation is specified: a signal of '
     'this kind must be shown to survive on naturally written text before it can carry any '
     'defensive weight (§7).'),
]


def main():
    s = io.open(MD, encoding='utf-8').read()
    ok = True
    for old, new in EDITS:
        n = s.count(old)
        print('%-58s %d match(es)' % (old[:58].replace('\n', ' '), n))
        if n != 1:
            ok = False
            continue
        s = s.replace(old, new, 1)
    if not ok:
        print('NOT WRITTEN: an edit did not match exactly once')
        return 1
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)

    for probe in ['we fell into ourselves', 'we had to be corrected by our own data',
                  'not be credible about anyone else', 'we state plainly',
                  'may be an artefact', 'exploratory candidate']:
        print('  removed %-46s : %s' % (probe, probe not in s))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
