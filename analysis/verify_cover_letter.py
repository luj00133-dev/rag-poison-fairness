"""Verify the cover letter's factual claims against the current manuscript, then export it.

The letter was written before the tables were renumbered and the figures numbered, so its claims
are re-checked against the document as it now stands rather than assumed to still hold. It happens
to cite no table or figure number, which is why the renumbering did not invalidate it -- but that
is a conclusion to verify, not to assume.

Also exports a plain-text version. The letter is submitted either as a file or pasted into a
submission form, and a form field takes plain text; markdown asterisks would show up literally.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LETTER = os.path.join(P, 'paper', 'cover_letter.md')
TXT = os.path.join(P, 'paper', 'cover_letter.txt')
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
PDF = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.pdf')

CLAIMS = [
    ('title as submitted',
     'Adversarially Invariant Fairness Statistics', None),
    ('equivalence bound exactly zero', '0.0000', None),
    ('six retrieval back-ends', 'six retrieval back-ends', None),
    ('dense drift 0.1750', '0.1750', None),
    ('BM25 drift 0.2280', '0.2280', None),
    ('SPLADE drift 0.2250', '0.2250', None),
    ('one perturbation step', 'one perturbation step', None),
    ('three modes named', 'balancing the quantity it counts', None),
    ('positive control claim', 'working instruments', None),
    ('batch-average power bound', 'batch', None),
    ('section 5.9 exists', None, '## 5.9'),
    ('section 8.1 exists', None, '### 8.1'),
    # the letter deliberately does not cite a protocol COUNT: it names the requirements
    # instead, which is what a letter should do. So the check is that each named
    # requirement is real in the manuscript, not that a number matches.
    ('protocol: per-group shifts', 'per-group shifts', None),
    ('protocol: attacker strength', 'attacker strength', None),
    ('protocol: encoder as a factor', 'encoder', None),
    ('protocol: equivalence bounds', 'equivalence bound', None),
    ('protocol: threat model', 'threat model', None),
]


def to_plain(md):
    out = []
    for line in md.split('\n'):
        s = line.rstrip()
        if s.startswith('#'):
            s = s.lstrip('#').strip()
        s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
        s = re.sub(r'\*(.+?)\*', r'\1', s)
        s = s.replace('`', '')
        out.append(s)
    text = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', text)


def main():
    letter = io.open(LETTER, encoding='utf-8').read()
    md = io.open(MD, encoding='utf-8').read()

    # 1. does the letter cite any numbered table or figure?
    stale = re.findall(r'(?:Table|Figure)\s+\d+', letter)
    print('numbered table/figure citations in the letter: %s' % (stale or 'none'))

    # 2. every factual claim present in the manuscript
    print()
    print('%-34s %s' % ('claim', 'status'))
    bad = 0
    for label, in_letter, in_md in CLAIMS:
        ok = True
        if in_letter:
            ok = ok and (in_letter in letter) and (in_letter in md)
        if in_md:
            ok = ok and (in_md in md)
        if not ok:
            bad += 1
        print('  %-32s %s' % (label, 'ok' if ok else 'CHECK'))

    # 3. the letter's own structure claims
    print()
    print('letter length: %d words' % len(letter.split()))

    # 4. export plain text for pasting into a submission form
    io.open(TXT, 'w', encoding='utf-8', newline='\n').write(to_plain(letter))
    print('wrote %s' % TXT)

    print()
    print('RESULT: %s' % ('letter consistent with the manuscript'
                          if bad == 0 and not stale
                          else '%d item(s) to check' % (bad + len(stale))))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
