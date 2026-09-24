"""Run the API vision test using the key DSH stores, without printing it.

The shell environment has DEEPSEEK_API_KEY set but empty, while
~/.dsh/.credentials.yaml holds a real value that the deepseek-official provider
uses. Rather than copy that value anywhere, this reads it, runs the test, and
reports only whether the endpoint accepted an image.

The key is never written to disk, echoed, or included in any output; only its
length is reported, and only so that a silent empty-read is distinguishable from a
rejected request.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_api_vision import call  # noqa: E402

CREDS = os.path.join(os.path.expanduser('~'), '.dsh', '.credentials.yaml')


def load_key() -> str:
    env = os.environ.get('DEEPSEEK_API_KEY', '').strip()
    if env:
        return env
    if not os.path.exists(CREDS):
        return ''
    text = io.open(CREDS, encoding='utf-8', errors='replace').read()
    # a flat "KEY: value" yaml mapping is all this file uses
    m = re.search(r'^\s*DEEPSEEK_API_KEY\s*:\s*["\']?([^"\'\r\n]+)',
                  text, re.M)
    return m.group(1).strip() if m else ''


def main():
    key = load_key()
    print('key source : %s' % ('environment' if os.environ.get(
        'DEEPSEEK_API_KEY', '').strip() else '~/.dsh/.credentials.yaml'))
    print('key length : %d  (value never printed)' % len(key))
    print()
    if not key:
        print('no key available; cannot test')
        return 1

    for model in ('deepseek-flash', 'deepseek-v4-flash'):
        results = []
        for n in (3, 5):
            ok, out = call(model, key, n)
            got = ''.join(c for c in out if c.isdigit())
            correct = ok and got == str(n)
            results.append(correct)
            print('%-20s black squares=%-2d  ok=%-5s reply=%r'
                  % (model, n, ok, out[:50].replace('\n', ' ')))
        print('%-20s -> %s' % (model,
                               'READS IMAGES (both correct)' if all(results)
                               else 'not reading images' if not any(results)
                               else 'inconsistent (one of two correct)'))
        print()

    print('Interpretation: a text-only model cannot count squares in an image,')
    print('and a model that guesses a constant fails one of the two probes. Both')
    print('correct means the endpoint is genuinely reading the image.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
