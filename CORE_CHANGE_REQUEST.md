# Core Change Requests

## CR-001 — Shared polyphonic voicing / orchestration representation

### Status

Implemented in shared Core and synced additively to player/piano.

- shared types: VoiceEvent, PolyphonicEventCandidate, InstrumentAssignment, DoublingRelation, VoiceLeadingRelation, TopNoteConstraint, BassRelation
- shared online path: PolyphonicOnlineEvaluator, PolyphonicPerformanceMemory, perform_one_polyphonic_event
- monophonic CandidateEvent and existing online API remain unchanged
- one polyphonic sonority is treated as one immediate action, followed by listen/re-plan
- SoftPlan still rejects exact_future_notes
- piano-specific range, hand distribution, pedal, touch, and feasibility remain in players/piano
- implementation is documented in docs/CR-001_SHARED_POLYPHONIC_REPRESENTATION.md

### Requested core change

Introduce a shared polyphonic event / voicing representation in Core rather than
keeping chordal pitch collections as a piano-only data structure.

The shared representation should be able to express, at minimum:

- simultaneous and near-simultaneous pitch collections
- ordered voices / voice identities when musically meaningful
- register and spacing
- doubling
- top-note / melody constraints
- bass relationship
- voice-leading relationships from the previous sonority
- harmonic role of each voice when known
- optional instrument / section assignment for orchestration
- articulation, dynamics, onset offsets, and duration at voice or group level
- confidence / provenance hooks where interpretation is inferred rather than explicit

The representation must not assume that every voicing is a piano chord. It should
support later use by guitar, vocal harmony, horn sections, strings, ensemble writing,
and orchestration.

### Musical reason

Voicing is not intrinsically piano-specific. Piano is simply the first workstream
that requires a rich polyphonic realization model.

The same musical intelligence is needed when the system must decide how harmony is
distributed across multiple simultaneous voices or instruments. If this concept stays
inside `players/piano/`, later workstreams would have to duplicate spacing,
doubling, register, voice-leading, and top-line logic, creating incompatible local
representations.

The Core should therefore own the common semantic representation of a sonority and
its voice relationships. Instrument layers should own only instrument-specific
physical and stylistic realization constraints.

### Proposed architectural boundary

Core owns:

- abstract polyphonic sonority / voicing representation
- voice identity and inter-voice relationships
- generic spacing / register / doubling semantics
- generic voice-leading relations
- generic orchestration assignment fields or interfaces
- common evaluation features that are instrument-independent

Instrument layers own:

- playable note ranges and hand/embouchure/fingering constraints
- instrument-specific voicing grammar
- piano hand distribution and pedal behavior
- guitar string/fret feasibility
- horn/voice breathing and articulation constraints
- section-specific orchestration conventions

### Affected modules

Likely shared areas:

- `core/umr/`
- shared candidate/event representation used by online evaluation
- future orchestration / arrangement interfaces
- serialization and tests for polyphonic musical events

Current implementation affected indirectly:

- `src/music_intelligence/reasoning/legend_style_core.py`
- `src/music_intelligence/reasoning/online_improviser.py`
- `players/piano/policy.py`

### Regression risk

- changing `CandidateEvent` directly could break current monophonic improvisation tests
- sax / bebop code must remain valid without requiring polyphonic fields
- online hot-path evaluation must not become dependent on heavy orchestration objects
- exact-future-note freezing must remain prohibited; a polyphonic candidate is still
  only an immediately playable action, not a precomposed future sequence

### Compatibility direction

Prefer an additive design rather than replacing monophonic behavior outright.

Possible directions include:

1. a generic `PerformanceEvent` with one-or-more voices and a lightweight monophonic
   compatibility layer, or
2. a shared `SonorityCandidate` / `Voicing` object referenced by immediate
   performance candidates.

The final choice should be made in the Core workstream after checking UMR and realtime
requirements.

### Tests required

- existing v1.30 monophonic online improviser tests remain unchanged and passing
- a polyphonic candidate can represent multiple simultaneous voices
- voice ordering / identities survive serialization
- generic spacing and doubling information can be represented without piano semantics
- instrument-specific constraints remain outside Core
- committing a polyphonic candidate still commits only one immediate action before
  listen/re-plan
- no API permits a full future chord sequence to be frozen inside `SoftPlan`
