"""Inspect the raw API response for an image request.

The previous probe returned HTTP 200 with an empty message for both models, which
means the request was accepted but produced no content. Possible causes with very
different implications: the response carries the answer in a different field, the
image part was dropped downstream, the prompt tripped a refusal, or the model name
routed to something that cannot answer.

This prints the response structure (keys, finish_reason, usage) and the first
characters of any content-bearing field, so the cause is visible rather than inferred.
"""
import base64
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_api_vision import make_png  # noqa: E402

CREDS = os.path.join(os.path.expanduser('~'), '.dsh', '.credentials.yaml')


def load_key():
    env = os.environ.get('DEEPSEEK_API_KEY', '').strip()
    if env:
        return env
    text = io.open(CREDS, encoding='utf-8', errors='replace').read()
    m = re.search(r'^\s*DEEPSEEK_API_KEY\s*:\s*["\']?([^"\'\r\n]+)', text, re.M)
    return m.group(1).strip() if m else ''


def post(body, key):
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key,
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:600]


def main():
    key = load_key()
    if not key:
        print('no key')
        return 1
    b64 = base64.b64encode(make_png(3)).decode()

    print('=== 1. text-only request (control) ===')
    st, d = post({'model': 'deepseek-flash',
                  'messages': [{'role': 'user', 'content': 'Reply with the word OK.'}],
                  'max_tokens': 32}, key)
    print('   status', st)
    if isinstance(d, dict):
        ch = d.get('choices', [{}])[0]
        print('   message keys:', list(ch.get('message', {}).keys()))
        print('   content:', repr(ch.get('message', {}).get('content'))[:120])
        print('   finish_reason:', ch.get('finish_reason'))
        print('   usage:', d.get('usage'))
    else:
        print('   body:', d[:300])

    print()
    print('=== 2. image request, minimal body ===')
    st, d = post({'model': 'deepseek-flash',
                  'messages': [{'role': 'user', 'content': [
                      {'type': 'image_url',
                       'image_url': {'url': 'data:image/png;base64,' + b64}},
                      {'type': 'text', 'text': 'Count the black squares.'}]}],
                  'max_tokens': 200}, key)
    print('   status', st)
    if isinstance(d, dict):
        print('   raw keys:', list(d.keys()))
        print(json.dumps(d, ensure_ascii=False)[:900])
    else:
        print('   body:', d[:600])

    print()
    print('=== 3. image request, text part first ===')
    st, d = post({'model': 'deepseek-flash',
                  'messages': [{'role': 'user', 'content': [
                      {'type': 'text', 'text': 'Count the black squares in the image.'},
                      {'type': 'image_url',
                       'image_url': {'url': 'data:image/png;base64,' + b64}}]}],
                  'max_tokens': 200}, key)
    print('   status', st)
    if isinstance(d, dict):
        ch = d.get('choices', [{}])[0]
        print('   content:', repr(ch.get('message', {}).get('content'))[:200])
        print('   finish_reason:', ch.get('finish_reason'))
    else:
        print('   body:', d[:600])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
