# Canonical Form-Based Learning

RealSolo treats musical position as the canonical learning coordinate.

Wall-clock/source seconds are retained only as alignment evidence and provenance.
They are not the primary address used to learn, retrieve, compare, or condition
musical behavior.

## Canonical address

Every structural event can carry a `MetricFormPosition`:

```
form
  -> hierarchical section path
  -> form iteration / chorus when relevant
  -> measure
  -> beat inside the measure
  -> local microtiming offset
```

Examples:

- jazz: `AABA32 / A1 / chorus 2 / measure 7 / beat 4+`
- pop: `verse_2 / measure 3 / beat 2`
- classical: `movement_1 / exposition / primary_theme / measure 5 / beat 1`

The section hierarchy is generic. It can describe flat pop sections, cyclic jazz
forms, or nested classical structures.

## Meter semantics

`StructuralPerformanceEvent.onset_beats` remains a quarter-note-domain
compatibility coordinate. Canonical `beat_in_measure` is expressed in the
current meter denominator's units.

Thus:

- in 4/4, beat positions 0,1,2,3 correspond to written beats 1,2,3,4;
- in 6/8, positions 0..5 correspond to written eighth-note locations;
- meter changes are represented by `MeterSegment` entries in `FormMap`.

This separates exact notation position from higher-level compound-meter pulse
grouping.

## Learning policy

1. Raw evidence may arrive before meter/form is known.
2. Such evidence receives an explicit unresolved `MetricFormPosition`.
3. It may be persisted as evidence, but unresolved metric artifacts do not
   update learned musical priors.
4. After meter/form alignment, structural events are canonicalized to
   measure/beat/form coordinates.
5. Every learning artifact receives a `metric_form_context`.
6. Artifact identity includes form position, so the same lick or comping cell in
   an A section and a bridge remains two observations.
7. Form-conditioned priors normalize across repeated choruses/form traversals,
   while exact `form_iteration` remains available for longitudinal development.

## Runtime bridge

The shared ensemble state and the AI drummer can carry the same
`MetricFormPosition`. Instrument players should consume this shared address
instead of creating instrument-specific form theories.

The Autonomous Research Listener keeps source playback time for alignment, but
its evidence is staged in the same canonical form-address schema. Structural
promotion is blocked until measure + beat are resolved.

## Principle

A time value answers: "when did this happen in the recording?"

A form address answers: "where did this happen in the music?"

RealSolo learns the second.
