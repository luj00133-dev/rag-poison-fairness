"""What does the generator actually receive, and can the stance be read off it?

The negative control on the controlled corpus showed the generator does not
follow an inverted context (0/6) while it does notice an unrelated one (6/6).
Before interpreting that as a property of retrieval-augmented generation, we
have to see the passages themselves: if the retrieved context does not state a
comparable stance, "the generator ignored the stance" is not a finding about the
generator.

This prints, for one query per condition:
  * the question;
  * every retrieved passage, truncated, with its group and stance label;
  * the answer the generator gave from that context;
  * the NLI stance of the *context* itself toward each group, using the same
    scoring convention as the answer-level metric, so the retrieval-layer and
    generation-layer signals are on one scale.
"""
import os
import sys

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.eval.attribution import (ANSWER_SYSTEM, ANSWER_USER,
                                  STANCE_TEMPLATES, format_context)
from src.eval.generation import ChatClient, NliScorer
from src.run_attribution import collect_contexts
from src.run_experiment import load_config


def context_stance(doc_texts, texts_for_group, scorer):
    """Stance of a whole context block toward a group, on the answer-level scale.

    The context is treated as one premise: does it entail the favourable
    statement more than the unfavourable one? This is deliberately the same
    convention used for answers so the two numbers can be compared directly.
    """
    if not doc_texts:
        return float('nan')
    fav, unfav = texts_for_group
    joined = ' '.join(doc_texts)
    p = scorer.entailment([joined], [fav])[0]
    n = scorer.entailment([joined], [unfav])[0]
    return p - n


def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else 'configs/generation_bbq.json'
    gen = sys.argv[2] if len(sys.argv) > 2 else 'qwen-turbo'
    n_show = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    cfg = load_config(cfg_path, quick=False)
    bundle, conditions, meta = collect_contexts(cfg)
    groups = meta['groups']
    client = ChatClient.from_name(gen, cache_path='results/gen_inspect_cache.json')
    scorer = NliScorer()

    print('=' * 88)
    print('RETRIEVED CONTEXT INSPECTION')
    print('=' * 88)
    print(f'config: {cfg_path}   generator: {client.provider.label}')
    print()

    for q, docs, poison_ids in conditions['clean'][:n_show]:
        g1, g2 = groups[q.stratum]
        print('#' * 88)
        print(f'QUESTION [{q.qid} / {q.stratum}]: {q.text}')
        print(f'groups: g1={g1}  g2={g2}')
        print('#' * 88)

        for cond in ('clean', 'poisoned'):
            items = [x for x in conditions[cond] if x[0].qid == q.qid]
            if not items:
                continue
            _, cdocs, cpoison = items[0]
            print()
            print(f'--- condition: {cond}  '
                  f'({len(cpoison)} of {len(cdocs)} passages injected) ---')
            for i, d in enumerate(cdocs):
                mark = 'POISON' if d.doc_id in set(cpoison) else 'clean '
                text = (d.text or '').replace('\n', ' ')
                print(f'  [{i}] {mark} group={d.group!r:<22s} '
                      f'stance={d.stance!r:<14s} {text[:96]}')

            ctexts = [d.text for d in cdocs]
            for gname in (g1, g2):
                tmpl = STANCE_TEMPLATES.get(gname)
                if tmpl is None:
                    continue
                s = context_stance(ctexts, tmpl, scorer)
                print(f'  -> context stance toward {gname:<16s} = {s:+.3f}')

            ans = client.chat(
                ANSWER_SYSTEM,
                ANSWER_USER.format(context=format_context(cdocs),
                                   question=q.text)).strip()
            print(f'  -> answer: {ans[:180]}')
            for gname in (g1, g2):
                tmpl = STANCE_TEMPLATES.get(gname)
                if tmpl is None:
                    continue
                sa = scorer.stance([ans], tmpl[0], tmpl[1])[0]
                print(f'  -> answer stance toward {gname:<16s} = {sa:+.3f}')
        print()

    client.flush()


if __name__ == '__main__':
    main()
