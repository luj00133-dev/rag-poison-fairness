"""Strip the stray control character left in the tex by an escaping bug.

`re.sub(..., '\\\\begin{thebibliography}{22}', s)` in the rebuild script produced a
BACKSPACE (U+0008) before "\\begin", because a non-raw replacement string turns "\\b"
into the backspace escape. The visible text was repaired by hand, but the byte itself
remained on the line.

This removes any control character other than tab/newline/return, reporting what it
removed, so the file is verified rather than assumed clean for a third time.
"""
import io

TEX = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.tex'

s = io.open(TEX, encoding='utf-8').read()
bad = [(i, ch) for i, ch in enumerate(s) if ord(ch) < 32 and ch not in '\n\r\t']
print('control characters found: %d' % len(bad))
for i, ch in bad:
    print('   offset %d: U+%04X  context %r' % (i, ord(ch), s[max(0, i - 30):i + 30]))

if bad:
    s = ''.join(ch for ch in s if ord(ch) >= 32 or ch in '\n\r\t')
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    s2 = io.open(TEX, encoding='utf-8').read()
    left = [i for i, ch in enumerate(s2) if ord(ch) < 32 and ch not in '\n\r\t']
    print('rewritten. remaining control characters: %s' % (left or 'none'))
else:
    print('nothing to do')
