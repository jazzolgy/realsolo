# Canonical Musical Coordinate Policy

## Purpose

RealSolo uses **musical structure**, not absolute audio time, as the canonical
coordinate system for learning, comparison, retrieval, and reasoning.

Absolute time remains important for source alignment and provenance, but it is
not the primary semantic address of a musical event.

## Canonical distinction

```text
absolute time (seconds)
= source-location / alignment / provenance coordinate

musical coordinate
= canonical learning / comparison / reasoning coordinate
```

A source event should therefore be represented, when the evidence supports it,
with a musical address such as:

```text
form / form_iteration
section
bar_in_section
bar_in_form
beat
subdivision
```

and may additionally carry structural interpretation such as:

```text
phrase_position
harmonic_position
cadence_position
role
motif_state
ensemble_state
```

## Address versus interpretation

Objective or alignment-derived coordinates must remain separate from
higher-level musical interpretation.

```yaml
musical_coordinate:
  form_iteration: 3
  section_id: A2
  bar_in_section: 6
  bar_in_form: 14
  beat: 4
  subdivision: 0.6667

structural_interpretation:
  phrase_position: ending
  harmonic_function: dominant
  cadence_position: pre_resolution
  role: foreground
  motif_state: transformation
  ensemble_state: building

audio_provenance:
  onset_sec: 83.417
  offset_sec: 83.962
  confidence: 0.93
```

The distinction matters because bar/beat alignment and phrase/harmonic-role
interpretation have different evidential status and may carry different
confidence.

## Promotion pipeline

Temporary time-domain coordinates are not final learning keys.

```text
audio timestamp
→ beat grid
→ bar
→ section
→ form iteration / chorus
→ canonical musical coordinate
→ structural interpretation
→ shared learning
```

Temporary fields such as `bar_est` may be used during alignment, but should
not become the final canonical training/retrieval address until promoted into a
validated musical coordinate with provenance and confidence.

## Jazz terminology

For jazz UI and analysis, `chorus` may remain a useful human-facing label.
Internally, `form_iteration` is preferred when the schema must also cover pop,
classical, intro/outro, interludes, and other structures where the word chorus
would be ambiguous.

## Audio provenance is preserved

Rubato, fermata, free time, pickup, tempo drift, and meter change require
musical position and wall-clock audio position to remain separately available.

```yaml
musical_position:
  section: A
  bar: 7
  beat: 2.5

audio_provenance:
  onset_sec: 83.417
  offset_sec: 83.962
```

RealSolo must never discard the source timestamp merely because a canonical
musical coordinate has been assigned.

## Shared consumer contract

The following systems should converge on the same canonical musical coordinate:

- Transcription
- Shared Learning / Corpus-derived analysis
- UMR
- Harmony / form reasoning
- Legend study
- AI Players
- Realtime ensemble runtime
- Evaluation / comparison tooling

This allows structurally equivalent moments to be compared across repeated form
iterations, alternate performances of the same tune, and eventually different
songs or genres.

## RealChord role

When a RealChord item is present in the shared symbolic corpus, it should be
treated as a primary **chart/form/harmony reference source** for canonical
musical alignment.

Its role is to help supply or validate form, section, bar, beat, and expected
harmony coordinates. It is not evidence that the performed harmony is
identical to the chart.

Keep the distinction:

```text
RealChord / chart reference
→ Expected Harmony

performed audio / transcription
→ Observed Harmony

reasoning / reconciliation
→ Inferred Harmony
```

Substitution, reharmonization, anticipation, omission, displacement, and other
performance-specific behavior must therefore remain representable without
overwriting the chart reference.

## Retrieval objective

The long-term retrieval question is not:

> What happened 842.31 seconds into a recording?

It is closer to:

> At this form position, phrase stage, harmonic function, cadence state,
> foreground/background relation, and ensemble condition, what musical actions
> occurred and how were they evaluated?

This coordinate policy is the basis for cross-chorus, cross-take,
cross-performer, and cross-song structural learning.
