# BE-003 Autumn Leaves expressive-dynamics pass v0.1

Date: 2026-10-04
Source: owner-supplied `be_playlist_project_audio`
Track window: 708.0–1069.0 s
Disposition: DERIVED_ONLY / OBSERVATION_ONLY

## Purpose

First focused pass for the shared Expressive Intelligence layer.

The goal is not only to estimate loudness. Each musical event should eventually
carry:

- source-normalized perceptual dynamic;
- local-relative dynamic;
- accent strength;
- note-body / sustain evidence;
- attack sharpness;
- dynamic trend;
- form / phrase / ensemble context;
- confidence and provenance.

Absolute time remains evidence provenance. The canonical learning coordinate is
form / section / chorus / bar / beat / subdivision once alignment is stable.

## Event-level analysis

A harmonic-component onset pass on the owner-supplied Autumn Leaves segment
produced 2,360 candidate harmonic events for this dynamics study.

For each candidate event, the private/local analysis measured:

- short-window RMS / energy;
- onset strength;
- spectral centroid / brightness proxy;
- attack sharpness;
- post-attack body / sustain ratio;
- local context within roughly +/-2 s.

A provisional perceptual-intensity score was constructed from track-normalized
feature ranks:

- 50% energy;
- 20% onset strength;
- 10% brightness;
- 10% attack sharpness;
- 10% note-body / sustain evidence.

This is an analysis heuristic, not a ground-truth dynamic label.

Observed event-level perceptual-intensity distribution on a 0..1
source-normalized scale:

- median: about 0.511
- 75th percentile: about 0.638
- 90th percentile: about 0.740
- 95th percentile: about 0.785

Local-relative dynamic difference around each event had a median near zero, as
expected by construction, with the upper 90th percentile near +0.193 and upper
95th percentile near +0.256.

## Repeated-form finding

Using the leading double-tempo timing hypothesis and provisional 32-bar cycles,
cycle-level median perceptual intensity varied substantially:

- cycle 0: 0.474
- cycle 1: 0.330
- cycle 2: 0.386
- cycle 3: 0.542
- cycle 4: 0.603
- cycle 5: 0.549
- cycle 6: 0.609
- cycle 7: 0.434
- cycle 8: 0.420

This is important for runtime design:

**same form position must not imply a fixed dynamic realization.**

Across complete provisional cycles, bar-position dynamic shapes showed generally
low or inconsistent cycle-to-cycle correlation. Repeated harmonic/form position
therefore needs a conditional expression model driven by narrative state,
ensemble density, phrase function, register, tension and prior repetition.

## Accent evidence

On the current provisional four-beat grid, mean local accent strength was
approximately:

- beat 1: 0.054
- beat 2: 0.065
- beat 3: 0.050
- beat 4: 0.052

Beat 2 is slightly elevated in this pass, but the difference is too small and
the downbeat phase is not yet canonical. Do not promote this as a Bill Evans
accent rule.

## Runtime implication

Vocabulary and motif identity must be stored separately from expressive
realization.

A reusable phrase / lick should therefore carry an expression family, not a
single frozen velocity pattern:

```text
phrase_identity
+ relative_dynamic_contour
+ accent_targets
+ attack/body profile
+ entry/peak/release roles
+ allowed variation
```

At runtime, Shared Core should choose musical expression intentions such as:

- perceptual intensity;
- relative dynamic contour;
- accent strength / relocation;
- foreground/background weight;
- note-body target;
- phrase-level crescendo / decrescendo / sudden drop.

Instrument Players then map those intentions into physical controls
(piano velocity/touch/pedal, sax air/tongue/brightness, bass pluck/body/release,
drum stroke/cymbal/ghost-note contrast).

## First learning conclusion

The current evidence supports a key design rule:

**Expression belongs to the phrase-in-context, not to the lick as a fixed
recording.**

A remembered vocabulary item may preserve a relative expressive identity, but
absolute dynamic level and accent placement must remain context-conditioned and
may change across repetitions.

## Uncertainty

This pass is still mixed-audio evidence and does not yet isolate Piano RH, Piano
LH, Bass and Drums at event level. No player-specific expressive tendency is
promoted from this file.

Next validation should repeat the same feature extraction after score/form and
instrument attribution improve, then compare:

- same motif across repetitions;
- same harmonic position across choruses;
- motif development stage vs dynamic contour;
- phrase ending vs note-body / release;
- piano phrase peak vs drummer setup / lift;
- foreground/background handoff.
