"""Check whether the six-point protocol in 5.8.1 preserves the content of section 8's list.

Both files lost section 8's nine-point protocol when the conclusion was replaced: the
replacement's end boundary ran past the conclusion and swallowed the list. This is my
regression, not the user's, and it has to be repaired without leaving two protocols that say
different things.

The nine points of section 8 were:

  1 measure per-group shifts, not cross-group differences
  2 report injection as a rate, not a count
  3 report the encoder as a factor
  4 give equivalence bounds for null claims
  5 state the threat model explicitly
  6 report adversarial inclusion as a function of attacker strength
  7 report a utility-preserving baseline
  8 for a randomised defense, state the distribution and assume it is known
  9 for a penalty-based defense, report whether the penalty is computable

The six points now standing in 5.8.1 cover 5, 6, 7, 8, 9 plus one on sweeping to failure.
So 1-4 -- the four that section 8 called prerequisites for a fairness statistic to be
reported at all -- are the ones at risk. This script reports, for each, whether the concept
survives anywhere in the paper.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

# concept -> the phrasings that would evidence it
CONCEPTS = {
    '1 per-group shifts not differences': [
        'per-group shifts rather than cross-group differences',
        'per-group shifts, not cross-group differences',
        'per-group shifts'],
    '2 injection as a rate': ['as a rate rather than a count', 'injection rate'],
    '3 encoder as a factor': ['encoder reported as a factor', 'encoder as a factor',
                              'per-checkpoint property'],
    '4 equivalence bounds': ['equivalence bound', 'equivalence bounds'],
    '5 threat model': ['threat model'],
    '6 inclusion vs attacker strength': ['as a function of attacker strength',
                                         'attacker strength'],
    '7 utility-preserving baseline': ['utility-preserving', 'utility proxy'],
    '8 randomised distribution': ['randomised defense', 'randomized defense',
                                  'state the distribution'],
    '9 penalty computable': ['computable from public information'],
}


def main():
    s = io.open(TEX, encoding='utf-8').read()
    print('%-34s %-6s %s' % ('concept', 'count', 'first occurrence context'))
    print('-' * 104)
    for name, phrasings in CONCEPTS.items():
        total = 0
        ctx = ''
        for p in phrasings:
            n = s.count(p)
            total += n
            if n and not ctx:
                i = s.find(p)
                ctx = ' '.join(s[max(0, i - 55):i + 55].split())
        print('%-34s %-6d %s' % (name, total, ctx[:70]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
