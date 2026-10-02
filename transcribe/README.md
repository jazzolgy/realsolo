# Transcribe / Notation

Shared transcription and notation workstream for RealSolo.

The goal is not only "audio to notes". This layer turns performed musical
evidence and AI-player committed events into readable score representation.

## Why this is separate

All player branches should be able to produce notation without each building
its own score engine.

Piano, bass, drums and saxophone can therefore expose committed performance
events while this branch owns the common notation pipeline.

## Core separation

Performance Representation != Notation Representation.

Examples:
- swing timing may be performed unevenly but notated as straight eighths;
- rolled or spread piano voicings may belong to one notated sonority;
- ghost notes or pedal resonance may be audible but omitted;
- phrase-level interpretation may require ties, rests, tuplets or simplified
  notation different from raw onset timestamps.

## Initial outputs

- internal NotationIntent / NotationCandidate structures
- MusicXML export
- instrument-part score projection
- full-score assembly
- later PDF/visual engraving through a renderer adapter

The branch should keep rendering technology replaceable. MusicXML is an output
format, not the internal musical representation.
