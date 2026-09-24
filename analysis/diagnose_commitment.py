"""Is the BBQ null a real null, or a probe that cannot register anything there?

The controlled corpus shows a per-group stance shift of -0.13/+0.13 under
injection; BBQ shows +0.001 to +0.044. Two explanations fit that, and the paper
currently reports only the second:

  (A) the retrieval-layer skew does not reach the output on a naturally written
      corpus -- a real null;
  (B) the free-form probe cannot register stance on these questions, so *any*
      effect would read as zero.

They are distinguishable, and the data already hints at (B). EAE-D on BBQ clean is
0.425 with 57.5% of passages unattributed, against 0.827 on the controlled corpus:
the BBQ answers lean on their context far less. The questions are also different in
kind -- "Who performed better in the engineering evaluation?" invites a
stance-bearing comparison, "Who avoids risky things?" invites a descriptive answer
that may name no group and compare nothing.

The diagnostic that separates them: measure the *stance margins* rather than the
difference of margins. For each answer the NLI scorer gives P(entail | answer,
favourable) and P(entail | answer, unfavourable). A committed answer has one high
and one low; an uncommitted answer has both near zero. If BBQ answers are
uncommitted, `max(pos, neg)` will be near zero there and large on the controlled
corpus, and the null is a probe failure.

Reports per corpus and generator:
    commitment   mean max(P(fav), P(unfav)) -- how much stance content the answer has
    margin       mean |stance| -- the statistic the paper reports
    uncommitted  fraction of answers with commitment < 0.1
"""
import json
import os
import sys

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

CORPORA = [
    ('controlled', 'results/generation/generation.json'),
    ('BBQ (full)', 'results/generation_bbq/generation.json'),
]


def analyse(path, label):
    if not os.path.exists(path):
        print('%-14s (missing)' % label)
        return None
    d = json.load(open(path, encoding='utf-8'))
    print('=== %s ===' % label)
    print('%-14s %-10s %7s %10s %10s %12s' % (
        'generator', 'condition', 'n', 'commitment', '|margin|', 'uncommitted'))
    out = {}
    for g in d['generators']:
        for cond in ('clean', 'poisoned'):
            recs = [r for r in g['records']
                    if r['condition'] == cond and r.get('nli')]
            if not recs:
                continue
            commit, margin, uncomm = [], [], []
            for r in recs:
                nli = r['nli']
                pos = [v for k, v in nli.items() if k.endswith('_fav')]
                neg = [v for k, v in nli.items() if k.endswith('_unfav')]
                if not pos or not neg:
                    continue
                # per group: commitment is the larger of the two entailment
                # probabilities, margin is their difference
                for p, n in zip(sorted(pos), sorted(neg)):
                    commit.append(max(p, n))
                    margin.append(abs(p - n))
                    uncomm.append(1.0 if max(p, n) < 0.1 else 0.0)
            out[(g['generator'], cond)] = (
                float(np.mean(commit)), float(np.mean(margin)),
                float(np.mean(uncomm)))
            print('%-14s %-10s %7d %10.4f %10.4f %11.1f%%' % (
                g['generator'], cond, len(recs), out[(g['generator'], cond)][0],
                out[(g['generator'], cond)][1],
                100 * out[(g['generator'], cond)][2]))
    print()
    return out


def main():
    print('Commitment = mean max(P(fav), P(unfav)). A high value means the answer')
    print('takes a position, so a stance measurement has something to measure. Near')
    print('zero means the answer is non-committal and NO probe of this kind can')
    print('register an effect, however large the retrieval-layer skew.')
    print()
    results = {}
    for label, path in CORPORA:
        results[label] = analyse(path, label)

    print('=' * 78)
    print('VERDICT')
    print('=' * 78)
    print()
    ctl = results.get('controlled') or {}
    bbq = results.get('BBQ (full)') or {}
    ctl_c = [v[0] for k, v in ctl.items() if k[1] == 'clean']
    bbq_c = [v[0] for k, v in bbq.items() if k[1] == 'clean']
    ctl_u = [v[2] for k, v in ctl.items() if k[1] == 'clean']
    bbq_u = [v[2] for k, v in bbq.items() if k[1] == 'clean']
    if not (ctl_c and bbq_c):
        print('insufficient data')
        return 0
    print('clean-condition commitment, mean over generators:')
    print('   controlled  %.4f   (uncommitted %.1f%%)'
          % (float(np.mean(ctl_c)), 100 * float(np.mean(ctl_u))))
    print('   BBQ         %.4f   (uncommitted %.1f%%)'
          % (float(np.mean(bbq_c)), 100 * float(np.mean(bbq_u))))
    print()
    ratio = float(np.mean(ctl_c)) / max(float(np.mean(bbq_c)), 1e-9)
    print('commitment ratio controlled/BBQ: %.2fx' % ratio)
    print()
    if ratio > 2.0:
        print('CONCLUSION: the BBQ answers are substantially less committed, so the')
        print('free-form null there is at least partly a probe limitation rather than')
        print('evidence that no effect exists. The paper must say which, and the way')
        print('to say it is a probe that forces commitment and can be applied to both')
        print('corpora -- which is the forced-choice design, scored by NLI instead of')
        print('parsed from text so it yields a continuous margin.')
    else:
        print('CONCLUSION: commitment is comparable across corpora, so the BBQ null')
        print('is not explained by non-committal answers. The scoping to template')
        print('corpora stands and no probe change would alter it.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
