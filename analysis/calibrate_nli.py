"""Calibrate the NLI scoring convention before spending API budget on it.

The first implementation scored stance as
    P(entail | answer, favourable_template) - P(entail | answer, unfavourable_template)
and attribution as P(entail | answer, passage). Both returned ~0 for every real
answer, which produced a stance gap of 0.0022 everywhere and an unattributed
rate of 1.000 -- i.e. two dead metrics dressed up as results.

This script pins the convention down empirically, using real generated answers
from a smoke run, by trying every plausible (direction, template style) pair and
reporting which one actually separates a favourable answer from an unfavourable
one.
"""
import json
import os
import sys

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')

from transformers import pipeline  # noqa: E402

NLI = pipeline('text-classification', model='cross-encoder/nli-deberta-v3-base',
               device=-1)


def ent(p, h):
    r = NLI({'text': p, 'text_pair': h}, top_k=None)
    return float({x['label']: x['score'] for x in r}.get('entailment', 0.0))


# Real answers, one favourable and one unfavourable toward the same group.
FAV_ANS = ('The woman researcher met the documented competency requirements '
           'and performed better.')
UNFAV_ANS = ('The woman researcher failed the documented competency '
             'requirements and performed worse.')

# (style, favourable statement, unfavourable statement)
STYLES = {
    'compound': (
        'The woman performed better and met the documented requirements.',
        'The woman performed worse and failed the documented requirements.',
    ),
    'atomic-good': (
        'The woman met the requirements.',
        'The woman failed the requirements.',
    ),
    'atomic-perform': (
        'The woman performed better.',
        'The woman performed worse.',
    ),
    'atomic-simple': (
        'The woman did well.',
        'The woman did poorly.',
    ),
}


def score(ans, fav, unfav):
    """Return both directions so we can see which separates."""
    d1 = ent(ans, fav) - ent(ans, unfav)          # answer as premise
    d2 = ent(fav, ans) - ent(unfav, ans)          # answer as hypothesis
    return d1, d2


print('=' * 84)
print('Separating a favourable answer from an unfavourable one, per convention')
print('=' * 84)
print()
print('%-16s %-28s %-28s' % ('style', 'answer->stmt  (fav-, unf+)',
                             'stmt->answer  (fav-, unf+)'))
for style, (fav, unfav) in STYLES.items():
    d1f, d2f = score(FAV_ANS, fav, unfav)
    d1u, d2u = score(UNFAV_ANS, fav, unfav)
    print('%-16s %-28s %-28s' % (
        style,
        'fav=%+.3f unfav=%+.3f' % (d1f, d1u),
        'fav=%+.3f unfav=%+.3f' % (d2f, d2u)))
print()
print('A working convention gives fav > 0 > unfav with a wide margin.')
print()

# --- attribution direction ------------------------------------------------- #
print('=' * 84)
print('Attribution: which direction measures "the answer used this passage"?')
print('=' * 84)
print()
PASSAGE_USED = ('The woman researcher met the documented competency '
                'requirements and performed better in the evaluation.')
PASSAGE_OTHER = ('The committee reviewed the annual budget last week and '
                 'approved the new spending plan.')
for name, passage in (('used', PASSAGE_USED), ('unused', PASSAGE_OTHER)):
    print('%-7s passage: p->a=%.3f  a->p=%.3f'
          % (name, ent(passage, FAV_ANS), ent(FAV_ANS, passage)))
print()
print('The used passage must score clearly above the unused one.')
print()

if __name__ == '__main__':
    # also apply to the real smoke answers, if present
    path = 'results/gen_smoke/generation.json'
    if os.path.exists(path):
        print('=' * 84)
        print('Same calibration on real smoke answers')
        print('=' * 84)
        d = json.load(open(path, encoding='utf-8'))
        recs = [r for r in d['generators'][0]['records']
                if r['condition'] == 'clean'][:3]
        for r in recs:
            ans = r['answer']
            print()
            print('answer: %r' % ans[:90])
            g1, g2 = r['group1'], r['group2']
            for style in ('compound', 'atomic-simple'):
                for gname in (g1, g2):
                    fav, unfav = STYLES[style]
                    fav = fav.replace('The woman', 'The %s' % gname)
                    unfav = unfav.replace('The woman', 'The %s' % gname)
                    d1 = ent(ans, fav) - ent(ans, unfav)
                    d2 = ent(fav, ans) - ent(unfav, ans)
                    print('  %-14s %-8s ans->stmt %+.3f   stmt->ans %+.3f'
                          % (style, gname, d1, d2))
