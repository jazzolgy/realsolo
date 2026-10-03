# Autumn Leaves Audio Evidence Baseline Validation v0.1

This validation uses the owner-provided BE-003 segment only as a test case for
the Audio Evidence Engine. It does not promote detector hypotheses into musical
meaning or notation.

## Source preparation

The playlist range 708.0–1069.0 seconds was materialized as a 361-second WAV
segment using the same source-boundary design implemented by
`FFmpegSegmentMaterializer`.

The source SHA-256 is recorded in the adjacent JSON manifest so future runs can
distinguish source drift from detector drift.

## Direct acoustic baseline

Using the current optional librosa baseline settings:

- onset hypotheses: **1,421**
- spectral pitch hypotheses: **7,240**
- mean pitch hypotheses per onset: **5.095**
- unpitched/percussive hypotheses: **1,398**
- weak token split: kick 11, snare 1,237, cymbal-or-hihat 150
- navigation tempo reference: **103.359375 BPM**
- navigation beat positions: **601**

These values are reproducibility measurements, not ground truth.

## Why the counts differ from earlier research extraction

The earlier event dataset used a different detector pass and parameter set.
The Audio Evidence Engine now treats detector configuration as versioned
provenance. A new run must therefore be preserved as a new validation version
rather than silently replacing the older 9,627-pitch / 1,273-percussive-event
v0.2 dataset.

This is deliberate: detector drift is evidence about the system and should be
auditable.

## Separation status

A model-independent `SourceSeparator` boundary and optional
`DemucsCLISeparator` are now implemented. The Demucs adapter produces
`SeparatedSource` objects carrying model and stem metadata, after which stem
metadata may contribute only a weak acoustic instrument prior.

This validation manifest does **not** claim that Demucs separation was executed
for BE-003. The direct acoustic baseline is recorded independently so source
preparation, detector behavior, and future separator effects can be compared
rather than conflated.

## Architectural constraints confirmed

This validation pass performs no:

- chord/harmony determination;
- canonical form alignment;
- phrase or motif interpretation;
- ensemble-interaction reasoning;
- voice/staff assignment;
- notation or engraving.

Those remain downstream responsibilities.
