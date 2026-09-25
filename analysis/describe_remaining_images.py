"""Describe the ChatGPT concept images that were never described, on the working vision route.

The earlier per-image run (analysis/describe_downloads_each.py) finished image.png and
image (1).png and then died with UnicodeEncodeError on a GBK console -- its own logging
bug, not an API failure. Images (2), (3) and (4) therefore have no description anywhere
on disk, and they are 2:1 candidates for Paper A.

This run reuses the working DeepSeek vision route, writes UTF-8 explicitly (PYTHONIOENCODING
is not relied on), one image per request, and appends so a later crash cannot erase an
earlier description.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from describe_image import load_key, describe  # noqa: E402

DOWNLOADS = os.path.join(os.path.expanduser('~'), 'Downloads')
FILES = ['image (2).png', 'image (3).png', 'image (4).png']
OUT = os.path.join(HERE, '..', 'results', 'chatgpt_image_descriptions_2_3_4.txt')

QUESTION = (
    'Describe this image literally and completely for someone who cannot see it and must '
    'write its LaTeX caption. First say what kind of image it is (schematic / flow diagram '
    '/ bar chart / line chart / screenshot / other) and how many panels it has. Then '
    'transcribe EVERY piece of visible text: title, panel labels, box labels, arrow labels, '
    'axis labels and ticks, legend entries, and every number. Then describe the layout: what '
    'is in each panel, what connects to what, and the reading order. Finally, state whether '
    'the image presents empirical data (real measured numbers) or is purely conceptual, and '
    'whether any text is clipped, garbled or misspelled. Do not speculate beyond what is visible.'
)


def main():
    key = load_key()
    if not key:
        sys.stderr.write('no DeepSeek key available\n')
        return 1
    chunks = []
    for name in FILES:
        path = os.path.join(DOWNLOADS, name)
        if not os.path.exists(path):
            sys.stderr.write('missing: %s\n' % path)
            continue
        text = describe(path, QUESTION, 'deepseek-flash', 8000, key)
        block = '%s\n%s\n%s\n%s\n' % ('=' * 78, name, '=' * 78, text)
        chunks.append(block)
        with io.open(OUT, 'a', encoding='utf-8', newline='\n') as fh:
            fh.write(block)
        sys.stdout.buffer.write(block.encode('utf-8', 'replace'))
        sys.stdout.buffer.flush()
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(''.join(chunks))
    sys.stdout.buffer.write(('wrote %s\n' % OUT).encode('utf-8'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
