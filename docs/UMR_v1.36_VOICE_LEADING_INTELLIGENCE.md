# UMR v1.36 — Shared Voice-Leading Intelligence

## Goal

Voice-leading is promoted to a shared Music Intelligence concept rather than
being treated as piano-specific nearest-note optimization.

The layer serves melody, comping, orchestration, arranging, horn writing, bass,
and later LegendProfile analysis.

## Musical distinctions

v1.36 explicitly distinguishes:
- common-tone retention
- semitone / whole-step continuity
- larger leap cost
- guide-tone / structural-target attraction
- voice identity
- top-line continuity
- bass motion
- contrary and oblique outer-voice motion
- parallel-perfect risk
- unresolved tendency ("resolution debt")

These are weighted affordances and costs, not universal prohibitions.

## Resolution debt

A tension or tendency can create a ResolutionDebt such as:
- dominant b9 -> root / chord target
- 7th -> 3rd in a resolution
- suspension -> chord tone
- chromatic approach -> intended target

The debt is not a fixed future note. It records:
- voice identity
- source pitch
- tendency description
- acceptable target pitch classes
- urgency
- age in committed events
- provenance

A later immediate action may satisfy it. If not, the debt can persist and become
more costly, allowing delayed resolution and expressive reinterpretation.

This keeps the runtime causal:

commit one immediate action -> listen -> evaluate whether the tendency still
matters -> resolve, postpone, reinterpret, or abandon.

## Voice identity

Shared Core defaults to identity-aware movement. Piano hand redistribution,
guitar-string assignment, orchestral divisi, or nearest-note remapping remain
instrument/realization concerns unless a caller explicitly disables identity
preservation.

## Parallel perfects

Perfect parallel motion receives a bounded penalty rather than a hard ban.
This is deliberate: jazz, modal, quartal, planing and modern contexts may use
parallel structures intentionally.

## Architectural boundary

Shared Core:
- semantic voice identity
- target roles
- continuity / attraction / debt
- generic motion relationships

Instrument layers:
- physical hand/fingering assignment
- playable range
- touch/pedal/breath
- style-specific voicing shapes

## Runtime invariant

No exact future note sequence or future voicing sequence is introduced.
Voice-leading evaluates current-to-candidate relationships only.
