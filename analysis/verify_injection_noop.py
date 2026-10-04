"""Assert the injection change is a no-op when align_graded is off.

Reconstructs the poisoned passages under the new code with default settings and compares them
against the texts the ORIGINAL implementation would produce, computed independently here from
the same inputs. If a single character differs, every committed number is suspect and the
change has to be fixed before anything else runs.

This is the check that the earlier prose-based reasoning ("default False keeps the original
behaviour") is worth nothing without.
"""
import io
import os
import random
import sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)

# ALIGN is a function-local constant in make_poison_docs, so it is read out of the source by
# executing just that assignment rather than retyped. A retyped copy is how a verifier ends up
# agreeing with a mistake.
_src = io.open(os.path.join(P, 'src', 'attacks', 'poisoning.py'),
               encoding='utf-8').read()
_i = _src.find('ALIGN = (')
_j = _src.find(')', _i)
_ns = {}
exec(_src[_i:_j + 1], _ns)
ALIGN = _ns['ALIGN']
assert ALIGN and len(ALIGN) > 40, 'failed to read ALIGN from source'
print('ALIGN read from source: %d chars' % len(ALIGN))


def original_text(core: str) -> str:
    """Exactly what the pre-change implementation built."""
    return f"{core} {ALIGN}"


class FakeDoc:
    def __init__(self, doc_id, text, group, stance):
        self.doc_id, self.text, self.group, self.stance = doc_id, text, group, stance
        self.is_poison = False


def main():
    from src.attacks.poisoning import PoisonSpec, make_poison_docs

    markers = (
        " The finding was filed", " The entry appears",
        " The record was cross-checked", " The measurement was repeated",
        " The result was entered", " The observation was dated",
    )

    def strip_filler(text):
        for m in markers:
            i = text.find(m)
            if i >= 0:
                return text[:i].rstrip()
        return text.strip()

    pool = []
    for i in range(12):
        grp = 'A' if i % 2 == 0 else 'B'
        pool.append(FakeDoc('d%02d' % i,
                            f"Group {grp} performed better on the task. "
                            f"The finding was filed in the annual review.",
                            grp, 1 if grp == 'A' else -1))

    spec = PoisonSpec(favoured_group='A', suppressed_group='B', n_poison=6,
                      prefix='POISON-test', seed=1234)
    docs = make_poison_docs(pool, spec)

    # Independent replay of the original algorithm, same rng seed and call order
    rng = random.Random(spec.seed)
    fav_tmpl = [d for d in pool if d.group == 'A']
    sup_tmpl = [d for d in pool if d.group == 'B']
    expected = []
    for i in range(spec.n_poison):
        if i % 2 == 0:
            base = fav_tmpl[rng.randrange(len(fav_tmpl))]
            grp, stance = 'A', +1
        else:
            base = sup_tmpl[rng.randrange(len(sup_tmpl))]
            grp, stance = 'B', -1
        core = strip_filler(base.text)
        expected.append((f"POISON-test-{i:04d}", original_text(core), grp, stance))

    print('passages generated: %d' % len(docs))
    bad = 0
    for got, (eid, etext, egrp, estance) in zip(docs, expected):
        same = (got.doc_id == eid and got.text == etext
                and got.group == egrp and got.stance == estance)
        if not same:
            bad += 1
            print('  MISMATCH')
            print('    got     : %r' % (got.doc_id, got.text[:90]))
            print('    expected: %r' % (eid, etext[:90]))
    print()
    print('VERDICT: default path is byte-identical to the original: %s' % (bad == 0))

    # and confirm the graded path actually differs, otherwise it does nothing
    spec_g = PoisonSpec(favoured_group='A', suppressed_group='B', n_poison=6,
                        prefix='POISON-test', seed=1234, align_graded=True)
    docs_g = make_poison_docs(pool, spec_g)
    lens = sorted(len(d.text) - len(original_text(strip_filler(
        d.text.split(ALIGN.split()[0])[0].rstrip()))) for d in docs_g)
    distinct = sorted({len(d.text) for d in docs_g})
    print('graded path produces %d distinct passage lengths: %s' % (len(distinct), distinct))
    print('VERDICT: graded path differs from default: %s'
          % (len(distinct) > 1))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
