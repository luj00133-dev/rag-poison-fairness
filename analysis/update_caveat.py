"""Update the discussion's caveat, which described the BBQ null as a real one.

The passage currently reads as a warning that the per-group report is sensitive to an
instrument that manufactures effects, using the controlled-versus-natural contrast as
the example. That contrast has been resolved the other way: the natural-corpus null
came from a probe that could not register stance, not from an absent effect. The
warning is still worth making -- sensitivity is not validity -- but it now needs a
real example rather than one that turned out to be an instrument artefact, and the
strongest available example is the free-form probe itself.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

OLD = ('**A caveat we insist on.** The per-group report is more sensitive, and '
       'sensitivity is not validity. §5.7 also shows that on the controlled corpus '
       'the per-group shift is large and replicates across four generators while on '
       'the naturally written corpus it largely disappears, and our negative control '
       'attributes that to the controlled corpus\'s questions presupposing their '
       'answers. A more sensitive statistic will report a larger effect on an '
       'instrument that manufactures one. Sensitivity without a control is how a '
       'measurement paper produces a finding that does not exist, and we report both '
       'outcomes rather than the favourable one.')

NEW = ('**A caveat we insist on, and a worked example of it from this paper.** The '
       'per-group report is more sensitive than an aggregate, and sensitivity is not '
       'validity. The clearest example is our own: the free-form probe reports a '
       'large, replicated per-group shift on the controlled corpus and nothing on the '
       'naturally written one, and it would have been easy to publish that as a '
       'finding about corpora. It is not — the probe scores answers that take no '
       'position in 99.0% of cases on natural text, so it was structurally incapable '
       'of reporting the effect that a commitment-forcing probe then found there. A '
       'sensitive statistic on an instrument that manufactures commitment will report '
       'an effect on an instrument that manufactures one; a *insensitive* statistic '
       'on an instrument that suppresses commitment will report a null that does not '
       'exist. We hit the second case, and the control that caught it was measuring '
       'commitment rather than trusting the margin. We therefore report both probes '
       'and both corpora, and treat the disagreement between them as the result.')

if s.count(OLD) != 1:
    print('anchor not found verbatim (%d); searching by prefix' % s.count(OLD))
    i = s.find('**A caveat we insist on.**')
    assert i != -1
    j = s.find('\n\n', i)
    OLD = s[i:j]
    NEW = NEW
    s = s[:i] + NEW + s[j:]
else:
    s = s.replace(OLD, NEW)

io.open(P, 'w', encoding='utf-8').write(s)
print('discussion caveat updated with a real example')
print('paper length: %d chars' % len(s))
