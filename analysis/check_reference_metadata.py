"""Check the reference metadata against the manuscript's own entries.

Two failure modes matter here and this checks for both:

  1. a metadata file that does not cover every reference, or covers numbers that do not
     exist (the first version of this file invented three "duplicate" entries for
     references 19/21/22 that were not duplicates of anything -- caught by exactly this
     comparison, which is why it is a script and not a hand check);
  2. a metadata claim that contradicts the printed entry, e.g. a different first author or
     year, which would silently change what the reference says.

Surname-level comparison only: the manuscript prints initials and the metadata carries full
names, so an exact string match is not the right test. A mismatch is reported for a human
to look at, not auto-corrected.
"""
import io
import json
import os
import re
import unicodedata

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
META = os.path.join(P, 'results', 'reference_metadata.json')


def fold(s):
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()


def manuscript_entries():
    md = io.open(MD, encoding='utf-8').read()
    at = md.rfind('\n[1] ')
    out = {}
    for m in re.finditer(r'^\[(\d+)\] (.*?)(?=\n\[\d+\] |\Z)', md[at:], re.M | re.S):
        out[int(m.group(1))] = ' '.join(m.group(2).split())
    return out


def main():
    entries = manuscript_entries()
    meta = json.load(io.open(META, encoding='utf-8'))['references']
    meta = {int(k): v for k, v in meta.items()}

    print('manuscript entries : %d' % len(entries))
    print('metadata entries   : %d' % len(meta))
    only_md = sorted(set(entries) - set(meta))
    only_meta = sorted(set(meta) - set(entries))
    print('missing from meta  : %s' % (only_md or 'none'))
    print('extra in meta      : %s' % (only_meta or 'none'))
    print()

    problems = []
    for n in sorted(set(entries) & set(meta)):
        text = entries[n]
        # The printed year is the LAST four-digit number in the entry, not the first: an
        # entry reading "pp. 2086-2105, 2022" has two, and taking the first reported a
        # false problem on reference 21 (the page number was read as the year). Reference
        # entries put the year last, so that is the rule.
        years = re.findall(r'\b(?:19|20)\d{2}\b', text)
        year_md = int(years[-1]) if years else None
        year_meta = meta[n].get('year')
        surname_meta = fold(meta[n]['authors'][0].split()[-1])
        surname_md = fold(text)[:60]
        first_ok = surname_meta in surname_md
        year_ok = (year_md == year_meta) if year_md else None
        flag = []
        if not first_ok:
            flag.append('first author')
        if year_ok is False:
            flag.append('year %s vs %s' % (year_md, year_meta))
        if flag:
            problems.append(n)
        print('%2d  %-26s | meta: %-22s %s %s'
              % (n, text[:26], meta[n]['authors'][0][:22], year_meta,
                 '<-- ' + ', '.join(flag) if flag else ''))

    print()
    print('entries needing a look: %s' % (problems or 'none'))
    return 1 if (only_md or only_meta) else 0


if __name__ == '__main__':
    raise SystemExit(main())
