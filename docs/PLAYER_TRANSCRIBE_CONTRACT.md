# Player -> Transcribe Contract

## Purpose

Player branches must not implement independent notation engines.

Each player should eventually provide a stream of committed musical events with
enough semantic metadata for transcription.

Minimum shared information should include, where applicable:

- player / instrument identity
- committed event ID
- performance onset / offset
- performed pitch or unpitched instrument token
- duration
- voice / layer role
- articulation
- dynamics
- ornament / technique
- harmonic / phrase context references
- gesture grouping
- confidence / provenance

Polyphonic gestures may contain non-simultaneous voice onsets while still
belonging to one musical gesture.

## Transcribe responsibility

The transcribe layer decides:

- score-time quantization
- note/rest spelling
- enharmonic spelling
- tuplets
- ties
- staff / voice allocation
- notation of articulations and techniques
- whether an audible event is notation-relevant
- readable simplification
- MusicXML projection

## Runtime relation

Notation is downstream of committed performance.

It must never feed a rewritten score back into the live player as if the score
had been the original improvisational decision.
