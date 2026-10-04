"""Survey the paper's claims for statements that overreach what the measurements now support.

Expression changes can raise acceptance, but only inside the line: no claim may be made stronger
than the evidence, and no limitation affecting the central conclusion may be hidden. So before
proposing any reframing, this lists every unqualified form of the paper's central claims, which
are the places where an unconditional wording now sits on top of a conditional result.

Each hit is printed with its context so the wording can be checked rather than assumed.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

PATTERNS = [
    (r'\b(are|is) (structurally )?(blind|insensitive)\b', 'unqualified blindness'),
    (r'\bwe show that\b', 'unqualified demonstration'),
    (r'\bevery (statistic|metric|candidate)\b', 'universal quantifier'),
    (r'\b(always|never|invariantly)\b', 'absolute'),
    (r'\bin general\b', 'generalisation'),
    (r'\bregardless of\b', 'independence claim'),
    (r'\bno defense\b', 'universal negative'),
]


def main():
    s = io.open(MD, encoding='utf-8').read()
    lines = s.split('\n')
    total = 0
    for pat, label in PATTERNS:
        hits = []
        for i, line in enumerate(lines, 1):
            for m in re.finditer(pat, line, re.I):
                hits.append((i, m.group(0)))
        if hits:
            print('%-22s %d occurrence(s)' % (label, len(hits)))
            for i, frag in hits[:6]:
                j = lines[i - 1].lower().find(frag.lower())
                print('   L%-5d ...%s...' % (i, lines[i - 1][max(0, j - 70):j + 90].strip()))
            total += len(hits)
            print()
    print('total unqualified phrasings: %d' % total)
    print()
    print('Reading: each of these is a candidate for a scope qualifier. NOT all should be')
    print('changed -- a claim that is genuinely scoped in the same sentence is fine. The point')
    print('is to find the ones sitting on top of a conditional result with no qualifier.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
