"""Find which result directories are canonical, from the scripts that consume them.

The supplementary package should contain the runs that back the paper, not every developmental
smoke run. Rather than guess, this reads the list of result directories each analysis script
actually opens, across figure_data.py and the table/figure checkers.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS = os.path.join(P, 'analysis')
RESULTS = os.path.join(P, 'results')

CONSUMERS = [
    'figure_data.py', 'make_figures.py', 'check_all_tables.py', 'page_profile.py',
    'compose_failure_modes_figure.py', 'stats_paper.py', 'compare_six_backbones.py',
    'compare_scale.py', 'diagnose_gte_large.py', 'diagnose_poison_scores.py',
]


def main():
    available = {d for d in os.listdir(RESULTS)
                 if os.path.isdir(os.path.join(RESULTS, d))}
    used = {}
    for name in CONSUMERS:
        p = os.path.join(ANALYSIS, name)
        if not os.path.exists(p):
            continue
        s = io.open(p, encoding='utf-8').read()
        found = set()
        for m in re.finditer(r'results[/\\]([A-Za-z0-9_]+)', s):
            found.add(m.group(1))
        for m in re.finditer(r'''["']([a-z][a-z0-9_]{2,})["']''', s):
            if m.group(1) in available:
                found.add(m.group(1))
        used[name] = sorted(found & available)

    print('%-32s %s' % ('consumer', 'result directories it opens'))
    print('-' * 96)
    canonical = set()
    for name, dirs in used.items():
        if dirs:
            print('%-32s %s' % (name, ', '.join(dirs)))
            canonical |= set(dirs)

    print()
    print('canonical union: %d directories' % len(canonical))
    print('  %s' % sorted(canonical))

    total = 0
    print()
    print('%-24s %10s' % ('directory', 'KB'))
    for d in sorted(canonical):
        p = os.path.join(RESULTS, d)
        sz = sum(os.path.getsize(os.path.join(dp, f))
                 for dp, _, fs in os.walk(p) for f in fs)
        total += sz
        print('  %-22s %10d' % (d, round(sz / 1024)))
    print('  %-22s %10d' % ('TOTAL', round(total / 1024)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
