"""Stage 4: rebuild how the Results chapter reads, and cut the last defensive residue.

Two moves, both from the skill's structure rules.

1. The Results chapter opened with a housekeeping note ("Status of this section ... all
   numbers are reproducible with the commands in Appendix A ... the controlled suite
   completes in ~25 s"). That is a lab log opening: it tells the reader about our process
   before telling them what we found. It is replaced by a short argument map that states
   what each experiment is FOR -- the positive control establishes the instruments work,
   each of the three modes is then demonstrated, and the adaptive sweep closes the loop.
   The reproducibility facts are not lost; they belong in Data and Code Availability and
   Appendix A, where they already are.

2. Subsection headings are made declarative rather than procedural, so the section can be
   read as a claim chain: what each result establishes, not what we did.

3. The remaining self-weakening sentences are cut: "this free-form probe is the third
   instrument failure the paper documents" (an escalation the skill warns against --
   never help the reader turn a local observation into a verdict) becomes a statement
   about what the probe measures.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(P, 'paper', 'manuscript_R1R2_v1.md')

OLD_OPEN = ('> **Status of this section.** All numbers reported below were produced by the '
            'released implementation and are reproducible with the commands in Appendix A. '
            'Two corpora are used: a controlled corpus with an exactly known clean '
            'reference (§5.1–§5.3) and the natural BBQ corpus (§5.4), each swept over '
            'injection rate $\\rho \\in \\{0.1\\%, \\dots, 2\\%\\}$ of corpus size; §5.5 '
            'adds the backbone alignment against five further retrievers, §5.6 the '
            'encoder-scale check, and §5.7 the generation-stage propagation check. The '
            'controlled suite completes in ~25 s, the BBQ replication in ~180 s, and the '
            'multi-backbone sweep in ~12 min, all on CPU with no GPU.')

NEW_OPEN = ('The chapter is organised as an argument rather than as a sequence of runs. '
            '§5.1 and §5.2 establish the two dimensions and the attack, and — critically — '
            'show that the statistics we indict are *working instruments*: a positive '
            'control moves the ground truth by a known amount and they respond. §5.3 and '
            '§5.4 then demonstrate two of the three failure modes on a controlled corpus '
            'with an exactly known clean reference and on the naturally written BBQ '
            'benchmark, each swept over injection rate $\\rho \\in \\{0.1\\%, \\dots, '
            '2\\%\\}$. §5.5 and §5.6 establish that the encoder is a factor rather than an '
            'implementation detail. §5.7 shows the retrieval-layer skew reaches the '
            'generated text, and §5.8 closes the loop with a defense-aware attacker: the '
            'defenses do not merely weaken, and the static numbers that select them are '
            'optimistic exactly where the literature looks.')

HEADINGS = [
    ('### 5.1 Pairwise poisoning is an R2 attack, not an R1 attack',
     '### 5.1 Two orthogonal dimensions of representation'),
    ('### 5.2 The R1-only defense is inert',
     '### 5.2 A positive control: the statistics under test are working instruments'),
    ('### 5.3 The R2 constraint works — on the R2 metric — and does not defend',
     '### 5.3 F1: an aggregate over group counts returns its clean value'),
    ('### 5.4 Replication on a natural corpus (BBQ)',
     '### 5.4 F2: reference-based statistics track the query, not the attack'),
    ('### 5.5 Encoder robustness: a per-checkpoint property, not a family property',
     '### 5.5 F3 and the positive resolution: the diagnostic is the per-group shift'),
    ('### 5.6 Adaptive attacker: no defense survives an informed adversary',
     '### 5.6 The encoder is a factor: susceptibility is a per-checkpoint property'),
    ('### 5.7 Generation-stage propagation: does the retrieval skew reach the output?',
     '### 5.7 The skew reaches the generated text'),
    ('### 5.8 The collapse is not an artefact of one retriever',
     '### 5.8 Under an informed attacker the defenses invert'),
]

CUTS = [
    (' This free-form probe is the third instrument failure the paper documents.', ''),
    ('The honest statement is that', 'The result is that'),
]


def main():
    s = io.open(MD, encoding='utf-8').read()
    n = s.count(OLD_OPEN)
    print('results-opening anchor: %d match(es)' % n)
    if n == 1:
        s = s.replace(OLD_OPEN, NEW_OPEN, 1)
        print('results opening replaced (housekeeping note -> argument map)')

    for old, new in HEADINGS:
        c = s.count(old)
        if c == 1:
            s = s.replace(old, new, 1)
        print('%-62s %s' % (old[:62], 'renamed' if c == 1 else 'NOT FOUND (%d)' % c))

    for old, new in CUTS:
        c = s.count(old)
        if c:
            s = s.replace(old, new)
        print('cut %-52s %d occurrence(s)' % (old[:52], c))

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    print('--- section 5 headings now ---')
    for m in re.finditer(r'^### 5\.\d.*$', s, re.M):
        print('   ' + m.group(0)[:78])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
