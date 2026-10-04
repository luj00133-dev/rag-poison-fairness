"""Repair my own regression: restore section 8's reporting-protocol list, in both sources.

The narrative rewrite replaced the conclusion using an end boundary of "the next \\rule in
the file", which in the tex is the rule before Data and Code Availability -- but the nine-item
protocol list sat between the conclusion and that rule, so both files lost it. The conclusion
was then left pointing at "§8", where nothing remained.

The list is the richest statement of the paper's recommendation, so it is restored rather
than replaced by thinner restatements. The other two protocol statements stay: the six items
in 5.8.1 are the adversarial-evaluation rules specific to that section's result, and the
abstract summarises. To avoid three lists that could drift apart, the restored list in
section 8 is the complete one and the conclusion points at it.

Restored in the tex and the markdown, with the body/framing sentences that surrounded it.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

PROTOCOL_TEX = r'''We close with the protocol the results imply. The first four points are about \textbf{measurement validity} --- whether a statistic can see the attack at all --- and the last five about \textbf{adversarial evaluation hygiene}, which is what makes a robustness claim interpretable:

\begin{enumerate}
\def\labelenumi{\arabic{enumi}.}
\tightlist
\item
  \textbf{Measure per-group shifts, not cross-group differences.} An absolute gap between groups is dominated by pre-existing corpus asymmetry and is blind to an attack that relocates both groups together. Report both group-level quantities, and report the change in each.
\item
  \textbf{Report injection as a rate, not a count.} A fixed passage count measures corpus size rather than attack strength.
\item
  \textbf{Report the encoder as a factor.} Susceptibility is a per-checkpoint property that is not monotone in encoder size --- within one family and training recipe, scaling GTE raised text-attack success eight-fold while scaling E5 lowered it to zero. A single-encoder robustness claim reports an unmeasured property of that checkpoint.
\item
  \textbf{Give equivalence bounds for null claims.} ``No effect detected'' and ``no effect'' are different claims, and only the second supports a conclusion about a defense family. Where the per-query difference is identically zero this is conclusive; where it is not, the bound is the honest statement.
\item
  \textbf{State the threat model explicitly, including whether the attacker knows the defense.} A robustness claim without this qualifier is uninterpretable, and the qualifier is what separates the two evaluations in §5.6.
\item
  \textbf{Report adversarial inclusion as a function of attacker strength, not at a single operating point.} One value cannot distinguish a robust defense from one evaluated below its failure threshold. In our sweep every defense fails by \(\lambda \le 2\); a sweep stopping at \(\lambda = 0.25\) would have shown three apparently robust defenses.
\item
  \textbf{Report a utility-preserving baseline.} A defense can achieve low adversarial inclusion trivially by returning fewer or worse passages, which is why we report \texttt{in\_pool\_rate} alongside \texttt{poison@k} throughout.
\item
  \textbf{For a randomised defense, state the distribution and assume it is known.} Report the attacker's optimal response to the expectation rather than to a sample; by Proposition 4, randomisation bounds variance and not the expectation.
\item
  \textbf{For a penalty-based defense, report whether the penalty is computable from public information.} If it is, treat it as a constraint in the attacker's optimisation rather than as an unknown; by Corollary 2 that is the difference between a cost and a barrier.
\end{enumerate}

Point 9 is the one most easily overlooked and, in our experiments, decisive for the defense that looked strongest statically. Point 5 is the one most often omitted in this literature. Points 1--4 are prerequisites for a fairness statistic to be reported at all under adversarial conditions, and points 5--9 for a robustness claim to be credited.

'''

PROTOCOL_MD = '''We close with the protocol the results imply. The first four points are about **measurement validity** — whether a statistic can see the attack at all — and the last five about **adversarial evaluation hygiene**, which is what makes a robustness claim interpretable:

1. **Measure per-group shifts, not cross-group differences.** An absolute gap between groups is dominated by pre-existing corpus asymmetry and is blind to an attack that relocates both groups together. Report both group-level quantities, and report the change in each.
2. **Report injection as a rate, not a count.** A fixed passage count measures corpus size rather than attack strength.
3. **Report the encoder as a factor.** Susceptibility is a per-checkpoint property that is not monotone in encoder size — within one family and training recipe, scaling GTE raised text-attack success eight-fold while scaling E5 lowered it to zero. A single-encoder robustness claim reports an unmeasured property of that checkpoint.
4. **Give equivalence bounds for null claims.** "No effect detected" and "no effect" are different claims, and only the second supports a conclusion about a defense family. Where the per-query difference is identically zero this is conclusive; where it is not, the bound is the honest statement.
5. **State the threat model explicitly, including whether the attacker knows the defense.** A robustness claim without this qualifier is uninterpretable, and the qualifier is what separates the two evaluations in §5.6.
6. **Report adversarial inclusion as a function of attacker strength, not at a single operating point.** One value cannot distinguish a robust defense from one evaluated below its failure threshold. In our sweep every defense fails by $\\lambda \\le 2$; a sweep stopping at $\\lambda = 0.25$ would have shown three apparently robust defenses.
7. **Report a utility-preserving baseline.** A defense can achieve low adversarial inclusion trivially by returning fewer or worse passages, which is why we report `in_pool_rate` alongside `poison@k` throughout.
8. **For a randomised defense, state the distribution and assume it is known.** Report the attacker's optimal response to the expectation rather than to a sample; by Proposition 4, randomisation bounds variance and not the expectation.
9. **For a penalty-based defense, report whether the penalty is computable from public information.** If it is, treat it as a constraint in the attacker's optimisation rather than as an unknown; by Corollary 2 that is the difference between a cost and a barrier.

Point 9 is the one most easily overlooked and, in our experiments, decisive for the defense that looked strongest statically. Point 5 is the one most often omitted in this literature. Points 1–4 are prerequisites for a fairness statistic to be reported at all under adversarial conditions, and points 5–9 for a robustness claim to be credited.

'''

# The list must end section 8, i.e. sit immediately BEFORE the conclusion. Anchoring on the
# last paragraph of section 8 would have been wrong: the paragraph beginning "The open
# problem is the one the framework itself exposes" is inside the CONCLUSION (the rewritten
# conclusion ends on it), so inserting there would have placed the protocol after the
# conclusion instead of before it.
TEX_ANCHOR = '\\section{Conclusion}\\label{conclusion}'
MD_ANCHOR = '## 9. Conclusion'


def main():
    for path, block, anchor in ((TEX, PROTOCOL_TEX, TEX_ANCHOR),
                                (MD, PROTOCOL_MD, MD_ANCHOR)):
        s = io.open(path, encoding='utf-8').read()
        if 'Measure per-group shifts' in s:
            print('%-22s already has the list; skipped' % os.path.basename(path))
            continue
        if anchor not in s:
            print('%-22s ANCHOR FAIL' % os.path.basename(path))
            continue
        s = s.replace(anchor, block + anchor, 1)
        io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
        print('%-22s restored (%d chars) before the conclusion'
              % (os.path.basename(path), len(block)))

    # fix the dangling pointer in the conclusion, both files
    for path in (TEX, MD):
        s = io.open(path, encoding='utf-8').read()
        n = s.count('set out in §8')
        if n:
            s = s.replace('set out in §8', 'set out in §8 and §5.8.1')
            io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
        print('%-22s pointer fixed: %d' % (os.path.basename(path), n))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
