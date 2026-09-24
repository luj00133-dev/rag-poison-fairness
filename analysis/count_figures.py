"""Count figures and tables in the papers this work is positioned against.

The question is whether Paper A's zero figures and twenty tables is unusual for this
literature, and the only way to answer it is to count. arXiv's HTML rendering carries
figure captions, so the fetched full texts give the numbers directly.

Two caveats that matter for how the result is read:
  * the count includes sub-figures, because a "Figure 6 (a)-(f)" panel grid is six
    images in the PDF and one caption in the text. Reference counts are reported
    alongside caption counts to bound this.
  * these are preprints of conference and journal papers, so the counts reflect the
    authors' choice rather than a hard venue limit.
"""
import glob
import io
import os
import re
import sys

#: saved full texts, by paper
SOURCES = {
    'FARO (Zhao et al. 2026)': None,
}


def count(text):
    """Captions and in-text mentions of figures and tables."""
    fig_caps = len(re.findall(r'(?m)^\s*Figure\s+\d+\s*[:.]', text))
    fig_refs = len(set(re.findall(r'Figure\s+(\d+)', text)))
    tab_caps = len(re.findall(r'(?m)^\s*Table\s+\d+\s*[:.]', text))
    tab_refs = len(set(re.findall(r'Table\s+(\d+)', text)))
    # panel sub-figures: "(a) ... (b) ..." markers adjacent to a figure caption
    panels = 0
    for m in re.finditer(r'(?m)^\s*Figure\s+\d+\s*[:.]', text):
        window = text[m.start():m.start() + 400]
        panels += len(set(re.findall(r'\(([a-h])\)', window)))
    return {
        'fig_captions': fig_caps,
        'fig_numbers': fig_refs,
        'panels_in_first_figure': panels,
        'tab_captions': tab_caps,
        'tab_numbers': tab_refs,
    }


def main():
    paths = sys.argv[1:]
    if not paths:
        paths = glob.glob(os.path.join(
            os.environ.get('TEMP', '/tmp'),
            'dsh-spill-*', 'session-*', '*get_fulltext.txt'))
    if not paths:
        print('no full-text files found; pass paths as arguments')
        return 1
    print('%-34s %8s %8s %8s %8s' % (
        'paper', 'fig caps', 'fig nums', 'tab caps', 'tab nums'))
    for p in paths:
        text = io.open(p, encoding='utf-8', errors='replace').read()
        title = ''
        for line in text.split('\n')[:6]:
            if line.strip() and 'Paper:' not in line and 'Authors:' not in line:
                title = line.strip()[:32]
                break
        c = count(text)
        print('%-34s %8d %8d %8d %8d' % (
            title, c['fig_captions'], c['fig_numbers'],
            c['tab_captions'], c['tab_numbers']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
