"""Restore the tex bibliography from the pre-renumber backup and do one clean pass.

Two repairs have already fought each other over these three entries, each one locally
reasonable and jointly wrong -- the tell was a citation SET mismatch between the tex and
the markdown, which is exactly why the markdown is used as the reference here.

This script starts from paperA_R1R2.tex.bak (state before the uncited-reference removal
and before any renumbering), then applies one transformation, keyed on entry CONTENT:

  1. delete the FairRAG bibitem (uncited in both sources),
  2. renumber the three entries after it by content marker: Jacobs 21->20,
     Ekstrand 22->21, Efron 23->22,
  3. rewrite in-text cite numbers with the same mapping, in a SINGLE pass that cannot
     re-match its own output,
  4. print every line it changed, so the result is inspectable rather than asserted.

The previous cascade happened because bibitem keys and cite numbers were transformed by
sequential string replacements; doing both from one content-keyed table in one pass is
the fix.

Two superseded scripts were deleted rather than left in place -- fix_uncited_reference.py
(the cascading renumber), repair_bibitem_keys.py and repair_bibitem_cites.py (partial
corrections that double-mapped the cites). Also deleted: two throwaway diagnostics whose
only purpose was to interrogate the corrupted intermediate state.

THIS SCRIPT IS NOT IDEMPOTENT: it expects .bak to hold the pre-removal state. Against an
already-repaired file the content markers no longer match ref21/ref22/ref23 and it will
refuse to write, which is the intended behaviour.
"""
import io
import re

TEX = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.tex'
BACKUP = TEX + '.bak'           # state before the uncited-reference removal. There is
                                # no .bak2: the command that was meant to create it ran
                                # with a bad workdir and silently produced nothing, which
                                # is why this script now asserts the backup exists.
MD = r'G:\keyan\projects\rag-poison-fairness\paper\manuscript_R1R2_v1.md'

DROP_MARKER = 'R. Shrestha'                     # ref20, uncited
ENTRY_MAP = [('A. Z. Jacobs', 21, 20),
             ('A. Das, R. Burke', 22, 21),
             ('R. J. Tibshirani', 23, 22)]
CITE_MAP = {21: 20, 22: 21, 23: 22}


def main():
    s = io.open(BACKUP, encoding='utf-8').read()
    before = s

    # ---- 1. drop the uncited entry
    pat = re.compile(r'\\bibitem\{ref20\}\s*[^\n]*R\. Shrestha[^\n]*\n')
    if len(pat.findall(s)) != 1:
        print('DROP FAIL: %d matches' % len(pat.findall(s)))
        return 1
    s = pat.sub('', s)
    print('dropped bibitem ref20 (FairRAG, uncited)')

    # ---- 2. renumber bibitem keys by content (keys are unique strings at this point)
    for marker, old, new in ENTRY_MAP:
        p = re.compile(r'\\bibitem\{ref%d\}(\s*[^\n]*%s)' % (old, re.escape(marker)))
        if len(p.findall(s)) != 1:
            print('KEY FAIL %r: %d matches' % (marker, len(p.findall(s))))
            return 1
        s = p.sub(lambda m, new=new: '\\bibitem{ref%d}%s' % (new, m.group(1)), s, count=1)
        print('bibitem %-20s ref%d -> ref%d' % (marker[:20], old, new))

    # the bibliography width argument covers the entry count.
    # NOTE: the replacement is a RAW string. Written as a normal string, "\\begin"
    # becomes a backspace character (U+0008), which silently produced a mangled
    # "\begin{thebibliography}" and 25 LaTeX errors -- the second escaping bug in this
    # one script, and the reason the file is re-verified rather than assumed.
    s = re.sub(r'\\begin\{thebibliography\}\{\d+\}',
               r'\\begin{thebibliography}{22}', s)

    # ---- 3. cites: one pass, deciding each token from its original numbers
    at = s.find('\\begin{thebibliography}')
    head, tail = s[:at], s[at:]
    changed = []

    def repl(m):
        nums = [int(x) for x in re.findall(r'\d+', m.group(1))]
        if not any(n in CITE_MAP for n in nums):
            return m.group(0)
        new = ', '.join(str(CITE_MAP.get(n, n)) for n in nums)
        out = '{[' + '}' + new + '{' + ']}'
        changed.append((m.group(0), out))
        return out

    head = re.sub(r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}', repl, head)
    s = head + tail

    print()
    print('cite sites rewritten: %d' % len(changed))
    for old, new in changed:
        print('   %s -> %s' % (old, new))

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    # ---- 4. verify against the file and against the markdown
    s2 = io.open(TEX, encoding='utf-8').read()
    at2 = s2.find('\\begin{thebibliography}')
    body2, refs2 = s2[:at2], s2[at2:]
    keys = [int(m.group(1)) for m in re.finditer(r'\\bibitem\{ref(\d+)\}', refs2)]
    nums = sorted({int(x) for t in re.findall(r'\{\[\}([^}]*)\{\]\}', body2)
                   for x in re.findall(r'\d+', t) if int(x) < 100})
    md = io.open(MD, encoding='utf-8').read()
    md_body = md[:md.rfind('\n[1] P. Lewis')]
    md_nums = sorted({int(x) for m in re.finditer(r'\[(\d+(?:\s*,\s*\d+)*)\]', md_body)
                      for x in re.findall(r'\d+', m.group(1)) if int(x) < 100})
    print()
    print('tex keys     : %s (contiguous %s)'
          % (keys, keys == list(range(1, len(keys) + 1))))
    print('tex cited    : %s' % nums)
    print('md  cited    : %s' % md_nums)
    print('tex uncited  : %s' % ([n for n in keys if n not in nums] or 'none'))
    print('agree with md: %s' % (nums == md_nums))
    print('changed file : %s' % (s != before))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
