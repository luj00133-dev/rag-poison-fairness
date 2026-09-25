"""Move four repetitive result tables from the body into Appendix C.

Rationale, measured rather than assumed (analysis/page_profile.py): the body is 39
pages of a 50-page review-format PDF and 13 of its 14 tables are in Section 5 alone.
The four tables moved here are not new evidence -- each is a second or third view of a
result already carried by a body table:

  Table 5  injection-rate sweep          same phenomenon as Table 2, different x-axis
  Table 7  R2 constraint on BBQ          same conclusion as Table 4, second corpus
  Table 10 GTE scale mechanism           a decomposition of Table 8's scale column
  Table 11 R1 inertness x encoder/scale  the cross-back-end cut of Table B1

They are appended as C6-C9 rather than renumbering C1-C5 or the body tables, because
renumbering would touch every cross-reference in the paper for no gain. The prose that
interprets each table stays in the body and gains a pointer, so no argument is lost --
only the tabular repetition.

The script is idempotent in the sense that it fails loudly rather than half-applying:
every anchor and every table block is checked to occur exactly once before any write.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, '..', 'paper', 'manuscript_R1R2_v1.md')

# (old label, new label, caption fragment that identifies the block)
MOVES = [
    ('Table 5', 'Table C6', '**Table 5.** Attack effect vs. injection rate'),
    ('Table 7', 'Table C7', '**Table 7.** R2 constraint effect on BBQ'),
    ('Table 10', 'Table C8', '**Table 10.** Where the GTE scale effect comes from'),
    ('Table 11', 'Table C9', '**Table 11.** R1-only constraint inertness across encoders'),
]

# where the body should point instead of showing the table
POINTERS = {
    'Table 5': 'The sweep itself is in Appendix C, Table C6.',
    'Table 7': 'The operating-point comparison is in Appendix C, Table C7.',
    'Table 10': 'The decomposition is in Appendix C, Table C8.',
    'Table 11': 'The cross-back-end cut is in Appendix C, Table C9.',
}


def extract_block(text, caption_start):
    """Return (start, end, block) covering the caption line, its table and one
    trailing blank line. The table body is the run of lines starting with '|'."""
    lines = text.split('\n')
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(caption_start):
            start = i
            break
    if start is None:
        return None
    j = start + 1
    while j < len(lines) and not lines[j].startswith('|'):
        if lines[j].strip() and not lines[j].startswith('*'):
            # a non-table, non-emphasis line before the table: unexpected shape
            return None
        j += 1
    while j < len(lines) and lines[j].startswith('|'):
        j += 1
    end = j
    while end < len(lines) and not lines[end].strip():
        end += 1
    return start, end, lines[start:j]


def main():
    s = io.open(MD, encoding='utf-8').read()
    original = s

    moved = []
    for old, new, caption in MOVES:
        got = extract_block(s, caption)
        if got is None:
            print('ANCHOR FAIL: %r' % caption[:60])
            return 1
        start, end, block = got
        lines = s.split('\n')
        # renumber the caption inside the moved block
        block = [block[0].replace(old + '.', new + '.')] + block[1:]
        moved.append((new, block))
        replacement = POINTERS[old]
        lines[start:end] = [replacement, '']
        s = '\n'.join(lines)
        print('moved %-9s -> %-9s (%d lines)' % (old, new, len(block)))

    # append into Appendix C, after the last table block of that appendix
    anchor = '| template_plus_projection | dense | R1 drift (TV) | 0.1625 | [0.1187, 0.2083] |'
    if s.count(anchor) != 1:
        print('APPENDIX ANCHOR FAIL (%d matches)' % s.count(anchor))
        return 1
    add = ['']
    for new, block in moved:
        add.extend(block)
        add.append('')
    s = s.replace(anchor, anchor + '\n' + '\n'.join(add).rstrip('\n'), 1)

    # in-text references to the moved tables now point at the appendix labels
    for old, new, _ in MOVES:
        s = re.sub(r'\b%s\b' % old, new, s)
        s = re.sub(r'\b%s\b' % old.replace(' ', ''), new.replace(' ', ''), s)

    if s == original:
        print('no change made')
        return 1
    io.open(MD, 'w', encoding='utf-8', newline='\n').write(s)
    print()
    print('body tables now   : %d' % len(re.findall(r'^\*\*Table \d+\.', s, re.M)))
    print('appendix tables now: %d' % len(re.findall(r'^\*\*Table [A-Z]\d+\.', s, re.M)))
    print('stale Table 5/7/10/11 references left: %d'
          % len(re.findall(r'\bTable (?:5|7|10|11)\b', s)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
