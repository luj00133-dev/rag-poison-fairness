"""Inspect how figures and tables are labelled and cited in both sources.

Two suspected defects to confirm precisely:

  1. no figure in the paper is numbered, and no numbered figure is cited anywhere -- which is
     invalid for a journal article, since readers and reviewers expect "Figure 1" to resolve;
  2. the numbered table sequence is 1,2,3,4,6,8,9,12,13,14,15 with 5, 7, 10, 11 absent and
     uncited.

Neither may be real: the tex may carry figure numbering that the docx pipeline strips. This
reports the actual state of both files rather than my guess about either.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')


def show(label, text):
    print('=' * 70)
    print(label)
    print('=' * 70)
    caps = re.findall(r'\\caption\{', text)
    print('  \\caption{ count            : %d' % len(caps))
    print('  figure labels (fig:...)    : %d' % len(re.findall(r'\\label\{fig:', text)))
    print('  table  labels (tab:...)    : %d' % len(re.findall(r'\\label\{tab:', text)))
    print('  "Figure N" citations       : %d' % len(re.findall(r'Figure[~ ]\s*\d', text)))
    print('  "Fig. N" citations         : %d' % len(re.findall(r'Fig\.\s*\d', text)))
    print('  "\\ref{fig:" citations      : %d' % len(re.findall(r'\\ref\{fig:', text)))
    print('  "Table N" citations        : %d' % len(re.findall(r'Table[~ ]\s*[A-Z]?\d', text)))
    # figure caption openings
    print()
    print('  caption openings:')
    for m in re.finditer(r'\\caption\{([^\n]{0,88})', text):
        print('     %s' % ' '.join(m.group(1).split())[:86])
    print()
    print('  image includes:')
    for m in re.finditer(r'\\includegraphics[^{]*\{([^}]+)\}', text):
        print('     %s' % m.group(1))


def main():
    md = io.open(MD, encoding='utf-8').read()
    tex = io.open(TEX, encoding='utf-8').read()

    show('LATEX', tex)
    print()
    print('=' * 70)
    print('MARKDOWN')
    print('=' * 70)
    print('  image includes            : %d' % len(re.findall(r'!\[', md)))
    print('  "Figure N" citations      : %d' % len(re.findall(r'Figure\s*\d', md)))
    print('  numbered table captions   : %s' % re.findall(r'\*\*Table ([A-Z]?\d+)\.', md))
    print()
    print('  table citations found in text:')
    cited = sorted(set(re.findall(r'Table\s+([A-Z]?\d+)', md)))
    print('     %s' % cited)
    nums = [c for c in re.findall(r'\*\*Table ([A-Z]?\d+)\.', md) if c.isdigit()]
    print('     captions present : %s' % sorted(nums, key=int))
    print('     cited but no caption: %s' % [c for c in cited if c.isdigit() and c not in nums])
    print('     caption but never cited: %s'
          % [c for c in sorted(nums, key=int)
             if len(re.findall(r'Table\s+%s\b' % c, md)) <= 1])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
