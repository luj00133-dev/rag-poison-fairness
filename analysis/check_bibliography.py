"""Check the bibliography in both sources: contiguous numbering, no uncited entries.

This exists because two real defects in this paper were invisible to a clean compile:

  * one reference was never cited (it compiled fine, and `pdflatex` reports nothing),
  * and reference numbers were assigned thematically rather than by first appearance,
    so the printed citation order is not monotonic.

The second is reported, not fixed: renumbering by first appearance would rewrite every
citation in the paper, including numbers inside reference entries themselves, and the
paper already shipped with the pattern. The first is fixed.

Verification is done on the SOURCES rather than on extracted PDF text, because
pdftotext wraps the reference list across lines and truncates the bracketed numerals --
which produced a false "3 uncited references" reading the first time this was checked.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, '..', 'paper', 'manuscript_R1R2_v1.md')
TEX = os.path.join(HERE, '..', 'paper', 'latex', 'paperA_R1R2.tex')


def cite_numbers(body):
    """All numbers cited in the body, across the three syntaxes the two files use."""
    found = set()
    # markdown and tex plain: [12] or [3, 5]
    for m in re.finditer(r'\[(\d+(?:\s*,\s*\d+)*)\]', body):
        found.update(int(n) for n in re.findall(r'\d+', m.group(1)))
    # tex escaped: {[}12{]} and {[}3, 5{]}
    for m in re.finditer(r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}', body):
        found.update(int(n) for n in re.findall(r'\d+', m.group(1)))
    found.discard(0)
    return found


def main():
    md = io.open(MD, encoding='utf-8').read()
    tex = io.open(TEX, encoding='utf-8').read()

    ok = True

    # ---- markdown
    # The reference list starts at the FIRST numbered entry; entry numbers may skip
    # (e.g. a list numbered 1..17, 19), so collect every ^[N] line rather than
    # assuming contiguity, and report gaps separately.
    md_refs_at = md.rfind('\n[1] P. Lewis')
    md_body, md_refs = md[:md_refs_at], md[md_refs_at:]
    md_nums = [int(m.group(1)) for m in re.finditer(r'^\[(\d+)\] ', md_refs, re.M)]
    print('markdown entries      : %d  numbers %d..%d'
          % (len(md_nums), min(md_nums), max(md_nums)))
    gaps = [n for n in range(1, max(md_nums) + 1) if n not in md_nums]
    if gaps:
        print('  FAIL numbering gaps : %s' % gaps)
        ok = False
    cited_md = cite_numbers(md_body)
    uncited_md = [n for n in md_nums if n not in cited_md]
    print('  uncited             : %s' % (uncited_md or 'none'))
    print('  cited but undefined : %s'
          % (sorted(n for n in cited_md if n not in md_nums) or 'none'))
    ok = ok and not uncited_md

    # ---- tex
    tex_bib_at = tex.find('\\begin{thebibliography}')
    tex_body, tex_refs = tex[:tex_bib_at], tex[tex_bib_at:]
    keys = [int(m.group(1)) for m in re.finditer(r'\\bibitem\{ref(\d+)\}', tex_refs)]
    width = re.search(r'\\begin\{thebibliography\}\{(\d+)\}', tex_refs)
    cited_tex = cite_numbers(tex_body)
    uncited_tex = [n for n in keys if n not in cited_tex]
    print('tex entries           : %d  keys contiguous: %s  width arg: %s'
          % (len(keys), keys == list(range(1, len(keys) + 1)),
             width.group(1) if width else '?'))
    print('  uncited             : %s' % (uncited_tex or 'none'))
    print('  cited but undefined : %s'
          % (sorted(n for n in cited_tex if n not in keys) or 'none'))
    ok = ok and not uncited_tex

    # ---- reported, not fixed: printed citation order
    seen, order = set(), []
    for m in re.finditer(r'\[(\d+(?:\s*,\s*\d+)*)\]', md_body):
        for n in re.findall(r'\d+', m.group(1)):
            n = int(n)
            if n and n not in seen:
                seen.add(n)
                order.append(n)
    print()
    print('printed citation order: %s' % order)
    if order != sorted(order):
        print('  NOTE numbering is thematic, not by first appearance. Reported, not')
        print('       renumbered: doing so would rewrite every citation in the paper.')

    print()
    print('RESULT: %s' % ('bibliography consistent' if ok else 'PROBLEM'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
