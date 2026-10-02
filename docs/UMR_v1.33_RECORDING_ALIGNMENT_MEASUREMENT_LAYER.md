# UMR v1.33 — Recording Alignment Measurement Layer

## Purpose

v1.31 and v1.32 established bounded symbolic-motion and score-level phrase-space priors. v1.33 adds the measurement layer required before replacing empirical Parker performance parameters with recording evidence.

The new layer is deliberately offline. It does not generate or rewrite music. It converts a score-note stream, a performance-aligned note stream, and downbeat anchors into auditable measurements.

## Local pulse, not one global BPM

A fixed tempo cannot be used as the reference for microtiming. Parker recordings drift, breathe, and may contain local rubato. LocalBeatTimeMap therefore interpolates expected note time between neighboring downbeat anchors. Onset deviation is measured against that local pulse.

This separates two questions:
1. where the ensemble's local beat actually is;
2. where Parker places the note relative to that beat.

Without this separation, tempo drift can be misread as layback or anticipation.

## Measurements

For each aligned note the layer records score beat position and pitch, expected onset from the local downbeat map, performed onset, onset offset in milliseconds, metric class, expected/performed duration, and duration ratio.

For unbroken notated eighth-note triples at positions beat -> beat+0.5 -> next beat, performed inter-onset intervals estimate local swing ratio.

## Robust note matching

If a dataset supplies stable note IDs, they are used. Otherwise an order-preserving pitch dynamic-programming alignment tolerates inserted or missed transcription notes without shifting the full suffix.

## Evidence gate

No runtime timing prior should be updated merely because a file is called aligned. Before promotion we require recording identity verified, matching score/recording excerpt, true performance-aligned note-on times, acceptable match coverage, sufficient context-bin sample count, and outlier/alignment-error audit.

## Dataset discovery

Riley & Dixon's Charlie Parker Aligned Digital Omnibook is the target evidence source because the authors describe 50 digitized Omnibook tracks with manual downbeats and performance-aligned MIDI refined against high-resolution transcription activations. A current mirror is listed at Hugging Face as xavriley/CharlieParkerAlignedOmnibook.

The public parker-timeseries derivative remains useful for score-level phrase/rest statistics, but its generated timestamp_ms is not treated as note-level microtiming evidence.

## Benchmark plan

The first measurement batch is intentionally diverse: Confirmation, Blues For Alice, Billie's Bounce, Ko Ko, Now's The Time, with Yardbird Suite as an additional benchmark.

The local compilation MP3 is kept only as a cross-check source. Tracks known not to be Parker are excluded and Milestones remains on hold until recording identity is verified.

## Runtime contract remains unchanged

The alignment layer is research-only. The live performer still follows:

Perceive -> Predict -> Generate Candidates -> Evaluate -> Commit one immediate event -> Listen Again.

Recording statistics can bias a candidate policy; they cannot precompose a future solo.
