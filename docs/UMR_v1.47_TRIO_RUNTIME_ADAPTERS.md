# UMR v1.47 — Piano / Bass / Drums Runtime Adapters

## Purpose

v1.46 created the ensemble runtime loop. v1.47 gives piano, bass, and drums the
same app-facing adapter boundary.

The adapter is deliberately thin. It does not recreate instrument intelligence
inside the realtime app.

## NativeImmediateResult

Each instrument workstream eventually exposes one native immediate decider that
returns:

- one committed RenderGesture, or deliberate silence;
- density;
- energy;
- tension;
- leadership;
- phrase maturity;
- semantic tags / provenance.

The adapter combines that result with the current InteractionDirective and
publishes PlayerRuntimeDecision to the v1.46 loop.

## No fake readiness

An adapter may exist before an instrument branch has an executable native
decider.

If no native decider is connected, the adapter returns None. The runtime loop
marks that player as skipped rather than silently substituting fake AI output.

This is especially important at the current project stage:

- Piano has substantial executable player policy on player/piano.
- Bass currently has a research/workstream shell but no committed executable
  player implementation in players/bass.
- Drums currently has research/design material but no committed executable
  player implementation in players/drums.

Therefore v1.47 creates the integration boundary without pretending the trio is
already musically implemented.

## Next integration work

1. player/piano exposes one small native realtime decider around its existing
   immediate comping pipeline.
2. player/bass implements its first immediate bass policy and exposes the same
   decider shape.
3. player/drums implements its first immediate drum policy and exposes the same
   decider shape.
4. realtime/ensemble-app injects those deciders into PianoRuntimeAdapter,
   BassRuntimeAdapter, and DrumsRuntimeAdapter.
5. Remove app-local fallback parts one instrument at a time.

The realtime loop and renderer contract do not need to change as player
intelligence becomes richer.
