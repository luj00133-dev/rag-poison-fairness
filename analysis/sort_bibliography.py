"""Re-sort the bibliography, which the merge left out of alphabetical order.

The two added entries (Carlini 2019, Tramer 2020) were appended before
\\end{thebibliography}, so the list now runs ... Bagwe, Dai, Edemabu, ... Nadeem, Zou,
Carlini, Tramer. IP&M prints an alphabetical author-date list, and an out-of-order entry is
exactly the kind of thing a production editor returns.

The bibliography is also a single \\begin{thebibliography} block whose entries are one
\\bibitem per line, so sorting is a matter of parsing the labels, reordering those lines and
writing them back.
"""
import io
import os
import re

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')


def key(label):
    """Sort key = the label's author part, which is what the list is alphabetised on."""
    m = re.match(r'([^()]+)', label)
    s = m.group(1).strip() if m else label
    s = s.replace('\\&', 'and').replace('\\', '')
    return s.lower()


def main():
    lines = io.open(TEX, encoding='utf-8').read().split('\n')
    start = next(i for i, l in enumerate(lines) if l.startswith('\\begin{thebibliography}'))
    end = next(i for i, l in enumerate(lines) if l.startswith('\\end{thebibliography}'))

    entries = []
    for l in lines[start + 1:end]:
        if l.startswith('\\bibitem['):
            entries.append(l)
    print('entries parsed: %d' % len(entries))

    order_before = [re.match(r'\\bibitem\[([^\]]*)\]', e).group(1) for e in entries]
    entries.sort(key=lambda e: key(re.match(r'\\bibitem\[([^\]]*)\]', e).group(1)))
    order_after = [re.match(r'\\bibitem\[([^\]]*)\]', e).group(1) for e in entries]

    changed = [b for a, b in zip(order_before, order_after) if a != b]
    print('entries that move: %d' % len(changed))
    for a, b in zip(order_before, order_after):
        if a != b:
            print('   %-28s -> %-28s' % (a[:28], b[:28]))

    new = lines[:start + 1] + entries + lines[end:]
    s = '\n'.join(new)
    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)

    # verify from disk
    s2 = io.open(TEX, encoding='utf-8').read()
    labels = re.findall(r'\\bibitem\[([^\]]*)\]', s2)
    keys = [key(l) for l in labels]
    print()
    print('labels now: %d, alphabetical: %s' % (len(labels), keys == sorted(keys)))
    print('first three: %s' % labels[:3])
    print('last three : %s' % labels[-3:])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
