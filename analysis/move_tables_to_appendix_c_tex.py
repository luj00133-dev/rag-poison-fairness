"""Mirror the markdown table move in the LaTeX source (Tables 5/7/10/11 -> C6-C9).

The two sources are edited separately because the tex is what the PDF is built from
and the markdown is what the docx is built from; leaving one behind means the two
disagree about how many tables the paper has, which is exactly the bug this pair of
scripts exists to prevent.

The tex tables are pandoc longtables, so the unit to move is not a line but a group:
one or more `{\\def\\LTcaptype{none} ... \\end{longtable} }` blocks, plus the caption
and any `\\emph{...}` sub-labels between them. Ranges are given explicitly, taken from
a read of the file, because inferring them from the caption alone is not reliable for
Table 5 (two longtables under one caption).

Anchors are checked before any write; the script refuses to half-apply.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', 'paper', 'latex', 'paperA_R1R2.tex')

# (name, first line, last line, new label) -- 1-based inclusive, from reading the file
BLOCKS = [
    ('Table 5', 625, 698, 'Table C6'),
    ('Table 7', 736, 750, 'Table C7'),
    ('Table 10', 892, 917, 'Table C8'),
    ('Table 11', 921, 952, 'Table C9'),
]

POINTERS = {
    'Table 5': 'The sweep itself is in Appendix C, Table C6.',
    'Table 7': 'The operating-point comparison is in Appendix C, Table C7.',
    'Table 10': 'The decomposition is in Appendix C, Table C8.',
    'Table 11': 'The cross-back-end cut is in Appendix C, Table C9.',
}

# Appendix insertion point: the closing brace of Table C5's longtable group, i.e. the
# last line before the rule that precedes the AI declaration. Two earlier attempts
# anchored on C5's final DATA ROW, which is inside the longtable -- the new tables then
# landed inside it and pdflatex reported 23 alignment errors. Anchor on the end of the
# environment, and assert that the line after it is not part of a table.
APPENDIX_ANCHOR = ('template\\_plus\\_projection & dense & R1 drift (TV) & 0.1625 '
                   '& {[}0.1187, 0.2083{]} ' + '\\\\' + '\n'
                   '\\end{longtable}\n'
                   '}')


def main():
    lines = io.open(TEX, encoding='utf-8').read().split('\n')

    # verify every block boundary before touching anything
    for name, a, b, _ in BLOCKS:
        head = lines[a - 1]
        tail = lines[b - 1]
        if not head.startswith('\\textbf{%s.}' % name):
            print('HEAD FAIL %s: %r' % (name, head[:70]))
            return 1
        if not (tail.startswith('\\end{longtable}') or tail == '}'):
            print('TAIL FAIL %s: %r' % (name, tail[:70]))
            return 1

    # extract from the bottom up so earlier indices stay valid
    moved = []
    for name, a, b, new in sorted(BLOCKS, key=lambda x: -x[1]):
        block = lines[a - 1:b]
        block = [block[0].replace('%s.' % name, '%s.' % new, 1)] + block[1:]
        moved.append((new, block))
        lines[a - 1:b] = [POINTERS[name], '']
        print('moved %-9s -> %-9s (%d lines)' % (name, new, len(block)))
    moved.reverse()

    s = '\n'.join(lines)

    if APPENDIX_ANCHOR not in s:
        print('APPENDIX ANCHOR FAIL')
        return 1
    add = []
    for new, block in moved:
        add.append('')
        add.extend(block)
    s = s.replace(APPENDIX_ANCHOR, APPENDIX_ANCHOR + '\n' + '\n'.join(add), 1)

    for name, _, _, new in BLOCKS:
        s = re.sub(r'\\textbf{%s\.}' % name, '\\textbf{%s.}' % new, s)
        s = re.sub(r'(?<![\w.])%s(?![\w.])' % name, new, s)

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    print('body tables now    : %d' % len(re.findall(r'\\textbf\{Table \d+\.\}', s)))
    print('appendix tables now: %d' % len(re.findall(r'\\textbf\{Table [A-Z]\d+\.\}', s)))
    stale = re.findall(r'(?<![\w.])Table (?:5|7|10|11)(?![\w.])', s)
    print('stale references   : %d' % len(stale))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
