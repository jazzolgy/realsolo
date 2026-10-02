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


## CR-003 — Shared ensemble-response observation / interaction evidence

### Status

Requested from player/piano; current implementation is an experimental piano-side
adapter only.

### Requested Core capability

Provide an instrument-neutral representation for what the ensemble does shortly after
a performed gesture, without assuming that the earlier gesture caused the later event.

Minimum useful fields:

- responding actor / section
- observed response type
- response strength
- latency in beats or time
- observation confidence
- explicit attribution confidence
- provenance
- reference to the immediately preceding performed gesture or interaction event

Candidate response types currently explored in piano:

- rhythmic echo
- accent alignment
- phrase extension
- phrase end
- density increase / decrease
- space opened
- harmonic response
- no clear response

The final Core taxonomy should be cross-instrument and may differ from these provisional
piano labels.

### Musical reason

Ensemble improvisation is not only:

```
listen -> choose -> perform
```

It is also:

```
perform
  -> hear what the other musicians did next
  -> estimate whether a meaningful interaction relation occurred
  -> update the next immediate decision
```

This information is not piano-specific. A saxophonist, drummer, bassist, guitarist, or
arranger agent may all need to remember whether an earlier gesture was echoed,
answered, intensified, left space for, or followed by an ensemble density change.

### Causality caution

Temporal adjacency must not be treated as proof of musical causation.

Core should preserve at least two confidence concepts:

- confidence that the response event was actually observed;
- confidence that the response is meaningfully attributable to the preceding gesture.

A low-attribution observation may still be stored but should have little policy effect.

### Current piano-side experiment

`players/piano/ensemble_response.py` currently defines:

- `EnsembleActor`
- `ResponseType`
- `EnsembleResponseObservation`
- `GestureResponseRecord`
- `evaluate_response_bias()`

The piano policy uses only bounded recent memory and modest score biases. It does not
force a response or pre-plan future gestures.

Examples:

- drummer rhythmic echo -> mild support for preserving rhythmic identity while other
  dimensions may vary;
- soloist phrase extension -> favor space/restrained support rather than immediate build;
- space opened / phrase end -> favor answer/fill/punctuation candidates;
- ensemble density increase -> favor recovery space or softer realization.

These are experimental policy interpretations, not proposed Core rules.

### Likely architectural boundary

Core owns:

- generic response observation representation
- performer/section identity
- temporal relation / latency
- confidence and attribution confidence
- provenance
- bounded interaction-event memory interface

Instrument/player layers own:

- whether a specific response should cause that instrument to lay out, answer, build,
  change register, preserve groove identity, etc.

### Regression risk

Low if introduced additively.

Do not make all performance events require a response record. Most ticks may contain
no clear response.

### Tests required

- response may be recorded without claiming causality
- observation confidence and attribution confidence remain distinct
- low attribution produces weak downstream influence
- multiple instrument/section actors can be represented
- no piano-specific register/hand/pedal fields enter the shared representation
- no future action sequence is stored
- existing monophonic/polyphonic online paths remain compatible


## CR-004 — Shared accompaniment role occupancy / harmonic-rhythmic coverage

### Status

Requested from player/piano after cross-source validation with piano/guitar comping material.
Current implementation is an experimental piano-side adapter.

### Requested Core capability

Represent which ensemble member or section is currently occupying accompaniment functions,
without assuming that one instrument must always own them.

Minimum useful information:

- accompaniment/comping actor or section identity
- current role priority: primary / secondary / shared / unspecified
- harmonic coverage strength
- rhythmic coverage strength
- accompaniment activity
- confidence that performers agree on the active harmony/alterations
- confidence/provenance for inferred role assignment

The representation should not encode piano-specific hands, voicing families, pedal, or register.

### Musical reason

Small-group accompaniment conflict is not captured by generic ensemble density alone.

Two ensembles may have the same global density while differing radically:

1. bass/drums/soloist are active but no other chordal instrument is comping;
2. guitar is already supplying continuous harmony and rhythmic support.

The pianist should not respond identically.

Cross-source evidence from piano/guitar comping pedagogy explicitly emphasizes:

- knowing each musician's current role;
- avoiding conflict when piano and guitar can perform the same role;
- deciding which instrument is the primary comping instrument;
- sparse/rhythmic piano behavior when guitar supplies continuous harmonic material;
- switching comping responsibility to create variety and consistency;
- avoiding unnecessary added material when rhythm and harmony are already covered.

### Current piano-side experiment

`players/piano/role_occupancy.py` defines:

- `CompingPriority`
- `CompingRoleOccupancy`
- `RoleOccupancyBias`
- `evaluate_role_occupancy_bias()`

Current piano policy experiments include:

- other instrument primary + strong coverage -> favor lay-out/sparse punctuation;
- duplicated sustained harmonic coverage -> penalty;
- shared high coverage -> favor space/sparse gestures, penalize dense overlap;
- piano primary -> support/anchor is not treated as role conflict;
- low harmonic-agreement confidence -> caution before adding harmonic material.

These mappings remain instrument-policy hypotheses, not proposed Core rules.

### Likely architectural boundary

Core owns:

- generic accompaniment role occupancy
- actor/section identity
- harmonic/rhythmic coverage estimates
- priority/ownership semantics
- agreement/confidence/provenance

Player layers own:

- how their instrument reacts to occupied roles
- instrument-specific sparse/dense realization
- touch, register, pedal, articulation
- whether to punctuate, lay out, sustain, or change voicing family

### Regression risk

Low if additive.

Role occupancy should be optional. Ensemble configurations without multiple comping-capable
instruments should not be forced to populate it.

### Tests required

- same ensemble density can yield different role-occupancy states
- multiple comping-capable instruments can be represented
- harmonic and rhythmic coverage remain separate
- role priority may be shared or unspecified, not only primary/secondary
- low agreement confidence remains distinct from low harmonic coverage
- no piano-specific fields enter the shared object
- representation contains no future turn schedule or exact future notes


## CR-005 — Shared ensemble-breath / foreground-support complementarity evidence

### Status

Requested from player/piano after repeated analysis of the uploaded Charlie Parker
compilation. Current implementation is an experimental piano-side adapter.

### Requested Core capability

Represent an observed short-term relation between foreground activity and accompaniment
support without assigning a causal actor unless evidence exists.

Minimum useful fields:

- breath / complementarity type
- foreground activity drop or rise
- low-harmonic support persistence
- percussive support persistence
- post-event foreground re-entry contrast
- observation confidence
- actor-attribution confidence
- provenance

Provisional observed relation types:

- foreground handoff
- collective release
- collective build
- none / unclassified

### Musical reason

Generic ensemble density is insufficient.

Two passages may have similar overall loudness while differing in an important way:

1. foreground melodic activity falls while rhythm/harmonic support continues;
2. foreground and accompaniment support fall together.

These situations invite different immediate responses from a pianist, soloist, drummer,
or other ensemble agent.

### Causality / attribution caution

Mixed-audio evidence does not establish:

- that the foreground source is a specific player;
- that a specific accompanist intentionally caused the response;
- that temporal adjacency proves musical causation.

Actor attribution must therefore remain independent from the raw complementarity
observation and may legitimately remain zero.

### Current piano-side experiment

`players/piano/bebop_complementarity.py` defines:

- `EnsembleBreathType`
- `EnsembleComplementarityEvidence`
- `classify_ensemble_complementarity()`

Current Piano Solo interpretations include:

- foreground handoff + active support -> preserve space or use a light pickup;
- foreground handoff -> penalize dense overfilling;
- collective release -> permit a directed new phrase entry or continued space.

Current Piano Comping interpretations include:

- supported foreground handoff -> favor lay-out / brief punctuation;
- supported foreground handoff -> penalize sustained harmonic overfill;
- collective release -> permit continued ensemble breath.

These policy mappings remain instrument-local hypotheses.

### Likely architectural boundary

Core owns:

- observed foreground/support relation
- temporal morphology
- confidence
- attribution confidence
- provenance

Player layers own:

- whether to answer, lay out, sustain, build, punctuate, or re-enter;
- register, touch, articulation, density, and instrument-specific realization.

### Tests required

- foreground handoff and collective release remain distinguishable;
- harmonic and percussive support remain separate;
- actor attribution can remain unknown;
- observation contains no future action or exact notes;
- same evidence can be interpreted differently by different instrument policies.


## CR-006 — Shared turn-taking × harmonic/form interaction context

### Status

Requested from player/piano after combining Parker-derived turn-taking morphology with
the existing Shared Harmony Core. Current implementation is a piano-side adapter.

### Requested Core capability

Allow already-observed turn-taking evidence to be referenced alongside the current
harmonic/form state without collapsing the two evidence streams.

Useful shared fields:

- turn-taking episode type / confidence
- phrase-position / boundary pressure
- current harmonic direction or action family
- anticipation strength
- resolution strength
- stability / color-field strength
- provenance for each evidence source
- actor-attribution confidence

The shared layer should not prescribe instrument-specific actions.

### Musical reason

The same observed foreground handoff can have different musical meaning depending on
where it occurs:

- stable harmonic field;
- dominant/resolution pressure;
- known upcoming harmony;
- phrase/cadence boundary.

A pianist, saxophonist, guitarist, or drummer may react differently to the same
ensemble morphology because of harmonic/form location.

### Evidence separation

Do not infer harmony from the Parker audio morphology.

The current experiment keeps:

1. audio-observed turn-taking morphology;
2. Shared Harmony Core state;
3. instrument-local policy interpretation

as separate layers.

### Current piano-side experiment

`players/piano/bebop_harmonic_turn.py` currently derives provisional phases:

- `STABLE_FIELD`
- `DIRECTED_RESOLUTION`
- `ANTICIPATORY`
- `FORM_BOUNDARY`
- `AMBIGUOUS`

using only existing Core fields/action options.

Piano Solo currently interprets those phases as soft immediate biases for:

- connective/color development in stable fields;
- guide-tone / directed resolution under resolution pressure;
- pickup / anticipation when future harmony is known;
- phrase/texture reset near form boundaries.

Piano Comping currently interprets them as soft immediate biases for:

- compact directed support;
- anticipated punctuation;
- form-boundary space;
- release-boundary alignment.

These mappings are player policy, not proposed shared rules.

### Runtime invariant

The shared context must contain no:

- future exact notes;
- fixed future phrase;
- scheduled lick;
- deterministic next action.

It only describes the current relation between observed interaction and harmonic/form
context.


## CR-007 — Shared Scale/Linear scorebook-practice feedback

### Status

Requested from player/piano after the first cross-book practice batch using the nine
uploaded Real/New Real/Vocal/Christmas collections.

Piano now consumes v1.54 Shared Scale/Linear affordances through an instrument-local
register adapter. This request concerns additional **shared context**, not Piano
candidate semantics.

### Evidence source

Derived abstract evidence only. No complete copyrighted melody is stored.

Representative scorebook contexts include:

- even-8th dense harmonic motion;
- medium swing with dense functional changes;
- Afro sections with interlude / solo break;
- half-time rock -> Bossa -> rock feel changes;
- two-feel -> in-four -> back-to-two changes;
- medium-rock repeated rhythm-section writing;
- functional ballad / standard material.

Detailed batch record:

- `research/linear_scale/SCOREBOOK_PRACTICE_BATCH_001.md`
- `research/linear_scale/scorebook_practice_batch_001.json`

### Finding 1 — keep ScaleField evidence-driven

The current v1.54 decision is supported by scorebook practice:

- do not infer a compulsory seven-note scale from chord suffix alone;
- explicit local-key / harmonic evidence may expand the contextual field;
- ambiguous or modern score evidence should remain plural/incomplete when necessary.

No change requested here.

### Finding 2 — route weighting needs feel / section hooks

The same legal pitch-class route can have very different musical plausibility under:

- two feel;
- in four;
- half-time rock;
- Bossa;
- Afro;
- straight-8th ballad;
- vamp;
- head;
- solo;
- interlude;
- solo break.

Requested shared context or hook:

- `feel_change`
- `section_role`
- form/boundary state

Core need not prescribe a player action. It should make this evidence available to
route evaluation and provenance.

### Finding 3 — expose harmonic-rhythm horizon

Requested shared concepts:

- `beats_to_harmonic_change`
- `harmonic_rhythm_density`
- `target_arrival_horizon`

Musical reason:

A chromatic approach/enclosure intention has different plausibility when the target is
an eighth-note away versus several bars away.

The fields must not schedule exact future notes.

### Finding 4 — enclosure needs bounded abstract state

v1.54 correctly exposes `ENCLOSURE` as an intention, but its immediate first-step
pitch classes currently overlap a generic chromatic approach.

Requested future shared representation may include:

- active route kind;
- target pitch class;
- route stage / sides remaining;
- resolution debt;
- start time;
- confidence/provenance.

It must **not** store a frozen future pitch sequence.

This will also fit the newer Legend Vocabulary architecture: an enclosure can be
triggered by Shared Bebop grammar, a remembered fragment, or a Legend vocabulary item
while still using the same shared route state.

### Finding 5 — preserve ingestion provenance/confidence

When Scorebook Ingestion Layer is connected, linear-route evidence should preserve:

- source/book ID;
- page span / evidence locator;
- harmonic parse confidence;
- feel/section parse confidence;
- provenance.

A low-confidence score reading should never become a high-confidence route rule.

### Current Piano boundary

`players/piano/shared_linear_adapter.py` now realizes Core route pitch classes in a
piano register.

Shared Core owns:

- route identity;
- immediate pitch classes;
- target pitch classes;
- tension/resolution semantics.

Piano owns:

- octave/register;
- physical range;
- touch/articulation;
- coordination with left-hand comping.

When shared affordances are supplied, Piano does not independently invent
approach/neighbor/passing route semantics. The former local path is retained only as
compatibility fallback.

### Tests required for future Core changes

- feel/section evidence changes route weighting without changing raw harmonic identity;
- harmonic-rhythm horizon affects approach/enclosure confidence;
- enclosure state contains no future exact note sequence;
- low-confidence score evidence cannot promote a high-confidence route without new
  supporting evidence;
- existing v1.54 no-invented-scale behavior remains unchanged;
- all instrument consumers can reuse the same shared fields.


## CR-008 — Shared abstract written-line comparator

### Status

Requested from player/piano after scorebook practice on:

- Anthropology
- Autumn Leaves
- Actual Proof
- Asa (The Zoo Blues)

Current implementation is a Piano-side **research/evaluation harness** only:

- `players/piano/linear_practice_comparator.py`
- `research/linear_scale/scorebook_abstract_comparator_batch_001.json`

It does not alter Piano musical policy.

### Requested shared capability

Provide an instrument-neutral comparator between:

1. an abstract observation of a written line / remembered vocabulary item; and
2. Shared Linear/Scale candidate route families.

The comparator must not require or retain a complete copyrighted melody.

Recommended abstract dimensions:

- route family
- structural target class
- interval-motion class
- chromatic vs field motion
- contour class
- target-arrival horizon
- section role
- rhythmic density class
- confidence
- provenance

### Musical reason

Exact-note similarity is the wrong primary metric for jazz learning.

The useful question is whether the system has learned the **musical operation**:

- chordal outlining
- diatonic or chromatic passing
- approach
- enclosure
- common-tone retention
- scale fragment
- arpeggio fragment
- anticipation

and whether it applies that operation toward the right structural target and at the
right harmonic/form moment.

This also provides a common evaluation layer for Legend Vocabulary.

Example:

```
Parker fragment
-> abstract route / target / contour observation
-> Shared Linear candidate routes
-> compare musical operation
```

without requiring literal phrase reproduction.

### Scorebook practice findings

#### Anthropology

High-confidence abstract evidence supports a combination of:

- chordal;
- diatonic passing;
- chromatic passing;
- approach;
- enclosure-like directed connection;

under short target horizons and high rhythmic density.

#### Autumn Leaves

The written head provides a useful benchmark for:

- chordal target stability;
- diatonic passing;
- approach;
- common-tone / sustained target behavior;

under medium swing and recurring functional cycles.

#### Actual Proof

The page demonstrates why a comparator must allow:

- chordal / color anchoring;
- scale fragments;
- arpeggio fragments;
- common-tone behavior;

while remaining aware of:

- NC;
- vamp-until-cue;
- written keyboard figures;
- meter changes;
- section-role changes.

#### Asa

The page supports abstract comparison of:

- chordal motion;
- scale fragments;
- chromatic passing;
- arpeggio fragments;
- altered-dominant target behavior.

### Proposed metrics

Useful shared metrics include:

- route-family recall;
- route-family over-generation;
- target-class alignment;
- contour compatibility;
- horizon compatibility;
- section-role compatibility;
- provenance-weighted confidence.

These should remain diagnostics/evaluation and should not by themselves force runtime
actions.

### Legend Intelligence compatibility

The comparator should work for all six approved vocabulary-use types:

- LITERAL_QUOTE
- TRANSPOSED_LICK
- ADAPTED_LICK
- FRAGMENT_RECALL
- ABSTRACTED_PATTERN
- HYBRID_COMPOSITION

A literal quote may be evaluated for source similarity separately, while this comparator
measures whether its **musical function** fits the current context.

### Copyright / memory boundary

The shared comparator must be able to operate on derived observations that contain no:

- full melody;
- exact phrase sequence;
- full copyrighted rhythm transcription.

Provenance may point back to a private score/source when authorized research requires
manual verification.

### Tests requested

- comparator operates without literal pitch sequence;
- route-family recall is independent of transposition;
- target alignment is separable from route-family match;
- confidence/provenance survive comparison;
- scorebook and Legend Vocabulary observations can use the same schema;
- no comparator field schedules future notes.
