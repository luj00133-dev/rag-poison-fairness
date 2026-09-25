"""Build author-date reference data for all 22 entries, from real metadata.

IP&M prints author-date references, and the manuscript's entries are numeric-style
abbreviations ("W. Zou, R. Geng, B. Wang, J. Jia.") that cannot be converted by
reformatting alone: author-date needs the full author list, the year, the article title
and the journal name, and several entries currently end in "et al." with no complete list.

So this asks the literature index for each work by title and records what it returns:
authors as printed, year, title, venue, volume/pages, DOI. The result is written to a
JSON file that the conversion step reads, so the conversion itself is a pure text
operation over verified data rather than a place where bibliographic facts get invented.

Entries the index cannot resolve are reported and left for manual completion -- an
unresolved entry is a visible gap, which is the correct failure mode.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, '..', 'paper', 'manuscript_R1R2_v1.md')
OUT = os.path.join(HERE, '..', 'results', 'reference_metadata.json')

# current entries, in current numeric order (number -> the text after "[N] ")
def current_entries():
    s = io.open(MD, encoding='utf-8').read()
    at = s.rfind('\n[1] ')
    out = {}
    for m in re.finditer(r'^\[(\d+)\] (.*?)(?=\n\[\d+\] |\Z)', s[at:], re.M | re.S):
        out[int(m.group(1))] = ' '.join(m.group(2).split())
    return out


def main():
    sys.path.insert(0, HERE)
    from mcp_bridge import lookup  # noqa: F401   (placeholder; real call is via MCP)

    print('This module is driven by the agent through the MCP literature tools.')
    print('Current entries to resolve:')
    for n, e in sorted(current_entries().items()):
        print('%2d  %s' % (n, e[:96]))


if __name__ == '__main__':
    main()
