"""Update the tex abstract and contribution list to cover the merged section 5.8.

The markdown and the tex carry the same front matter and had to be updated together; a
paper whose abstract promises eight findings while the body reports thirteen is the kind of
mismatch an editor notices.

Two insertions:
  * a new abstract bullet reporting the adaptive result (static advantage largest on the
    pretrained encoders, no defense surviving one perturbation step, the attack keeping over
    94% semantic fidelity, and the set-composition asymmetry);
  * a ninth numbered contribution, the six-point reporting protocol.
"""
import io
import os

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(P, 'paper', 'latex', 'paperA_R1R2.tex')

ABSTRACT_ANCHOR = ('  \\textbf{A provenance signal is necessary, and we report an '
                   'exploratory candidate.}')
ABSTRACT_BULLET = r'''\item
  \textbf{Under an informed attacker the defenses do not merely weaken, they invert --- and the static numbers are most optimistic exactly where the literature looks.} Sweeping six retrieval back-ends against a defense-aware attacker, the static advantage is \emph{largest} on the pretrained encoders the compared work uses (four begin at exactly 0.000 adversarial inclusion), yet no defense retains measurable benefit beyond one perturbation step on any of them, and the injected passages stay over 94\% semantically intact throughout, so the collapse cannot be blamed on the attack destroying its own material. The only configuration that survives at all is the one whose constraint acts on the composition of the retrieved \emph{set} rather than on individual passages --- which is precisely the constraint this paper shows is blind. From these results we derive the reporting requirements a robustness claim must meet to be interpretable, and state them as a protocol rather than a suggestion.
'''

CONTRIB_ANCHOR = r'  A measurement protocol implied by the above:'
CONTRIB_BULLET = r'''\item
  \textbf{An adaptive-attacker result that turns the negative result into an actionable one.} Against a defense-aware attacker on six back-ends, the static advantage of the strongest defense is largest precisely on the pretrained encoders the compared literature uses, and no defense survives beyond one perturbation step on any of them while the attack retains over 94\% semantic fidelity (§5.8). The only constraint that retains any benefit is the one acting on set composition rather than on individual passages --- the axis this paper shows is blind --- which is why we conclude that the escape is \emph{measurement} rather than defense. From this we derive a six-point reporting protocol for robustness claims, the constructive counterpart to the three failure modes (§5.8.1).
'''


def main():
    s = io.open(TEX, encoding='utf-8').read()
    if ABSTRACT_ANCHOR not in s:
        print('ABSTRACT ANCHOR FAIL')
        return 1
    if CONTRIB_ANCHOR not in s:
        print('CONTRIB ANCHOR FAIL')
        return 1

    # abstract bullet goes AFTER the provenance bullet's \item block, i.e. just before
    # \end{itemize} of the abstract list
    end_item = s.find('\\end{itemize}', s.find(ABSTRACT_ANCHOR))
    if end_item < 0:
        print('could not find the end of the abstract itemize')
        return 1
    s = s[:end_item] + ABSTRACT_BULLET + s[end_item:]

    # contribution 9 goes after contribution 8 (which begins at CONTRIB_ANCHOR) and before
    # the closing \end{enumerate} of the contribution list
    start8 = s.find(CONTRIB_ANCHOR)
    end_enum = s.find('\\end{enumerate}', start8)
    if end_enum < 0:
        print('could not find the end of the contribution enumerate')
        return 1
    s = s[:end_enum] + CONTRIB_BULLET + s[end_enum:]

    io.open(TEX, 'w', encoding='utf-8', newline='\n').write(s)
    print('abstract bullet added: %s' % ('94\\% semantically intact' in s))
    print('contribution 9 added : %s' % ('six-point reporting protocol for robustness' in s))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
