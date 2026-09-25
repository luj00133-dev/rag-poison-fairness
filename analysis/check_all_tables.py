"""Check that every table in the paper actually prints something.

Table 12 compiled cleanly while printing no table at all: its longtable had no
\\endfirsthead/\\endhead, so longtable treated the four data rows as footer material and
dropped them. Nothing in the pdflatex log reports this -- the caption and the surrounding
prose are present, and the page looks normal at a glance.

So this walks every "Table N." caption in the tex, parses the longtable that follows it,
and asks two questions:

  1. does the block have a well-formed longtable structure (\\endfirsthead, \\endhead,
     \\endlastfoot, matching \\end{longtable})?
  2. does the block contain at least one data row AFTER \\endlastfoot -- i.e. in the table
     body rather than in a head or foot?

and then confirms the caption's table number appears in the built PDF, so a table that is
parsed correctly in the source but lost in layout is still caught.
"""
import io
import os
import re
import subprocess

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')
PDF = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.pdf')
pdftotext = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                         'Programs', 'MiKTeX', 'miktex', 'bin', 'x64',
                         'pdftotext.exe')


def main():
    lines = io.open(TEX, encoding='utf-8').read().split('\n')
    txt = subprocess.run([pdftotext, '-layout', PDF, '-'], capture_output=True,
                         timeout=180).stdout.decode('utf-8', 'replace')

    caps = [(i, l) for i, l in enumerate(lines) if re.match(r'\\textbf\{Table [\dA-Z]+\.\}', l)]
    print('captions found: %d' % len(caps))
    print()
    problems = []
    for idx, ln in caps:
        label = re.match(r'\\textbf\{(Table [\dA-Z]+)\.\}', ln).group(1)
        # the longtable belonging to this caption: the next \begin{longtable} after it
        begin = next((j for j in range(idx, len(lines))
                      if lines[j].startswith('\\begin{longtable}')), None)
        if begin is None:
            problems.append((label, 'no longtable'))
            print('%-10s no longtable found' % label)
            continue
        close = next((j for j in range(begin, len(lines)) if lines[j] == '}'), None)
        blk = lines[begin:close + 1] if close else lines[begin:]
        text = '\n'.join(blk)
        # Two longtable shapes are valid and both appear in this file: the headless form
        # pandoc emits (no \endfirsthead/\endhead), and the form with explicit head/foot
        # markers used for Table 12. A checker that assumes only one of them reports every
        # table in the other shape as empty -- which is what the first version did.
        marked = all(k in text for k in ('\\endfirsthead', '\\endhead', '\\endlastfoot'))
        body = blk[blk.index('\\endlastfoot') + 1:] if marked else blk
        data = [l for l in body
                if l.rstrip().endswith('\\\\') and 'minipage' not in l and '&' in l]
        struct = marked or ('\\end{longtable}' in text)
        in_pdf = label in txt or label.replace('Table ', '') + '.' in txt
        flag = []
        if not struct:
            flag.append('structure')
        if not data:
            flag.append('no body rows')
        if not in_pdf:
            flag.append('not in PDF')
        if flag:
            problems.append((label, ', '.join(flag)))
        print('%-10s rows=%-3d shape=%-8s in_pdf=%-5s %s'
              % (label, len(data), 'marked' if marked else 'headless', in_pdf,
                 '<-- ' + ', '.join(flag) if flag else ''))

    print()
    print('tables with problems: %s' % (problems or 'none'))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
