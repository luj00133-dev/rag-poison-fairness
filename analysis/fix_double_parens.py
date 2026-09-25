"""Remove the two doubled parentheses that \\citeyearpar leaves inside existing brackets.

\\citeyearpar prints "(2020)", so placing it inside a parenthesis the sentence already has
gives "((2020))" -- visible in the built PDF at two sites. natbib's \\citeyear prints the
bare year, which is what is wanted inside an existing bracket.

Both sites, in the built text:
  "...generation (RAG; ((2020))) has become..."            -> "(RAG; 2020)"
  "...EAE-D statistic of Kim & Diaz ((2025)) was..."        -> "of Kim \\& Diaz (2025)"

The second is written as an explicit author string because natbib's narrative form for a
two-author label prints "Kim & Diaz" and the sentence wants exactly that.
"""
import io

TEX = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.tex'

EDITS = [
    ('(RAG; \\citeyearpar{lewis2020})', '(RAG; \\citeyear{lewis2020})',
     'bare year inside the existing bracket'),
    ('statistic of \\citeauthor{kim2025b} (\\citeyearpar{kim2025b}) was implemented',
     'statistic of Kim \\& Diaz (\\citeyear{kim2025b}) was implemented',
     'author string plus bare year'),
]


def main():
    s = io.open(TEX, encoding='utf-8').read()
    for old, new, why in EDITS:
        n = s.count(old)
        print('%-56s %d match(es)  [%s]' % (old[:56], n, why))
        if n != 1:
            print('NOT WRITTEN: an edit did not match exactly once')
            return 1
        s = s.replace(old, new, 1)
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print('written.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
