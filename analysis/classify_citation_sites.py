"""Classification of every citation site in Paper A, by position in the file.

Produced from analysis/dump_citation_sites.py, whose output shows each site with its
surrounding words. The class decides the natbib command:

  citep    -- the citation is a parenthetical aside                       -> \\citep{...}
  texcite  -- the surrounding words already print the author name, so the  -> \\citep{...}
              name must be REMOVED from the prose and the citation carries it
  year     -- the surrounding words already print the name and the        -> \\citeyearpar{...}
              sentence keeps it ("except [4], and [4] itself")
  author   -- the name is possessive or follows "of"                     -> \\citeauthor{...}
  skip     -- not a citation at all (the bootstrap interval "[0, 0]")

The distinction matters because a wrong class prints the author twice ("Wang et al.
Wang et al. (2025) show") or leaves a citation stranded mid-clause. Site positions are
1-based, in order of appearance.
"""
import io
import json
import re

HERE = r'G:\keyan\projects\rag-poison-fairness\analysis'
TEX = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.tex'
OUT = HERE + r'\citation_site_classes.json'

# site number -> (class, keys, the exact printed name to remove when class == 'texcite',
#                and the prefix of the prose that identifies the site for verification)
CLASSES = {
    1:  ('citep',   ['lewis2020'], None, 'Retrieval-augmented generation (RAG)'),
    2:  ('citep',   ['zou2025', 'zhang2025'], None, 'large majority of cases'),
    3:  ('texcite', ['wang2025'], 'Wang et al.~', 'need not target factual correctness'),
    4:  ('citep',   ['zhao2026'], None, 'equalise group proportions'),
    5:  ('citep',   ['wu2025'], None, 'group-relevant passages'),
    6:  ('citep',   ['kim2025a'], None, "generator's own bias"),
    7:  ('citep',   ['kim2025b'], None, 'equal exposure'),
    8:  ('citep',   ['kim2025b'], None, 'aggregate composition'),
    9:  ('texcite', ['zou2025'], 'Zou et al.~', 'Corpus poisoning against RAG was established by'),
    10: ('citep',   ['zhang2025'], None, 'black-box and query-agnostic settings'),
    11: ('citep',   ['liang2026'], None, 'knowledge-graph-structured retrieval'),
    12: ('citep',   ['ha2025', 'chang2025', 'liu2025'], None, 'multimodal pipelines'),
    13: ('texcite', ['wang2025'], 'Wang et al.~', 'rank highly regardless of their text'),
    14: ('year',    ['wang2025'], None, 'targets \\emph{factual} correctness except'),
    15: ('year',    ['wang2025'], None, 'and'),
    16: ('texcite', ['wu2025'], 'Wu et al.~', 'defines fairness by the statistic it optimises'),
    17: ('texcite', ['kim2025a'], 'Kim et al.~', 'exploration of mitigation strategies'),
    18: ('texcite', ['kim2025b'], 'Kim and Diaz ', 'both R1 and R2 are outside their formulation'),
    19: ('texcite', ['zhao2026'], 'Zhao et al.~', 'Most closely related is'),
    20: ('texcite', ['kim2025a'], 'Kim et al.~', 'Two further works are relevant'),
    21: ('texcite', ['bagwe2025'], 'Bagwe et al.~', 'measured along the wrong axis'),
    22: ('texcite', ['dai2024'], 'Dai et al.~', 'frame how this work should be read'),
    23: ('texcite', ['hu2024'], 'Hu et al.~', 'rather than the statistic'),
    24: ('year',    ['wang2025'], None, 'stable and generalizable defense performance'),
    25: ('year',    ['mohanty2026'], None, 'single-stage defenses give limited robustness'),
    26: ('year',    ['wu2025'], None, 'comprehensive exploration of strategies'),
    27: ('texcite', ['jacobs2021'], 'Jacobs and Wallach ', 'we do not claim it as ours'),
    28: ('texcite', ['ekstrand2022a'], 'Ekstrand et al.~', 'tools for making those mismatches explicit'),
    29: ('citep',   ['ekstrand2022b'], None, 'alongside the aggregate for this reason'),
    30: ('citep',   ['efron1993'], None, 'rather than to a single number, is standard'),
    31: ('citep',   ['parrish2022', 'nadeem2021'], None, 'template inventories'),
    32: ('year',    ['wang2025'], None, 'the mean query direction, following'),
    33: ('year',    ['wang2025'], None, 'Multi-query consistency'),
    34: ('author',  ['zhao2026'], None, 'the encoders GTE-base'),
    35: ('author',  ['kim2025b'], None, 'Contriever'),
    36: ('year',    ['wang2025', 'wu2025'], None, 'E5-large-v2'),
    37: ('skip',    [], None, 'bootstrap CI collapses to'),
    38: ('author',  ['zhao2026'], None, 'published defense family:'),
    39: ('author',  ['wu2025'], None, 'under a fairness constraint,'),
    40: ('author',  ['kim2025a'], None, 'proportions and ordering,'),
    41: ('author',  ['kim2025b'], None, 'embedder group balance,'),
    42: ('year',    ['wang2025'], None, 'multi-query consistency'),
    43: ('citep',   ['parrish2022'], None, 'We therefore replicate on \\textbf{BBQ}'),
    44: ('citep',   ['zou2025'], None, 'factual-poisoning literature'),
    45: ('author',  ['zhao2026'], None, 'GTE-base'),
    46: ('author',  ['kim2025b'], None, 'Contriever'),
    47: ('year',    ['wang2025', 'wu2025'], None, 'E5-base-v2'),
    48: ('texcite', ['kim2025b'], 'Kim \\& Diaz ', 'expected-attributed-exposure (EAE-D) statistic of'),
    49: ('author',  ['zhao2026'], None, 'the objective of'),
    50: ('author',  ['wu2025'], None, 'proportion adjustment of'),
    51: ('year',    ['wang2025'], None, 'Multi-query consistency'),
    52: ('citep',   ['ekstrand2022b'], None, 'TREC 2022 Fair Ranking Track'),
    53: ('year',    ['zhang2025'], None, 'query-agnostic attack'),
    54: ('author',  ['zhao2026'], None, 'Concretely,'),
    55: ('author',  ['wu2025'], None, "optimisation,"),
    56: ('author',  ['kim2025a'], None, 'proportion adjustment,'),
    57: ('author',  ['kim2025b'], None, 'embedder control, and'),
    58: ('author',  ['zhao2026'], None, 'the re-ranking of'),
    59: ('author',  ['wu2025'], None, 'proportion adjustment of'),
    60: ('author',  ['kim2025a'], None, 'embedder control of'),
    61: ('author',  ['kim2025b'], None, 'exposure equalisation of'),
    62: ('skip',    [], None, 'bootstrap CI collapses to'),
    63: ('skip',    [], None, 'so the CI is'),
    64: ('author',  ['kim2025b'], None, 'fair-ranking work we compare against'),
    65: ('author',  ['kim2025b'], None, 'attributed exposure'),
    66: ('year',    ['wang2025', 'kim2025a'], None, 'generator bias'),
    67: ('year',    ['wu2025', 'kim2025a', 'kim2025b'], None, 'Binary groups.} Following'),
}


def main():
    # verify against the live file: count sites and check the identifying prefix is present
    s = io.open(TEX, encoding='utf-8').read()
    body = s[:s.find('\\begin{thebibliography}')]
    found = list(re.finditer(r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}', body))
    print('sites in file: %d, classified: %d' % (len(found), len(CLASSES)))
    if len(found) != len(CLASSES):
        print('FAIL: count mismatch')
        return 1
    bad = []
    for i, m in enumerate(found, 1):
        cls, keys, name, marker = CLASSES[i]
        nums = re.sub(r'\s', '', m.group(1))
        if cls != 'skip' and not keys:
            bad.append(i)
        if marker and marker not in body[:m.start()]:
            bad.append(i)
    print('sites whose identifying marker is absent: %s' % (sorted(set(bad)) or 'none'))
    json.dump({str(k): v for k, v in CLASSES.items()},
              io.open(OUT, 'w', encoding='utf-8'), indent=1)
    print('wrote %s' % OUT)
    counts = {}
    for cls, _, _, _ in CLASSES.values():
        counts[cls] = counts.get(cls, 0) + 1
    print('class counts: %s' % counts)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
