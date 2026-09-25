"""Verify that the five concept figures are really inside paperA_R1R2.pdf.

Compiling without error is not evidence that an image landed in the PDF: a misnamed
file or a float dropped by the layout engine both compile cleanly. This reads the
PDF's own object stream and reports every embedded image XObject with its pixel
dimensions, then checks each expected figure size is present.

No third-party PDF library is available on this machine (no pymupdf, no pypdf), and
these PDFs are uncompressed-object output from pdflatex, so a direct byte scan is
sound here.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PDF = os.path.join(HERE, '..', 'paper', 'latex', 'paperA_R1R2.pdf')

# name -> (width, height) of the PNG placed on disk, or None for a vector figure.
# fig_framework.png is deliberately absent: the framework panel is now drawn in TikZ
# (fig_framework_tikz.pdf), so the bitmap is a spare, not a figure of the paper.
EXPECTED = {
    'fig_f_f1.png': (2880, 1440),
    'fig_f_f2.png': (2880, 1440),
    'fig_f_f3.png': (2880, 1440),
    'fig_probe_commitment.png': (2880, 1440),
    'fig_framework_tikz.pdf': None,
    'fig_responsiveness.pdf': None,
    'fig_r1_inertness.pdf': None,
    'fig_encoder_scale.pdf': None,
    'fig_aggregate_vs_pergroup.pdf': None,
}


def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    raw = open(pdf, 'rb').read()
    print('pdf            : %s' % os.path.abspath(pdf))
    print('bytes          : %d' % len(raw))
    pages = len(re.findall(rb'/Type\s*/Page[^s]', raw))
    print('pages          : %d' % pages)

    imgs = re.findall(rb'/Subtype\s*/Image[^>]*?/Width\s+(\d+)[^>]*?/Height\s+(\d+)',
                      raw, re.S)
    print('image xobjects : %d' % len(imgs))
    found = set()
    for w, h in imgs:
        found.add((int(w), int(h)))
        print('   embedded %sx%s' % (w.decode(), h.decode()))

    print()
    ok = True
    for name, dims in EXPECTED.items():
        if dims is None:
            continue
        if dims in found:
            print('OK   %-26s %sx%s present in PDF' % (name, dims[0], dims[1]))
        else:
            print('FAIL %-26s %sx%s NOT found in PDF' % (name, dims[0], dims[1]))
            ok = False

    # every \includegraphics the tex asks for must appear in the compile log.
    # The log wraps long paths across lines, so a literal "fig_x.png" search gives
    # false negatives -- observed, and the reason this check was rewritten. Match the
    # stem against the log with all whitespace removed.
    log = os.path.join(os.path.dirname(os.path.abspath(pdf)), 'paperA_R1R2.pass2.log')
    if os.path.exists(log):
        text = re.sub(r'\s+', '', io.open(log, encoding='latin-1').read())
        stems = ['fig_framework_tikz.pdf', 'fig_f_f1.png', 'fig_f_f2.png',
                 'fig_f_f3.png', 'fig_probe_commitment.png', 'fig_responsiveness.pdf',
                 'fig_r1_inertness.pdf', 'fig_encoder_scale.pdf',
                 'fig_aggregate_vs_pergroup.pdf']
        print()
        for s in stems:
            hit = s in text
            print('%s %-30s loaded by pdflatex' % ('OK  ' if hit else 'FAIL', s))
            ok = ok and hit

    print()
    print('RESULT: %s' % ('all concept figures are embedded' if ok else 'PROBLEM'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
