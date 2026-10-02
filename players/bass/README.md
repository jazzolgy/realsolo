# Bass Player

AI Bassist workstream.

## Ownership

This directory is the instrument-facing public namespace for the Bass player.

During the safe migration period, executable bass policy remains implemented in
`src/music_intelligence/bass/` and is re-exported through `players.bass`.
This avoids duplicating musical policy or breaking existing imports while making
instrument ownership explicit at the repository level.

New app/integration code may import the public Bass API from `players.bass`.
Existing `music_intelligence.bass` imports remain supported until a later,
separately tested migration moves implementation ownership physically.

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

The bass layer must not build a separate jazz-harmony theory. If a concept is
instrument-neutral, it belongs in Shared Core.

## Runtime contract

Plan harmonic/rhythmic intention and candidate family, not a fixed future line.

Commit one immediate bass action -> listen -> re-plan.
