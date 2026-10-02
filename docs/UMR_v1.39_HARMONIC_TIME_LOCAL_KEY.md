# UMR v1.39 — Harmonic Rhythm + Local Key / Tonicization Intelligence

## Why this layer

The harmony core already knows function, tension, voice-leading, modal state,
and reharmonization. It still needs time.

The same secondary dominant can be:
- a brief tonicization;
- part of an extended dominant chain;
- a convincing key-of-the-moment;
- or the beginning of a stronger section-level region.

Those distinctions depend on duration, repetition, cadence, metric placement,
section boundaries, and whether the music quickly returns to a parent key.

## Source basis

The uploaded jazz-theory material explicitly places secondary/substitute
dominants, key-of-the-moment, interpolated chords, and modal interchange in the
advanced harmonic curriculum. The project instructions also require harmony to
be understood simultaneously at local, phrase, section, song, and performance
time scales rather than from the current chord alone.

v1.39 converts that requirement into an explicit temporal layer.

## HarmonicSpan / HarmonicRhythmSummary

HarmonicSpan stores one perceived harmonic region with:
- start / duration in beats
- root / symbol / function
- local tonic hypothesis
- metric strength
- arrival strength
- continuation strength
- provenance

HarmonicRhythmSummary measures:
- mean and median harmonic span
- harmonic changes per four beats
- acceleration / deceleration of harmonic rhythm
- regularity of span duration

This is temporal description, not a direct aesthetic score.

## Local key versus tonicization

TonicizationEvidence combines:
- dominant relation to a target
- optional predominant support
- actual resolution
- target duration
- repeated confirmation
- cadence strength
- section-boundary alignment
- strength of return to the parent key

The output is a graded LocalKeyHypothesis:
- transient
- tonicization
- local key region
- sectional key region

The threshold model is a provisional Shared-Core heuristic, not a claim that
jazz harmony has a universally correct numeric boundary between tonicization
and modulation.

## Runtime invariant

The system may know that a local target is becoming more important and may use
that knowledge to bias present candidates.

It still does not freeze a future chord sequence or future notes.

Perceive -> update harmonic-time state -> update local-key confidence ->
evaluate current harmonic affordances -> commit one immediate action ->
listen/re-plan.
