# Core Change Requests

## CCR-TRANSCRIBE-001 — Promote committed performance event contract to Shared Core

### Status

Pending.

### Motivation

The transcribe workstream currently contains a prototype common intake schema at:

`src/music_intelligence/transcribe/events.py`

That location is acceptable for the vertical slice, but it should not become the
long-term ownership boundary. Piano / bass / drums / sax player branches should
not depend on the transcribe package merely to publish already-committed
performance events.

The shared contract belongs in an instrument-neutral Shared Core / UMR-facing
module, while transcribe should consume it.

### Requested Shared Core contract

Provide an instrument-neutral committed performance event schema containing,
where applicable:

- event_id
- player_id
- instrument identity
- commitment state: COMMITTED / PLAYED
- physical onset / offset
- transport beat onset / offset when available
- performed pitch evidence without forcing a single integer MIDI note
  - nominal pitch
  - frequency / cents deviation
  - continuous-pitch reference
- unpitched instrument token
- voice / layer role hints
- dynamics
- articulation
- ornament
- technique
- gesture_id
- harmonic_context_id
- phrase_context_id
- ensemble_state_id
- factorized confidence
- interpretation alternatives
- evidence references
- provenance
- extensible metadata

### Explicit exclusions

The Shared Core event contract must **not** contain notation decisions such as:

- quantized score onset / duration
- written note value
- rest spelling
- ties
- tuplets
- enharmonic spelling
- staff / written voice assignment
- MusicXML-specific fields

Those remain owned by transcribe.

### Causality

Only already committed or played events should be accepted as transcription
performance evidence. Provisional future player intent remains in
`PlayerActionIntent` / player policy and must not be treated as score truth.

### Migration plan

1. Keep the transcribe-local schema as the vertical-slice prototype.
2. Add the approved shared event contract in Shared Core.
3. Change `music_intelligence.transcribe.events` into a compatibility import /
   adapter rather than a second source of truth.
4. Update all player branches to publish the shared contract.
5. Add cross-branch contract tests.

### Why this is a Core request

This is not a request for Shared Core to own notation. It is only a request for
a common immutable description of **what was actually committed/performed** so
all downstream consumers can share one UMR-compatible performance boundary.
