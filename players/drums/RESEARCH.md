# AI Drummer Research Notes

## Boundary

This workstream is an instrument-specific realization layer.

It owns drum-set time feel, orchestration, comping, fills/setups, dynamics,
articulation, microtiming, physical feasibility, and drummer-specific interaction.

It **does not** redefine Shared Core form/phrase/narrative/memory/ensemble
semantics or Shared Harmony theory.  Harmonic information is consumed through
shared objects/projections and used only to shape drum realization.

## Runtime invariant

The drummer may plan groove, energy, orchestration, interaction intention, and
candidate families, but it must not freeze a future drum sequence.

**Plan intention -> choose one immediate drum gesture -> commit -> listen -> re-plan.**

A gesture may contain simultaneous or near-simultaneous drum-kit hits.  It is
one current physical/musical action, not a cached bar or fill.

## Research direction

### 1. Performance representation before audio generation

The first vertical slice should operate at performance-event level:

- drum voice / kit surface
- limb assignment and feasibility
- velocity
- articulation
- microtiming
- musical role (time / comp / setup / fill / accent / space)

This keeps musical decisions inspectable and testable before committing to a
specific sampler or neural audio renderer.

### 2. Human groove priors

The Groove MIDI Dataset (GMD) is a useful legal/open research source for
velocity and microtiming priors.  It contains human-performed expressive drums
with tempo/style metadata and can support later style-conditioned priors.

GrooVAE is useful as evidence that quantized patterns can be mapped to expressive
velocity/microtiming.  In RealSolo it should be treated as a prior/adapter or
offline research baseline, not as the runtime architecture, because fixed
2/4-bar generation conflicts with the online listen/re-plan contract.

### 3. Interaction policy

Drummer intelligence should separate:

- **timekeeping stability** — preserve a legible pulse/feel;
- **activity headroom** — play less when the ensemble is already dense;
- **phrase punctuation** — setups/fills near phrase or section boundaries;
- **explicit ensemble cues** — kicks deserve high priority;
- **tension projection** — Shared Core/Harmony tension may increase intensity,
  without the drum layer deriving chord-scale or functional harmony theory;
- **space** — silence is an intentional candidate, not an error.

### 4. Planned next research

- brush grammar and ballad time
- ride-cymbal microtiming distributions by tempo
- bass-drum feathering vs accent roles
- comping independence and limb-conditioned probability
- setup/fill length as an online continuation problem
- bass/drums coupling and shared microtiming
- drummer LegendProfile features that describe decision tendencies rather than
  memorized licks/fills
- evaluation: beat stability, response latency, ensemble responsiveness,
  physical feasibility, groove preference, intervention rate

## Initial vertical slice

The first implementation supports a medium-swing online policy:

- canonical ride placement evaluated only at the current triplet-grid instant
- hi-hat 2/4 at current downbeats
- snare/bass-drum comping candidates
- explicit ensemble kick candidate
- phrase/section setup candidate
- intentional space candidate
- read-only Shared Harmony tension input
- limb feasibility validation
- exactly one committed gesture per decision call

This is deliberately a small, inspectable baseline for later learned candidate
priors and real-time listening.
