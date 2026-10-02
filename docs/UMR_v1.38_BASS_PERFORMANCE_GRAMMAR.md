# AI Bassist v1.38 — Bass Performance Grammar v0.1

## Goal

Move the bass workstream from ad-hoc candidate weights toward explicit
bass-specific decision semantics without creating a second harmony engine.

The project asks why a player chooses an action in context, not merely what the
next pitch is. v1.38 therefore introduces a small Performance Grammar between
Shared Core semantics and immediate bass realization.

## Source basis

This pass is grounded in the uploaded bass-study material.

The most directly applicable pedagogical observations are:

- walking bass commonly uses a quarter-note pulse;
- chordal, scale-related, and chromatic movement are treated as distinct ways of
  building a line;
- the last note before a chord change is frequently treated as an approach or
  preparation toward the next root;
- repeated notes, register direction, articulation, skips, ghosted events and
  rhythmic embellishment affect bass-line character;
- groove-specific bass behavior can be coupled to drum/percussion function
  rather than explained by harmony alone.

These are encoded as soft tendencies. The sources are pedagogical evidence, not
universal empirical laws.

## Architectural boundary

Shared Core owns:

- harmonic evidence and inference
- chord/scale/tonality semantics
- harmonic function
- generic voice-leading
- form / phrase / memory / narrative
- shared ensemble state

Bass Performance Grammar owns:

- bass metric role
- bass target strategy
- bass movement/realization category
- bass register trajectory preference
- bass groove relation
- bass articulation intention
- repeated-note pressure
- bass-specific simplification/space preference

The grammar does **not** infer a chord scale. `SHARED_SCALE_OR_COLOR` is only a
realization category for pitch material that a future Shared Core interface may
explicitly provide.

## New objects

`MetricRole`

- `HARMONIC_ANCHOR`
- `CONTINUATION`
- `PREPARATION`
- `TWO_FEEL_ANCHOR`
- `PEDAL_ANCHOR`

`MotionStrategy`

- `CHORDAL`
- `SHARED_SCALE_OR_COLOR`
- `CHROMATIC_APPROACH`
- `DIRECT_ANTICIPATION`
- `PEDAL`

`TargetStrategy`

- current root
- current chord member
- next root
- none

`RegisterIntent`

- stable
- ascend
- descend

`GrooveRelation`

- on pulse
- prepare change
- sustain anchor

`ArticulationIntent`

- neutral
- connected
- short
- ghosted

## Current scoring behavior

### Beat 1 / harmonic anchor

Current-root support receives a soft bonus. Chromatic preparation on the main
anchor is discouraged, but never globally forbidden.

### Middle walking beats

Chordal/current-harmony continuation receives a small support weight.

### Last beat before a known next harmony

Chromatic approach receives the strongest grammar bonus; direct anticipation
receives a smaller bonus. Staying on the current root is still legal but loses
some directional preference.

### Repetition

Immediate repeated pitch is penalized according to
`repeated_note_tolerance`. Repetition is never banned because stylistic,
rhythmic, pedal, ostinato and ensemble contexts may require it.

### Register trajectory

`ASCEND` and `DESCEND` are soft intentions. They bias the current candidate
without storing future pitches.

### Ensemble activity

A very busy ensemble applies a small simplification pressure to chromatic/color
movement. This is intentionally minimal until the shared real-time ensemble
state is connected.

## Integration

`immediate_realizer.py` now combines:

1. Shared Core harmonic evidence
2. Shared Core voice-leading score
3. Bass Performance Grammar score
4. bass register / leap realization

and returns one-event candidates with the grammar decision attached.

The runtime invariant remains unchanged:

```
plan intention / candidate family
-> evaluate one immediate action
-> commit
-> listen again
-> re-plan
```

## What this version deliberately does not do

- no fixed 4-bar walking line
- no chord-symbol parser in Bass
- no local chord-scale theory
- no Ron Carter phrase copying
- no drummer simulation
- no learned probability claims

## Next vertical slice

The next useful step is **Bass Groove Interaction v0.1**:

- represent bass-to-drum/percussion coupling as a bass-specific consumer of
  shared ensemble evidence;
- distinguish pulse support, kick lock, ride/hi-hat relation, fill response,
  syncopated counter-pattern and deliberate space;
- keep microtiming relative to a shared beat/groove reference;
- add ghost/dead-note and note-length realization only after the interaction
  role is explicit.

Brazilian-bass material is especially useful for this next slice because it
describes bass behavior in relation to surdo accents and rhythmic-section
function, making the interaction dependency explicit rather than inferred from
pitch alone.
