"""Trace why make_docx failed to embed the figures.

The compile step writes a DOCX with zero embedded images and raises
UnrecognizedImageError. The PNGs are valid (`Image.from_file` loads them, Pillow
reports RGBA 2078x992), so the fault is in the path resolution or the match, not the
files. This walks the exact code path for each manuscript image line and prints what
it resolves to.
"""
import io
import os
import re

MD = os.path.join('paper', 'manuscript_R1R2_v1.md')
PAT = re.compile(
    r'^!\[(?P<cap>[^\]]*)\]\((?P<path>[^)]+)\)'
    r'(?:\{width=(?P<w>[0-9.]+)(?P<u>mm|cm|in)\})?\s*$')

s = io.open(MD, encoding='utf-8').read()
lines = s.split('\n')
print('image lines found by scanning for "![" : %d' % s.count('!['))
print()

matched = 0
for i, line in enumerate(lines, 1):
    if '![' not in line:
        continue
    m = PAT.match(line.strip())
    print('line %d: match=%s' % (i, bool(m)))
    if not m:
        print('   raw: %r' % line[:110])
        continue
    matched += 1
    src = m.group('path')
    png = os.path.splitext(src)[0] + '.png'
    cand = png if os.path.exists(png) else src
    if not os.path.isabs(cand):
        cand = os.path.join(os.path.dirname(MD), cand)
    print('   caption  : %s' % m.group('cap')[:56])
    print('   declared : %s%s' % (m.group('w'), m.group('u')))
    print('   resolved : %s  exists=%s' % (cand, os.path.exists(cand)))
    if os.path.exists(cand):
        from docx.image.image import Image as DocxImage
        try:
            im = DocxImage.from_file(cand)
            print('   docx img : %dx%d %s' % (im.px_width, im.px_height,
                                              im.content_type))
        except Exception as exc:
            print('   docx img : FAILED %s' % type(exc).__name__)

print()
print('matched %d image line(s)' % matched)
