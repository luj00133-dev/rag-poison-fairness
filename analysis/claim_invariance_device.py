"""Does CPU-versus-GPU encoding change the paper's *claims*, not just its rankings?

The speed measurement is unambiguous: GTE-base encoding is 171x faster on the
RTX 5060 (1079 vs 6.3 docs/s), so the full 17,792-document BBQ corpus costs 18
seconds instead of 47 minutes. That removes the reason the generation-stage
evaluation was subsampled.

The equivalence measurement is equally unambiguous and less convenient: the two
devices do not produce identical embeddings (max |a-b| = 2.4e-4) and only 27 of 48
queries keep an identical top-5. So the question is not "are they the same" -- they
are not -- but "does the choice of device change the numbers the paper reports".

That distinction matters because the paper itself documents that its dense
retrieval scores are extremely close: clean top-5 threshold 0.8982 against
best-poison 0.8907, a margin of 0.0075. A perturbation of 2.4e-4 is three times
smaller than that margin in embedding space, but ranking flips are free when
scores are this tight, so the only way to know is to run the pipeline both ways
and compare the metrics.

Measures, on the controlled corpus with the canonical configuration:
    poison@k        adversarial-passage inclusion
    drift_tv        R1 composition drift
    stance_gap      R2 stance gap
for the clean condition, the text attack and the projection attack, on CPU and on
GPU, side by side.
"""
import os
import sys

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import torch  # noqa: E402


def run(device):
    """Execute the retrieval pipeline on one device and return the metrics."""
    # the retriever reads the device from torch's default, so set it here
    from src.run_experiment import (apply_attack, build_bundle,
                                    build_retriever, load_config)
    from src.eval.metrics import corpus_favourable_rate, evaluate_query

    cfg = load_config('configs/default.json', quick=False)
    bundle = build_bundle(cfg)
    k = int(cfg['top_k'])

    retriever = build_retriever('st', bundle.docs, cfg)
    # force the encoder onto the requested device
    if hasattr(retriever, 'model'):
        retriever.model.to(device)

    clean_res = {q.qid: retriever.search(q.text, k) for q in bundle.queries}
    clean = {qid: r.docs for qid, r in clean_res.items()}
    ref = {s: corpus_favourable_rate([d for d in bundle.docs if d.group in gs], gs)
           for s, gs in bundle.groups.items()}

    out = {}
    for attack in ('clean', 'template', 'template_plus_projection'):
        if attack == 'clean':
            hits, drifts, gaps = [], [], []
            for q in bundle.queries:
                m = evaluate_query(
                    clean_res[q.qid],
                    clean_docs=clean[q.qid], groups=bundle.groups[q.stratum],
                    pool_ids=bundle.candidate_pool[q.qid], topk_poison_ids=set(),
                    corpus_fav_ref=ref[q.stratum])
                hits.append(0.0)
                drifts.append(m.drift_tv)
                gaps.append(m.stance_gap)
        else:
            atk, poison = apply_attack(attack, retriever, bundle.docs,
                                       bundle.queries, cfg, bundle.groups)
            if hasattr(atk, 'model'):
                atk.model.to(device)
            pids = {p.doc_id for p in poison}
            hits, drifts, gaps = [], [], []
            for q in bundle.queries:
                res = atk.search(q.text, k)
                m = evaluate_query(
                    res, clean_docs=clean[q.qid],
                    groups=bundle.groups[q.stratum],
                    pool_ids=bundle.candidate_pool[q.qid],
                    topk_poison_ids=pids, corpus_fav_ref=ref[q.stratum])
                hits.append(m.poison_in_topk)
                drifts.append(m.drift_tv)
                gaps.append(m.stance_gap)
        out[attack] = {
            'poison@k': float(np.nanmean(hits)),
            'drift_tv': float(np.nanmean(drifts)),
            'stance_gap': float(np.nanmean(gaps)),
        }
    return out


def main():
    print('torch %s  cuda=%s' % (torch.__version__, torch.cuda.is_available()))
    if not torch.cuda.is_available():
        print('no GPU; nothing to compare')
        return 1

    results = {}
    for dev in ('cpu', 'cuda'):
        print('\n=== running pipeline on %s ===' % dev)
        results[dev] = run(dev)
        for atk, m in results[dev].items():
            print('   %-24s poison@k=%.4f  drift=%.4f  gap=%.4f'
                  % (atk, m['poison@k'], m['drift_tv'], m['stance_gap']))

    print()
    print('=' * 78)
    print('DOES THE DEVICE CHANGE THE REPORTED NUMBERS?')
    print('=' * 78)
    print()
    print('%-26s %10s %10s %10s' % ('attack / metric', 'cpu', 'gpu', 'delta'))
    worst = 0.0
    for atk in results['cpu']:
        for met in ('poison@k', 'drift_tv', 'stance_gap'):
            a, b = results['cpu'][atk][met], results['cuda'][atk][met]
            d = abs(a - b)
            worst = max(worst, d)
            print('%-26s %10.4f %10.4f %10.4f'
                  % ('%s / %s' % (atk, met), a, b, d))
    print()
    print('largest absolute difference: %.4f' % worst)
    print()
    if worst <= 0.05:
        print('VERDICT: the device does not change any reported metric by more')
        print('than 0.05, so GPU encoding can regenerate the pipeline without')
        print('altering the paper\'s claims. The full BBQ corpus becomes')
        print('affordable, which is what the generation-stage evaluation needed.')
    else:
        print('VERDICT: the device moves a reported metric by %.4f. The claims'
              % worst)
        print('are not device-invariant at this precision, so either the whole')
        print('pipeline is regenerated on one device and the choice is reported,')
        print('or the GPU run is treated as a separate robustness check rather')
        print('than as the canonical numbers.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
