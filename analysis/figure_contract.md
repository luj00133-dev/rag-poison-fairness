Figure contract for the three concept figures
=============================================

Written before any drawing code, per the figure contract: core conclusion, evidence chain,
archetype, backend, and export contract for each figure. The three figures below are the ones
actually placed in the manuscript; the framework figure, the failure-modes composite and the
probe figure are currently ChatGPT-generated bitmaps or bitmaps composed from them, which is why
they do not match the four vector data figures in palette, type or resolution.

HOUSE STYLE TO MATCH (read out of the existing data figures, not chosen fresh)
  palette   Okabe-Ito: blue #0072B2, orange #E69F00, green #009E73, purple #CC79A7,
            plus grey #8c8c8c, light grey #d9d9d9
  type      Arial; base 7 pt, axis labels 7.5, legend 6.5
  widths    88 mm single column, 140 mm wide, 190 mm double
  output    vector PDF with pdf.fonttype 42 so text stays editable, plus 600-dpi PNG
  caption   la bbox tight is disabled upstream so the declared size is the delivered size
  integrity no number appears in a concept figure; every measured value lives in the data
            figures and tables. The present captions already say this, and it is kept.

--------------------------------------------------------------------------------
FIGURE 1  Framework  (replaces fig_framework.png)
--------------------------------------------------------------------------------
CORE CONCLUSION
  Pairwise poisoning is balanced in group composition by construction and skewed in
  within-group stance, which is why a composition statistic reads clean while the evidence
  has moved.

EVIDENCE CHAIN (three panels, one job each, no panel without a unique piece of evidence)
  A  RETRIEVAL.  A group-neutral query, the top-k set returned for it, and the fact that the
     query never names a group, so any skew is attributable to the corpus rather than to the
     question. Carries: the setting.
  B  INJECTION.  Matched pairs drawn from the legitimate template inventory: one favourable
     to group A, one unfavourable to group B, visually indistinguishable from clean passages.
     Carries: the balance, which is the paper's whole mechanism.
  C  WHAT A STATISTIC SEES.  Two readouts of the same attacked set: the R1 composition
     statistic at its clean value, and the R2 stance statistic skewed. Carries: the
     dissociation, and it is the panel the reader must remember.

ARCHETYPE  schematic-led composite.
HERO PANEL  C. It is drawn last, largest, and gets the only accent colour in the figure.

--------------------------------------------------------------------------------
FIGURE 2  Failure modes F1/F2/F3  (replaces fig_failure_modes.pdf)
--------------------------------------------------------------------------------
CORE CONCLUSION
  Three distinct mechanisms make an aggregate read clean, and naming them makes the
  blindness predictable rather than incidental.

EVIDENCE CHAIN (three panels, deliberately equal weight -- they are alternatives, not stages,
so a hero panel would misrepresent them as a sequence)
  F1  BALANCED COUNT.  Injection contributes equally to every group, so any statistic over
      group counts returns its clean value.
  F2  PRESERVED NUISANCE.  The statistic is anchored to a reference the attack does not
      change, so it reports the query-varying component instead of the attack-varying one.
  F3  CANCELLED SHIFT.  All groups move together, so a difference between groups is
      unchanged however far the groups move.
  Each panel carries one mechanism and nothing else; three panels of a mechanism the reader
  cannot distinguish from its siblings would fail the evidence-chain test.

ARCHETYPE  schematic-led composite, symmetric 3-up.

--------------------------------------------------------------------------------
FIGURE 3  The probe, not the corpus  (replaces fig_probe_commitment.png)
--------------------------------------------------------------------------------
CORE CONCLUSION
  The natural corpus appeared to show nothing because of the instrument: a free-form probe
  lets answers take no position, and a forced-choice probe on identical retrieval conditions
  makes them commit and reads an effect.

EVIDENCE CHAIN (two panels, before/after on the same conditions)
  LEFT   free-form probe, most answers taking no position, so the statistic reads near zero
         under every condition and no effect of any size could have appeared in it.
  RIGHT  forced-choice probe, same conditions, answers commit, effect appears.
  The contrast is the point; neither panel alone carries it.

ARCHETYPE  schematic-led composite, 2-up with a shared baseline.

--------------------------------------------------------------------------------
WHAT IS DELIBERATELY NOT DONE
--------------------------------------------------------------------------------
  * no measured values enter any of the three: the captions state that the panels are
    conceptual and point at the tables. Numbers drawn by hand into a schematic are the
    easiest way to publish a figure that disagrees with its own text.
  * the framework figure is NOT redrawn in TikZ. An earlier TikZ version exists and is
    unused; drawing it in the same backend as the other two and the four data figures gives
    one palette and one typeface across the whole paper, which is the actual defect being
    fixed. Mixing a third drawing system in would recreate the problem in a new form.
