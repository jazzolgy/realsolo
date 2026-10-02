# UMR v1.48 — Executable Native Trio Deciders

## Purpose

v1.47 defined the common runtime adapter boundary. v1.48 connects that boundary
to executable instrument logic already present in the player workstreams.

## Piano

The realtime branch now consumes the current player/piano comping pipeline:

- PianoVoicingRequest
- immediate candidate generation
- contextual comping evaluation
- harmonic reasoning guidance
- one committed comping action
- RenderGesture projection

Silence remains a valid committed piano decision.

The app does not derive chord spellings for piano. It expects a resolved
PianoVoicingRequest / harmonic material from upstream Shared Harmony.

## Bass

The realtime branch now consumes the executable player/bass stack:

- Shared HarmonicFrame
- bass interaction grammar
- local performance memory
- immediate bass candidate generation
- shared voice-leading
- bass performance-expression profile
- one immediate committed bass event

The rendered event preserves note-body ratio, articulation and local
microtiming projection.

## Drums

The realtime branch now consumes the executable player/drums online policy:

- DrummerSoftPlan
- DrummerRuntimeContext
- tempo-conditioned swing timing
- ride / hi-hat / comping candidates
- setup / transition behavior
- performance memory
- one immediate drum gesture

Drum kit voices are projected to renderer MIDI only after the player has made
its musical decision.

## Runtime loop

The practical trio path is now:

Shared EnsembleState snapshot
-> Interaction Scheduler
-> PianoNativeDecider / BassNativeDecider / DrumsNativeDecider
-> Runtime Adapters
-> PlayerRuntimeDecision
-> atomic state publication
-> RenderGesture(s)
-> listen / re-plan

All three deciders receive the same snapshot generation.

## Current dependency

The realtime branch carries synchronized snapshots of executable player code so
the integration can be tested now. Instrument policy ownership remains in
player/piano, player/bass and player/drums. Future development should continue
there and be synchronized/merged into realtime rather than editing duplicated
instrument policy inside the app.

## Causality

No native decider returns a future line, future bar, or score.

Only one immediate player decision crosses the realtime boundary per cycle.
