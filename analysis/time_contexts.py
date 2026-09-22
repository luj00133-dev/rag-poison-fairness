"""Time each stage of collect_contexts on the BBQ corpus.

collect_contexts has run for 45+ minutes on BBQ without producing output, which
is far beyond what the encoding cost accounts for (~15 min at the measured
20 docs/s). Guessing at the cause has already cost two runs, so this measures
each stage instead.

Usage:
    python analysis/time_contexts.py            # controlled corpus
    python analysis/time_contexts.py bbq        # BBQ
"""
import os
import sys
import time

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.run_experiment import (  # noqa: E402
    apply_attack,
    build_bundle,
    build_defenses,
    build_retriever,
    load_config,
)


def stamp(label, t0):
    dt = time.time() - t0
    print(f'  {label:<46s} {dt:7.1f}s', flush=True)
    return time.time()


def main():
    if len(sys.argv) > 1:
        cfg_path = ('configs/generation_bbq_sub.json' if sys.argv[1] == 'bbq-sub'
                    else 'configs/generation_bbq.json' if sys.argv[1] == 'bbq'
                    else 'configs/attribution.json')
    else:
        cfg_path = 'configs/attribution.json'
    print(f'config: {cfg_path}', flush=True)
    cfg = load_config(cfg_path, quick=False)

    t = time.time()
    bundle = build_bundle(cfg)
    t = stamp(f'build_bundle ({len(bundle.docs)} docs, '
              f'{len(bundle.queries)} queries)', t)

    k = int(cfg['top_k'])
    rk = str(cfg.get('retriever', 'st'))

    retriever = build_retriever(rk, bundle.docs, cfg)
    t = stamp('build_retriever(clean) [encodes corpus]', t)

    n = 0
    for q in bundle.queries[:20]:
        retriever.search(q.text, k)
        n += 1
    t = stamp(f'search x{n} (clean)', t)

    # defences build their own retrievers and a calibration encode
    defs = build_defenses(retriever, bundle.docs, cfg)
    t = stamp(f'build_defenses ({len(defs)} defenses)', t)

    for q in bundle.queries[:20]:
        for d in defs:
            d.retrieve(q, k)
    t = stamp('defense.retrieve x20 x n_defenses', t)

    retriever2, poison = apply_attack(
        'template_plus_projection', retriever, bundle.docs, bundle.queries,
        cfg, bundle.groups,
    )
    t = stamp(f'apply_attack ({len(poison)} poison docs)', t)

    for q in bundle.queries[:20]:
        retriever2.search(q.text, k)
    t = stamp('search x20 (poisoned)', t)

    from src.retrieval.dense import SentenceTransformerRetriever
    print(f'\n  encoder cache: {SentenceTransformerRetriever.cache_stats()}',
          flush=True)
    print('\ndone', flush=True)


if __name__ == '__main__':
    main()
