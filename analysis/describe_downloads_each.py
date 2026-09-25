"""Describe each downloaded ChatGPT image separately, with a budget large enough to finish.

The batched attempt returned finish_reason=length with the answer still inside
reasoning_content: five 2K-resolution PNGs are a lot of prompt, and this model spends the
budget reasoning before it emits content. So: one image per request, 8000 tokens, and
reasoning_content is captured as a fallback so a truncation stays visible instead of
looking like a refusal.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from describe_image import load_key
from describe_downloads import ask

DOWNLOADS = os.path.join(os.path.expanduser('~'), 'Downloads')
FILES = ['image.png', 'image (1).png', 'image (2).png', 'image (3).png', 'image (4).png']

QUESTION = (
    'Describe this image literally and completely for someone who cannot see it. '
    'First say what kind of image it is (schematic / flow diagram / bar chart / line chart / '
    'screenshot of code / screenshot of a chat / other). Then transcribe ALL visible text, '
    'including the title, every box label, every arrow label, every axis label and tick, and '
    'every number. Then describe the layout: how many panels, what is in each panel, what '
    'connects to what. Finally say whether the image presents empirical data (real numbers from '
    'an experiment) or is conceptual. Do not speculate beyond what is visible.'
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results',
                   'chatgpt_image_descriptions.txt')


def main():
    key = load_key()
    if not key:
        print('no key')
        return 1
    chunks = []
    for name in FILES:
        p = os.path.join(DOWNLOADS, name)
        if not os.path.exists(p):
            continue
        txt = ask([p], QUESTION + '\n\nThis image is: ' + name, key, max_tokens=8000)
        block = '=' * 78 + '\n' + name + '\n' + '=' * 78 + '\n' + txt + '\n'
        chunks.append(block)
        print(block, flush=True)
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(chunks))
    print('wrote', OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
