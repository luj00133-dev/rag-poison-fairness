"""Rewrite Limitation 6.

It currently says the generation-stage evaluation is preliminary, on a single
generator, with an unresolved query-diversity problem. All three statements are
now out of date: the evaluation covers four generators spanning three families, the
query-diversity problem was solved by using the full BBQ corpus, and the outcome of
solving it was a partial failure to replicate that the limitation must now state
plainly rather than as a caveat.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

start = s.find('6. **The generation-stage evaluation is preliminary,')
assert start != -1
end = s.find('\n\n', start)
assert end > start
old = s[start:end]

NEW = (
    '6. **The generation-stage evaluation is now multi-generator and multi-corpus, '
    'and the wider evaluation weakened its conclusion.** \u00a75.7 reports four '
    'generators spanning three model families (API-served Qwen and DeepSeek, plus '
    'open-weight Mistral-7B run locally in 4-bit on an RTX 5060), scored by '
    'entailment rather than by a prompted judge, with paired permutation tests and '
    'bootstrap intervals. Two limits remain, and the second is the important one. '
    '(i) *Retrieval conditions are measured on one backbone* (GTE-base); the '
    'generation-stage comparison holds retrieval fixed, so the encoder-dependence '
    'documented in \u00a75.5 is not varied here. (ii) *The effect does not '
    'generalise to a naturally written corpus.* On the controlled corpus the '
    'per-group shift is large and replicates across all four generators '
    '($p \\le 0.0035$ in six of six per-group comparisons). On the full BBQ '
    'benchmark, with 144 distinct naturally written questions, two of three '
    'generators show no measurable shift and the third shows one three to six '
    'times smaller with a different signature. We therefore scope the propagation '
    'claim to template corpora and withdraw the general form. This is not a '
    'power problem: BBQ supplies nine times as many distinct questions as the '
    'controlled corpus, and the two API generators give null results there with '
    'confidence intervals that exclude the controlled-corpus effect size. The '
    'negative control in \u00a78 explains the asymmetry \u2014 on the controlled '
    'corpus the generator ignores an inverted context, so its answers are driven by '
    'the question\'s framing rather than by the evidence \u2014 and it is the '
    'reason we report the controlled-corpus result as scoped rather than as '
    'representative. A corpus whose questions presuppose their answers can produce '
    'a propagation effect that a natural corpus does not.'
)

s = s[:start] + NEW + s[end:]
io.open(P, 'w', encoding='utf-8').write(s)
print('Limitation 6 rewritten (%d -> %d chars)' % (len(old), len(NEW)))
print()
print('paper length: %d chars' % len(s))
