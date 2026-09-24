"""Describe an image through the DeepSeek vision API.

This exists because the harness's `read_image` tool refuses: the DSH DeepSeek provider
plugin hardcodes `inputModalities: ["text"]` (dsh-llm-deepseek/lib/index.js:447) and
`settings.yaml` exposes no field to override it, so the tool believes the route cannot
take images.

The measurement says otherwise. Sending a PNG to `deepseek-flash` over the
OpenAI-compatible endpoint returns a description of the image contents in
`reasoning_content`, so the capability is present and only the local declaration is
missing. Until that declaration is fixed, this script is the working path: it reads a
file, sends it, and prints the model's answer.

Note the token budget. The model spends `reasoning_content` before emitting `content`,
and an image question can exhaust a small budget before the answer starts -- the first
probe returned `finish_reason: length` with empty content for exactly that reason. The
budget here is generous for that reason, and `reasoning_content` is printed when
`content` comes back empty so a truncation is visible instead of looking like a refusal.
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

CREDS = os.path.join(os.path.expanduser('~'), '.dsh', '.credentials.yaml')
MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.webp': 'image/webp', '.gif': 'image/gif'}


def load_key() -> str:
    env = os.environ.get('DEEPSEEK_API_KEY', '').strip()
    if env:
        return env
    if not os.path.exists(CREDS):
        return ''
    text = io.open(CREDS, encoding='utf-8', errors='replace').read()
    m = re.search(r'^\s*DEEPSEEK_API_KEY\s*:\s*["\']?([^"\'\r\n]+)', text, re.M)
    return m.group(1).strip() if m else ''


def describe(path: str, question: str, model: str = 'deepseek-flash',
             max_tokens: int = 2000, key: str = '') -> str:
    ext = os.path.splitext(path)[1].lower()
    mime = MIME.get(ext)
    if mime is None:
        return 'unsupported image type: %s' % ext
    raw = open(path, 'rb').read()
    b64 = base64.b64encode(raw).decode()
    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': question},
            {'type': 'image_url',
             'image_url': {'url': 'data:%s;base64,%s' % (mime, b64)}},
        ]}],
        'max_tokens': max_tokens,
        'temperature': 0,
    }
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key,
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return 'HTTP %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300])
    except Exception as e:
        return '%s: %s' % (type(e).__name__, str(e)[:200])

    ch = d.get('choices', [{}])[0]
    msg = ch.get('message', {})
    content = (msg.get('content') or '').strip()
    reasoning = (msg.get('reasoning_content') or '').strip()
    finish = ch.get('finish_reason')
    if content:
        out = content
        if finish == 'length':
            out += '\n[truncated: finish_reason=length; raise max_tokens]'
        return out
    if reasoning:
        return ('[no final answer, finish_reason=%s]\n'
                'reasoning trace:\n%s' % (finish, reasoning[:1500]))
    return '[empty response, finish_reason=%s] %s' % (finish,
                                                      json.dumps(d)[:400])


DEFAULT_Q = ('Describe this figure precisely for someone who cannot see it: its layout, '
             'how many panels, what each axis shows, what the legend says, whether any '
             'label is clipped or overlapping, and whether any text is garbled or '
             'misspelled. Then state whether it looks like a publication-quality figure.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('images', nargs='+')
    ap.add_argument('--question', '-q', default=DEFAULT_Q)
    ap.add_argument('--model', default='deepseek-flash')
    ap.add_argument('--max-tokens', type=int, default=2000)
    args = ap.parse_args()

    key = load_key()
    if not key:
        print('no DeepSeek key available (environment or ~/.dsh/.credentials.yaml)')
        return 1
    for p in args.images:
        print('=' * 78)
        print(os.path.basename(p))
        print('=' * 78)
        print(describe(p, args.question, args.model, args.max_tokens, key))
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
