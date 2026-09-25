"""Scope a numeric -> author-date citation conversion: what is actually cited, and where.

IP&M prints author-date references (verified against two 2026 articles via Crossref's
deposited reference strings, e.g. "Aljundi, R., Babiloni, F., ... (2018). Memory aware
synapses..."). The manuscript is numeric, so the conversion has to be scoped before it is
attempted: how many sites, how many are multi-citations, and -- critically -- which
bracketed numbers in the text are NOT citations.

That last question is the one that breaks naive conversions. This paper also brackets
table numbers, and an earlier renumbering pass was polluted by a "[0]" table marker, so
the scope report lists every bracketed numeral that is not a known reference number.
"""
import io
import re

P = r'G:\keyan\projects\rag-poison-fairness\paper'
MD = P + r'\manuscript_R1R2_v1.md'
TEX = P + r'\latex\paperA_R1R2.tex'

REFS = set(range(1, 23))


def report(label, text, md):
    body = text[:text.rfind('\n[1] ')] if md else text[:text.find('\\bibitem{ref1}')]
    pat = r'\[(\d+(?:\s*,\s*\d+)*)\]' if md else r'\{\[\}(\d+(?:\s*,\s*\d+)*)\{\]\}'
    sites = [(m.group(0), [int(x) for x in re.findall(r'\d+', m.group(1))])
             for m in re.finditer(pat, body)]
    single = [s for s in sites if len(s[1]) == 1]
    multi = [s for s in sites if len(s[1]) > 1]
    print('=== %s ===' % label)
    print('  citation sites      : %d' % len(sites))
    print('  single-reference    : %d' % len(single))
    print('  multi-reference     : %d   %s'
          % (len(multi), [s[0] for s in multi][:8]))
    cited = sorted({n for _, nums in sites for n in nums})
    print('  distinct refs cited : %s' % cited)
    print('  refs never cited    : %s'
          % ([n for n in sorted(REFS) if n not in cited] or 'none'))

    # bracketed numerals that are not references
    allbr = re.findall(r'\[(\d+)\]' if md else r'\{\[\}(\d+)\{\]\}', body)
    odd = sorted({int(x) for x in allbr if int(x) not in REFS and int(x) != 0})
    print('  bracketed, not a ref: %s' % (odd[:12] or 'none'))
    return cited


c_md = report('markdown', io.open(MD, encoding='utf-8').read(), True)
c_tex = report('tex', io.open(TEX, encoding='utf-8').read(), False)
print()
print('the two sources cite the same set: %s' % (c_md == c_tex))
