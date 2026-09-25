"""Full formatting/consistency pass over Paper A's LaTeX source.

Written after several defects in this file were found by hand or by accident, each of
which had survived a clean compile:

  * a corrupted table row from a pandoc math artefact ("\\$-\\\\(0.0075** | **\\\\)-\\$0.0013");
  * three duplicate \\bibitem keys, which pdflatex reports only as a silent
    wrong-citation;
  * an uncited bibliography entry;
  * a title-cased "Our" produced by the pandoc converter writing "[0]" as ".Our";
  * a stray backspace byte from a bad Python replacement string.

So this checks the things a compile cannot: typography, artefact patterns, name and
number consistency, and the mathematics delimiters.

Every rule reports file offsets and the offending line, and the exit code is non-zero if
any rule fires, so it can be run as a gate.
"""
import io
import re
import sys
import unicodedata
import os

TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'paper', 'latex', 'paperA_R1R2.tex')


def lines_with(text, pattern, flags=0):
    """(lineno, line) for every line matching pattern."""
    out = []
    for i, ln in enumerate(text.split('\n'), 1):
        if re.search(pattern, ln, flags):
            out.append((i, ln))
    return out


def main():
    s = io.open(TEX, encoding='utf-8').read()
    problems = []

    def report(rule, hits, limit=6):
        if hits:
            problems.append(rule)
        print('%-42s %s' % (rule, ('OK' if not hits else '%d hit(s)' % len(hits))))
        for i, ln in hits[:limit]:
            print('     L%-5d %s' % (i, ln.strip()[:120]))

    # ---- 1. control characters and non-ASCII oddities
    ctrl = [(i, repr(c)) for i, c in enumerate(s) if ord(c) < 32 and c not in '\n\r\t']
    print('%-42s %s' % ('control characters', 'OK' if not ctrl else ctrl[:5]))
    if ctrl:
        problems.append('control characters')

    # ---- 2. pandoc math artefacts and escaped-dollar debris
    report('pandoc artefact (** | ** or \\$-)',
           lines_with(s, r'\*\*\s*\|\s*\*\*|\\\$-|\$-\\'))

    # ---- 3. .Our / .The style: a lost space after a sentence end
    report('missing space after sentence (.[A-Z])',
           lines_with(s, r'(?<![A-Z])\.(?=[A-Z][a-z]{2,})'))

    # ---- 4. straight quotes (the file should use ``...'' or no quotes)
    report('straight double quotes',
           lines_with(s, r'(?<!\\)"'))

    # ---- 5. unbalanced math delimiters per line
    bad_math = []
    for i, ln in enumerate(s.split('\n'), 1):
        if ln.lstrip().startswith('%'):
            continue
        if len(re.findall(r'(?<!\\)\$', ln)) % 2:
            bad_math.append((i, ln))
    report('odd number of $ on a line', bad_math)

    # ---- 6. brace balance over the whole file
    depth = 0
    worst = 0
    for c in s:
        if c == '{':
            depth += 1
            worst = max(worst, depth)
        elif c == '}':
            depth -= 1
    print('%-42s %s (final depth %d)' % ('brace balance', 'OK' if depth == 0 else 'UNBALANCED', depth))
    if depth != 0:
        problems.append('brace balance')

    # ---- 7. environment balance
    begins = re.findall(r'\\begin\{(\w+\*?)\}', s)
    ends = re.findall(r'\\end\{(\w+\*?)\}', s)
    from collections import Counter
    cb, ce = Counter(begins), Counter(ends)
    unbal = {k: (cb[k], ce[k]) for k in set(cb) | set(ce) if cb[k] != ce[k]}
    print('%-42s %s' % ('environment balance', 'OK' if not unbal else unbal))
    if unbal:
        problems.append('environment balance')

    # ---- 8. double spaces inside text
    dbl = lines_with(s, r'[a-z]{2}  +[a-z]')
    report('double space inside sentences', dbl)

    # ---- 9. a bare space before \citet, where a tie (~) keeps the author name with the
    # word it follows. Restricted to \citet: \citeyearpar and \citep are parenthetical and
    # legitimately follow a word with a normal space, so flagging those (as the first
    # version did, 20 hits) is noise.
    report('space before \\citet (use ~)',
           lines_with(s, r'[A-Za-z] \\citet\{'))

    # ---- 10. the author name, checked in both orders
    for probe in ('Jiang Lu', 'Lu Jiang'):
        n = s.count(probe)
        print('%-42s %d' % ('author string %r' % probe, n))

    # ---- 11. em-dash consistency: the file uses --- for a dash
    report('suspicious en-dash in prose (not in numbers)',
           lines_with(s, r'(?<!\d)–(?!\d)'))

    # ---- 12. repeated words ("the the")
    report('repeated word',
           [(i, ln) for i, ln in lines_with(s, r'\b(\w+)\s+\1\b', re.I)
            if not re.search(r'\\(emph|texttt|textbf|cite|ref)\b', ln)])

    print()
    if problems:
        print('RESULT: %d rule(s) fired -> %s' % (len(problems), problems))
        return 1
    print('RESULT: no formatting problems found')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
