"""Clean the placeholder pollution out of the shared generation cache.

What happened. run_attribution() caches generator replies in a single file,
results/attribution_cache.json, with no separation between --dry-run and real runs. Two
dry runs of mine (measuring API cost, and validating the config) cached the placeholder
strings "[dry-run answer]" and "NONE" under REAL prompt keys. A subsequent paid run then
found 225 of its 576 keys already cached and served the placeholders, so it made zero API
calls and produced answers of "[dry-run answer]" -- which the NLI scorer cannot score, hence
the NaN summary.

This removes only the placeholder entries. Real cached model replies are kept, since they are
genuine outputs and still valid. The fix for the root cause is in a separate change.
"""
import io
import json
import os
import shutil

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(P, 'results', 'attribution_cache.json')
BACKUP = os.path.join(P, 'results', '_cache_backup', 'attribution_cache.contaminated.json')

PLACEHOLDERS = {'[dry-run answer]', 'NONE', ''}


def main():
    if not os.path.exists(CACHE):
        print('cache not found at %s' % CACHE)
        return 1
    if not os.path.exists(BACKUP):
        os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
        shutil.copy(CACHE, BACKUP)
        print('backed up to %s' % BACKUP)
    else:
        print('backup already exists, not overwriting')

    cache = json.load(io.open(CACHE, encoding='utf-8'))
    before = len(cache)
    cleaned = {k: v for k, v in cache.items() if v not in PLACEHOLDERS}
    removed = before - len(cleaned)

    json.dump(cleaned, io.open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    print('entries: %d -> %d (removed %d placeholders)' % (before, len(cleaned), removed))

    # verify none survive
    after = json.load(io.open(CACHE, encoding='utf-8'))
    bad = sum(1 for v in after.values() if v in PLACEHOLDERS)
    print('placeholders remaining: %d' % bad)
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
