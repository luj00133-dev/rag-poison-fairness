"""Renumber the bibliography by first appearance, in both sources, in one pass.

Why: the reference numbers were assigned thematically, so the printed citation order
runs 1..13, 18, 19, 14, 20, 21, 17, 22, 15, 16. Elsevier's numeric style expects
numbers to ascend with first citation, and a reviewer notices when they do not.

Design notes, written down because three earlier scripts on this same file corrupted it:

  * The mapping is derived from the body, not typed in. Each reference's new number is
    its rank in the first-appearance order, so the mapping cannot drift from the text.

  * All substitutions happen in a SINGLE pass over the string with a callback, so a
    replacement can never be re-matched by another rule. The earlier cascade came from
    sequential str.replace passes.

  * Replacement strings are RAW, because "\\b" in a non-raw replacement is a backspace
    character and produced a mangled "\\begin{thebibliography}" plus 25 LaTeX errors.

  * Reference ENTRIES are reordered by moving whole blocks, never by editing numbers in
    place, and the number each entry prints is then written from the new order.

  * The result is verified by re-deriving first-appearance order from the rewritten file
    and asserting it is 1..N, plus a citation-SET comparison between markdown and tex.
    The script refuses to write unless the dry run is clean.

Run with --apply to write; without it, it only reports.
"""
import io
import re
import sys

HERE = r'G:\keyan\projects\rag-poison-fairness\paper'
MD = HERE + r'\manuscript_R1R2_v1.md'
TEX = HERE + r'\latex\paperA_R1R2.tex'


def cite_tokens(text, md):
    """(start, end, numbers, raw) for every bracketed citation, in order.

    Numbers below 1 or at/above 100 are ignored: the markdown uses "[0]" as an internal
    table marker elsewhere in the pipeline, and long numbers in the text are years or
    measurement values, not citations. Reference numbers are 1..22.
    """
    pat = r'\[(\d+(?:\s*,\s*\d+)*)\]' if md else r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}'
    out = []
    for m in re.finditer(pat, text):
        nums = [int(x) for x in re.findall(r'\d+', m.group(1))]
        if nums and all(1 <= n < 100 for n in nums):
            out.append((m.start(), m.end(), nums, m.group(0)))
    return out


def body_of(text, md):
    """The text before the reference list -- where citation order is defined.

    The tex boundary is the first \\bibitem. Two failure modes are guarded here, both of
    which produced a silent truncation rather than an error:

      * an earlier version used the markdown boundary for both formats, so in the tex the
        search missed, returned -1, and "text[:boundary]" became "drop the last
        character" -- which deleted the final newline of \\end{document} and left the file
        compiling to "Emergency stop" with no PDF;
      * re-running against an already-truncated file repeated the damage, because the
        boundary was still missing and the guard was still absent.

    A missing boundary now raises instead of slicing. The script is meant to be run once,
    against a file that still has its bibliography.
    """
    if md:
        boundary = text.rfind('\n[1] ')
        what = "markdown reference list ('\\n[1] ')"
    else:
        boundary = text.find('\\bibitem{ref1}')
        what = 'tex bibliography (\\bibitem{ref1})'
    if boundary <= 0:
        raise SystemExit(
            'BOUNDARY NOT FOUND: %s. The file is either already renumbered or damaged; '
            'restore it from the .pre-renumber copy before re-running.' % what)
    return text[:boundary]


def first_appearance(text, md):
    seen, order = set(), []
    for _, _, nums, _ in cite_tokens(body_of(text, md), md):
        for n in nums:
            if n not in seen:
                seen.add(n)
                order.append(n)
    return order


def renumber_cites(text, mapping, md):
    pat = r'\[(\d+(?:\s*,\s*\d+)*)\]' if md else r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}'

    def repl(m):
        nums = [int(x) for x in re.findall(r'\d+', m.group(1))]
        if not nums or any(n >= 100 for n in nums):
            return m.group(0)
        new = ', '.join(str(mapping.get(n, n)) for n in nums)
        if md:
            return '[%s]' % new
        return '{[' + '}' + new + '{' + ']}'

    return re.sub(pat, repl, text)


def main():
    apply = '--apply' in sys.argv
    md = io.open(MD, encoding='utf-8').read()
    tex = io.open(TEX, encoding='utf-8').read()

    order = first_appearance(md, True)
    tex_order = first_appearance(tex, False)
    print('markdown first-appearance order (%d refs): %s' % (len(order), order))
    print('tex      first-appearance order (%d refs): %s' % (len(tex_order), tex_order))
    if order != tex_order:
        print('FAIL: the two sources disagree about citation order; not writing.')
        return 1

    mapping = {old: new for new, old in enumerate(order, start=1)}
    moved = {o: n for o, n in mapping.items() if o != n}
    print()
    print('%-26s %s' % ('reference', 'old -> new'))
    for old in sorted(mapping, key=lambda k: mapping[k]):
        flag = '' if old == mapping[old] else '   <-- moves'
        print('  entry %-3d -> %-3d%s' % (old, mapping[old], flag))
    print()
    print('%d of %d entries change position' % (len(moved), len(mapping)))

    # ---------- markdown reference list: reorder blocks, then number them
    md_refs_at = md.rfind('\n[1] ')
    md_body, md_refs = md[:md_refs_at], md[md_refs_at:]
    blocks = {}
    for m in re.finditer(r'^\[(\d+)\] (.*?)(?=\n\[\d+\] |\Z)', md_refs, re.M | re.S):
        blocks[int(m.group(1))] = m.group(2).rstrip('\n')
    if sorted(blocks) != sorted(mapping):
        print('FAIL md: entry numbers %s vs mapping %s'
              % (sorted(blocks), sorted(mapping)))
        return 1
    new_md_refs = '\n\n' + '\n\n'.join('[%d] %s' % (mapping[o], blocks[o])
                                       for o in sorted(mapping, key=lambda k: mapping[k])) + '\n'

    # ---------- tex reference list: same, preserving the \bibitem line blocks
    tex_refs_at = tex.find('\\begin{thebibliography}')
    tex_head, tex_refs = tex[:tex_refs_at], tex[tex_refs_at:]
    tb = {}
    for m in re.finditer(r'\\bibitem\{ref(\d+)\}(.*?)(?=\\bibitem\{ref\d+\}|\n\\end\{thebibliography\})',
                         tex_refs, re.S):
        tb[int(m.group(1))] = m.group(2)
    if sorted(tb) != sorted(mapping):
        print('FAIL tex: entry numbers %s vs mapping %s' % (sorted(tb), sorted(mapping)))
        return 1
    new_tex_refs = ('\\begin{thebibliography}{%d}\n' % len(mapping)
                    + '\n'.join('\\bibitem{ref%d}%s' % (mapping[o], tb[o])
                                for o in sorted(mapping, key=lambda k: mapping[k]))
                    + '\n\\end{thebibliography}\n')

    # Everything after the original \end{thebibliography} -- in practice the
    # \end{document} line. The earlier version rebuilt the file from head + refs only and
    # silently dropped this tail, which removed \end{document} and made pdflatex stop
    # with "Emergency stop" and no PDF. Asserted below rather than assumed.
    close = tex_refs.find('\\end{thebibliography}')
    tex_tail = tex_refs[close + len('\\end{thebibliography}'):] if close >= 0 else ''

    new_md = renumber_cites(md_body, mapping, True) + new_md_refs
    new_tex = renumber_cites(tex_head, mapping, False) + new_tex_refs + tex_tail

    # structural guard: a document that lost its terminator must never be written
    for label, text, needed in (('tex', new_tex, '\\end{document}'),
                                ('tex', new_tex, '\\begin{document}'),
                                ('tex', new_tex, '\\end{thebibliography}')):
        if needed not in text:
            print('FAIL: rewritten %s is missing %s; not writing.' % (label, needed))
            return 1

    # ---------- dry-run verification before writing anything
    for label, text, is_md in (('markdown', new_md, True), ('tex', new_tex, False)):
        got = first_appearance(text, is_md)
        ok = got == list(range(1, len(mapping) + 1))
        print('%-9s rewritten first-appearance order %s -> ascending 1..%d: %s'
              % (label, got, len(mapping), ok))
        if not ok:
            print('FAIL: %s order is not ascending; not writing.' % label)
            return 1

    if not apply:
        print()
        print('DRY RUN clean. Re-run with --apply to write.')
        return 0

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(new_md)
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(new_tex)
    print()
    print('written.')

    # ---------- verify from disk
    md2 = io.open(MD, encoding='utf-8').read()
    tex2 = io.open(TEX, encoding='utf-8').read()
    print('markdown order now: %s' % first_appearance(md2, True))
    print('tex      order now: %s' % first_appearance(tex2, False))
    keys = [int(m.group(1)) for m in re.finditer(r'\\bibitem\{ref(\d+)\}', tex2)]
    print('tex keys contiguous: %s' % (keys == list(range(1, len(keys) + 1))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
