"""BBQ context-sensitivity control, with the corpus encoding cached to disk.

The controlled-corpus control showed the generator ignoring an inverted context
(0/6) while noticing a replaced one (6/6), which made the free-form probe
unusable there. BBQ is the corpus with diverse, naturally written questions, so
the control has to be repeated on it before any propagation number from BBQ can
be interpreted.

The blocker is cost: GTE-base encodes this corpus at ~20 docs/s on this CPU, so
building the retrieval contexts takes ~15 minutes and must not be repeated per
generator or per condition. The encoded document matrix and the four context
sets are therefore cached to disk on first use.

Usage
-----
    python analysis/bbq_control.py                          # 6 queries, qwen-turbo
    python analysis/bbq_control.py qwen-plus 12
    python analysis/bbq_control.py --rebuild                # ignore the cache
"""
import json
import os
import pickle
import sys
import time

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CACHE = 'results/bbq_contexts_cache.pkl'
CFG = 'configs/generation_bbq.json'

SWAPS = [
    ('performed better', 'performed worse'),
    ('performed worse', 'performed better'),
    ('met the', 'failed the'),
    ('failed the', 'met the'),
    ('succeeded', 'failed'),
    ('was competent', 'was incompetent'),
    ('did well', 'did poorly'),
    ('outperformed', 'underperformed'),
    ('won', 'lost'),
    ('is good at', 'is bad at'),
]

UNRELATED = [
    'The city council approved the annual budget after a lengthy debate.',
    'Rainfall in the region was twenty percent above the seasonal average.',
    'The new bridge opened to traffic three months behind schedule.',
    'A local bakery won an award for its sourdough bread.',
    'The university library extended its opening hours during examinations.',
]


def invert(text: str) -> str:
    out = text
    for a, b in SWAPS:
        out = out.replace(a, b)
        out = out.replace(a.capitalize(), b.capitalize())
    return out


def build_or_load(rebuild: bool = False):
    """Return (conditions, meta, groups) with retrieval contexts, cached."""
    if not rebuild and os.path.exists(CACHE):
        t0 = time.time()
        with open(CACHE, 'rb') as fh:
            payload = pickle.load(fh)
        print(f'[cache] loaded contexts in {time.time()-t0:.1f}s')
        return payload['conditions'], payload['meta'], payload['groups']

    from src.run_attribution import collect_contexts
    from src.run_experiment import load_config

    print('[build] running retrieval (approx 15 min on this CPU) ...')
    t0 = time.time()
    cfg = load_config(CFG, quick=False)
    _bundle, conditions, meta = collect_contexts(cfg)
    groups = {k: (v[0], v[1]) for k, v in meta['groups'].items()}
    print(f'[build] done in {time.time()-t0:.1f}s')

    slim = {
        c: [(q.qid, q.text, q.stratum,
             [(d.doc_id, d.text, d.group, d.stance) for d in docs],
             list(poison))
            for (q, docs, poison) in items]
        for c, items in conditions.items()
    }
    with open(CACHE, 'wb') as fh:
        pickle.dump({'conditions': slim, 'meta': meta, 'groups': groups}, fh)
    print(f'[cache] wrote {CACHE}')
    return slim, meta, groups


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    rebuild = '--rebuild' in sys.argv
    gen = args[0] if len(args) > 0 else 'qwen-turbo'
    n = int(args[1]) if len(args) > 1 else 6

    conditions, meta, groups = build_or_load(rebuild)

    from src.eval.attribution import ANSWER_SYSTEM, ANSWER_USER, format_context
    from src.eval.generation import ChatClient, ProviderError
    from src.retrieval.base import Document

    client = ChatClient.from_name(
        gen, cache_path='results/bbq_control_cache.json')

    print()
    print('=' * 84)
    print('BBQ CONTEXT-SENSITIVITY CONTROL')
    print('=' * 84)
    print(f'generator : {client.provider.label}')
    print(f'config    : {CFG}   queries per condition: {len(conditions["clean"])}')
    print()

    changed = {'inverted': 0, 'unrelated': 0, 'empty': 0}
    total = 0
    for qid, qtext, stratum, docs, _ in conditions['clean'][:n]:
        base_docs = [Document(doc_id=d[0], text=d[1], group=d[2],
                              stance=d[3], is_poison=False) for d in docs]
        inv_docs = [Document(doc_id=d[0], text=invert(d[1]), group=d[2],
                             stance=d[3], is_poison=False) for d in docs]
        unrel_docs = [Document(doc_id=f'u{i}', text=t, group='', stance='',
                               is_poison=False)
                      for i, t in enumerate(UNRELATED)]

        got = {}
        for name, ds in (('retrieved', base_docs), ('inverted', inv_docs),
                         ('unrelated', unrel_docs), ('empty', [])):
            try:
                got[name] = client.chat(
                    ANSWER_SYSTEM,
                    ANSWER_USER.format(context=format_context(ds),
                                       question=qtext)).strip()
            except ProviderError as exc:
                got[name] = f'<error {str(exc)[:50]}>'

        total += 1
        for name in ('inverted', 'unrelated', 'empty'):
            if got[name] != got['retrieved']:
                changed[name] += 1

        print(f'Q [{qid}/{stratum}]: {qtext[:78]}')
        for name in ('retrieved', 'inverted', 'unrelated', 'empty'):
            print(f'   {name:<10s} {got[name][:150]}')
        print()

    client.flush()

    print('=' * 84)
    print('VERDICT')
    print('=' * 84)
    print(f'queries tested: {total}')
    for name in ('inverted', 'unrelated', 'empty'):
        print(f'  answer changed when context is {name:<10s}: '
              f'{changed[name]}/{total}')
    print()
    if changed['inverted'] == 0 and changed['empty'] == 0:
        print('  NEITHER flipped nor absent context changes the answer: the')
        print('  generator answers from its prior and this probe measures')
        print('  rigidity, not propagation.')
    elif changed['inverted'] > 0:
        print('  The generator DOES follow a flipped context, so the free-form')
        print('  probe is informative here and a null result would be real.')
    else:
        print('  Mixed: inspect the transcripts above before interpreting.')
    print(f'\n[cache] contexts at {CACHE} -- reusable across generators')


if __name__ == '__main__':
    main()
