"""Add the local open-weight generator to Paper A's generation table.

The table reported three API generators from two families, which left the paper
exposed to the objection that a propagation result measured only on hosted models
says nothing about the open-weight systems most RAG deployments run.
Mistral-7B-Instruct (4-bit, locally on an RTX 5060, deterministic across repeated
greedy calls) is a third family and replicates the per-group shift at the same
magnitude.

Two corrections to the first attempt at this script, both from reading the file
rather than assuming:
  * the generation table is **Table 11** after the body renumbering, not Table 14;
  * its cells use U+2212 MINUS SIGN, not an ASCII hyphen, so a literal match built
    with '-' silently fails. Rows are matched by their leading label instead.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()
lines = s.split('\n')

# --- 1. append a row after the qwen-max row ---------------------------------- #
idx = next(i for i, l in enumerate(lines) if l.startswith('| qwen-max'))
new_row = ('| **mistral-7b** (local, open weights) | +0.0025 | 0.42 | '
           '**\u22120.1297** | **0.0001** | **+0.1322** | **<0.0001** |')
lines.insert(idx + 1, new_row)
s = '\n'.join(lines)
print('row added after line %d' % (idx + 1))

# --- 2. caption -------------------------------------------------------------- #
OLD_CAP = ('**Table 11.** Generation-layer stance, entailment-scored, three '
           'generators. Controlled corpus, GTE-base retrieval, ')
NEW_CAP = ('**Table 11.** Generation-layer stance, entailment-scored, four '
           'generators spanning three model families. Controlled corpus, '
           'GTE-base retrieval, ')
assert s.count(OLD_CAP) == 1, s.count(OLD_CAP)
s = s.replace(OLD_CAP, NEW_CAP)
print('caption updated')

# --- 3. findings and prose --------------------------------------------------- #
SUBS = [
    ('**Finding 8. The retrieval-layer skew propagates to the generated output, '
     'and it replicates across three independent generators \u2014 but only when '
     'the two groups are measured separately.**',
     '**Finding 8. The retrieval-layer skew propagates to the generated output, '
     'and it replicates across three independent model families \u2014 including '
     'an open-weight model run locally \u2014 but only when the two groups are '
     'measured separately.**'),
    ('across three generators from two model families. The per-group shifts are '
     'large, consistent in sign, and highly significant everywhere:',
     'across four generators spanning three model families, one of them '
     '(Mistral-7B) open-weight and served locally rather than by an API, so that '
     'the result does not rest on hosted models alone. The per-group shifts are '
     'large, consistent in sign, and highly significant everywhere:'),
]
for old, new in SUBS:
    n = s.count(old)
    assert n == 1, (n, old[:60])
    s = s.replace(old, new)
    print('prose updated: %s' % old[:46])

io.open(P, 'w', encoding='utf-8').write(s)

# verify
import re
print()
print('generators in the table:')
for m in re.finditer(r'^\| (?:\*\*)?([a-z0-9\-\.]+)(?:\*\*)?[^|]*\|',
                     s[s.find('**Table 11.**'):s.find('**Table 11.**') + 2000],
                     re.M):
    print('   %s' % m.group(1))
