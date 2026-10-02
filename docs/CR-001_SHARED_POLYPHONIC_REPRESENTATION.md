# CR-001 — Shared Polyphonic Voicing / Orchestration Representation

Status: implemented in Core and synced to player/piano.

Decision: add shared PolyphonicEventCandidate without replacing monophonic CandidateEvent. A polyphonic sonority is one immediate action, not a future chord sequence. Voice identity/order, register/spacing, doubling, top-line and bass relations, generic voice-leading, orchestration assignment, articulation/dynamics/timing, confidence and provenance are Core semantics. Piano hand distribution, playable range, pedal, touch and piano-specific voicing grammar remain in the piano layer.

The online path commits exactly one sonority and immediately returns to listen/re-plan. SoftPlan exact-future-note freezing remains prohibited.
