"""What merging Paper B would actually add to Paper A, and the citation map to do it.

Measured, not assumed. A's section 6 already carries four propositions, including one on
public randomisation (6.5) -- so B's section 4 is already absorbed and must NOT be
transplanted. The same is true of B's section 6 reporting protocol, most of whose rules
already appear in A's section 8 protocol.

What is left is genuinely new:

  1. the six-back-end adaptive sweep, which shows the *static* advantage is largest on the
     pretrained encoders the compared literature uses, and that no defense survives beyond
     one or two perturbation steps on any of them; A's section 5.6 states the inversion for
     one dense retriever plus a per-lambda grid in Appendix C and does not have this;
  2. the evaluation-cost result ("usage" >= 0.943 at lambda=1 on every back-end), which is
     what rules out the objection that the attacker simply destroyed its own passages;
  3. the set-composition result: the only configuration retaining benefit is the one whose
     constraint is over the retrieved set rather than over individual passages.

This script prints that assessment and the citation map from B's numeric references to A's
author-date keys, so the transplant can be done without renumbering anything.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')
B = os.path.join(P, 'paper', 'manuscript_B_adaptive_v1.md')

# B's numeric reference -> A's author-date key, matched by first author and year
B_TO_A = {
    1: 'lewis2020', 2: 'zou2025', 3: 'zhang2025', 4: 'wang2025', 5: 'zhao2026',
    6: 'wu2025', 7: 'kim2025a', 8: 'kim2025b', 9: 'ekstrand2022b',
    10: 'ekstrand2022a', 11: 'patterson2021', 12: 'liang2026', 13: 'ha2025',
    14: 'liu2025', 15: 'edemacu2026', 16: 'bagwe2025', 17: 'jacobs2021',
    18: 'efron1993', 19: 'parrish2022',
}


def refs(path):
    s = io.open(path, encoding='utf-8').read()
    i = s.rfind('\n[1] ')
    out = {}
    for m in re.finditer(r'^\[(\d+)\] (.{0,110})', s[i:], re.M):
        out[int(m.group(1))] = ' '.join(m.group(2).split())
    return out


def main():
    ra, rb = refs(A), refs(B)
    print('A refs: %d   B refs: %d' % (len(ra), len(rb)))
    print()
    print('%-5s %-58s %s' % ('B#', 'B entry', 'A key'))
    print('-' * 100)
    unresolved = []
    for n in sorted(rb):
        k = B_TO_A.get(n)
        print('%-5d %-58s %s' % (n, rb[n][:58], k or '?? UNMAPPED'))
        if not k:
            unresolved.append(n)
    print()
    print('unmapped B references: %s' % (unresolved or 'none'))
    print('A keys referenced by the map: %d distinct' % len(set(B_TO_A.values())))

    # sanity: every mapped key must exist in A's author-date bibliography
    import json
    ay = json.load(io.open(os.path.join(P, 'results', 'reference_authoryear.json'),
                           encoding='utf-8'))['entries']
    have = {e['key'] for e in ay}
    bad = sorted({k for k in B_TO_A.values() if k not in have})
    print('mapped keys absent from A bibliography: %s' % (bad or 'none'))


if __name__ == '__main__':
    raise SystemExit(main())
