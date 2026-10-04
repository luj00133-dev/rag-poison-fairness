"""Fix the spacing the linter flagged before the Oliveira citation.

The lint rule "space before \\citet (use ~)" fired because the new citation was inserted as
"and \\citet{oliveira2026}" rather than "and~\\citet{oliveira2026}". A plain space there lets
LaTeX break the line between the conjunction and the citation, which reads badly; the tilde is the
conventional fix and the linter enforces it.

Written as a file because two shell attempts failed to match the backslash through the heredoc.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')


def main():
    s = io.open(TEX, encoding='utf-8').read()
    bad = 'and ' + chr(92) + 'citet{oliveira2026}'
    good = 'and~' + chr(92) + 'citet{oliveira2026}'
    print('occurrences of the space form: %d' % s.count(bad))
    if s.count(bad) == 1:
        s = s.replace(bad, good, 1)
        io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
        print('replaced with a non-breaking space')
    elif s.count(good) == 1:
        print('already uses the tilde form')
    else:
        print('neither form found; nothing written')
        return 1

    s2 = io.open(TEX, encoding='utf-8').read()
    print('tilde form present: %s' % (good in s2))
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in s2:
            print('FAIL: missing %s' % needed)
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
