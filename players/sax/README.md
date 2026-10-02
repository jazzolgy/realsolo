# Sax Player

AI Saxophonist workstream.

## Owns

- monophonic melodic realization
- phrase entrance / ending / breath / space
- register trajectory and leap grammar
- articulation: tongue, legato, accent, ghost, scoop, fall, doit, subtone
- bend / vibrato / growl / altissimo semantics
- rhythmic placement and microtiming
- motif development and call / response
- sax-specific physical feasibility
- saxophone-specific style / LegendProfile realization

## Consumes from Shared Core

- Expected / Observed / Inferred Harmony
- Harmonic Reasoning Orchestrator and HarmonicActionOptions
- function / modal / local-key hypotheses
- contextual tension
- voice-leading / resolution debt
- form / phrase / narrative / memory
- ensemble state and interaction
- future-harmony awareness

The sax layer does not own a separate jazz-harmony theory. It realizes shared
harmonic intelligence as a monophonic line.

## Runtime contract

Slow Brain may plan intention, target family, contour, register and density.
It must not prewrite a future solo.

Commit one immediate sax event -> listen -> update ensemble/harmony state ->
re-plan.
