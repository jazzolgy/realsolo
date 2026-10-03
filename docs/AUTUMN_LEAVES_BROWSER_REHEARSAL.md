# Autumn Leaves browser rehearsal

The Stage-1 browser now exposes a **Jam Quartet — AI quartet** mode.

When selected, the app loads the canonical public-safe Autumn Leaves G-minor
chart fixture and requests each beat from the real four-player runtime:

```text
browser transport
  ↓
/api/quartet-event
  ↓
Stage1QuartetRuntime
  ↓
Piano + Bass + Drums + Tenor Sax
  ↓
same immutable snapshot
  ↓
atomic publication
  ↓
role-aware Shared Groove
  ↓
RenderGesture
  ↓
approved sample engine
```

This replaces the old split path where accompaniment came from the trio runtime
while Sax came from the temporary `Stage1Soloist`.

## Listening

Run:

```bash
realsolo-ensemble install-assets --profile lite
realsolo-ensemble stage1 --asset-profile lite
```

Open the local Stage-1 page, choose **Jam Quartet — AI quartet**, and press Play.

The browser prefers the approved sample engine when the selected sample profile
is installed. Otherwise the existing SoundFont/oscillator fallbacks remain
available for diagnostics.

## First canonical listening conditions

- Autumn Leaves
- G minor
- 172 BPM
- Tenor Sax / Piano / Upright Bass / Drums
- Jazz Jam Session convention
- Swing
- ELASTIC coordination
- HUMAN_DRIFT off

The purpose of the first listen is not to optimize style immediately. First
verify the canonical path itself: foreground/support balance, phrase handoff,
space, Bass continuity, Sax breath behavior, and role-relative timing.

Only after this fixed-tempo pass is coherent should HUMAN_DRIFT be enabled.
