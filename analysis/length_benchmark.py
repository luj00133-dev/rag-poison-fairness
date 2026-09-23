"""How long are the papers this work is positioned against?

Paper A grew to 40 pages, which is worth checking against the actual length of
the comparison set rather than against intuition. arXiv does not expose a page
count through these tools, so this estimates from full-text length and reports
the estimate as an estimate: ~3,000 characters per page is the usual density for
a two-column or single-column cs.CR paper in 10pt with tables, and the error on
that constant is easily +/-30%, so the numbers below order the papers correctly
but should not be quoted as exact page counts.

Named lengths are used where known (conference proceedings have hard limits).
"""
import re

#: Full texts fetched separately; lengths in characters, from get_fulltext.
#: (label, chars, note)
PAPERS = [
    ('BRRA (Wang et al., TDSC 2026)', 96_000,
     'the closest attack-side work we compare against'),
    ('Kim & Diaz (ICTIR 2025)', 78_000,
     'fair-ranking for RAG; proceedings paper'),
    ('FARO (Zhao et al., 2026)', 61_000,
     'closest defense-side work'),
    ('TriShieldRAG (2026)', 74_000,
     'layered defenses, adaptive evaluation'),
    ('Wu et al. (COLING 2025)', 55_000,
     'fairness evaluation of RAG; proceedings paper'),
    ('Kim et al. (ACL Findings 2025)', 52_000,
     'embedder control'),
    ('BiasRAG (Bagwe et al., 2025)', 48_000,
     'fairness backdoor'),
    ('GraphRAG under Fire (S&P 2026)', 58_000,
     'proceedings paper, hard page limit'),
    ('MM-PoisonRAG (2025)', 51_000,
     'multimodal poisoning'),
    ('Poisoned-MRAG (2025)', 49_000,
     'multimodal poisoning'),
    ('PoisonedRAG (USENIX Sec 2025)', 60_000,
     'proceedings paper'),
    ('--- this work, Paper A ---', 291_883,
     'PDF bytes, not characters; see note'),
]

CHARS_PER_PAGE = 3_000


def estimate(chars: int) -> float:
    return chars / CHARS_PER_PAGE


#: Known hard limits for the venues involved, which matter more than the
#: estimate: a paper over the limit is not "long", it is rejected or cut.
LIMITS = [
    ('USENIX Security', '~13 pages body + unlimited appendices'),
    ('IEEE S&P', '13 pages body + unlimited appendices'),
    ('ACL / COLING', '8 pages + unlimited appendices (Findings: 8)'),
    ('ICTIR', '9 pages + unlimited appendices'),
    ('Computers & Security', 'no hard limit; ~30-40 pp typical for a full article'),
    ('IEEE TDSC / TIFS', '~14 pages regular paper, over-length page charges'),
]

if __name__ == '__main__':
    print('Estimated length of the comparison set (~%d chars/page):'
          % CHARS_PER_PAGE)
    print()
    print('%-36s %9s %8s  %s' % ('paper', 'chars', '~pages', 'note'))
    for label, chars, note in PAPERS[:-1]:
        print('%-36s %9s %8.1f  %s'
              % (label, format(chars, ','), estimate(chars), note))
    print()
    print('%-36s %9s %8s' % ('this work, Paper A (PDF bytes)', '291,883', '<= 40'))
    print('  (the PDF byte count is not comparable to the character counts above:')
    print('   it includes figures, fonts and the TeX object stream, and the 40-page')
    print('   figure comes from the .log, which is the authoritative count.)')
    print()
    print('Venue limits that matter more than length:')
    for venue, limit in LIMITS:
        print('  %-22s %s' % (venue, limit))
