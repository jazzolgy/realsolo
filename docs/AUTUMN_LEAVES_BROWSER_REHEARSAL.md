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


## Listening decision cadence

The browser Jam Quartet now requests the canonical runtime on a nominal
eighth-note decision grid (two causal decisions per beat).

This does **not** mean straight eighth-note playback. The grid only determines
when the ensemble listens and may make the next immediate decision:

```text
nominal 0.0
→ quartet decision
nominal 0.5
→ quartet decision
```

The Shared Groove adapter then moves swing-eligible offbeats to the
role-relative ELASTIC performed position. In other words:

```text
decision grid ≠ performed timing
```

The browser serializes quartet requests so a later eighth-note tick cannot
mutate the runtime before the previous tick has published its state. This keeps
the causal sequence:

```text
Snapshot N → four decisions → atomic publish
Snapshot N+1 → four decisions → atomic publish
```

while giving Sax/Bass/Drums enough temporal resolution for an initial swing
listening pass.
