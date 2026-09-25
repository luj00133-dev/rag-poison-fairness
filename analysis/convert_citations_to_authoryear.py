"""Convert Paper A from numeric citations to natbib author-date, in one explicit map.

Why a map and not a rule. The site has to become \\citet when the author name is part of
the sentence ("Zou et al. [2], who showed...") and \\citep when the citation is an aside
("injected passages [2, 3]"). A rule cannot tell those apart, and getting it wrong yields
"Zou et al. (2025) et al., who showed". Two further forms appear in this manuscript and
are handled explicitly:

  * "[5]'s optimisation" and "the re-ranking of [5]"  -> \\citeauthor{...}, because the
    author name is already possessive or already preceded by "of";
  * "except [4], and [4] itself measures"  -> the author name is printed separately as
    "Wang et al.~", so the citations must carry the YEAR ONLY (\\citeyearpar), otherwise
    the sentence reads "Wang et al. Wang et al. (2025)".

Three bracketed numerals are NOT citations -- the confidence interval "[0, 0]", which
appears three times -- and are deliberately left alone.

The document class must take the "authoryear" option for any of this to render; loading
natbib separately clashes, and \\biboptions afterwards has no effect. Both were tried and
both left every citation as "[?]".

Everything is applied in a single pass over the file, so a replacement cannot be
re-matched, and the script refuses to write unless every site in the map is found and no
numeric citation remains.
"""
import io
import re

TEX = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.tex'

# old numeric site -> replacement, in the order the sites appear in the file
SITES = [
    ("[1]",   r"\citep{lewis2020}"),
    ("[2, 3]", r"\citep{zou2025,zhang2025}"),
    ("[4]",   r"\citet{wang2025}"),                              # "Wang et al.~[4] show" -> name removed below
    ("[5]",   r"\citep{zhao2026}"),
    ("[6]",   r"\citep{wu2025}"),
    ("[7]",   r"\citep{kim2025a}"),
    ("[8]",   r"\citep{kim2025b}"),
    ("[8]",   r"\citep{kim2025b}"),
    ("[2]",   r"\citet{zou2025}"),
    ("[3]",   r"\citep{zhang2025}"),
    ("[9]",   r"\citep{liang2026}"),
    ("[10, 11, 12]", r"\citep{ha2025,chang2025,liu2025}"),
    ("[4]",   r"\citeyearpar{wang2025}"),                        # "Wang et al.~[4] combine"
    ("[4]",   r"\citeyearpar{wang2025}"),                        # "except [4]"
    ("[4]",   r"\citeyearpar{wang2025}"),                        # "and [4] itself"
    ("[6]",   r"\citet{wu2025}"),
    ("[7]",   r"\citet{kim2025a}"),
    ("[8]",   r"\citet{kim2025b}"),
    ("[5]",   r"\citet{zhao2026}"),
    ("[7]",   r"\citet{kim2025a}"),
    ("[13]",  r"\citet{bagwe2025}"),
    ("[14]",  r"\citet{dai2024}"),
    ("[15]",  r"\citet{hu2024}"),
    ("[4]",   r"\citeyearpar{wang2025}"),
    ("[16]",  r"\citeyearpar{mohanty2026}"),
    ("[6]",   r"\citeyearpar{wu2025}"),
    ("[17]",  r"\citet{jacobs2021}"),
    ("[18]",  r"\citet{ekstrand2022a}"),
    ("[19]",  r"\citep{ekstrand2022b}"),
    ("[20]",  r"\citep{efron1993}"),
    ("[21, 22]", r"\citep{parrish2022,nadeem2021}"),
    ("[4]",   r"\citeyearpar{wang2025}"),
    ("[4]",   r"\citeyearpar{wang2025}"),
    ("[5]",   r"\citeauthor{zhao2026}"),
    ("[8]",   r"\citeauthor{kim2025b}"),
    ("[4, 6]", r"\citeyearpar{wang2025,wu2025}"),
    ("[0, 0]", "[0, 0]"),                                        # confidence interval, not a citation
    ("[5]",   r"\citeauthor{zhao2026}"),
    ("[6]",   r"\citeauthor{wu2025}"),
    ("[7]",   r"\citeauthor{kim2025a}"),
    ("[8]",   r"\citeauthor{kim2025b}"),
    ("[4]",   r"\citeyearpar{wang2025}"),
    ("[21]",  r"\citep{parrish2022}"),
    ("[2]",   r"\citep{zou2025}"),
    ("[5]",   r"\citeauthor{zhao2026}"),
    ("[8]",   r"\citeauthor{kim2025b}"),
    ("[4, 6]", r"\citeyearpar{wang2025,wu2025}"),
    ("[8]",   r"\citeauthor{kim2025b}"),
    ("[5]",   r"\citeauthor{zhao2026}"),
    ("[6]",   r"\citeauthor{wu2025}"),
    ("[4]",   r"\citeyearpar{wang2025}"),
    ("[19]",  r"\citep{ekstrand2022b}"),
    ("[3]",   r"\citeyearpar{zhang2025}"),
    ("[5]",   r"\citeauthor{zhao2026}"),
    ("[6]",   r"\citeauthor{wu2025}"),
    ("[7]",   r"\citeauthor{kim2025a}"),
    ("[8]",   r"\citeauthor{kim2025b}"),
    ("[5]",   r"\citeauthor{zhao2026}"),
    ("[6]",   r"\citeauthor{wu2025}"),
    ("[7]",   r"\citeauthor{kim2025a}"),
    ("[8]",   r"\citeauthor{kim2025b}"),
    ("[0, 0]", "[0, 0]"),
    ("[0, 0]", "[0, 0]"),
    ("[8]",   r"\citeauthor{kim2025b}"),
    ("[8]",   r"\citeauthor{kim2025b}"),
    ("[4, 7]", r"\citeyearpar{wang2025,kim2025a}"),
    ("[6, 7, 8]", r"\citeyearpar{wu2025,kim2025a,kim2025b}"),
]

# the author name is already printed immediately before these sites, so it must go
NAME_BEFORE = [
    (r"Wang et al.~\{\[\}4\{\]\}", r"\citet{wang2025}"),
    (r"Zou et al.~\{\[\}2\{\]\}", r"\citet{zou2025}"),
    (r"Wu et al.~\{\[\}6\{\]\}", r"\citet{wu2025}"),
    (r"Kim et al.~\{\[\}7\{\]\}", r"\citet{kim2025a}"),
    (r"Kim and Diaz \{\[\}8\{\]\}", r"\citet{kim2025b}"),
    (r"Zhao et al.~\{\[\}5\{\]\}", r"\citet{zhao2026}"),
    (r"Bagwe et al.~\{\[\}13\{\]\}", r"\citet{bagwe2025}"),
    (r"Dai et al.~\{\[\}14\{\]\}", r"\citet{dai2024}"),
    (r"Hu et al.~\{\[\}15\{\]\}", r"\citet{hu2024}"),
    (r"Jacobs and Wallach \{\[\}17\{\]\}", r"\citet{jacobs2021}"),
    (r"Ekstrand et al.~\{\[\}18\{\]\}", r"\citet{ekstrand2022a}"),
    (r"Kim \\& Diaz \{\[\}8\{\]\}", r"\citet{kim2025b}"),
]

# "Zhou [4]" style: the possessive/author name is printed before the site
AUTHOR_BEFORE = [
    (r"of \{\[\}5\{\]\}", r"of \citeauthor{zhao2026}"),
    (r"of \{\[\}6\{\]\}", r"of \citeauthor{wu2025}"),
    (r"of \{\[\}7\{\]\}", r"of \citeauthor{kim2025a}"),
    (r"of \{\[\}8\{\]\}", r"of \citeauthor{kim2025b}"),
    (r"\{\[\}5\{\]\}'s", r"\citeauthor{zhao2026}'s"),
    (r"\{\[\}6\{\]\}'s", r"\citeauthor{wu2025}'s"),
    (r"\{\[\}7\{\]\}'s", r"\citeauthor{kim2025a}'s"),
    (r"\{\[\}8\{\]\}'s", r"\citeauthor{kim2025b}'s"),
]


def main():
    s = io.open(TEX, encoding='utf-8').read()
    at = s.find('\\begin{thebibliography}')
    head, tail = s[:at], s[at:]

    # 1. drop the printed author names that author-date will supply itself
    for pat, rep in NAME_BEFORE:
        head, n = re.subn(pat, rep, head)
        print('name-before: %-34s -> %-28s (%d)' % (pat[:34], rep[:28], n))

    # 2. possessive / "of [N]" forms
    for pat, rep in AUTHOR_BEFORE:
        head, n = re.subn(pat, rep, head)
        print('author-only: %-24s -> %-26s (%d)' % (pat, rep, n))

    # 3. every remaining site, in file order, from the explicit map
    pos = [0]
    used = [0]

    def walk(m):
        while used[0] < len(SITES) and SITES[used[0]][0] != '{[' + '}' + m.group(1) + '{' + ']}':
            used[0] += 1
        if used[0] >= len(SITES):
            raise SystemExit('MAP EXHAUSTED at site %r' % m.group(0))
        old, new = SITES[used[0]]
        used[0] += 1
        return new

    head = re.sub(r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}', walk, head)
    print('sites consumed from the map: %d of %d' % (used[0], len(SITES)))

    left = re.findall(r'\{\[\}\d+(?:\s*,\s*\d+)*\{\]\}', head)
    if left:
        print('FAIL: %d numeric citation(s) remain: %s' % (len(left), left[:5]))
        return 1

    s = head + tail
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print('written.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
