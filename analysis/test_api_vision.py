"""Does the DeepSeek API actually accept image input for this model?

This is the question that decides whether patching the DSH provider plugin is worth
anything. The plugin hardcodes `inputModalities: ["text"]` in
dsh-llm-deepseek/lib/index.js, and `settings.yaml` has no field to override it, so if
the endpoint rejects images then a patch would only move the failure from a local
check to an API error.

Sends a tiny deterministic image (a PNG with a known number of black squares) and
asks the model to count them, which a text-only model cannot answer correctly. Uses
the OpenAI-compatible image_url content part.

Nothing is written to the repository; the key is read from the environment.
"""
import base64
import json
import os
import struct
import urllib.error
import urllib.request
import zlib


def make_png(squares: int, size: int = 64, cell: int = 16) -> bytes:
    """A white PNG with `squares` black cells along the top row."""
    rows = []
    for y in range(size):
        row = bytearray(b'\x00')          # filter type 0
        for x in range(size):
            black = (y < cell) and (x // cell < squares)
            row += b'\x00\x00\x00' if black else b'\xff\xff\xff'
        rows.append(bytes(row))
    raw = b''.join(rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))

    ihdr = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def call(model: str, key: str, n_squares: int) -> tuple[bool, str]:
    png = make_png(n_squares)
    b64 = base64.b64encode(png).decode()
    body = {
        'model': model,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text',
                 'text': 'How many separate black squares are in this image? '
                         'Answer with just the number.'},
                {'type': 'image_url',
                 'image_url': {'url': 'data:image/png;base64,' + b64}},
            ],
        }],
        'max_tokens': 20,
        'temperature': 0,
    }
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key,
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
        return True, (d['choices'][0]['message']['content'] or '').strip()
    except urllib.error.HTTPError as e:
        return False, 'HTTP %s %s' % (e.code,
                                      e.read().decode('utf-8', 'replace')[:220])
    except Exception as e:
        return False, '%s: %s' % (type(e).__name__, str(e)[:160])


def main():
    key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not key:
        print('DEEPSEEK_API_KEY is not set in this environment')
        return 1
    print('key length: %d' % len(key))
    print()
    # two different images: a text-only model cannot get both right, and a model
    # that guesses a constant will fail one of them
    for model in ('deepseek-flash', 'deepseek-v4-flash'):
        for n in (3, 5):
            ok, out = call(model, key, n)
            verdict = ''
            if ok:
                got = ''.join(c for c in out if c.isdigit())
                if got:
                    verdict = ('CORRECT' if int(got) == n
                               else 'wrong (said %s, image had %d)' % (got, n))
                else:
                    verdict = 'no digit in reply'
            print('%-20s squares=%d  ok=%s  %-42s %s'
                  % (model, n, ok, out[:42].replace('\n', ' '), verdict))
    print()
    print('A model that answers both correctly is reading the image.')
    print('A refusal or an error about content types means text-only on this endpoint.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
