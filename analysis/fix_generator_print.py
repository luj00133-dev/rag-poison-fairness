"""Fix the --generator print to use model_id when the client has no `model` attribute.

LocalGenerator exposes model_id, DeepSeekClient exposes model. The first attempt at this
option printed client.model unconditionally and crashed before generating anything.
"""
import io
import os
import py_compile

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(P, 'src', 'run_attribution.py')

OLD = '''        client = LocalGenerator.from_name(args.generator)
        print(f"generator : {client.model} (local weights, no API calls)")'''
NEW = '''        client = LocalGenerator.from_name(args.generator)
        # LocalGenerator exposes model_id; DeepSeekClient exposes model. Use whichever the
        # client provides so neither path depends on the other's attribute name.
        _name = getattr(client, "model", None) or getattr(client, "model_id", "local")
        print(f"generator : {_name} (local weights, no API calls)")'''


def main():
    s = io.open(RUNNER, encoding='utf-8').read()
    n = s.count(OLD)
    print('anchor matches: %d' % n)
    if n != 1:
        print('ABORT')
        return 1
    s = s.replace(OLD, NEW, 1)
    io.open(RUNNER, 'w', encoding='utf-8', newline='\n').write(s)
    try:
        py_compile.compile(RUNNER, doraise=True)
        print('compiles: True')
    except Exception as e:
        print('compiles: False -- %s' % e)
        return 1
    print('model_id fallback present: %s' % ('getattr(client, "model_id"' in
                                             io.open(RUNNER, encoding='utf-8').read()))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
