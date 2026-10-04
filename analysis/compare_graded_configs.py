"""Compare every graded-injection configuration on the two properties the validation needs.

Summary of a tuning sweep that took four retrieval runs. The question for each configuration:

  * BALANCED   -- is drift_tv zero at the partial label levels, i.e. is composition unmoved
                  where the label is graded?
  * PARTIAL    -- how many queries carry a graded label at all?

Both are needed, and the validation's power comes from the second. This reports them side by
side so the outcome of the sweep is one table rather than four separate readings.
"""
import collections
import csv
import io
import glob
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(P, 'results')

CONFIGS = [
    ('pv_graded2', 'st', 'template', 'none (ungraded), strength 1.0'),
    ('pv_graded3', 'st', 'template', 'graded, strength 0.25'),
    ('pv_validate', 'st', 'template', 'graded, strength 0.25'),
    ('pv_bal_a', 'st', 'template', 'graded, strength 0.10'),
    ('pv_bal_b', 'st', 'template', 'graded, strength 0.05'),
    ('pv_bal_c', 'st', 'template_plus_projection', 'graded + projection, strength 0.25'),
    ('pv_graded', 'st', 'template_plus_projection', 'graded + projection, strength 1.0'),
]


def main():
    print('%-13s %-26s %-34s %7s %9s %9s'
          % ('run', 'attack', 'grading', 'partial', 'bal+part', 'levels'))
    print('-' * 104)
    for tag, ret, attack, note in CONFIGS:
        path = os.path.join(RESULTS, tag, 'per_query.csv')
        if not os.path.exists(path):
            print('%-13s %-26s %-34s %7s' % (tag, attack[:26], note[:34], 'MISSING'))
            continue
        rows = list(csv.DictReader(io.open(path, encoding='utf-8')))
        sel = [r for r in rows if r.get('defense') == 'vanilla'
               and r.get('retriever') == ret and r.get('attack') == attack]
        if not sel:
            print('%-13s %-26s %-34s %7s' % (tag, attack[:26], note[:34], 'no cell'))
            continue
        by = collections.defaultdict(list)
        for r in sel:
            try:
                by[round(float(r['poison_share']), 1)].append(float(r['drift_tv']))
            except (ValueError, TypeError):
                pass
        total = sum(len(v) for v in by.values())
        part = sum(len(v) for k, v in by.items() if 0 < k < 1.0)
        balpart = sum(len(v) for k, v in by.items()
                      if 0 < k < 1.0 and (sum(v) / len(v)) < 1e-9)
        levels = sorted(k for k in by if 0 < k < 1.0)
        print('%-13s %-26s %-34s %6d %9d %9s'
              % (tag, attack[:26], note[:34], part, balpart,
                 ','.join('%.1f' % x for x in levels) or '-'))

    print()
    print('Reading: "bal+part" counts queries whose label is graded AND whose composition drift')
    print('is exactly zero -- the regime in which the aggregate should be blind while the label')
    print('varies. That is the cell the validation needs, and it needs several hundred of them.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
