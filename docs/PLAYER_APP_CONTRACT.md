# Player -> App Runtime Contract

## Why this exists

The live app must not own bass, drum, or piano musical intelligence.

Current workstreams:
- `player/bass`
- `player/drums`
- `player/piano`

Each player owns its instrument-specific musical realization. The app owns:
- chart/session transport
- live input
- deadline-safe scheduling
- rendering
- UI

## Integration shape

```
Shared Core
   -> Bass Player  ----┐
   -> Drum Player  ----┤
   -> Piano Player ----┤
   -> Solo Player  ----┘
                       |
             committed immediate gestures
                       |
              Realtime App Scheduler
                       |
               Renderer / SoundFont
```

A player should not return a whole future chorus. It returns one immediately
committed gesture, then listens/re-plans.

## Renderer-facing gesture

The app currently defines an additive renderer DTO in
`realtime/ensemble_app/player_contract.py`.

Each voice carries:
- pitch
- velocity
- duration
- onset offset
- articulation
- instrument role

A gesture may also contain drum hits.

This DTO is intentionally narrower than Shared Core's
`PolyphonicEventCandidate`. Core/player semantics such as harmonic role,
voice-leading constraints, provenance, and candidate scores do not need to be
duplicated in the renderer. The selected/committed event is projected down to
only the data required for scheduling and sound.

## Mapping from Shared Core

Current Core `VoiceEvent` maps naturally:

- `pitch_midi` -> `RenderVoice.pitch_midi`
- `velocity` -> `RenderVoice.velocity`
- `duration_beats` -> `RenderVoice.duration_beats`
- `onset_offset_beats` -> `RenderVoice.onset_offset_beats`
- `articulation` -> `RenderVoice.articulation`
- `assignment.instrument_family/part_id` -> renderer instrument role

The app should consume committed player output, not candidate sets.

## Temporary fallback

The current Stage-1 local bass/drums/comping rules are retained only so the app
can produce sound before the player branches are integrated.

They are marked `source=realtime_fallback`.

Do not improve those fallback musical rules in the realtime branch. Improve the
corresponding player workstream instead.
