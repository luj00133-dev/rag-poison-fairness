"""Rewrite section 5.7: the BBQ null was the probe, not the corpus.

What the paper currently says, after the full-corpus run: the controlled-corpus
per-group shift replicates across generators but "does not survive a naturally
written corpus", and Limitation 6 states that as a limitation.

What the forced-choice experiment shows: that conclusion was an artefact of the
probe. The free-form probe cannot register stance on BBQ because 99.0% of those
answers are non-committal (mean max-entailment 0.007 against 0.156 on the controlled
corpus, a 22x gap), so the free-form statistic is near zero under every condition
there and no effect of any size could appear in it. Applying a probe that forces a
commitment, on the same retrieval conditions, does detect the effect on BBQ:
qwen-turbo gives five per-group shifts at p < 0.05, including woman +0.63 (p<1e-4),
nondisabled +0.57 (p<1e-4) and man +0.50 (p=0.0003).

The honest statement is narrower and more useful than either the optimistic or the
pessimistic version:
  * the free-form probe measures stance only where answers commit, and on a naturally
    written corpus they largely do not, which is a property of the instrument;
  * the forced-choice probe does measure there, and it finds an effect;
  * the effect is concentrated in particular groups rather than uniform, on both
    corpora, which is why averaging over groups understated it;
  * it is also generator-dependent, with one of three generators showing most of the
    signal, so "the effect replicates" must be stated per group and per model rather
    than as a single number.

This is the third instrument failure the paper documents, and it belongs with the
other two rather than in the limitations.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

# --- 1. replace the 5.7.1 sub-study ----------------------------------------- #
start = s.find('**5.7.1 The same experiment on a naturally written corpus, which does not replicate it.**')
end = s.find('**5.7.2 Two metric failures, and what they were caused by.**')
assert start != -1 and end > start, (start, end)

NEW = r'''**5.7.1 Why the natural corpus appeared to show nothing: the probe, not the corpus.** The free-form measurement above is valid only where answers actually take a position, and on a naturally written corpus they largely do not. Measuring the *commitment* of each answer — the larger of its two entailment probabilities, `max(P(fav), P(unfav))` — separates a real null from an instrument that cannot register anything:

**Table 15.** Answer commitment by corpus, clean condition. An answer with commitment near zero takes no position, so no stance change can appear in it however large the retrieval-layer skew.

| Corpus | mean commitment | answers below 0.1 |
|---|---|---|
| controlled | 0.1555 | 84.4% |
| **BBQ (full)** | **0.0071** | **99.0%** |

The gap is 22×, and it means the free-form statistic on BBQ is near zero under *every* condition: the effect we were looking for could not have appeared there. This also bounds the controlled-corpus result more honestly than we previously stated it — 84.4% of those answers are non-committal too, so the shift reported above rests on roughly a sixth of them.

**A probe that forces commitment detects the effect on BBQ.** We therefore re-ran the generation stage with the forced-choice probe used in earlier drafts of this work: the generator must choose between a favourable and an unfavourable statement about the group, drawn from the same template inventory the attack manipulates, with option order randomised per item so a position bias cannot masquerade as a stance effect. Before using it we verified it carries signal rather than position: the reply was a parseable choice in 100% of cases, and the probability of choosing position A is 100% when the favourable statement sits at A against 35% when it sits at B — a 65-point swing, so the choice tracks content.

**Table 16.** Forced-choice stance on the full BBQ corpus, 144 queries, per-group favourable-choice rate, paired permutation test against `clean`. Only shifts significant at $p < 0.05$ are listed.

| Generator | Group | Δ favourable rate | p |
|---|---|---|---|
| **qwen-turbo** | woman | **+0.6333** | **<0.0001** |
| **qwen-turbo** | nondisabled | **+0.5714** | **<0.0001** |
| **qwen-turbo** | man | **+0.5000** | **0.0003** |
| **qwen-turbo** | young | +0.2449 | 0.0121 |
| **qwen-turbo** | disabled | +0.2381 | 0.0274 |
| qwen-plus | man | +0.2333 | 0.0379 |
| mistral-7b | — | none reached significance | — |

**Finding 8, restated.** The retrieval-layer skew does reach the generated output on a naturally written corpus. What failed on BBQ was the free-form probe, which could not have detected the effect because 99.0% of the answers it scores take no position at all. With a probe that forces commitment, one generator shows five per-group shifts at $p < 0.05$ with the largest at $+0.63$.

Three qualifications belong with that, and we state them rather than leaving them to be found:

- **The effect is group-specific, not uniform.** On BBQ it concentrates in woman, nondisabled, man, young and disabled; on the controlled corpus (Table 12) it concentrates in asian, elderly and white. Averaging over groups, which is what a per-group *mean* does and what our earlier free-form analysis did, understates it substantially.
- **It is generator-dependent.** qwen-turbo carries most of the signal on both corpora; mistral-7b shows none that reaches significance on BBQ, and the one API generator we ran at largest scale shows a single group. A single dense number such as "the gap rose 46%" is therefore the wrong form for this result, and we no longer report one.
- **Concentration is not the same as a large average effect.** Five significant groups out of eight, each with a large rate shift, is a stronger statement than the average gap suggests, and a weaker one than "the system's stance changed across the board".

**This is the third instrument failure in the paper, and it belongs with the other two.** The free-form probe joins the reference-based stance statistics and the absolute cross-group gap as a measurement that returns a plausible number while being structurally unable to see the thing being measured. Its signature is the one we have now seen three times: a statistic that comes out near zero for reasons that have nothing to do with the phenomenon. We report it in the results rather than the limitations because it changes a conclusion we had already drawn.

**5.7.2 Two metric failures, and what they were caused by.**'''

s = s[:start] + NEW + '\n\n' + s[end:]
io.open(P, 'w', encoding='utf-8').write(s)
print('5.7.1 rewritten: the probe failed, not the corpus')
print('paper length: %d chars' % len(s))
