"""Convert Paper A from numeric citations to natbib author-date, using the site classes.

Reads analysis/citation_site_classes.json (67 sites, each classified as citep / texcite /
year / author / skip -- see classify_citation_sites.py for what the classes mean and how
they were determined) and:

  1. removes the printed author name that author-date will supply itself ("Wang et al.~"
     before a citation), for texcite sites only -- 14 of them;
  2. replaces each numeric site with the natbib command its class calls for, walking the
     file's sites in order so the map cannot drift from the text;
  3. rewrites the bibliography into author-date \\bibitem[Label]{key} entries from
     results/reference_authoryear.json;
  4. switches the document class to the authoryear option, which is what makes natbib
     render author-date at all (loading natbib separately clashes; \\biboptions has no
     effect -- both were tried and both left every citation as "[?]").

Failures are loud: a site whose class does not match the text stops the run before
anything is written.
"""
import io
import json
import os
import re

P = r'G:\keyan\projects\rag-poison-fairness'
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')
CLASSES = os.path.join(P, 'analysis', 'citation_site_classes.json')
REFS = os.path.join(P, 'results', 'reference_authoryear.json')


def cite_cmd(cls, keys):
    joined = ','.join(keys)
    if cls == 'citep':
        return r'\citep{%s}' % joined
    if cls == 'texcite':
        return r'\citet{%s}' % joined
    if cls == 'year':
        return r'\citeyearpar{%s}' % joined
    if cls == 'author':
        return r'\citeauthor{%s}' % keys[0]
    raise ValueError(cls)


def main():
    s = io.open(TEX, encoding='utf-8').read()
    classes = json.load(io.open(CLASSES, encoding='utf-8'))

    # ---- 1. remove printed author names at texcite sites
    removed = 0
    for k, (cls, keys, name, _marker) in sorted(classes.items(), key=lambda x: int(x[0])):
        if cls == 'texcite' and name:
            pat = re.escape(name) + r'(\s*)\{\[\}'
            s, n = re.subn(pat, r'\1{[}', s, count=1)
            if n != 1:
                print('FAIL: could not strip %r for site %s (%d matches)' % (name, k, n))
                return 1
            removed += 1
    print('printed author names removed: %d' % removed)

    # ---- 2. replace sites in order
    at = s.find('\\begin{thebibliography}')
    head, tail = s[:at], s[at:]
    it = iter(sorted(classes.items(), key=lambda x: int(x[0])))
    state = {'i': 0}

    def walk(m):
        num, (cls, keys, _n, _mk) = next(it)
        state['i'] += 1
        if cls == 'skip':
            return m.group(0)
        return cite_cmd(cls, keys)

    head = re.sub(r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}', walk, head)
    print('sites replaced: %d' % state['i'])

    # The three "[0, 0]" sites are statistical intervals, not citations, and are expected
    # to survive. The first version of this guard flagged them as unconverted citations
    # and aborted; it now expects exactly the sites the map marked 'skip' and nothing else.
    expected_skips = sum(1 for k, v in classes.items() if v[0] == 'skip')
    left = re.findall(r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}', head)
    if len(left) != expected_skips or any(x.strip() != '0, 0' for x in left):
        print('FAIL: unexpected numeric cites remain: %s' % left[:5])
        return 1
    print('skipped sites kept as-is: %d (all "[0, 0]" intervals)' % len(left))

    # An artifact the conversion exposes: "(RAG) \citep{lewis2020}" prints as
    # "generation (RAG) (Lewis et al., 2020)". The acronym and its citation belong in one
    # parenthesis. Applied as a post-pass so the site map stays a pure substitution.
    head = head.replace('(RAG) \\citep{lewis2020}', '(RAG; \\citep{lewis2020})')

    # ---- 3. document class
    if 'authoryear' not in head.split('\n')[3]:
        head = head.replace(
            r'\documentclass[review,3p,times]{elsarticle}',
            r'\documentclass[authoryear,review,3p,times]{elsarticle}', 1)

    # ---- 4. bibliography, alphabetical by the printed label
    refs = [e for e in json.load(io.open(REFS, encoding='utf-8'))['entries']
            if e.get('old_number')]

    def esc(t):
        """Escape the ampersands that separate author names.

        Unescaped "&" is an alignment tab in LaTeX and produced 22 errors
        ("Misplaced alignment tab character &"), one per reference entry. Only the
        separator form is escaped, so a genuine "\\&" already in the text is untouched.
        """
        return re.sub(r'(?<!\\)\s&\s', r' \\& ', t)

    def label(entry):
        """natbib's optional label, which is what the citation prints.

        It MUST be "Author(Year)" or "Author & Author(Year)" or "Author et al.(Year)",
        otherwise natbib reports "Bibliography not compatible with author-year citations"
        and silently falls back to numeric -- which is what the first version of this
        function caused by passing the bare surname.
        """
        text = entry['text']
        m = re.search(r'\((\d{4})\)', text)
        year = m.group(1) if m else 'n.d.'
        head = text[:m.start()].strip() if m else text
        # author block: "Surname, A. B., Surname2, C., & Surname3, D."
        chunks = [c.strip() for c in re.split(r',\s*&\s*|,\s*', head) if c.strip()]
        surnames = []
        for c in chunks:
            if re.fullmatch(r'(?:[A-Z]\.\s*)+', c):      # an initials run, not a surname
                continue
            surnames.append(c.split()[-1].rstrip('.'))
        if not surnames:
            return head + '(%s)' % year
        if len(surnames) == 1:
            return '%s(%s)' % (surnames[0], year)
        if len(surnames) == 2:
            # natbib prints \citet as "Kim and Diaz" and \citep as "(Kim & Diaz, 2025)",
            # so the label's separator must be an escaped ampersand: a bare "&" is a
            # LaTeX alignment tab and produced 14 errors inside \NAT@nm.
            return r'%s \& %s(%s)' % (surnames[0], surnames[1], year)
        return '%s et al.(%s)' % (surnames[0], year)

    bib = ['\\begin{thebibliography}{99}', '']
    ordered = sorted(refs, key=lambda x: x['text'].lower())
    # Two works can share a label -- here both Ekstrand 2022 entries -- and natbib needs
    # them distinguished, conventionally with a/b/c suffixes appended to the year and
    # repeated in the citation ("Ekstrand et al., 2022a").
    labels = [label(r) for r in ordered]
    seen = {}
    fixed = []
    for lab in labels:
        if labels.count(lab) > 1:
            seen[lab] = seen.get(lab, 0) + 1
            fixed.append(lab[:-1] + chr(ord('a') + seen[lab] - 1) + ')')
        else:
            fixed.append(lab)
    dupes = sorted({l for l in labels if labels.count(l) > 1})
    if dupes:
        print('disambiguated labels: %s -> %s' % (dupes, [f for f in fixed if f not in labels]))
    for r, lab in zip(ordered, fixed):
        bib.append('\\bibitem[%s]{%s} %s' % (lab, r['key'], esc(r['text'])))
    bib.append('\\end{thebibliography}')
    raw_tail = '\n' + '\n'.join(bib) + '\n'

    # Keep whatever followed the original bibliography -- in practice \end{document}.
    # The first version of this rebuild dropped that, which is the same truncation that
    # broke the earlier renumbering pass; hence the explicit assertion below.
    after = s[at:]
    end_doc = after.find('\\end{document}')
    if end_doc < 0:
        print('FAIL: \\end{document} not found after the bibliography')
        return 1
    tail = raw_tail + after[end_doc:]

    new = head + tail
    for needed in ('\\begin{document}', '\\end{document}', '\\begin{thebibliography}',
                   '\\end{thebibliography}'):
        if needed not in new:
            print('FAIL: rewritten file is missing %s' % needed)
            return 1

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(new)
    print('bibliography entries written: %d' % len(ordered))
    print('written.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
