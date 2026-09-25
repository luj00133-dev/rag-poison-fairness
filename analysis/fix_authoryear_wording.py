"""Two wording fixes the author-date conversion exposed.

1. "(RAG) [1]" became "(RAG; \\citep{lewis2020})", which prints with a doubled
   parenthesis: "(RAG; (Lewis et al., 2020))". Inside an existing parenthesis the year
   alone is wanted, so the command is \\citeyearpar.

2. "the EAE-D statistic of [8]" became "of \\citet{kim2025b}", and \\citet at that
   position prints "of Kim & Diaz (2025)" -- the sentence wants the author name without
   the "and", and natbib's narrative form for a two-author label uses an ampersand in
   author-date mode regardless. Rewritten as an explicit author + year so the possessive
   phrase reads naturally.

Written as a file rather than inline because the previous inline attempt died on an
undefined \\citeyear and wrote nothing, leaving the edit half-planned and unapplied.
"""
import io

TEX = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.tex'

EDITS = [
    ('(RAG; \\citep{lewis2020})', '(RAG; \\citeyearpar{lewis2020})',
     'doubled parenthesis around the acronym and its year'),
    ('statistic of \\citet{kim2025b} was implemented',
     'statistic of \\citeauthor{kim2025b} (\\citeyearpar{kim2025b}) was implemented',
     'author name in a possessive phrase'),
]


def main():
    s = io.open(TEX, encoding='utf-8').read()
    ok = True
    for old, new, why in EDITS:
        n = s.count(old)
        print('%-52s %d match(es)  [%s]' % (old[:52], n, why))
        if n != 1:
            ok = False
            continue
        s = s.replace(old, new, 1)
    if not ok:
        print('NOT WRITTEN: an edit did not match exactly once')
        return 1
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print('written.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
