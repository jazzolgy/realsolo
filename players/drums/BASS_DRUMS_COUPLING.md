# Bebop Bass–Drums Coupling

## Boundary

This layer **reads Shared EnsembleState** and does not modify Core, bass-player
logic, harmony, or shared interaction semantics.

The drum workstream only asks:

> How much rhythmic floor is the bass already providing, and how should that
> change the drummer's immediate realization?

It does not ask what bass note should be played.

## Projection

From the active Shared Core bass player/intention, the drum adapter reads:

- BASS role presence
- LOCK interaction
- density / energy
- phrase maturity
- semantic tags such as `walking` and `quarter_note_pulse`
- explicit ensemble-figure/accent tags when available

This becomes a drummer-owned `BassPulseProjection`.

## Coupling interpretation

The first bebop coupling model estimates:

- **shared_pulse** — how strongly bass + ensemble already establish time
- **drummer_freedom** — how much the drummer can vary surface rhythm without
  threatening pulse clarity
- **floor_support_need** — whether quiet bass-drum reinforcement adds useful
  bottom
- **accent_alignment_opportunity** — whether a selective kick alignment is
  musically meaningful
- **low_end_overlap_risk** — whether audible kick-floor duplication may muddy
  the bass register

The central design assumption is:

`strong walking bass != play more kick with bass`

Instead:

`strong walking bass -> more shared pulse -> more drum surface freedom`

and often:

`strong/dense bass -> less need for audible bass-drum floor duplication`

while explicit ensemble figures can still create selective alignment windows.

## Why this matters for bebop

The historical/aural model of bebop is complementary:

- acoustic bass can provide continuous quarter-note trajectory;
- ride cymbal carries drum-set time identity;
- snare/bass drum become freer to comment and punctuate;
- occasional alignment has meaning precisely because continuous duplication is
  not required.

Therefore RealSolo should not score bass/drums lock using simultaneous-hit rate.

## Future calibration

These weights remain engineering hypotheses until we have:
- identified recordings
- bass/drum event annotations
- expert listening judgments
- ideally separated stems or reliable multitrack material

The implementation deliberately preserves that uncertainty.
