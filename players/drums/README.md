# Drum Player

AI Drummer workstream.

## Ownership

This directory is the instrument-facing public namespace for the Drum player.

During the safe migration period, executable drum policy remains implemented in
`src/music_intelligence/drums/` and is re-exported through `players.drums`.
This avoids copying drummer policy into the realtime app and preserves every
existing `music_intelligence.drums` import.

New app/integration code may import the public Drum API from `players.drums`.
Physical movement of implementation files can happen later as an isolated,
fully tested migration.

## Owns

- ride pattern / hi-hat / snare / bass-drum realization
- swing and straight time-feel realization
- comping density and orchestration
- fills, setups, kicks, crashes, cymbal choices
- dynamics, articulation, stick/brush semantics
- limb/kit feasibility
- microtiming and groove placement
- phrase punctuation and sectional transitions
- interaction with bass, piano, soloist, and ensemble energy
- drummer-specific style / LegendProfile realization

## Consumes from Shared Core

- song / section / phrase / form
- ensemble state and interaction
- tension / release trajectory
- musical narrative and memory
- harmonic rhythm when relevant
- future structural awareness

The drum layer may understand harmonic rhythm and form without duplicating
Shared Harmony theory.

## Runtime contract

Plan groove, energy, orchestration, and interaction intention rather than a
fixed future drum sequence.

Commit one immediate drum gesture -> listen -> re-plan.
