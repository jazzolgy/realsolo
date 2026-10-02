# Bass Player

AI Bassist workstream.

## Owns

- walking-bass and two-feel realization
- pedal point / ostinato realization
- root/non-root bass choice
- approach tones and chromatic connection
- register and range
- duration, articulation, ghost/dead-note semantics where applicable
- groove placement and microtiming
- interaction with drums, piano, soloist, and ensemble density
- bass-specific style / LegendProfile realization

## Consumes from Shared Core

- Expected / Observed / Inferred Harmony
- functional relationship graph
- contextual tension
- shared voice-leading intelligence
- form / phrase / narrative / memory
- ensemble state and interaction
- future-harmony awareness

The bass layer must not build a separate jazz-harmony theory. If a concept is genuinely instrument-neutral, move/propose it in Core.

## Runtime contract

Plan harmonic/rhythmic intention and candidate family, not a fixed future line.

Commit one immediate bass action -> listen -> re-plan.

## First vertical slice

Implemented in `src/music_intelligence/bass/immediate_realizer.py`.

Current scope:

- consumes `HarmonicFrame` rather than parsing chord symbols independently
- respects inferred -> observed -> expected evidence precedence for immediate realization
- generates walking, two-feel, and pedal immediate-action candidates
- uses Shared Core voice-leading to score current-to-next bass motion
- permits chromatic approach / direct anticipation near a known next harmony
- refuses to invent a perfect-fifth candidate when current pitch-class evidence does not support it
- returns only one-event candidates; no future bass line is frozen

Not yet claimed as solved:

- learned walking-bass grammar
- swing/microtiming and note-length model
- drummer coupling
- soloist/piano density interaction beyond a minimal placeholder
- ostinato memory/pattern continuation
- bass-specific LegendProfile corpus
- acoustic/electric physical-performance models
