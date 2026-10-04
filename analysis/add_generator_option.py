"""Add a --generator option to run_attribution.py.

Motivation, not convenience. The prospective-validation experiment needs the generation stage
at several poison rates across four strata, and the runner hard-codes DeepSeekClient, so every
point of the gradient is a paid API run. src/eval/generation.py already provides LocalGenerator
with the same chat() interface -- run_generation.py uses it for the Mistral-7B panel -- and the
weights are on this machine. Routing run_attribution through it makes the experiment affordable
and reproducible offline.

The edit is deliberately minimal and additive: the default stays DeepSeekClient with its
existing behaviour (including the DEEPSEEK_API_KEY requirement), and --generator only selects
a local model. Both clients expose chat(), model and base_url, which is all this runner uses.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(P, 'src', 'run_attribution.py')

OLD_ARG = '''    ap.add_argument("--limit", type=int, default=0,
                    help="cap queries per condition (0 = all)")'''
NEW_ARG = '''    ap.add_argument("--limit", type=int, default=0,
                    help="cap queries per condition (0 = all)")
    ap.add_argument("--generator", default=None,
                    help="local generator name (e.g. mistral-7b) instead of the "
                         "DeepSeek API; no API key needed")'''

OLD_CLIENT = '''    client = DeepSeekClient(dry_run=args.dry_run)
    print(f"generator : {client.model} @ {client.base_url}"
          f"{'  [DRY RUN]' if args.dry_run else ''}")'''
NEW_CLIENT = '''    if args.generator:
        from .eval.generation import LocalGenerator  # local import: heavy deps

        client = LocalGenerator.from_name(args.generator)
        # LocalGenerator exposes model_id; DeepSeekClient exposes model. Use whichever
        # the client provides so neither path depends on the other's attribute name.
        _name = getattr(client, "model", None) or getattr(client, "model_id", "local")
        print(f"generator : {_name} (local weights, no API calls)")
    else:
        client = DeepSeekClient(dry_run=args.dry_run)
        print(f"generator : {client.model} @ {client.base_url}"
              f"{'  [DRY RUN]' if args.dry_run else ''}")'''


def main():
    s = io.open(RUNNER, encoding='utf-8').read()
    for old, new, label in ((OLD_ARG, NEW_ARG, 'CLI option'),
                            (OLD_CLIENT, NEW_CLIENT, 'client construction')):
        n = s.count(old)
        print('%-22s %d match(es)' % (label, n))
        if n != 1:
            print('  ^ ABORT: anchor must match exactly once')
            return 1
        s = s.replace(old, new, 1)
    io.open(RUNNER, 'w', encoding='utf-8', newline='\n').write(s)

    s2 = io.open(RUNNER, encoding='utf-8').read()
    for probe in ('--generator', 'LocalGenerator.from_name', 'DeepSeekClient(dry_run'):
        print('  %-30s %s' % (probe, probe in s2))
    # syntax check
    import py_compile
    try:
        py_compile.compile(RUNNER, doraise=True)
        print('  compiles: True')
    except Exception as e:
        print('  compiles: False -- %s' % e)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
