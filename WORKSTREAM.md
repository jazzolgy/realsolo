# Workstream: Transcription / Notation

Owns the transformation from performed musical evidence / UMR into readable notation.

Core principle:
Performance Representation != Notation Representation.

The transcribe workstream must not assume that every audible event becomes a
notated note. It should preserve interpretation alternatives, confidence, and
provenance where useful.

## Owns

- performance-to-notation interpretation
- score-time quantization and readable rhythm selection
- voice/staff assignment for notation
- ties, tuplets, rests, articulations, ornaments and notational simplification
- chord-symbol / harmony annotation projection
- MusicXML export
- notation-oriented rendering adapters
- readable-score evaluation
- transcription confidence / alternatives
- round-trip comparison between intended performance and engraved result

## Consumes from Shared Core

- UMR musical structure
- Expected / Observed / Inferred Harmony
- phrase / form / motif / voice / texture
- performance timing / swing / rubato
- instrument and role information
- player committed events
- ensemble state when needed for part separation

## Does NOT own

- player musical policy
- instrument-specific improvisation grammar
- shared jazz harmony theory
- ensemble interaction policy
- audio playback synthesis

Player branches should expose committed performed events / UMR-compatible
semantics. This branch decides how those events should be represented as a
readable score.

## Target flow

Committed Performance Events
-> Performance Representation
-> Musical Structure
-> Notation Intent
-> Notation Candidates
-> Preferred Readable Score
-> MusicXML / score renderer

The preferred notation may differ from literal microtiming while still
faithfully representing the musical intention.
