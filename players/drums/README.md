# Drum Player

AI Drummer workstream.

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

The drum layer should understand harmonic rhythm and form without duplicating Shared Harmony theory.

## Runtime contract

Plan groove, energy, orchestration, and interaction intention rather than a fixed future drum sequence.

Commit one immediate drum gesture -> listen -> re-plan.
