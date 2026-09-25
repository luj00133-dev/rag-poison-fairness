"""Compose the three F-mode schematics into one side-by-side PDF for the markdown source.

The tex composes them with the `subcaption` package, which pandoc does not translate, so
the markdown pass needs the row pre-composed. The three panels are wide (2:1) and stacked
at native aspect they would carry text too small to read, so each is scaled to the same
height and placed side by side with a white gutter, which reproduces the tex layout
closely enough for the docx and for review.

Panel labels (a)/(b)/(c) are drawn on, because the markdown caption is one caption and
the individual panels otherwise lose the labels the tex gives them.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, '..', 'paper', 'figures')
LATEX = os.path.join(HERE, '..', 'paper', 'latex')

PANELS = [('fig_f_f1.png', '(a) F1, balanced count'),
          ('fig_f_f2.png', '(b) F2, preserved nuisance'),
          ('fig_f_f3.png', '(c) F3, cancelled shift')]

PANEL_H = 620          # px, gives ~7-8pt effective text at 140mm print width
GUTTER = 40
LABEL_BAND = 74
MARGIN = 8
LABEL_PT = 34          # px; PIL's default bitmap font is ~11px and is illegible in print


def load_label_font(size=LABEL_PT):
    for name in ('arial.ttf', 'segoeui.ttf', 'calibri.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    ims = []
    for name, label in PANELS:
        im = Image.open(os.path.join(FIGS, name)).convert('RGB')
        w = int(round(im.width * PANEL_H / im.height))
        im = im.resize((w, PANEL_H), Image.LANCZOS)
        ims.append((im, label))

    width = MARGIN * 2 + sum(im.width for im, _ in ims) + GUTTER * (len(ims) - 1)
    canvas = Image.new('RGB', (width, PANEL_H + LABEL_BAND + MARGIN * 2), 'white')

    x = MARGIN
    draw = ImageDraw.Draw(canvas)
    font = load_label_font()
    for im, label in ims:
        canvas.paste(im, (x, MARGIN))
        tw = draw.textlength(label, font=font)
        draw.text((x + (im.width - tw) / 2.0, MARGIN + PANEL_H + 16), label,
                  fill='black', font=font)
        x += im.width + GUTTER

    out_pdf = os.path.join(FIGS, 'fig_failure_modes.pdf')
    canvas.save(out_pdf, 'PDF', resolution=300.0)
    canvas.save(os.path.join(FIGS, 'fig_failure_modes.png'), 'PNG')
    print('composed %dx%d px -> %s' % (canvas.width, canvas.height, out_pdf))
    print('also wrote fig_failure_modes.png')

    # keep the tex directory in step, for anyone re-running the tex by hand
    print('note: the tex composes the same three panels with subcaption, so it does not '
          'need this file')


if __name__ == '__main__':
    main()
