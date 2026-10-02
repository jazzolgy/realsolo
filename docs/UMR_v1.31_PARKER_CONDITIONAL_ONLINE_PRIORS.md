# UMR v1.31 — Parker Conditional Online Priors

v1.31 turns part of the Parker study into runtime decision priors without violating the improvisation contract. The system still does not precompose future note strings; statistics only bias the immediately available candidate at commit time.

The committed data is aggregate only. The exact-131 source is treated as pedagogical symbolic Parker-style evidence, not as a substitute for aligned recording transcription, and raw source material is not committed to this public repository.

Measured aggregate results: 1,254 adjacent transitions; stepwise motion <= whole step 61.88%; motion within a perfect fourth 94.18%; wide leaps >= perfect fifth 4.78%; adjacent compound leaps 0%. Among 56 wide leaps with a following interval, 85.71% recover in contrary motion and 98.21% are followed by an interval within a perfect fourth. Three-note spans greater than an octave occur in 0.089% of windows and four-note spans in 0.806%. Terminal long values occur in 56.49% of the 131 items.

The OnlineMusicalEvaluator now derives motion features from committed history and the candidate under consideration: step motion, within-P4 motion, wide leap, after-wide-leap state, contrary recovery, compact recovery, compound-span pressure, phrase phase, and structural terminal long tone.

PARKER_V131_BLEND keeps research/expert tendencies at full weight and the pedagogical symbolic motion prior at bounded weight 0.65. Current ensemble evidence retains override authority.

The full local regression suite after this change: **653 passed**.

Next: use the supplied Parker audio + Omnibook matches to obtain recording-aligned phrase and microtiming evidence, then compare it with the symbolic prior rather than assuming both sources encode the same behavior.
