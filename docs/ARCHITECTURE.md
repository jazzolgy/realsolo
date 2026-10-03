# RealSolo Architecture

## Core principle

RealSolo is an AI improvising musician, not an offline solo generator.

Runtime loop:

Perceive
→ Future Harmony / Form Awareness
→ Musical Intention
→ Soft Target
→ Candidate Routes
→ Universal + Style + Legend + Ensemble Evaluation
→ Immediate Commit
→ Listen Again
→ Re-plan / Continue / Stop / Answer

The system may anticipate and prepare, but it must not precompose an exact future note sequence and replay it as improvisation.

## Shared layers

- `core/umr/` — universal music representation
- `core/harmony/` — expected / observed / inferred harmony
- `core/phrase/` — phrase, motif, narrative and memory
- `core/rhythm/` — beat, groove, swing and microtiming
- `core/cognition/` — expectation, surprise, tension, release
- `core/legend_profiles/` — multi-legend contextual tendencies
- `core/online_evaluator/` — evaluates only unperformed immediate candidates

## Canonical Musical Coordinate

RealSolo learns musical behavior primarily in **musical structure coordinates**,
not elapsed recording time.

Canonical event/evidence address:

```text
song
-> arrangement segment
-> core form / section
-> form bar / score bar
-> beat / subdivision
-> chorus or recurrence index
-> performance phase
-> phrase / harmony / ensemble role
```

Elapsed seconds remain source provenance and a locator back into the recording.
They must not be the primary comparison coordinate for musical learning.

This rule applies across Jazz, Pop and Classical music. Jazz may use chorus/form
recurrence; Pop often uses section instance + bar-within-section; Classical may
use nested formal-function coordinates such as movement/section/phrase/bar.
One-off intros, vamps, interludes, tags, cadenzas, codas and outros remain
first-class arrangement segments rather than being forced into a recurring
form grid.

Promotion path:

```text
audio timestamp / feature
-> beat and bar alignment
-> section / form / recurrence alignment
-> instrument and ensemble attribution
-> same-position comparison
-> vocabulary / tendency / shared grammar
```

Unaligned timestamp-only acoustic data may be stored for navigation and anomaly
detection, but it must not directly update musical research priors.

## Instrument layers

- `players/sax/`
- `players/piano/`
- later: bass, drums, guitar, voice, etc.

Instrument-specific performance grammar must remain separate from shared musical intelligence.

## Real-time layer

### Ownership principle

> **Realtime does not decide the music. Portable Core and Players decide the performance intention; Realtime executes that intention as sound on the mobile device accurately and with low latency.**

Realtime therefore owns low-latency execution, scheduling, I/O, device/audio integration, and performance output. It must not independently invent instrument musical policy that belongs to Portable Core or Players.


- `realtime/audio_input/`
- `realtime/midi_input/`
- `realtime/beat_form_tracker/`
- `realtime/ensemble_state/`
- `realtime/scheduler/`
- `realtime/performance_output/`

## Research layer

Each legend study is evidence-gated and provenance-aware. Charlie Parker is the first high-resolution study, not the model identity.

Cross-legend comparison must separate:
1. SharedJazzGrammar
2. Era / Substyle Grammar
3. Instrument Grammar
4. LegendProfile
5. RecordingContextProfile
6. Current Ensemble State


## Cross-instrument musical memory

Legend vocabulary is not owned by the source instrument.

An observed solo idea may be decomposed into transferable musical dimensions:
pitch/interval, rhythm, contour, accent, density arc, phrase shape,
tension/release, target behavior, interaction role, articulation, and register
trajectory.

Examples:
- Bill Evans piano rhythm/contour may become Sax or Bass material.
- Charlie Parker interval/target behavior may become Piano material.
- Drum-solo rhythm, accent and density arcs may become Piano/Sax/Bass phrase
  material with newly generated pitches.
- A pitched-source phrase may contribute only rhythm or phrase shape to Drums.

`source_instrument` records provenance, not ownership. Players request the
dimensions they can use and apply their own physical/instrument grammar at
realization time.

Promotion rule:
SOURCE INSTRUMENT OBSERVATION
-> INSTRUMENT-NEUTRAL MUSICAL DIMENSIONS
-> Legend Vocabulary / Shared Memory
-> target Player realization

Do not copy source-instrument physical constraints into another Player.


## Shared Solo Grammar

General improvisation methodology is shared musical intelligence, not Legend
ownership.

Examples include motif statement/repetition/variation, fragmentation,
sequence, rhythmic displacement, augmentation/diminution, register change,
space, contrast, recap, resolution, future-harmony targeting, call/response,
and tension/density-arc development.

Legend research answers **how a specific musician tends to use these shared
operations in context**. It must not redefine the operations as if they were
owned by that musician.

Drum-solo studies may contribute shared rhythmic/development operations.
Parker studies may contribute melodic/linear priors. Bill Evans studies may
contribute motif, harmony, rhythm, space, and interaction priors. Any Player
may consume the transferable dimensions and realize them through its own
instrument grammar.


## Shared Solo Realization Boundary

Solo intelligence is split by **musical meaning** versus **instrument realization**.

### Shared Core owns

`src/music_intelligence/reasoning/`

- `solo_grammar.py` — general improvisation development operations
- `solo_phrase_intent.py` — short-horizon solo intention
- `solo_candidates.py` — instrument-neutral semantic candidate specs
- `solo_runtime.py` — one-event online solo planning
- `solo_expression.py` — instrument-neutral expressive intention
- `solo_realizer.py` — common realizer protocol/registry
- `feasibility.py` — common feasibility assessment schema/protocol
- `turn_taking.py`
- `ensemble_complementarity.py`
- `phrase_space.py`
- `harmonic_turn.py`

These layers must not branch on `if instrument == "piano"` or import a Player.

### Players own physical realization

Each Player supplies its own:

- `solo_realizer.py`
- `solo_expression.py`
- `feasibility.py`

Current implementations exist for Piano, Sax, Bass and Drums.

The flow is:

```text
Shared Solo Candidate
        +
Shared Solo Expression Intent
        ↓
registered instrument SoloRealizer
        ↓
instrument-specific realization
        ↓
instrument-specific Feasibility
        ↓
evaluation / ONE EVENT commit
        ↓
listen and re-plan
```

The source instrument of an idea does not own the musical idea. A drum-derived
rhythmic/displacement pattern, Parker-derived linear idea, or Bill Evans-derived
motif/space behavior may enter Shared Solo intelligence and then be realized by
any Player.

### Piano ownership is intentionally narrow

Piano-specific ownership is limited to concepts that are actually piano-specific,
especially register realization, voicing, two-hand comping, left-hand comping,
right-hand comping, hand allocation, pedal/touch and physical keyboard feasibility.

General solo phrasing, rhythm, interaction, variation, narrative, turn-taking,
space and candidate meaning belong in Shared Core when they do not depend on the
physical piano.
