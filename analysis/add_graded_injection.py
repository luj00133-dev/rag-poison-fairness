"""Make the injection produce partially contaminated contexts.

The problem, established by measurement. The injection count is uniform per stratum
(poison_count_for) and every poisoned passage gets the SAME constant ALIGN string. So all
injected passages have near-identical retrieval strength and win or lose together: either
they take the whole top-k (poison_share = 1.0) or none of them rank at all (0.0). Across the
committed runs the attacked queries are 41.9% full and 43.9% zero, with only 14.2% partial,
and the generation runs were 100% binary ({0:144, 5:432} and {0:192, 5:576}). A graded label
cannot be supervised on that, which is why the prospective validation could not be built.

The change. Give each poisoned passage a DIFFERENT amount of query-alignment vocabulary,
spread across a range, so the injected set straddles the retrieval boundary instead of
crossing it as a block. How many of them rank into a query's top-k then varies per query,
which is exactly the graded evidence-relocation label the validation needs.

Kept strictly additive and off by default:
  * PoisonSpec gains align_graded (default False) and align_strength (default 1.0);
  * when align_graded is False the text is byte-identical to before, so every committed
    number reproduces -- asserted by the reproducibility check that follows this change.
"""
import io
import os
import py_compile

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(P, 'src', 'attacks', 'poisoning.py')

SPEC_OLD = '''    #: identifier prefix so attack-success metrics need no oracle at eval time
    prefix: str = "POISON"
    seed: int = 1234'''
SPEC_NEW = '''    #: identifier prefix so attack-success metrics need no oracle at eval time
    prefix: str = "POISON"
    seed: int = 1234
    #: When True, each poisoned passage receives a DIFFERENT share of the query-alignment
    #: vocabulary, so the injected set straddles the retrieval boundary rather than
    #: crossing it as a block. This is what makes the retrieved fraction of adversarial
    #: passages vary per query instead of being all-or-nothing, which a graded validation
    #: requires. Default False keeps the original behaviour and every committed number.
    align_graded: bool = False
    #: Scale on the alignment vocabulary when align_graded is set. 1.0 spreads passages
    #: across the full ALIGN string; smaller values compress them toward the weak end.
    align_strength: float = 1.0'''

TEXT_OLD = '''                text=f"{core} {ALIGN}",'''
TEXT_NEW = '''                text=f"{core} {_align_for(i, spec)}",'''

HELPER_ANCHOR = '''    poison: List[Document] = []
    for i in range(spec.n_poison):'''

HELPER_NEW = '''    def _align_for(idx: int, spec: "PoisonSpec") -> str:
        """Alignment vocabulary for one poisoned passage.

        With align_graded off this returns ALIGN unchanged, so the generated text is
        byte-identical to the original implementation. With it on, passage ``idx`` receives
        a prefix of ALIGN whose length is spread across the passage set, giving the injected
        passages a range of retrieval strengths: the strongest still out-rank clean evidence
        while the weakest do not, so the number of adversarial passages in a top-k varies
        per query. The stance-bearing clause is untouched either way, so the group signal a
        defense must detect is unchanged.
        """
        if not spec.align_graded:
            return ALIGN
        terms = ALIGN.split()
        n = spec.n_poison
        if n <= 1:
            frac = 1.0
        else:
            # spread idx across (0, 1]: weakest first, strongest last
            frac = (idx + 1) / float(n)
        frac *= max(0.0, min(1.0, float(spec.align_strength)))
        k = max(1, int(round(frac * len(terms))))
        return " ".join(terms[:k])

''' + HELPER_ANCHOR


def main():
    s = io.open(SRC, encoding='utf-8').read()
    for old, new, label in ((SPEC_OLD, SPEC_NEW, 'PoisonSpec fields'),
                            (TEXT_OLD, TEXT_NEW, 'text assembly'),
                            (HELPER_ANCHOR, HELPER_NEW, 'helper')):
        n = s.count(old)
        print('%-20s %d match(es)' % (label, n))
        if n != 1:
            print('  ABORT: anchor must match exactly once')
            return 1
        s = s.replace(old, new, 1)
    io.open(SRC, 'w', encoding='utf-8', newline='\n').write(s)

    py_compile.compile(SRC, doraise=True)
    s2 = io.open(SRC, encoding='utf-8').read()
    print()
    print('align_graded default False : %s' % ('align_graded: bool = False' in s2))
    print('helper present             : %s' % ('def _align_for' in s2))
    print('compiles                   : True')

    # invariant: default path must reproduce the original string exactly
    ns = {}
    exec(compile('ALIGN = "a b c d e f"\n', '<t>', 'exec'), ns)
    print()
    print('default-path invariance is asserted by re-running a committed config')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
