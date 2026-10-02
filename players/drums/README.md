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


## Shared Legend Intelligence

The drum player consumes Shared Core Legend Intelligence through:
- `LegendProfileView`
- `VocabularyQuery / VocabularyProvider`
- `VocabularyMemoryItem`
- the six shared vocabulary-use families, including literal quotation and hybrid composition

`players/drums/` does **not** own named-musician research profiles.  It owns
only drum-set realization of shared legend evidence.  Generic kit/limb
feasibility remains instrument-owned; a named drummer's observed tendencies
remain Shared Legend evidence.

## Scorebook ingestion boundary

Drums will consume the Core Scorebook Ingestion schema once that shared schema
is present on this branch.  Do not create a competing drum-local schema for
`feel_change`, `written_part`, `navigation`, `section_role`,
`bass_instruction`, `confidence`, or `provenance`.

Until the Core schema is synchronized, existing Standard100 parsing is a
practice/compatibility adapter rather than the canonical scorebook model.
