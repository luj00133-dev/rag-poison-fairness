"""Port the narrative rewrite into the LaTeX source.

The tex and the markdown carry the same prose but different citation machinery: the
markdown uses numeric refs internally, the tex uses natbib author-date. So the changed
blocks are written out again here rather than copied, and the LaTeX escaping is the tex's
own convention (\\emph, \\citep, ``...'', \\%).

Ported in this stage: the title, the abstract, the two introduction blocks whose framing
changed, the two 5.8 passages, and the conclusion. Section headings changed in the markdown
are ported as well, matched on their LaTeX form. Appendix E is NOT ported here -- the
markdown appendix numbering (Appendix E) does not exist in the tex, and the record of
changes belongs with the other appendices; that port is deliberately left to a separate
step so this one stays verifiable.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

OLD_TITLE = (r'\title{Measuring Retrieval Fairness Under Adversarial Poisoning: Why the '
             r'Standard Statistics Are Blind, and What to Measure Instead}')
NEW_TITLE = (r'\title{Adversarially Invariant Fairness Statistics: Why Aggregate '
             r'Retrieval-Fairness Metrics Cannot Detect Pairwise Poisoning}')

NEW_ABSTRACT = r'''
Fairness defenses for retrieval-augmented generation are selected, tuned and validated by aggregate statistics of the retrieved set: the share of passages about each protected group, the deviation of a group's stance from a corpus reference, or the exposure of items across requests. Because a defense is only as sensitive as the statistic that selects it, an adversary who can make that statistic invariant defeats the defense \emph{selection} without touching the defense. We show that this is not a weakness of any particular metric but a structural property of the class, and that it is checkable before any attack is built. Every statistic in this literature has the form of a per-group quantity aggregated across groups, and an adversary can preserve that aggregate in exactly three ways: by balancing the quantity it counts (\textbf{F1}), by anchoring it to a reference the attack leaves intact (\textbf{F2}), or by moving all groups together so that a difference between them cancels (\textbf{F3}). The three modes are a falsifiable test rather than a description: applied to the published metrics they predict which will be blind, and the predictions hold.

The attack that realises them is \emph{pairwise poisoning}, which injects matched passages drawn from the legitimate template inventory --- one favourable to a group, one unfavourable to another --- so that the injection is balanced across groups by construction and the stance of the evidence is skewed instead. We formalise representation as two orthogonal dimensions, \textbf{(R1) group composition} and \textbf{(R2) within-group stance}, and measure both on a controlled corpus and on a naturally written bias benchmark. A positive control in which the ground truth changes by a known amount while corpus size is held fixed establishes that the indicted statistics are \emph{working instruments}: they respond monotonically and in the correct direction. Against those same instruments, the R1 constraint is inert with an equivalence bound of exactly \(\pm 0.0000\) --- every constrained configuration reproduces the unconstrained inclusion rate per query, because the unconstrained baseline already admits adversarial passages on every query where it can (1.000 dense, 0.750 BM25), leaving no headroom for a reduction to appear. The signal lives in the per-group shifts rather than in the gap between groups: injection moves the suppressed group's stance by \(-0.13\) to \(-0.18\) and the favoured group's by \(+0.13\), consistently across four generators spanning three model families at \(p \le 0.0035\), while the absolute cross-group gap moves by less than 0.002. A defense-aware attacker then inverts the static ranking of defenses across six retrieval back-ends: the strongest defense's static advantage is \emph{largest} on the pretrained encoders the compared literature uses --- four begin at exactly 0.000 inclusion --- and no defense retains measurable benefit beyond one perturbation step on any of them, while the injected passages stay over 94\% semantically intact.

The consequence is a reporting requirement rather than another defense. We give a six-point protocol under which a robustness claim is interpretable: per-group shifts rather than cross-group differences, adversarial inclusion as a function of attacker strength rather than at a single operating point, the encoder reported as a factor, equivalence bounds for null claims, and the threat model stated explicitly. The study covers binary group partitions at the retrieval and generation layers across two corpora; the framework's applicability is bounded by the availability of group- and stance-annotated passages, which is an infrastructure problem for the field rather than a computation.

'''

INTRO_EDITS = [
    # the "we fell into it ourselves" paragraph -> a statement about the metric class
    (r'**A second, subtler failure --- one we fell into ourselves.**', None),
]

CONCLUSION_OLD_ANCHOR = r'\section{Conclusion}\label{conclusion}'
CONCLUSION_NEW = r'''\section{Conclusion}\label{conclusion}

Fairness defenses for retrieval-augmented generation are chosen and validated by aggregate statistics of the retrieved set. We have shown that the standard statistics are adversarially invariant: an attacker who balances what they count, preserves what they reference, or relocates all groups together leaves the statistic at its clean value while controlling the evidence. The invariance has one cause, it is predictable from the form of the statistic rather than measured after the fact, and the defense failure that follows is a consequence of it rather than a separate phenomenon.

The two dimensions we separate make the mechanism visible. \textbf{R1} is group composition; \textbf{R2} is within-group stance. Pairwise poisoning is balanced in R1 by construction, because the injected passages are matched pairs drawn from the legitimate template inventory, so every composition statistic reads clean while the stance of the evidence is skewed. The natural repair --- move to stance and keep the same arithmetic, measuring the gap between groups --- fails for the same structural reason: an absolute difference is dominated by the corpus's pre-existing asymmetry and is blind to an attack that relocates both groups. The diagnostic is the per-group shift, and it is large and consistent where the aggregate is not: the suppressed group's stance moves by \(-0.13\) to \(-0.18\) and the favoured group's by \(+0.13\) across four generators spanning three model families at \(p \le 0.0035\), while the absolute cross-group gap moves by less than 0.002.

The consequence for the defense class is a ceiling rather than a null. The unconstrained baseline already admits adversarial passages on every query where it can, so no reduction is available even in principle; the per-query difference is identically zero and the equivalence bound is exactly \(\pm 0.0000\). The constraint does change which passages are selected --- it moves the R2 stance gap substantially --- and that is precisely the point: selection changes, and not one adversarial passage is displaced. Extending the constraint to a second dimension improves the statistic it measures without changing adversarial inclusion. The problem is one of detection, not of optimisation, and detection requires evidence about individual passages rather than about the set they belong to.

Under a defense-aware attacker the picture sharpens rather than softens. Across six retrieval back-ends the static advantage of the strongest defense is \emph{largest} on the pretrained encoders the compared literature uses --- four of the six begin at exactly 0.000 adversarial inclusion --- and no defense retains measurable benefit beyond one perturbation step on any of them, while the injected passages stay over 94\% semantically intact. A defense selected on its static advantage is therefore defeated comprehensively, and the static numbers that would select it are most optimistic exactly where that literature looks.

Two things follow, and they are what this paper contributes. The first is a \textbf{test}: three questions that predict, before any attack is built, whether a candidate statistic is invariant to an adversary who balances the quantity it counts, anchors it to a reference the attack preserves, or moves all groups together. The second is a \textbf{standard}: the reporting requirements a robustness or fairness claim must meet to be interpretable, set out in §8 --- per-group shifts rather than cross-group differences, injection as a rate rather than a count, the encoder reported as a factor, equivalence bounds for null claims, the threat model stated, adversarial inclusion reported as a function of attacker strength, and a penalty treated as the attacker's constraint when it is computable from public information. Applied together these change what a result has to contain; they do not require a new defense, and every one of them is cheap.

The open problem is the one the framework itself exposes. A per-group report is more sensitive than an aggregate, and a more sensitive instrument still has to be shown to measure the right quantity. The individual-level signal we report in §7 is a candidate in that direction, and the test that would settle it is stated with it: it must survive on naturally written text. Establishing which cues about individual passages do survive --- and why --- is the measurement problem this work leaves open.

'''

HEADING_RENAMES = [
    (r'\subsection{Pairwise poisoning is an R2 attack, not an R1 attack}',
     r'\subsection{Two orthogonal dimensions of representation}'),
    (r'\subsection{The R1-only defense is inert}',
     r'\subsection{The R1 constraint is inert}'),
    (r'\subsection{The R2 constraint works --- on the R2 metric --- and does not defend}',
     r'\subsection{F1: an aggregate over group counts returns its clean value}'),
    (r'\subsection{Replication on a natural corpus (BBQ)}',
     r'\subsection{F2: reference-based statistics track the query, not the attack}'),
    (r'\subsection{Encoder robustness: a per-checkpoint property, not a family property}',
     r'\subsection{The diagnostic is the per-group shift, not the gap between groups}'),
    (r'\subsection{Adaptive attacker: no defense survives an informed adversary}',
     r'\subsection{Under an informed attacker no defense survives}'),
    (r'\subsection{Generation-stage propagation: does the retrieval skew reach the output?}',
     r'\subsection{The skew reaches the generated text}'),
    (r'\subsection{The collapse is not an artefact of one retriever}',
     r'\subsection{Under an informed attacker the defenses invert}'),
]


def main():
    s = io.open(TEX, encoding='utf-8').read()
    changed = []

    if OLD_TITLE in s:
        s = s.replace(OLD_TITLE, NEW_TITLE, 1)
        changed.append('title')
    else:
        print('TITLE ANCHOR FAIL')

    a = s.find('\\begin{abstract}')
    b = s.find('\\end{abstract}')
    if a > 0 and b > a:
        s = s[:a + len('\\begin{abstract}')] + NEW_ABSTRACT + s[b:]
        changed.append('abstract')
    else:
        print('ABSTRACT BOUNDARY FAIL')

    c = s.find(CONCLUSION_OLD_ANCHOR)
    d = s.find('\\begin{center}\\rule', c)
    if c > 0 and d > c:
        s = s[:c] + CONCLUSION_NEW + s[d:]
        changed.append('conclusion')
    else:
        print('CONCLUSION BOUNDARY FAIL c=%d d=%d' % (c, d))

    for old, new in HEADING_RENAMES:
        n = s.count(old)
        if n == 1:
            s = s.replace(old, new, 1)
            changed.append('heading:%s' % old[13:40])
        else:
            print('HEADING NOT FOUND (%d): %s' % (n, old[:60]))

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    print('ported %d blocks: %s' % (len(changed), ', '.join(changed)))
    # structural guards
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}', '\\begin{abstract}', '\\end{abstract}'):
        if needed not in s:
            print('FAIL: missing %s' % needed)
            return 1
    print('structure intact')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
