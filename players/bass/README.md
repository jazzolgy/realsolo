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

## Implemented vertical slices

### v1.37 — Immediate realization

Implemented in `src/music_intelligence/bass/immediate_realizer.py`.

- consumes `HarmonicFrame` rather than parsing chord symbols independently
- respects inferred -> observed -> expected evidence precedence for immediate realization
- generates walking, two-feel, and pedal immediate-action candidates
- uses Shared Core voice-leading to score current-to-next bass motion
- permits chromatic approach / direct anticipation near a known next harmony
- refuses to invent a perfect-fifth candidate when current pitch-class evidence does not support it
- returns only one-event candidates; no future bass line is frozen

### v1.38 — Bass Performance Grammar v0.1

Implemented in `src/music_intelligence/bass/performance_grammar.py`.

The grammar now separates:

- `MetricRole` — harmonic anchor / continuation / preparation / two-feel / pedal
- `MotionStrategy` — chordal / shared scale-or-color / chromatic approach / anticipation / pedal
- `TargetStrategy` — current root / current chord member / next root
- `RegisterIntent` — stable / ascend / descend
- `GrooveRelation` — on-pulse / prepare-change / sustain-anchor
- `ArticulationIntent` — neutral / connected / short / ghosted

The current realizer consumes this grammar as a soft scoring layer. Repetition,
register direction, final-beat preparation, and ensemble-density simplification
are preferences rather than hard rules.

## Source basis currently used

The first grammar pass is grounded in the uploaded bass-method material,
especially:

- walking-bass sources that distinguish chordal, scalar, and chromatic motion
- methods that privilege the last beat before a harmony change as preparation
- quarter-note walking and two-feel pedagogy
- bass groove sources showing percussion/drum-derived rhythmic behavior
- transcriptions reserved for later contextual LegendProfile analysis

These sources are treated as pedagogical/performance evidence, not universal laws.

## Not yet claimed as solved

- learned walking-bass probability model from aligned corpus
- swing/microtiming and performed note-length model
- drummer coupling using live ensemble evidence
- soloist/piano density interaction beyond a small soft penalty
- ostinato memory/pattern continuation
- bass-specific LegendProfile corpus
- acoustic/electric physical-performance models
- style-conditioned articulation / ghost-note policy
