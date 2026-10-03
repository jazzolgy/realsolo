# Logical Score, Engraving and Export Slice

This slice extends the combined AI Transcription + Notation product from
candidate interpretation to a renderer-neutral deliverable.

```text
Performance Evidence
→ transcription interpretation
→ preferred notation candidate
→ LogicalScore
→ EngravingPlan
→ Layout / Renderer Projection
→ MusicXML
```

## Product boundary

LogicalScore is the durable notation-domain representation. It is not UMR,
not a performed-event model, and not MusicXML.

EngravingPlan contains visual decisions that can change without changing the
musical content of LogicalScore. This lets a future standalone application
offer different house styles or renderers without rewriting transcription.

MusicXML remains an export/interchange adapter. A future native editor or
renderer should consume the same LogicalScore + EngravingPlan boundary.

## Current vertical slice

The product facade can now:

1. accept versioned Performance Evidence;
2. generate transcription/notation candidates;
3. choose readable rhythm, spelling and staff allocation;
4. assemble a one-part LogicalScore;
5. build a practical EngravingPlan;
6. audit score usability;
7. export MusicXML.

Multi-part assembly, editing state, native rendering, and actual audio-model
inference remain separate next-stage work.
