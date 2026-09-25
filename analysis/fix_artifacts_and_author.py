"""Fix the \\$-\\$ artifacts: a minus sign inside a dollar sign, which prints as "$-$".

The pandoc conversion wrote negative numbers variously as "\\$-\\$0.1297" or "\\$-\\$0.13",
which typesets as "$-$0.1297" -- a literal dollar sign, a hyphen, a dollar sign, then the
number. The correct form is a math-mode minus: "\\(-0.1297\\)".

Also sets the author name. The tex has "Jiang Lu"; the author's Chinese name is 江璐, whose
surname is Lu and given name Jiang, so the Chinese convention (surname first) gives
"Lu Jiang" -- which is also what the repository's git identity uses and matches the email
lujiang12@njust.edu.cn, where "lu" is the surname. The previous order printed the name in
Western order, which is inconsistent with the email and with the metadata already in the
docx.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')


def main():
    s = io.open(TEX, encoding='utf-8').read()
    before = s

    # 1. "\$-\(NUMBER" -> "\(-NUMBER"  (the number may still be followed by ** leftovers)
    pat = re.compile(r'\\\$-\\\((\d)')
    n1 = len(pat.findall(s))
    s = pat.sub(r'\\(-\1', s)
    print('dollar-minus artifacts fixed : %d' % n1)

    # any remaining bare "\$-" or "-\$" pairs
    n2 = len(re.findall(r'\\\$-|-\$', s))
    s = s.replace('\\$-', '-').replace('-$', '-')
    print('other stray dollar signs     : %d' % n2)

    # 2. author name
    n3 = s.count('Jiang Lu')
    s = s.replace('Jiang Lu', 'Lu Jiang')
    print('author name occurrences fixed: %d ("Jiang Lu" -> "Lu Jiang")' % n3)

    # 3. report remaining markdown-bold debris anywhere in the file
    debris = re.findall(r'\*\*[^*\n]{0,40}\*\*', s)
    print('markdown bold debris left    : %d %s' % (len(debris), debris[:4]))

    if s == before:
        print('nothing changed')
        return 0
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    # ---- verify
    s2 = io.open(TEX, encoding='utf-8').read()
    print()
    print('after: "\\$-" occurrences   : %d' % s2.count('\\$-'))
    print('after: "Jiang Lu"           : %d' % s2.count('Jiang Lu'))
    print('after: "Lu Jiang"           : %d' % s2.count('Lu Jiang'))
    auth = re.search(r'\\author\[[^\]]*\]\{[^}]*\}', s2)
    print('author line                 : %s' % (auth.group(0) if auth else '?'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
