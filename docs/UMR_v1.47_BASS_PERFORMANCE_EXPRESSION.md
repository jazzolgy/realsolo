# AI Bassist v1.47 — Performance Expression Layer

## Purpose

Pitch choice alone cannot represent a convincing bebop bass performance.

v1.47 separates the immediate note event from how that event is performed.

## BassExpressionProfile

Each immediate bass candidate may now carry:

- `sounding_length_ratio`
- `accent`
- `microtiming_ms`
- `articulation`
- `ghost_opportunity`
- explanatory reasons

The shared `CandidateEvent.duration_beats` remains the notated/structural
duration. Sounding length is a separate bass-performance property.

## Design rules

### Note length

Walking, two-feel and pedal start from different sounding-length baselines.
Interaction intent can then lengthen or shorten the current event.

This avoids treating every written quarter note as an identical acoustic event.

### Accent

Accent is not inferred directly from harmonic importance.

A harmonic anchor may get modest definition, but preparation notes are allowed
to stay lighter so the following arrival can speak.

Recent accent history also creates a small release pressure instead of
converging on one constant velocity.

### Microtiming

The current baseline permits only a small local offset around Shared Core pulse.

It deliberately avoids encoding a universal rule such as "bebop bass is always
N milliseconds ahead/behind". Current offsets are test heuristics for role
contrast and remain bounded.

### Ghost/dead-note opportunity

v1.47 does not blindly add a ghost note with a fake harmonic pitch.

It exposes a bounded opportunity score. A future physical-performance/rendering
layer can realize this as a muted/percussive bass event when instrument profile,
groove context and renderer semantics are available.

Recent ghost/dead-note use suppresses another ornament, preventing constant
decoration.

## Interaction mapping

Examples:

- ANCHOR / HOLD / RESET: slightly fuller body and stable attack
- YIELD: reduced attack/foreground presence
- PROPEL / BUILD: more forward attack energy
- CONNECT / ANSWER: connected directional delivery
- RELEASE: softened local attack
- FILL: limited ornamental opportunity

These are bass-specific realizations of interaction intent, not replacements for
Shared EnsembleState.

## Next slice

Connect expression profiles to the realtime renderer and live ensemble evidence:

1. project accent into velocity;
2. project sounding length into note-off timing;
3. project microtiming relative to authoritative transport;
4. realize ghost/dead-note opportunity with an explicit muted event type;
5. let drum/piano/soloist evidence influence the profile at runtime.
