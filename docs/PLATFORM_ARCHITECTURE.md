# Music Intelligence Platform Architecture

## Platform goal

The project is a Music Intelligence Platform with a shared Music Intelligence Core and multiple product applications.

```text
Music Intelligence Platform
├─ AI Player
├─ AI Transcriber / Notation
├─ Composition Assistant
├─ Practice & Education
└─ Research & Analysis
        │
        └─ Shared Music Intelligence Core
```

The Core owns reusable musical meaning: UMR, harmony, form, phrase/motif, rhythm/groove, cognition, learning, memory, vocabulary, style/genre/legend evidence and shared evaluation.

Applications consume this intelligence through stable contracts. They must not duplicate generic musical intelligence inside product code.

## AI Player

The AI Player uses the one-event causal loop:

```text
Perceive
→ Predict
→ Generate Candidates
→ Evaluate
→ Commit ONE EVENT
→ Listen Again
```

Shared Core owns musical decisions. Players own instrument-specific realization. Realtime owns low-latency execution only.

## AI Transcriber / Notation

The notation path is a sibling application/capability:

```text
Audio / MIDI / committed performance
→ Performance Evidence
→ Notation Intelligence
→ Logical Score
→ Practical Engraving / Layout
→ Renderer / MusicXML
→ Playable Score / Part
```

It shares musical semantics with the Core but has its own notation-domain representation.

## Shared contracts, separate product surfaces

A future standalone notation business should be able to use the same engine without importing RealSolo ensemble or realtime code.

Therefore the platform must distinguish:

- shared musical semantics;
- performance-generation semantics;
- notation semantics;
- product UI/application concerns.

This keeps the intelligence reusable while allowing multiple commercial products to evolve independently.
