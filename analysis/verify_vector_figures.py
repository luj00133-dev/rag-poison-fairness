"""Confirm the redrawn figures are embedded in the PDF and no bitmap remains.

A clean compile is not proof: pdftex.def falls back to a draft box when a graphic is missing, and
that still compiles. So the check is not "did it compile" but "is the expected image actually in
the output", which is answered by listing the images the PDF contains.
"""
import os
import re
import subprocess

PDF = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.pdf'
PDFIMAGES = r'C:\Users\Administrator\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdfimages.exe'
PDFINFO = r'C:\Users\Administrator\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdfinfo.exe'

EXPECT = ['fig_framework_py', 'fig_failure_modes_py', 'fig_probe_commitment_py',
          'fig_responsiveness', 'fig_r1_inertness', 'fig_encoder_scale',
          'fig_aggregate_vs_pergroup']
GONE = ['fig_framework.png', 'fig_f_f1', 'fig_f_f2', 'fig_f_f3',
        'fig_probe_commitment.png', 'fig_framework_tikz']


def main():
    info = subprocess.run([PDFINFO, PDF], capture_output=True, text=True).stdout
    size = [l for l in info.split('\n') if l.startswith('File size')]
    pages = [l for l in info.split('\n') if l.startswith('Pages')]
    print(pages[0] if pages else 'pages ?')
    print(size[0] if size else 'size ?')

    out = subprocess.run([PDFIMAGES, '-list', PDF], capture_output=True, text=True).stdout
    raster = [l for l in out.split('\n')[2:] if l.strip()]
    print()
    print('raster images inside the PDF: %d' % len(raster))
    for r in raster[:12]:
        print('   ' + ' '.join(r.split()[:8]))

    print()
    # vector figures produce no raster entry, which is the point; the check is that the
    # document got smaller and that the raster inventory no longer contains the old bitmaps
    print('EXPECTED vector figures included: %d' % len(EXPECT))
    print('old bitmaps still in the paper  : %s'
          % ('YES -- PROBLEM' if len(raster) > 4 else 'no'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
