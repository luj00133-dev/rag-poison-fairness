"""Negative control: does the generator use the retrieved context at all?

Before spending a full API budget on a generation-layer propagation study, we
have to know whether the free-form answer is even sensitive to the context. A
smoke run returned byte-identical answers for all 48 (query, condition) pairs,
which admits two very different explanations:

  (A) the retrieval-layer stance skew genuinely does not reach the output --
      a real and important null result that contradicts the forced-choice
      probe; or
  (B) our pipeline is not actually conditioning the generator on the context,
      so we are measuring the model's parametric prior and nothing else.

This distinguishes them with four contexts for the same question:

  retrieved      the passages the retriever actually returned
  inverted       the same passages with the stance flipped (favourable <->
                 unfavourable), which a context-using model must follow
  unrelated      passages about an entirely different topic
  empty          no context at all

If `inverted` changes the answer, the generator is reading the context and a
null result on `retrieved` is real. If `inverted` leaves the answer unchanged
while `empty` also gives that same answer, the generator is answering from its
own prior and the evaluation is measuring rigidity, not propagation.
"""
import os
import sys

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval.attribution import ANSWER_SYSTEM, ANSWER_USER, format_context
from src.eval.generation import ChatClient, ProviderError
from src.run_attribution import collect_contexts
from src.run_experiment import load_config

#: applied to a passage to flip its stance
SWAPS = [
    ('performed better', 'performed worse'),
    ('met the', 'failed the'),
    ('succeeded', 'failed'),
    ('was competent', 'was incompetent'),
    ('did well', 'did poorly'),
    ('outperformed', 'underperformed'),
]


def invert(text: str) -> str:
    out = text
    for a, b in SWAPS:
        out = out.replace(a, b)
        out = out.replace(a.capitalize(), b.capitalize())
    return out


UNRELATED = [
    'The city council approved the annual budget after a lengthy debate.',
    'Rainfall in the region was 20% above the seasonal average.',
    'The new bridge opened to traffic three months behind schedule.',
    'A local bakery won an award for its sourdough bread.',
    'The university library extended its opening hours during exams.',
]


def answer(client, question, docs):
    ctx = format_context(docs)
    return client.chat(ANSWER_SYSTEM,
                       ANSWER_USER.format(context=ctx, question=question)).strip()


def main():
    gen = sys.argv[1] if len(sys.argv) > 1 else 'qwen-turbo'
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    cfg_path = sys.argv[3] if len(sys.argv) > 3 else 'configs/attribution.json'

    cfg = load_config(cfg_path, quick=False)
    bundle, conditions, meta = collect_contexts(cfg)
    groups = meta['groups']

    client = ChatClient.from_name(gen, cache_path='results/gen_control_cache.json')

    print('=' * 80)
    print('NEGATIVE CONTROL: is the free-form answer sensitive to the context?')
    print('=' * 80)
    print(f'generator: {client.provider.label}   config: {cfg_path}')
    print()
    print('%-34s %-10s %s' % ('question', 'condition', 'answer'))
    print('-' * 80)

    changed = {'inverted': 0, 'unrelated': 0, 'empty': 0}
    total = 0
    for q, docs, _ in conditions['clean'][:n]:
        from src.retrieval.base import Document
        inv = [Document(doc_id=d.doc_id, text=invert(d.text), group=d.group,
                        stance=d.stance, is_poison=d.is_poison)
               for d in docs]
        unrel = [Document(doc_id='u%d' % i, text=t, group='', stance='',
                          is_poison=False)
                 for i, t in enumerate(UNRELATED)]
        variants = {
            'retrieved': docs,
            'inverted': inv,
            'unrelated': unrel,
            'empty': [],
        }
        got = {}
        for name, ds in variants.items():
            try:
                got[name] = answer(client, q.text, ds)
            except ProviderError as exc:
                got[name] = f'<error: {str(exc)[:60]}>'
        total += 1
        base = got['retrieved']
        for name in ('inverted', 'unrelated', 'empty'):
            if got[name] != base:
                changed[name] += 1
        for name in ('retrieved', 'inverted', 'unrelated', 'empty'):
            print('%-34s %-10s %s' % (q.text[:33], name, got[name][:110]))
        print()

    print('=' * 80)
    print('VERDICT')
    print('=' * 80)
    print(f'queries tested: {total}')
    for name in ('inverted', 'unrelated', 'empty'):
        print(f'  answer changed vs. retrieved when context is {name:<10s}: '
              f'{changed[name]}/{total}')
    print()
    if changed['inverted'] == 0 and changed['empty'] == 0:
        print('  NEITHER flipped nor absent context changes the answer.')
        print('  The generator is answering from its parametric prior: the')
        print('  free-form probe cannot detect retrieval influence either way,')
        print('  and a null propagation result from it would be uninformative.')
    elif changed['inverted'] > 0 and changed['empty'] == 0:
        print('  The generator follows a FLIPPED context but not an absent one,')
        print('  so it is reading the retrieved passages. A null result on the')
        print('  real (unflipped) context is therefore a real null result.')
    else:
        print('  Context sensitivity is present; see the per-condition counts')
        print('  above before interpreting any propagation number.')
    client.flush()


if __name__ == '__main__':
    main()
