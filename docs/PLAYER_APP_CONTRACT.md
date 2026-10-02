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


## Shared-Core projection adapter

`player_adapter.committed_polyphonic_to_render_gesture()` now provides the
canonical path from a selected `PolyphonicEventCandidate` into the renderer.

Important: this adapter runs **after** a player has selected/committed the
gesture. It never sees candidate sets and does not re-score musical alternatives.

This means the existing piano workstream can connect without leaking
piano-policy code into realtime, and bass/drums can use the same path once their
player implementations expose committed events.
