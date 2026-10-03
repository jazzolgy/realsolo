# Observation vs Contextual Interpretation

Performance Evidence must preserve what the audio system heard before musical
context was applied.

The core rule is:

> Observation and interpretation are separate evidence layers. Context may
> revise a hypothesis, but it must never overwrite the raw detector output.

## Three-stage model

```text
1. Observation
   acoustic / detector evidence
   ↓
   raw detector probabilities

2. Interpretation
   ensemble, groove, register, continuity and other musical context
   ↓
   context-corrected posterior probabilities

3. Commitment
   downstream decision about what is stored or consumed
```

For example:

```text
raw instrument probabilities
bass       0.55
kick drum  0.35
piano      0.10

context-corrected posterior
bass       0.86
kick drum  0.10
piano      0.04
```

The posterior does not replace the raw distribution.

## Why both are required

A large change such as raw bass=.28 -> posterior bass=.91 is a warning signal:
context is doing most of the interpretive work and may be hallucinating if the
context itself is wrong.

A small change such as .88 -> .93 means acoustic evidence and context agree.

Preserving both layers enables:

- debugging;
- calibration;
- context-correction audits;
- training;
- hallucinated-interpretation detection;
- later notation decisions that may choose to trust raw evidence differently.

## Performance Evidence fields

The additive v1 contract supports:

- raw_instrument_probabilities
- context_instrument_probabilities
- raw_role_probabilities
- context_role_probabilities
- raw_confidence
- contextual_confidence
- context_corrections
- revision_history

Existing `confidence`, `alternatives`, `evidence`, and provenance remain
valid for backward compatibility.

## Ownership boundary

The Audio Evidence Engine may produce and revise these evidence distributions.
It must not decide enharmonic spelling, voice/staff assignment, ties, beams,
tuplets, cross-staff notation, engraving, or MusicXML structure.

Those decisions remain downstream in AI Transcription + Notation.


## Naming boundary

The former architectural label **Shared Audio Intelligence** is deprecated in
favor of **Audio Evidence Engine**.

The distinction is intentional:

- **Audio Evidence Engine** owns probabilistic observation, detector evidence,
  context-adjusted posterior hypotheses, calibration, revision history, and
  provenance.
- **Music Intelligence Core** owns musical meaning and instrument-neutral
  reasoning such as harmony, form, phrase, ensemble state, and interaction.
- **Performance Evidence** is the contract between them.

```text
Audio / MIDI
   ↓
Audio Evidence Engine
   ↓
Performance Evidence
   ↓
Music Intelligence Core
   ↓
Transcription / Ensemble / Learning / Player
```

The package name for new audio-side implementation should be
`music_intelligence.audio_evidence`. Existing historical references to
"Shared Audio Intelligence" should be treated as deprecated terminology rather
than a separate subsystem.
