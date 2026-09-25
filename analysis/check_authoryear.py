"""Verify the author-date conversion: every citation key resolves, nothing is orphaned.

The numeric checker cannot do this job any more -- there are no numbers in the text. What
matters for natbib author-date is:

  * every key used by \\citep / \\citet / \\citeyearpar / \\citeauthor has a \\bibitem;
  * every \\bibitem is cited at least once (an uncited entry is the defect the numeric
    checker caught earlier, and it is equally a defect here);
  * every \\bibitem carries a natbib label of the form Author(Year), because without one
    natbib falls back to numeric and prints "[?]";
  * no numeric citation survives except the bootstrap interval "[0, 0]".

Run against the tex source, not the PDF: pdftotext reflows the reference list and breaks
key-to-entry matching.
"""
import io
import os
import re

TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'paper', 'latex', 'paperA_R1R2.tex')

# \citeyear is included because two sites need a bare year inside an existing
# parenthesis; without it in this list, lewis2020 looked uncited and the checker failed a
# paper that was in fact correct.
CITE_COMMANDS = ('citep', 'citet', 'citeyear', 'citeyearpar', 'citeauthor')


def main():
    s = io.open(TEX, encoding='utf-8').read()
    at = s.find('\\begin{thebibliography}')
    body, bib = s[:at], s[at:]

    used = set()
    for cmd in CITE_COMMANDS:
        for m in re.finditer(r'\\%s\{([^}]*)\}' % cmd, body):
            used.update(k.strip() for k in m.group(1).split(',') if k.strip())

    # re.findall returns the groups in pattern order, so each item is (label, key).
    # The first version unpacked them as (key, label), which inverted the dictionary and
    # made every label look invalid.
    items = re.findall(r'\\bibitem\[([^\]]*)\]\{([^}]*)\}', bib)
    labels = {key: lab for lab, key in items}
    keys = sorted(labels)

    print('citation keys used   : %d' % len(used))
    print('bibliography entries : %d' % len(keys))
    print('unresolved citations : %s' % (sorted(used - set(keys)) or 'none'))
    print('uncited entries      : %s' % (sorted(set(keys) - used) or 'none'))

    # A label is valid if it ends in "(YYYY)" or "(YYYYa)". Written that way because the
    # author part may contain the LaTeX escape \&, which defeats a pattern that tries to
    # describe the author part as well.
    label_re = re.compile(r'\(\d{4}[a-z]?\)$')
    bad_labels = [k for k, lab in labels.items() if not label_re.search(lab.strip())]
    print('labels not Author(Year): %s'
          % ([(k, labels[k]) for k in bad_labels] or 'none'))

    dup = sorted({lab for lab in labels.values() if list(labels.values()).count(lab) > 1})
    print('duplicate labels     : %s' % (dup or 'none'))

    numeric = sorted(set(re.findall(r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}', body)))
    print('numeric cites left   : %s' % (numeric or 'none'))

    ok = (not (used - set(keys)) and not (set(keys) - used) and not bad_labels
          and not dup and numeric == ['0, 0'])
    print()
    print('RESULT: %s' % ('author-date conversion consistent' if ok else 'PROBLEM'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
