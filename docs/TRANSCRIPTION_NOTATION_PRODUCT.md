# AI Transcription + Notation Product

## Product decision

The standalone business is a single **AI Transcription + Notation** product.

Transcription and notation are not separate commercial products in this architecture.
They are successive intelligence stages of one customer workflow:

```text
Audio / MIDI / live or uploaded performance
→ source adapter / analysis model
→ Performance Evidence
→ transcription interpretation
→ notation candidates
→ Logical Score
→ engraving / layout
→ readable editable score
→ export / editor / rehearsal use
```

The product promise is therefore not merely "audio to notes" and not merely
"automatic engraving." It is:

> Give the system music and receive a musically interpreted, readable,
> editable score suitable for real rehearsal and performance.

## Business boundary

The combined product may become independent from RealSolo.

Therefore the reusable engine must:

- accept multiple source adapters rather than depend on one audio model;
- preserve uncertainty and alternatives from transcription into notation;
- use versioned Performance Evidence and notation/score contracts;
- remain independent of RealSolo realtime scheduling and Player generation;
- expose a product-facing facade that a desktop app, web app, mobile app,
  cloud service, or RealSolo adapter can all call;
- keep renderer/editor concerns downstream from musical transcription logic.

## Intelligence layers

### 1. Source understanding

Future audio/MIDI adapters may perform:

- source separation;
- onset/offset estimation;
- pitch / continuous-pitch tracking;
- instrument identification;
- dynamic/articulation/technique evidence;
- beat/tempo/form/harmony observations.

These adapters produce Performance Evidence. They do not decide notation.

### 2. Transcription interpretation

The engine interprets performed evidence in score time:

- rhythmic quantization;
- tuplets;
- rests and ties;
- gesture grouping;
- phrase-aware simplification;
- uncertainty-preserving alternatives.

### 3. Notation intelligence

The engine decides readable representation:

- enharmonic spelling;
- voice/staff allocation;
- instrument notation conventions;
- dynamics/articulations/techniques;
- score construction;
- part extraction.

### 4. Engraving and delivery

Downstream layers provide:

- practical engraving/layout;
- collision and spacing rules;
- MusicXML;
- future native renderer;
- future editor;
- PDF/SVG or other delivery formats.

## RealSolo relationship

RealSolo is one source/application of the same engine:

```text
RealSolo committed Player events
→ RealSolo adapter
→ Performance Evidence
→ same Transcription + Notation Engine
→ live chart / part / score / export
```

A standalone product instead enters through audio/MIDI/upload adapters.

The engine must not know which product invoked it.
