"""Report inline-code spans in the paper, including the ones Appendix B added.

Inline backticks are a Markdown construct that pandoc turns into \\texttt{} only
in some positions; in the prose we inserted by hand for Appendix B they came
through as raw backticks, and LaTeX read the following word as a control
sequence (\\python), which is a hard compile error. The real compile check caught
it; this script localises it.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'paper', 'manuscript_R1R2_v1.md')
s = io.open(P, encoding='utf-8').read()

i = s.find('## Appendix B')
app = s[i:]
spans = re.findall(r'`([^`\n]+)`', app)
print('Appendix B: %d inline-code spans' % len(spans))
for x in sorted(set(spans)):
    print('   %s' % x)

print()
tex = io.open(os.path.join(os.path.dirname(P), 'latex', 'paperA_R1R2.tex'),
              encoding='utf-8').read()
print('\\texttt occurrences in the generated .tex: %d' % tex.count('texttt'))
print('raw backticks surviving into the .tex: %d' % tex.count('`'))
