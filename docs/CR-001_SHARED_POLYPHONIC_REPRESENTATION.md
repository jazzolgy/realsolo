# CR-001 — Shared Polyphonic Voicing / Orchestration Representation

Status: implemented on research/legend-intelligence for integration review.

## Decision

Use an additive shared PolyphonicEventCandidate rather than replacing the existing monophonic CandidateEvent.

This preserves the v1.30/v1.31 sax and bebop hot path while creating an instrument-neutral semantic representation for piano, guitar, voices, horn sections, strings, and later orchestration.

## Shared Core owns

VoiceEvent carries stable voice identity, pitch, **voice-local onset offset**, duration, dynamics, articulation, harmonic role, optional instrument/section/part assignment, confidence, and provenance.

PolyphonicEventCandidate carries one immediate polyphonic gesture plus group timing/dynamics/articulation, voice order, top-note constraint, bass relation, explicit doubling relations, generic voice-leading relations, confidence/provenance, tags, and annotations.

A polyphonic gesture is **not assumed to be sample-accurately simultaneous**. Each voice can start slightly early or late relative to the gesture anchor, allowing natural rolled voicings, spread attacks, near-simultaneous chord placement, and other expressive onset distributions. Semantic voice order and physical onset order are stored separately.

Generic register span, inter-note spacing, and voice-onset spread are derived properties.

The representation contains no piano-hand, guitar-fret, sax-fingering, breathing, playable-range, or pedal assumptions.

## Online contract

perform_one_polyphonic_event() accepts a SoftPlan, scores only the currently available sonority candidates, commits exactly one PolyphonicEventCandidate, and returns control to the listening/re-planning loop.

"One immediate action" means **one current musical decision/gesture**, not "all notes must sound at exactly one timestamp." Once the gesture is committed, the realtime scheduler may emit its individual VoiceEvent onsets according to their local offsets.

A gesture may therefore occupy a small internal time span while still being one immediate musical commitment. It is not a future chord sequence.

SoftPlan.exact_future_notes remains prohibited. CR-001 does not add any future-voicing-sequence field.

## Compatibility

The existing monophonic CandidateEvent, CandidateScore, OnlineMusicalEvaluator, and perform_one_event() are unchanged.

Instrument workstreams may adapt their local candidate types toward the shared representation incrementally rather than through a breaking migration.

## Generic online evaluation

The first instrument-neutral evaluator supports identity-aware voice-leading, top-line constraint satisfaction, declared bass identity, explicit doubling semantics, and ensemble-density fit. Instrument-specific feasibility remains downstream in instrument policy.

## Required follow-up

The realtime scheduler should schedule per-voice physical onsets from:
event anchor + PolyphonicEventCandidate.onset_offset_beats + VoiceEvent.onset_offset_beats.

The piano branch should replace duplicated semantic fields in PianoVoicingCandidate with an adapter or direct use of PolyphonicEventCandidate, while retaining piano range, hand distribution, pedal, touch, and style logic locally.
