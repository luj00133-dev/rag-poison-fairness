"""Report the full-BBQ generation result, which does not replicate the controlled-corpus effect.

Making the full corpus affordable changed the answer, which is exactly what the
GPU work was for. On the controlled corpus the per-group shift replicates across
four generators spanning three families at d_g1 = -0.13, d_g2 = +0.13, p <= 0.0035
in all six per-group comparisons. On the full BBQ corpus (144 distinct, naturally
written questions) it does not:

    qwen-turbo   d_g1 = +0.0012 (p=0.82)   d_g2 = -0.0014 (p=0.95)   no effect
    qwen-plus    d_g1 = +0.0017 (p=0.78)   d_g2 = -0.0028 (p=0.91)   no effect
    mistral-7b   d_g1 = +0.0435 (p=0.006)  d_g2 = +0.0209 (p=0.030)  3-6x smaller

Three things separate the two settings, and the paper has to say all of them:
  * magnitude: 0.02-0.04 on BBQ against 0.13 on the controlled corpus;
  * sign: on BBQ both groups move *up* for the local model rather than one
    collapsing and the other rising, and for the API models the direction is not
    stable;
  * coverage: 3 of 6 per-group comparisons reach p<0.05 on BBQ, against 6 of 6 on
    the controlled corpus.

The controlled corpus's questions presuppose their own answers ("Who performed
better in the engineering evaluation?"), and the same property already showed up
in the negative control, where the generator ignored an inverted context but
reacted to an unrelated one. So the controlled-corpus effect is best read as a
property of a template corpus, and the general claim does not survive a naturally
written corpus.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

# --- 1. Finding 8 is narrowed and a new table carries the BBQ result --------- #
OLD = ('**Finding 8. The retrieval-layer skew propagates to the generated output, '
       'and it replicates across three independent model families \u2014 including '
       'an open-weight model run locally \u2014 but only when the two groups are '
       'measured separately.**')

NEW = ('**Finding 8. On the controlled corpus the retrieval-layer skew propagates '
       'to the generated output and replicates across three model families, but '
       'it does not survive a naturally written corpus.**')

assert s.count(OLD) == 1, s.count(OLD)
s = s.replace(OLD, NEW)

# --- 2. insert the BBQ replication sub-study after the controlled result ----- #
ANCHOR = '**5.7.1 Two metric failures, and what they were caused by.**'
assert s.count(ANCHOR) == 1, s.count(ANCHOR)

BBQ = '''**5.7.1 The same experiment on a naturally written corpus, which does not replicate it.** The section above is measured on the controlled corpus, whose questions presuppose their own answers. That corpus was rendered affordable to improve: encoder throughput on an RTX 5060 is 171x the CPU rate measured here (1079 against 6.3 documents per second), and we verified that the device changes none of the reported retrieval metrics — all nine attack-by-metric combinations are identical to four decimal places — so the full 17,792-document BBQ corpus could be used instead of a subsample. It supplies 144 distinct, naturally written questions in place of our 16.

**Table 15.** The same generation-stage measurement on the full BBQ corpus. 144 queries, four conditions, paired permutation test against `clean`.

| Generator | Δ gap (absolute) | p | Δ group 1 | p | Δ group 2 | p |
|---|---|---|---|---|---|---|
| qwen-turbo | −0.0091 | 0.41 | +0.0012 | 0.82 | −0.0014 | 0.95 |
| qwen-plus | −0.0075 | 0.52 | +0.0017 | 0.78 | −0.0028 | 0.91 |
| **mistral-7b** | **+0.0420** | **0.006** | **+0.0435** | **0.006** | **+0.0209** | **0.030** |

The effect does not carry over, and three separate things distinguish the two settings:

- **Magnitude.** 0.02–0.04 on BBQ against 0.13 on the controlled corpus.
- **Sign.** On BBQ the local model moves *both* groups upward, rather than one collapsing while the other rises. The two API generators show no effect at all, and what little movement there is points the other way.
- **Coverage.** Three of the six per-group comparisons reach $p < 0.05$ on BBQ, against six of six on the controlled corpus.

**We therefore narrow the propagation claim rather than the corpus.** Finding 8 holds for a template corpus whose questions presuppose their answers, which is what the controlled corpus is; it does not hold for the naturally written benchmark. The negative control in §8 pointed the same way before this experiment existed: on the controlled corpus the generator ignored a context whose stance had been *inverted* while reacting to a completely unrelated one, so its answers there are determined by the question's framing rather than by the evidence. A corpus built that way can register an effect that a natural corpus does not, and the honest reading is that the retrieval-layer skew is consequential **when the generator is genuinely weighing the retrieved evidence**, which our template corpus cannot guarantee and BBQ can measure.

This is the second finding in this paper that a wider evaluation narrowed, and both narrowed in the same direction: the controlled corpus supports stronger conclusions than the natural one, and we now treat that asymmetry as a property of the instrument rather than of the phenomenon.

**5.7.2 Two metric failures, and what they were caused by.**'''

s = s.replace(ANCHOR, BBQ)
print('5.7.1 added; Finding 8 narrowed')

io.open(P, 'w', encoding='utf-8').write(s)
print('paper length: %d chars' % len(s))
