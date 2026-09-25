"""Fill the AI declaration with the real tooling and move it after the appendices.

Two defects fixed here, both from earlier mechanical edits to this file:

  * The declaration section was inserted "immediately before References" --- but that was
    computed at a time when References directly followed Appendix C, so once Appendix D
    was added the declaration ended up BEFORE Appendix D and split the appendices. It now
    sits after the last appendix, which is where a declaration belongs and where the
    markdown source already has it.
  * Three identical horizontal rules had accumulated before References; two are removed.

The declaration text is written from what was actually done in this project: bibliographic
verification, prose revision, and one conceptual figure generated from a description
supplied by the author. The generators analysed in §5.7 are research instruments of the
paper itself and are already described there, so they are named in the declaration too
rather than left implicit.
"""
import io
import re

TEX = r'G:\keyan\projects\rag-poison-fairness\paper\latex\paperA_R1R2.tex'

RULE = '\\begin{center}\\rule{0.5\\linewidth}{0.5pt}\\end{center}'
DECL_HEAD = '\\section{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process}'

DECL = (
    DECL_HEAD + '\\label{ai-declaration}\n\n'
    'During the preparation of this work the author used DeepSeek Harness (deepseek-flash) '
    'in order to search and verify bibliographic metadata, draft and revise prose, and '
    'produce one conceptual schematic figure of the framework from a description supplied '
    'by the author. After using this tool, the author reviewed and edited all output, '
    'verified every citation against the primary source, and takes full responsibility for '
    'the content of the publication.\n\n'
    '\\textbf{On the tooling used for the research itself.} The generator outputs analysed '
    'in §5.7 were produced by the DeepSeek and Qwen API models and by a local Mistral-7B '
    'checkpoint, exactly as stated in §5.7 and Appendix D.6. No other AI tool contributed '
    'to the research procedure.\n\n'
)


def main():
    s = io.open(TEX, encoding='utf-8').read()

    # 1. remove the old declaration block (heading + its two paragraphs)
    start = s.find(DECL_HEAD)
    if start < 0:
        print('DECLARATION NOT FOUND')
        return 1
    end = s.find('\\section{Appendix D.')
    if end < 0 or end < start:
        print('APPENDIX D ANCHOR FAIL')
        return 1
    removed = s[start:end]
    s = s[:start] + s[end:]
    print('removed declaration block (%d chars) from between App. C and D' % len(removed))

    # 2. collapse the duplicated rules before References
    refs_at = s.find('\\section{References}')
    if refs_at < 0:
        print('REFERENCES ANCHOR FAIL')
        return 1
    head, tail = s[:refs_at], s[refs_at:]
    while head.rstrip().endswith(RULE + '\n\n' + RULE):
        head = head.rstrip()[: -len(RULE)].rstrip() + '\n\n'
    head = head.rstrip('\n') + '\n\n'

    # 3. insert the declaration between the last appendix and References
    s = head + DECL + tail
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    # ---- verify placement and structure
    s2 = io.open(TEX, encoding='utf-8').read()
    order = re.findall(r'\\section\{([^}]*)\}', s2)
    print()
    print('section order:')
    for name in order:
        print('   %s' % name[:74])
    rules = s2.count(RULE)
    print()
    print('horizontal rules : %d' % rules)
    print('ends with end{document}: %s' % s2.rstrip().endswith('\\end{document}'))
    print('placeholders left: %s' % ('NAME OF TOOL' in s2 or 'REASON:' in s2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
