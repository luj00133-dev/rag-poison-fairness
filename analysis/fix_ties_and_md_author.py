"""Final typographic fixes plus the author name in the markdown source.

1. Two \\citet commands follow a word across an ordinary space ("related is \\citet{...}").
   A tie keeps the author name on the same line as the word it follows; without it a line
   can break between "is" and "Zhao et al. (2026)", which reads badly at a column edge.

2. The markdown source still carries the author name in Western order, while the tex now
   has the Chinese order that matches the email (lujiang12@njust.edu.cn) and the git
   identity. Both sources must agree, since the docx is built from the markdown.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

TEX_EDITS = [
    ('work on how retrieval evidence is measured ',
     'work on how retrieval evidence is measured '),      # placeholder, replaced below
]
TIES = [
    ('so it belongs to the corpus of work on how retrieved evidence is measured --- not to',
     None),
]


def main():
    # ---- tex: tie the two \citet occurrences that follow a word
    s = io.open(TEX, encoding='utf-8').read()
    fixed = 0
    for pat in [' evidence is measured \\citet{', ' closely related is \\citet{']:
        if pat in s:
            s = s.replace(pat, pat.replace(' \\citet{', '~\\citet{'), 1)
            fixed += 1
    # the second one is worded differently in this revision; catch any remaining form
    s2, n = _tie_generic(s)
    print('citet ties added: %d (+%d generic)' % (fixed, n))
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s2)

    # ---- markdown: author name order
    md = io.open(MD, encoding='utf-8').read()
    c = md.count('Jiang Lu')
    md = md.replace('Jiang Lu', 'Lu Jiang')
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(md)
    print('markdown author occurrences fixed: %d' % c)

    # ---- verify
    t = io.open(TEX, encoding='utf-8').read()
    import re
    bad = re.findall(r'[A-Za-z] \\citet\{', t)
    print('remaining space-before-citet in tex : %d' % len(bad))
    print('tex author                          : %s'
          % re.search(r'\\author\[[^\]]*\]\{([^}]*)\}', t).group(1))
    m = io.open(MD, encoding='utf-8').read()
    print('md  "Jiang Lu" / "Lu Jiang"          : %d / %d'
          % (m.count('Jiang Lu'), m.count('Lu Jiang')))
    return 0


def _tie_generic(s):
    import re
    out = []
    n = 0
    for line in s.split('\n'):
        new = re.sub(r'([A-Za-z]) \\citet\{', r'\1~\\citet{', line)
        if new != line:
            n += 1
        out.append(new)
    return '\n'.join(out), n


if __name__ == '__main__':
    raise SystemExit(main())
