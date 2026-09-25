"""Describe the five locally downloaded images in one pass, via the DeepSeek vision route.

Same route as analysis/describe_image.py, but batched: these five are candidates for
insertion into Paper A/B, so the useful answer is what each one *is* and whether it is a
schematic (worth inserting) or a chart (which we must redraw from committed results,
because a generated chart cannot be traced to the numbers in the paper).
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
from describe_image import load_key, MIME

DOWNLOADS = os.path.join(os.path.expanduser('~'), 'Downloads')
FILES = ['image.png', 'image (1).png', 'image (2).png', 'image (3).png', 'image (4).png']

QUESTION = (
    'You are helping decide which of these images can be inserted into a scientific paper. '
    'For the image, report: (1) one-line summary of what it is; (2) type: schematic/flow diagram, '
    'bar/line chart, screenshot of code or a terminal, or other; (3) every piece of text you can '
    'read, especially titles, axis labels, legend entries, box labels and any numbers; (4) whether '
    'it contains any factual claim about data. Be literal and concise.'
)


def ask(paths, question, key, model='deepseek-flash', max_tokens=4000):
    content = [{'type': 'text', 'text': question}]
    for p in paths:
        mime = MIME.get(os.path.splitext(p)[1].lower(), 'image/png')
        b64 = base64.b64encode(open(p, 'rb').read()).decode()
        content.append({'type': 'text', 'text': 'IMAGE FILE: %s' % os.path.basename(p)})
        content.append({'type': 'image_url',
                        'image_url': {'url': 'data:%s;base64,%s' % (mime, b64)}})
    body = {'model': model,
            'messages': [{'role': 'user', 'content': content}],
            'max_tokens': max_tokens, 'temperature': 0}
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return 'HTTP %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:500])
    ch = d.get('choices', [{}])[0]
    msg = ch.get('message', {})
    content_out = (msg.get('content') or '').strip()
    reasoning = (msg.get('reasoning_content') or '').strip()
    finish = ch.get('finish_reason')
    if content_out:
        return content_out + (('\n[truncated: finish_reason=%s]' % finish) if finish == 'length' else '')
    if reasoning:
        return '[no final answer, finish=%s]\nreasoning:\n%s' % (finish, reasoning[:3000])
    return '[empty, finish=%s] %s' % (finish, json.dumps(d)[:500])


def main():
    key = load_key()
    if not key:
        print('no key')
        return 1
    paths = [os.path.join(DOWNLOADS, f) for f in FILES]
    paths = [p for p in paths if os.path.exists(p)]
    print('images:', [os.path.basename(p) for p in paths])
    out = ask(paths, QUESTION, key)
    with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                              'results', 'chatgpt_image_descriptions.txt'),
                 'w', encoding='utf-8', newline='\n') as f:
        f.write(out)
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
