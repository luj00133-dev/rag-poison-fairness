"""Correct the abstract and Limitation 6, which still carry the retracted claim.

Both currently say the propagation effect does not generalise to a naturally written
corpus and that the general claim is withdrawn. The forced-choice experiment
overturns that: the effect is there on BBQ, and what failed was the free-form probe,
which could not have detected it because 99.0% of the answers it scores take no
position at all.

Leaving the retraction in place would be the mirror image of the error it was
correcting -- reporting a null that the instrument could not have avoided. So both
passages are rewritten to say what happened: the probe failed, the effect is present
on both corpora, it is group-specific and generator-dependent, and the free-form
probe joins the other two instrument failures the paper documents.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

# --- abstract ---------------------------------------------------------------- #
OLD_ABS = ('**That effect does not survive a naturally written corpus, and we '
           'report the failure rather than the controlled-corpus number alone**: '
           'on the full BBQ benchmark, 144 distinct naturally written questions, '
           'two of three generators show no measurable shift at all and the third '
           'shows one three to six times smaller with a different group-wise '
           'signature. The propagation claim is therefore scoped to a template '
           'corpus whose questions presuppose their answers — a property our own '
           'negative control had already exposed — and the general claim is '
           'withdrawn.')

NEW_ABS = ('**On a naturally written corpus the same effect is present, but only a '
           'probe that forces a commitment can see it.** The free-form measurement '
           'returns nothing on the full BBQ benchmark, and the reason is the '
           'instrument rather than the phenomenon: 99.0% of the answers it scores '
           'take no position at all (mean commitment 0.007 against 0.156 on the '
           'controlled corpus), so no effect of any size could appear in it. '
           'Replacing it with a forced-choice probe on identical retrieval '
           'conditions detects the effect — five per-group shifts at $p < 0.05$ for '
           'one generator, the largest at $+0.63$ — and shows that it is '
           '**group-specific and generator-dependent**, which is why reporting a '
           'single averaged gap understated it. This free-form probe is the third '
           'instrument failure the paper documents.')

assert s.count(OLD_ABS) == 1, s.count(OLD_ABS)
s = s.replace(OLD_ABS, NEW_ABS)
print('abstract corrected')

# --- Limitation 6 ------------------------------------------------------------ #
start = s.find('6. **The generation-stage evaluation is now multi-generator')
assert start != -1
end = s.find('\n\n', start)
assert end > start

NEW_LIM = (
    '6. **The generation-stage evaluation is multi-generator and multi-probe, and '
    'the probes disagree in a way that is itself a result.** \u00a75.7 reports four '
    'generators spanning three model families (API-served Qwen and DeepSeek, plus '
    'open-weight Mistral-7B run locally in 4-bit on an RTX 5060), two corpora, and '
    'two probes: free-form answers scored by entailment, and a forced-choice probe '
    'scored by the choice it forces. Three limits remain. (i) *Retrieval conditions '
    'are measured on one backbone* (GTE-base), held fixed across the generation-stage '
    'comparison, so the encoder-dependence of \u00a75.5 is not varied here. (ii) *The '
    'two probes support different conclusions, and the freer one is the weaker.* '
    'Free-form answers commit to a position in only 15.6% of cases on the controlled '
    'corpus and 1.0% on BBQ, so that probe is near-blind on natural text; the '
    'forced-choice probe detects the effect on both. We report both rather than the '
    'favourable one, because a probe that manufactures commitment can also '
    'manufacture an effect, and \u00a75.7.1 records the checks we ran to establish '
    'that the forced choice tracks statement content rather than option position '
    '(100% versus 35% agreement with the placement of the favourable statement). '
    '(iii) *The effect is generator-dependent.* One of three generators carries most '
    'of the signal on both corpora, a second shows a single group on BBQ, and the '
    'third shows none reaching significance there. A result of this shape is not '
    'summarisable as one number, and we no longer report one. Whether a larger '
    'generator would show more or less is an open question: we ran one open-weight '
    'model and three API models, and the scale of the API models is not controlled.'
)

s = s[:start] + NEW_LIM + s[end:]
io.open(P, 'w', encoding='utf-8').write(s)
print('Limitation 6 corrected (%d -> %d chars)' % (end - start, len(NEW_LIM)))
print()
print('paper length: %d chars' % len(s))
