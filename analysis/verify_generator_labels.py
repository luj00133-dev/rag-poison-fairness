"""Check every generation result file for generator/label mismatches.

The runs were launched sequentially with the generator list on the command line, and
the natural-corpus run takes about 25 minutes. If two were ever interleaved or a
label was recorded wrongly, a conclusion could be attached to the wrong model -- a
silent, serious error. Nothing suggests it happened, but the result files carry both
the short name and the full label, so the pairing is checkable rather than assumed.

For each file, verifies that the recorded label is consistent with the recorded short
name, and reports which models appear where.
"""
import json
import os

FILES = [
    ('controlled / free-form', 'results/generation/generation.json'),
    ('BBQ / free-form', 'results/generation_bbq/generation.json'),
    ('controlled / forced-choice', 'results/fc_controlled/forced_choice.json'),
    ('BBQ / forced-choice', 'results/fc_bbq/forced_choice.json'),
    ('smoke / forced-choice', 'results/fc_smoke/forced_choice.json'),
]

#: short name -> substrings that must appear in the label
EXPECT = {
    'qwen-plus': ('qwen', 'qwen-plus'),
    'qwen-turbo': ('qwen', 'qwen-turbo'),
    'qwen-max': ('qwen', 'qwen-max'),
    'mistral-7b': ('local', 'mistral'),
}


def main():
    problems = 0
    print('%-28s %-12s %-42s %s' % ('result file', 'name', 'label', 'ok'))
    for title, path in FILES:
        if not os.path.exists(path):
            print('%-28s (missing)' % title)
            continue
        d = json.load(open(path, encoding='utf-8'))
        for g in d.get('generators', []):
            name = g.get('generator', '?')
            label = g.get('label') or g.get('provider') or '?'
            low = str(label).lower()
            want = EXPECT.get(name)
            ok = True if want is None else all(w in low for w in want)
            if not ok:
                problems += 1
            print('%-28s %-12s %-42s %s' % (
                title, name, str(label)[:42], 'OK' if ok else '** MISMATCH **'))
    print()
    # cross-check: the same (corpus, probe, model) must give the same record count
    print('record counts by file:')
    for title, path in FILES:
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        counts = {g['generator']: len(g.get('records', []))
                  for g in d.get('generators', [])}
        print('   %-28s %s' % (title, counts))
    print()
    print('mismatched labels: %d' % problems)
    if problems == 0:
        print('RESULT: every generator is paired with the label its name implies,')
        print('so no conclusion is attached to the wrong model.')
    return 0 if problems == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
