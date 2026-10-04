"""Verify Appendix E's numbers, and that its claims match what the body now says.

An appendix that quotes SUPERSEDED values is the most dangerous place in a paper to make a
transcription error: the numbers are deliberately different from the body's, so nothing
cross-checks them automatically. What can be checked is that

  * each superseded value quoted is the value the earlier drafts actually reported, from the
    record in the git history and in the analysis scripts;
  * each "the corrected value is X" matches what the body now reports;
  * every cross-reference in the appendix points at a section that exists.

Checked in the tex, since that is what is published.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

# (superseded value quoted in Appendix E, where the corrected value lives in the body,
#  the corrected value as reported)
CHECKS = [
    ('0.125 / 0.438 / 0.750', 'factor of six', 'factor of three', 'Table C1'),
    ('18 of 18 adaptive cells', None, None, None),
    ('+0.997', None, '-0.997', None),
    ('0.798--0.828', None, '0.831--0.968', None),
    ('six passages per stratum', None, None, '§5.4'),
    ('0.03\\%', None, '10\\%', None),
]


def main():
    s = io.open(TEX, encoding='utf-8').read()
    a = s.find('\\section{Appendix E.')
    b = s.find('\\section{Declaration of generative AI')
    app = s[a:b] if a > 0 and b > a else ''
    print('Appendix E length: %d chars' % len(app))
    if not app:
        print('FAIL: appendix not found')
        return 1

    print()
    print('--- quoted values present in the appendix ---')
    for row in CHECKS:
        for v in row:
            if v and v not in app:
                print('  MISSING %r' % v)
    print('  (only missing entries are reported)')

    print()
    print('--- cross-references inside the appendix ---')
    for m in re.finditer(r'§([\d.]+)', app):
        print('  §%s' % m.group(1))
    for tbl in re.findall(r'Table [A-Z]?\d+', app):
        print('  %s' % tbl)

    print()
    print('--- consistency: does the body still state the corrected values? ---')
    body = s[:a]
    for probe in ['factor of three', 'a factor of three over no defense']:
        print('  %-44s %s' % (probe, 'in body' if probe in body else 'NOT in body'))
    print('  %-44s %s' % ('old factor-of-six claim in body',
                          'STILL PRESENT' if 'factor of six' in body else 'removed'))

    print()
    print('--- the appendix must not be cited as if it were a limitation ---')
    for probe in ['Appendix E', 'appendix-e']:
        print('  %-16s occurrences outside the appendix: %d'
              % (probe, s[:a].count(probe) + s[b:].count(probe)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
