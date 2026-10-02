# Stage-1 Piano Integration

Stage 1 now uses the actual `player/piano` immediate comping pipeline for the
piano part of accompaniment.

Runtime split:
- piano: `player/piano`
- bass: realtime fallback until `player/bass` exposes committed events
- drums: realtime fallback until `player/drums` exposes committed events
- soloist: current one-event Core bridge

The chart adapter supplies expected harmony to the pianist. It does not prebuild
a future piano part. On each accompaniment tick the pianist receives current
context, builds a bounded immediate candidate slate, commits one comping action
(or silence), and the selected shared polyphonic event is projected through the
common renderer adapter.

The chart-to-resolved-harmony adapter is deliberately narrow. Shared harmony
should eventually provide the authoritative resolved harmonic roles so this
temporary adapter can be removed.
