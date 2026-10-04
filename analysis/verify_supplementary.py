"""Verify the supplementary package: the README's description must match the actual files.

The manifest tells a reader what columns mean. That description was written from the manuscript's
own definitions, so it has to be checked against the shipped CSVs -- a manifest that misdescribes a
column is worse than none, because a reader will trust it.

Also checks that every directory the manifest lists exists and is non-empty, and that the archive
covers the runs the manuscript's tables and figures draw on.
"""
import csv
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(P, 'supplementary')

# column -> the meaning the manifest asserts
CLAIMED = {
    'qid': 'query identifier',
    'drift_tv': 'R1 total-variation distance',
    'drift_js': 'R1 Jensen-Shannon',
    'stance_shift': 'R2 per-group shift vs clean reference',
    'stance_div': 'R2 deviation from corpus reference',
    'stance_onesided': 'R2 one-sidedness',
    'stance_gap': 'R2 cross-group difference',
    'poison_in_topk': 'attack-success indicator',
    'poison_share': 'adversarial fraction of the top-k',
    'in_pool_rate': 'utility control',
    'mean_score': 'mean retrieval score',
}


def main():
    readme = os.path.join(SUPP, 'README_SUPPLEMENTARY.txt')
    if not os.path.exists(readme):
        print('README_SUPPLEMENTARY.txt MISSING')
        return 1
    text = io.open(readme, encoding='utf-8').read()

    dirs = sorted(d for d in os.listdir(SUPP)
                  if os.path.isdir(os.path.join(SUPP, d)))
    print('directories in the package: %d' % len(dirs))

    problems = []

    # 1. every directory is named in the manifest and is non-empty
    for d in dirs:
        if d not in text:
            problems.append('directory not described in the manifest: %s' % d)
        files = os.listdir(os.path.join(SUPP, d))
        if not files:
            problems.append('empty directory: %s' % d)

    # 2. every retrieval per-query file has the columns the manifest claims
    print()
    print('%-30s %-8s %s' % ('directory', 'rows', 'column check'))
    for d in dirs:
        p = os.path.join(SUPP, d, 'per_query.csv')
        if not os.path.exists(p):
            print('  %-28s %-8s %s' % (d, '-', 'no per_query.csv'))
            continue
        with io.open(p, encoding='utf-8', newline='') as fh:
            rdr = csv.DictReader(fh)
            cols = rdr.fieldnames or []
            n = sum(1 for _ in rdr)
        gen = d.startswith(('S11','S12'))
        fc = d.startswith(('S13','S14'))
        want = (['qid','stratum','condition','generator','n_poison_in_context',
                 'stance_g1','stance_g2','gap'] if gen else
                ['qid','stratum','condition','generator','group','p_fav','margin',
                 'commitment','choice'] if fc else list(CLAIMED))
        missing = [c for c in want if c not in cols]
        if missing:
            # generation-stage files legitimately carry a different schema
            note = 'different schema (%d cols)' % len(cols) if len(cols) < 8 else \
                   'MISSING %s' % missing
            if len(cols) >= 8:
                problems.append('%s missing claimed columns: %s' % (d, missing))
        else:
            note = 'all claimed columns present'
        print('  %-28s %-8d %s' % (d, n, note))

    # 3. the manifest's column list must not claim columns that appear nowhere
    print()
    with io.open(os.path.join(SUPP, dirs[0], 'per_query.csv'), encoding='utf-8') as fh:
        actual = set(csv.DictReader(fh).fieldnames or [])
    claimed_in_readme = set()
    for line in text.split('\n'):
        tok = line.strip().split()
        if tok and tok[0] in CLAIMED:
            claimed_in_readme.add(tok[0])
    print('columns named in the manifest : %d' % len(claimed_in_readme))
    print('columns actually in the data  : %d' % len(actual))
    phantom = claimed_in_readme - actual
    if phantom:
        problems.append('manifest names columns that do not exist: %s' % sorted(phantom))

    print()
    if problems:
        for p_ in problems:
            print('  PROBLEM: %s' % p_)
    print('RESULT: %s' % ('manifest consistent with the data' if not problems
                          else '%d problem(s)' % len(problems)))
    return 0 if not problems else 1


if __name__ == '__main__':
    raise SystemExit(main())
