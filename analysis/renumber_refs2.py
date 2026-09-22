"""Second pass: the remaining §5.6 references now belong to the generation-stage
section, which moved to §5.7."""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

subs = [
    ('and \u00a75.6 the generation-stage propagation check',
     'and \u00a75.6\u2013\u00a75.7 the encoder-scale and generation-stage checks'),
    ('the self-report probe that failed in \u00a75.6',
     'the self-report probe that failed in \u00a75.7'),
    ('\u00a75.6 additionally requires a DeepSeek API key',
     '\u00a75.7 additionally requires a DeepSeek API key'),
    ('The key used for the \u00a75.6 runs is rotated and revoked',
     'The key used for the \u00a75.7 runs is rotated and revoked'),
    ('\u00a75.5 adds the backbone alignment against two real semantic encoders',
     '\u00a75.5 adds the backbone alignment against five further retrievers, and '
     '\u00a75.6 the encoder-scale check'),
]
for old, new in subs:
    n = s.count(old)
    s = s.replace(old, new)
    print('%d replacement(s): %s' % (n, old[:56]))

io.open(P, 'w', encoding='utf-8').write(s)
print()
left = re.findall(r'\u00a75\.6[^\d]', s)
print('remaining §5.6 references:', len(left))
print('remaining §5.7 references:', len(re.findall(r'\u00a75\.7', s)))
