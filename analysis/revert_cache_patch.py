"""Revert the broken cache patch and re-run the generation stage for real.

The patch referenced a `dry_run` argument that run_attribution() does not have, so it would
have raised NameError the moment the function was called. Reverted.

The lesson is narrower and more useful than the patch: --dry-run is not a free way to measure
what a real run costs, because it writes placeholder replies into the SAME cache the real run
reads. Measuring with --dry-run therefore corrupts the measurement it was supposed to inform.
The correct way to measure is to call the real path with use_cache=True: cached keys cost
nothing and write nothing new, and the remaining keys are exactly the real work to be done.
"""
import io
import os
import py_compile

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATTRIB = os.path.join(P, 'src', 'eval', 'attribution.py')

BROKEN = '''    # Dry runs must never share the real cache: their placeholder replies would be
    # served to a later paid run under the same prompt keys, silently replacing real
    # generations. That is exactly what happened once, so the paths are now distinct.
    _cache_name = "attribution_cache_dryrun.json" if dry_run else "attribution_cache.json"
    cache_path = os.path.join("results", _cache_name)'''
RESTORED = '''    cache_path = os.path.join("results", "attribution_cache.json")'''


def main():
    s = io.open(ATTRIB, encoding='utf-8').read()
    n = s.count(BROKEN)
    print('broken patch found: %d' % n)
    if n == 1:
        s = s.replace(BROKEN, RESTORED, 1)
        io.open(ATTRIB, 'w', encoding='utf-8', newline='\n').write(s)
        print('reverted')
    py_compile.compile(ATTRIB, doraise=True)
    s2 = io.open(ATTRIB, encoding='utf-8').read()
    print('dry_run reference gone:', 'dry_run else' not in s2)
    print('cache_path restored    :', RESTORED.strip() in s2)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
