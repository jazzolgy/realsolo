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


## CR-002 — Resolved harmonic-role pitch-class material for instrument realization

### Status

Requested from player/piano; not implemented in Core yet.

### Requested Core capability

Provide an instrument-neutral resolved harmonic-role representation that can bridge
`HarmonicAffordance` to instrument candidate generation without forcing each
instrument to parse chord symbols or reconstruct jazz harmony rules independently.

Minimum useful information:

- active/root pitch class when known
- one or more pitch-class candidates for structural roles such as 3rd / 7th
- resolved pitch classes for selected tension roles exposed by the current affordance
- confidence/provenance for each role resolution
- optional indication of whether a role is required, preferred, contextual, or merely available
- preservation of Expected / Observed / Inferred distinctions where ambiguity remains

The representation should remain instrument-neutral and must not contain piano register,
hand assignment, spacing, fingering, pedal, or concrete voicing layout.

### Musical reason

v1.34 correctly gives instruments semantic affordances such as:

- `dominant.stable_identity`
- `dominant.altered_color`
- `major7.color_field`

and role labels such as `3rd`, `b7`, `b9`, `#9`, `b13`.

However, the current affordance does not expose the actual pitch classes that realize
those roles in the current harmonic frame.

If piano derives those pitch classes by parsing `G7`, `Cmaj7`, etc., then the piano
workstream silently becomes a second jazz-harmony engine, violating the shared-Core
source-of-truth boundary. The same duplication would later appear in guitar, arranging,
bass, horns, and vocal harmony.

### Current piano-side bridge

`players/piano/voicing.py` currently defines a deliberately thin
`ResolvedHarmonicMaterial` input containing:

- `affordance_id`
- `root_pitch_class`
- `role_pitch_classes`

The piano generator does **not** parse chord symbols. It returns no shell candidate
when required guide-tone roles are absent rather than guessing the harmony.

This is an adapter/provisional boundary, not intended as the permanent owner of the
shared representation.

### Likely Core boundary

Core owns:

- mapping current harmonic evidence/affordance to pitch-class role possibilities
- uncertainty/confidence/provenance
- role semantics and tension availability

Instrument layers own:

- octave/register placement
- physical realization
- spacing and hand/fingering constraints
- instrument-specific family selection
- touch/articulation/pedal

### Regression risk

Low if introduced additively.

Do not remove or repurpose the existing `HarmonicAffordance` API. A resolved-role
object can be optional/downstream so existing sax and harmony tests remain unchanged.

### Tests required

- dominant frame can resolve structural roles without instrument knowledge
- altered tension choices resolve relative to root correctly
- Expected / Observed / Inferred ambiguity is not silently collapsed
- unresolved or low-confidence roles may remain plural
- no field contains piano register/hand/voicing layout
- no chord-symbol parsing is required in `players/piano/`
- representation contains no exact future note sequence
