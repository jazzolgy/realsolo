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

## Instrument layers

- `players/sax/`
- `players/piano/`
- later: bass, drums, guitar, voice, etc.

Instrument-specific performance grammar must remain separate from shared musical intelligence.

## Real-time layer

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


## Default jazz performance convention

Unless an explicit user/session/arrangement instruction or written score/chart
instruction says otherwise, jazz performance uses the shared
`JAZZ_JAM_SESSION` convention.

Precedence:

```text
explicit user/session instruction
> written score/chart instruction
> jazz jam-session convention
> genre/style/legend soft priors
> player realization
```

The convention is owned by Shared Music Intelligence because it coordinates
multiple players. It must not be duplicated independently in Piano, Bass,
Drums, Sax, or Realtime.

The default means shared form, repeated form during improvisation, foreground
leadership with accompaniment yielding, rhythm-section form/pulse orientation,
and phrase/form-boundary handoff cues. It does not invent a fixed solo order,
number of choruses, trading scheme, intro, tag, or ending when none is given.
