"""Rebuild Table 12 by replacing an exact LINE RANGE, not by matching braces.

Two earlier attempts failed on the container, not the content:

  1. the first emitted a longtable without \\endfirsthead / \\endhead, so longtable treated
     the data rows as footer material and printed no table at all -- caption, then prose;
  2. the second found the group's opening brace with rfind('{'), which landed on the brace
     of \\def\\LTcaptype{ and produced "{\\def\\LTcaptype{\\def\\LTcaptype{none}" -- 24
     LaTeX errors and no PDF.

So this version works on lines. It finds the caption line, then the next
"\\begin{longtable}" line, walks back to the line that opens the group ("{\\def\\LTcaptype")
and forward to the line after the matching "}", and replaces that range. Verification parses
the resulting file rather than counting markers.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')
BACKUP = TEX + '.pre-t12'

HEADERS = ['Generator', r'\(\Delta\) gap (absolute)', 'p',
           r'\textbf{\(\Delta\) group 1}', 'p', r'\textbf{\(\Delta\) group 2}', 'p']
ROWS = [
    ['qwen-turbo', '+0.0008', '0.32', r'\textbf{-0.1297}', r'\textbf{<0.0001}',
     r'\textbf{+0.1305}', r'\textbf{<0.0001}'],
    ['qwen-plus', '+0.0018', '0.042', r'\textbf{-0.1280}', r'\textbf{0.0035}',
     r'\textbf{+0.1298}', r'\textbf{0.0015}'],
    ['qwen-max', '-0.0491', '0.18', r'\textbf{-0.1785}', r'\textbf{0.0001}',
     r'\textbf{+0.1294}', r'\textbf{0.0029}'],
    [r'\textbf{mistral-7b} (local, open weights)', '+0.0025', '0.42',
     r'\textbf{-0.1297}', r'\textbf{0.0001}', r'\textbf{+0.1322}', r'\textbf{<0.0001}'],
]


def header_row():
    cells = ['\\begin{minipage}[b]{\\linewidth}\\raggedright\n%s\n\\end{minipage}' % h
             for h in HEADERS]
    return ' & '.join(cells) + r' \\'


def build():
    n = len(HEADERS)
    frac = ' * \\real{%.4f}' % (1.0 / n)
    colspec = '\n'.join(
        '  >{\\raggedright\\arraybackslash}p{(\\linewidth - %d\\tabcolsep)%s}'
        % (2 * (n - 1), frac) for _ in range(n))
    return '\n'.join([
        r'{\def\LTcaptype{none} % do not increment counter',
        r'\begin{longtable}[]{@{}',
        colspec + '@{}}',
        r'\toprule\noalign{}',
        header_row(),
        r'\midrule\noalign{}',
        r'\endfirsthead',
        r'\toprule\noalign{}',
        header_row(),
        r'\midrule\noalign{}',
        r'\endhead',
        r'\bottomrule\noalign{}',
        r'\endlastfoot',
    ] + [' & '.join(r) + r' \\' for r in ROWS] + [r'\end{longtable}', '}'])


def main():
    lines = io.open(BACKUP, encoding='utf-8').read().split('\n')
    cap = next((i for i, l in enumerate(lines) if l.startswith('\\textbf{Table 12.}')), None)
    if cap is None:
        print('caption line not found')
        return 1
    begin = next(i for i in range(cap, len(lines)) if lines[i].startswith('\\begin{longtable}'))
    open_i = max(i for i in range(cap, begin) if lines[i].startswith('{\\def\\LTcaptype'))
    close_i = next(i for i in range(begin, len(lines)) if lines[i] == '}')
    print('replacing lines %d..%d (%d lines)' % (open_i + 1, close_i + 1, close_i - open_i + 1))

    new_lines = build().split('\n')
    out = lines[:open_i] + new_lines + lines[close_i + 1:]
    s = '\n'.join(out)
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    # ---- verify by parsing the written file
    s2 = io.open(TEX, encoding='utf-8').read().split('\n')
    cap = next(i for i, l in enumerate(s2) if l.startswith('\\textbf{Table 12.}'))
    begin = next(i for i in range(cap, len(s2)) if s2[i].startswith('\\begin{longtable}'))
    close = next(i for i in range(begin, len(s2)) if s2[i] == '}')
    blk = s2[begin:close + 1]
    text = '\n'.join(blk)
    print()
    print('\\endfirsthead     : %s' % ('\\endfirsthead' in text))
    print('\\endhead          : %s' % ('\\endhead' in text))
    print('\\endlastfoot      : %s' % ('\\endlastfoot' in text))
    print('nested \\def count  : %d (must be 1)' % text.count('\\def\\LTcaptype'))
    body = blk[blk.index('\\endlastfoot') + 1:]
    data = [l for l in body if l.rstrip().endswith('\\\\')]
    print('data rows          : %d (must be 4)' % len(data))
    print('all rows 7 columns : %s' % all(l.count('&') == 6 for l in data))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
