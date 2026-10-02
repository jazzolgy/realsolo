# Transcribe / Notation

Shared transcription and notation workstream for RealSolo.

The goal is not only "audio to notes". This layer turns performed musical
evidence and AI-player committed events into readable score representation.

## Core boundary

**Performance Representation != Notation Representation.**

The branch follows:

Committed Performance Events / Audio Analysis
-> Performance Evidence
-> Musical Structure references
-> NotationIntent
-> NotationCandidate family
-> Preferred Readable Score
-> MusicXML / replaceable renderer

It must not feed rewritten notation back into the live player as though the
score had been the original improvisational decision.

## Consumes, does not duplicate

This workstream consumes Shared Core / UMR semantics such as:

- player / instrument identity
- performance timing and transport beat mapping
- Expected / Observed / Inferred Harmony references
- phrase / form / motif references
- ensemble state references
- committed player events

It does not own:

- player musical policy
- instrument improvisation grammar
- shared jazz harmony reasoning
- ensemble interaction scheduling
- audio synthesis

Shared Core changes, when necessary, should be proposed through
`CORE_CHANGE_REQUEST.md` rather than silently copied here.

## Current vertical slice

### 1. Common committed-event input

`CommittedPerformanceEvent` preserves:

- physical onset / offset
- performed beat onset / offset when available
- pitched or unpitched evidence
- continuous-pitch reference
- voice / layer role hints
- articulation / ornament / technique
- gesture, phrase, harmony, ensemble references
- factorized confidence
- alternatives, evidence and provenance

Only COMMITTED / PLAYED events enter transcription. Provisional player intent
is not score evidence.

### 2. Notation intent / candidates

`NotationIntent` records whether evidence should be included, omitted or kept
optional and carries notation-facing interpretation without forcing one score.

`NotationCandidate` keeps competing readable representations with separate
fidelity, readability and complexity costs.

### 3. Rhythm / score time

The initial deterministic rhythm layer supports:

- exact score-time spans using rational beat units
- readable grid quantization
- explicit rests
- barline splitting and tie chains
- arbitrary N:M tuplet representation

Microtiming is evidence, not automatically literal notation.

### 4. Pitch spelling

Enharmonic spelling is candidate-based. It may consume a key-signature or
explicit spelling preference supplied by Shared Core / a human correction, but
does not infer harmony itself.

Continuous pitch without a nominal Western pitch is not prematurely forced into
12-TET notation.

### 5. Voice / staff allocation

Staff and voice are separate from player and instrument identity. Allocation
keeps alternatives and can consume role, register, continuity and explicit
notation-context hints.

### 6. Piano gesture notation

Staggered onsets inside one committed piano gesture may produce candidates for:

- simultaneous chord
- arpeggiated chord
- separate structural onsets

A small micro-stagger is therefore not automatically copied as several written
attack times.

### 7. Bass / sax / drum directives

Initial notation-only rules cover:

- bass dead / ghost notes
- sax scoop, fall, doit, bend, vibrato, growl, subtone and grace-note evidence
- drum unpitched tokens, cymbal x-noteheads, ghost notes and common techniques

These rules describe performed evidence; they do not generate instrument music.

### 8. MusicXML

`ReadableScore` / `ScorePart` / `ScoreEvent` form the notation-domain score
assembly model. `score_to_musicxml()` projects it to MusicXML 4.0.

MusicXML is an output format, never the internal UMR.

### 9. Individual part / full score

A full `ReadableScore` owns multiple parts. Individual parts are extracted
without rewriting the underlying notation events.

## Evaluation direction

The long-term product target is not timestamp fidelity alone. Evaluation should
include readable rhythm, voice separation, instrument notation, engraving and
ultimately **Human Time to Final Score (HTFS)**.
