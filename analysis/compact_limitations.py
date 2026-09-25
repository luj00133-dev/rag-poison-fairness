"""Turn Section 8's ten-item Limitations list into a summary table plus Appendix D.

Why: the list is 2,741 words, all of it in the body, and it is the last thing a reader
meets before the conclusion. The content is worth keeping -- reviewers read limitations
-- but a ten-item essay is the wrong shape for it in a methods paper whose own
contribution is a *structured* treatment of measurement failure.

The move is deliberately lossless: the full prose is relocated verbatim to Appendix D
under the same numbering, and the body keeps a table that a reader can scan. Nothing is
summarised away, and every item is still stated in the paper.

One preservation detail matters. Item 6 contains three sub-items (query diversity, the
inverted-context negative control, the fixed attribution metric) that are findings in
their own right, not caveats -- the negative control is the reason the forced-choice
probe is the primary measurement. They are moved verbatim with their parent item.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, '..', 'paper', 'manuscript_R1R2_v1.md')

START = '**Limitations.**'
END = '## 9. Conclusion'

# col 2: what the limitation constrains, or where the paper already handles it
TABLE = """**Limitations.** Ten constraints bound what this study establishes. The table states
each one and what it costs; the full statement of each, with the measurements behind it,
is in Appendix D.

| # | Limitation | What it constrains, or what already handles it |
|---|---|---|
| 1 | **Group- and stance-annotated passages are required, and neutral retrieval corpora do not carry them** | The binding constraint on this whole line of work: the framework's applicability is bounded by annotation, not computation. R1 needs a group label per passage and R2 a stance label, and no standard neutral corpus (NQ, MS MARCO) has either, nor can stance toward a group be inferred from a neutral passage. Described in detail in Appendix D.1. |
| 2 | **Neither corpus is a neutral retrieval benchmark, and they disagree in two respects** | The text-only attack works only on the controlled corpus; the R2 constraint reduces inclusion only on BBQ. Both conditions are reported rather than the favourable one, and the mechanism behind the first disagreement is identified (§5.4). |
| 3 | **The absolute R2 metric does not transfer across corpora** | `stance_gap` is exactly 0 on the balanced controlled corpus but 0.9326 on BBQ *before any attack*. Only the change from the clean baseline is informative there, and §5.4 relies on the change throughout. |
| 4 | **Injection budget must be reported as a rate, not a count** | A fixed count measures corpus size rather than attack strength. §5.4 sweeps $\\rho \\in \\{0.1\\%, \\dots, 2\\%\\}$; readers comparing against absolute counts must convert. |
| 5 | **Nine retrieval back-ends, and the scale check changed the conclusion** | GTE-base → GTE-large moves susceptibility from 0.0625 to 0.5000 within one family and recipe, so a single-encoder robustness claim reports an unmeasured checkpoint property (§5.5). Contriever is not swept at large scale and multilingual or instruction-tuned embedders are not tested. |
| 6 | **The generation-stage evaluation is multi-generator and multi-probe, and the probes disagree** | Three sub-limits, each with a measurement behind it: retrieval conditions are fixed to one backbone; the free-form probe commits to a position in only 15.6\\% (controlled) and 1.0\\% (BBQ) of cases, which is why the forced-choice probe is primary; and the effect is generator-dependent. Appendix D.6 also records the inverted-context negative control and a corrected attribution metric. |
| 7 | **Binary groups: $|\\mathcal{G}| = 2$ throughout** | Extension to $|\\mathcal{G}| > 2$ is mechanical for R1 and R2 but is not evaluated here. BBQ's race/ethnicity category is also markedly imbalanced in our build (960 vs 88 passages). |

"""


def main():
    s = io.open(MD, encoding='utf-8').read()

    i = s.find(START)
    j = s.find(END)
    if i < 0 or j < 0 or j < i:
        print('BOUNDARY FAIL: start=%d end=%d' % (i, j))
        return 1
    block = s[i:j]
    # the moved prose keeps its numbering; strip the bold lead-in and its blank line
    body_prose = block[len(START):].strip('\n')

    # Appendix D goes at the very end, after Appendix C's last table and before the
    # References divider
    refs = s.find('## References')
    if refs < 0:
        print('REFERENCES ANCHOR FAIL')
        return 1
    appendix_d = ('## Appendix D. Limitations in full\n\n'
                  'The body states each limitation in one line and what it costs; this '
                  'appendix states them in full, with the measurements behind each. The '
                  'numbering matches the body table.\n\n'
                  + body_prose + '\n\n---\n\n')

    s = s[:i] + TABLE + s[j:]
    refs = s.find('## References')
    s = s[:refs] + appendix_d + s[refs:]

    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)

    words_table = len(re.findall(r'\b[\w-]+\b', TABLE))
    words_moved = len(re.findall(r'\b[\w-]+\b', body_prose))
    print('limitations table in body : %d words' % words_table)
    print('full prose moved to App. D: %d words' % words_moved)
    print('appendix D present        : %s' % ('yes' if '## Appendix D.' in s else 'NO'))
    print('body now has %d tables, appendix %d'
          % (len(re.findall(r'^\*\*Table \d+\.', s, re.M)),
             len(re.findall(r'^\*\*Table [A-Z]\d+\.', s, re.M))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
