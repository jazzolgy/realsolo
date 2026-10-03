# Shared Audio Intelligence Engine v0.1

## Scope

This module is the common audio-understanding input layer for RealSolo / Music
Intelligence Platform. It is instrument-neutral and must not live inside a
Player. Bill Evans / Autumn Leaves is the first validation case, not the model
identity.

The core distinction is:

Raw sound
!= confirmed note
!= instrument ownership
!= musical meaning

Uncertainty is preserved across those boundaries.

## Repository gap analysis at v0.1 start

Already present on `main`:
- Shared Learning `StructuralPerformanceData` and all-domain extractors.
- A rights-aware `AudioAnalysisAdapter` protocol and DERIVED_ONLY learning gate.
- Non-reconstructive audio aggregate ingestion.
- Score-context resolution with evidence-bounded form/phase handling.
- Offline score/performance alignment and local beat-map measurement.
- Shared ensemble-state / groove / interaction infrastructure.
- Player-specific realization boundaries.

Missing before this slice:
- a common event-level audio evidence schema with separate pitch/onset/duration/
  instrument/alignment/role confidence;
- probabilistic instrument ownership rather than a forced scalar instrument;
- a bounded Acoustic Evidence + Musical Context -> posterior revision step;
- revision history and hard-example collection;
- an uncertainty-preserving bridge into the existing Shared Learning contract;
- a public-safe Autumn Leaves validation contract.

Not implemented yet:
- separator inference (Demucs or jazz-specific);
- instrument-specific transcription backends;
- beat/form/score aligner from raw audio;
- phrase/motif/gesture grouping from audio;
- ensemble-interaction extractor from event streams;
- separator/transcriber fine-tuning loop.

## Stable v0.1 API

Import from `music_intelligence.audio_intelligence`:

- `AudioEventHypothesis`
- `ConfidenceVector`
- `AttributionFactor`
- `PosteriorAttributor`
- `RevisionLedger`
- `to_structural_performance_data`
- `AutumnLeavesValidationCase`

`AudioEventHypothesis` stores acoustic/event evidence. It may remain ambiguous.
`PosteriorAttributor` combines instrument probabilities with context factors,
but clips contextual log-shifts so musical plausibility cannot erase acoustic
evidence. `RevisionLedger` preserves every attribution change and diverts
uncertain cases to a hard-example pool.

The bridge adds `instrument_probabilities`, `role_probabilities` and
`confidence_fields` to `StructuralPerformanceEvent` as additive,
backwards-compatible fields. The legacy scalar `instrument` is left blank when
posterior probability/margin is insufficient.

## First vertical slice

Detector/transcriber hypothesis
-> factorized evidence
-> bounded posterior attribution
-> revision history / hard example
-> StructuralPerformanceData
-> existing Shared Learning Engine

The first test intentionally uses an ambiguous low-register F3 diagnostic with
Bass vs Piano-LH competition. It is synthetic validation data, not a claimed
note from the Bill Evans recording.

## Autumn Leaves validation boundary

Case: `BE-003`, owner-supplied playlist audio, 708-1069 s.

Public-safe v0.1 metadata:
- 2,000 harmonic onsets;
- 9,742 pitch hypotheses;
- 1,311 percussive events;
- pulse estimate about 103.36 BPM;
- canonical score/form alignment unresolved;
- rights disposition DERIVED_ONLY.

Exact note streams remain private/local. No Head/Solo/Out-Head label is promoted
until score/harmony alignment supports it. No evidence updates trainable priors
without explicit training permission.

## Next implementation slice

1. Beat-grid evidence contract + score-position posterior.
2. Canonical bar / chorus / HEAD-SOLO-OUT_HEAD-ENDING alignment.
3. Piano-LH vs Bass attribution factors from continuity, spectrum, simultaneous
   chord evidence, register trajectory and score harmony.
4. Drum event-class probabilities.
5. Phrase/gesture grouping and repeated-harmony ensemble comparisons.
6. Hard-example export for future separator/transcriber fine-tuning.
