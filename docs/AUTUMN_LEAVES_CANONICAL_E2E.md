# Autumn Leaves canonical quartet E2E

This scenario is the first public-safe end-to-end rehearsal fixture for the
four-player realtime path.

## Musical setup

- tune/form reference: Autumn Leaves, G minor jam-session study
- tempo: 172 BPM
- meter: 4/4
- players: Tenor Sax / Piano / Upright Bass / Drums
- performance convention: Jazz Jam Session
- groove: Swing
- coordination: ELASTIC
- HUMAN_DRIFT: off

The fixture contains chord/form information only. It does not embed the melody
or a copyrighted recorded-note transcription.

## Runtime path

```text
SongChart
   ↓
current + next-tick harmony
   ↓
Stage1QuartetRuntime
   ↓
one immutable EnsembleState snapshot
   ├─ Piano immediate decision
   ├─ Bass immediate decision
   ├─ Drums immediate decision
   └─ Sax immediate decision
   ↓
atomic publication
   ↓
role-aware Shared Groove projection
   ↓
PortableRenderPacket v1
   ↓
renderer/native audio runtime
```

No Player receives another Player's same-tick decision.

## What this test is for

The first pass is intended to answer structural questions before aesthetic
tuning:

1. Do all four Players participate through the canonical runtime path?
2. Do they receive the same jam-session convention?
3. Does the form progress correctly, including half-bar harmonic changes?
4. Does every committed gesture reach Portable Runtime Protocol v1?
5. Does ELASTIC role-aware timing remain active while HUMAN_DRIFT stays off?
6. Does one tick publish before the next tick is perceived?

The first pass is not intended to prove that the performance is already
stylistically convincing.

## Next listening step

After this E2E regression is stable, generate an approved-sample rehearsal
render from the PortableRenderPackets and inspect:

- foreground/support balance;
- phrase handoff;
- Piano space around Sax phrases;
- Bass continuity during Drum setups;
- Sax phrase density and breath behavior;
- role-relative timing under ELASTIC groove.

Only after the fixed-tempo quartet is audibly coherent should HUMAN_DRIFT be
activated.
