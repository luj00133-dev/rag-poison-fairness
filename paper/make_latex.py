"""
Convert the manuscripts to LaTeX.

Two target classes are supported because the two candidate venues differ:

  ``elsarticle``  -- Elsevier, for Computers & Security (Paper A's lead target)
  ``ieeetran``    -- IEEE, for TDSC / TIFS (Paper B's lead target, and Paper A's
                     alternative)

Pandoc handles the body; we post-process the generated ``.tex`` to (a) insert the
class and the author block, (b) convert the Markdown tables' ``longtable``
output into something Elsevier/IEEE accept, and (c) keep the math intact.

The Chinese fission report needs ``xelatex`` and a CJK font, so it is emitted
separately with a CJK-aware preamble.

Run
---
    python paper/make_latex.py                 # both manuscripts + report
    python paper/make_latex.py --class ieee    # IEEE layout
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "latex")

AUTHOR_BLOCK = r"""\author[njust]{Jiang Lu\corref{cor1}}
\ead{lujiang12@njust.edu.cn}
\ead{luj00133@gmail.com}
\cortext[cor1]{Corresponding author.}
\affiliation[njust]{organization={School of Electronic and Optical Engineering,
Nanjing University of Science and Technology}, city={Nanjing}, country={China}}
"""

IEEE_AUTHOR = r"""\author{Jiang~Lu}
\affiliation{School of Electronic and Optical Engineering,
Nanjing University of Science and Technology, Nanjing, China}
\email{lujiang12@njust.edu.cn}
"""

ELSEVIER_PREAMBLE = r"""\documentclass[review,3p,times]{elsarticle}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{calc}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\usepackage{lineno}
\modulolinenumbers[1]
"""

IEEE_PREAMBLE = r"""\documentclass[journal]{IEEEtran}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{calc}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
"""

CJK_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage{xeCJK}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{calc}
\usepackage{geometry}
\geometry{top=2.54cm,bottom=2.54cm,left=2.0cm,right=2.0cm}
\usepackage[hidelinks]{hyperref}
\setCJKmainfont{SimSun}
\setCJKsansfont{Microsoft YaHei}
"""

#: Unicode symbols that pdflatex cannot typeset, mapped to LaTeX math.
#: The manuscripts are written in Markdown, where "epsilon" and "lambda" are
#: often typed as the literal characters rather than as $\\varepsilon$. Pandoc
#: passes them through unchanged, and pdflatex then aborts on
#: "Unicode character ... not set up for use with LaTeX". Converting here keeps
#: the Markdown readable *and* the LaTeX compilable.
UNICODE_MATH = {
    "\u03b5": r"$\varepsilon$",      # ε
    "\u03bb": r"$\lambda$",          # λ
    "\u03b1": r"$\alpha$",           # α
    "\u03b2": r"$\beta$",            # β
    "\u03b3": r"$\gamma$",           # γ
    "\u03b4": r"$\delta$",           # δ
    "\u03bc": r"$\mu$",              # μ
    "\u03c4": r"$\tau$",             # τ
    "\u03c1": r"$\rho$",             # ρ
    "\u03c3": r"$\sigma$",           # σ
    "\u0394": r"$\Delta$",           # Δ
    "\u2264": r"$\leq$",             # ≤
    "\u2265": r"$\geq$",             # ≥
    "\u2248": r"$\approx$",          # ≈
    "\u2260": r"$\neq$",             # ≠
    "\u2192": r"$\rightarrow$",      # →
    "\u2208": r"$\in$",              # ∈
    "\u2209": r"$\notin$",           # ∉
    "\u2205": r"$\emptyset$",        # ∅
    "\u2229": r"$\cap$",             # ∩
    "\u222a": r"$\cup$",             # ∪
    "\u2286": r"$\subseteq$",        # ⊆
    "\u2200": r"$\forall$",          # ∀
    "\u2203": r"$\exists$",          # ∃
    "\u2211": r"$\sum$",             # ∑
    "\u221a": r"$\sqrt{}$",          # √
    "\u00d7": r"$\times$",           # ×
    "\u2212": r"$-$",                # −
    "\u2261": r"$\equiv$",           # ≡
    "\u2032": r"$'$",                # ′
}

#: Characters that have a text-mode LaTeX command and need no math.
UNICODE_TEXT = {
    "\u2014": "---",   # em dash
    "\u2013": "--",    # en dash
    "\u2018": "`", "\u2019": "'",
    "\u201c": "``", "\u201d": "''",
    "\u2026": r"\ldots{}",
    "\u00a0": "~",
    "\u2705": r"\checkmark{}",   # used in the report's red-line table
    "\u26a0": r"\textbf{!}",     # warning sign
}


def sanitize_unicode(text: str) -> str:
    """Replace characters pdflatex cannot handle.

    Math symbols are *not* wrapped when they already sit inside a ``$...$``
    span, otherwise the output would contain ``$\varepsilon$`` inside math and
    fail. We therefore split on math spans and only convert the text portions.
    """
    out = []
    for i, chunk in enumerate(re.split(r"(\$[^$]*\$)", text)):
        if i % 2 == 1:  # inside math -- leave alone
            out.append(chunk)
            continue
        for ch, rep in UNICODE_TEXT.items():
            chunk = chunk.replace(ch, rep)
        for ch, rep in UNICODE_MATH.items():
            chunk = chunk.replace(ch, rep)
        out.append(chunk)
    return "".join(out)


def _preamble(base: str) -> str:
    """Add the definitions pandoc assumes but the venue classes lack.

    Pandoc emits ``\\def\\LTcaptype{none}`` around uncaptioned ``longtable``s
    ("do not increment counter"). ``none`` is not a counter any class defines,
    so LaTeX raises ``No counter 'none' defined`` for every table. Declaring it
    is the intended fix -- the definition exists precisely to make the
    environment not increment anything, so an unused counter is harmless, and it
    is cheaper than post-processing dozens of longtable blocks.
    """
    extra = "\\newcounter{none}\n"
    if "\\newcounter{none}" in base:
        return base
    return base + extra


def run(cmd: list[str]) -> tuple[int, str, str]:
    """Run a subprocess and return (rc, stdout, stderr)."""
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.returncode, p.stdout or "", p.stderr or ""


def _convert_leftover_code_spans(tex: str) -> str:
    """Turn Markdown inline-code spans that pandoc left literal into ``\\texttt``.

    Pandoc converts `` `foo` `` to ``\\texttt{foo}`` in ordinary paragraphs, but
    it leaves the backticks literal in some positions -- prose we inserted by
    hand, and text inside constructs pandoc treats as raw. A surviving backtick
    is not a cosmetic problem: LaTeX reads whatever follows it as a control
    sequence, so `` `python analysis/x.py` `` produced
    ``! Undefined control sequence`` on ``\\python`` and failed the build.

    Content is escaped before wrapping, since code spans routinely contain
    characters that are special in LaTeX (``_`` in filenames here).
    """
    out = []
    in_code = False
    for ch in tex:
        if ch == '`':
            out.append('\\texttt{' if not in_code else '}')
            in_code = not in_code
            continue
        if in_code:
            if ch == '_':
                out.append('\\_')
            elif ch == '\\':
                # an escaped char inside a code span: keep as-is
                out.append(ch)
            elif ch in '#$%&{}':
                out.append('\\' + ch)
            elif ch == '~':
                out.append('\\textasciitilde{}')
            elif ch == '^':
                out.append('\\textasciicircum{}')
            else:
                out.append(ch)
        else:
            out.append(ch)
    return ''.join(out)


def postprocess(tex: str) -> str:
    """Turn pandoc's output into something a venue class will accept.

    Five fixes, all of which would otherwise be visible in the compiled PDF:

    1. The Markdown front matter (Author / Affiliation / Corresponding author /
       Target venue) is *already* inside ``\\author{}``; leaving the Markdown
       copy in the body duplicates the author block and leaks an internal note
       about target venues into the manuscript.
    2. Pandoc renders ``## Abstract`` as a numbered subsection. It must become
       the class's ``abstract`` environment, with the keywords following it.
    3. Markdown's own section numbering ("## 3. Title") would be doubled by
       LaTeX's, so the leading number is stripped.
    4. ``\\tightlist`` is a pandoc macro neither venue class defines, which
       produces an undefined-control-sequence error.
    5. Backticks that survive pandoc's inline-code conversion become LaTeX
       control sequences and fail the build (see
       :func:`_convert_leftover_code_spans`).

    Every backslash-bearing replacement uses ``str.replace`` rather than
    ``re.sub``: a replacement *string* in ``re.sub`` is a template, so
    ``"\\end{abstract}"`` raises "bad escape". That mistake is easy to make and
    cost us two iterations here, so the rule is applied throughout.
    """
    # 5 first: it is the pass that can still see the raw backticks
    tex = _convert_leftover_code_spans(tex)

    # 1. drop front matter (from "**Author**:" up to the Abstract heading).
    #    Slice rather than regex so the replacement never sees a backslash.
    cut = tex.find("\\textbf{Author}")
    if cut != -1:
        abs_at = tex.find("\\subsection{Abstract}", cut)
        if abs_at != -1:
            tex = tex[:cut] + tex[abs_at:]

    # 2. abstract environment
    tex = tex.replace(
        "\\subsection{Abstract}\\label{abstract}", "\\begin{abstract}"
    )
    for kw in ("\\textbf{Keywords}:", "\\textbf{Keyword}:",
               "\\textbf{Key words}:", "\\textbf{Key\\ words}:"):
        if kw in tex:
            tex = tex.replace(kw, "\\end{abstract}\n\n\\begin{keyword}\n", 1)
            break

    # 3. promote every heading by one level.
    #    The Markdown uses "# Title" for the title and "## N. Section" for the
    #    top-level sections. Since the title is removed (it goes into \title),
    #    pandoc's subsections ARE the paper's sections; leaving them as
    #    \subsection produces a document with no \section at all and an
    #    incorrectly nested hierarchy. Deepest-first so the renaming cannot
    #    cascade.
    # do it properly with an explicit level shift, deepest first, via sentinels
    # so the renaming cannot cascade
    tex = tex.replace("\\subsubsection{", "\x00L3\x00")
    tex = tex.replace("\\subsection{", "\x00L2\x00")
    tex = tex.replace("\\section{", "\x00L1\x00")
    tex = tex.replace("\x00L3\x00", "\\subsection{")
    tex = tex.replace("\x00L2\x00", "\\section{")
    tex = tex.replace("\x00L1\x00", "\\section{")  # any pre-existing section stays

    # close the keyword block at the first section heading. Must look for
    # \section (after promotion) -- searching for the pre-promotion \subsection
    # silently failed and left the keyword environment unclosed.
    if "\\begin{keyword}" in tex and "\\end{keyword}" not in tex:
        sec = tex.find("\\section{")
        if sec != -1:
            tex = tex[:sec] + "\\end{keyword}\n\n" + tex[sec:]

    # 3. strip Markdown's own numbering from headings
    for cmd in ("\\section{", "\\subsection{", "\\subsubsection{"):
        out, i = [], 0
        while True:
            j = tex.find(cmd, i)
            if j == -1:
                out.append(tex[i:])
                break
            out.append(tex[i:j + len(cmd)])
            k = j + len(cmd)
            m = re.match(r"\d+(?:\.\d+)*\.?\s+", tex[k:k + 24])
            if m:
                k += m.end()
            i = k
        tex = "".join(out)

    # 4. define the pandoc macro both classes lack
    if "\\tightlist" in tex and "\\providecommand{\\tightlist}" not in tex:
        macro = (
            "\\providecommand{\\tightlist}{%\n"
            "  \\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}}\n"
        )
        tex = tex.replace("\\begin{document}", macro + "\\begin{document}", 1)
    # 5. bibliography.  The Markdown keeps references as a plain numbered list,
    #    which pandoc renders as an itemised list inside a section -- reviewers
    #    and copy-editors expect \bibitem entries.  Rewrite the block between the
    #    References heading and the next section into a thebibliography.
    tex = _convert_bibliography(tex)
    return tex


def _convert_bibliography(tex: str) -> str:
    """Turn the Markdown reference list into a ``thebibliography`` block.

    Pandoc has no way to know that a trailing numbered list of ``[n] Title``
    lines is a bibliography: it emits ``\\section{References}`` followed by
    paragraphs whose leading bracket is *escaped* for LaTeX (``{[}1{]}]``).
    Both venue classes expect ``\\begin{thebibliography}{n}`` with ``\\bibitem``
    entries, so each numbered paragraph is rewritten and the escaped brackets
    removed.

    Matching on the escaped form matters -- a pattern written against the
    original ``[1]`` silently finds nothing, which is how the first attempt at
    this failed.
    """
    i = tex.find("\\section{References}")
    if i == -1:
        return tex
    # skip past the section heading and its label
    start = tex.find("\n", tex.find("\\label{references}") if
                     "\\label{references}" in tex[i:i + 120] else i)
    if start == -1:
        start = i
    end = tex.find("\\end{document}", start)
    if end == -1:
        end = len(tex)

    block = tex[start:end]
    # entries look like:  {[}1{]} Author...  (possibly wrapped over lines)
    parts = re.split(r"(?m)^\s*\{\[\}(\d+)\{\]\}\s*", block)
    if len(parts) < 3:
        return tex

    entries = []
    # parts = [preamble, num1, body1, num2, body2, ...]
    for k in range(1, len(parts) - 1, 2):
        body = " ".join(parts[k + 1].split())
        if not body:
            continue
        entries.append(f"\\bibitem{{ref{parts[k]}}} {body}")
    if not entries:
        return tex

    bib = ("\n\\begin{thebibliography}{" + str(len(entries)) + "}\n"
           + "\n".join(entries) + "\n\\end{thebibliography}\n")
    return tex[:start] + bib + tex[end:]


def to_tex(md_path: str, out_path: str, template: str) -> bool:
    """Run pandoc to a standalone .tex, then splice in our preamble."""
    rc, _, err = run([
        "pandoc", md_path,
        "-f", "markdown+tex_math_dollars+pipe_tables+footnotes",
        "-t", "latex",
        "--standalone",
        "--wrap=preserve",
        # Syntax highlighting emits \NormalTok / \AttributeTok / \CommentTok and
        # wraps code in Shaded/Highlighting environments, none of which a venue
        # class defines -- 57 undefined-control-sequence errors in Paper A alone.
        # The manuscripts contain only shell commands in an appendix, where
        # colour carries no information, so highlighting is off rather than
        # pulling in fancyvrb + framed + a highlight-macros style file.
        "--no-highlight",
        "-o", out_path,
    ])
    if rc != 0:
        print(f"  pandoc FAILED: {err.strip()[:300]}")
        return False

    tex = open(out_path, encoding="utf-8").read()

    # replace pandoc's default preamble with the venue template.  The
    # replacement must go through a lambda: a plain string replacement would be
    # treated as a template, and the backslashes in "\documentclass" are invalid
    # escapes there.
    def _repl(_m):
        return template + "\n\\begin{document}\n"

    tex = re.sub(
        r"\\documentclass(\[[^\]]*\])?\{article\}.*?\\begin\{document\}",
        _repl,
        tex, flags=re.S,
    )

    # pandoc emits longtable for pipe tables; both venues prefer table/tabular
    # for short tables. Leave longtable (it compiles under both classes) but
    # drop the \endhead/\endfirsthead scaffolding that confuses some classes.
    tex = tex.replace("\\endfirsthead", "")
    tex = tex.replace("\\endhead", "")
    tex = tex.replace("\\endfoot", "")
    tex = tex.replace("\\endlastfoot", "")

    tex = postprocess(tex)
    open(out_path, "w", encoding="utf-8").write(tex)
    return True


def split_title(md_path: str) -> tuple[str, str]:
    """First H1 becomes the title; any following short paragraph the subtitle."""
    lines = open(md_path, encoding="utf-8").read().split("\n")
    title = ""
    subtitle = ""
    for l in lines:
        if l.startswith("# "):
            title = l[2:].strip()
            break
    return title, subtitle


def build(md_path: str, out_name: str, cls: str, author: str) -> bool:
    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, out_name)
    base = CJK_PREAMBLE if cls == "cjk" else (
        IEEE_PREAMBLE if cls == "ieee" else ELSEVIER_PREAMBLE
    )
    base = _preamble(base)

    title, _ = split_title(md_path)
    # pandoc reads the H1 as a section, so drop it and inject \title instead
    tmp = out_path + ".body.md"
    body = open(md_path, encoding="utf-8").read()
    body = re.sub(r"^# .*$", "", body, count=1, flags=re.M)
    body = sanitize_unicode(body)
    open(tmp, "w", encoding="utf-8").write(body)

    ok = to_tex(tmp, out_path, base)
    os.remove(tmp)
    if not ok:
        return False

    tex = open(out_path, encoding="utf-8").read()
    title_tex = f"\\title{{{title}}}\n"
    if cls == "cjk":
        head = title_tex + "\\date{}\n\\maketitle\n"
    else:
        head = title_tex + author + "\\date{}\n\\maketitle\n"
    tex = tex.replace("\\begin{document}", "\\begin{document}\n" + head, 1)
    open(out_path, "w", encoding="utf-8").write(tex)
    print(f"  wrote {out_path}  ({os.path.getsize(out_path):,} bytes)")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", default="elsevier",
                    choices=["elsevier", "ieee"])
    args = ap.parse_args(argv)

    print("=" * 70)
    print("LaTeX conversion")
    print("=" * 70)

    jobs = [
        ("manuscript_R1R2_v1.md", "paperA_R1R2.tex", args.cls,
         IEEE_AUTHOR if args.cls == "ieee" else AUTHOR_BLOCK),
        ("manuscript_B_adaptive_v1.md", "paperB_adaptive.tex", args.cls,
         IEEE_AUTHOR if args.cls == "ieee" else AUTHOR_BLOCK),
    ]
    ok = 0
    for md, out, cls, author in jobs:
        p = os.path.join(HERE, md)
        if not os.path.exists(p):
            print(f"  missing {md}")
            continue
        print(f"  {md} -> {out} [{cls}]")
        if build(p, out, cls, author):
            ok += 1

    # the fission report is Chinese and needs xelatex + a CJK preamble.
    # Located by glob because the filename is Chinese and is mangled when passed
    # through some Windows shells; matching on the ASCII prefix avoids that.
    import glob as _glob

    _cands = _glob.glob(os.path.join(os.path.dirname(HERE), "R2*.md"))
    rep = _cands[0] if _cands else ""
    if os.path.exists(rep):
        print("  fission report -> report_cjk.tex [cjk]")
        if build(rep, "report_cjk.tex", "cjk", ""):
            ok += 1
    else:
        print(f"  (fission report not found at {rep})")

    print(f"\n{ok} file(s) converted into {OUT}")
    print("Compile with:  pdflatex <file>.tex   (or xelatex for the CJK report)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
