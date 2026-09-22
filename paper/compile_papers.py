"""Compile both papers with MiKTeX pdflatex, twice each, and report REAL LaTeX
errors parsed from the .log files -- not from the pandoc conversion log.

This exists because we previously reported "0 LaTeX errors" on the strength of
the conversion script's output while `pdflatex` was not even on PATH. This
script is the check that claim should always have been.
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
LATEX = os.path.join(HERE, 'latex')
PDFLATEX = os.path.join(
    os.environ['LOCALAPPDATA'], 'Programs', 'MiKTeX', 'miktex', 'bin', 'x64',
    'pdflatex.exe')

report = []


def emit(line=''):
    report.append(line)
    print(line)


emit('pdflatex: %s  exists=%s' % (PDFLATEX, os.path.exists(PDFLATEX)))

for stem in ('paperA_R1R2', 'paperB_adaptive'):
    tex = os.path.join(LATEX, stem + '.tex')
    for p in (1, 2):
        log = os.path.join(LATEX, '%s.pass%d.log' % (stem, p))
        with open(log, 'wb') as fh:
            rc = subprocess.call(
                [PDFLATEX, '-interaction=nonstopmode',
                 '-output-directory=' + LATEX, tex],
                stdout=fh, stderr=subprocess.STDOUT)
        emit('%-18s pass %d exit=%s' % (stem, p, rc))

    raw = open(os.path.join(LATEX, '%s.pass2.log' % stem),
               encoding='latin-1').read()
    errs = [m for m in re.findall(r'^!.*$', raw, re.M)]
    undef = re.findall(
        r'LaTeX Warning: (?:Citation|Reference) .*?undefined', raw)
    overfull = re.findall(r'Overfull \\hbox \(([0-9.]+)pt', raw)
    pages = re.search(r'Output written on .*?\((\d+) pages', raw)
    pdf = os.path.join(LATEX, stem + '.pdf')
    emit('  errors=%d  undefined_refs=%d  overfull>20pt=%d  pages=%s  pdf=%d bytes'
         % (len(errs), len(undef),
            len([o for o in overfull if float(o) > 20.0]),
            pages.group(1) if pages else '?',
            os.path.getsize(pdf) if os.path.exists(pdf) else -1))
    for e in errs[:10]:
        emit('   ' + e[:160])
    for u in undef[:10]:
        emit('   U ' + u[:160])

open(os.path.join(LATEX, 'compile_report.txt'), 'w',
     encoding='utf-8').write('\n'.join(report) + '\n')
