# Standalone AI Transcription / Notation Product

## Strategic direction

The transcription/notation engine should be able to ship in two contexts:

1. as a capability inside RealSolo;
2. as a standalone AI transcription / notation product.

RealSolo remains an interactive performance and music-intelligence platform.
The standalone notation product focuses on turning performed or generated music
into readable, editable, playable scores.

## Product promise

The standalone product is not "a smaller Sibelius."

Its primary promise is:

> Give it music; get back a musically intelligent score that a real musician
> can read, edit, rehearse and perform.

The long-term editor may offer conventional score editing, but automatic
musical understanding is the differentiator.

## Shared engine boundary

The reusable notation engine owns:

- performance-evidence intake contracts;
- rhythmic interpretation and quantization;
- pitch spelling;
- voice/staff separation;
- logical score construction;
- instrument notation profiles;
- practical engraving decisions;
- score-quality audit;
- MusicXML and future renderer adapters.

It must not depend directly on:

- RealSolo ensemble scheduling;
- player-generation policy;
- RealSolo-specific improvisation grammar;
- live interaction state machines;
- RealSolo UI/application code.

## Integration model

### Standalone product

Audio / MIDI / uploaded performance
-> source adapter
-> Performance Evidence
-> Notation Intelligence
-> LogicalScore
-> Practical Engraving
-> Playable Score
-> Score Editor / export

### RealSolo

AI Player / human performance
-> RealSolo adapter
-> same Performance Evidence contract
-> same Notation Intelligence
-> score shown to user / exported part

## Packaging plan

Do not split repositories prematurely.

Phase 1:
- remove direct RealSolo runtime imports from the transcribe engine;
- keep adapters at the boundary;
- enforce dependency tests.

Phase 2:
- expose a stable notation-engine API;
- separate source adapters (audio, MIDI, RealSolo);
- establish serialization for Performance Evidence and LogicalScore.

Phase 3:
- extract the engine into its own package/repository if product development
  requires independent release cadence.

This avoids duplicating code before the API is stable.

## Commercial implication

A standalone product can serve users who do not need RealSolo's interactive
ensemble features: performers, teachers, arrangers, composers, students,
producers and music schools.

RealSolo can still consume the same engine internally, so improvements to
transcription quality benefit both products.
