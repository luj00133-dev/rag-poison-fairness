"""Correct two subsection headings that did not match their sections' content.

verify_headings.py checks each heading against the terms that would have to appear for it
to be honest. Two failed:

  * 5.2 was renamed "A positive control ..." but the positive control (Table 1, corpus size
    held fixed, the statistics responding monotonically) is in 5.1; 5.2 is the inertness
    result. Its original heading was in fact accurate.
  * 5.6 was renamed "The encoder is a factor ... GTE/E5", but 5.6 is the adaptive attacker
    and the encoder sweep is 5.5. Also my error, and also reverting.

So this restores both, keeping the four renames whose sections do contain what the heading
claims, and holding 5.5's "F3" out of the title because it overstates what that section
demonstrates: the per-group shift is the diagnostic it establishes, and F3 is fully
demonstrated at the generation layer in 5.7.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

FIXES = [
    ('### 5.2 A positive control: the statistics under test are working instruments',
     '### 5.2 The R1 constraint is inert'),
    ('### 5.5 F3 and the positive resolution: the diagnostic is the per-group shift',
     '### 5.5 The diagnostic is the per-group shift, not the gap between groups'),
    ('### 5.6 The encoder is a factor: susceptibility is a per-checkpoint property',
     '### 5.6 Under an informed attacker no defense survives'),
]


def main():
    s = io.open(MD, encoding='utf-8').read()
    for old, new in FIXES:
        c = s.count(old)
        print('%-72s %s' % (old[:72], 'fixed' if c == 1 else 'NOT FOUND (%d)' % c))
        if c == 1:
            s = s.replace(old, new, 1)
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    import re
    for m in re.finditer(r'^### 5\.\d.*$', s, re.M):
        print('   ' + m.group(0))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
